"""
WhatsApp AI Chatbot - Conversation Manager
=========================================
Handles conversation history management, loading/saving conversations,
and user ID sanitization.

Author: Rian Infotech
Version: 2.2 (Structured)
"""

import os
import json
import logging
from typing import List, Dict

# Import configuration and core functionality
from src.config.config import CONVERSATIONS_DIR
from src.core.supabase_client import get_supabase_manager

# Configure logging
logger = logging.getLogger(__name__)

# ============================================================================
# DIRECTORY INITIALIZATION
# ============================================================================

def initialize_conversations_directory() -> None:
    """Initialize the conversations directory if it doesn't exist."""
    if not os.path.exists(CONVERSATIONS_DIR):
        os.makedirs(CONVERSATIONS_DIR)
        logger.info(f"Created conversations directory at {CONVERSATIONS_DIR}")


# Initialize directory on module import
initialize_conversations_directory()

# ============================================================================
# USER ID UTILITIES
# ============================================================================

def sanitize_user_id(raw_user_id: str) -> str:
    """
    Convert raw user ID to a safe filename.
    
    Args:
        raw_user_id: Raw user ID from WhatsApp
        
    Returns:
        Sanitized string safe for use as filename
    """
    return "".join(c if c.isalnum() else '_' for c in raw_user_id)


# ============================================================================
# CONVERSATION HISTORY MANAGEMENT
# ============================================================================

def load_conversation_history(user_id: str) -> List[Dict[str, str]]:
    """
    Load conversation history for a specific user from Supabase.
    
    Args:
        user_id: Unique identifier for the user (phone number)
        
    Returns:
        List of conversation messages in OpenAI format
    """
    supabase = get_supabase_manager()
    
    if supabase.is_connected():
        # Use Supabase for data storage
        return supabase.load_conversation_history(user_id)
    else:
        # Fallback to JSON files if Supabase not available
        logger.warning("Supabase not connected, falling back to JSON files")
        file_path = os.path.join(CONVERSATIONS_DIR, f"{user_id}.json")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                history = json.load(file)
                
            # Validate history format (OpenAI format: role + content)
            if isinstance(history, list) and all(
                isinstance(item, dict) and 'role' in item and 'content' in item 
                for item in history
            ):
                return history
            else:
                logger.warning(f"Invalid history format in {file_path}. Starting fresh.")
                return []
                
        except FileNotFoundError:
            # New conversation - no history file yet
            return []
            
        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON from {file_path}. Starting fresh.")
            return []
            
        except Exception as e:
            logger.error(f"Unexpected error loading history from {file_path}: {e}")
            return []


def save_conversation_history(user_id: str, history: List[Dict[str, str]]) -> None:
    """
    Save conversation history for a specific user to Supabase.
    
    Args:
        user_id: Unique identifier for the user (phone number)
        history: List of conversation messages to save
    """
    supabase = get_supabase_manager()
    
    if supabase.is_connected():
        # Use Supabase for data storage
        supabase.save_conversation_history(user_id, history)
    else:
        # Fallback to JSON files if Supabase not available
        logger.warning("Supabase not connected, falling back to JSON files")
        file_path = os.path.join(CONVERSATIONS_DIR, f"{user_id}.json")
        
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(history, file, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving conversation history to {file_path}: {e}") 