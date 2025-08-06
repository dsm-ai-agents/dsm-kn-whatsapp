"""
Analytics Service for Phase 3A: Smart Business Intelligence
Tracks conversation analytics, lead scoring, and business intelligence metrics
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import uuid

from src.core.supabase_client import get_supabase_manager

logger = logging.getLogger(__name__)

class InteractionQuality(Enum):
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"

class BusinessCategory(Enum):
    PRICING = "pricing"
    TECHNICAL = "technical"
    SUPPORT = "support"
    SALES = "sales"
    GENERAL = "general"

class UrgencyLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

@dataclass
class ConversationSession:
    session_id: str
    contact_id: str
    phone_number: str
    message_count: int = 0
    user_messages: int = 0
    bot_messages: int = 0
    session_start_time: Optional[datetime] = None
    last_activity_time: Optional[datetime] = None
    journey_start_stage: Optional[str] = None
    current_journey_stage: Optional[str] = None
    engagement_score: float = 0.0
    lead_score: float = 0.0
    business_intent_detected: bool = False
    pricing_discussed: bool = False
    demo_requested: bool = False

@dataclass
class MessageAnalytics:
    message_id: str
    contact_id: str
    message_role: str  # user, assistant
    message_content: str
    message_length: int
    ai_handler_used: Optional[str] = None  # enhanced, rag, basic
    rag_documents_retrieved: int = 0
    rag_query_time_ms: Optional[int] = None
    personalization_level: Optional[str] = None
    response_strategy: Optional[str] = None
    communication_style: Optional[str] = None
    detected_intents: List[str] = None
    business_category: Optional[str] = None
    urgency_level: str = "medium"
    sentiment_score: Optional[float] = None
    processing_time_ms: Optional[int] = None
    token_count: Optional[int] = None
    cost_estimate: Optional[float] = None

    def __post_init__(self):
        if self.detected_intents is None:
            self.detected_intents = []

class AnalyticsService:
    """
    Comprehensive analytics service for tracking conversation performance,
    lead scoring, and business intelligence metrics
    """
    
    def __init__(self):
        self.supabase = get_supabase_manager()
        self.active_sessions: Dict[str, ConversationSession] = {}
        
    # ========== CONVERSATION ANALYTICS ==========
    
    def start_conversation_session(self, contact_id: str, phone_number: str, 
                                 journey_stage: str = "discovery") -> str:
        """
        Start a new conversation session for analytics tracking
        
        Args:
            contact_id: Contact UUID
            phone_number: Phone number
            journey_stage: Initial journey stage
            
        Returns:
            Session ID
        """
        try:
            session_id = str(uuid.uuid4())
            session = ConversationSession(
                session_id=session_id,
                contact_id=contact_id,
                phone_number=phone_number,
                session_start_time=datetime.utcnow(),
                last_activity_time=datetime.utcnow(),
                journey_start_stage=journey_stage,
                current_journey_stage=journey_stage
            )
            
            # Store in memory for active tracking
            self.active_sessions[phone_number] = session
            
            # Store in database
            session_data = {
                'id': session_id,
                'contact_id': contact_id,
                'phone_number': phone_number,
                'session_id': session_id,
                'session_start_time': session.session_start_time.isoformat(),
                'last_activity_time': session.last_activity_time.isoformat(),
                'journey_start_stage': journey_stage,
                'journey_end_stage': journey_stage,
                'message_count': 0,
                'user_messages': 0,
                'bot_messages': 0,
                'engagement_score': 0.0,
                'lead_score': 0.0,
                'business_intent_detected': False,
                'pricing_discussed': False,
                'demo_requested': False
            }
            
            result = self.supabase.client.table('conversation_analytics')\
                .insert(session_data)\
                .execute()
                
            if result.data:
                logger.info(f"📊 ANALYTICS - Started conversation session {session_id} for {phone_number}")
                return session_id
            else:
                logger.error(f"Failed to create conversation session in database")
                return session_id  # Return anyway for memory tracking
                
        except Exception as e:
            logger.error(f"Error starting conversation session: {e}")
            return str(uuid.uuid4())  # Return a session ID anyway
    
    def get_or_create_session(self, contact_id: str, phone_number: str, 
                            journey_stage: str = "discovery") -> str:
        """
        Get existing session or create new one
        """
        try:
            # Check if we have an active session in memory
            if phone_number in self.active_sessions:
                session = self.active_sessions[phone_number]
                # Check if session is still active (within last hour)
                if session.last_activity_time and \
                   (datetime.utcnow() - session.last_activity_time).seconds < 3600:
                    return session.session_id
            
            # Check database for recent session
            result = self.supabase.client.table('conversation_analytics')\
                .select('session_id, last_activity_time')\
                .eq('phone_number', phone_number)\
                .gte('last_activity_time', (datetime.utcnow() - timedelta(hours=1)).isoformat())\
                .order('last_activity_time', desc=True)\
                .limit(1)\
                .execute()
            
            if result.data:
                session_id = result.data[0]['session_id']
                logger.info(f"📊 ANALYTICS - Resuming session {session_id} for {phone_number}")
                return session_id
            
            # Create new session
            return self.start_conversation_session(contact_id, phone_number, journey_stage)
            
        except Exception as e:
            logger.error(f"Error getting/creating session: {e}")
            return self.start_conversation_session(contact_id, phone_number, journey_stage)
    
    def track_message(self, message_analytics: MessageAnalytics, 
                     session_id: Optional[str] = None) -> bool:
        """
        Track individual message analytics
        
        Args:
            message_analytics: Message analytics data
            session_id: Optional session ID
            
        Returns:
            Success status
        """
        try:
            # Find or create conversation analytics session
            if not session_id:
                # Try to find recent session
                result = self.supabase.client.table('conversation_analytics')\
                    .select('id')\
                    .eq('contact_id', message_analytics.contact_id)\
                    .gte('last_activity_time', (datetime.utcnow() - timedelta(hours=1)).isoformat())\
                    .order('last_activity_time', desc=True)\
                    .limit(1)\
                    .execute()
                
                conversation_analytics_id = result.data[0]['id'] if result.data else None
            else:
                # Get conversation analytics ID from session
                result = self.supabase.client.table('conversation_analytics')\
                    .select('id')\
                    .eq('session_id', session_id)\
                    .execute()
                
                conversation_analytics_id = result.data[0]['id'] if result.data else None
            
            # Prepare message analytics data
            message_data = {
                'conversation_analytics_id': conversation_analytics_id,
                'contact_id': message_analytics.contact_id,
                'message_id': message_analytics.message_id,
                'message_role': message_analytics.message_role,
                'message_content': message_analytics.message_content[:1000],  # Limit length
                'message_length': message_analytics.message_length,
                'ai_handler_used': message_analytics.ai_handler_used,
                'rag_documents_retrieved': message_analytics.rag_documents_retrieved,
                'rag_query_time_ms': message_analytics.rag_query_time_ms,
                'personalization_level': message_analytics.personalization_level,
                'response_strategy': message_analytics.response_strategy,
                'communication_style': message_analytics.communication_style,
                'detected_intents': message_analytics.detected_intents,
                'business_category': message_analytics.business_category,
                'urgency_level': message_analytics.urgency_level,
                'sentiment_score': message_analytics.sentiment_score,
                'processing_time_ms': message_analytics.processing_time_ms,
                'token_count': message_analytics.token_count,
                'cost_estimate': message_analytics.cost_estimate,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Insert message analytics
            result = self.supabase.client.table('message_analytics')\
                .insert(message_data)\
                .execute()
            
            if result.data:
                logger.debug(f"📊 ANALYTICS - Tracked message {message_analytics.message_id}")
                
                # Update conversation session counts
                self._update_conversation_counts(conversation_analytics_id, message_analytics.message_role)
                
                return True
            else:
                logger.error(f"Failed to insert message analytics")
                return False
                
        except Exception as e:
            logger.error(f"Error tracking message analytics: {e}")
            return False
    
    def _update_conversation_counts(self, conversation_analytics_id: Optional[str], 
                                  message_role: str) -> None:
        """Update conversation message counts"""
        try:
            if not conversation_analytics_id:
                return
                
            # Increment appropriate counter
            if message_role == 'user':
                update_data = {
                    'user_messages': 'user_messages + 1',
                    'message_count': 'message_count + 1',
                    'last_activity_time': datetime.utcnow().isoformat()
                }
            elif message_role == 'assistant':
                update_data = {
                    'bot_messages': 'bot_messages + 1', 
                    'message_count': 'message_count + 1',
                    'last_activity_time': datetime.utcnow().isoformat()
                }
            else:
                return
            
            # Use raw SQL for increment operations
            if message_role == 'user':
                sql = """
                UPDATE conversation_analytics 
                SET user_messages = user_messages + 1,
                    message_count = message_count + 1,
                    last_activity_time = NOW()
                WHERE id = %s
                """
            else:
                sql = """
                UPDATE conversation_analytics 
                SET bot_messages = bot_messages + 1,
                    message_count = message_count + 1,
                    last_activity_time = NOW()
                WHERE id = %s
                """
            
            self.supabase.execute_raw_sql(sql, (conversation_analytics_id,))
            
        except Exception as e:
            logger.error(f"Error updating conversation counts: {e}")
    
    def update_conversation_metrics(self, phone_number: str, 
                                  engagement_score: Optional[float] = None,
                                  lead_score: Optional[float] = None,
                                  journey_stage: Optional[str] = None,
                                  business_intent: Optional[bool] = None,
                                  pricing_discussed: Optional[bool] = None,
                                  demo_requested: Optional[bool] = None) -> bool:
        """
        Update conversation-level metrics
        
        Args:
            phone_number: Phone number to update
            engagement_score: Engagement score (0-100)
            lead_score: Lead score (0-100)
            journey_stage: Current journey stage
            business_intent: Whether business intent was detected
            pricing_discussed: Whether pricing was discussed
            demo_requested: Whether demo was requested
            
        Returns:
            Success status
        """
        try:
            # Build update data
            update_data = {}
            if engagement_score is not None:
                update_data['engagement_score'] = engagement_score
            if lead_score is not None:
                update_data['lead_score'] = lead_score
            if journey_stage is not None:
                update_data['journey_end_stage'] = journey_stage
            if business_intent is not None:
                update_data['business_intent_detected'] = business_intent
            if pricing_discussed is not None:
                update_data['pricing_discussed'] = pricing_discussed
            if demo_requested is not None:
                update_data['demo_requested'] = demo_requested
            
            if not update_data:
                return True
                
            update_data['updated_at'] = datetime.utcnow().isoformat()
            
            # Update most recent conversation session
            result = self.supabase.client.table('conversation_analytics')\
                .update(update_data)\
                .eq('phone_number', phone_number)\
                .gte('last_activity_time', (datetime.utcnow() - timedelta(hours=1)).isoformat())\
                .execute()
            
            if result.data:
                logger.debug(f"📊 ANALYTICS - Updated conversation metrics for {phone_number}")
                return True
            else:
                logger.warning(f"No recent conversation found to update for {phone_number}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating conversation metrics: {e}")
            return False
    
    # ========== LEAD SCORING ANALYTICS ==========
    
    def update_lead_scoring(self, contact_id: str, phone_number: str,
                          overall_score: float,
                          engagement_score: float = 0,
                          intent_score: float = 0,
                          fit_score: float = 0,
                          timing_score: float = 0,
                          behavioral_data: Optional[Dict] = None) -> bool:
        """
        Update lead scoring analytics
        
        Args:
            contact_id: Contact UUID
            phone_number: Phone number
            overall_score: Overall lead score (0-100)
            engagement_score: Engagement component score
            intent_score: Intent component score
            fit_score: Fit component score
            timing_score: Timing component score
            behavioral_data: Additional behavioral indicators
            
        Returns:
            Success status
        """
        try:
            # Prepare lead scoring data
            scoring_data = {
                'contact_id': contact_id,
                'phone_number': phone_number,
                'overall_score': overall_score,
                'engagement_score': engagement_score,
                'intent_score': intent_score,
                'fit_score': fit_score,
                'timing_score': timing_score,
                'last_calculated': datetime.utcnow().isoformat()
            }
            
            # Add behavioral data if provided
            if behavioral_data:
                scoring_data.update({
                    'messages_sent': behavioral_data.get('messages_sent', 0),
                    'questions_asked': behavioral_data.get('questions_asked', 0),
                    'pricing_inquiries': behavioral_data.get('pricing_inquiries', 0),
                    'technical_questions': behavioral_data.get('technical_questions', 0),
                    'demo_requests': behavioral_data.get('demo_requests', 0),
                    'response_speed_avg': behavioral_data.get('response_speed_avg'),
                    'session_frequency': behavioral_data.get('session_frequency'),
                    'conversation_depth': behavioral_data.get('conversation_depth'),
                    'company_size_indicator': behavioral_data.get('company_size_indicator'),
                    'industry_match_score': behavioral_data.get('industry_match_score'),
                    'budget_indicators': behavioral_data.get('budget_indicators', []),
                    'decision_maker_signals': behavioral_data.get('decision_maker_signals', False),
                    'conversion_stage': behavioral_data.get('conversion_stage', 'awareness'),
                    'conversion_probability': behavioral_data.get('conversion_probability', 0),
                    'next_best_action': behavioral_data.get('next_best_action')
                })
            
            # Upsert lead scoring data
            result = self.supabase.client.table('lead_scoring_analytics')\
                .upsert(scoring_data, on_conflict='phone_number')\
                .execute()
            
            if result.data:
                logger.info(f"📊 ANALYTICS - Updated lead scoring for {phone_number}: {overall_score:.1f}")
                return True
            else:
                logger.error(f"Failed to update lead scoring analytics")
                return False
                
        except Exception as e:
            logger.error(f"Error updating lead scoring: {e}")
            return False
    
    # ========== BUSINESS INTELLIGENCE METRICS ==========
    
    def update_daily_metrics(self, metric_date: Optional[datetime] = None) -> bool:
        """
        Calculate and update daily business intelligence metrics
        
        Args:
            metric_date: Date to calculate metrics for (defaults to today)
            
        Returns:
            Success status
        """
        try:
            if not metric_date:
                metric_date = datetime.utcnow().date()
            
            date_str = metric_date.isoformat()
            start_of_day = f"{date_str} 00:00:00+00"
            end_of_day = f"{date_str} 23:59:59+00"
            
            # Calculate conversation metrics
            conversation_metrics = self._calculate_conversation_metrics(start_of_day, end_of_day)
            
            # Calculate message metrics
            message_metrics = self._calculate_message_metrics(start_of_day, end_of_day)
            
            # Calculate lead metrics
            lead_metrics = self._calculate_lead_metrics(start_of_day, end_of_day)
            
            # Calculate journey metrics
            journey_metrics = self._calculate_journey_metrics()
            
            # Calculate AI performance metrics
            ai_metrics = self._calculate_ai_metrics(start_of_day, end_of_day)
            
            # Combine all metrics
            daily_metrics = {
                'metric_date': date_str,
                **conversation_metrics,
                **message_metrics,
                **lead_metrics,
                **journey_metrics,
                **ai_metrics,
                'updated_at': datetime.utcnow().isoformat()
            }
            
            # Upsert daily metrics
            result = self.supabase.client.table('business_intelligence_metrics')\
                .upsert(daily_metrics, on_conflict='metric_date')\
                .execute()
            
            if result.data:
                logger.info(f"📊 ANALYTICS - Updated daily metrics for {date_str}")
                return True
            else:
                logger.error(f"Failed to update daily metrics")
                return False
                
        except Exception as e:
            logger.error(f"Error updating daily metrics: {e}")
            return False
    
    def _calculate_conversation_metrics(self, start_time: str, end_time: str) -> Dict:
        """Calculate conversation-related metrics for a time period"""
        try:
            # Total conversations
            total_result = self.supabase.client.table('conversation_analytics')\
                .select('id', count='exact')\
                .gte('session_start_time', start_time)\
                .lte('session_start_time', end_time)\
                .execute()
            
            total_conversations = total_result.count or 0
            
            # New vs returning conversations (simplified - based on contact creation date)
            new_result = self.supabase.client.table('conversation_analytics')\
                .select('contact_id', count='exact')\
                .gte('session_start_time', start_time)\
                .lte('session_start_time', end_time)\
                .execute()
            
            new_conversations = new_result.count or 0
            returning_conversations = max(0, total_conversations - new_conversations)
            
            return {
                'total_conversations': total_conversations,
                'new_conversations': new_conversations,
                'returning_conversations': returning_conversations
            }
            
        except Exception as e:
            logger.error(f"Error calculating conversation metrics: {e}")
            return {
                'total_conversations': 0,
                'new_conversations': 0,
                'returning_conversations': 0
            }
    
    def _calculate_message_metrics(self, start_time: str, end_time: str) -> Dict:
        """Calculate message-related metrics for a time period"""
        try:
            # Total messages
            total_result = self.supabase.client.table('message_analytics')\
                .select('message_role', count='exact')\
                .gte('timestamp', start_time)\
                .lte('timestamp', end_time)\
                .execute()
            
            total_messages = total_result.count or 0
            
            # User vs bot messages
            user_result = self.supabase.client.table('message_analytics')\
                .select('id', count='exact')\
                .eq('message_role', 'user')\
                .gte('timestamp', start_time)\
                .lte('timestamp', end_time)\
                .execute()
            
            bot_result = self.supabase.client.table('message_analytics')\
                .select('id', count='exact')\
                .eq('message_role', 'assistant')\
                .gte('timestamp', start_time)\
                .lte('timestamp', end_time)\
                .execute()
            
            user_messages = user_result.count or 0
            bot_messages = bot_result.count or 0
            
            return {
                'total_messages': total_messages,
                'user_messages': user_messages,
                'bot_messages': bot_messages,
                'successful_responses': bot_messages,  # Simplified
                'failed_responses': 0  # Would need error tracking
            }
            
        except Exception as e:
            logger.error(f"Error calculating message metrics: {e}")
            return {
                'total_messages': 0,
                'user_messages': 0,
                'bot_messages': 0,
                'successful_responses': 0,
                'failed_responses': 0
            }
    
    def _calculate_lead_metrics(self, start_time: str, end_time: str) -> Dict:
        """Calculate lead-related metrics for a time period"""
        try:
            # Leads generated (conversations with business intent)
            leads_result = self.supabase.client.table('conversation_analytics')\
                .select('id', count='exact')\
                .eq('business_intent_detected', True)\
                .gte('session_start_time', start_time)\
                .lte('session_start_time', end_time)\
                .execute()
            
            # Qualified leads (high lead score)
            qualified_result = self.supabase.client.table('conversation_analytics')\
                .select('id', count='exact')\
                .gte('lead_score', 70)\
                .gte('session_start_time', start_time)\
                .lte('session_start_time', end_time)\
                .execute()
            
            # Demo requests
            demo_result = self.supabase.client.table('conversation_analytics')\
                .select('id', count='exact')\
                .eq('demo_requested', True)\
                .gte('session_start_time', start_time)\
                .lte('session_start_time', end_time)\
                .execute()
            
            # Pricing inquiries
            pricing_result = self.supabase.client.table('conversation_analytics')\
                .select('id', count='exact')\
                .eq('pricing_discussed', True)\
                .gte('session_start_time', start_time)\
                .lte('session_start_time', end_time)\
                .execute()
            
            return {
                'leads_generated': leads_result.count or 0,
                'qualified_leads': qualified_result.count or 0,
                'demo_requests': demo_result.count or 0,
                'pricing_inquiries': pricing_result.count or 0
            }
            
        except Exception as e:
            logger.error(f"Error calculating lead metrics: {e}")
            return {
                'leads_generated': 0,
                'qualified_leads': 0,
                'demo_requests': 0,
                'pricing_inquiries': 0
            }
    
    def _calculate_journey_metrics(self) -> Dict:
        """Calculate customer journey distribution metrics"""
        try:
            # Get current journey stage distribution
            discovery_result = self.supabase.client.table('contacts')\
                .select('id', count='exact')\
                .eq('journey_stage', 'discovery')\
                .execute()
            
            interest_result = self.supabase.client.table('contacts')\
                .select('id', count='exact')\
                .eq('journey_stage', 'interest')\
                .execute()
            
            evaluation_result = self.supabase.client.table('contacts')\
                .select('id', count='exact')\
                .eq('journey_stage', 'evaluation')\
                .execute()
            
            decision_result = self.supabase.client.table('contacts')\
                .select('id', count='exact')\
                .eq('journey_stage', 'decision')\
                .execute()
            
            return {
                'discovery_stage_contacts': discovery_result.count or 0,
                'interest_stage_contacts': interest_result.count or 0,
                'evaluation_stage_contacts': evaluation_result.count or 0,
                'decision_stage_contacts': decision_result.count or 0
            }
            
        except Exception as e:
            logger.error(f"Error calculating journey metrics: {e}")
            return {
                'discovery_stage_contacts': 0,
                'interest_stage_contacts': 0,
                'evaluation_stage_contacts': 0,
                'decision_stage_contacts': 0
            }
    
    def _calculate_ai_metrics(self, start_time: str, end_time: str) -> Dict:
        """Calculate AI performance metrics for a time period"""
        try:
            # RAG queries
            rag_result = self.supabase.client.table('rag_query_logs')\
                .select('id', count='exact')\
                .gte('created_at', start_time)\
                .lte('created_at', end_time)\
                .execute()
            
            # Enhanced responses
            enhanced_result = self.supabase.client.table('message_analytics')\
                .select('id', count='exact')\
                .eq('ai_handler_used', 'enhanced')\
                .gte('timestamp', start_time)\
                .lte('timestamp', end_time)\
                .execute()
            
            # Fallback responses
            fallback_result = self.supabase.client.table('message_analytics')\
                .select('id', count='exact')\
                .eq('ai_handler_used', 'basic')\
                .gte('timestamp', start_time)\
                .lte('timestamp', end_time)\
                .execute()
            
            return {
                'rag_queries': rag_result.count or 0,
                'enhanced_responses': enhanced_result.count or 0,
                'fallback_responses': fallback_result.count or 0
            }
            
        except Exception as e:
            logger.error(f"Error calculating AI metrics: {e}")
            return {
                'rag_queries': 0,
                'enhanced_responses': 0,
                'fallback_responses': 0
            }
    
    # ========== PERFORMANCE TRACKING ==========
    
    def track_performance(self, endpoint: str, operation_type: str, 
                         execution_time_ms: int, status: str,
                         model_used: Optional[str] = None,
                         tokens_processed: Optional[int] = None,
                         cost_incurred: Optional[float] = None,
                         error_message: Optional[str] = None,
                         contact_id: Optional[str] = None,
                         session_id: Optional[str] = None,
                         metadata: Optional[Dict] = None) -> bool:
        """
        Track system and AI performance metrics
        
        Args:
            endpoint: API endpoint or function name
            operation_type: Type of operation (ai_response, rag_query, etc.)
            execution_time_ms: Execution time in milliseconds
            status: success, error, timeout
            model_used: AI model used (if applicable)
            tokens_processed: Number of tokens processed
            cost_incurred: Cost incurred for the operation
            error_message: Error message if status is error
            contact_id: Associated contact ID
            session_id: Associated session ID
            metadata: Additional metadata
            
        Returns:
            Success status
        """
        try:
            performance_data = {
                'endpoint': endpoint,
                'operation_type': operation_type,
                'execution_time_ms': execution_time_ms,
                'status': status,
                'model_used': model_used,
                'tokens_processed': tokens_processed,
                'cost_incurred': cost_incurred,
                'error_message': error_message,
                'contact_id': contact_id,
                'session_id': session_id,
                'request_metadata': metadata or {},
                'timestamp': datetime.utcnow().isoformat()
            }
            
            result = self.supabase.client.table('performance_tracking')\
                .insert(performance_data)\
                .execute()
            
            if result.data:
                logger.debug(f"📊 ANALYTICS - Tracked performance for {endpoint}: {execution_time_ms}ms")
                return True
            else:
                logger.error(f"Failed to track performance metrics")
                return False
                
        except Exception as e:
            logger.error(f"Error tracking performance: {e}")
            return False
    
    # ========== ANALYTICS QUERIES ==========
    
    def get_conversation_analytics(self, phone_number: Optional[str] = None,
                                 start_date: Optional[datetime] = None,
                                 end_date: Optional[datetime] = None,
                                 limit: int = 100) -> List[Dict]:
        """
        Get conversation analytics data
        
        Args:
            phone_number: Filter by specific phone number
            start_date: Start date filter
            end_date: End date filter
            limit: Maximum number of records
            
        Returns:
            List of conversation analytics records
        """
        try:
            query = self.supabase.client.table('conversation_analytics')\
                .select('*')\
                .order('session_start_time', desc=True)\
                .limit(limit)
            
            if phone_number:
                query = query.eq('phone_number', phone_number)
            if start_date:
                query = query.gte('session_start_time', start_date.isoformat())
            if end_date:
                query = query.lte('session_start_time', end_date.isoformat())
            
            result = query.execute()
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error getting conversation analytics: {e}")
            return []
    
    def get_lead_scoring_analytics(self, min_score: Optional[float] = None,
                                 limit: int = 100) -> List[Dict]:
        """
        Get lead scoring analytics data
        
        Args:
            min_score: Minimum lead score filter
            limit: Maximum number of records
            
        Returns:
            List of lead scoring records
        """
        try:
            query = self.supabase.client.table('lead_scoring_analytics')\
                .select('*')\
                .order('overall_score', desc=True)\
                .limit(limit)
            
            if min_score is not None:
                query = query.gte('overall_score', min_score)
            
            result = query.execute()
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error getting lead scoring analytics: {e}")
            return []
    
    def get_business_intelligence_summary(self, days: int = 7) -> Dict:
        """
        Get business intelligence summary for the last N days
        
        Args:
            days: Number of days to include in summary
            
        Returns:
            Business intelligence summary
        """
        try:
            start_date = (datetime.utcnow() - timedelta(days=days)).date().isoformat()
            
            result = self.supabase.client.table('business_intelligence_metrics')\
                .select('*')\
                .gte('metric_date', start_date)\
                .order('metric_date', desc=True)\
                .execute()
            
            if not result.data:
                return {'error': 'No data available'}
            
            # Aggregate metrics
            metrics = result.data
            summary = {
                'period_days': days,
                'total_conversations': sum(m.get('total_conversations', 0) for m in metrics),
                'total_messages': sum(m.get('total_messages', 0) for m in metrics),
                'total_leads': sum(m.get('leads_generated', 0) for m in metrics),
                'qualified_leads': sum(m.get('qualified_leads', 0) for m in metrics),
                'demo_requests': sum(m.get('demo_requests', 0) for m in metrics),
                'pricing_inquiries': sum(m.get('pricing_inquiries', 0) for m in metrics),
                'rag_queries': sum(m.get('rag_queries', 0) for m in metrics),
                'enhanced_responses': sum(m.get('enhanced_responses', 0) for m in metrics),
                'avg_conversion_rate': sum(m.get('conversion_rate', 0) for m in metrics) / len(metrics) if metrics else 0,
                'avg_lead_score': sum(m.get('avg_lead_score', 0) for m in metrics) / len(metrics) if metrics else 0,
                'daily_breakdown': metrics
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting business intelligence summary: {e}")
            return {'error': str(e)}

# Global analytics service instance
_analytics_service = None

def get_analytics_service() -> AnalyticsService:
    """Get global analytics service instance"""
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = AnalyticsService()
    return _analytics_service