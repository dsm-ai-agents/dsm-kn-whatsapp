"""
Enhanced Context Service for Personalized Conversations
Manages user journey tracking, behavioral patterns, and conversation state
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
from src.core.supabase_client import get_supabase_manager

logger = logging.getLogger(__name__)

class JourneyStage(Enum):
    DISCOVERY = "discovery"
    INTEREST = "interest"
    EVALUATION = "evaluation"
    DECISION = "decision"

class EngagementLevel(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class PersonalizationLevel(Enum):
    BASIC = "basic"
    CONTEXTUAL = "contextual"
    RELATIONSHIP = "relationship"
    CLOSING = "closing"

@dataclass
class ConversationState:
    """Current conversation state for personalization"""
    phone_number: str
    current_topic: Optional[str] = None
    unresolved_questions: List[str] = None
    action_items: List[str] = None
    context_continuity: Dict[str, Any] = None
    emotional_context: Dict[str, Any] = None
    last_message_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.unresolved_questions is None:
            self.unresolved_questions = []
        if self.action_items is None:
            self.action_items = []
        if self.context_continuity is None:
            self.context_continuity = {}
        if self.emotional_context is None:
            self.emotional_context = {}

@dataclass
class EnhancedCustomerContext:
    """Enhanced customer context with personalization data"""
    # Basic info (existing)
    phone_number: str
    name: Optional[str] = None
    company: Optional[str] = None
    lead_status: str = "new"
    
    # Journey tracking
    journey_stage: str = "discovery"
    conversation_count: int = 0
    first_contact_date: Optional[datetime] = None
    total_interactions: int = 0
    
    # Interest and behavior tracking
    topics_discussed: List[str] = None
    questions_asked: List[str] = None
    pain_points_mentioned: List[str] = None
    goals_expressed: List[str] = None
    
    # Behavioral patterns
    response_time_pattern: str = "unknown"
    engagement_level: str = "medium"
    information_preference: str = "medium"
    decision_making_style: str = "unknown"
    
    # Sales context
    budget_range: Optional[str] = None
    timeline: Optional[str] = None
    decision_maker: bool = False
    competitors_mentioned: List[str] = None
    
    # Personalization flags
    prefers_examples: bool = True
    industry_focus: Optional[str] = None
    company_size: Optional[str] = None
    technical_level: str = "business_user"
    
    def __post_init__(self):
        # Initialize lists if None
        if self.topics_discussed is None:
            self.topics_discussed = []
        if self.questions_asked is None:
            self.questions_asked = []
        if self.pain_points_mentioned is None:
            self.pain_points_mentioned = []
        if self.goals_expressed is None:
            self.goals_expressed = []
        if self.competitors_mentioned is None:
            self.competitors_mentioned = []

class EnhancedContextService:
    """Service for managing enhanced customer context and personalization"""
    
    def __init__(self):
        self.supabase = get_supabase_manager()
    
    def get_enhanced_customer_context(self, phone_number: str) -> Optional[EnhancedCustomerContext]:
        """Get comprehensive customer context with personalization data"""
        try:
            # Get contact data with all personalization fields
            result = self.supabase.client.table('contacts')\
                .select('*')\
                .eq('phone_number', phone_number)\
                .execute()
            
            if not result.data:
                # Create new contact with default personalization data
                return self._create_new_contact_context(phone_number)
            
            contact_data = result.data[0]
            
            # Convert to EnhancedCustomerContext
            context = EnhancedCustomerContext(
                phone_number=phone_number,
                name=contact_data.get('name'),
                company=contact_data.get('company'),
                lead_status=contact_data.get('lead_status', 'new'),
                
                # Journey tracking
                journey_stage=contact_data.get('journey_stage', 'discovery'),
                conversation_count=contact_data.get('conversation_count', 0),
                first_contact_date=self._parse_datetime(contact_data.get('first_contact_date')),
                total_interactions=contact_data.get('total_interactions', 0),
                
                # Interest and behavior tracking
                topics_discussed=contact_data.get('topics_discussed', []),
                questions_asked=contact_data.get('questions_asked', []),
                pain_points_mentioned=contact_data.get('pain_points_mentioned', []),
                goals_expressed=contact_data.get('goals_expressed', []),
                
                # Behavioral patterns
                response_time_pattern=contact_data.get('response_time_pattern', 'unknown'),
                engagement_level=contact_data.get('engagement_level', 'medium'),
                information_preference=contact_data.get('information_preference', 'medium'),
                decision_making_style=contact_data.get('decision_making_style', 'unknown'),
                
                # Sales context
                budget_range=contact_data.get('budget_range'),
                timeline=contact_data.get('timeline'),
                decision_maker=contact_data.get('decision_maker', False),
                competitors_mentioned=contact_data.get('competitors_mentioned', []),
                
                # Personalization flags
                prefers_examples=contact_data.get('prefers_examples', True),
                industry_focus=contact_data.get('industry_focus'),
                company_size=contact_data.get('company_size'),
                technical_level=contact_data.get('technical_level', 'business_user')
            )
            
            logger.info(f"Retrieved enhanced context for {phone_number}: journey={context.journey_stage}, engagement={context.engagement_level}")
            return context
            
        except Exception as e:
            logger.error(f"Error getting enhanced customer context for {phone_number}: {e}")
            return self._create_new_contact_context(phone_number)
    
    def update_customer_context(self, phone_number: str, updates: Dict[str, Any]) -> bool:
        """Update customer context with new personalization data"""
        try:
            # Prepare update data, handling JSONB fields
            update_data = {}
            for key, value in updates.items():
                if key in ['topics_discussed', 'questions_asked', 'pain_points_mentioned', 
                          'goals_expressed', 'competitors_mentioned']:
                    # Handle JSONB array fields
                    if isinstance(value, list):
                        update_data[key] = value
                    else:
                        update_data[key] = [value] if value else []
                else:
                    update_data[key] = value
            
            # Add updated_at timestamp
            update_data['updated_at'] = datetime.utcnow().isoformat()
            
            # Update contact record
            result = self.supabase.client.table('contacts')\
                .update(update_data)\
                .eq('phone_number', phone_number)\
                .execute()
            
            if result.data:
                logger.info(f"Updated context for {phone_number}: {list(updates.keys())}")
                return True
            else:
                logger.warning(f"No contact found to update for {phone_number}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating customer context for {phone_number}: {e}")
            return False
    
    def analyze_and_update_journey_stage(self, phone_number: str, message_text: str, 
                                       current_context: EnhancedCustomerContext) -> str:
        """Analyze message and update journey stage if needed"""
        try:
            # Journey stage progression logic
            message_lower = message_text.lower()
            current_stage = current_context.journey_stage
            
            # Discovery -> Interest indicators
            if current_stage == "discovery":
                interest_signals = [
                    'interested', 'tell me more', 'how does', 'what are the benefits',
                    'pricing', 'cost', 'demo', 'trial', 'examples', 'case studies'
                ]
                if any(signal in message_lower for signal in interest_signals):
                    new_stage = "interest"
                    self.update_customer_context(phone_number, {'journey_stage': new_stage})
                    return new_stage
            
            # Interest -> Evaluation indicators
            elif current_stage == "interest":
                evaluation_signals = [
                    'compare', 'vs', 'versus', 'alternatives', 'competitors',
                    'timeline', 'implementation', 'requirements', 'features',
                    'integration', 'security', 'compliance'
                ]
                if any(signal in message_lower for signal in evaluation_signals):
                    new_stage = "evaluation"
                    self.update_customer_context(phone_number, {'journey_stage': new_stage})
                    return new_stage
            
            # Evaluation -> Decision indicators
            elif current_stage == "evaluation":
                decision_signals = [
                    'ready to', 'want to proceed', 'let\'s do this', 'sign up',
                    'get started', 'next steps', 'contract', 'agreement',
                    'when can we', 'schedule', 'meeting', 'call'
                ]
                if any(signal in message_lower for signal in decision_signals):
                    new_stage = "decision"
                    self.update_customer_context(phone_number, {'journey_stage': new_stage})
                    return new_stage
            
            return current_stage
            
        except Exception as e:
            logger.error(f"Error analyzing journey stage for {phone_number}: {e}")
            return current_context.journey_stage
    
    def update_behavioral_patterns(self, phone_number: str, message_text: str, 
                                 response_time_seconds: Optional[int] = None) -> bool:
        """Update behavioral patterns based on message analysis"""
        try:
            updates = {}
            message_lower = message_text.lower()
            
            # Analyze engagement level
            high_engagement_signals = [
                'excited', 'amazing', 'perfect', 'exactly what we need',
                'love this', 'impressive', 'wow', 'fantastic'
            ]
            low_engagement_signals = [
                'maybe', 'not sure', 'think about it', 'later',
                'busy', 'not now', 'hmm'
            ]
            
            if any(signal in message_lower for signal in high_engagement_signals):
                updates['engagement_level'] = 'high'
            elif any(signal in message_lower for signal in low_engagement_signals):
                updates['engagement_level'] = 'low'
            
            # Analyze information preference
            if len(message_text) > 100:  # Long messages indicate high info preference
                updates['information_preference'] = 'high'
            elif len(message_text) < 20:  # Short messages indicate low info preference
                updates['information_preference'] = 'low'
            
            # Analyze response time pattern
            if response_time_seconds:
                if response_time_seconds < 60:  # Less than 1 minute
                    updates['response_time_pattern'] = 'fast'
                elif response_time_seconds > 3600:  # More than 1 hour
                    updates['response_time_pattern'] = 'slow'
                else:
                    updates['response_time_pattern'] = 'medium'
            
            # Analyze decision making style
            analytical_signals = [
                'data', 'statistics', 'metrics', 'roi', 'analysis',
                'compare', 'research', 'study', 'evidence'
            ]
            intuitive_signals = [
                'feel', 'sense', 'gut', 'instinct', 'seems right',
                'looks good', 'sounds great'
            ]
            
            if any(signal in message_lower for signal in analytical_signals):
                updates['decision_making_style'] = 'analytical'
            elif any(signal in message_lower for signal in intuitive_signals):
                updates['decision_making_style'] = 'intuitive'
            
            if updates:
                return self.update_customer_context(phone_number, updates)
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating behavioral patterns for {phone_number}: {e}")
            return False
    
    def extract_and_store_insights(self, phone_number: str, message_text: str) -> bool:
        """
        AI-POWERED information extraction from user messages
        Uses intelligent AI agent to extract structured customer information
        """
        try:
            logger.info(f"🔍 AI-POWERED EXTRACTION - Analyzing message from {phone_number}")
            
            # Get existing context for the AI agent
            existing_context = self.get_enhanced_customer_context(phone_number)
            existing_data = {}
            
            if existing_context:
                # Convert existing context to dict for AI agent
                existing_data = {
                    'name': getattr(existing_context, 'name', None),
                    'email': getattr(existing_context, 'email', None),
                    'company': getattr(existing_context, 'company', None),
                    'position': getattr(existing_context, 'position', None),
                    'industry_focus': getattr(existing_context, 'industry_focus', None),
                    'company_size': getattr(existing_context, 'company_size', None),
                    'technical_level': getattr(existing_context, 'technical_level', None),
                }
                # Remove None values
                existing_data = {k: v for k, v in existing_data.items() if v}
            
            # Use AI agent to extract information
            from src.agents.information_extraction_agent import get_information_extraction_agent
            extraction_agent = get_information_extraction_agent()
            
            ai_extracted = extraction_agent.extract_customer_information(
                message_text=message_text,
                existing_context=existing_data
            )
            
            # FALLBACK: Also run existing extraction for pain points (AI might miss some patterns)
            fallback_updates = self._extract_sales_and_project_context(message_text, phone_number)
            
            # Merge AI extraction with fallback (AI takes precedence)
            all_updates = {**fallback_updates, **ai_extracted}
            
            # Log what we extracted
            if all_updates:
                extracted_fields = list(all_updates.keys())
                logger.info(f"📝 AI EXTRACTED DATA - {phone_number}: {extracted_fields}")
                
                # Update database
                return self.update_customer_context(phone_number, all_updates)
            else:
                logger.debug(f"📝 NO EXTRACTION - No extractable data found in message")
                return True
                
        except Exception as e:
            logger.error(f"Error in AI extraction for {phone_number}: {e}")
            # Fallback to existing extraction if AI fails
            return self._extract_sales_and_project_context(message_text, phone_number)

    def _extract_personal_information(self, message_text: str) -> Dict:
        """Extract names, emails, titles, contact info"""
        import re
        updates = {}
        message_lower = message_text.lower()
        
        # NAME EXTRACTION with validation (improved patterns)
        name_patterns = [
            r"my name is ([A-Za-z]+(?:\s+[A-Za-z]+){0,2})(?:\s+and|\s+from|\s*,|\s*\.|\s*$)",
            r"i'?m\s+(?:dr\.?\s+|mr\.?\s+|ms\.?\s+)?([A-Za-z]+(?:\s+[A-Za-z]+){0,2})(?:\s+and|\s+from|\s*,|\s*\.|\s*$)",
            r"i am\s+(?:dr\.?\s+|mr\.?\s+|ms\.?\s+)?([A-Za-z]+(?:\s+[A-Za-z]+){0,2})(?:\s+and|\s+from|\s*,|\s*\.|\s*$)",
            r"call me ([A-Za-z]+(?:\s+[A-Za-z]+)?)(?:\s+and|\s+from|\s*,|\s*\.|\s*$)",
            r"this is\s+(?:dr\.?\s+|mr\.?\s+|ms\.?\s+)?([A-Za-z]+(?:\s+[A-Za-z]+){0,2})(?:\s+and|\s+from|\s*,|\s*\.|\s*$)"
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, message_text, re.IGNORECASE)
            if match:
                potential_name = match.group(1).strip().title()
                if self._is_valid_name(potential_name):
                    updates['name'] = potential_name
                    logger.info(f"📝 EXTRACTED NAME: {potential_name}")
                    break
        
        # EMAIL EXTRACTION
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, message_text)
        if email_match:
            email = email_match.group().lower()
            updates['email'] = email
            logger.info(f"📧 EXTRACTED EMAIL: {email}")
        
        # JOB TITLE EXTRACTION
        title_patterns = [
            r"i'?m (?:the |a )?(?:chief |head |senior |lead )?(ceo|cto|cfo|cmo|vp|director|manager|engineer|developer|analyst|coordinator|specialist)(?:\s+of\s+[\w\s]+)?",
            r"(?:as|i'?m) (?:the |a )?(?:chief |head |senior |lead )?([\w\s]{2,25})(?:\s+at|\s+for|\s*,|\s*$)",
            r"my (?:role|position|title) is (?:the |a )?([\w\s]{2,25})(?:\s+at|\s+for|\s*,|\s*$)"
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, message_lower)
            if match:
                title = match.group(1).strip().title()
                if self._is_valid_job_title(title):
                    updates['position'] = title
                    logger.info(f"💼 EXTRACTED TITLE: {title}")
                    break
        
        return updates

    def _extract_business_context(self, message_text: str) -> Dict:
        """Extract company, industry, size, tech stack information"""
        import re
        updates = {}
        message_lower = message_text.lower()
        
        # COMPANY EXTRACTION (fixed patterns - more precise)
        company_patterns = [
            r"(?:i work at|we'?re from|working at|employed at)\s+([A-Z][A-Za-z0-9\s&\.-]{2,30}(?:\s+(?:Corp|Inc|LLC|Ltd|Company|Co))?)(?:\s|\.|\s+and|\s+you|\s+where|$)",
            r"our company (?:is |called )?([A-Z][A-Za-z0-9\s&\.-]{2,30}(?:\s+(?:Corp|Inc|LLC|Ltd|Company|Co))?)(?:\s|\.|\s+and|\s+you|\s+where|$)",
            r"(?:company called|working for)\s+([A-Z][A-Za-z0-9\s&\.-]{2,30}(?:\s+(?:Corp|Inc|LLC|Ltd|Company|Co))?)(?:\s|\.|\s+and|\s+you|\s+where|$)"
        ]
        
        for pattern in company_patterns:
            match = re.search(pattern, message_text)
            if match:
                company = match.group(1).strip()
                if self._is_valid_company_name(company):
                    updates['company'] = company
                    logger.info(f"🏢 EXTRACTED COMPANY: {company}")
                    break
        
        # INDUSTRY DETECTION (enhanced)
        industry_keywords = {
            'healthcare': ['hospital', 'medical', 'healthcare', 'clinic', 'patient', 'doctor', 'nurse', 'health'],
            'fintech': ['bank', 'finance', 'financial', 'payment', 'trading', 'investment', 'insurance', 'loans'],
            'retail': ['store', 'shop', 'ecommerce', 'e-commerce', 'retail', 'customer', 'sales', 'merchandise'],
            'manufacturing': ['factory', 'production', 'manufacturing', 'supply chain', 'logistics', 'warehouse'],
            'education': ['school', 'university', 'education', 'student', 'teacher', 'academic', 'learning'],
            'saas': ['software', 'saas', 'platform', 'app', 'tech', 'startup', 'development'],
            'consulting': ['consulting', 'consultant', 'advisory', 'services', 'client'],
            'real_estate': ['real estate', 'property', 'mortgage', 'housing', 'construction']
        }
        
        for industry, keywords in industry_keywords.items():
            keyword_count = sum(1 for keyword in keywords if keyword in message_lower)
            if keyword_count >= 1:  # At least one match
                updates['industry_focus'] = industry
                logger.info(f"🏭 DETECTED INDUSTRY: {industry} (matches: {keyword_count})")
                break
        
        # COMPANY SIZE DETECTION
        size_patterns = {
            'startup': [r'startup', r'founding', r'just started', r'small team', r'team of \d{1,2}'],
            'small': [r'small business', r'team of \d{1,3}', r'\d{1,2} employees', r'family business'],
            'medium': [r'growing company', r'100 employees', r'mid-size', r'medium business', r'\d{2,3} people'],
            'enterprise': [r'large company', r'corporation', r'1000 employees', r'enterprise', r'multinational']
        }
        
        for size, patterns in size_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    updates['company_size'] = size
                    logger.info(f"📊 DETECTED SIZE: {size}")
                    break
            if 'company_size' in updates:
                break
        
        return updates

    def _extract_communication_preferences(self, message_text: str) -> Dict:
        """Extract communication style and preference indicators"""
        updates = {}
        message_lower = message_text.lower()
        
        # TECHNICAL LEVEL ASSESSMENT
        technical_indicators = {
            'technical': ['api', 'integration', 'webhook', 'database', 'json', 'xml', 'rest', 'sdk', 'development'],
            'business_user': ['process', 'workflow', 'efficiency', 'reporting', 'dashboard', 'analytics'],
            'executive': ['roi', 'revenue', 'growth', 'strategic', 'competitive', 'market', 'business case']
        }
        
        max_score = 0
        detected_level = 'business_user'  # default
        
        for level, indicators in technical_indicators.items():
            score = sum(1 for indicator in indicators if indicator in message_lower)
            if score > max_score:
                max_score = score
                detected_level = level
        
        if max_score > 0:
            updates['technical_level'] = detected_level
            logger.info(f"🎯 DETECTED TECH LEVEL: {detected_level} (score: {max_score})")
        
        # COMMUNICATION URGENCY
        urgency_indicators = ['urgent', 'asap', 'immediately', 'rush', 'emergency', 'critical']
        if any(indicator in message_lower for indicator in urgency_indicators):
            updates['response_urgency'] = 'high'
            logger.info(f"⚡ DETECTED HIGH URGENCY")
        
        return updates

    def _is_valid_name(self, name: str) -> bool:
        """Enhanced name validation"""
        if len(name) < 2 or len(name) > 50:
            return False
        
        # Invalid names
        invalid_names = {
            'hello', 'hi', 'hey', 'bot', 'here', 'looking', 'interested', 
            'thanks', 'please', 'help', 'support', 'team', 'company',
            'business', 'service', 'solution', 'product', 'information'
        }
        
        return name.lower() not in invalid_names and name.replace(' ', '').isalpha()

    def _is_valid_job_title(self, title: str) -> bool:
        """Validate job title"""
        if len(title) < 2 or len(title) > 50:
            return False
        
        invalid_titles = {'here', 'there', 'work', 'job', 'position', 'looking', 'interested'}
        return title.lower() not in invalid_titles

    def _is_valid_company_name(self, company: str) -> bool:
        """Enhanced company name validation"""
        if len(company) < 2 or len(company) > 100:
            return False
        
        invalid_companies = {
            'work', 'company', 'business', 'here', 'there', 'place', 'office',
            'team', 'group', 'organization', 'firm', 'agency'
        }
        
        return company.lower() not in invalid_companies

    def _extract_sales_and_project_context(self, message_text: str, phone_number: str = None) -> Dict:
        """Enhanced version of existing extraction logic for backward compatibility"""
            message_lower = message_text.lower()
            updates = {}
            
            # Extract pain points
            pain_indicators = [
                'problem', 'issue', 'challenge', 'difficulty', 'struggle',
                'frustrated', 'slow', 'inefficient', 'manual', 'time-consuming'
            ]
            
        current_context = self.get_enhanced_customer_context(phone_number) if phone_number else None
            if current_context:
                pain_points = current_context.pain_points_mentioned.copy()
                
                for indicator in pain_indicators:
                    if indicator in message_lower and indicator not in pain_points:
                        pain_points.append(indicator)
                
                if len(pain_points) > len(current_context.pain_points_mentioned):
                    updates['pain_points_mentioned'] = pain_points
            
            # Extract goals
            goal_indicators = [
                'want to', 'need to', 'goal', 'objective', 'target',
                'improve', 'increase', 'reduce', 'automate', 'streamline'
            ]
            
            if current_context:
                goals = current_context.goals_expressed.copy()
                
                for indicator in goal_indicators:
                    if indicator in message_lower and indicator not in goals:
                        goals.append(indicator)
                
                if len(goals) > len(current_context.goals_expressed):
                    updates['goals_expressed'] = goals
            
            # Extract budget/timeline hints
            if 'budget' in message_lower or '$' in message_text:
                if 'small' in message_lower or 'tight' in message_lower:
                    updates['budget_range'] = 'small'
                elif 'large' in message_lower or 'significant' in message_lower:
                    updates['budget_range'] = 'large'
                else:
                    updates['budget_range'] = 'medium'
            
            if 'urgent' in message_lower or 'asap' in message_lower:
                updates['timeline'] = 'urgent'
            elif 'soon' in message_lower or 'quickly' in message_lower:
                updates['timeline'] = 'short'
            elif 'months' in message_lower or 'planning' in message_lower:
                updates['timeline'] = 'medium'
            
            # Check for decision maker indicators
            decision_maker_signals = [
                'i decide', 'my decision', 'i choose', 'ceo', 'founder',
                'owner', 'manager', 'director', 'head of'
            ]
            
            if any(signal in message_lower for signal in decision_maker_signals):
                updates['decision_maker'] = True
            
        # CURRENT TOOLS MENTIONED (NEW!)
        tools_mentioned = []
        common_tools = [
            'salesforce', 'hubspot', 'pipedrive', 'zoho', 'monday', 'asana', 
            'slack', 'teams', 'zoom', 'excel', 'google sheets', 'zapier'
        ]
        
        for tool in common_tools:
            if tool in message_lower:
                tools_mentioned.append(tool)
        
        if tools_mentioned:
            updates['current_tools'] = tools_mentioned
            logger.info(f"🔧 DETECTED TOOLS: {', '.join(tools_mentioned)}")
        
        return updates
    
    def get_conversation_state(self, phone_number: str) -> Optional[ConversationState]:
        """Get current conversation state"""
        try:
            result = self.supabase.client.table('conversation_states')\
                .select('*')\
                .eq('phone_number', phone_number)\
                .execute()
            
            if result.data:
                data = result.data[0]
                return ConversationState(
                    phone_number=phone_number,
                    current_topic=data.get('current_topic'),
                    unresolved_questions=data.get('unresolved_questions', []),
                    action_items=data.get('action_items', []),
                    context_continuity=data.get('context_continuity', {}),
                    emotional_context=data.get('emotional_context', {}),
                    last_message_at=self._parse_datetime(data.get('last_message_at'))
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting conversation state for {phone_number}: {e}")
            return None
    
    def update_conversation_state(self, phone_number: str, 
                                current_topic: Optional[str] = None,
                                add_question: Optional[str] = None,
                                resolve_question: Optional[str] = None,
                                add_action_item: Optional[str] = None,
                                context_update: Optional[Dict] = None) -> bool:
        """Update conversation state"""
        try:
            # Get existing state or create new
            existing_state = self.get_conversation_state(phone_number)
            
            if existing_state:
                # Update existing state
                unresolved_questions = existing_state.unresolved_questions.copy()
                action_items = existing_state.action_items.copy()
                context_continuity = existing_state.context_continuity.copy()
            else:
                # Create new state
                unresolved_questions = []
                action_items = []
                context_continuity = {}
            
            # Apply updates
            if add_question and add_question not in unresolved_questions:
                unresolved_questions.append(add_question)
            
            if resolve_question and resolve_question in unresolved_questions:
                unresolved_questions.remove(resolve_question)
            
            if add_action_item and add_action_item not in action_items:
                action_items.append(add_action_item)
            
            if context_update:
                context_continuity.update(context_update)
            
            # Prepare upsert data
            upsert_data = {
                'phone_number': phone_number,
                'current_topic': current_topic,
                'unresolved_questions': unresolved_questions,
                'action_items': action_items,
                'context_continuity': context_continuity,
                'last_message_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            # Get contact_id if exists
            contact_result = self.supabase.client.table('contacts')\
                .select('id')\
                .eq('phone_number', phone_number)\
                .execute()
            
            if contact_result.data:
                upsert_data['contact_id'] = contact_result.data[0]['id']
            
            # Upsert conversation state
            result = self.supabase.client.table('conversation_states')\
                .upsert(upsert_data, on_conflict='phone_number')\
                .execute()
            
            if result.data:
                logger.info(f"Updated conversation state for {phone_number}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error updating conversation state for {phone_number}: {e}")
            return False
    
    def get_personalization_level(self, context: EnhancedCustomerContext) -> PersonalizationLevel:
        """Determine appropriate personalization level based on context"""
        try:
            # Closing level - ready to buy
            if (context.journey_stage == "decision" or 
                context.engagement_level == "high" or
                context.decision_maker):
                return PersonalizationLevel.CLOSING
            
            # Relationship level - engaged and evaluating
            if (context.journey_stage == "evaluation" or
                context.conversation_count >= 3 or
                len(context.topics_discussed) >= 3):
                return PersonalizationLevel.RELATIONSHIP
            
            # Contextual level - showing interest
            if (context.journey_stage == "interest" or
                context.conversation_count >= 1 or
                len(context.pain_points_mentioned) > 0):
                return PersonalizationLevel.CONTEXTUAL
            
            # Basic level - new or minimal engagement
            return PersonalizationLevel.BASIC
            
        except Exception as e:
            logger.error(f"Error determining personalization level: {e}")
            return PersonalizationLevel.BASIC
    
    def increment_interaction_count(self, phone_number: str) -> bool:
        """Increment total interactions and conversation count"""
        try:
            # Get current counts
            result = self.supabase.client.table('contacts')\
                .select('total_interactions, conversation_count')\
                .eq('phone_number', phone_number)\
                .execute()
            
            if result.data:
                current_interactions = result.data[0].get('total_interactions', 0)
                current_conversations = result.data[0].get('conversation_count', 0)
                
                # Update counts
                updates = {
                    'total_interactions': current_interactions + 1,
                    'conversation_count': current_conversations + 1,
                    'updated_at': datetime.utcnow().isoformat()
                }
                
                return self.update_customer_context(phone_number, updates)
            
            return False
            
        except Exception as e:
            logger.error(f"Error incrementing interaction count for {phone_number}: {e}")
            return False
    
    def _create_new_contact_context(self, phone_number: str) -> EnhancedCustomerContext:
        """Create new contact with default personalization data"""
        try:
            # Create new contact record
            contact_data = {
                'phone_number': phone_number,
                'journey_stage': 'discovery',
                'conversation_count': 0,
                'first_contact_date': datetime.utcnow().isoformat(),
                'total_interactions': 0,
                'engagement_level': 'medium',
                'information_preference': 'medium',
                'response_time_pattern': 'unknown',
                'decision_making_style': 'unknown',
                'prefers_examples': True,
                'technical_level': 'business_user',
                'decision_maker': False,
                'topics_discussed': [],
                'questions_asked': [],
                'pain_points_mentioned': [],
                'goals_expressed': [],
                'competitors_mentioned': [],
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            result = self.supabase.client.table('contacts')\
                .insert(contact_data)\
                .execute()
            
            if result.data:
                logger.info(f"Created new enhanced contact context for {phone_number}")
            
            return EnhancedCustomerContext(phone_number=phone_number)
            
        except Exception as e:
            logger.error(f"Error creating new contact context for {phone_number}: {e}")
            return EnhancedCustomerContext(phone_number=phone_number)
    
    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string safely"""
        if not dt_str:
            return None
        try:
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except:
            return None

# Global service instance
_enhanced_context_service = None

def get_enhanced_context_service() -> EnhancedContextService:
    """Get global enhanced context service instance"""
    global _enhanced_context_service
    if _enhanced_context_service is None:
        _enhanced_context_service = EnhancedContextService()
    return _enhanced_context_service