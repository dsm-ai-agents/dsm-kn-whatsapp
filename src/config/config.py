"""
Configuration settings for the WhatsApp AI Chatbot
==================================================
Centralized configuration management for all application settings.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================================================
# API CONFIGURATION
# ============================================================================

# OpenAI Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# WaSender API Configuration
WASENDER_API_TOKEN = os.getenv('WASENDER_API_TOKEN')
WASENDER_API_URL = "https://wasenderapi.com/api/send-message"

# ============================================================================
# DIRECTORY CONFIGURATION
# ============================================================================

# Directory for storing conversation histories (fallback)
CONVERSATIONS_DIR = 'conversations'

# ============================================================================
# PERSONA CONFIGURATION
# ============================================================================

# Persona Configuration
PERSONA_FILE_PATH = 'persona.json'
DEFAULT_PERSONA_NAME = "Assistant"
DEFAULT_PERSONA_DESCRIPTION = "You are a helpful assistant."
DEFAULT_BASE_PROMPT = (
    "You are a helpful and concise AI assistant replying in a WhatsApp chat. "
    "Do not use Markdown formatting. Keep your answers short, friendly, and easy to read. "
    "If your response is longer than 3 lines, split it into multiple messages using \\n every 3 lines. "
    "Each \\n means a new WhatsApp message. Avoid long paragraphs or unnecessary explanations."
)

# ============================================================================
# MESSAGE CONFIGURATION
# ============================================================================

# Message splitting configuration
MAX_LINES_PER_MESSAGE = 3
MAX_CHARS_PER_LINE = 100

# Message delay configuration (in seconds)
MIN_MESSAGE_DELAY = 2.0
MAX_MESSAGE_DELAY = 4.0

# ============================================================================
# FLASK CONFIGURATION
# ============================================================================

# Flask Configuration
FLASK_HOST = '0.0.0.0'
FLASK_PORT = 5001
FLASK_DEBUG = True 

# ============================================================================
# AI INTENT DETECTION CONFIGURATION
# ============================================================================

# Minimum confidence threshold for AI intent detection
AI_INTENT_CONFIDENCE_THRESHOLD = float(os.getenv('AI_INTENT_CONFIDENCE_THRESHOLD', '0.7'))

# Whether to enable AI intent detection (fallback to pattern matching if disabled)
AI_INTENT_DETECTION_ENABLED = os.getenv('AI_INTENT_DETECTION_ENABLED', 'true').lower() == 'true'

# OpenAI model to use for intent detection
AI_INTENT_MODEL = os.getenv('AI_INTENT_MODEL', 'gpt-3.5-turbo')

# Whether to log intent analysis to Supabase
AI_INTENT_LOGGING_ENABLED = os.getenv('AI_INTENT_LOGGING_ENABLED', 'true').lower() == 'true'

# ============================================================================
# LEAD QUALIFICATION & CALENDLY CONFIGURATION
# ============================================================================

# Lead qualification AI settings - Made more selective
LEAD_QUALIFICATION_CONFIDENCE_THRESHOLD = float(os.getenv('LEAD_QUALIFICATION_CONFIDENCE_THRESHOLD', '0.85'))  # Increased from 0.75
LEAD_QUALIFICATION_ENABLED = os.getenv('LEAD_QUALIFICATION_ENABLED', 'true').lower() == 'true'
LEAD_QUALIFICATION_MODEL = os.getenv('LEAD_QUALIFICATION_MODEL', 'gpt-3.5-turbo')
LEAD_QUALIFICATION_LOGGING_ENABLED = os.getenv('LEAD_QUALIFICATION_LOGGING_ENABLED', 'true').lower() == 'true'

# Calendly integration settings
CALENDLY_DISCOVERY_CALL_URL = os.getenv('CALENDLY_DISCOVERY_CALL_URL', 'https://calendly.com/your-company/discovery-call')
CALENDLY_AUTO_SEND_ENABLED = os.getenv('CALENDLY_AUTO_SEND_ENABLED', 'true').lower() == 'true'
CALENDLY_COOLDOWN_HOURS = int(os.getenv('CALENDLY_COOLDOWN_HOURS', '24'))  # Hours to wait before sending another Calendly invite

# Lead scoring settings - Made more selective
QUALIFIED_LEAD_MIN_SCORE = int(os.getenv('QUALIFIED_LEAD_MIN_SCORE', '80'))  # Increased from 70
DISCOVERY_CALL_LEAD_SCORE_BOOST = int(os.getenv('DISCOVERY_CALL_LEAD_SCORE_BOOST', '30')) 