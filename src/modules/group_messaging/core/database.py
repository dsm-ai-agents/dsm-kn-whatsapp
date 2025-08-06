"""
Database Abstraction Layer
==========================
Provides database operations for the group messaging module.
Supports multiple database providers (Supabase, PostgreSQL, etc.)
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Union
from datetime import datetime

from ..config.settings import GroupMessagingConfig
from ..models.group import Group, GroupMessage
from ..models.schedule import ScheduledMessage

logger = logging.getLogger(__name__)


class DatabaseProvider(ABC):
    """Abstract base class for database providers."""
    
    @abstractmethod
    def connect(self) -> bool:
        """Establish database connection."""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if database is connected."""
        pass
    
    # Group operations
    @abstractmethod
    def create_group(self, group: Group) -> Optional[str]:
        """Create a new group record."""
        pass
    
    @abstractmethod
    def get_group(self, group_jid: str) -> Optional[Group]:
        """Get group by JID."""
        pass
    
    @abstractmethod
    def list_groups(self, limit: int = 50, offset: int = 0) -> List[Group]:
        """List all groups with pagination."""
        pass
    
    @abstractmethod
    def update_group(self, group_jid: str, updates: Dict[str, Any]) -> bool:
        """Update group information."""
        pass
    
    @abstractmethod
    def delete_group(self, group_jid: str) -> bool:
        """Delete group record."""
        pass
    
    # Message operations
    @abstractmethod
    def log_group_message(self, message: GroupMessage) -> Optional[str]:
        """Log a group message."""
        pass
    
    @abstractmethod
    def get_group_messages(self, group_jid: str, limit: int = 50) -> List[GroupMessage]:
        """Get messages for a group."""
        pass
    
    # Scheduled message operations
    @abstractmethod
    def create_scheduled_message(self, scheduled_msg: ScheduledMessage) -> Optional[str]:
        """Create a scheduled message."""
        pass
    
    @abstractmethod
    def get_scheduled_message(self, schedule_id: str) -> Optional[ScheduledMessage]:
        """Get scheduled message by ID."""
        pass
    
    @abstractmethod
    def list_scheduled_messages(self, status: str = None, limit: int = 50) -> List[ScheduledMessage]:
        """List scheduled messages."""
        pass
    
    @abstractmethod
    def update_scheduled_message(self, schedule_id: str, updates: Dict[str, Any]) -> bool:
        """Update scheduled message."""
        pass
    
    @abstractmethod
    def get_due_messages(self, current_time: datetime) -> List[ScheduledMessage]:
        """Get messages that are due for sending."""
        pass


class SupabaseProvider(DatabaseProvider):
    """Supabase database provider implementation."""
    
    def __init__(self, config: GroupMessagingConfig):
        self.config = config
        self.client = None
        
    def connect(self) -> bool:
        """Establish Supabase connection."""
        try:
            from supabase import create_client, Client
            
            self.client = create_client(
                self.config.database_url,
                self.config.database_key
            )
            
            # Test connection
            result = self.client.table('groups').select('count').limit(1).execute()
            logger.info("Connected to Supabase successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
            return False
    
    def is_connected(self) -> bool:
        """Check if connected to Supabase."""
        return self.client is not None
    
    def create_group(self, group: Group) -> Optional[str]:
        """Create a new group record in Supabase."""
        try:
            data = {
                'group_jid': group.group_jid,
                'name': group.name,
                'img_url': group.img_url,
                'status': group.status.value if hasattr(group.status, 'value') else group.status,
                'member_count': group.member_count,
                'metadata': group.metadata
            }
            
            result = self.client.table('groups').insert(data).execute()
            
            if result.data:
                group_id = result.data[0]['id']
                logger.info(f"Created group: {group.name} with ID: {group_id}")
                return group_id
                
        except Exception as e:
            logger.error(f"Failed to create group {group.name}: {e}")
            
        return None
    
    def get_group(self, group_jid: str) -> Optional[Group]:
        """Get group by JID from Supabase."""
        try:
            result = self.client.table('groups')\
                .select('*')\
                .eq('group_jid', group_jid)\
                .execute()
            
            if result.data:
                data = result.data[0]
                return Group(
                    id=data['id'],
                    group_jid=data['group_jid'],
                    name=data['name'],
                    img_url=data.get('img_url'),
                    member_count=data.get('member_count', 0),
                    created_at=datetime.fromisoformat(data['created_at'].replace('Z', '+00:00')) if data.get('created_at') else None,
                    updated_at=datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00')) if data.get('updated_at') else None,
                    metadata=data.get('metadata', {})
                )
                
        except Exception as e:
            logger.error(f"Failed to get group {group_jid}: {e}")
            
        return None
    
    def list_groups(self, limit: int = 50, offset: int = 0) -> List[Group]:
        """List all groups from Supabase."""
        try:
            result = self.client.table('groups')\
                .select('*')\
                .order('created_at', desc=True)\
                .range(offset, offset + limit - 1)\
                .execute()
            
            groups = []
            for data in result.data:
                group = Group(
                    id=data['id'],
                    group_jid=data['group_jid'],
                    name=data['name'],
                    img_url=data.get('img_url'),
                    member_count=data.get('member_count', 0),
                    created_at=datetime.fromisoformat(data['created_at'].replace('Z', '+00:00')) if data.get('created_at') else None,
                    metadata=data.get('metadata', {})
                )
                groups.append(group)
            
            return groups
            
        except Exception as e:
            logger.error(f"Failed to list groups: {e}")
            return []
    
    def update_group(self, group_jid: str, updates: Dict[str, Any]) -> bool:
        """Update group information in Supabase."""
        try:
            result = self.client.table('groups')\
                .update(updates)\
                .eq('group_jid', group_jid)\
                .execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Failed to update group {group_jid}: {e}")
            return False
    
    def delete_group(self, group_jid: str) -> bool:
        """Delete group from Supabase."""
        try:
            result = self.client.table('groups')\
                .delete()\
                .eq('group_jid', group_jid)\
                .execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Failed to delete group {group_jid}: {e}")
            return False
    
    def log_group_message(self, message: GroupMessage) -> Optional[str]:
        """Log a group message to Supabase."""
        try:
            data = {
                'group_jid': message.group_jid,
                'message_content': message.message_content,
                'message_id': message.message_id,
                'message_type': message.message_type,
                'media_url': message.media_url,
                'status': message.status,
                'sender_info': message.sender_info,
                'metadata': message.metadata
            }
            
            result = self.client.table('group_message_logs').insert(data).execute()
            
            if result.data:
                return result.data[0]['id']
                
        except Exception as e:
            logger.error(f"Failed to log group message: {e}")
            
        return None
    
    def get_group_messages(self, group_jid: str, limit: int = 50) -> List[GroupMessage]:
        """Get messages for a group from Supabase."""
        try:
            result = self.client.table('group_message_logs')\
                .select('*')\
                .eq('group_jid', group_jid)\
                .order('sent_at', desc=True)\
                .limit(limit)\
                .execute()
            
            messages = []
            for data in result.data:
                message = GroupMessage(
                    id=data['id'],
                    group_jid=data['group_jid'],
                    message_content=data['message_content'],
                    message_id=data.get('message_id'),
                    message_type=data.get('message_type', 'text'),
                    media_url=data.get('media_url'),
                    sent_at=datetime.fromisoformat(data['sent_at'].replace('Z', '+00:00')) if data.get('sent_at') else None,
                    status=data.get('status', 'sent'),
                    sender_info=data.get('sender_info', {}),
                    metadata=data.get('metadata', {})
                )
                messages.append(message)
            
            return messages
            
        except Exception as e:
            logger.error(f"Failed to get messages for group {group_jid}: {e}")
            return []
    
    def create_scheduled_message(self, scheduled_msg: ScheduledMessage) -> Optional[str]:
        """Create a scheduled message in Supabase."""
        try:
            data = {
                'message_content': scheduled_msg.message_content,
                'target_type': scheduled_msg.target_type,
                'target_ids': scheduled_msg.target_ids,
                'scheduled_time': scheduled_msg.scheduled_time.isoformat(),
                'status': scheduled_msg.status,
                'recurring_pattern': scheduled_msg.recurring_pattern,
                'recurring_end_date': scheduled_msg.recurring_end_date.isoformat() if scheduled_msg.recurring_end_date else None,
                'campaign_name': scheduled_msg.campaign_name,
                'created_by': scheduled_msg.created_by,
                'metadata': scheduled_msg.metadata
            }
            
            result = self.client.table('scheduled_messages').insert(data).execute()
            
            if result.data:
                return result.data[0]['id']
                
        except Exception as e:
            logger.error(f"Failed to create scheduled message: {e}")
            
        return None
    
    def get_scheduled_message(self, schedule_id: str) -> Optional[ScheduledMessage]:
        """Get scheduled message by ID from Supabase."""
        # Implementation similar to get_group
        pass
    
    def list_scheduled_messages(self, status: str = None, limit: int = 50) -> List[ScheduledMessage]:
        """List scheduled messages from Supabase."""
        # Implementation similar to list_groups
        pass
    
    def update_scheduled_message(self, schedule_id: str, updates: Dict[str, Any]) -> bool:
        """Update scheduled message in Supabase."""
        # Implementation similar to update_group
        pass
    
    def get_due_messages(self, current_time: datetime) -> List[ScheduledMessage]:
        """Get messages that are due for sending from Supabase."""
        try:
            result = self.client.table('scheduled_messages')\
                .select('*')\
                .eq('status', 'pending')\
                .lte('scheduled_time', current_time.isoformat())\
                .execute()
            
            # Convert to ScheduledMessage objects and return
            # Implementation details...
            return []
            
        except Exception as e:
            logger.error(f"Failed to get due messages: {e}")
            return []


class DatabaseManager:
    """
    Database manager that handles different database providers.
    This is the main interface for database operations.
    """
    
    def __init__(self, config: GroupMessagingConfig):
        self.config = config
        self.provider = self._create_provider()
        
    def _create_provider(self) -> DatabaseProvider:
        """Create appropriate database provider based on configuration."""
        if self.config.database_provider.lower() == "supabase":
            return SupabaseProvider(self.config)
        else:
            raise ValueError(f"Unsupported database provider: {self.config.database_provider}")
    
    def connect(self) -> bool:
        """Connect to database."""
        return self.provider.connect()
    
    def is_connected(self) -> bool:
        """Check if connected to database."""
        return self.provider.is_connected()
    
    # Delegate all operations to the provider
    def create_group(self, group: Group) -> Optional[str]:
        return self.provider.create_group(group)
    
    def get_group(self, group_jid: str) -> Optional[Group]:
        return self.provider.get_group(group_jid)
    
    def list_groups(self, limit: int = 50, offset: int = 0) -> List[Group]:
        return self.provider.list_groups(limit, offset)
    
    def update_group(self, group_jid: str, updates: Dict[str, Any]) -> bool:
        return self.provider.update_group(group_jid, updates)
    
    def delete_group(self, group_jid: str) -> bool:
        return self.provider.delete_group(group_jid)
    
    def log_group_message(self, message: GroupMessage) -> Optional[str]:
        return self.provider.log_group_message(message)
    
    def get_group_messages(self, group_jid: str, limit: int = 50) -> List[GroupMessage]:
        return self.provider.get_group_messages(group_jid, limit)
    
    def create_scheduled_message(self, scheduled_msg: ScheduledMessage) -> Optional[str]:
        return self.provider.create_scheduled_message(scheduled_msg)
    
    def get_scheduled_message(self, schedule_id: str) -> Optional[ScheduledMessage]:
        return self.provider.get_scheduled_message(schedule_id)
    
    def list_scheduled_messages(self, status: str = None, limit: int = 50) -> List[ScheduledMessage]:
        return self.provider.list_scheduled_messages(status, limit)
    
    def update_scheduled_message(self, schedule_id: str, updates: Dict[str, Any]) -> bool:
        return self.provider.update_scheduled_message(schedule_id, updates)
    
    def get_due_messages(self, current_time: datetime) -> List[ScheduledMessage]:
        return self.provider.get_due_messages(current_time) 