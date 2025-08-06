"""
Encryption Utilities
===================
Shared encryption/decryption functions for API keys.
"""

import os
import logging
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

# Get encryption key from environment or generate one
ENCRYPTION_KEY = os.environ.get('API_KEY_ENCRYPTION_KEY')
if not ENCRYPTION_KEY:
    # Generate a key for development (in production, this should be stored securely)
    ENCRYPTION_KEY = Fernet.generate_key().decode()
    logger.warning("Using generated encryption key. Set API_KEY_ENCRYPTION_KEY environment variable in production.")

cipher_suite = Fernet(ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY)

def encrypt_api_key(api_key: str) -> str:
    """Encrypt API key for secure storage."""
    return cipher_suite.encrypt(api_key.encode()).decode()

def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt API key for use."""
    return cipher_suite.decrypt(encrypted_key.encode()).decode() 