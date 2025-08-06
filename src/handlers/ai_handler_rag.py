import logging
from typing import List, Dict, Optional
from src.handlers.ai_handler import (
    initialize_openai_client, 
    get_tenant_openai_client,
    openai_client,
    PERSONA_DESCRIPTION
)
from src.services.rag_service import get_rag_service

logger = logging.getLogger(__name__)

def generate_ai_response_with_rag(message_text: str, 
                                 conversation_history: Optional[List[Dict[str, str]]] = None, 
                                 customer_context: Optional[Dict] = None, 
                                 tenant_id: str = None) -> str:
    """
    Generate AI response using RAG-enhanced knowledge
    Seamlessly integrates with existing customer personalization system
    
    Args:
        message_text: The user's message
        conversation_history: Previous conversation context
        customer_context: Customer CRM information for personalization
        tenant_id: Tenant ID to use tenant-specific API key
        
    Returns:
        AI-generated response text with business knowledge
    """
    # Get tenant-specific OpenAI client (existing functionality)
    if tenant_id:
        client, is_tenant_key = get_tenant_openai_client(tenant_id)
        if not client:
            return "Sorry, I'm having trouble connecting to my AI brain right now. Please check your OpenAI API key configuration."
    else:
        client = openai_client
        if not client:
            logger.error("OpenAI client not initialized")
            return "Sorry, I'm having trouble connecting to my AI brain right now (API key issue)."
    
    try:
        # Step 1: Analyze query intent for better response generation
        intent_analysis = analyze_query_intent_with_rag(message_text, customer_context)
        
        # Step 2: Retrieve relevant business knowledge using RAG
        rag_service = get_rag_service()
        retrieved_docs = rag_service.query_knowledge_base(
            query=message_text,
            customer_context=customer_context,
            top_k=5
        )
        
        # Step 3: Determine response strategy based on retrieval results and intent
        if retrieved_docs and len(retrieved_docs) > 0:
            # RAG-enhanced response with business knowledge
            system_prompt = rag_service.get_contextual_prompt(
                query=message_text,
                retrieved_docs=retrieved_docs,
                customer_context=customer_context
            )
            
            # Enhance prompt with discovery call guidance if needed
            if intent_analysis.get('should_offer_discovery_call', False):
                system_prompt += _add_discovery_call_guidance(intent_analysis, customer_context)
            
            response_type = "RAG_ENHANCED"
            logger.info(f"🧠 RAG ENHANCED - Using {len(retrieved_docs)} knowledge documents for response (scores: {[f'{doc.score:.3f}' for doc in retrieved_docs[:3]]})")
        else:
            # Fallback to original personalization if no relevant docs found
            system_prompt = _build_fallback_prompt(customer_context)
            response_type = "RAG_FALLBACK"
            logger.info("🧠 RAG FALLBACK - No relevant documents found, using personalized fallback")
        
        # Step 3: Prepare conversation messages (existing logic)
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history (existing functionality)
        if conversation_history:
            for msg in conversation_history[-10:]:  # Last 10 messages for context
                if msg.get('role') and msg.get('content'):
                    messages.append({
                        "role": msg['role'],
                        "content": msg['content']
                    })
        
        # Add current user message
        messages.append({"role": "user", "content": message_text})
        
        # Step 4: Generate AI response using existing OpenAI integration
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Using existing model choice
            messages=messages,
            max_tokens=1000,
            temperature=0.7
        )
        
        # Extract and return response
        if response and response.choices and len(response.choices) > 0:
            ai_response = response.choices[0].message.content.strip()
            
            # Enhanced logging with RAG information
            if customer_context and customer_context.get('name'):
                logger.info(f"🧠 {response_type} - Generated response for {customer_context['name']} ({customer_context.get('lead_status', 'unknown')} lead): {ai_response[:100]}...")
            else:
                logger.info(f"🧠 {response_type} - Generated response: {ai_response[:100]}...")
            
            # Log successful RAG usage for analytics
            if response_type == "RAG_ENHANCED":
                _log_successful_rag_response(message_text, customer_context, retrieved_docs, ai_response)
            
            return ai_response
        else:
            logger.error(f"OpenAI returned unexpected response: {response}")
            return "I received an unexpected response from my AI brain. Please try again."
            
    except Exception as e:
        logger.error(f"Error generating RAG-enhanced AI response: {e}")
        return "I'm having trouble processing your request right now. Please try again in a moment."

def _build_fallback_prompt(customer_context: Optional[Dict]) -> str:
    """
    Build fallback prompt when no RAG documents are retrieved
    Maintains existing personalization capabilities
    """
    base_prompt = PERSONA_DESCRIPTION
    
    if customer_context and customer_context.get('name'):
        customer_name = customer_context['name']
        company = customer_context.get('company', '')
        lead_status = customer_context.get('lead_status', 'new')
        industry = customer_context.get('industry', '')
        
        # Enhanced fallback with more context
        personalized_prompt = f"""You are the AI Assistant for Rian Infotech, specializing in AI automation solutions.

CUSTOMER CONTEXT:
- Name: {customer_name}
- Company: {company}
- Industry: {industry}
- Lead Status: {lead_status}

RESPONSE GUIDELINES:
1. Address the customer by name: "{customer_name}"
2. Reference their company when relevant: "{company}"
3. Provide helpful information about AI automation solutions
4. For specific details about services, pricing, or technical requirements, offer to connect them with our team
5. Be professional, friendly, and personalized
6. Focus on understanding their needs and providing value

IMPORTANT: Since I don't have access to our detailed service catalog right now, I'll focus on understanding your needs and can connect you with our team for specific information about our solutions.
"""
        return personalized_prompt
    
    return base_prompt

def _add_discovery_call_guidance(intent_analysis: Dict, customer_context: Optional[Dict]) -> str:
    """
    Add discovery call guidance to the system prompt based on intent analysis
    """
    customer_name = customer_context.get('name', '') if customer_context else ''
    lead_status = customer_context.get('lead_status', 'new') if customer_context else 'new'
    
    guidance = "\n\n--- DISCOVERY CALL GUIDANCE ---\n"
    
    if intent_analysis.get('has_pricing_intent', False):
        if lead_status in ['new', 'contacted']:
            guidance += """
PRICING QUERY DETECTED - NEW LEAD:
- Acknowledge their pricing interest
- Explain that pricing depends on their specific needs
- Emphasize the value of a discovery call to provide accurate pricing
- Mention that most clients find the discovery call valuable even if they don't proceed
- Include the Calendly link: https://calendly.com/rianinfotech/discovery-call
- Provide pricing ranges from the knowledge base as reference
"""
        elif lead_status in ['qualified', 'hot']:
            guidance += """
PRICING QUERY DETECTED - QUALIFIED LEAD:
- Provide detailed pricing information from knowledge base
- Offer discovery call for custom solution design
- Emphasize ROI and business value
- Include the Calendly link: https://calendly.com/rianinfotech/discovery-call
"""
    
    if 'discovery_call' in intent_analysis.get('intents', []):
        guidance += """
DISCOVERY CALL REQUEST DETECTED:
- Enthusiastically confirm the discovery call option
- Explain what they'll get from the call
- Provide the Calendly link: https://calendly.com/rianinfotech/discovery-call
- Mention the call is free and typically takes 30-45 minutes
"""
    
    guidance += f"""
PERSONALIZATION:
- Use customer name: "{customer_name}" if available
- Current lead status: {lead_status}
- Tailor the discovery call pitch to their status level

CALENDLY LINK FORMAT:
Always format as: "📅 Book your free discovery call: https://calendly.com/rianinfotech/discovery-call"
"""
    
    return guidance

def analyze_query_intent_with_rag(message_text: str, customer_context: Optional[Dict] = None) -> Dict[str, any]:
    """
    Analyze user query to determine intent and optimize RAG retrieval
    Enhanced with customer context for better intent detection
    """
    # Base intent categories
    intents = {
        'pricing': ['price', 'cost', 'pricing', 'package', 'plan', 'fee', 'budget', 'expensive', 'cheap', 'how much', 'quote'],
        'discovery_call': ['discovery', 'consultation', 'call', 'meeting', 'demo', 'discuss', 'talk', 'schedule'],
        'services': ['service', 'solution', 'automation', 'AI', 'what do you do', 'offerings', 'capabilities'],
        'technical': ['API', 'integration', 'technical', 'requirements', 'how does it work', 'implementation'],
        'company': ['about', 'team', 'experience', 'who are you', 'company', 'background'],
        'support': ['help', 'support', 'problem', 'issue', 'trouble', 'assistance'],
        'industry_specific': ['healthcare', 'finance', 'retail', 'manufacturing', 'education'],
        'lead_qualification': ['interested', 'demo', 'trial', 'consultation', 'meeting', 'call']
    }
    
    detected_intents = []
    message_lower = message_text.lower()
    
    for intent, keywords in intents.items():
        if any(keyword in message_lower for keyword in keywords):
            detected_intents.append(intent)
    
    # Enhance with customer context
    context_insights = {}
    if customer_context:
        lead_status = customer_context.get('lead_status', 'new')
        industry = customer_context.get('industry', '')
        
        # Adjust intent priorities based on lead status
        if lead_status in ['qualified', 'hot'] and 'pricing' in detected_intents:
            context_insights['priority_intent'] = 'pricing'
        elif lead_status == 'new' and 'services' in detected_intents:
            context_insights['priority_intent'] = 'services'
        
        # Add industry context
        if industry and industry.lower() in message_lower:
            detected_intents.append('industry_specific')
            context_insights['industry_focus'] = industry
    
    # Check for pricing-related queries that should trigger discovery call flow
    pricing_triggers = ['how much', 'what does it cost', 'pricing', 'price', 'budget', 'quote', 'cost', 'fee']
    has_pricing_intent = any(trigger in message_lower for trigger in pricing_triggers)
    
    # Determine if discovery call should be offered
    should_offer_discovery_call = (
        has_pricing_intent or 
        'discovery_call' in detected_intents or 
        'lead_qualification' in detected_intents
    )
    
    return {
        'intents': detected_intents,
        'primary_intent': detected_intents[0] if detected_intents else 'general',
        'confidence': len(detected_intents) / len(intents) if detected_intents else 0.1,
        'context_insights': context_insights,
        'has_pricing_intent': has_pricing_intent,
        'should_offer_discovery_call': should_offer_discovery_call,
        'rag_optimization': {
            'should_use_rag': len(detected_intents) > 0,
            'preferred_categories': _map_intents_to_categories(detected_intents),
            'search_enhancement': _generate_search_enhancement(detected_intents, customer_context)
        }
    }

def _map_intents_to_categories(intents: List[str]) -> List[str]:
    """Map detected intents to knowledge base categories"""
    intent_to_category = {
        'pricing': ['services', 'pricing'],
        'services': ['services'],
        'technical': ['technical', 'services'],
        'company': ['company'],
        'support': ['support', 'technical'],
        'industry_specific': ['industries'],
        'lead_qualification': ['sales', 'services']
    }
    
    categories = set()
    for intent in intents:
        if intent in intent_to_category:
            categories.update(intent_to_category[intent])
    
    return list(categories)

def _generate_search_enhancement(intents: List[str], customer_context: Optional[Dict]) -> str:
    """Generate additional search terms to enhance RAG retrieval"""
    enhancements = []
    
    # Add intent-specific enhancements
    if 'pricing' in intents:
        enhancements.extend(['cost', 'package', 'pricing'])
    if 'technical' in intents:
        enhancements.extend(['implementation', 'integration', 'API'])
    if 'industry_specific' in intents and customer_context:
        industry = customer_context.get('industry')
        if industry:
            enhancements.append(industry)
    
    return ' '.join(enhancements)

def _log_successful_rag_response(query: str, customer_context: Optional[Dict], 
                               retrieved_docs: List, response: str):
    """Log successful RAG responses for analytics and improvement"""
    try:
        # This could be expanded to include more detailed analytics
        logger.info(f"RAG SUCCESS - Query: {query[:50]}..., Docs: {len(retrieved_docs)}, Response Length: {len(response)}")
        
        # Could add database logging here for detailed analytics
        # self.supabase.log_rag_success(query, customer_context, retrieved_docs, response)
        
    except Exception as e:
        logger.warning(f"Failed to log RAG success: {e}")

# Backward compatibility function
def generate_ai_response_enhanced(message_text: str, 
                                conversation_history: Optional[List[Dict[str, str]]] = None, 
                                customer_context: Optional[Dict] = None, 
                                tenant_id: str = None) -> str:
    """
    Backward compatibility wrapper - calls RAG-enhanced version
    """
    return generate_ai_response_with_rag(message_text, conversation_history, customer_context, tenant_id) 