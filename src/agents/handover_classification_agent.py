"""
Smart Handover Classification Agent
Uses AI to intelligently determine when customers actually want human help
vs asking questions that the bot should handle directly
"""

import json
import logging
from typing import Dict, Tuple
from openai import OpenAI

logger = logging.getLogger(__name__)

class HandoverClassificationAgent:
    def __init__(self, api_key: str = None):
        """Initialize the handover classification agent"""
        self.client = OpenAI(api_key=api_key) if api_key else None
        
    def should_trigger_handover(self, message_text: str, customer_context: Dict = None) -> Tuple[bool, str, float]:
        """
        Intelligently determine if a message is requesting human handover
        
        Args:
            message_text: The customer's message
            customer_context: Known information about the customer
            
        Returns:
            Tuple of (should_handover: bool, reason: str, confidence: float)
        """
        if not self.client:
            logger.warning("OpenAI client not initialized - falling back to keyword detection")
            return self._fallback_keyword_detection(message_text)
            
        try:
            # Prepare classification prompt
            classification_prompt = self._build_classification_prompt(message_text, customer_context)
            
            # Call OpenAI API for intelligent classification
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Fast and accurate for classification
                messages=[
                    {
                        "role": "system", 
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user", 
                        "content": classification_prompt
                    }
                ],
                temperature=0.1,  # Low temperature for consistent classification
                max_tokens=200,
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            result = json.loads(response.choices[0].message.content)
            
            should_handover = result.get('requires_human', False)
            reason = result.get('reason', 'AI classification')
            confidence = result.get('confidence', 0.5)
            
            logger.info(f"🤖 HANDOVER CLASSIFICATION - Message: '{message_text[:50]}...' → Handover: {should_handover} ({confidence:.2f} confidence)")
            
            return should_handover, reason, confidence
            
        except Exception as e:
            logger.error(f"Error in AI handover classification: {e}")
            # Fallback to conservative keyword detection
            return self._fallback_keyword_detection(message_text)
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for handover classification"""
        return """You are an expert customer service classifier. Your job is to determine if a customer message is genuinely requesting to speak with a human agent, or if it's a question/request that an AI chatbot should handle.

HANDOVER REQUIRED (requires_human: true):
- Explicit requests for human contact: "I want to talk to a human", "Can I speak to someone?", "I need human help"
- Complex technical support beyond bot capabilities: "I have a complex integration issue that needs debugging"
- Complaints requiring human empathy: "I'm very frustrated with this service"
- Account-specific issues: "There's a billing problem with my account", "I need to change my subscription"
- Situations requiring human judgment: "I need to negotiate terms", "This is a special case"

NO HANDOVER NEEDED (requires_human: false):
- Questions about bot memory/capabilities: "What's my name?", "Do you remember what I told you?", "What company do I work for?"
- Product information requests: "Tell me about your pricing", "How does this feature work?"
- General questions: "Can you explain this?", "What are the benefits?"
- Requests for information the bot can provide: "Can you send me documentation?", "What are your hours?"
- Testing bot functionality: "Do you know who I am?", "What did I tell you earlier?"

RESPOND WITH VALID JSON:
{
  "requires_human": boolean,
  "reason": "brief explanation of decision",
  "confidence": 0.0-1.0 (how certain you are)
}"""

    def _build_classification_prompt(self, message_text: str, customer_context: Dict = None) -> str:
        """Build the classification prompt with context"""
        
        context_info = ""
        if customer_context:
            context_info = f"\nCustomer Context: {json.dumps(customer_context, indent=2)}"
        
        return f"""Classify this customer message:

MESSAGE: "{message_text}"
{context_info}

Is this customer genuinely requesting to speak with a human agent, or asking a question that the AI chatbot should handle?

Consider:
- The specific wording and intent
- Whether this is testing bot memory vs requesting human help
- If the bot has the capabilities to answer this question
- The customer's context and previous interactions

Respond with JSON classification:"""

    def _fallback_keyword_detection(self, message_text: str) -> Tuple[bool, str, float]:
        """
        Fallback keyword-based detection (more conservative)
        Only triggers on very explicit human requests
        """
        message_lower = message_text.lower()
        
        # Very explicit human request keywords
        explicit_keywords = [
            "speak to a human", "talk to a human", "human agent", "human support",
            "speak to someone", "talk to someone", "connect me to",
            "transfer me to", "escalate to", "human representative",
            "real person", "live agent", "customer service rep"
        ]
        
        # Complaint/frustration indicators that might need human
        complaint_keywords = [
            "frustrated", "angry", "terrible service", "this doesn't work",
            "billing issue", "account problem", "cancel my", "refund"
        ]
        
        # Check for explicit requests
        for keyword in explicit_keywords:
            if keyword in message_lower:
                return True, f"Explicit human request: '{keyword}'", 0.9
        
        # Check for complaints (lower confidence)
        for keyword in complaint_keywords:
            if keyword in message_lower:
                return True, f"Complaint detected: '{keyword}'", 0.7
        
        # Default: no handover needed
        return False, "No clear human request detected", 0.8


def get_handover_classification_agent() -> HandoverClassificationAgent:
    """Get a configured handover classification agent"""
    try:
        # Get OpenAI API key from environment or config
        import os
        api_key = os.getenv('OPENAI_API_KEY')
        
        if not api_key:
            # Try to get from config file
            try:
                import sys
                sys.path.append(os.path.dirname(os.path.dirname(__file__)))
                from config.config import get_openai_client
                client = get_openai_client()
                return HandoverClassificationAgent(api_key=client.api_key)
            except:
                logger.warning("Could not get OpenAI API key - classification agent will use fallback keyword detection")
                return HandoverClassificationAgent()
        
        return HandoverClassificationAgent(api_key=api_key)
        
    except Exception as e:
        logger.error(f"Error creating handover classification agent: {e}")
        return HandoverClassificationAgent()