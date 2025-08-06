"""
WhatsApp AI Chatbot - Persona Manager
====================================
Handles bot personality configuration loading and management.

Author: Rian Infotech
Version: 2.2 (Structured)
"""

import json
import logging
from typing import Tuple

# Import configuration
from src.config.config import (
    PERSONA_FILE_PATH,
    DEFAULT_PERSONA_NAME,
    DEFAULT_PERSONA_DESCRIPTION,
    DEFAULT_BASE_PROMPT
)

# Configure logging
logger = logging.getLogger(__name__)

# ============================================================================
# PERSONA MANAGEMENT
# ============================================================================

def load_bot_persona() -> Tuple[str, str]:
    """
    Load bot persona configuration from JSON file.
    
    Returns:
        Tuple of (persona_name, persona_description)
    """
    try:
        with open(PERSONA_FILE_PATH, 'r', encoding='utf-8') as file:
            persona_data = json.load(file)
            
        # Extract persona components
        persona_name = persona_data.get('name', DEFAULT_PERSONA_NAME)
        custom_description = persona_data.get('description', DEFAULT_PERSONA_DESCRIPTION)
        base_prompt = persona_data.get('base_prompt', DEFAULT_BASE_PROMPT)
        
        # Combine base prompt and description
        full_persona_description = f"{base_prompt}\n\n{custom_description}"
        
        logger.info(f"Successfully loaded persona: {persona_name}")
        return persona_name, full_persona_description
        
    except FileNotFoundError:
        logger.warning(f"Persona file not found at {PERSONA_FILE_PATH}. Using default persona.")
        return DEFAULT_PERSONA_NAME, DEFAULT_BASE_PROMPT
        
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from {PERSONA_FILE_PATH}. Using default persona.")
        return DEFAULT_PERSONA_NAME, DEFAULT_BASE_PROMPT
        
    except Exception as e:
        logger.error(f"Unexpected error loading persona: {e}. Using default persona.")
        return DEFAULT_PERSONA_NAME, DEFAULT_BASE_PROMPT


# Load persona on module import
PERSONA_NAME, PERSONA_DESCRIPTION = load_bot_persona() 