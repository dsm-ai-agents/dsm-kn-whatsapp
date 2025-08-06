"""
Custom Exceptions for Group Messaging Module
============================================
Defines specific exception types for better error handling.
"""


class GroupMessagingError(Exception):
    """Base exception for all group messaging related errors."""
    pass


class APIError(GroupMessagingError):
    """Raised when external API calls fail."""
    pass


class ValidationError(GroupMessagingError):
    """Raised when input validation fails."""
    pass


class DatabaseError(GroupMessagingError):
    """Raised when database operations fail."""
    pass


class SchedulingError(GroupMessagingError):
    """Raised when message scheduling operations fail."""
    pass


class ConfigurationError(GroupMessagingError):
    """Raised when module configuration is invalid."""
    pass 