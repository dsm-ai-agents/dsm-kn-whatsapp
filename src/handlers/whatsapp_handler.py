"""
WhatsApp AI Chatbot - WhatsApp Handler
=====================================
Handles WhatsApp API integration via WaSenderAPI,
message sending, and retry logic.

Author: Rian Infotech
Version: 2.2 (Structured)
"""

import logging
import random
import time
from typing import Optional, List
import requests

# Import configuration
from src.config.config import WASENDER_API_TOKEN, WASENDER_API_URL, MAX_LINES_PER_MESSAGE, MAX_CHARS_PER_LINE

# Configure logging
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION VALIDATION
# ============================================================================

def is_wasender_configured() -> bool:
    """Check if WaSender API is properly configured."""
    return WASENDER_API_TOKEN is not None


# ============================================================================
# MESSAGE SPLITTING UTILITIES
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


# ============================================================================
# WHATSAPP MESSAGE SENDING
# ============================================================================

def send_whatsapp_message(recipient_number: str, message_content: str, 
                         message_type: str = 'text', media_url: Optional[str] = None) -> tuple[bool, Optional[str]]:
    """
    Send message via WaSenderAPI.
    
    Args:
        recipient_number: WhatsApp number to send to
        message_content: Text content of the message
        message_type: Type of message (text, image, video, audio, document)
        media_url: URL for media content (if applicable)
        
    Returns:
        Tuple of (success: bool, message_id: Optional[str])
    """
    if not WASENDER_API_TOKEN:
        logger.error("WaSender API token not configured")
        return False, None

    # Prepare API request
    headers = {
        'Authorization': f'Bearer {WASENDER_API_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    # Clean recipient number (remove @s.whatsapp.net suffix)
    clean_number = recipient_number.split('@')[0] if '@' in recipient_number else recipient_number
    
    # Ensure proper country code format for Indian numbers
    if clean_number.startswith('91') and len(clean_number) == 12:
        # Already has country code (91xxxxxxxxxx)
        formatted_number = clean_number
    elif len(clean_number) == 10 and clean_number.startswith(('6', '7', '8', '9')):
        # Indian mobile number without country code (xxxxxxxxxx)
        formatted_number = f"91{clean_number}"
    else:
        # Use as-is for other formats
        formatted_number = clean_number
    
    logger.debug(f"Phone number formatting: {recipient_number} -> {clean_number} -> {formatted_number}")
    
    # Prepare payload based on message type
    payload = {'to': formatted_number}

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
        return False, None
    
    # Send message
    try:
        response = requests.post(WASENDER_API_URL, headers=headers, json=payload, timeout=20)
        response.raise_for_status()
        
        response_data = response.json()
        logger.info(f"Message sent to {recipient_number}: {response_data}")
        
        # Try to extract message ID from response
        message_id = None
        if isinstance(response_data, dict):
            # Debug: Log what we're looking for
            logger.debug(f"Extracting message ID from response: {response_data}")
            
            # WASender API specific field names (based on actual response)
            message_id = (
                response_data.get('messageId') or 
                response_data.get('message_id') or 
                response_data.get('id') or
                response_data.get('data', {}).get('msgId') or  # WASender uses 'msgId'
                response_data.get('data', {}).get('messageId') or
                response_data.get('data', {}).get('message_id') or
                response_data.get('data', {}).get('id') or
                str(response_data.get('data', {}).get('msgId')) if response_data.get('data', {}).get('msgId') else None
            )
            
            # Convert numeric message IDs to string
            if message_id and isinstance(message_id, (int, float)):
                message_id = str(message_id)
            
            logger.debug(f"Extracted message ID: {message_id}")
        
        return True, message_id
        
    except requests.exceptions.RequestException as e:
        status_code = getattr(e.response, 'status_code', 'N/A') if e.response else 'N/A'
        response_text = getattr(e.response, 'text', 'N/A') if e.response else 'N/A'
        
        logger.error(f"Failed to send message to {recipient_number} (Status: {status_code}): {e}")
        logger.error(f"Response: {response_text}")
        
        if status_code == 422:
            logger.error("WaSenderAPI 422 Error: Check payload format and WaSenderAPI documentation")
        
        return False, None
        
    except Exception as e:
        logger.error(f"Unexpected error sending WhatsApp message: {e}")
        return False, None


def send_complete_message(recipient_number: str, full_message: str) -> tuple[bool, Optional[str]]:
    """
    Send a complete message as a single WhatsApp message.
    Includes retry logic for failed attempts.
    
    Args:
        recipient_number: WhatsApp number to send to
        full_message: Complete message to send as one message
        
    Returns:
        Tuple of (success: bool, message_id: Optional[str])
    """
    logger.info(f"Sending complete message to {recipient_number}")
    
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        # Send complete message
        success, message_id = send_whatsapp_message(recipient_number, full_message)
        if success:
            logger.info(f"Successfully sent complete message to {recipient_number} (ID: {message_id})")
            return True, message_id
        else:
            retry_count += 1
            if retry_count < max_retries:
                retry_delay = random.uniform(3.0, 6.0)  # Longer delay for retries
                logger.warning(f"Message failed, retrying in {retry_delay:.1f}s (attempt {retry_count}/{max_retries})")
                time.sleep(retry_delay)
            else:
                logger.error(f"Failed to send message after {max_retries} attempts")
                return False, None
    
    return False, None 