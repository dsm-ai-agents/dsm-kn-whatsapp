"""
Group Messaging Module Configuration
====================================
Centralized configuration for the group messaging module.
Designed to be easily configurable for different environments.
"""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class GroupMessagingConfig:
    """Configuration class for Group Messaging Module."""
    
    # WhatsApp API Configuration
    whatsapp_api_provider: str = "wasender"  # Can be extended to support other providers
    whatsapp_api_token: Optional[str] = None
    whatsapp_api_url: str = "https://www.wasenderapi.com/api"
    
    # Database Configuration
    database_provider: str = "supabase"  # Can be "supabase", "postgresql", etc.
    database_url: Optional[str] = None
    database_key: Optional[str] = None  # For Supabase
    
    # Scheduling Configuration
    scheduler_enabled: bool = True
    scheduler_timezone: str = "UTC"
    max_scheduled_messages: int = 1000
    scheduler_check_interval: int = 60  # seconds
    
    # Rate Limiting
    rate_limit_enabled: bool = True
    messages_per_minute: int = 20
    messages_per_hour: int = 500
    
    # Retry Configuration
    max_retries: int = 3
    retry_delay_seconds: int = 5
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Module-specific settings
    module_name: str = "group_messaging"
    module_version: str = "1.0.0"
    
    # Additional settings can be added here
    extra_settings: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_env(cls, prefix: str = "GROUP_MSG_") -> 'GroupMessagingConfig':
        """
        Create configuration from environment variables.
        
        Args:
            prefix: Environment variable prefix (default: GROUP_MSG_)
            
        Returns:
            GroupMessagingConfig instance
        """
        return cls(
            whatsapp_api_provider=os.getenv(f'{prefix}WHATSAPP_PROVIDER', 'wasender'),
            whatsapp_api_token=os.getenv(f'{prefix}WHATSAPP_TOKEN') or os.getenv('WASENDER_API_TOKEN'),
            whatsapp_api_url=os.getenv(f'{prefix}WHATSAPP_URL', 'https://wasenderapi.com/api'),
            
            database_provider=os.getenv(f'{prefix}DB_PROVIDER', 'supabase'),
            database_url=os.getenv(f'{prefix}DB_URL') or os.getenv('SUPABASE_URL'),
            database_key=os.getenv(f'{prefix}DB_KEY') or os.getenv('SUPABASE_KEY'),
            
            scheduler_enabled=os.getenv(f'{prefix}SCHEDULER_ENABLED', 'true').lower() == 'true',
            scheduler_timezone=os.getenv(f'{prefix}TIMEZONE', 'UTC'),
            max_scheduled_messages=int(os.getenv(f'{prefix}MAX_SCHEDULED', '1000')),
            scheduler_check_interval=int(os.getenv(f'{prefix}CHECK_INTERVAL', '60')),
            
            rate_limit_enabled=os.getenv(f'{prefix}RATE_LIMIT', 'true').lower() == 'true',
            messages_per_minute=int(os.getenv(f'{prefix}MSG_PER_MIN', '20')),
            messages_per_hour=int(os.getenv(f'{prefix}MSG_PER_HOUR', '500')),
            
            max_retries=int(os.getenv(f'{prefix}MAX_RETRIES', '3')),
            retry_delay_seconds=int(os.getenv(f'{prefix}RETRY_DELAY', '5')),
            
            log_level=os.getenv(f'{prefix}LOG_LEVEL', 'INFO'),
        )
    
    def validate(self) -> bool:
        """
        Validate the configuration.
        
        Returns:
            True if configuration is valid
            
        Raises:
            ValueError: If required configuration is missing
        """
        if not self.whatsapp_api_token:
            raise ValueError("WhatsApp API token is required")
        
        if not self.database_url:
            raise ValueError("Database URL is required")
        
        if self.database_provider == "supabase" and not self.database_key:
            raise ValueError("Database key is required for Supabase")
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'whatsapp_api_provider': self.whatsapp_api_provider,
            'whatsapp_api_url': self.whatsapp_api_url,
            'database_provider': self.database_provider,
            'scheduler_enabled': self.scheduler_enabled,
            'scheduler_timezone': self.scheduler_timezone,
            'rate_limit_enabled': self.rate_limit_enabled,
            'messages_per_minute': self.messages_per_minute,
            'messages_per_hour': self.messages_per_hour,
            'max_retries': self.max_retries,
            'log_level': self.log_level,
            'module_name': self.module_name,
            'module_version': self.module_version,
        }


# Default configuration instance
default_config = GroupMessagingConfig.from_env() 