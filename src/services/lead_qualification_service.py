"""
Lead Qualification & Calendly Integration Service
================================================
AI-powered lead qualification system that automatically identifies potential
leads from user messages and sends Calendly discovery meeting links.

Author: AI Assistant
Version: 1.0
"""

import logging
import json
from typing import Dict, Tuple, Optional
from datetime import datetime

# Core imports
from src.core.supabase_client import get_supabase_manager
from src.handlers.whatsapp_handler import send_complete_message

# Configuration imports
from src.config.config import (
    LEAD_QUALIFICATION_CONFIDENCE_THRESHOLD,
    LEAD_QUALIFICATION_ENABLED,
    LEAD_QUALIFICATION_MODEL,
    LEAD_QUALIFICATION_LOGGING_ENABLED,
    CALENDLY_DISCOVERY_CALL_URL,
    CALENDLY_AUTO_SEND_ENABLED,
    CALENDLY_COOLDOWN_HOURS,
    QUALIFIED_LEAD_MIN_SCORE,
    DISCOVERY_CALL_LEAD_SCORE_BOOST
)

# Configure logging
logger = logging.getLogger(__name__)

# ============================================================================
# AI LEAD QUALIFICATION FUNCTIONS
# ============================================================================

def analyze_lead_qualification_ai(message_text: str, conversation_history: Optional[list] = None) -> tuple[bool, float, str, dict]:
    """
    AI-powered analysis to determine if user is a qualified lead for discovery call.
    
    Args:
        message_text: The user's message content
        conversation_history: Previous conversation context (optional)
        
    Returns:
        Tuple of (is_qualified_lead, confidence_score, reason, lead_metadata)
    """
    logger.info(f"🎯 LEAD AI - Starting lead qualification analysis for: '{message_text}'")
    
    # Enhanced filtering for basic messages
    if not message_text or len(message_text.strip()) < 5:
        logger.info(f"🎯 LEAD AI - Message too short for lead analysis")
        return False, 0.0, "Message too short", {}
    
    # Filter out simple greetings and basic responses
    simple_patterns = [
        'hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening',
        'thanks', 'thank you', 'ok', 'okay', 'yes', 'no', 'sure', 'fine',
        'how are you', 'what\'s up', 'wassup', 'sup', 'hola', 'namaste'
    ]
    
    message_lower = message_text.lower().strip()
    if any(pattern in message_lower for pattern in simple_patterns) and len(message_text.strip()) < 20:
        logger.info(f"🎯 LEAD AI - Simple greeting detected, not qualifying: '{message_text}'")
        return False, 0.0, "Simple greeting - not business intent", {}
    
    # Require minimum conversation depth for new contacts
    if not conversation_history or len(conversation_history) < 3:
        logger.info(f"🎯 LEAD AI - Insufficient conversation history for lead qualification")
        return False, 0.0, "Insufficient conversation depth", {}
    
    try:
        from openai import OpenAI
        import os
        
        # Check if lead qualification is enabled
        if not LEAD_QUALIFICATION_ENABLED:
            logger.info("Lead qualification disabled")
            return False, 0.0, "Lead qualification disabled", {}
        
        # Initialize OpenAI client
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Build conversation context
        context = ""
        if conversation_history:
            recent_messages = conversation_history[-5:]  # Last 5 messages for context
            context = "\n".join([f"{'User' if msg.get('role') == 'user' else 'Bot'}: {msg.get('content', '')}" for msg in recent_messages])
        
        # Construct the lead qualification prompt
        prompt = f"""
Analyze this conversation to determine if the user is a GENUINELY QUALIFIED business lead for a discovery call.

Current message: "{message_text}"

Recent conversation context:
{context}

CRITICAL: Only qualify leads who demonstrate STRONG business intent. Be very selective.

REQUIRED for qualification (ALL must be present):
1. CLEAR BUSINESS INTENT:
   - Explicitly asking about business solutions/services
   - Discussing specific business problems or challenges
   - Asking about pricing for business use
   - Mentioning implementation or integration needs
   - Asking detailed questions about business features

2. BUSINESS CONTEXT:
   - Mentions their company, role, or industry
   - Discusses team or organizational needs
   - References current business tools/systems
   - Talks about business growth or scaling

3. BUYING SIGNALS:
   - Timeline questions ("when can we start", "how long")
   - Budget-related inquiries
   - Decision-making language ("we need", "looking for")
   - Comparison shopping ("vs competitors")
   - Implementation or trial questions

4. CONVERSATION DEPTH:
   - Has asked multiple substantive questions
   - Provided specific business context
   - Engaged beyond basic information gathering
   - Shows serious interest in business solutions

AUTOMATICALLY EXCLUDE:
- Simple greetings (hi, hello, hey)
- General information seekers without business context
- Personal/consumer use inquiries
- Basic support questions
- One-word or very short responses
- Casual browsers without specific needs
- Students or researchers (unless for business)

QUALIFICATION LEVELS:
- HIGH (85-100): Multiple strong business indicators + clear buying signals + detailed engagement
- MEDIUM (70-84): Some business context + decent engagement + mild buying signals
- LOW (50-69): Limited business indicators with minimal engagement
- NOT_QUALIFIED (0-49): No clear business intent or insufficient context

Respond in this exact JSON format:
{{
  "is_qualified_lead": true/false,
  "confidence": 0.0-1.0,
  "lead_quality": "HIGH/MEDIUM/LOW/NOT_QUALIFIED",
  "lead_score": 0-100,
  "reason": "brief explanation",
  "business_indicators": ["list", "of", "detected", "indicators"],
  "buying_signals": ["list", "of", "buying", "signals"],
  "recommended_action": "discovery_call/nurture/qualify_further/none"
}}

Be VERY selective - only recommend discovery calls for leads with confidence >{LEAD_QUALIFICATION_CONFIDENCE_THRESHOLD} AND clear business intent.
"""

        # Call OpenAI API
        response = client.chat.completions.create(
            model=LEAD_QUALIFICATION_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.2,  # Low temperature for consistent analysis
            response_format={"type": "json_object"}
        )
        
        # Parse the response
        result = json.loads(response.choices[0].message.content)
        
        is_qualified = result.get('is_qualified_lead', False)
        confidence = float(result.get('confidence', 0.0))
        reason = result.get('reason', 'No reason provided')
        
        # Extract metadata
        lead_metadata = {
            'lead_quality': result.get('lead_quality', 'NOT_QUALIFIED'),
            'lead_score': result.get('lead_score', 0),
            'business_indicators': result.get('business_indicators', []),
            'buying_signals': result.get('buying_signals', []),
            'recommended_action': result.get('recommended_action', 'none'),
            'analysis_timestamp': datetime.utcnow().isoformat()
        }
        
        # Log the analysis
        logger.info(f"🎯 LEAD AI - Message: '{message_text[:50]}...' | Qualified: {is_qualified} | Confidence: {confidence:.2f} | Quality: {lead_metadata['lead_quality']} | Score: {lead_metadata['lead_score']}")
        
        # Only mark as qualified if confidence is high enough and score meets minimum
        final_qualified = (
            is_qualified and 
            confidence >= LEAD_QUALIFICATION_CONFIDENCE_THRESHOLD and
            lead_metadata['lead_score'] >= QUALIFIED_LEAD_MIN_SCORE
        )
        
        # Log to Supabase for analytics
        if LEAD_QUALIFICATION_LOGGING_ENABLED:
            try:
                supabase = get_supabase_manager()
                if supabase.is_connected():
                    supabase.client.table('lead_qualification_log').insert({
                        'message_text': message_text,
                        'is_qualified_lead': is_qualified,
                        'confidence_score': confidence,
                        'lead_quality': lead_metadata['lead_quality'],
                        'lead_score': lead_metadata['lead_score'],
                        'business_indicators': lead_metadata['business_indicators'],
                        'buying_signals': lead_metadata['buying_signals'],
                        'recommended_action': lead_metadata['recommended_action'],
                        'final_decision': final_qualified,
                        'reason': reason,
                        'model_used': LEAD_QUALIFICATION_MODEL,
                        'created_at': 'now()'
                    }).execute()
            except Exception as log_error:
                logger.warning(f"Failed to log lead qualification: {log_error}")
        
        return final_qualified, confidence, reason, lead_metadata
        
    except Exception as e:
        logger.error(f"Lead qualification AI failed: {e}")
        return False, 0.0, f"AI analysis failed: {str(e)}", {}


def send_calendly_discovery_call(phone_number: str, lead_metadata: dict) -> tuple[bool, str]:
    """
    Send Calendly discovery call link to qualified lead.
    
    Args:
        phone_number: WhatsApp phone number
        lead_metadata: Lead qualification metadata
        
    Returns:
        Tuple of (success, status_message)
    """
    logger.info(f"📅 CALENDLY - Sending discovery call invitation to {phone_number}")
    
    try:
        if not CALENDLY_AUTO_SEND_ENABLED:
            logger.info("Calendly auto-send disabled")
            return False, "Auto-send disabled"
            
        if not CALENDLY_DISCOVERY_CALL_URL:
            logger.error("Calendly URL not configured")
            return False, "Calendly URL not configured"
        
        # Personalize message based on lead quality
        lead_quality = lead_metadata.get('lead_quality', 'MEDIUM')
        business_indicators = lead_metadata.get('business_indicators', [])
        
        # Create simple Calendly message for WhatsApp
        if lead_quality == 'HIGH':
            message = f"""🎯 Thanks for your interest in our business solutions!

I'd love to schedule a quick 15-minute discovery call to discuss your specific needs.

Book your call here: {CALENDLY_DISCOVERY_CALL_URL}

Looking forward to speaking with you! 🚀"""

        elif lead_quality == 'MEDIUM':
            message = f"""👋 Thanks for your interest!

I'd love to learn more about your needs. Would you like to schedule a brief 15-minute call?

Book here: {CALENDLY_DISCOVERY_CALL_URL}

No commitment required - just a conversation! 📅"""

        else:  # LOW quality
            message = f"""Thank you for your interest! 

Schedule a 15-minute consultation: {CALENDLY_DISCOVERY_CALL_URL}

Looking forward to connecting! 🤝"""
        
        # Send the message
        logger.info(f"📅 CALENDLY SENDING - About to send Calendly message to {phone_number}")
        logger.info(f"📅 CALENDLY MESSAGE - Message content: {message[:100]}...")
        
        success, sent_message_id = send_complete_message(phone_number, message)
        
        logger.info(f"📅 CALENDLY RESULT - Success: {success}, Result: {sent_message_id}")
        
        if success and sent_message_id:
            # CRITICAL: Track this message as bot-sent to prevent loop processing
            supabase = get_supabase_manager()
            if supabase.is_connected():
                track_success = supabase.track_bot_sent_message(sent_message_id, phone_number)
                logger.info(f"📅 CALENDLY TRACKING - Bot message tracking {'successful' if track_success else 'failed'}: {sent_message_id}")
                
                # Verify tracking worked
                import time
                time.sleep(0.1)  # Small delay to ensure tracking is committed
                verify_tracking = supabase.is_bot_sent_message(sent_message_id)
                logger.info(f"📅 CALENDLY VERIFY - Tracking verification: {verify_tracking} for {sent_message_id}")
                
                # EXTRA SAFEGUARD: Also save the message content to conversation history as assistant message
                # This provides an additional layer of protection against reprocessing
                try:
                    supabase.save_message_with_status(
                        phone_number=phone_number,
                        message_content=message,
                        role='assistant',
                        message_id=sent_message_id,
                        status='sent'
                    )
                    logger.info(f"📅 CALENDLY HISTORY - Saved Calendly message to conversation history")
                except Exception as save_error:
                    logger.warning(f"📅 CALENDLY HISTORY WARNING - Failed to save to history: {save_error}")
            
            logger.info(f"📅 CALENDLY SUCCESS - Discovery call invitation sent to {phone_number}")
            return True, "Discovery call invitation sent successfully"
        elif success:
            logger.warning(f"📅 CALENDLY WARNING - Message sent but no message ID returned")
            return True, "Discovery call invitation sent successfully (no ID)"
        else:
            logger.error(f"📅 CALENDLY ERROR - Failed to send invitation: {sent_message_id}")
            return False, f"Failed to send invitation: {sent_message_id}"
            
    except Exception as e:
        logger.error(f"📅 CALENDLY ERROR - Exception sending discovery call: {e}")
        return False, f"Exception: {str(e)}"


def handle_qualified_lead_process(phone_number: str, message_text: str, lead_metadata: dict) -> tuple[bool, str]:
    """
    Complete process for handling a qualified lead including CRM updates and Calendly invitation.
    
    Args:
        phone_number: WhatsApp phone number
        message_text: Original qualifying message
        lead_metadata: Lead qualification analysis results
        
    Returns:
        Tuple of (success, status_message)
    """
    logger.info(f"🎯 LEAD PROCESS - Starting qualified lead process for {phone_number}")
    
    try:
        supabase = get_supabase_manager()
        if not supabase.is_connected():
            logger.error("Supabase not connected for lead processing")
            return False, "Database connection failed"
        
        # 1. Get or create contact
        contact = supabase.get_or_create_contact(phone_number)
        if not contact:
            logger.error(f"Failed to create/get contact for {phone_number}")
            return False, "Contact creation failed"
        
        contact_id = contact['id']
        
        # 2. Update lead score and status (ensure max 100)
        current_score = contact.get('lead_score', 0) or 0
        new_score = min(current_score + DISCOVERY_CALL_LEAD_SCORE_BOOST, 100)
        
        # Update contact with new lead information
        supabase.client.table('contacts').update({
            'lead_score': new_score,
            'lead_status': 'qualified',  # Mark as qualified lead
            'last_contacted_at': 'now()',
            'discovery_call_requested': True,
            'source': 'whatsapp_qualification'
        }).eq('id', contact_id).execute()
        
        # 3. Create lead record if doesn't exist
        existing_lead = supabase.client.table('lead_details').select('*').eq('contact_id', contact_id).execute()
        
        if not existing_lead.data:
            # Create new lead
            supabase.client.table('lead_details').insert({
                'contact_id': contact_id,
                'lead_status': 'qualified',
                'lead_score': min(new_score, 100),
                'source': 'whatsapp_qualification',
                'priority': 'high' if lead_metadata.get('lead_quality') == 'HIGH' else 'medium',
                'qualification_trigger': message_text,
                'qualification_timestamp': 'now()',
                'business_indicators': lead_metadata.get('business_indicators', []),
                'buying_signals': lead_metadata.get('buying_signals', []),
                'lead_quality': lead_metadata.get('lead_quality'),
                'ai_confidence': lead_metadata.get('confidence', 0.0)
            }).execute()
        else:
            # Update existing lead
            supabase.client.table('lead_details').update({
                'lead_score': min(new_score, 100),
                'lead_status': 'qualified',
                'priority': 'high' if lead_metadata.get('lead_quality') == 'HIGH' else 'medium',
                'qualification_trigger': message_text,
                'qualification_timestamp': 'now()',
                'business_indicators': lead_metadata.get('business_indicators', []),
                'buying_signals': lead_metadata.get('buying_signals', []),
                'discovery_call_requested': True
            }).eq('contact_id', contact_id).execute()
        
        # 4. Log activity
        supabase.client.table('activities').insert({
            'contact_id': contact_id,
            'activity_type': 'lead_qualification',
            'title': 'Qualified Lead - Discovery Call Invited',
            'description': f'AI-qualified lead based on message: "{message_text[:100]}..."',
            'metadata': {
                'qualifying_message': message_text,
                'lead_quality': lead_metadata.get('lead_quality'),
                'lead_score': lead_metadata.get('lead_score'),
                'confidence': lead_metadata.get('confidence'),
                'business_indicators': lead_metadata.get('business_indicators', []),
                'buying_signals': lead_metadata.get('buying_signals', []),
                'calendly_url': CALENDLY_DISCOVERY_CALL_URL
            },
            'created_at': 'now()'
        }).execute()
        
        # 5. Send Calendly invitation
        calendly_success, calendly_message = send_calendly_discovery_call(phone_number, lead_metadata)
        
        if calendly_success:
            # 6. Log successful discovery call invitation
            supabase.client.table('activities').insert({
                'contact_id': contact_id,
                'activity_type': 'calendly_invitation',
                'title': 'Discovery Call Invitation Sent',
                'description': f'Calendly discovery call link sent for qualified lead (Quality: {lead_metadata.get("lead_quality", "UNKNOWN")})',
                'metadata': {
                    'calendly_url': CALENDLY_DISCOVERY_CALL_URL,
                    'lead_quality': lead_metadata.get('lead_quality'),
                    'invitation_type': 'auto_qualified'
                },
                'created_at': 'now()'
            }).execute()
            
            logger.info(f"🎯 LEAD SUCCESS - Complete qualified lead process completed for {phone_number}")
            return True, f"Qualified lead processed and discovery call invitation sent (Score: {new_score})"
        else:
            logger.warning(f"🎯 LEAD PARTIAL - Lead processed but Calendly failed: {calendly_message}")
            return True, f"Lead processed but invitation failed: {calendly_message}"
            
    except Exception as e:
        logger.error(f"🎯 LEAD ERROR - Exception in qualified lead process: {e}")
        return False, f"Lead process failed: {str(e)}"


# ============================================================================
# MAIN LEAD QUALIFICATION FUNCTION
# ============================================================================

def detect_and_process_qualified_lead(message_text: str, phone_number: str, conversation_history: Optional[list] = None) -> tuple[bool, str]:
    """
    Main function to detect qualified leads and process them for discovery calls.
    
    Args:
        message_text: User's message content
        phone_number: WhatsApp phone number
        conversation_history: Previous conversation context
        
    Returns:
        Tuple of (lead_qualified, status_message)
    """
    logger.info(f"🎯 LEAD ENTRY - Starting lead qualification for: '{message_text}' from {phone_number}")
    
    try:
        # FIRST: Check if Calendly invitation has already been sent to this contact
        supabase = get_supabase_manager()
        if supabase.is_connected():
            try:
                contact = supabase.get_or_create_contact(phone_number)
                if contact and contact.get('discovery_call_requested'):
                    logger.info(f"🎯 CALENDLY ALREADY SENT - Discovery call already requested for {phone_number}, skipping lead qualification")
                    return False, "Discovery call invitation already sent to this contact"
                    
                # Also check recent activities for Calendly invitations (configurable cooldown period)
                if contact:
                    from datetime import datetime, timedelta
                    cooldown_cutoff = (datetime.utcnow() - timedelta(hours=CALENDLY_COOLDOWN_HOURS)).isoformat()
                    
                    recent_calendly = supabase.client.table('activities')\
                        .select('*')\
                        .eq('contact_id', contact['id'])\
                        .eq('activity_type', 'calendly_invitation')\
                        .gte('created_at', cooldown_cutoff)\
                        .execute()
                    
                    if recent_calendly.data:
                        logger.info(f"🎯 CALENDLY RECENT - Recent Calendly invitation found for {phone_number} within {CALENDLY_COOLDOWN_HOURS}h cooldown, skipping lead qualification")
                        return False, f"Recent discovery call invitation already sent (within {CALENDLY_COOLDOWN_HOURS} hours)"
                        
            except Exception as check_error:
                logger.warning(f"🎯 CALENDLY CHECK WARNING - Failed to check existing invitations: {check_error}")
                # Continue with lead qualification if check fails
        
        # 1. AI Lead Qualification Analysis
        is_qualified, confidence, reason, metadata = analyze_lead_qualification_ai(message_text, conversation_history)
        
        logger.info(f"🎯 LEAD ANALYSIS - Qualified: {is_qualified} | Confidence: {confidence:.2f} | Quality: {metadata.get('lead_quality', 'UNKNOWN')} | Reason: {reason}")
        
        if is_qualified:
            # 2. Process the qualified lead
            logger.info(f"🎯 LEAD QUALIFIED - Processing qualified lead for {phone_number}")
            logger.info(f"🎯 LEAD METADATA - Quality: {metadata.get('lead_quality')}, Score: {metadata.get('lead_score')}")
            
            success, process_message = handle_qualified_lead_process(phone_number, message_text, metadata)
            
            logger.info(f"🎯 LEAD PROCESS RESULT - Success: {success}, Message: {process_message}")
            
            if success:
                return True, f"Qualified lead processed - {process_message}"
            else:
                return False, f"Lead qualification failed - {process_message}"
        else:
            logger.info(f"🎯 LEAD NOT QUALIFIED - No lead qualification needed: {reason}")
            return False, f"Not qualified for discovery call: {reason}"
            
    except Exception as e:
        logger.error(f"🎯 LEAD ERROR - Exception in lead qualification: {e}")
        return False, f"Lead qualification error: {str(e)}" 