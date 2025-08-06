"""
AI Information Extraction Agent
Uses LLM to intelligently extract structured customer information from natural language messages
"""

import json
import logging
from typing import Dict, Optional, Any
from openai import OpenAI

logger = logging.getLogger(__name__)

class InformationExtractionAgent:
    def __init__(self, api_key: str = None):
        """Initialize the AI extraction agent"""
        self.client = OpenAI(api_key=api_key) if api_key else None
        
    def extract_customer_information(self, message_text: str, existing_context: Dict = None) -> Dict[str, Any]:
        """
        Extract structured customer information from natural language message
        
        Args:
            message_text: The user's message
            existing_context: Already known information about the customer
            
        Returns:
            Dict with extracted information in structured format
        """
        if not self.client:
            logger.warning("OpenAI client not initialized - falling back to empty extraction")
            return {}
            
        try:
            # Prepare the extraction prompt
            extraction_prompt = self._build_extraction_prompt(message_text, existing_context)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Fast and cost-effective for extraction
                messages=[
                    {
                        "role": "system", 
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user", 
                        "content": extraction_prompt
                    }
                ],
                temperature=0.1,  # Low temperature for consistent extraction
                max_tokens=500,
                response_format={"type": "json_object"}  # Ensure JSON response
            )
            
            # Parse the response
            extracted_data = json.loads(response.choices[0].message.content)
            
            # Validate and clean the extracted data
            cleaned_data = self._validate_and_clean_extraction(extracted_data)
            
            logger.info(f"🤖 AI EXTRACTION - Extracted: {list(cleaned_data.keys())}")
            
            return cleaned_data
            
        except Exception as e:
            logger.error(f"Error in AI extraction: {e}")
            return {}
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the extraction agent"""
        return """You are an expert information extraction agent. Your job is to analyze customer messages and extract structured information.

EXTRACTION RULES:
1. Only extract information that is explicitly mentioned or clearly implied
2. Return ONLY the fields that contain actual information
3. Use null for missing information - don't guess or infer beyond reasonable certainty
4. Be conservative - better to miss information than extract wrong information
5. Normalize data to standard formats (e.g., email lowercase, names title case)

FIELD DEFINITIONS:
- name: Person's full name (first + last preferred)
- email: Email address 
- company: Company/organization name
- position: Job title or role
- industry_focus: Industry sector (healthcare, fintech, saas, manufacturing, etc.)
- company_size: Organization size (startup, small, medium, large, enterprise)
- technical_level: Technical expertise (non_technical, business_user, technical, developer, executive)
- response_urgency: How urgent their request is (low, medium, high)
- budget_range: Budget indicators (small, medium, large, enterprise)
- timeline: Project timeline urgency (flexible, moderate, urgent, immediate)
- current_tools: Tools/software they currently use
- pain_points_mentioned: Specific problems they mentioned
- goals_expressed: What they want to achieve
- decision_maker: Whether they make purchasing decisions (true/false)

RESPONSE FORMAT: Valid JSON object with only the fields that contain information."""

    def _build_extraction_prompt(self, message_text: str, existing_context: Dict = None) -> str:
        """Build the extraction prompt with context"""
        
        context_info = ""
        if existing_context:
            context_info = f"\nEXISTING CONTEXT: {json.dumps(existing_context, indent=2)}"
        
        return f"""Please extract customer information from this message:

MESSAGE: "{message_text}"
{context_info}

Extract any relevant customer information into structured JSON format. Only include fields where you found actual information.

Examples of good extraction:
- "My name is Sarah" → {{"name": "Sarah"}}
- "I'm the CTO at Microsoft" → {{"name": "unknown", "position": "CTO", "company": "Microsoft", "decision_maker": true}}
- "We're a healthcare startup using Salesforce" → {{"industry_focus": "healthcare", "company_size": "startup", "current_tools": ["Salesforce"]}}
- "This is urgent!" → {{"response_urgency": "high"}}

Return only valid JSON:"""

    def _validate_and_clean_extraction(self, extracted_data: Dict) -> Dict[str, Any]:
        """Validate and clean the extracted data"""
        
        # Define valid fields and their types
        valid_fields = {
            'name': str,
            'email': str,
            'company': str,
            'position': str,
            'industry_focus': str,
            'company_size': str,
            'technical_level': str,
            'response_urgency': str,
            'budget_range': str,
            'timeline': str,
            'current_tools': list,
            'pain_points_mentioned': list,
            'goals_expressed': list,
            'decision_maker': bool
        }
        
        cleaned = {}
        
        for field, value in extracted_data.items():
            # Skip invalid fields
            if field not in valid_fields:
                continue
                
            # Skip null/empty values
            if value is None or value == "" or value == []:
                continue
                
            # Type validation and cleaning
            expected_type = valid_fields[field]
            
            if expected_type == str:
                if isinstance(value, str) and value.strip():
                    # Clean string values
                    cleaned_value = value.strip()
                    
                    # Special cleaning for specific fields
                    if field == 'email':
                        cleaned_value = cleaned_value.lower()
                    elif field in ['name', 'company', 'position']:
                        cleaned_value = cleaned_value.title()
                    elif field in ['industry_focus', 'company_size', 'technical_level', 'response_urgency', 'budget_range', 'timeline']:
                        cleaned_value = cleaned_value.lower()
                        
                    cleaned[field] = cleaned_value
                    
            elif expected_type == list:
                if isinstance(value, list) and value:
                    # Clean list values
                    cleaned_list = [str(item).strip() for item in value if item]
                    if cleaned_list:
                        cleaned[field] = cleaned_list
                elif isinstance(value, str) and value.strip():
                    # Convert single string to list
                    cleaned[field] = [value.strip()]
                    
            elif expected_type == bool:
                if isinstance(value, bool):
                    cleaned[field] = value
                elif isinstance(value, str):
                    cleaned[field] = value.lower() in ['true', 'yes', '1']
        
        return cleaned


def get_information_extraction_agent() -> InformationExtractionAgent:
    """Get a configured information extraction agent"""
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
                return InformationExtractionAgent(api_key=client.api_key)
            except:
                logger.warning("Could not get OpenAI API key - extraction agent will return empty results")
                return InformationExtractionAgent()
        
        return InformationExtractionAgent(api_key=api_key)
        
    except Exception as e:
        logger.error(f"Error creating extraction agent: {e}")
        return InformationExtractionAgent()