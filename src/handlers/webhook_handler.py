"""
WhatsApp AI Chatbot - Enhanced Webhook Handler
=============================================
Handles all WASender webhook events including message status updates,
delivery receipts, and message upserts with comprehensive logging.

Author: Rian Infotech
Version: 1.0 (Enhanced Webhook Processing)
"""

import logging
from typing import Dict, Tuple, Optional
from datetime import datetime, timezone

# Import core functionality
from src.core.supabase_client import get_supabase_manager
from src.handlers.message_processor import process_incoming_message

# Configure logging
logger = logging.getLogger(__name__)

# ============================================================================
# WEBHOOK EVENT PROCESSORS
# ============================================================================

def process_messages_upsert(webhook_data: Dict) -> Tuple[bool, str]:
    """
    Process messages.upsert event - handles incoming messages.
    
    Args:
        webhook_data: Full webhook payload
        
    Returns:
        Tuple of (success, status_message)
    """
    try:
        data = webhook_data.get('data', {})
        messages_list = data.get('messages')
        
        logger.info(f"📥 MESSAGES.UPSERT EVENT - Processing incoming message")
        
        if not messages_list:
            logger.warning("📥 MESSAGES.UPSERT - No message data in upsert event")
            return False, "No message data in upsert event"
        
        # Handle both list and single message formats
        if isinstance(messages_list, list):
            if not messages_list:
                logger.warning("📥 MESSAGES.UPSERT - Empty messages list in upsert event")
                return False, "Empty messages list in upsert event"
            # Process the first message in the list
            message_info = messages_list[0]
        else:
            # Single message object
            message_info = messages_list
        
        # Extract key info for debugging
        message_key = message_info.get('key', {})
        message_id = message_key.get('id', 'unknown')
        from_me = message_key.get('fromMe', False)
        remote_jid = message_key.get('remoteJid', 'unknown')
        
        logger.info(f"📥 MESSAGES.UPSERT - Message ID: {message_id}, FromMe: {from_me}, RemoteJid: {remote_jid}")
        
        # Log the event
        supabase = get_supabase_manager()
        if supabase.is_connected():
            supabase.log_webhook_event('messages.upsert', webhook_data, 'processing')
        
        # Process the incoming message
        success, status_message = process_incoming_message(message_info)
        
        # Log the result
        if supabase.is_connected():
            result_status = 'processed' if success else 'failed'
            supabase.log_webhook_event('messages.upsert', webhook_data, result_status)
        
        logger.info(f"📥 MESSAGES.UPSERT - Processing result: {success}, Message: {status_message}")
        
        return success, status_message
        
    except Exception as e:
        logger.error(f"Error processing messages.upsert: {e}", exc_info=True)
        return False, f"Failed to process message upsert: {str(e)}"

def process_message_sent(webhook_data: Dict) -> Tuple[bool, str]:
    """
    Process message.sent event - updates message status to 'sent'.
    This should ONLY update status, never trigger message processing.
    
    Args:
        webhook_data: Full webhook payload
        
    Returns:
        Tuple of (success, status_message)
    """
    try:
        data = webhook_data.get('data', {})
        
        # Extract message ID from various possible locations (WASender compatibility)
        message_id = (
            data.get('message_id') or 
            data.get('key', {}).get('id') or
            str(data.get('msgId')) if data.get('msgId') else None
        )
        
        # Extract phone numbers from various possible locations
        from_number = (
            data.get('from') or 
            data.get('key', {}).get('remoteJid') or
            data.get('jid', '')
        )
        to_number = data.get('to', '')
        
        logger.info(f"📤 MESSAGE.SENT EVENT - Processing status update for message {message_id}")
        
        if not message_id:
            logger.warning("📤 MESSAGE.SENT - No message ID found, skipping status update")
            return True, "Message sent event acknowledged (no message ID)"
        
        # Log the event
        supabase = get_supabase_manager()
        if supabase.is_connected():
            supabase.log_webhook_event('message.sent', webhook_data, 'processing')
        
        # Determine the phone number to update
        # For outgoing messages, use 'to' number, for incoming use 'from'
        phone_number = to_number if to_number else from_number
        
        # Ensure phone number has correct WhatsApp format
        if phone_number and not phone_number.endswith('@s.whatsapp.net'):
            phone_number = f"{phone_number}@s.whatsapp.net"
        
        if phone_number and supabase.is_connected():
            # Update message status to 'sent'
            success = supabase.update_message_status(phone_number, str(message_id), 'sent')
            
            if success:
                logger.info(f"📤 MESSAGE.SENT - Updated message {message_id} status to 'sent' for {phone_number}")
                supabase.log_webhook_event('message.sent', webhook_data, 'processed')
                return True, f"Message {message_id} marked as sent"
            else:
                logger.warning(f"📤 MESSAGE.SENT - Failed to update message {message_id} status for {phone_number}")
                supabase.log_webhook_event('message.sent', webhook_data, 'failed')
                return False, f"Failed to update message {message_id} status"
        else:
            logger.info(f"📤 MESSAGE.SENT - No phone number found, acknowledging event for message {message_id}")
            return True, "Message sent event acknowledged (no phone number to update)"
        
    except Exception as e:
        logger.error(f"Error processing message.sent: {e}", exc_info=True)
        return False, f"Failed to process message sent: {str(e)}"

def process_message_receipt_update(webhook_data: Dict) -> Tuple[bool, str]:
    """
    Process message-receipt.update event - updates message status to 'delivered' or 'read'.
    
    Args:
        webhook_data: Full webhook payload
        
    Returns:
        Tuple of (success, status_message)
    """
    try:
        data = webhook_data.get('data', {})
        
        # Extract message ID from various possible locations (WASender compatibility)
        message_id = (
            data.get('message_id') or 
            data.get('key', {}).get('id') or
            str(data.get('msgId')) if data.get('msgId') else None
        )
        
        # Extract receipt type from various possible locations
        receipt_type = (
            data.get('receipt', {}).get('type') or
            data.get('receiptType') or
            'delivered'  # default
        )
        
        # Extract phone number from various possible locations
        from_number = (
            data.get('from') or 
            data.get('key', {}).get('remoteJid') or
            data.get('jid', '')
        )
        
        if not message_id:
            return False, "No message ID in receipt update event"
        
        # Log the event
        supabase = get_supabase_manager()
        if supabase.is_connected():
            supabase.log_webhook_event('message-receipt.update', webhook_data, 'processing')
        
        # Map receipt type to status
        status_map = {
            'delivered': 'delivered',
            'read': 'read',
            'played': 'read'  # For voice messages
        }
        new_status = status_map.get(receipt_type, 'delivered')
        
        # Ensure phone number has correct WhatsApp format
        if from_number and not from_number.endswith('@s.whatsapp.net'):
            from_number = f"{from_number}@s.whatsapp.net"
        
        if from_number and supabase.is_connected():
            # Update message status
            success = supabase.update_message_status(from_number, str(message_id), new_status)
            
            if success:
                logger.info(f"Updated message {message_id} status to '{new_status}' for {from_number}")
                supabase.log_webhook_event('message-receipt.update', webhook_data, 'processed')
                return True, f"Message {message_id} marked as {new_status}"
            else:
                logger.warning(f"Failed to update message {message_id} receipt status for {from_number}")
                supabase.log_webhook_event('message-receipt.update', webhook_data, 'failed')
                return False, f"Failed to update message {message_id} receipt status"
        else:
            logger.warning(f"No phone number found in receipt update event for message {message_id}")
            return True, "Receipt update event acknowledged (no phone number to update)"
        
    except Exception as e:
        logger.error(f"Error processing message-receipt.update: {e}", exc_info=True)
        return False, f"Failed to process receipt update: {str(e)}"

def process_messages_update(webhook_data: Dict) -> Tuple[bool, str]:
    """
    Process messages.update event - handles message edits or updates.
    
    Args:
        webhook_data: Full webhook payload
        
    Returns:
        Tuple of (success, status_message)
    """
    try:
        data = webhook_data.get('data', {})
        message_id = data.get('message_id') or data.get('key', {}).get('id')
        from_number = data.get('from') or data.get('key', {}).get('remoteJid', '')
        
        # Log the event
        supabase = get_supabase_manager()
        if supabase.is_connected():
            supabase.log_webhook_event('messages.update', webhook_data, 'processing')
        
        # For now, just log the update event
        # In the future, we could implement message editing functionality
        logger.info(f"Received message update for {message_id} from {from_number}")
        
        if supabase.is_connected():
            supabase.log_webhook_event('messages.update', webhook_data, 'processed')
        
        return True, f"Message update event processed for {message_id}"
        
    except Exception as e:
        logger.error(f"Error processing messages.update: {e}", exc_info=True)
        return False, f"Failed to process message update: {str(e)}"

# ============================================================================
# MAIN WEBHOOK PROCESSOR
# ============================================================================

def process_webhook_event(webhook_data: Dict) -> Tuple[bool, str]:
    """
    Main webhook event processor that routes to specific handlers.
    
    Args:
        webhook_data: Full webhook payload from WASender
        
    Returns:
        Tuple of (success, status_message)
    """
    try:
        event_type = webhook_data.get('event', 'unknown')
        
        logger.info(f"Processing webhook event: {event_type}")
        
        # Route to appropriate handler based on event type
        if event_type == 'messages.upsert':
            return process_messages_upsert(webhook_data)
        
        elif event_type == 'message.sent':
            return process_message_sent(webhook_data)
        
        elif event_type == 'message-receipt.update':
            return process_message_receipt_update(webhook_data)
        
        elif event_type == 'messages.update':
            return process_messages_update(webhook_data)
        
        else:
            # Handle unknown event types
            logger.info(f"Received unknown webhook event type: {event_type}")
            
            # Still log the event for debugging
            supabase = get_supabase_manager()
            if supabase.is_connected():
                supabase.log_webhook_event(event_type, webhook_data, 'unknown')
            
            return True, f"Unknown event type '{event_type}' acknowledged"
    
    except Exception as e:
        logger.error(f"Error processing webhook event: {e}", exc_info=True)
        return False, f"Webhook processing failed: {str(e)}"

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def extract_phone_number_from_webhook(webhook_data: Dict) -> Optional[str]:
    """
    Extract phone number from webhook data.
    
    Args:
        webhook_data: Webhook payload
        
    Returns:
        Phone number string or None
    """
    try:
        data = webhook_data.get('data', {})
        
        # Try different possible locations for phone number
        phone_number = (
            data.get('from') or 
            data.get('to') or 
            data.get('key', {}).get('remoteJid') or
            data.get('key', {}).get('participant')
        )
        
        return phone_number
        
    except Exception as e:
        logger.error(f"Error extracting phone number from webhook: {e}")
        return None

def extract_message_id_from_webhook(webhook_data: Dict) -> Optional[str]:
    """
    Extract message ID from webhook data.
    
    Args:
        webhook_data: Webhook payload
        
    Returns:
        Message ID string or None
    """
    try:
        data = webhook_data.get('data', {})
        
        # Try different possible locations for message ID
        message_id = (
            data.get('message_id') or 
            data.get('key', {}).get('id') or
            data.get('id')
        )
        
        return message_id
        
    except Exception as e:
        logger.error(f"Error extracting message ID from webhook: {e}")
        return None 