"""
Enhanced AI Handler with RAG and Personalization
Combines RAG knowledge retrieval with advanced personalization
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime
import time

# Import existing components
from src.handlers.ai_handler import (
    initialize_openai_client, 
    get_tenant_openai_client,
    openai_client,
    PERSONA_DESCRIPTION
)

# Import RAG components
from src.services.rag_service import get_rag_service
from src.handlers.ai_handler_rag import (
    analyze_query_intent_with_rag,
    _add_discovery_call_guidance
)

# Import new personalization components
from src.services.enhanced_context_service import get_enhanced_context_service
from src.services.personalization_engine import get_personalization_engine

# Import analytics components
from src.services.analytics_service import get_analytics_service, MessageAnalytics

logger = logging.getLogger(__name__)

def generate_enhanced_ai_response(message_text: str, 
                                conversation_history: Optional[List[Dict[str, str]]] = None, 
                                customer_context: Optional[Dict] = None, 
                                tenant_id: str = None) -> str:
    """
    Generate AI response with full enhancement: RAG + Personalization + Context Tracking
    
    This is the most advanced response generation combining:
    1. Enhanced context tracking and journey analysis
    2. Personalized response strategies
    3. RAG knowledge retrieval
    4. Intent analysis and discovery call integration
    
    Args:
        message_text: The user's message
        conversation_history: Previous conversation context
        customer_context: Customer CRM information for personalization
        tenant_id: Tenant ID to use tenant-specific API key
        
    Returns:
        AI-generated response with full personalization and knowledge enhancement
    """
    start_time = time.time()
    
    # Get tenant-specific OpenAI client
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
        # Extract phone number for context tracking
        phone_number = customer_context.get('phone_number') if customer_context else None
        if not phone_number:
            logger.warning("No phone number provided for enhanced context tracking")
            # Fall back to RAG-only response
            from src.handlers.ai_handler_rag import generate_ai_response_with_rag
            return generate_ai_response_with_rag(message_text, conversation_history, customer_context, tenant_id)
        
        # Initialize services
        context_service = get_enhanced_context_service()
        personalization_engine = get_personalization_engine()
        rag_service = get_rag_service()
        analytics_service = get_analytics_service()
        
        # Initialize analytics tracking
        contact_id = customer_context.get('id') if customer_context else None
        session_id = None
        rag_docs_count = 0
        rag_query_time = 0
        
        # Step 1: Get and update enhanced customer context
        logger.info(f"🔍 ENHANCED - Retrieving context for {phone_number}")
        enhanced_context = context_service.get_enhanced_customer_context(phone_number)
        
        if not enhanced_context:
            logger.error(f"Failed to get enhanced context for {phone_number}")
            # Fall back to RAG-only response
            from src.handlers.ai_handler_rag import generate_ai_response_with_rag
            return generate_ai_response_with_rag(message_text, conversation_history, customer_context, tenant_id)
        
        # Step 2: Update context with current interaction
        logger.info(f"📊 ENHANCED - Analyzing and updating context")
        
        # Analyze journey stage progression
        new_journey_stage = context_service.analyze_and_update_journey_stage(
            phone_number, message_text, enhanced_context
        )
        enhanced_context.journey_stage = new_journey_stage
        
        # Update behavioral patterns
        context_service.update_behavioral_patterns(
            phone_number, message_text, response_time_seconds=None
        )
        
        # Extract and store business insights
        context_service.extract_and_store_insights(phone_number, message_text)
        
        # Increment interaction count
        context_service.increment_interaction_count(phone_number)
        
        # Update conversation state
        context_service.update_conversation_state(
            phone_number,
            current_topic=_extract_current_topic(message_text),
            add_question=_extract_question(message_text),
            context_update={"last_interaction": datetime.utcnow().isoformat()}
        )
        
        # Get updated context after all updates
        enhanced_context = context_service.get_enhanced_customer_context(phone_number)
        
        # Step 3: Generate personalization strategy
        logger.info(f"🎯 ENHANCED - Generating personalization strategy")
        personalization_strategy = personalization_engine.get_personalization_strategy(enhanced_context)
        
        # Step 4: Analyze query intent for RAG optimization
        logger.info(f"🧠 ENHANCED - Analyzing query intent")
        intent_analysis = analyze_query_intent_with_rag(message_text, customer_context)
        
        # Step 5: Retrieve relevant knowledge using RAG
        logger.info(f"📚 ENHANCED - Retrieving knowledge with RAG")
        rag_start_time = time.time()
        retrieved_docs = rag_service.query_knowledge_base(
            query=message_text,
            customer_context=customer_context,
            top_k=5
        )
        rag_query_time = int((time.time() - rag_start_time) * 1000)  # Convert to milliseconds
        rag_docs_count = len(retrieved_docs) if retrieved_docs else 0
        
        # Step 6: Build enhanced system prompt
        logger.info(f"✍️ ENHANCED - Building personalized system prompt")
        
        if retrieved_docs and len(retrieved_docs) > 0:
            # Start with RAG-enhanced prompt
            system_prompt = rag_service.get_contextual_prompt(
                query=message_text,
                retrieved_docs=retrieved_docs,
                customer_context=customer_context
            )
            response_type = "ENHANCED_RAG"
        else:
            # Fallback to personalized prompt without RAG
            system_prompt = _build_enhanced_fallback_prompt(enhanced_context)
            response_type = "ENHANCED_PERSONALIZED"
        
        # Add personalization guidance
        personalization_additions = personalization_engine.generate_personalized_prompt_additions(
            personalization_strategy, enhanced_context
        )
        system_prompt += personalization_additions
        
        # Add discovery call guidance if needed
        if intent_analysis.get('should_offer_discovery_call', False):
            system_prompt += _add_discovery_call_guidance(intent_analysis, customer_context)
        
        # Add conversation continuity
        conversation_state = context_service.get_conversation_state(phone_number)
        if conversation_state and conversation_state.unresolved_questions:
            system_prompt += f"\n\nCONVERSATION CONTINUITY:\n"
            system_prompt += f"- Previous unresolved questions: {', '.join(conversation_state.unresolved_questions)}\n"
            system_prompt += f"- Current topic context: {conversation_state.current_topic or 'General inquiry'}\n"
        
        # Step 7: Prepare conversation messages
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history with enhanced context awareness
        if conversation_history:
            # Limit history based on personalization level
            history_limit = _get_history_limit(personalization_strategy.personalization_level)
            for msg in conversation_history[-history_limit:]:
                if msg.get('role') and msg.get('content'):
                    messages.append({
                        "role": msg['role'],
                        "content": msg['content']
                    })
        
        # Add current user message
        messages.append({"role": "user", "content": message_text})
        
        # Step 8: Generate AI response with enhanced parameters
        logger.info(f"🤖 ENHANCED - Generating AI response")
        
        # Adjust model parameters based on personalization strategy
        model_params = _get_model_parameters(personalization_strategy)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            **model_params
        )
        
        # Step 9: Extract and process response
        if response and response.choices and len(response.choices) > 0:
            ai_response = response.choices[0].message.content.strip()
            
            # Post-process response based on personalization strategy
            ai_response = _post_process_response(ai_response, personalization_strategy, enhanced_context)
            
            # Log comprehensive response generation info
            end_time = time.time()
            response_time = int((end_time - start_time) * 1000)  # milliseconds
            
            logger.info(f"✅ ENHANCED SUCCESS - {response_type} response generated in {response_time}ms")
            logger.info(f"   📊 Context: Journey={enhanced_context.journey_stage}, Engagement={enhanced_context.engagement_level}")
            logger.info(f"   🎯 Strategy: {personalization_strategy.response_strategy.value} + {personalization_strategy.communication_style.value}")
            logger.info(f"   📚 RAG: {len(retrieved_docs)} docs retrieved (scores: {[f'{doc.score:.3f}' for doc in retrieved_docs[:3]]})")
            logger.info(f"   💬 Response: {ai_response[:100]}...")
            
            # Track comprehensive analytics
            try:
                # Create session if needed
                if contact_id:
                    session_id = analytics_service.get_or_create_session(
                        contact_id=contact_id,
                        phone_number=phone_number,
                        journey_stage=enhanced_context.journey_stage
                    )
                
                # Track message analytics for user message
                user_message_analytics = MessageAnalytics(
                    message_id=f"user_{int(time.time())}_{phone_number}",
                    contact_id=contact_id,
                    message_role="user",
                    message_content=message_text,
                    message_length=len(message_text),
                    detected_intents=intent_analysis.get('intents', []),
                    business_category=_detect_business_category(message_text, intent_analysis),
                    urgency_level=_detect_urgency_level(message_text),
                    processing_time_ms=response_time
                )
                analytics_service.track_message(user_message_analytics, session_id)
                
                # Track message analytics for bot response
                bot_message_analytics = MessageAnalytics(
                    message_id=f"bot_{int(time.time())}_{phone_number}",
                    contact_id=contact_id,
                    message_role="assistant",
                    message_content=ai_response,
                    message_length=len(ai_response),
                    ai_handler_used="enhanced",
                    rag_documents_retrieved=rag_docs_count,
                    rag_query_time_ms=rag_query_time,
                    personalization_level=personalization_strategy.personalization_level.value,
                    response_strategy=personalization_strategy.response_strategy.value,
                    communication_style=personalization_strategy.communication_style.value,
                    detected_intents=intent_analysis.get('intents', []),
                    business_category=_detect_business_category(message_text, intent_analysis),
                    urgency_level=personalization_strategy.urgency_level,
                    processing_time_ms=response_time,
                    token_count=_estimate_tokens(ai_response),
                    cost_estimate=_estimate_cost(ai_response)
                )
                analytics_service.track_message(bot_message_analytics, session_id)
                
                # Update conversation-level metrics
                analytics_service.update_conversation_metrics(
                    phone_number=phone_number,
                    engagement_score=_calculate_engagement_score(enhanced_context, personalization_strategy),
                    lead_score=enhanced_context.total_interactions * 10,  # Simple calculation
                    journey_stage=enhanced_context.journey_stage,
                    business_intent=intent_analysis.get('has_business_intent', False),
                    pricing_discussed=intent_analysis.get('has_pricing_intent', False),
                    demo_requested='demo' in intent_analysis.get('intents', [])
                )
                
                # Track performance metrics
                analytics_service.track_performance(
                    endpoint="ai_handler_enhanced",
                    operation_type="enhanced_ai_response",
                    execution_time_ms=response_time,
                    status="success",
                    model_used="gpt-4o-mini",
                    tokens_processed=_estimate_tokens(ai_response),
                    cost_incurred=_estimate_cost(ai_response),
                    contact_id=contact_id,
                    session_id=session_id,
                    metadata={
                        "response_type": response_type,
                        "rag_docs_retrieved": rag_docs_count,
                        "personalization_level": personalization_strategy.personalization_level.value,
                        "journey_stage": enhanced_context.journey_stage,
                        "engagement_level": enhanced_context.engagement_level
                    }
                )
                
            except Exception as analytics_error:
                logger.error(f"Analytics tracking failed: {analytics_error}")
                # Don't fail the response generation due to analytics issues
            
            return ai_response
        else:
            logger.error(f"OpenAI returned unexpected response: {response}")
            return "I received an unexpected response from my AI brain. Please try again."
            
    except Exception as e:
        logger.error(f"Error generating enhanced AI response: {e}")
        import traceback
        traceback.print_exc()
        
        # Graceful fallback to RAG-only response
        try:
            logger.info("🔄 FALLBACK - Attempting RAG-only response")
            from src.handlers.ai_handler_rag import generate_ai_response_with_rag
            return generate_ai_response_with_rag(message_text, conversation_history, customer_context, tenant_id)
        except Exception as fallback_error:
            logger.error(f"Fallback to RAG also failed: {fallback_error}")
            return "I'm having trouble processing your request right now. Please try again in a moment."

def _extract_current_topic(message_text: str) -> Optional[str]:
    """Extract the current topic from the message"""
    message_lower = message_text.lower()
    
    # Topic keywords mapping
    topic_keywords = {
        "pricing": ["price", "cost", "pricing", "package", "plan", "fee", "budget"],
        "implementation": ["implement", "setup", "install", "deploy", "integration"],
        "features": ["feature", "functionality", "capability", "what does", "how does"],
        "support": ["support", "help", "assistance", "problem", "issue"],
        "timeline": ["timeline", "when", "how long", "duration", "schedule"],
        "demo": ["demo", "demonstration", "show me", "example", "trial"],
        "comparison": ["compare", "versus", "vs", "alternative", "competitor"],
        "technical": ["technical", "api", "integration", "security", "compliance"]
    }
    
    for topic, keywords in topic_keywords.items():
        if any(keyword in message_lower for keyword in keywords):
            return topic
    
    return None

def _extract_question(message_text: str) -> Optional[str]:
    """Extract questions from the message"""
    # Simple question detection
    if "?" in message_text:
        # Extract the question part
        sentences = message_text.split(".")
        for sentence in sentences:
            if "?" in sentence:
                return sentence.strip()
    
    # Implicit question patterns
    question_starters = ["how", "what", "when", "where", "why", "can you", "do you", "is it", "are you"]
    message_lower = message_text.lower()
    
    for starter in question_starters:
        if message_lower.startswith(starter):
            return message_text
    
    return None

def _build_enhanced_fallback_prompt(context) -> str:
    """Build enhanced fallback prompt when RAG is not available"""
    base_prompt = PERSONA_DESCRIPTION
    
    enhanced_prompt = f"""You are the AI Assistant for Rian Infotech, specializing in AI automation solutions.

ENHANCED CUSTOMER CONTEXT:
- Customer: {context.name or 'Valued Customer'} from {context.company or 'their organization'}
- Journey Stage: {context.journey_stage}
- Engagement Level: {context.engagement_level}
- Total Interactions: {context.total_interactions}
- Conversation Count: {context.conversation_count}
- Topics Previously Discussed: {', '.join(context.topics_discussed) if context.topics_discussed else 'None'}
- Known Pain Points: {', '.join(context.pain_points_mentioned) if context.pain_points_mentioned else 'None'}
- Expressed Goals: {', '.join(context.goals_expressed) if context.goals_expressed else 'None'}
- Technical Level: {context.technical_level}
- Decision Maker: {'Yes' if context.decision_maker else 'No'}
- Budget Range: {context.budget_range or 'Unknown'}
- Timeline: {context.timeline or 'Unknown'}

RESPONSE GUIDELINES:
1. Use the customer's name and reference their company when appropriate
2. Build on previous conversation topics and context
3. Address their known pain points and goals
4. Adapt technical level to their preference
5. Reference their journey stage in your response approach
6. Be helpful, professional, and contextually relevant
"""
    
    return enhanced_prompt

def _get_history_limit(personalization_level) -> int:
    """Get conversation history limit based on personalization level"""
    from src.services.enhanced_context_service import PersonalizationLevel
    
    limit_map = {
        PersonalizationLevel.BASIC: 5,
        PersonalizationLevel.CONTEXTUAL: 8,
        PersonalizationLevel.RELATIONSHIP: 12,
        PersonalizationLevel.CLOSING: 15
    }
    
    return limit_map.get(personalization_level, 8)

def _get_model_parameters(strategy) -> Dict:
    """Get model parameters based on personalization strategy"""
    base_params = {
        "max_tokens": 1000,
        "temperature": 0.7
    }
    
    # Adjust based on communication style
    from src.services.personalization_engine import CommunicationStyle
    
    if strategy.communication_style == CommunicationStyle.TECHNICAL:
        base_params["temperature"] = 0.5  # More precise for technical content
        base_params["max_tokens"] = 1200   # Allow longer technical explanations
    elif strategy.communication_style == CommunicationStyle.CONVERSATIONAL:
        base_params["temperature"] = 0.8   # More creative for conversational tone
    elif strategy.communication_style == CommunicationStyle.FORMAL:
        base_params["temperature"] = 0.6   # Balanced for formal communication
    
    # Adjust based on personalization level
    from src.services.enhanced_context_service import PersonalizationLevel
    
    if strategy.personalization_level == PersonalizationLevel.CLOSING:
        base_params["max_tokens"] = 1200   # Allow longer closing responses
    elif strategy.personalization_level == PersonalizationLevel.BASIC:
        base_params["max_tokens"] = 800    # Keep basic responses concise
    
    return base_params

def _post_process_response(response: str, strategy, context) -> str:
    """Post-process response based on personalization strategy"""
    # Add personalized greeting if it's a new conversation
    if context.conversation_count <= 1 and context.name and not response.startswith(context.name):
        # Add name if not already present
        if context.name not in response:
            response = f"Hi {context.name}! " + response
    
    # Ensure call-to-action is appropriate
    if strategy.call_to_action_type == "schedule_call" and "calendly" not in response.lower():
        if not response.endswith(".") and not response.endswith("!") and not response.endswith("?"):
            response += "."
        response += "\n\n📅 Ready to discuss your specific needs? Book a free discovery call: https://calendly.com/rianinfotech/discovery-call"
    
    return response

# ========== ANALYTICS HELPER FUNCTIONS ==========

def _detect_business_category(message_text: str, intent_analysis: Dict) -> str:
    """Detect business category from message and intent analysis"""
    intents = intent_analysis.get('intents', [])
    message_lower = message_text.lower()
    
    if 'pricing' in intents or any(word in message_lower for word in ['price', 'cost', 'pricing', 'package']):
        return "pricing"
    elif any(word in message_lower for word in ['technical', 'api', 'integration', 'how does', 'requirements']):
        return "technical"
    elif any(word in message_lower for word in ['help', 'support', 'problem', 'issue', 'trouble']):
        return "support"
    elif any(word in message_lower for word in ['buy', 'purchase', 'demo', 'trial', 'meeting', 'call']):
        return "sales"
    else:
        return "general"

def _detect_urgency_level(message_text: str) -> str:
    """Detect urgency level from message content"""
    message_lower = message_text.lower()
    
    if any(word in message_lower for word in ['urgent', 'asap', 'immediately', 'emergency', 'critical']):
        return "urgent"
    elif any(word in message_lower for word in ['soon', 'quickly', 'fast', 'priority']):
        return "high"
    elif any(word in message_lower for word in ['when', 'timeline', 'deadline']):
        return "medium"
    else:
        return "low"

def _calculate_engagement_score(enhanced_context, personalization_strategy) -> float:
    """Calculate engagement score based on context and strategy"""
    base_score = 50.0  # Start with neutral engagement
    
    # Adjust based on interaction count
    if enhanced_context.total_interactions > 10:
        base_score += 20
    elif enhanced_context.total_interactions > 5:
        base_score += 10
    
    # Adjust based on journey stage
    stage_scores = {
        'discovery': 30,
        'interest': 50,
        'evaluation': 70,
        'decision': 90
    }
    base_score = stage_scores.get(enhanced_context.journey_stage, base_score)
    
    # Adjust based on engagement level
    if enhanced_context.engagement_level == 'high':
        base_score += 15
    elif enhanced_context.engagement_level == 'low':
        base_score -= 15
    
    # Adjust based on personalization strategy urgency
    if personalization_strategy.urgency_level == 'high':
        base_score += 10
    
    return min(100.0, max(0.0, base_score))

def _estimate_tokens(text: str) -> int:
    """Estimate token count for text (rough approximation)"""
    # Rough approximation: 1 token ≈ 4 characters for English text
    return len(text) // 4

def _estimate_cost(text: str) -> float:
    """Estimate cost for text processing (rough approximation)"""
    tokens = _estimate_tokens(text)
    # GPT-4o-mini pricing: roughly $0.00015 per 1K tokens for output
    return (tokens / 1000) * 0.00015

# Backwards compatibility function
def generate_ai_response_with_full_enhancement(message_text: str, 
                                             conversation_history: Optional[List[Dict[str, str]]] = None, 
                                             customer_context: Optional[Dict] = None, 
                                             tenant_id: str = None) -> str:
    """Alias for generate_enhanced_ai_response for backwards compatibility"""
    return generate_enhanced_ai_response(message_text, conversation_history, customer_context, tenant_id)