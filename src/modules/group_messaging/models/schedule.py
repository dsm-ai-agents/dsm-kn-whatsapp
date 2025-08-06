"""
Scheduled Message Data Models
============================
Data models for scheduling WhatsApp group messages.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class ScheduleStatus(Enum):
    """Schedule status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RecurringPattern(Enum):
    """Recurring pattern enumeration."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


@dataclass
class ScheduledMessage:
    """
    Scheduled message data model.
    
    Attributes:
        id: Unique identifier
        message_content: Message text content
        target_type: Type of target (group, bulk_groups)
        target_ids: List of target group JIDs
        scheduled_time: When to send the message
        status: Current status of the scheduled message
        recurring_pattern: Pattern for recurring messages
        recurring_end_date: When recurring should end
        campaign_name: Optional campaign name
        created_by: Who created this scheduled message
        created_at: When this schedule was created
        executed_at: When the message was actually sent
        error_message: Error details if failed
        metadata: Additional metadata
    """
    message_content: str
    target_groups: List[str]  # Changed from target_ids to match API
    scheduled_at: datetime  # Changed from scheduled_time to match API
    id: Optional[str] = None
    message_type: str = "text"  # Added field
    media_url: Optional[str] = None  # Added field
    status: ScheduleStatus = ScheduleStatus.PENDING
    recurring_pattern: Optional[RecurringPattern] = None
    recurring_interval: Optional[int] = None  # Added field
    recurring_end_date: Optional[datetime] = None
    next_send_at: Optional[datetime] = None  # Added field for recurring messages
    last_sent_at: Optional[datetime] = None  # Added field for tracking
    total_sent: int = 0  # Added field for statistics
    total_failed: int = 0  # Added field for statistics
    campaign_name: Optional[str] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-initialization validation."""
        if not self.message_content:
            raise ValueError("message_content is required")
        
        if not self.target_groups or not isinstance(self.target_groups, list):
            raise ValueError("target_groups must be a non-empty list")
        
        if not self.scheduled_at:
            raise ValueError("scheduled_at is required")
        
        if self.created_at is None:
            self.created_at = datetime.utcnow()
    
    @classmethod
    def create_single_group_schedule(cls, group_jid: str, message: str, 
                                   scheduled_time: datetime, **kwargs) -> 'ScheduledMessage':
        """
        Create a scheduled message for a single group.
        
        Args:
            group_jid: Target group JID
            message: Message content
            scheduled_time: When to send
            **kwargs: Additional attributes
            
        Returns:
            ScheduledMessage instance
        """
        return cls(
            message_content=message,
            target_type="group",
            target_ids=[group_jid],
            scheduled_time=scheduled_time,
            **kwargs
        )
    
    @classmethod
    def create_bulk_group_schedule(cls, group_jids: List[str], message: str, 
                                 scheduled_time: datetime, **kwargs) -> 'ScheduledMessage':
        """
        Create a scheduled message for multiple groups.
        
        Args:
            group_jids: List of target group JIDs
            message: Message content
            scheduled_time: When to send
            **kwargs: Additional attributes
            
        Returns:
            ScheduledMessage instance
        """
        return cls(
            message_content=message,
            target_type="bulk_groups",
            target_ids=group_jids,
            scheduled_time=scheduled_time,
            **kwargs
        )
    
    @classmethod
    def create_recurring_schedule(cls, group_jids: List[str], message: str,
                                scheduled_time: datetime, pattern: RecurringPattern,
                                end_date: datetime = None, **kwargs) -> 'ScheduledMessage':
        """
        Create a recurring scheduled message.
        
        Args:
            group_jids: List of target group JIDs
            message: Message content
            scheduled_time: First occurrence time
            pattern: Recurring pattern (daily, weekly, monthly)
            end_date: When to stop recurring
            **kwargs: Additional attributes
            
        Returns:
            ScheduledMessage instance
        """
        return cls(
            message_content=message,
            target_type="bulk_groups" if len(group_jids) > 1 else "group",
            target_ids=group_jids,
            scheduled_time=scheduled_time,
            recurring_pattern=pattern,
            recurring_end_date=end_date,
            **kwargs
        )
    
    def is_due(self, current_time: datetime = None) -> bool:
        """
        Check if this scheduled message is due for sending.
        
        Args:
            current_time: Current time (defaults to now)
            
        Returns:
            True if message should be sent now
        """
        if current_time is None:
            current_time = datetime.utcnow()
        
        return (
            self.status == ScheduleStatus.PENDING and
            self.scheduled_time <= current_time
        )
    
    def is_recurring(self) -> bool:
        """Check if this is a recurring message."""
        return self.recurring_pattern is not None
    
    def get_next_occurrence(self) -> Optional[datetime]:
        """
        Get the next occurrence time for recurring messages.
        
        Returns:
            Next scheduled time or None if not recurring
        """
        if not self.is_recurring():
            return None
        
        if self.recurring_end_date and datetime.utcnow() >= self.recurring_end_date:
            return None
        
        if self.recurring_pattern == RecurringPattern.DAILY:
            from datetime import timedelta
            return self.scheduled_time + timedelta(days=1)
        elif self.recurring_pattern == RecurringPattern.WEEKLY:
            from datetime import timedelta
            return self.scheduled_time + timedelta(weeks=1)
        elif self.recurring_pattern == RecurringPattern.MONTHLY:
            # Simple monthly increment (same day next month)
            from dateutil.relativedelta import relativedelta
            return self.scheduled_time + relativedelta(months=1)
        
        return None
    
    def mark_as_sent(self, executed_time: datetime = None) -> None:
        """Mark this scheduled message as sent."""
        self.status = ScheduleStatus.SENT
        self.executed_at = executed_time or datetime.utcnow()
    
    def mark_as_failed(self, error_message: str) -> None:
        """Mark this scheduled message as failed."""
        self.status = ScheduleStatus.FAILED
        self.error_message = error_message
        self.executed_at = datetime.utcnow()
    
    def cancel(self) -> None:
        """Cancel this scheduled message."""
        self.status = ScheduleStatus.CANCELLED
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'message_content': self.message_content,
            'target_type': self.target_type,
            'target_ids': self.target_ids,
            'scheduled_time': self.scheduled_time.isoformat() if self.scheduled_time else None,
            'status': self.status.value if isinstance(self.status, ScheduleStatus) else self.status,
            'recurring_pattern': self.recurring_pattern.value if self.recurring_pattern else None,
            'recurring_end_date': self.recurring_end_date.isoformat() if self.recurring_end_date else None,
            'campaign_name': self.campaign_name,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'executed_at': self.executed_at.isoformat() if self.executed_at else None,
            'error_message': self.error_message,
            'metadata': self.metadata
        } 