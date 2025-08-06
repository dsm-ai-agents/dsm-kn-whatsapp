"""
Scheduler Service for Group Messaging Module
============================================
Handles scheduling and processing of delayed and recurring messages.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from ..models.schedule import ScheduledMessage, ScheduleStatus, RecurringPattern
from ..services.group_service import GroupService
from ..services.database_service import DatabaseService
from ..core.exceptions import SchedulingError, DatabaseError

logger = logging.getLogger(__name__)


class SchedulerService:
    """Service for handling message scheduling and recurring messages."""
    
    def __init__(self, group_service: GroupService, database_service: DatabaseService):
        """
        Initialize scheduler service.
        
        Args:
            group_service: Group service for sending messages
            database_service: Database service for persistence
        """
        self.group_service = group_service
        self.db_service = database_service
    
    def calculate_next_send_time(
        self, 
        current_time: datetime, 
        pattern: RecurringPattern, 
        interval: Optional[int] = None
    ) -> datetime:
        """
        Calculate the next send time for a recurring message.
        
        Args:
            current_time: Current/base time to calculate from
            pattern: Recurring pattern (daily, weekly, monthly)
            interval: Interval for the pattern (e.g., every 2 days)
            
        Returns:
            Next scheduled send time
            
        Raises:
            SchedulingError: If calculation fails
        """
        try:
            if interval is None:
                interval = 1
            
            if interval < 1:
                raise SchedulingError("Interval must be at least 1")
            
            if pattern == RecurringPattern.DAILY:
                next_time = current_time + timedelta(days=interval)
            elif pattern == RecurringPattern.WEEKLY:
                next_time = current_time + timedelta(weeks=interval)
            elif pattern == RecurringPattern.MONTHLY:
                # Approximate monthly calculation (30 days)
                next_time = current_time + timedelta(days=30 * interval)
            else:
                raise SchedulingError(f"Unsupported recurring pattern: {pattern}")
            
            logger.info(f"Calculated next send time: {next_time} (pattern: {pattern}, interval: {interval})")
            return next_time
            
        except Exception as e:
            logger.error(f"Failed to calculate next send time: {e}")
            raise SchedulingError(f"Failed to calculate next send time: {str(e)}")
    
    def process_pending_messages(self) -> int:
        """
        Process all pending scheduled messages that are ready to be sent.
        
        Returns:
            Number of messages processed
            
        Raises:
            SchedulingError: If processing fails
        """
        try:
            # Get pending messages ready to be sent
            pending_messages = self.db_service.get_pending_scheduled_messages()
            
            if not pending_messages:
                logger.info("No pending scheduled messages to process")
                return 0
            
            logger.info(f"Processing {len(pending_messages)} pending scheduled messages")
            
            processed_count = 0
            
            for scheduled_message in pending_messages:
                try:
                    success = self._process_single_message(scheduled_message)
                    if success:
                        processed_count += 1
                        
                except Exception as e:
                    logger.error(f"Failed to process scheduled message {scheduled_message.id}: {e}")
                    # Mark as failed
                    self.db_service.update_scheduled_message_status(
                        scheduled_message.id,
                        ScheduleStatus.FAILED.value,
                        error_message=str(e)
                    )
            
            logger.info(f"Successfully processed {processed_count}/{len(pending_messages)} scheduled messages")
            return processed_count
            
        except Exception as e:
            logger.error(f"Failed to process pending messages: {e}")
            raise SchedulingError(f"Failed to process pending messages: {str(e)}")
    
    def _process_single_message(self, scheduled_message: ScheduledMessage) -> bool:
        """
        Process a single scheduled message.
        
        Args:
            scheduled_message: Message to process
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Processing scheduled message: {scheduled_message.id}")
            
            # Update status to processing
            self.db_service.update_scheduled_message_status(
                scheduled_message.id,
                ScheduleStatus.PROCESSING.value
            )
            
            # Send messages to all target groups
            results = self.group_service.send_bulk_group_messages(
                group_jids=scheduled_message.target_groups,
                message_content=scheduled_message.message_content,
                message_type=scheduled_message.message_type,
                media_url=scheduled_message.media_url
            )
            
            # Count successful and failed sends
            successful_sends = sum(1 for r in results if r.status == "sent")
            failed_sends = len(results) - successful_sends
            
            # Save message results to database
            for result in results:
                self.db_service.save_group_message(result)
            
            # Update scheduled message statistics
            total_sent = scheduled_message.total_sent + successful_sends
            total_failed = scheduled_message.total_failed + failed_sends
            
            # Determine if this is a recurring message
            if scheduled_message.recurring_pattern:
                # Calculate next send time
                next_send_time = self.calculate_next_send_time(
                    scheduled_message.scheduled_at,
                    scheduled_message.recurring_pattern,
                    scheduled_message.recurring_interval
                )
                
                # Update for next occurrence
                self.db_service.update_scheduled_message_status(
                    scheduled_message.id,
                    ScheduleStatus.PENDING.value,
                    scheduled_at=next_send_time.isoformat(),
                    next_send_at=next_send_time.isoformat(),
                    last_sent_at=datetime.utcnow().isoformat(),
                    total_sent=total_sent,
                    total_failed=total_failed
                )
                
                logger.info(f"Recurring message {scheduled_message.id} rescheduled for {next_send_time}")
            else:
                # Mark as completed for one-time messages
                self.db_service.update_scheduled_message_status(
                    scheduled_message.id,
                    ScheduleStatus.SENT.value,
                    last_sent_at=datetime.utcnow().isoformat(),
                    total_sent=total_sent,
                    total_failed=total_failed
                )
                
                logger.info(f"One-time scheduled message {scheduled_message.id} completed")
            
            logger.info(f"Scheduled message processed: {successful_sends} successful, {failed_sends} failed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to process scheduled message {scheduled_message.id}: {e}")
            
            # Mark as failed
            self.db_service.update_scheduled_message_status(
                scheduled_message.id,
                ScheduleStatus.FAILED.value,
                error_message=str(e)
            )
            
            return False
    
    def schedule_message(
        self,
        message_content: str,
        target_groups: List[str],
        scheduled_at: datetime,
        message_type: str = "text",
        media_url: Optional[str] = None,
        recurring_pattern: Optional[RecurringPattern] = None,
        recurring_interval: Optional[int] = None
    ) -> ScheduledMessage:
        """
        Schedule a message for future delivery.
        
        Args:
            message_content: Message text content
            target_groups: List of target group JIDs
            scheduled_at: When to send the message
            message_type: Type of message (text, image, etc.)
            media_url: URL of media file (if applicable)
            recurring_pattern: Pattern for recurring messages
            recurring_interval: Interval for recurring pattern
            
        Returns:
            Created ScheduledMessage object
            
        Raises:
            SchedulingError: If scheduling fails
        """
        try:
            # Validate inputs
            if not message_content or not message_content.strip():
                raise SchedulingError("Message content is required")
            
            if not target_groups or len(target_groups) == 0:
                raise SchedulingError("At least one target group is required")
            
            # Handle timezone-aware datetime comparison
            current_time = datetime.utcnow()
            if scheduled_at.tzinfo is not None:
                # scheduled_at is timezone-aware, make current_time timezone-aware too
                from datetime import timezone
                current_time = current_time.replace(tzinfo=timezone.utc)
            elif current_time.tzinfo is not None:
                # current_time is timezone-aware, make scheduled_at timezone-aware
                scheduled_at = scheduled_at.replace(tzinfo=timezone.utc)
            
            if scheduled_at <= current_time:
                raise SchedulingError("Scheduled time must be in the future")
            
            # Create scheduled message
            scheduled_message = ScheduledMessage(
                message_content=message_content,
                message_type=message_type,
                media_url=media_url,
                target_groups=target_groups,
                scheduled_at=scheduled_at,
                status=ScheduleStatus.PENDING,
                recurring_pattern=recurring_pattern,
                recurring_interval=recurring_interval
            )
            
            # Calculate next send time for recurring messages
            if recurring_pattern:
                scheduled_message.next_send_at = self.calculate_next_send_time(
                    scheduled_at, recurring_pattern, recurring_interval
                )
            
            # Save to database
            saved_message = self.db_service.save_scheduled_message(scheduled_message)
            
            logger.info(f"Successfully scheduled message: {saved_message.id}")
            return saved_message
            
        except Exception as e:
            logger.error(f"Failed to schedule message: {e}")
            raise SchedulingError(f"Failed to schedule message: {str(e)}")
    
    def cancel_scheduled_message(self, message_id: str) -> bool:
        """
        Cancel a scheduled message.
        
        Args:
            message_id: ID of the message to cancel
            
        Returns:
            True if successful, False if message not found
            
        Raises:
            SchedulingError: If cancellation fails
        """
        try:
            success = self.db_service.update_scheduled_message_status(
                message_id,
                ScheduleStatus.CANCELLED.value
            )
            
            if success:
                logger.info(f"Successfully cancelled scheduled message: {message_id}")
            else:
                logger.warning(f"Scheduled message not found: {message_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to cancel scheduled message {message_id}: {e}")
            raise SchedulingError(f"Failed to cancel message: {str(e)}")
    
    def get_next_scheduled_time(self) -> Optional[datetime]:
        """
        Get the next scheduled message time.
        
        Returns:
            Next scheduled time or None if no messages pending
        """
        try:
            pending_messages = self.db_service.get_pending_scheduled_messages()
            
            if not pending_messages:
                return None
            
            # Find the earliest scheduled time
            next_time = min(msg.scheduled_at for msg in pending_messages)
            return next_time
            
        except Exception as e:
            logger.error(f"Failed to get next scheduled time: {e}")
            return None 