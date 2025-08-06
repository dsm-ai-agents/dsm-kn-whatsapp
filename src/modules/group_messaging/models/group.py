"""
Group Data Models
================
Data models for WhatsApp groups and group messages.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class GroupStatus(Enum):
    """Group status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


@dataclass
class Group:
    """
    WhatsApp Group data model.
    
    Attributes:
        id: Unique identifier (UUID)
        group_jid: WhatsApp group JID (e.g., "123456789-987654321@g.us")
        name: Group display name
        img_url: Group profile image URL
        status: Group status (active, inactive, archived)
        member_count: Number of group members
        created_at: Group creation timestamp
        updated_at: Last update timestamp
        metadata: Additional group metadata
    """
    group_jid: str
    name: str
    id: Optional[str] = None
    img_url: Optional[str] = None
    status: GroupStatus = GroupStatus.ACTIVE
    member_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-initialization validation."""
        if not self.group_jid:
            raise ValueError("group_jid is required")
        
        if not self.name:
            raise ValueError("name is required")
        
        # Validate group JID format (basic validation)
        if not self.group_jid.endswith("@g.us"):
            raise ValueError("Invalid group JID format")
    
    @classmethod
    def from_wasender_api(cls, api_data: Dict[str, Any]) -> 'Group':
        """
        Create Group instance from Wasender API response.
        
        Args:
            api_data: Raw API response data
            
        Returns:
            Group instance
        """
        return cls(
            group_jid=api_data.get('jid'),
            name=api_data.get('name', 'Unknown Group'),
            img_url=api_data.get('imgUrl'),
            metadata={'raw_api_data': api_data}
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'group_jid': self.group_jid,
            'name': self.name,
            'img_url': self.img_url,
            'status': self.status.value if isinstance(self.status, GroupStatus) else self.status,
            'member_count': self.member_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'metadata': self.metadata
        }


@dataclass
class GroupMessage:
    """
    Group message data model.
    
    Attributes:
        id: Unique identifier
        group_jid: Target group JID
        message_content: Message text content
        message_id: WhatsApp message ID (from API response)
        message_type: Type of message (text, image, video, etc.)
        media_url: URL for media content (if applicable)
        sent_at: Message send timestamp
        status: Message delivery status
        sender_info: Information about who sent the message
        metadata: Additional message metadata
    """
    group_jid: str
    message_content: str
    id: Optional[str] = None
    message_id: Optional[str] = None
    message_type: str = "text"
    media_url: Optional[str] = None
    sent_at: Optional[datetime] = None
    status: str = "sent"
    wasender_message_id: Optional[str] = None
    error_message: Optional[str] = None
    sender_info: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-initialization validation."""
        if not self.group_jid:
            raise ValueError("group_jid is required")
        
        if not self.message_content and self.message_type == "text":
            raise ValueError("message_content is required for text messages")
        
        if self.sent_at is None:
            self.sent_at = datetime.utcnow()
    
    @classmethod
    def create_text_message(cls, group_jid: str, content: str, **kwargs) -> 'GroupMessage':
        """
        Create a text message for a group.
        
        Args:
            group_jid: Target group JID
            content: Message text content
            **kwargs: Additional message attributes
            
        Returns:
            GroupMessage instance
        """
        return cls(
            group_jid=group_jid,
            message_content=content,
            message_type="text",
            **kwargs
        )
    
    @classmethod
    def create_media_message(cls, group_jid: str, media_url: str, 
                           message_type: str, caption: str = "", **kwargs) -> 'GroupMessage':
        """
        Create a media message for a group.
        
        Args:
            group_jid: Target group JID
            media_url: URL of the media file
            message_type: Type of media (image, video, audio, document)
            caption: Optional caption text
            **kwargs: Additional message attributes
            
        Returns:
            GroupMessage instance
        """
        return cls(
            group_jid=group_jid,
            message_content=caption,
            media_url=media_url,
            message_type=message_type,
            **kwargs
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'group_jid': self.group_jid,
            'message_content': self.message_content,
            'message_id': self.message_id,
            'message_type': self.message_type,
            'media_url': self.media_url,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'status': self.status,
            'sender_info': self.sender_info,
            'metadata': self.metadata
        }


@dataclass
class GroupCreationRequest:
    """
    Request model for creating new groups.
    
    Attributes:
        name: Group name
        participants: List of participant phone numbers/JIDs
        description: Optional group description
    """
    name: str
    participants: List[str] = field(default_factory=list)
    description: Optional[str] = None
    
    def __post_init__(self):
        """Post-initialization validation."""
        if not self.name:
            raise ValueError("Group name is required")
        
        if not self.name.strip():
            raise ValueError("Group name cannot be empty")
        
        # Validate participants list
        if self.participants and not isinstance(self.participants, list):
            raise ValueError("Participants must be a list")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API requests."""
        return {
            'name': self.name.strip(),
            'participants': self.participants,
            'description': self.description
        } 