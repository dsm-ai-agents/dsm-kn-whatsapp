"""
WhatsApp Group Messaging Module
===============================
A standalone, reusable module for WhatsApp group messaging and scheduling.

Features:
- Group management (list, create, message)
- Bulk group messaging
- Message scheduling with recurring options
- Background job processing
- Database abstraction for easy integration

Author: Rian Infotech
Version: 1.0.0
License: MIT
"""

__version__ = "1.0.0"
__author__ = "Rian Infotech"

# Core exports for easy importing
from .services.group_service import GroupService
from .services.scheduler_service import SchedulerService
from .services.database_service import DatabaseService
from .api.routes import create_group_messaging_blueprint

# Models
from .models.group import Group, GroupMessage
from .models.schedule import ScheduledMessage
from .models.contact import Contact

# Configuration
from .config.settings import GroupMessagingConfig

__all__ = [
    # Services
    'GroupService',
    'SchedulerService', 
    'DatabaseService',
    
    # Core
    'create_group_messaging_blueprint',
    
    # Models
    'Group',
    'GroupMessage',
    'ScheduledMessage',
    'Contact',
    
    # Config
    'GroupMessagingConfig'
] 