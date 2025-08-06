"""
Emergency Handover Management Service
Handles timeout rescue and progressive messaging for abandoned handovers
Integrates with existing APScheduler system for background processing
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from src.core.supabase_client import get_supabase_manager
from src.handlers.whatsapp_handler import send_complete_message

logger = logging.getLogger(__name__)

class HandoverManagementService:
    def __init__(self, supabase_client=None):
        """
        Initialize handover management service.
        
        Args:
            supabase_client: Optional Supabase client (uses global if not provided)
        """
        self.supabase = supabase_client or get_supabase_manager()
    
    def rescue_abandoned_customers(self) -> Dict[str, int]:
        """
        Emergency rescue for customers abandoned in handover queue
        Returns statistics of rescued conversations
        """
        logger.info("🚨 EMERGENCY RESCUE - Starting abandoned customer rescue")
        
        rescued_count = 0
        notified_count = 0
        error_count = 0
        
        try:
            if not self.supabase.is_connected():
                logger.error("Database not connected for rescue operation")
                return {"rescued": 0, "notified": 0, "errors": 1, "error": "no_db"}
            
            # Find abandoned conversations (60+ minutes)
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=1)
            
            abandoned_result = self.supabase.client.table('conversations')\
                .select('id, handover_timestamp, contacts!inner(phone_number, name)')\
                .eq('handover_requested', True)\
                .eq('bot_enabled', False)\
                .lt('handover_timestamp', cutoff_time.isoformat())\
                .execute()
            
            logger.info(f"🔍 RESCUE SCAN - Found {len(abandoned_result.data)} abandoned conversations")
            
            for conv in abandoned_result.data:
                try:
                    success = self._emergency_reenable_bot(conv)
                    if success:
                        rescued_count += 1
                        logger.info(f"✅ RESCUED - {conv['contacts']['phone_number']}")
                    else:
                        error_count += 1
                        logger.error(f"❌ RESCUE FAILED - {conv['contacts']['phone_number']}")
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error rescuing conversation {conv['id']}: {e}")
            
            # PROGRESSIVE TIMEOUT SYSTEM - Check multiple intervals
            notified_count += self._process_progressive_updates(cutoff_time)
            
            logger.info(f"🎯 RESCUE COMPLETE - Rescued: {rescued_count}, Updated: {notified_count}, Errors: {error_count}")
            return {
                "rescued": rescued_count, 
                "notified": notified_count, 
                "errors": error_count
            }
            
        except Exception as e:
            logger.error(f"Emergency rescue operation failed: {e}")
            return {"rescued": 0, "notified": 0, "errors": 1, "error": str(e)}
    
    def _emergency_reenable_bot(self, conversation: Dict) -> bool:
        """Re-enable bot with professional apology message"""
        try:
            phone_number = conversation['contacts']['phone_number']
            customer_name = conversation['contacts']['name'] or "there"
            
            # Calculate wait time for context
            handover_time = datetime.fromisoformat(conversation['handover_timestamp'].replace('Z', '+00:00'))
            wait_minutes = int((datetime.now(timezone.utc) - handover_time).total_seconds() / 60)
            
            # Get customer context for personalized apology
            context_response = self.supabase.client.table('contacts')\
                .select('enhanced_context')\
                .eq('phone_number', phone_number)\
                .execute()
            
            customer_context = {}
            if context_response.data:
                customer_context = context_response.data[0].get('enhanced_context', {})
            
            company = customer_context.get('company', '')
            urgency = customer_context.get('response_urgency', 'medium')
            
            company_context = f" from {company}" if company else ""
            urgency_prefix = "🚨 URGENT CASE - " if urgency == 'high' else ""
            compensation = "We're providing extended trial access and priority implementation support as an apology." if wait_minutes > 90 else "We'll ensure priority attention for your next request."
            
            apology_message = f"""Hi {customer_name}! 🙏

{urgency_prefix}I sincerely apologize - you've been waiting {wait_minutes} minutes for our human team{company_context}. This is completely unacceptable.

**IMMEDIATE ASSISTANCE NOW AVAILABLE:**

🚀 **I'm back with FULL CONTEXT** of our entire conversation
✅ Advanced AI assistance with human-level problem solving
✅ Complete product demonstrations and technical deep-dives  
✅ Instant custom solution recommendations for your specific needs
✅ Real-time pricing and ROI calculations
✅ GUARANTEED priority callback scheduling (within 2 hours)

**{compensation}**

I'm personally committed to resolving this RIGHT NOW! What's the most important thing I can help you with immediately? 

💪 I have all the context and capabilities to move your project forward this instant!

(Human handover is still available - but you'll get immediate priority attention) 🎯"""

            # Send apology message
            send_success, message_id = send_complete_message(phone_number, apology_message)
            
            if send_success:
                # Re-enable bot in database and reset update tracking
                update_result = self.supabase.client.table('conversations')\
                    .update({
                        'bot_enabled': True,
                        'handover_requested': False,
                        'handover_resolved_at': datetime.now(timezone.utc).isoformat(),
                        'handover_resolution_reason': f'Auto-resolved: Emergency timeout after {wait_minutes}min',
                        'handover_updates_sent': {},  # Reset update tracking for future handovers
                        'updated_at': datetime.now(timezone.utc).isoformat()
                    })\
                    .eq('id', conversation['id'])\
                    .execute()
                
                # Save the apology message to conversation history
                self.supabase.save_message_with_status(
                    phone_number=phone_number,
                    message_content=apology_message,
                    role='assistant',
                    message_id=message_id,
                    status='sent'
                )
                
                logger.info(f"✅ EMERGENCY RESCUE SUCCESS - Bot re-enabled for {phone_number}")
                return True
            else:
                logger.error(f"❌ EMERGENCY RESCUE FAILED - Could not send message to {phone_number}")
                return False
                
        except Exception as e:
            logger.error(f"Error in emergency re-enable: {e}")
            return False
    
    def _process_progressive_updates(self, cutoff_time: datetime) -> int:
        """
        Process progressive timeout messages at different intervals
        Returns count of notifications sent
        """
        total_notified = 0
        
        # Define progressive intervals (minutes from handover start)
        intervals = [
            {'minutes': 10, 'type': '10min'},
            {'minutes': 20, 'type': '20min'},
            {'minutes': 30, 'type': '30min'},
            {'minutes': 45, 'type': '45min'},
        ]
        
        current_time = datetime.now(timezone.utc)
        
        for interval in intervals:
            # Calculate time boundary for this interval
            interval_cutoff = current_time - timedelta(minutes=interval['minutes'])
            
            # Don't check intervals older than 60 minutes (those get rescued)
            if interval_cutoff <= cutoff_time:
                continue
                
            # Find conversations that need this interval update
            conversations = self._get_conversations_needing_update(interval_cutoff, interval['type'])
            
            for conv in conversations:
                try:
                    if self._send_progressive_update(conv, interval['type']):
                        total_notified += 1
                        logger.info(f"📤 PROGRESSIVE UPDATE - Sent {interval['type']} to {conv['contacts']['phone_number']}")
                except Exception as e:
                    logger.error(f"Error sending {interval['type']} update to {conv['id']}: {e}")
        
        return total_notified
    
    def _get_conversations_needing_update(self, interval_cutoff: datetime, update_type: str) -> List[Dict]:
        """Get conversations that need a specific interval update"""
        try:
            # Calculate previous interval to avoid overlapping
            previous_minutes = {'10min': 0, '20min': 10, '30min': 20, '45min': 30}
            prev_cutoff = datetime.now(timezone.utc) - timedelta(minutes=previous_minutes[update_type])
            
            result = self.supabase.client.table('conversations')\
                .select('id, handover_timestamp, contacts!inner(phone_number, name, enhanced_context)')\
                .eq('handover_requested', True)\
                .eq('bot_enabled', False)\
                .lt('handover_timestamp', interval_cutoff.isoformat())\
                .gt('handover_timestamp', prev_cutoff.isoformat())\
                .execute()
            
            # Filter out conversations that already received this update
            filtered_conversations = []
            for conv in result.data:
                if not self._has_received_update(conv['id'], update_type):
                    filtered_conversations.append(conv)
            
            return filtered_conversations
            
        except Exception as e:
            logger.error(f"Error getting conversations for {update_type}: {e}")
            return []
    
    def _send_progressive_update(self, conversation: Dict, update_type: str) -> bool:
        """Send personalized progressive update based on customer context and timing"""
        try:
            phone_number = conversation['contacts']['phone_number']
            customer_name = conversation['contacts']['name'] or "there"
            
            # Get customer context for personalization
            customer_context = conversation['contacts'].get('enhanced_context', {})
            urgency = customer_context.get('response_urgency', 'medium')
            company = customer_context.get('company', '')
            position = customer_context.get('position', '')
            
            # Calculate wait time for context
            handover_time = datetime.fromisoformat(conversation['handover_timestamp'].replace('Z', '+00:00'))
            wait_minutes = int((datetime.now(timezone.utc) - handover_time).total_seconds() / 60)
            
            message = self._generate_progressive_message(
                update_type, customer_name, wait_minutes, urgency, company, position
            )
            
            # Send the message
            send_success, message_id = send_complete_message(phone_number, message)
            
            if send_success:
                # Mark update as sent
                self._mark_update_sent(conversation['id'], update_type)
                
                # Save message to history
                self.supabase.save_message_with_status(
                    phone_number=phone_number,
                    message_content=message,
                    role='assistant',
                    message_id=message_id,
                    status='sent'
                )
                
                return True
            else:
                logger.error(f"Failed to send {update_type} message to {phone_number}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending progressive update: {e}")
            return False
    
    def _generate_progressive_message(self, update_type: str, name: str, wait_minutes: int, 
                                    urgency: str, company: str, position: str) -> str:
        """Generate personalized message based on timing and customer context"""
        
        # Personalization elements
        greeting = f"Hi {name}!" if name != "there" else "Hi there!"
        company_context = f" from {company}" if company else ""
        urgency_tone = "URGENT" if urgency == 'high' else ""
        
        if update_type == '10min':
            return f"""{greeting} 👋

I see you've been waiting {wait_minutes} minutes to connect with our human team{company_context}. 

Your request is important to us and you're in our priority queue! 🔥

⏱️ **Current status**: Our specialists are finishing up with complex technical cases
📞 **Estimated wait**: 10-20 more minutes

While you wait, I'm here with full AI-powered assistance:
✅ Detailed product demos and pricing
✅ Technical integration planning  
✅ Custom solution recommendations
✅ Immediate answers to urgent questions

Would you like me to help with anything specific while we get a human connected? I have all the context from our conversation! 😊"""

        elif update_type == '20min':
            return f"""{greeting} ⏳

Quick 20-minute update: You're still our priority{company_context}!

🎯 **Good news**: Our team is aware of your {urgency} request and you're next in line
⏱️ **Updated estimate**: 15-25 more minutes

💡 **Smart options while you wait:**
🔹 I can provide detailed technical specifications  
🔹 Schedule a GUARANTEED priority call for tomorrow
🔹 Send you comprehensive product information via email
🔹 Start preparing a custom proposal based on your needs

{urgency_tone + ' - ' if urgency_tone else ''}Would any of these help move things forward immediately? 🚀"""

        elif update_type == '30min':
            return f"""{greeting} ⚡

30-minute update: I understand waiting this long isn't ideal{company_context}.

🔄 **Current situation**: Higher than normal support volume today
⏱️ **Realistic estimate**: 15-30 more minutes for human connection
🎯 **Alternative**: I can help you immediately with 95% of requests

**I'm equipped to handle:**
✅ Complete product walkthroughs with screen sharing
✅ Technical architecture discussions
✅ Pricing and ROI calculations  
✅ Integration planning and timelines
✅ Custom demo preparation for your team

{urgency_tone + ' case - ' if urgency_tone else ''}Want to get started while we wait? I guarantee I can move your project forward right now! 💪"""

        elif update_type == '45min':
            return f"""{greeting} 🚨

{urgency_tone + ' UPDATE - ' if urgency_tone else ''}45 minutes is definitely longer than acceptable{company_context}.

⚠️ **Escalation notice**: Your case is being moved to our senior team
⏱️ **Final estimate**: 10-15 more minutes OR immediate AI assistance
🎁 **Compensation**: We'll provide extended trial and priority implementation support

**IMMEDIATE options to resolve this now:**
🚀 **Fast-track demo**: I can show you everything in 10 minutes
📞 **Guaranteed callback**: Schedule priority call with decision maker  
📧 **Instant proposal**: I'll prepare detailed solution summary
💬 **Direct assistance**: I can solve most technical questions immediately

This wait is unacceptable - let me make it right! Which option works best for you? 🤝"""
        
        else:
            # Fallback message
            return f"""{greeting}

Thank you for your patience! You've been waiting {wait_minutes} minutes and we appreciate your understanding.

Our team is working to connect with you as soon as possible. I'm here to help in the meantime! 😊"""
    
    def _has_received_update(self, conversation_id: str, update_type: str) -> bool:
        """Check if conversation already received this type of update"""
        try:
            # Query conversation to check handover_updates_sent field
            result = self.supabase.client.table('conversations')\
                .select('handover_updates_sent')\
                .eq('id', conversation_id)\
                .execute()
            
            if result.data and len(result.data) > 0:
                updates_sent = result.data[0].get('handover_updates_sent', {})
                
                # Check if this update type was already sent
                if isinstance(updates_sent, dict) and update_type in updates_sent:
                    logger.debug(f"Update {update_type} already sent to conversation {conversation_id}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking update status for {conversation_id}: {e}")
            # Return False to be safe - will send update if there's an error
            return False
    
    def _mark_update_sent(self, conversation_id: str, update_type: str):
        """Mark that we sent an update (for tracking)"""
        try:
            # Get current updates_sent data
            result = self.supabase.client.table('conversations')\
                .select('handover_updates_sent')\
                .eq('id', conversation_id)\
                .execute()
            
            current_updates = {}
            if result.data and len(result.data) > 0:
                current_updates = result.data[0].get('handover_updates_sent', {})
                if not isinstance(current_updates, dict):
                    current_updates = {}
            
            # Add the new update with timestamp
            current_updates[update_type] = datetime.now(timezone.utc).isoformat()
            
            # Update the database
            update_result = self.supabase.client.table('conversations')\
                .update({'handover_updates_sent': current_updates})\
                .eq('id', conversation_id)\
                .execute()
            
            if update_result.data:
                logger.info(f"✅ Marked {update_type} update as sent for conversation {conversation_id}")
            else:
                logger.warning(f"⚠️ Failed to mark {update_type} update for conversation {conversation_id}")
                
        except Exception as e:
            logger.error(f"Error marking update as sent for {conversation_id}: {e}")
            # Don't raise exception - this is tracking, not critical functionality

    def reset_update_tracking(self, conversation_id: str) -> bool:
        """
        Reset update tracking for a conversation (e.g., when human responds)
        
        Args:
            conversation_id: The conversation ID to reset tracking for
            
        Returns:
            True if successful, False otherwise
        """
        try:
            update_result = self.supabase.client.table('conversations')\
                .update({'handover_updates_sent': {}})\
                .eq('id', conversation_id)\
                .execute()
            
            if update_result.data:
                logger.info(f"✅ Reset update tracking for conversation {conversation_id}")
                return True
            else:
                logger.warning(f"⚠️ Failed to reset update tracking for conversation {conversation_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error resetting update tracking for {conversation_id}: {e}")
            return False

    def get_handover_statistics(self) -> Dict[str, int]:
        """Get current handover queue statistics with update tracking info"""
        try:
            if not self.supabase.is_connected():
                return {"error": "Database not connected"}
            
            # Count active handovers with update tracking data
            active_handovers = self.supabase.client.table('conversations')\
                .select('id, handover_timestamp, handover_updates_sent')\
                .eq('handover_requested', True)\
                .eq('bot_enabled', False)\
                .execute()
            
            total_waiting = len(active_handovers.data)
            
            if total_waiting == 0:
                return {"total_waiting": 0, "waiting_over_30min": 0, "waiting_over_60min": 0, "notified_customers": 0}
            
            # Calculate wait times and tracking stats
            current_time = datetime.now(timezone.utc)
            waiting_over_30min = 0
            waiting_over_60min = 0
            notified_customers = 0
            
            for conv in active_handovers.data:
                handover_time = datetime.fromisoformat(conv['handover_timestamp'].replace('Z', '+00:00'))
                wait_minutes = (current_time - handover_time).total_seconds() / 60
                
                if wait_minutes > 60:
                    waiting_over_60min += 1
                elif wait_minutes > 30:
                    waiting_over_30min += 1
                
                # Check if customer has been notified
                updates_sent = conv.get('handover_updates_sent', {})
                if isinstance(updates_sent, dict) and updates_sent:
                    notified_customers += 1
            
            return {
                "total_waiting": total_waiting,
                "waiting_over_30min": waiting_over_30min, 
                "waiting_over_60min": waiting_over_60min,
                "notified_customers": notified_customers
            }
            
        except Exception as e:
            logger.error(f"Error getting handover statistics: {e}")
            return {"error": str(e)}


# Global instance
_handover_service = None

def get_handover_management_service():
    """Get global handover management service instance"""
    global _handover_service
    if _handover_service is None:
        _handover_service = HandoverManagementService()
    return _handover_service