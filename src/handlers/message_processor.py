"""
WhatsApp AI Chatbot - Message Processor
======================================
Handles incoming WhatsApp message processing, content extraction,
and message validation.

Author: Rian Infotech
Version: 2.2 (Structured)
"""

import logging
from typing import Dict, Tuple, Optional

# Import core functionality
from src.core.conversation_manager import load_conversation_history, save_conversation_history, sanitize_user_id
from src.core.supabase_client import get_supabase_manager

# Import handlers
from src.handlers.ai_handler import generate_ai_response
from src.handlers.whatsapp_handler import send_complete_message

# Configure logging
logger = logging.getLogger(__name__)

# Session-based bot message tracking (fallback when database is unavailable)
_session_bot_messages = set()

# ============================================================================
# HANDOVER DETECTION FUNCTIONS
# ============================================================================

def detect_user_handover_request_ai(message_text: str) -> tuple[bool, float, str]:
    """
    AI-powered detection of user requests for human handover using OpenAI.
    
    Args:
        message_text: The user's message content
        
    Returns:
        Tuple of (should_handover, confidence_score, reason)
    """
    logger.info(f"🤖 AI INTENT - Starting AI analysis for message: '{message_text}'")
    
    if not message_text or len(message_text.strip()) < 3:
        logger.info(f"🤖 AI INTENT - Message too short, skipping AI analysis")
        return False, 0.0, "Message too short"
    
    try:
        from openai import OpenAI
        import os
        import json
        from src.config.config import (
            AI_INTENT_CONFIDENCE_THRESHOLD, 
            AI_INTENT_DETECTION_ENABLED,
            AI_INTENT_MODEL,
            AI_INTENT_LOGGING_ENABLED
        )
        
        # Check if AI intent detection is enabled
        if not AI_INTENT_DETECTION_ENABLED:
            logger.info("AI intent detection disabled, using fallback")
            return detect_user_handover_request_fallback(message_text), 0.5, "AI detection disabled"
        
        # Initialize OpenAI client
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Construct the analysis prompt
        prompt = f"""
Analyze this user message to determine if they want to speak with a human agent or are expressing frustration with automated responses.

User message: "{message_text}"

Consider these indicators for human handover:
- Direct requests for human support ("talk to human", "speak to someone")
- Expressions of frustration ("this isn't helping", "I'm frustrated")
- Requests for escalation ("get me a manager", "customer service")
- Indications the bot isn't meeting their needs ("you don't understand")
- Asking for "real" or "actual" person
- General dissatisfaction with automated responses

Respond in this exact JSON format:
{{"handover_needed": true/false, "confidence": 0.0-1.0, "reason": "brief explanation"}}

Be conservative - only recommend handover if confidence is high (>{AI_INTENT_CONFIDENCE_THRESHOLD}).
"""

        # Call OpenAI API
        response = client.chat.completions.create(
            model=AI_INTENT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.1,  # Low temperature for consistent results
            response_format={"type": "json_object"}
        )
        
        # Parse the response
        result = json.loads(response.choices[0].message.content)
        
        handover_needed = result.get('handover_needed', False)
        confidence = float(result.get('confidence', 0.0))
        reason = result.get('reason', 'No reason provided')
        
        # Log the AI analysis for monitoring
        logger.info(f"🤖 AI INTENT - Message: '{message_text[:50]}...' | Handover: {handover_needed} | Confidence: {confidence:.2f} | Reason: {reason}")
        
        # Only trigger handover if confidence is high enough
        should_handover = handover_needed and confidence >= AI_INTENT_CONFIDENCE_THRESHOLD
        
        # Log to Supabase for monitoring and improvement
        if AI_INTENT_LOGGING_ENABLED:
            try:
                supabase = get_supabase_manager()
                if supabase.is_connected():
                    supabase.client.table('intent_analysis_log').insert({
                        'message_text': message_text,
                        'handover_needed': handover_needed,
                        'confidence_score': confidence,
                        'reason': reason,
                        'final_decision': should_handover,
                        'model_used': AI_INTENT_MODEL,
                        'created_at': 'now()'
                    }).execute()
            except Exception as log_error:
                logger.warning(f"Failed to log intent analysis: {log_error}")
        
        return should_handover, confidence, reason
        
    except Exception as e:
        logger.error(f"AI intent detection failed: {e}")
        # Fallback to pattern matching if AI fails
        return detect_user_handover_request_fallback(message_text), 0.5, f"AI failed, used fallback: {str(e)}"


def detect_user_handover_request_fallback(message_text: str) -> bool:
    """
    CONSERVATIVE fallback pattern-matching detection for when AI is unavailable.
    Only triggers on very explicit human requests to avoid false positives.
    
    Args:
        message_text: The user's message content
        
    Returns:
        True if user is requesting human handover, False otherwise
    """
    if not message_text or len(message_text.strip()) < 3:
        return False
    
    message_lower = message_text.lower().strip()
    
    # VERY explicit human request triggers only (no ambiguous phrases)
    explicit_human_requests = [
        'talk to a human', 'speak to a human', 'connect me to a human',
        'i want to talk to a human', 'i need to speak to a human',
        'human agent', 'human support', 'live agent', 'real person',
        'transfer me to human', 'escalate to human', 'customer service agent'
    ]
    
    # Only trigger on very explicit requests to avoid false positives
    for trigger in explicit_human_requests:
        if trigger in message_lower:
            logger.info(f"🔄 CONSERVATIVE FALLBACK - Explicit human request detected: '{trigger}' in message: {message_text[:50]}...")
            return True
    
    logger.debug(f"🔄 CONSERVATIVE FALLBACK - No explicit human request found in: {message_text[:50]}...")
    return False


def detect_user_handover_request(message_text: str, customer_context: dict = None) -> bool:
    """
    SMART handover detection using AI classification agent that distinguishes between
    actual handover requests and memory/capability questions.
    
    Args:
        message_text: The user's message content
        customer_context: Known information about the customer for better context
        
    Returns:
        True if user is requesting human handover, False otherwise
    """
    logger.info(f"🎯 SMART HANDOVER - Starting intelligent detection for: '{message_text}'")
    
    try:
        # Use our smart classification agent
        from src.agents.handover_classification_agent import get_handover_classification_agent
        
        agent = get_handover_classification_agent()
        should_handover, reason, confidence = agent.should_trigger_handover(message_text, customer_context)
        
        logger.info(f"🤖 SMART CLASSIFICATION - Should handover: {should_handover} | Confidence: {confidence:.2f} | Reason: {reason}")
        
        return should_handover
        
    except Exception as e:
        logger.error(f"🎯 SMART HANDOVER ERROR - Exception in classification: {e}")
        # Fallback to very conservative pattern matching
        fallback_result = detect_user_handover_request_fallback(message_text)
        logger.info(f"🎯 SMART HANDOVER FALLBACK - Using conservative fallback: {fallback_result}")
        return fallback_result


def handle_user_handover_request(phone_number: str, trigger_message: str) -> tuple[bool, str]:
    """
    Handle user's request for human support by disabling bot and sending confirmation.
    Enhanced with CRM integration for lead management.
    
    Args:
        phone_number: WhatsApp phone number
        trigger_message: The message that triggered handover
        
    Returns:
        Tuple of (success, status_message)
    """
    try:
        logger.info(f"🤝 HANDOVER REQUEST - Processing handover request from {phone_number}: {trigger_message[:100]}...")
        
        supabase = get_supabase_manager()
        
        if not supabase.is_connected():
            logger.error("🤝 HANDOVER REQUEST - Database not connected, cannot process handover")
            return False, "Database not available for handover"
        
        # 1. First save the user's trigger message
        safe_user_id = sanitize_user_id(phone_number)
        supabase.save_message_with_status(
            phone_number=phone_number,
            message_content=trigger_message,
            role='user',
            message_id=None,
            status='received'
        )
        
        # 2. CRM INTEGRATION: Get or create contact and lead
        from src.services.lead_service import LeadService
        lead_service = LeadService()
        
        try:
            # Get or create contact
            base_phone = phone_number.replace('@s.whatsapp.net', '').replace('_s_whatsapp_net', '')
            contact = supabase.get_or_create_contact(phone_number)
            
            if contact:
                contact_id = contact['id']
                logger.info(f"🏢 CRM INTEGRATION - Contact found/created: {contact_id}")
                
                # Create or update lead for handover
                lead_data = {
                    'contact_id': contact_id,
                    'company_name': f"Support Request - {base_phone}",
                    'specific_needs': f"Customer requested human support. Trigger message: {trigger_message[:200]}",
                    'lead_status': 'qualified',  # Requesting human support = qualified lead
                    'lead_score': min((contact.get('lead_score', 0) or 0) + 25, 100),  # Boost score for handover
                    'lead_source': 'whatsapp',
                    'priority': 'high',  # Human requests are high priority
                    'handover_requested': True,
                    'handover_trigger': trigger_message[:500],
                    'handover_timestamp': 'now()'
                }
                
                # Try to create lead
                try:
                    lead_response = lead_service.create_lead(lead_data)
                    if lead_response and lead_response.get('id'):
                        logger.info(f"🎯 CRM LEAD - Created lead: {lead_response['id']}")
                        
                        # Create follow-up task for agent
                        task_data = {
                            'contact_id': contact_id,
                            'title': f'Respond to human support request',
                            'description': f'Customer requested human support via WhatsApp. Message: "{trigger_message[:200]}"',
                            'due_date': 'now() + interval \'1 hour\'',  # 1 hour to respond
                            'priority': 'high',
                            'status': 'pending',
                            'task_type': 'customer_support'
                        }
                        
                        task_result = supabase.client.table('tasks').insert(task_data).execute()
                        if task_result.data:
                            logger.info(f"📋 CRM TASK - Created follow-up task: {task_result.data[0]['id']}")
                    
                except Exception as lead_error:
                    logger.warning(f"🎯 CRM LEAD - Failed to create lead: {lead_error}")
                
                # Log activity in CRM
                try:
                    activity_data = {
                        'contact_id': contact_id,
                        'activity_type': 'support_request',
                        'title': 'Human Support Requested',
                        'description': f'Customer requested to speak with human agent. Bot disabled for conversation. Trigger: "{trigger_message[:200]}"',
                        'metadata': {
                            'phone_number': base_phone,
                            'trigger_message': trigger_message,
                            'handover_source': 'whatsapp',
                            'bot_disabled': True
                        }
                    }
                    
                    activity_result = supabase.client.table('activities').insert(activity_data).execute()
                    if activity_result.data:
                        logger.info(f"📊 CRM ACTIVITY - Logged handover activity: {activity_result.data[0]['id']}")
                
                except Exception as activity_error:
                    logger.warning(f"📊 CRM ACTIVITY - Failed to log activity: {activity_error}")
                    
                # Update contact with latest interaction
                try:
                    contact_updates = {
                        'last_contacted_at': 'now()',
                        'lead_status': 'qualified',  # Escalate status
                        'lead_score': min((contact.get('lead_score', 0) or 0) + 25, 100),
                        'notes': f"Requested human support on {trigger_message[:100]}..." if not contact.get('notes') else contact['notes'] + f"\n[{trigger_message[:100]}...] - Human support requested"
                    }
                    
                    contact_update_result = supabase.client.table('contacts')\
                        .update(contact_updates)\
                        .eq('id', contact_id)\
                        .execute()
                    
                    if contact_update_result.data:
                        logger.info(f"👤 CRM CONTACT - Updated contact profile after handover")
                
                except Exception as contact_error:
                    logger.warning(f"👤 CRM CONTACT - Failed to update contact: {contact_error}")
            
        except Exception as crm_error:
            logger.warning(f"🏢 CRM INTEGRATION - CRM integration failed (continuing with handover): {crm_error}")
        
        # 3. Disable bot for this conversation
        # Clean phone number format for database lookup
        base_phone = phone_number.replace('@s.whatsapp.net', '').replace('_s_whatsapp_net', '')
        
        # Since we cleaned up duplicates, we should have only one conversation per phone number
        # Try the most common format first: base phone number
        logger.info(f"🔍 HANDOVER DEBUG - Looking for conversation with phone: {base_phone}")
        
        conversation_result = supabase.client.table('conversations')\
            .select('id, contacts!inner(phone_number)')\
            .eq('contacts.phone_number', base_phone)\
            .execute()
        
        if conversation_result.data:
            conversation_id = conversation_result.data[0]['id']
            logger.info(f"🤝 HANDOVER REQUEST - Found conversation ID: {conversation_id}")
            
            # Update conversation to disable bot
            update_result = supabase.client.table('conversations')\
                .update({
                    'bot_enabled': False,
                    'handover_requested': True,
                    'handover_timestamp': 'now()',
                    'handover_reason': trigger_message[:500],
                    'updated_at': 'now()'
                })\
                .eq('id', conversation_id)\
                .execute()
            
            logger.info(f"🔍 HANDOVER DEBUG - Updated conversation {conversation_id}: {len(update_result.data) if update_result.data else 0} rows affected")
        else:
            logger.warning(f"🚨 HANDOVER ERROR - No conversation found for phone: {base_phone}")
            update_result = type('obj', (object,), {'data': []})
        
        logger.info(f"🤝 HANDOVER REQUEST - Bot disabled status: {len(update_result.data) if update_result.data else 0} conversations updated")
        
        # 4. Send confirmation message to user
        confirmation_message = """🙋‍♀️ I understand you'd like to speak with a human!

I've switched off the automatic responses so our team can take over this conversation. One of our representatives will respond to you shortly.

✅ Bot mode: OFF
👥 Human mode: ON
🔔 High priority support ticket created

Thank you for your patience! 🙏"""
        
        send_success, sent_message_id = send_complete_message(phone_number, confirmation_message)
        
        if send_success:
            # Track this message as bot-sent to prevent future webhook duplicates
            if sent_message_id:
                supabase.track_bot_sent_message(sent_message_id, phone_number)
                logger.info(f"🤝 HANDOVER REQUEST - Tracked bot message {sent_message_id} to prevent duplicates")
            
            # Save the confirmation message to conversation history
            supabase.save_message_with_status(
                phone_number=phone_number,
                message_content=confirmation_message,
                role='assistant',
                message_id=sent_message_id,
                status='sent'
            )
            
            logger.info(f"🤝 HANDOVER REQUEST - Handover confirmation sent successfully to {phone_number}")
        else:
            logger.warning(f"🤝 HANDOVER REQUEST - Failed to send confirmation message to {phone_number}, but bot is still disabled")
        
        # 5. Log handover event for admin notification (regardless of message send status)
        logger.info(f"🚨 ADMIN ALERT - Handover requested by {phone_number}. Trigger: {trigger_message[:100]}...")
        
        # IMPORTANT: Always return success if bot was disabled, even if WhatsApp message failed
        # This prevents the system from continuing with AI response generation
        if len(update_result.data) > 0:
            return True, f"Handover request processed successfully (bot disabled, lead created). Message sent: {send_success}"
        else:
            return False, "Failed to disable bot for handover"
            
    except Exception as e:
        logger.error(f"🤝 HANDOVER REQUEST - Error processing handover for {phone_number}: {e}")
        return False, f"Handover processing error: {str(e)}"

# ============================================================================
# MESSAGE VALIDATION FUNCTIONS
# ============================================================================

def is_self_sent_message(message_info: Dict) -> bool:
    """
    Check if the message was sent by the bot itself.
    Uses smart detection to distinguish between:
    - Bot-generated messages (should be ignored)  
    - Human agent messages (should be processed)
    
    Args:
        message_info: Message information from webhook
        
    Returns:
        True if message is from the bot, False otherwise
    """
    message_id = message_info.get('key', {}).get('id')
    from_me = message_info.get('key', {}).get('fromMe', False)
    remote_jid = message_info.get('key', {}).get('remoteJid', '')
    
    # If fromMe is False, it's definitely not self-sent
    if not from_me:
        return False
    
    # For fromMe=True messages, we need to distinguish between bot and human
    # Check if this is a tracked bot message
    supabase = get_supabase_manager()
    if supabase.is_connected():
        is_bot_message = supabase.is_bot_sent_message(message_id)
        if is_bot_message:
            logger.info(f"🤖 BOT MESSAGE DETECTED - Ignoring tracked bot message: {message_id}")
            return True
    
    # If it's fromMe=True but not a tracked bot message, it's likely a human agent message
    # Let the main processing logic handle it
    logger.info(f"👤 POTENTIAL HUMAN MESSAGE - Not blocking fromMe message: {message_id}")
    return False


def is_system_message(message_info: Dict) -> bool:
    """
    Check if the message is a system message (not user content).
    
    Args:
        message_info: Message information from webhook
        
    Returns:
        True if it's a system message, False otherwise
    """
    return bool(message_info.get('messageStubType'))


# ============================================================================
# MESSAGE CONTENT EXTRACTION
# ============================================================================

def extract_message_content(message_info: Dict) -> Tuple[Optional[str], str]:
    """
    Extract text content from WhatsApp message data.
    
    Args:
        message_info: Message information from webhook
        
    Returns:
        Tuple of (message_text, message_type)
    """
    message_text = None
    message_type = 'unknown'
    
    if message_info.get('message'):
        msg_content = message_info['message']
        
        # Handle regular conversation messages
        if 'conversation' in msg_content:
            message_text = msg_content['conversation']
            message_type = 'text'
            
        # Handle extended text messages (replies, mentions, etc.)
        elif 'extendedTextMessage' in msg_content and 'text' in msg_content['extendedTextMessage']:
            message_text = msg_content['extendedTextMessage']['text']
            message_type = 'text'
    
    return message_text, message_type


def is_bot_like_message(message_text: str) -> bool:
    """
    Check if message content suggests it was sent by the bot.
    
    Args:
        message_text: The message content to check
        
    Returns:
        True if message appears to be from bot, False otherwise
    """
    if not message_text:
        return False
    
    # Check for common bot signatures (be very aggressive to prevent duplicates)
    bot_signatures = [
        "AI Assistant from Rian Infotech",
        "How can I assist you today?",
        "feel free to let me know",
        "How can Rian Infotech help",
        "I'm here to help",
        "🚀",  # Rocket emoji commonly used by our bot
        "specialized in AI automation",
        "Let me know how I can assist",
        "Great to hear from you again!",
        "Since you're very interested in AI automation solutions",
        "I'd love to help you with",
        "What specific areas are you looking to focus on",
        "Hi my airtel!",
        "interested in AI automation solutions",
        "How can Rian Infotech assist you today",
        "regarding AI solutions for your business",
        "regarding our services"
    ]
    
    message_lower = message_text.lower()
    
    # AGGRESSIVE: Check for any message longer than 100 chars that mentions both "Rian Infotech" and "AI automation"
    if len(message_text) > 100 and "rian infotech" in message_lower and "ai automation" in message_lower:
        return True
    
    # AGGRESSIVE: Check for messages that mention "CTO at Rian Infotech" (very specific to bot responses)
    if "cto at rian infotech" in message_lower:
        return True
    for signature in bot_signatures:
        if signature.lower() in message_lower:
            return True
    
    return False


# ============================================================================
# MAIN MESSAGE PROCESSING
# ============================================================================

def process_incoming_message(message_info: Dict) -> Tuple[bool, str]:
    """
    Process an incoming WhatsApp message and generate response.
    
    Args:
        message_info: Message information from webhook
        
    Returns:
        Tuple of (success, status_message)
    """
    logger.info(f"🚀 MESSAGE PROCESSOR - Starting to process incoming message")
    
    # Extract sender information and message ID
    remote_jid = message_info.get('key', {}).get('remoteJid')
    message_id = message_info.get('key', {}).get('id')
    from_me = message_info.get('key', {}).get('fromMe', False)
    
    # DEBUG: Log the webhook payload structure
    logger.info(f"🔍 WEBHOOK DEBUG - Message ID: {message_id}, RemoteJid: {remote_jid}, FromMe: {from_me}")
    logger.info(f"🔍 WEBHOOK DEBUG - Full key structure: {message_info.get('key', {})}")
    
    if not remote_jid:
        return False, "Missing sender information"
    
    # Check for self-sent messages (prevent loops)
    logger.info(f"🔍 CHECKING SELF-SENT for message {message_id} with fromMe={from_me}")
    if is_self_sent_message(message_info):
        logger.info(f"✅ SELF-SENT DETECTED - Ignoring self-sent message: {message_id}")
        return True, "Self-sent message ignored"
    else:
        logger.info(f"❌ NOT SELF-SENT - Processing message {message_id}")
    
    # Handle system messages
    if is_system_message(message_info):
        stub_type = message_info.get('messageStubType')
        stub_params = message_info.get('messageStubParameters', [])
        logger.info(f"Received system message type {stub_type} from {remote_jid}: {stub_params}")
        return True, "System message processed"
    
    # Extract message content
    message_text, message_type = extract_message_content(message_info)
    
    if message_type != 'text' or not message_text:
        logger.info(f"Received non-text or empty message from {remote_jid}: type={message_type}")
        return True, "Non-text message ignored"
    
    # Get Supabase manager for enhanced message handling
    supabase = get_supabase_manager()
    
    # ENHANCED BOT MESSAGE DETECTION: Multiple checks to prevent loops
    # Check if this is a bot message that we should ignore to prevent duplicates
    is_bot_message = False
    if supabase.is_connected():
        is_bot_message = supabase.is_bot_sent_message(message_id)
    
    # Additional bot message detection: Check if message content matches recent bot responses
    if not is_bot_message and from_me:
        # For fromMe=true messages, also check if the content matches recent bot responses
        # This prevents processing bot messages that weren't properly tracked
        try:
            if supabase.is_connected():
                contact = supabase.get_or_create_contact(remote_jid)
                if contact:
                    # Check last few messages to see if this content was recently sent by assistant
                    result = supabase.client.table('conversations')\
                        .select('messages')\
                        .eq('contact_id', contact['id'])\
                        .execute()
                    
                    if result.data and result.data[0].get('messages'):
                        recent_messages = result.data[0]['messages'][-10:]  # Last 10 messages
                        for msg in recent_messages:
                            if (msg.get('role') == 'assistant' and 
                                msg.get('content', '').strip() == message_text.strip()):
                                logger.info(f"🤖 BOT CONTENT MATCH - Ignoring duplicate bot response: {message_id}")
                                return True, "Duplicate bot response ignored (content match)"
                            # Also check for partial matches (first 50 characters)
                            if (msg.get('role') == 'assistant' and len(message_text) > 50 and
                                msg.get('content', '')[:50].strip() == message_text[:50].strip()):
                                logger.info(f"🤖 BOT PARTIAL MATCH - Ignoring similar bot response: {message_id}")
                                return True, "Similar bot response ignored (partial match)"
        except Exception as e:
            logger.debug(f"Bot content check failed: {e}")
    
    # ADDITIONAL CHECK: If message starts with "Hi my airtel!" it's likely a bot response
    if from_me and message_text.startswith("Hi my airtel!"):
        logger.info(f"🤖 BOT PATTERN MATCH - Ignoring bot greeting pattern: {message_id}")
        return True, "Bot greeting pattern ignored"
    
    if is_bot_message:
        logger.info(f"🤖 BOT MESSAGE - Ignoring tracked bot message: {message_id}")
        return True, "Bot message ignored (duplicate prevention)"
    
    # Determine message role and conversation contact
    if from_me:
        # For fromMe=true messages that aren't bot messages, treat as incoming user messages
        # This handles the WASender configuration issue
        logger.info(f"🔧 WASENDER FIX - Treating fromMe=true as incoming user message: {message_id}")
        conversation_contact = remote_jid
        message_role = 'user'
        logger.info(f"Processing incoming message from {remote_jid}: {message_text}")
    else:
        # This is a properly formatted incoming message
        conversation_contact = remote_jid
        message_role = 'user'
        logger.info(f"Processing incoming message from {remote_jid}: {message_text}")
    
    # For outgoing human messages, we already saved them above and returned
    # The rest of this function handles incoming user messages
    
    # For incoming messages, continue with bot logic
    # ULTRA SAFETY: Check if identical content was recently sent by bot (prevent webhook duplicates)
    if message_text and supabase.is_connected():
        # Check if this exact content was recently sent as assistant message
        try:
            contact = supabase.get_or_create_contact(conversation_contact)
            if contact:
                result = supabase.client.table('conversations')\
                    .select('messages')\
                    .eq('contact_id', contact['id'])\
                    .execute()
                
                if result.data:
                    messages = result.data[0].get('messages', [])
                    # Check last 5 messages for duplicate content from assistant
                    for msg in messages[-5:]:
                        if (msg.get('role') == 'assistant' and 
                            msg.get('content') == message_text):
                            logger.warning(f"🚫 DUPLICATE DETECTED - Identical bot content found: {message_text[:50]}...")
                            return True, "Duplicate bot content blocked"
        except Exception as e:
            logger.error(f"Error checking for duplicates: {e}")
    
    # EXTRA SAFETY: Block bot-like content to prevent duplicates  
    bot_content_indicators = [
        "Bot mode: OFF",
        "Human mode: ON", 
        "I understand you'd like to speak with a human",
        "🎯 Thanks for your interest in our business solutions!",
        "I'd love to schedule a quick 15-minute discovery call",
        "Book your call here:",
        "calendly.com",
        "Looking forward to speaking with you! 🚀"
    ]
    
    if message_text and any(indicator in message_text for indicator in bot_content_indicators):
        logger.warning(f"🚫 CONTENT SAFETY - Blocking bot-like message content: {message_text[:50]}...")
        return True, "Bot-like content blocked as safety measure"
    
    # FIRST: Check for handover request (before bot enabled check so users can always request handover)
    logger.info(f"🔍 HANDOVER CHECK - Checking message: '{message_text}' from {conversation_contact}")
    
    # Get customer context for intelligent handover detection
    customer_context = {}
    try:
        if supabase.is_connected():
            contact = supabase.get_or_create_contact(conversation_contact)
            if contact and contact.get('enhanced_context'):
                customer_context = contact['enhanced_context']
                logger.debug(f"🔍 CUSTOMER CONTEXT - Retrieved context: {list(customer_context.keys())}")
    except Exception as e:
        logger.debug(f"Could not retrieve customer context: {e}")
    
    handover_needed = detect_user_handover_request(message_text, customer_context)
    logger.info(f"🔍 HANDOVER RESULT - Handover needed: {handover_needed}")
    
    if handover_needed:
        logger.info(f"🤝 HANDOVER TRIGGERED - Processing handover request from {conversation_contact}")
        return handle_user_handover_request(conversation_contact, message_text)
    else:
        logger.info(f"🤖 CONTINUING BOT - No handover needed, continuing with bot logic")
    
    # LEAD QUALIFICATION: Check if user is a qualified lead for discovery call
    logger.info(f"🎯 LEAD CHECK - Checking for lead qualification: '{message_text}' from {conversation_contact}")
    try:
        from src.services.lead_qualification_service import detect_and_process_qualified_lead
        
        # Get conversation history for context
        conversation_history = []
        if supabase.is_connected():
            history_data = supabase.load_conversation_history(conversation_contact)
            if history_data:
                conversation_history = [
                    {'role': msg.get('role', 'user'), 'content': msg.get('content', '')} 
                    for msg in history_data[-10:]  # Last 10 messages for context
                ]
        
        # Check for lead qualification
        lead_qualified, lead_message = detect_and_process_qualified_lead(
            message_text, conversation_contact, conversation_history
        )
        
        if lead_qualified:
            logger.info(f"🎯 LEAD QUALIFIED - {lead_message}")
            # Save the incoming message to history
            if supabase.is_connected():
                supabase.save_message_with_status(
                    phone_number=conversation_contact,
                    message_content=message_text,
                    role=message_role,
                    message_id=message_id,
                    status='received'
                )
            # Return early - Calendly message already sent, no need for AI response
            return True, "Qualified lead processed with Calendly invitation"
        else:
            logger.info(f"🎯 LEAD NOT QUALIFIED - {lead_message}")
            
    except Exception as lead_error:
        logger.warning(f"🎯 LEAD ERROR - Lead qualification failed: {lead_error}")
        # Continue with normal bot flow if lead qualification fails
    
    # SECOND: Check if bot is enabled for this conversation
    if not is_bot_enabled_for_sender(conversation_contact):
        logger.info(f"Bot is disabled for {conversation_contact} - human is handling conversation")
        # Still save the incoming message to history for tracking with message ID
        if supabase.is_connected():
            supabase.save_message_with_status(
                phone_number=conversation_contact,
                message_content=message_text,
                role=message_role,
                message_id=message_id,
                status='received'
            )
        else:
            # Fallback to old method
            safe_user_id = sanitize_user_id(conversation_contact)
            conversation_history = load_conversation_history(safe_user_id)
            conversation_history.append({
                'role': message_role, 
                'content': message_text,
                'message_id': message_id,
                'status': 'received'
            })
            save_conversation_history(safe_user_id, conversation_history)
        
        return True, "Bot disabled - human handling conversation"
    
    # DEBUG: Log bot response generation attempt
    logger.info(f"🤖 BOT RESPONSE - Starting AI response generation for {conversation_contact}: {message_text}")
    
    # Fetch customer context from CRM for personalized responses
    customer_context = None
    if supabase.is_connected():
        customer_context = supabase.get_customer_context_by_phone(conversation_contact)
        if customer_context:
            logger.info(f"Loaded customer context for {customer_context.get('name', conversation_contact)}: {customer_context.get('lead_status', 'new')} lead")
        else:
            logger.info(f"No customer context found for {conversation_contact}")
    
    # Load conversation history for AI context
    safe_user_id = sanitize_user_id(conversation_contact)
    conversation_history = load_conversation_history(safe_user_id)
    
    # Generate AI response with Enhanced Personalization + RAG + Context Tracking
    logger.info(f"🤖 BOT RESPONSE - Calling Enhanced AI handler for response generation")
    try:
        # Import Enhanced AI handler (includes RAG + Personalization + Context Tracking)
        logger.info(f"🔄 ENHANCED - Attempting to import enhanced AI handler...")
        from src.handlers.ai_handler_enhanced import generate_enhanced_ai_response
        logger.info(f"✅ ENHANCED - Successfully imported enhanced AI handler")
        
        logger.info(f"🎯 ENHANCED - Generating enhanced response with personalization...")
        ai_response = generate_enhanced_ai_response(message_text, conversation_history, customer_context)
        logger.info(f"✅ ENHANCED SUCCESS - Generated personalized response: {ai_response[:100]}...")
        
    except ImportError as e:
        # Fallback to RAG-only handler
        logger.error(f"❌ ENHANCED IMPORT FAILED - {e}")
        logger.warning(f"Enhanced handler not available ({e}), falling back to RAG handler")
        try:
            logger.info(f"🔄 RAG FALLBACK - Attempting to import RAG handler...")
            from src.handlers.ai_handler_rag import generate_ai_response_with_rag
            logger.info(f"✅ RAG FALLBACK - Successfully imported RAG handler")
            
            ai_response = generate_ai_response_with_rag(message_text, conversation_history, customer_context)
            logger.info(f"✅ RAG FALLBACK SUCCESS - Generated RAG-enhanced response: {ai_response[:100]}...")
            
        except ImportError as rag_e:
            # Final fallback to original AI handler
            logger.error(f"❌ RAG IMPORT FAILED - {rag_e}")
            logger.warning("RAG handler also not available, falling back to original AI handler")
            try:
                logger.info(f"🔄 BASIC FALLBACK - Attempting to import basic AI handler...")
                from src.handlers.ai_handler import generate_ai_response
                logger.info(f"✅ BASIC FALLBACK - Successfully imported basic AI handler")
                
                ai_response = generate_ai_response(message_text, conversation_history, customer_context)
                logger.info(f"✅ BASIC FALLBACK SUCCESS - Generated standard response: {ai_response[:100]}...")
                
            except Exception as basic_e:
                logger.error(f"❌ ALL HANDLERS FAILED - {basic_e}")
                ai_response = "I'm having trouble processing your request right now. Please try again in a moment."
                
    except Exception as e:
        # Catch any other errors in enhanced handler
        logger.error(f"❌ ENHANCED HANDLER ERROR - {e}")
        import traceback
        logger.error(f"Enhanced handler traceback: {traceback.format_exc()}")
        
        # Fallback to RAG
        try:
            logger.info(f"🔄 ERROR FALLBACK - Attempting RAG after enhanced error...")
            from src.handlers.ai_handler_rag import generate_ai_response_with_rag
            ai_response = generate_ai_response_with_rag(message_text, conversation_history, customer_context)
            logger.info(f"✅ ERROR FALLBACK SUCCESS - Generated RAG response after enhanced error")
        except Exception as fallback_e:
            logger.error(f"❌ ERROR FALLBACK FAILED - {fallback_e}")
            ai_response = "I'm having trouble processing your request right now. Please try again in a moment."
    
    if not ai_response:
        logger.error(f"🤖 BOT RESPONSE - AI response generation failed for {conversation_contact}")
        return False, "Failed to generate AI response"
    
    logger.info(f"🤖 BOT RESPONSE - AI response generated: {ai_response[:100]}...")
    
    # Send response
    logger.info(f"🤖 BOT RESPONSE - Sending response to {conversation_contact}")
    send_success, sent_message_id = send_complete_message(conversation_contact, ai_response)
    
    if send_success:
        logger.info(f"🤖 BOT RESPONSE - Message sent successfully with ID: {sent_message_id}")
        
        # IMPORTANT: Track this message ID as bot-sent IMMEDIATELY to prevent future loop processing
        # This must happen before saving to ensure webhook processing sees the tracking
        if sent_message_id and supabase.is_connected():
            track_success = supabase.track_bot_sent_message(sent_message_id, conversation_contact)
            logger.info(f"🤖 BOT TRACKING - Bot message tracking {'successful' if track_success else 'failed'}: {sent_message_id}")
            
            # Immediately verify the tracking worked
            verify_tracking = supabase.is_bot_sent_message(sent_message_id)
            logger.info(f"🔍 BOT TRACKING VERIFY - Tracking verification: {verify_tracking} for {sent_message_id}")
            
            # Also track with a small delay to handle potential webhook timing issues
            import time
            time.sleep(0.1)  # Small delay to ensure tracking is committed
            
            # Double-check tracking after delay
            verify_tracking_after = supabase.is_bot_sent_message(sent_message_id)
            logger.info(f"🔍 BOT TRACKING VERIFY AFTER - Tracking verification after delay: {verify_tracking_after} for {sent_message_id}")
        elif sent_message_id:
            # If no Supabase connection, use a simple in-memory set for this session
            global _session_bot_messages
            if '_session_bot_messages' not in globals():
                _session_bot_messages = set()
            _session_bot_messages.add(sent_message_id)
            logger.info(f"🤖 BOT TRACKING FALLBACK - Added to session tracking: {sent_message_id}")
        
        # Save both messages to history with enhanced status tracking
        if supabase.is_connected():
            # Save user message with received status
            supabase.save_message_with_status(
                phone_number=conversation_contact,
                message_content=message_text,
                role=message_role,
                message_id=message_id,
                status='received'
            )
            # Save assistant response with sent status and message ID
            supabase.save_message_with_status(
                phone_number=conversation_contact,
                message_content=ai_response,
                role='assistant',
                message_id=sent_message_id,  # Now we have the actual message ID
                status='sent'
            )
        else:
            # Fallback to old method with enhanced message structure
            conversation_history.append({
                'role': message_role, 
                'content': message_text,
                'message_id': message_id,
                'status': 'received'
            })
            conversation_history.append({
                'role': 'assistant', 
                'content': ai_response,
                'message_id': sent_message_id,
                'status': 'sent'
            })
            save_conversation_history(safe_user_id, conversation_history)
        
        return True, "Message processed successfully"
    else:
        logger.error(f"🤖 BOT RESPONSE - Failed to send response to {conversation_contact}")
        return False, "Failed to send response"


# ============================================================================
# BOT STATUS FUNCTIONS
# ============================================================================

def is_bot_enabled_for_sender(sender_number: str) -> bool:
    """
    Check if bot is enabled for a specific sender's conversation.
    
    Args:
        sender_number: WhatsApp number format (e.g., 917033009600@s.whatsapp.net)
        
    Returns:
        True if bot should respond, False if human is handling
    """
    try:
        supabase = get_supabase_manager()
        
        if not supabase.is_connected():
            logger.warning("Database not connected, defaulting to bot enabled")
            return True  # Default to enabled if DB unavailable
        
        # Clean phone number format for database lookup - try multiple formats
        base_phone = sender_number.replace('@s.whatsapp.net', '').replace('_s_whatsapp_net', '')
        
        # Try different formats that might be in the database
        phone_formats = [
            base_phone,  # 917033009600
            f"{base_phone}_s_whatsapp_net",  # 917033009600_s_whatsapp_net
            base_phone[2:] if base_phone.startswith('91') and len(base_phone) > 10 else base_phone,  # 7033009600 (without country code)
            base_phone[1:] if base_phone.startswith('9') and len(base_phone) > 10 else base_phone,  # Alternative country code removal
        ]
        
        # Remove duplicates while preserving order
        phone_formats = list(dict.fromkeys(phone_formats))
        
        # DEBUG: Log phone number conversion
        logger.info(f"🔍 BOT STATUS DEBUG - Original: {sender_number}, Base: {base_phone}, Trying formats: {phone_formats}")
        
        # DEBUG: Let's also check what conversations exist for debugging
        try:
            all_conversations = supabase.client.table('conversations')\
                .select('id, bot_enabled, contacts!inner(phone_number, name)')\
                .execute()
            logger.info(f"🔍 BOT STATUS DEBUG - Total conversations in DB: {len(all_conversations.data) if all_conversations.data else 0}")
            if all_conversations.data:
                for conv in all_conversations.data[:3]:  # Show first 3 for debugging
                    logger.info(f"🔍 BOT STATUS DEBUG - Sample conversation: phone={conv['contacts']['phone_number']}, bot_enabled={conv.get('bot_enabled', True)}")
        except Exception as debug_e:
            logger.error(f"🔍 BOT STATUS DEBUG - Error getting all conversations: {debug_e}")
        
        # Try each format until we find a match
        for phone_format in phone_formats:
            result = supabase.client.table('conversations')\
                .select('bot_enabled, contacts!inner(phone_number)')\
                .eq('contacts.phone_number', phone_format)\
                .execute()
            
            # DEBUG: Log database lookup result for each format
            logger.info(f"🔍 BOT STATUS DEBUG - Format {phone_format}: {len(result.data) if result.data else 0} results")
            
            if result.data:
                bot_enabled = result.data[0].get('bot_enabled', True)
                logger.info(f"🔍 BOT STATUS DEBUG - Found conversation with {phone_format}, bot_enabled: {bot_enabled}")
                return bot_enabled
        
        # No conversation found with any format - default to enabled for new conversations
        logger.info(f"🔍 BOT STATUS DEBUG - No conversation found for any format of {base_phone}, defaulting to enabled")
        return True
        
    except Exception as e:
        logger.error(f"Error checking bot status for {sender_number}: {e}")
        return True  # Default to enabled on error