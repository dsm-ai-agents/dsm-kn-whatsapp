"""
Rian Infotech WhatsApp AI Chatbot
==================================
A powerful WhatsApp chatbot powered by OpenAI's GPT models and WaSenderAPI.
Handles incoming messages, generates AI responses, and maintains conversation history.

Author: Rian Infotech
Version: 2.0
"""

import os
import json
import logging
import random
import time
from datetime import datetime
from typing import List, Dict, Optional, Tuple

import requests
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from openai import OpenAI

# Import bulk messaging functionality
from bulk_messaging import send_bulk_message_individual, parse_contacts_from_text, format_bulk_job_summary

# Import Supabase functionality
from supabase_client import get_supabase_manager

# ============================================================================
# CONFIGURATION & SETUP
# ============================================================================

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configure static files
app.static_folder = 'static'

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONSTANTS & CONFIGURATION
# ============================================================================

# Directory for storing conversation histories
CONVERSATIONS_DIR = 'conversations'

# API Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
WASENDER_API_TOKEN = os.getenv('WASENDER_API_TOKEN')
WASENDER_API_URL = "https://wasenderapi.com/api/send-message"

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

# Message splitting configuration
MAX_LINES_PER_MESSAGE = 3
MAX_CHARS_PER_LINE = 100

# Message delay configuration (in seconds)
MIN_MESSAGE_DELAY = 2.0
MAX_MESSAGE_DELAY = 4.0

# ============================================================================
# INITIALIZATION
# ============================================================================

def initialize_app() -> None:
    """Initialize the application with required directories and API clients."""
    
    # Create conversations directory if it doesn't exist
    if not os.path.exists(CONVERSATIONS_DIR):
        os.makedirs(CONVERSATIONS_DIR)
        logger.info(f"Created conversations directory at {CONVERSATIONS_DIR}")
    
    # Initialize OpenAI client
    global openai_client
    if OPENAI_API_KEY:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        logger.info("OpenAI client initialized successfully")
    else:
        logger.error("OPENAI_API_KEY not found in environment variables")
        openai_client = None


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


# Initialize app and load persona
initialize_app()
PERSONA_NAME, PERSONA_DESCRIPTION = load_bot_persona()

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
# MESSAGE PROCESSING
# ============================================================================

def split_long_message(text: str, max_lines: int = MAX_LINES_PER_MESSAGE, 
                      max_chars_per_line: int = MAX_CHARS_PER_LINE) -> List[str]:
    """
    Split a long message into smaller chunks for better WhatsApp readability.
    
    Args:
        text: The message text to split
        max_lines: Maximum lines per message chunk
        max_chars_per_line: Maximum characters per line
        
    Returns:
        List of message chunks
    """
    # First split by existing newlines (\\n represents intended message breaks)
    paragraphs = text.split('\\n')
    chunks = []
    current_chunk = []
    current_line_count = 0
    
    for paragraph in paragraphs:
        # Handle long paragraphs by splitting into smaller lines
        if len(paragraph) > max_chars_per_line:
            words = paragraph.split()
            current_line = []
            current_length = 0
            
            for word in words:
                if current_length + len(word) + 1 <= max_chars_per_line:
                    current_line.append(word)
                    current_length += len(word) + 1
                else:
                    # Line is full, start new chunk if needed
                    if current_line_count >= max_lines:
                        chunks.append('\n'.join(current_chunk))
                        current_chunk = []
                        current_line_count = 0
                    
                    current_chunk.append(' '.join(current_line))
                    current_line_count += 1
                    current_line = [word]
                    current_length = len(word)
            
            # Add remaining words
            if current_line:
                if current_line_count >= max_lines:
                    chunks.append('\n'.join(current_chunk))
                    current_chunk = []
                    current_line_count = 0
                current_chunk.append(' '.join(current_line))
                current_line_count += 1
        else:
            # Paragraph fits in one line
            if current_line_count >= max_lines:
                chunks.append('\n'.join(current_chunk))
                current_chunk = []
                current_line_count = 0
            current_chunk.append(paragraph)
            current_line_count += 1
    
    # Add any remaining content
    if current_chunk:
        chunks.append('\n'.join(current_chunk))
    
    return chunks


def extract_message_content(message_info: Dict) -> Tuple[Optional[str], str]:
    """
    Extract text content from WhatsApp message data.
    
    Args:
        message_info: Message information from webhook
        
    Returns:
        Tuple of (message_text, message_type)
    """
    message_text = None
    message_type = 'unknown'
    
    if message_info.get('message'):
        msg_content = message_info['message']
        
        # Handle regular conversation messages
        if 'conversation' in msg_content:
            message_text = msg_content['conversation']
            message_type = 'text'
            
        # Handle extended text messages (replies, mentions, etc.)
        elif 'extendedTextMessage' in msg_content and 'text' in msg_content['extendedTextMessage']:
            message_text = msg_content['extendedTextMessage']['text']
            message_type = 'text'
    
    return message_text, message_type


# ============================================================================
# AI RESPONSE GENERATION
# ============================================================================

def generate_ai_response(message_text: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
    """
    Generate AI response using OpenAI API.
    
    Args:
        message_text: The user's message
        conversation_history: Previous conversation context
        
    Returns:
        AI-generated response text
    """
    if not openai_client:
        logger.error("OpenAI client not initialized")
        return "Sorry, I'm having trouble connecting to my AI brain right now (API key issue)."
    
    try:
        # Prepare messages for OpenAI API
        messages = []
        
        # Add system prompt with persona
        messages.append({"role": "system", "content": PERSONA_DESCRIPTION})
        
        # Add conversation history if available
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add current user message
        messages.append({"role": "user", "content": message_text})
        
        logger.info(f"Sending message to OpenAI: {message_text[:200]}...")
        
        # Call OpenAI API
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",  # Cost-effective model
            messages=messages,
            max_tokens=1000,
            temperature=0.7
        )
        
        # Extract and return response
        if response and response.choices and len(response.choices) > 0:
            ai_response = response.choices[0].message.content.strip()
            logger.info(f"Generated AI response: {ai_response[:100]}...")
            return ai_response
        else:
            logger.error(f"OpenAI returned unexpected response: {response}")
            return "I received an unexpected response from my AI brain. Please try again."

    except Exception as e:
        logger.error(f"Error calling OpenAI API: {e}", exc_info=True)
        return "I'm having trouble processing that request. Please try again later."


# ============================================================================
# WHATSAPP MESSAGE SENDING
# ============================================================================

def send_whatsapp_message(recipient_number: str, message_content: str, 
                         message_type: str = 'text', media_url: Optional[str] = None) -> bool:
    """
    Send message via WaSenderAPI.
    
    Args:
        recipient_number: WhatsApp number to send to
        message_content: Text content of the message
        message_type: Type of message (text, image, video, audio, document)
        media_url: URL for media content (if applicable)
        
    Returns:
        True if message sent successfully, False otherwise
    """
    if not WASENDER_API_TOKEN:
        logger.error("WaSender API token not configured")
        return False

    # Prepare API request
    headers = {
        'Authorization': f'Bearer {WASENDER_API_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    # Clean recipient number (remove @s.whatsapp.net suffix)
    clean_number = recipient_number.split('@')[0] if '@' in recipient_number else recipient_number
    
    # Prepare payload based on message type
    payload = {'to': clean_number}

    if message_type == 'text':
        payload['text'] = message_content
    elif message_type == 'image' and media_url:
        payload['imageUrl'] = media_url
        if message_content:
            payload['text'] = message_content 
    elif message_type == 'video' and media_url:
        payload['videoUrl'] = media_url
        if message_content:
            payload['text'] = message_content
    elif message_type == 'audio' and media_url:
        payload['audioUrl'] = media_url
    elif message_type == 'document' and media_url:
        payload['documentUrl'] = media_url
        if message_content:
            payload['text'] = message_content
    else:
        logger.error(f"Unsupported message type or missing media URL: {message_type}")
        return False
    
    # Send message
    try:
        response = requests.post(WASENDER_API_URL, headers=headers, json=payload, timeout=20)
        response.raise_for_status()
        
        logger.info(f"Message sent to {recipient_number}: {response.json()}")
        return True
        
    except requests.exceptions.RequestException as e:
        status_code = getattr(e.response, 'status_code', 'N/A') if e.response else 'N/A'
        response_text = getattr(e.response, 'text', 'N/A') if e.response else 'N/A'
        
        logger.error(f"Failed to send message to {recipient_number} (Status: {status_code}): {e}")
        logger.error(f"Response: {response_text}")
        
        if status_code == 422:
            logger.error("WaSenderAPI 422 Error: Check payload format and WaSenderAPI documentation")
        
        return False
        
    except Exception as e:
        logger.error(f"Unexpected error sending WhatsApp message: {e}")
        return False


def send_complete_message(recipient_number: str, full_message: str) -> bool:
    """
    Send a complete message as a single WhatsApp message.
    Includes retry logic for failed attempts.
    
    Args:
        recipient_number: WhatsApp number to send to
        full_message: Complete message to send as one message
        
    Returns:
        True if message sent successfully, False otherwise
    """
    logger.info(f"Sending complete message to {recipient_number}")
    
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        # Send complete message
        if send_whatsapp_message(recipient_number, full_message):
            logger.info(f"Successfully sent complete message to {recipient_number}")
            return True
        else:
            retry_count += 1
            if retry_count < max_retries:
                retry_delay = random.uniform(3.0, 6.0)  # Longer delay for retries
                logger.warning(f"Message failed, retrying in {retry_delay:.1f}s (attempt {retry_count}/{max_retries})")
                time.sleep(retry_delay)
            else:
                logger.error(f"Failed to send message after {max_retries} attempts")
                return False
    
    return False


# ============================================================================
# WEBHOOK HANDLING
# ============================================================================

def is_self_sent_message(message_info: Dict) -> bool:
    """
    Check if the message was sent by the bot itself.
    
    Args:
        message_info: Message information from webhook
        
    Returns:
        True if message is from the bot, False otherwise
    """
    return message_info.get('key', {}).get('fromMe', False)


def is_system_message(message_info: Dict) -> bool:
    """
    Check if the message is a system message (not user content).
    
    Args:
        message_info: Message information from webhook
        
    Returns:
        True if it's a system message, False otherwise
    """
    return bool(message_info.get('messageStubType'))


def process_incoming_message(message_info: Dict) -> Tuple[bool, str]:
    """
    Process an incoming WhatsApp message and generate response.
    
    Args:
        message_info: Message information from webhook
        
    Returns:
        Tuple of (success, status_message)
    """
    # Extract sender information
    sender_number = message_info.get('key', {}).get('remoteJid')
    if not sender_number:
        return False, "Missing sender information"
    
    # Check for self-sent messages (prevent loops)
    if is_self_sent_message(message_info):
        message_id = message_info.get('key', {}).get('id', 'Unknown')
        logger.info(f"Ignoring self-sent message: {message_id}")
        return True, "Self-sent message ignored"
    
    # Handle system messages
    if is_system_message(message_info):
        stub_type = message_info.get('messageStubType')
        stub_params = message_info.get('messageStubParameters', [])
        logger.info(f"Received system message type {stub_type} from {sender_number}: {stub_params}")
        return True, "System message processed"
    
    # Extract message content
    message_text, message_type = extract_message_content(message_info)
    
    if message_type != 'text' or not message_text:
        logger.info(f"Received non-text or empty message from {sender_number}: type={message_type}")
        return True, "Non-text message ignored"
    
    # Process text message
    logger.info(f"Processing message from {sender_number}: {message_text}")
    
    # Load conversation history
    safe_user_id = sanitize_user_id(sender_number)
    conversation_history = load_conversation_history(safe_user_id)
    
    # Generate AI response
    ai_response = generate_ai_response(message_text, conversation_history)
    
    if not ai_response:
        return False, "Failed to generate AI response"
    
    # Send response
    if send_complete_message(sender_number, ai_response):
        # Save conversation to history
        conversation_history.append({'role': 'user', 'content': message_text})
        conversation_history.append({'role': 'assistant', 'content': ai_response})
        save_conversation_history(safe_user_id, conversation_history)
        
        return True, "Message processed successfully"
    else:
        return False, "Failed to send response"


# ============================================================================
# FLASK ROUTES
# ============================================================================

@app.errorhandler(500)
def handle_internal_error(e):
    """Handle internal server errors."""
    logger.error(f"Internal server error: {e}", exc_info=True)
    return jsonify(status='error', message='Internal server error occurred'), 500


@app.errorhandler(404)
def handle_not_found(e):
    """Handle 404 errors gracefully."""
    return jsonify(status='error', message='Endpoint not found'), 404


@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Handle incoming WhatsApp messages via webhook.
    
    This endpoint receives webhook events from WaSenderAPI when messages
    are sent to the connected WhatsApp number.
    """
    try:
        # Get webhook data
        webhook_data = request.json
        if not webhook_data:
            logger.warning("Received webhook with no JSON data")
            return jsonify({'status': 'error', 'message': 'No data received'}), 400
        
        logger.info(f"Received webhook data: {str(webhook_data)[:200]}...")
        
        # Check for message upsert event
        if (webhook_data.get('event') == 'messages.upsert' and 
            webhook_data.get('data') and 
            webhook_data['data'].get('messages')):
            
            message_info = webhook_data['data']['messages']
            success, status_message = process_incoming_message(message_info)
            
            return jsonify({
                'status': 'success' if success else 'error',
                'message': status_message
            }), 200
            
        else:
            # Handle other event types
            event_type = webhook_data.get('event', 'unknown')
            logger.info(f"Received non-message event: {event_type}")
            return jsonify({'status': 'success', 'message': f'Event {event_type} acknowledged'}), 200
            
    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Webhook processing failed'}), 500


@app.route('/', methods=['GET'])
def dashboard():
    """Serve the web control panel."""
    return render_template('index.html')


@app.route('/favicon.ico')
def favicon():
    """Handle favicon requests to prevent 404 errors."""
    return '', 204  # No content


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint to verify bot status."""
    supabase = get_supabase_manager()
    return jsonify({
        'status': 'healthy',
        'bot_name': PERSONA_NAME,
        'openai_configured': openai_client is not None,
        'wasender_configured': WASENDER_API_TOKEN is not None,
        'supabase_connected': supabase.is_connected()
    }), 200


@app.route('/send-message', methods=['POST'])
def send_outbound_message():
    """
    Send a message to a specific WhatsApp number.
    
    Expected JSON payload:
    {
        "phone_number": "919876543210",
        "message": "Hello! This is a test message from Rian Infotech bot."
    }
    """
    try:
        # Get request data
        data = request.json
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No JSON data provided'
            }), 400
        
        phone_number = data.get('phone_number')
        message = data.get('message')
        
        # Validate input
        if not phone_number:
            return jsonify({
                'status': 'error',
                'message': 'phone_number is required'
            }), 400
        
        if not message:
            return jsonify({
                'status': 'error',
                'message': 'message is required'
            }), 400
        
        # Clean phone number format
        clean_number = phone_number.strip().replace('+', '').replace('-', '').replace(' ', '')
        
        # Add @s.whatsapp.net suffix if not present
        if '@s.whatsapp.net' not in clean_number:
            recipient_id = f"{clean_number}@s.whatsapp.net"
        else:
            recipient_id = clean_number
        
        logger.info(f"Sending outbound message to {clean_number}: {message[:100]}...")
        
        # Send message
        if send_complete_message(recipient_id, message):
            # Save to conversation history as an assistant message
            safe_user_id = sanitize_user_id(recipient_id)
            conversation_history = load_conversation_history(safe_user_id)
            conversation_history.append({'role': 'assistant', 'content': message})
            save_conversation_history(safe_user_id, conversation_history)
            
            return jsonify({
                'status': 'success',
                'message': f'Message sent successfully to {clean_number}',
                'recipient': clean_number
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': f'Failed to send message to {clean_number}'
            }), 500
            
    except Exception as e:
        logger.error(f"Error in send_outbound_message: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Internal server error occurred'
        }), 500


@app.route('/start-conversation', methods=['POST'])
def start_ai_conversation():
    """
    Start an AI conversation with a specific WhatsApp number.
    The bot will introduce itself as Rian Infotech assistant.
    
    Expected JSON payload:
    {
        "phone_number": "919876543210",
        "custom_intro": "Optional custom introduction message"
    }
    """
    try:
        # Get request data
        data = request.json
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No JSON data provided'
            }), 400
        
        phone_number = data.get('phone_number')
        custom_intro = data.get('custom_intro')
        
        # Validate input
        if not phone_number:
            return jsonify({
                'status': 'error',
                'message': 'phone_number is required'
            }), 400
        
        # Clean phone number format
        clean_number = phone_number.strip().replace('+', '').replace('-', '').replace(' ', '')
        
        # Add @s.whatsapp.net suffix if not present
        if '@s.whatsapp.net' not in clean_number:
            recipient_id = f"{clean_number}@s.whatsapp.net"
        else:
            recipient_id = clean_number
        
        # Generate AI introduction message
        if custom_intro:
            intro_message = custom_intro
        else:
            # Use the persona to generate a natural introduction
            intro_prompt = "Generate a friendly introduction message for WhatsApp to start a conversation with a potential client."
            intro_message = generate_ai_response(intro_prompt)
        
        logger.info(f"Starting AI conversation with {clean_number}")
        
        # Send introduction message
        if send_complete_message(recipient_id, intro_message):
            # Save to conversation history
            safe_user_id = sanitize_user_id(recipient_id)
            conversation_history = load_conversation_history(safe_user_id)
            conversation_history.append({'role': 'assistant', 'content': intro_message})
            save_conversation_history(safe_user_id, conversation_history)
            
            return jsonify({
                'status': 'success',
                'message': f'AI conversation started with {clean_number}',
                'recipient': clean_number,
                'intro_message': intro_message
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': f'Failed to start conversation with {clean_number}'
            }), 500
            
    except Exception as e:
        logger.error(f"Error in start_ai_conversation: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Internal server error occurred'
        }), 500


@app.route('/send-bulk-message', methods=['POST'])
def send_bulk_message():
    """
    Send the same message to multiple WhatsApp numbers using individual loop method.
    Now with Supabase campaign tracking.
    
    Expected JSON payload:
    {
        "contacts": "919876543210\n918765432109\n917654321098",
        "message": "Hello everyone! This is an important update from Rian Infotech.",
        "campaign_name": "Optional campaign name"
    }
    """
    try:
        # Get request data
        data = request.json
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No JSON data provided'
            }), 400
        
        contacts_text = data.get('contacts', '')
        message = data.get('message', '')
        campaign_name = data.get('campaign_name', f"Campaign {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        # Validate input
        if not contacts_text.strip():
            return jsonify({
                'status': 'error',
                'message': 'Contacts list is required'
            }), 400
        
        if not message.strip():
            return jsonify({
                'status': 'error',
                'message': 'Message content is required'
            }), 400
        
        # Parse contacts from text
        contacts = parse_contacts_from_text(contacts_text)
        
        if not contacts:
            return jsonify({
                'status': 'error',
                'message': 'No valid phone numbers found in contacts list'
            }), 400
        
        # Check contact limit
        if len(contacts) > 50:  # Reasonable limit for safety
            return jsonify({
                'status': 'error',
                'message': f'Too many contacts ({len(contacts)}). Maximum 50 contacts allowed per batch.'
            }), 400
        
        logger.info(f"Starting bulk message to {len(contacts)} contacts")
        
        # Initialize Supabase campaign tracking
        supabase = get_supabase_manager()
        campaign_id = None
        
        if supabase.is_connected():
            # Create campaign in Supabase
            campaign_id = supabase.create_bulk_campaign(
                name=campaign_name,
                message_content=message,
                total_contacts=len(contacts)
            )
            
            if campaign_id:
                supabase.update_campaign_status(campaign_id, 'running')
        
        # Send bulk messages using our existing send_complete_message function
        bulk_job = send_bulk_message_individual(
            contacts=contacts,
            message=message,
            send_function=send_complete_message
        )
        
        # Update Supabase with results
        if campaign_id and supabase.is_connected():
            # Update campaign status
            supabase.update_campaign_status(
                campaign_id=campaign_id,
                status='completed',
                successful_sends=bulk_job.successful_sends,
                failed_sends=bulk_job.failed_sends
            )
            
            # Log individual message results
            for result in bulk_job.results:
                supabase.log_message_result(
                    campaign_id=campaign_id,
                    phone_number=result.contact,
                    success=result.success,
                    error_message=result.error_message if not result.success else None
                )
        
        # Prepare response
        response_data = {
            'status': 'success',
            'job_id': bulk_job.job_id,
            'campaign_id': campaign_id,
            'total_contacts': bulk_job.total_contacts,
            'successful_sends': bulk_job.successful_sends,
            'failed_sends': bulk_job.failed_sends,
            'summary': format_bulk_job_summary(bulk_job)
        }
        
        # Add failed contacts details if any
        if bulk_job.failed_sends > 0:
            failed_contacts = [
                {
                    'contact': result.contact,
                    'error': result.error_message
                }
                for result in bulk_job.results if not result.success
            ]
            response_data['failed_contacts'] = failed_contacts
        
        return jsonify(response_data), 200
            
    except Exception as e:
        logger.error(f"Error in send_bulk_message: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Internal server error occurred'
        }), 500


@app.route('/api/dashboard-stats', methods=['GET'])
def get_dashboard_stats():
    """Get dashboard statistics from Supabase."""
    try:
        supabase = get_supabase_manager()
        
        if not supabase.is_connected():
            return jsonify({
                'status': 'error',
                'message': 'Database not connected'
            }), 503
        
        stats = supabase.get_dashboard_stats()
        
        return jsonify({
            'status': 'success',
            'data': stats
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve dashboard statistics'
        }), 500


@app.route('/api/contacts', methods=['GET'])
def get_contacts():
    """Get contacts list with pagination."""
    try:
        supabase = get_supabase_manager()
        
        if not supabase.is_connected():
            return jsonify({
                'status': 'error',
                'message': 'Database not connected'
            }), 503
        
        # Get pagination parameters
        limit = min(int(request.args.get('limit', 20)), 100)  # Max 100 contacts per request
        offset = int(request.args.get('offset', 0))
        
        contacts = supabase.get_contacts(limit=limit, offset=offset)
        
        return jsonify({
            'status': 'success',
            'data': contacts,
            'pagination': {
                'limit': limit,
                'offset': offset,
                'count': len(contacts)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting contacts: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve contacts'
        }), 500


@app.route('/api/campaigns', methods=['GET'])
def get_recent_campaigns():
    """Get recent bulk campaigns."""
    try:
        supabase = get_supabase_manager()
        
        if not supabase.is_connected():
            return jsonify({
                'status': 'error',
                'message': 'Database not connected'
            }), 503
        
        limit = min(int(request.args.get('limit', 10)), 50)  # Max 50 campaigns per request
        campaigns = supabase.get_recent_campaigns(limit=limit)
        
        return jsonify({
            'status': 'success',
            'data': campaigns
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting campaigns: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve campaigns'
        }), 500


@app.route('/api/campaign/<campaign_id>', methods=['GET'])
def get_campaign_details(campaign_id):
    """Get detailed information about a specific campaign."""
    try:
        supabase = get_supabase_manager()
        
        if not supabase.is_connected():
            return jsonify({
                'status': 'error',
                'message': 'Database not connected'
            }), 503
        
        campaign = supabase.get_campaign_summary(campaign_id)
        
        if not campaign:
            return jsonify({
                'status': 'error',
                'message': 'Campaign not found'
            }), 404
        
        return jsonify({
            'status': 'success',
            'data': campaign
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting campaign details: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve campaign details'
        }), 500


@app.route('/api/conversations', methods=['GET'])
def get_conversations():
    """Get all conversations with contact details."""
    try:
        supabase = get_supabase_manager()
        
        if not supabase.is_connected():
            return jsonify({
                'status': 'error',
                'message': 'Database not connected'
            }), 503
        
        # Get pagination parameters
        limit = min(int(request.args.get('limit', 50)), 100)
        offset = int(request.args.get('offset', 0))
        
        # Query to get conversations with contact details
        conversations = supabase.client.table('conversations')\
            .select('*, contacts!inner(phone_number, name, created_at)')\
            .order('last_message_at', desc=True)\
            .range(offset, offset + limit - 1)\
            .execute()
        
        # Format the response
        formatted_conversations = []
        for conv in conversations.data:
            # Get last message for preview
            messages = conv.get('messages', [])
            last_message = messages[-1] if messages else None
            
            formatted_conversations.append({
                'id': conv['id'],
                'contact': {
                    'phone_number': conv['contacts']['phone_number'],
                    'name': conv['contacts']['name'] or conv['contacts']['phone_number'],
                    'created_at': conv['contacts']['created_at']
                },
                'last_message_at': conv['last_message_at'],
                'message_count': len(messages),
                'last_message_preview': last_message['content'][:100] + '...' if last_message and len(last_message['content']) > 100 else (last_message['content'] if last_message else 'No messages'),
                'last_message_role': last_message['role'] if last_message else None
            })
        
        return jsonify({
            'status': 'success',
            'data': formatted_conversations,
            'pagination': {
                'limit': limit,
                'offset': offset,
                'count': len(formatted_conversations)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting conversations: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve conversations'
        }), 500


@app.route('/api/conversation/<conversation_id>', methods=['GET'])
def get_conversation_details(conversation_id):
    """Get detailed conversation messages."""
    try:
        supabase = get_supabase_manager()
        
        if not supabase.is_connected():
            return jsonify({
                'status': 'error',
                'message': 'Database not connected'
            }), 503
        
        # Get conversation with contact details
        result = supabase.client.table('conversations')\
            .select('*, contacts!inner(phone_number, name, created_at)')\
            .eq('id', conversation_id)\
            .execute()
        
        if not result.data:
            return jsonify({
                'status': 'error',
                'message': 'Conversation not found'
            }), 404
        
        conversation = result.data[0]
        
        # Format the response
        formatted_conversation = {
            'id': conversation['id'],
            'contact': {
                'phone_number': conversation['contacts']['phone_number'],
                'name': conversation['contacts']['name'] or conversation['contacts']['phone_number'],
                'created_at': conversation['contacts']['created_at']
            },
            'messages': conversation.get('messages', []),
            'last_message_at': conversation['last_message_at'],
            'created_at': conversation['created_at']
        }
        
        return jsonify({
            'status': 'success',
            'data': formatted_conversation
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting conversation details: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve conversation details'
        }), 500


@app.route('/api/conversation/search', methods=['GET'])
def search_conversations():
    """Search conversations by contact name or phone number."""
    try:
        supabase = get_supabase_manager()
        
        if not supabase.is_connected():
            return jsonify({
                'status': 'error',
                'message': 'Database not connected'
            }), 503
        
        search_query = request.args.get('q', '').strip()
        if not search_query:
            return jsonify({
                'status': 'error',
                'message': 'Search query is required'
            }), 400
        
        # Search in phone numbers and names
        conversations = supabase.client.table('conversations')\
            .select('*, contacts!inner(phone_number, name, created_at)')\
            .or_(f'contacts.phone_number.ilike.%{search_query}%,contacts.name.ilike.%{search_query}%')\
            .order('last_message_at', desc=True)\
            .limit(20)\
            .execute()
        
        # Format the response
        formatted_conversations = []
        for conv in conversations.data:
            messages = conv.get('messages', [])
            last_message = messages[-1] if messages else None
            
            formatted_conversations.append({
                'id': conv['id'],
                'contact': {
                    'phone_number': conv['contacts']['phone_number'],
                    'name': conv['contacts']['name'] or conv['contacts']['phone_number'],
                    'created_at': conv['contacts']['created_at']
                },
                'last_message_at': conv['last_message_at'],
                'message_count': len(messages),
                'last_message_preview': last_message['content'][:100] + '...' if last_message and len(last_message['content']) > 100 else (last_message['content'] if last_message else 'No messages'),
                'last_message_role': last_message['role'] if last_message else None
            })
        
        return jsonify({
            'status': 'success',
            'data': formatted_conversations,
            'query': search_query
        }), 200
        
    except Exception as e:
        logger.error(f"Error searching conversations: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Failed to search conversations'
        }), 500


# ============================================================================
# CRM API ENDPOINTS
# ============================================================================

@app.route('/api/crm/contacts', methods=['GET'])
def get_crm_contacts():
    """Get contacts with CRM information."""
    try:
        supabase = get_supabase_manager()
        
        if not supabase.is_connected():
            return jsonify({
                'status': 'error',
                'message': 'Database not connected'
            }), 503
        
        # Get pagination parameters
        limit = min(int(request.args.get('limit', 20)), 100)
        offset = int(request.args.get('offset', 0))
        lead_status = request.args.get('status')
        
        # Build query
        query = supabase.client.table('contacts')\
            .select('id, phone_number, name, email, company, position, lead_status, lead_score, source, notes, last_contacted_at, next_follow_up_at, created_at')
        
        if lead_status:
            query = query.eq('lead_status', lead_status)
        
        result = query.order('lead_score', desc=True)\
            .range(offset, offset + limit - 1)\
            .execute()
        
        return jsonify({
            'status': 'success',
            'data': result.data or [],
            'pagination': {
                'limit': limit,
                'offset': offset,
                'count': len(result.data or [])
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting CRM contacts: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve CRM contacts'
        }), 500


@app.route('/api/crm/contact/<contact_id>', methods=['PUT'])
def update_crm_contact(contact_id):
    """Update contact CRM information."""
    try:
        supabase = get_supabase_manager()
        
        if not supabase.is_connected():
            return jsonify({
                'status': 'error',
                'message': 'Database not connected'
            }), 503
        
        data = request.json
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
        
        # Update contact
        success = supabase.update_contact_lead_info(
            contact_id=contact_id,
            name=data.get('name'),
            email=data.get('email'),
            lead_status=data.get('lead_status'),
            lead_score=data.get('lead_score'),
            source=data.get('source'),
            company=data.get('company'),
            position=data.get('position'),
            notes=data.get('notes'),
            next_follow_up_at=data.get('next_follow_up_at')
        )
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Contact updated successfully'
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to update contact'
            }), 500
            
    except Exception as e:
        logger.error(f"Error updating CRM contact: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500


@app.route('/api/crm/deals', methods=['GET'])
def get_crm_deals():
    """Get deals with contact information."""
    try:
        supabase = get_supabase_manager()
        
        if not supabase.is_connected():
            return jsonify({
                'status': 'error',
                'message': 'Database not connected'
            }), 503
        
        # Get query parameters
        contact_id = request.args.get('contact_id')
        stage = request.args.get('stage')
        limit = min(int(request.args.get('limit', 20)), 100)
        
        deals = supabase.get_deals(contact_id=contact_id, stage=stage, limit=limit)
        
        return jsonify({
            'status': 'success',
            'data': deals
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting CRM deals: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve deals'
        }), 500


@app.route('/api/crm/deals', methods=['POST'])
def create_crm_deal():
    """Create a new deal."""
    try:
        supabase = get_supabase_manager()
        
        if not supabase.is_connected():
            return jsonify({
                'status': 'error',
                'message': 'Database not connected'
            }), 503
        
        data = request.json
        if not data or not data.get('contact_id') or not data.get('title'):
            return jsonify({
                'status': 'error',
                'message': 'contact_id and title are required'
            }), 400
        
        deal_id = supabase.create_deal(
            contact_id=data['contact_id'],
            title=data['title'],
            description=data.get('description'),
            value=float(data.get('value', 0)),
            currency=data.get('currency', 'USD'),
            stage=data.get('stage', 'prospecting'),
            probability=int(data.get('probability', 0)),
            expected_close_date=data.get('expected_close_date')
        )
        
        if deal_id:
            return jsonify({
                'status': 'success',
                'message': 'Deal created successfully',
                'deal_id': deal_id
            }), 201
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to create deal'
            }), 500
            
    except Exception as e:
        logger.error(f"Error creating CRM deal: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500


@app.route('/api/crm/deal/<deal_id>', methods=['PUT'])
def update_crm_deal(deal_id):
    """Update a deal."""
    try:
        supabase = get_supabase_manager()
        
        if not supabase.is_connected():
            return jsonify({
                'status': 'error',
                'message': 'Database not connected'
            }), 503
        
        data = request.json
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
        
        success = supabase.update_deal(deal_id, **data)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Deal updated successfully'
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to update deal'
            }), 500
            
    except Exception as e:
        logger.error(f"Error updating CRM deal: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500


@app.route('/api/crm/tasks', methods=['GET'])
def get_crm_tasks():
    """Get tasks with contact and deal information."""
    try:
        supabase = get_supabase_manager()
        
        if not supabase.is_connected():
            return jsonify({
                'status': 'error',
                'message': 'Database not connected'
            }), 503
        
        # Get query parameters
        contact_id = request.args.get('contact_id')
        status = request.args.get('status')
        limit = min(int(request.args.get('limit', 20)), 100)
        
        tasks = supabase.get_tasks(contact_id=contact_id, status=status, limit=limit)
        
        return jsonify({
            'status': 'success',
            'data': tasks
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting CRM tasks: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve tasks'
        }), 500


@app.route('/api/crm/tasks', methods=['POST'])
def create_crm_task():
    """Create a new task."""
    try:
        supabase = get_supabase_manager()
        
        if not supabase.is_connected():
            return jsonify({
                'status': 'error',
                'message': 'Database not connected'
            }), 503
        
        data = request.json
        if not data or not data.get('title'):
            return jsonify({
                'status': 'error',
                'message': 'title is required'
            }), 400
        
        task_id = supabase.create_task(
            contact_id=data.get('contact_id'),
            deal_id=data.get('deal_id'),
            title=data['title'],
            description=data.get('description'),
            task_type=data.get('task_type', 'follow_up'),
            priority=data.get('priority', 'medium'),
            due_date=data.get('due_date')
        )
        
        if task_id:
            return jsonify({
                'status': 'success',
                'message': 'Task created successfully',
                'task_id': task_id
            }), 201
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to create task'
            }), 500
            
    except Exception as e:
        logger.error(f"Error creating CRM task: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500


@app.route('/api/crm/task/<task_id>/complete', methods=['POST'])
def complete_crm_task(task_id):
    """Mark a task as completed."""
    try:
        supabase = get_supabase_manager()
        
        if not supabase.is_connected():
            return jsonify({
                'status': 'error',
                'message': 'Database not connected'
            }), 503
        
        success = supabase.complete_task(task_id)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Task completed successfully'
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to complete task'
            }), 500
            
    except Exception as e:
        logger.error(f"Error completing CRM task: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500


@app.route('/api/crm/task/<task_id>', methods=['DELETE'])
def delete_crm_task(task_id):
    """Delete a task."""
    try:
        supabase = get_supabase_manager()
        
        if not supabase.is_connected():
            return jsonify({
                'status': 'error',
                'message': 'Database not connected'
            }), 503
        
        # Delete task from database
        result = supabase.client.table('tasks').delete().eq('id', task_id).execute()
        
        if result.data:
            return jsonify({
                'status': 'success',
                'message': 'Task deleted successfully'
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Task not found or failed to delete'
            }), 404
            
    except Exception as e:
        logger.error(f"Error deleting CRM task: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500


@app.route('/api/crm/contact/<contact_id>/activities', methods=['GET'])
def get_contact_activities(contact_id):
    """Get activities for a specific contact."""
    try:
        supabase = get_supabase_manager()
        
        if not supabase.is_connected():
            return jsonify({
                'status': 'error',
                'message': 'Database not connected'
            }), 503
        
        limit = min(int(request.args.get('limit', 20)), 100)
        activities = supabase.get_contact_activities(contact_id, limit=limit)
        
        return jsonify({
            'status': 'success',
            'data': activities
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting contact activities: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve activities'
        }), 500


@app.route('/api/crm/activity', methods=['POST'])
def log_crm_activity():
    """Log a new activity."""
    try:
        supabase = get_supabase_manager()
        
        if not supabase.is_connected():
            return jsonify({
                'status': 'error',
                'message': 'Database not connected'
            }), 503
        
        data = request.json
        if not data or not data.get('contact_id') or not data.get('activity_type') or not data.get('title'):
            return jsonify({
                'status': 'error',
                'message': 'contact_id, activity_type, and title are required'
            }), 400
        
        success = supabase.log_activity(
            contact_id=data['contact_id'],
            activity_type=data['activity_type'],
            title=data['title'],
            description=data.get('description'),
            deal_id=data.get('deal_id'),
            duration_minutes=data.get('duration_minutes'),
            outcome=data.get('outcome')
        )
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Activity logged successfully'
            }), 201
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to log activity'
            }), 500
            
    except Exception as e:
        logger.error(f"Error logging CRM activity: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500


@app.route('/api/crm/lead-score/<contact_id>', methods=['POST'])
def calculate_contact_lead_score(contact_id):
    """Calculate and update lead score for a contact."""
    try:
        supabase = get_supabase_manager()
        
        if not supabase.is_connected():
            return jsonify({
                'status': 'error',
                'message': 'Database not connected'
            }), 503
        
        score = supabase.calculate_lead_score(contact_id)
        
        return jsonify({
            'status': 'success',
            'message': 'Lead score calculated successfully',
            'lead_score': score
        }), 200
        
    except Exception as e:
        logger.error(f"Error calculating lead score: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Failed to calculate lead score'
        }), 500


# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    logger.info(f"Starting {PERSONA_NAME} WhatsApp Bot...")
    logger.info(f"OpenAI configured: {openai_client is not None}")
    logger.info(f"WaSender configured: {WASENDER_API_TOKEN is not None}")
    
    # Run Flask app in development mode
    app.run(debug=True, port=5001, host='0.0.0.0')
