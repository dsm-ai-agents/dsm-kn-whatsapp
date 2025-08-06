"""
WhatsApp Contact Models
======================
Data models for WhatsApp contacts.
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Contact:
    """Represents a WhatsApp contact from Wasender API."""
    jid: str  # Contact JID (phone number)
    name: Optional[str] = None  # Contact name
    notify: Optional[str] = None  # Contact display name
    verified_name: Optional[str] = None  # Verified business name
    img_url: Optional[str] = None  # Profile picture URL
    status: Optional[str] = None  # WhatsApp status message
    is_business: bool = False  # Whether this is a business account
    last_seen: Optional[datetime] = None  # Last seen timestamp
    metadata: dict = None  # Additional metadata
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        
        # Validate JID format
        if not self.jid or not isinstance(self.jid, str):
            raise ValueError("Contact JID is required and must be a string")
    
    @property
    def display_name(self) -> str:
        """Get the best available display name for the contact."""
        return (
            self.verified_name or 
            self.notify or 
            self.name or 
            f"Contact {self.jid}"
        )
    
    @property
    def phone_number(self) -> str:
        """Extract phone number from JID."""
        if "@" in self.jid:
            return self.jid.split("@")[0]
        return self.jid
    
    def to_dict(self) -> dict:
        """Convert contact to dictionary format."""
        return {
            "jid": self.jid,
            "name": self.name,
            "notify": self.notify,
            "verified_name": self.verified_name,
            "img_url": self.img_url,
            "status": self.status,
            "is_business": self.is_business,
            "display_name": self.display_name,
            "phone_number": self.phone_number,
            "metadata": self.metadata
        } 