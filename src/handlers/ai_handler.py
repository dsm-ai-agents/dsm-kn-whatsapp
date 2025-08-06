"""
WhatsApp AI Chatbot - AI Handler
===============================
Handles OpenAI API integration, response generation,
and AI configuration management with multi-tenant support.

Author: Rian Infotech
Version: 2.3 (Multi-Tenant SaaS)
"""

import logging
from typing import List, Dict, Optional, Tuple
from openai import OpenAI

# Import configuration
from src.config.config import OPENAI_API_KEY
from src.config.persona_manager import load_bot_persona
from src.core.supabase_client import get_supabase_manager
from src.utils.encryption import decrypt_api_key

# Configure logging
logger = logging.getLogger(__name__)

# ============================================================================
# OPENAI CLIENT INITIALIZATION
# ============================================================================

# Global OpenAI client (fallback for system tenant)
openai_client = None

def initialize_openai_client() -> None:
    """Initialize the global OpenAI client with system API key."""
    global openai_client
    
    if OPENAI_API_KEY:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        logger.info("Global OpenAI client initialized successfully")
    else:
        logger.warning("OPENAI_API_KEY not found - only tenant keys will work")
        openai_client = None

def get_tenant_openai_client(tenant_id: str) -> Tuple[OpenAI, bool]:
    """
    Get OpenAI client for a specific tenant.
    Returns (client, is_tenant_key) tuple.
    """
    try:
        # Try to get tenant's OpenAI API key
        supabase = get_supabase_manager()
        result = supabase.supabase.table('tenant_api_keys').select('encrypted_key').eq(
            'tenant_id', tenant_id
        ).eq('key_type', 'openai').eq('is_active', True).limit(1).execute()
        
        if result.data:
            # Use tenant's API key
            encrypted_key = result.data[0]['encrypted_key']
            decrypted_key = decrypt_api_key(encrypted_key)
            
            # Update last_used_at
            supabase.supabase.table('tenant_api_keys').update({
                'last_used_at': 'now()'
            }).eq('tenant_id', tenant_id).eq('key_type', 'openai').execute()
            
            tenant_client = OpenAI(api_key=decrypted_key)
            logger.info(f"Using tenant-specific OpenAI key for tenant {tenant_id}")
            return tenant_client, True
        
        else:
            # Fall back to global client
            if openai_client:
                logger.info(f"Using global OpenAI key for tenant {tenant_id} (no tenant key found)")
                return openai_client, False
            else:
                logger.error(f"No OpenAI key available for tenant {tenant_id}")
                return None, False
                
    except Exception as e:
        logger.error(f"Error getting tenant OpenAI client: {e}", exc_info=True)
        # Fall back to global client
        if openai_client:
            return openai_client, False
        return None, False

def is_openai_configured(tenant_id: str = None) -> bool:
    """Check if OpenAI is properly configured for a tenant."""
    if tenant_id:
        client, _ = get_tenant_openai_client(tenant_id)
        return client is not None
    return openai_client is not None

# Initialize global client on module import
initialize_openai_client()

# Load persona
_, PERSONA_DESCRIPTION = load_bot_persona()

# ============================================================================
# AI RESPONSE GENERATION
# ============================================================================

def generate_ai_response(message_text: str, conversation_history: Optional[List[Dict[str, str]]] = None, 
                        customer_context: Optional[Dict] = None, tenant_id: str = None) -> str:
    """
    Generate AI response using OpenAI API with customer context and tenant-specific API keys.
    
    Args:
        message_text: The user's message
        conversation_history: Previous conversation context
        customer_context: Customer CRM information for personalization
        tenant_id: Tenant ID to use tenant-specific API key
        
    Returns:
        AI-generated response text
    """
    # Get tenant-specific OpenAI client
    if tenant_id:
        client, is_tenant_key = get_tenant_openai_client(tenant_id)
        if not client:
            return "Sorry, I'm having trouble connecting to my AI brain right now. Please check your OpenAI API key configuration."
        
        if is_tenant_key:
            logger.info(f"🔑 Using tenant API key for {tenant_id}")
        else:
            logger.info(f"🔑 Using fallback global API key for {tenant_id}")
    else:
        # Use global client for backward compatibility
        client = openai_client
        if not client:
            logger.error("OpenAI client not initialized")
            return "Sorry, I'm having trouble connecting to my AI brain right now (API key issue)."
    
    try:
        # Prepare messages for OpenAI API
        messages = []
        
        # Enhanced system prompt with customer context
        system_prompt = PERSONA_DESCRIPTION
        
        if customer_context and customer_context.get('name'):
            # Create a highly personalized system prompt override
            customer_name = customer_context['name']
            customer_company = customer_context.get('company', '')
            customer_position = customer_context.get('position', '')
            lead_status = customer_context.get('lead_status', 'new')
            notes = customer_context.get('notes', '')
            
            # Override the system prompt with EXTREMELY personalized instructions
            system_prompt = f"""You are the AI Assistant for Rian Infotech, a company specializing in AI automation solutions.

🚨 ABSOLUTE MANDATORY PERSONALIZATION REQUIREMENTS 🚨

CUSTOMER YOU ARE TALKING TO RIGHT NOW:
- Name: {customer_name}
- Company: {customer_company}  
- Position: {customer_position}
- Lead Status: {lead_status}
- Notes: {notes}

🎯 CRITICAL RESPONSE FORMAT - YOU MUST FOLLOW THIS EXACTLY:

STEP 1: MANDATORY GREETING
- You MUST start with "Hi {customer_name}!" or "Hello {customer_name}!"
- NEVER use generic greetings like "Hi!" or "Hello there!"

STEP 2: PERSONALIZED ACKNOWLEDGMENT
- Reference their company: "{customer_company}"
- Acknowledge their role: "as the {customer_position}"
- Show you remember them: "Great to hear from you again!" (for qualified/hot leads)

EXAMPLE CORRECT RESPONSE FORMAT:
"Hi {customer_name}! Great to hear from you again! I see you're the {customer_position} at {customer_company}. Since you're very interested in AI automation solutions, I'd love to help you with..."

🚨 WHAT YOU MUST NEVER DO:
- NEVER start with generic "Hi!" or "Hello!"
- NEVER ignore their name, company, or position
- NEVER give generic responses

LEAD STATUS SPECIFIC APPROACH:
- qualified lead: "Great to hear from you again!" + focus on their specific interests
- hot lead: Be extra responsive and prioritize their needs
- existing customer: Provide excellent ongoing support

PERSONALITY: Professional, helpful, knowledgeable about AI automation, and ALWAYS personalized.

⚠️ CRITICAL: If you fail to personalize this response with {customer_name}'s name and {customer_company}, you have failed completely. This is not optional."""
            
            logger.info(f"🔄 ULTRA-PERSONALIZED SYSTEM PROMPT for {customer_name}")
        
        # Add system prompt
        messages.append({"role": "system", "content": system_prompt})
        
        # Add few-shot example for personalization if customer context exists
        if customer_context and customer_context.get('name'):
            customer_name = customer_context['name']
            customer_company = customer_context.get('company', '')
            customer_position = customer_context.get('position', '')
            
            # Add example of correct personalized response
            messages.append({
                "role": "user", 
                "content": "Hi, I need help with my business"
            })
            messages.append({
                "role": "assistant", 
                "content": f"Hi {customer_name}! Great to hear from you again! I see you're the {customer_position} at {customer_company}. I'd be happy to help you with your business needs. What specific area would you like assistance with today?"
            })
            
            logger.info(f"✅ Added personalization example for {customer_name}")
        
        # Add conversation history if available
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add current user message
        messages.append({"role": "user", "content": message_text})
        
        # Log context usage and system prompt for debugging
        logger.info(f"DEBUG: Customer context received: {customer_context}")
        if customer_context and customer_context.get('name'):
            logger.info(f"✅ PERSONALIZATION ACTIVE: Generating AI response for {customer_context['name']} ({customer_context.get('lead_status', 'unknown')} lead): {message_text[:100]}...")
            logger.info(f"System prompt length with context: {len(system_prompt)} characters")
        else:
            logger.info(f"❌ NO PERSONALIZATION: Generating generic AI response: {message_text[:100]}...")
            if customer_context:
                logger.info(f"Customer context exists but missing name: {customer_context.keys()}")
            else:
                logger.info(f"No customer context available")
        
        # Call OpenAI API with tenant-specific client
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Cost-effective model
            messages=messages,
            max_tokens=1000,
            temperature=0.7
        )
        
        # Extract and return response
        if response and response.choices and len(response.choices) > 0:
            ai_response = response.choices[0].message.content.strip()
            
            # Log personalized response
            if customer_context and customer_context.get('name'):
                logger.info(f"Generated personalized response for {customer_context['name']}: {ai_response[:100]}...")
            else:
                logger.info(f"Generated AI response: {ai_response[:100]}...")
            
            return ai_response
        else:
            logger.error(f"OpenAI returned unexpected response: {response}")
            return "I received an unexpected response from my AI brain. Please try again."

    except Exception as e:
        logger.error(f"Error calling OpenAI API: {e}", exc_info=True)
        return "I'm having trouble processing that request. Please try again later." 
    # df