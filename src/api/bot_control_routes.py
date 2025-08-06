"""
WhatsApp AI Chatbot - Bot Control API Routes
===========================================
API endpoints for controlling bot behavior per conversation.
Allows humans to take over conversations by disabling bot responses.

Author: Rian Infotech
Version: 1.0
"""

import logging
from flask import Blueprint, request, jsonify
from datetime import datetime, timezone

# Import core functionality
from src.core.supabase_client import get_supabase_manager

# Configure logging
logger = logging.getLogger(__name__)

# Create Blueprint for bot control routes
bot_control_bp = Blueprint('bot_control', __name__)

# ============================================================================
# BOT CONTROL API ENDPOINTS
# ============================================================================

@bot_control_bp.route('/bot/status/<conversation_id>', methods=['GET'])
def get_bot_status(conversation_id):
    """
    Get the current bot status for a conversation.
    
    Returns whether the bot is enabled or disabled for this conversation.
    """
    try:
        supabase = get_supabase_manager()
        
        if not supabase.is_connected():
            return jsonify({
                'status': 'error',
                'message': 'Database not connected'
            }), 503
        
        # Get conversation with bot status
        result = supabase.client.table('conversations')\
            .select('id, bot_enabled, contacts!inner(phone_number, name)')\
            .eq('id', conversation_id)\
            .execute()
        
        if not result.data:
            return jsonify({
                'status': 'error',
                'message': 'Conversation not found'
            }), 404
        
        conversation = result.data[0]
        
        return jsonify({
            'status': 'success',
            'data': {
                'conversation_id': conversation['id'],
                'bot_enabled': conversation.get('bot_enabled', True),
                'contact': {
                    'phone_number': conversation['contacts']['phone_number'],
                    'name': conversation['contacts']['name'] or 'Unknown'
                },
                'status_text': 'Bot is responding automatically' if conversation.get('bot_enabled', True) else 'Bot is paused - Human is handling'
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting bot status: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Failed to get bot status'
        }), 500


@bot_control_bp.route('/bot/toggle/<conversation_id>', methods=['POST'])
def toggle_bot_status(conversation_id):
    """
    Toggle bot status for a specific conversation.
    
    Request body can include:
    - enabled: boolean (optional) - force specific state
    - reason: string (optional) - reason for toggle
    """
    try:
        supabase = get_supabase_manager()
        
        if not supabase.is_connected():
            return jsonify({
                'status': 'error',
                'message': 'Database not connected'
            }), 503
        
        # Get request data
        data = request.json or {}
        forced_state = data.get('enabled')  # None, True, or False
        reason = data.get('reason', 'Manual toggle')
        
        # Get current conversation status
        current_result = supabase.client.table('conversations')\
            .select('id, bot_enabled, contacts!inner(phone_number, name)')\
            .eq('id', conversation_id)\
            .execute()
        
        if not current_result.data:
            return jsonify({
                'status': 'error',
                'message': 'Conversation not found'
            }), 404
        
        current_conversation = current_result.data[0]
        current_status = current_conversation.get('bot_enabled', True)
        
        # Determine new status
        if forced_state is not None:
            new_status = forced_state
        else:
            new_status = not current_status  # Toggle
        
        # Update conversation
        update_result = supabase.client.table('conversations')\
            .update({
                'bot_enabled': new_status,
                'updated_at': datetime.now(timezone.utc).isoformat()
            })\
            .eq('id', conversation_id)\
            .execute()
        
        if not update_result.data:
            return jsonify({
                'status': 'error',
                'message': 'Failed to update conversation'
            }), 500
        
        # Log the toggle action
        log_bot_toggle(
            conversation_id=conversation_id,
            previous_status=current_status,
            new_status=new_status,
            reason=reason
        )
        
        # Prepare response
        action = 'enabled' if new_status else 'disabled'
        contact_name = current_conversation['contacts']['name'] or current_conversation['contacts']['phone_number']
        
        return jsonify({
            'status': 'success',
            'message': f'Bot {action} for conversation with {contact_name}',
            'data': {
                'conversation_id': conversation_id,
                'previous_status': current_status,
                'new_status': new_status,
                'action': action,
                'contact': {
                    'phone_number': current_conversation['contacts']['phone_number'],
                    'name': current_conversation['contacts']['name']
                },
                'reason': reason,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error toggling bot status: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Failed to toggle bot status'
        }), 500


@bot_control_bp.route('/bot/toggle-by-phone', methods=['POST'])
def toggle_bot_by_phone():
    """
    Toggle bot status by phone number (easier for frontend).
    
    Request body:
    - phone_number: string (required)
    - enabled: boolean (optional) - force specific state
    - reason: string (optional) - reason for toggle
    """
    try:
        supabase = get_supabase_manager()
        
        if not supabase.is_connected():
            return jsonify({
                'status': 'error',
                'message': 'Database not connected'
            }), 503
        
        data = request.json
        if not data or not data.get('phone_number'):
            return jsonify({
                'status': 'error',
                'message': 'phone_number is required'
            }), 400
        
        phone_number = data['phone_number']
        forced_state = data.get('enabled')
        reason = data.get('reason', 'Manual toggle by phone')
        
        # Clean phone number format
        if '@s.whatsapp.net' not in phone_number:
            phone_number = f"{phone_number.replace('+', '').replace('-', '').replace(' ', '')}_s_whatsapp_net"
        
        # Find conversation by phone number
        conversation_result = supabase.client.table('conversations')\
            .select('id, bot_enabled, contacts!inner(phone_number, name)')\
            .eq('contacts.phone_number', phone_number)\
            .execute()
        
        if not conversation_result.data:
            return jsonify({
                'status': 'error',
                'message': 'No conversation found for this phone number'
            }), 404
        
        conversation = conversation_result.data[0]
        conversation_id = conversation['id']
        current_status = conversation.get('bot_enabled', True)
        
        # Determine new status
        if forced_state is not None:
            new_status = forced_state
        else:
            new_status = not current_status
        
        # Update conversation
        update_result = supabase.client.table('conversations')\
            .update({
                'bot_enabled': new_status,
                'updated_at': datetime.now(timezone.utc).isoformat()
            })\
            .eq('id', conversation_id)\
            .execute()
        
        if not update_result.data:
            return jsonify({
                'status': 'error',
                'message': 'Failed to update conversation'
            }), 500
        
        # Log the toggle action
        log_bot_toggle(
            conversation_id=conversation_id,
            previous_status=current_status,
            new_status=new_status,
            reason=reason
        )
        
        action = 'enabled' if new_status else 'disabled'
        contact_name = conversation['contacts']['name'] or conversation['contacts']['phone_number']
        
        return jsonify({
            'status': 'success',
            'message': f'Bot {action} for {contact_name}',
            'data': {
                'conversation_id': conversation_id,
                'previous_status': current_status,
                'new_status': new_status,
                'action': action,
                'contact': {
                    'phone_number': conversation['contacts']['phone_number'],
                    'name': conversation['contacts']['name']
                },
                'reason': reason,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error toggling bot by phone: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Failed to toggle bot status'
        }), 500


@bot_control_bp.route('/bot/bulk-toggle', methods=['POST'])
def bulk_toggle_bot():
    """
    Toggle bot status for multiple conversations at once.
    
    Request body:
    - conversation_ids: array of conversation IDs
    - enabled: boolean (required) - new state for all
    - reason: string (optional) - reason for bulk toggle
    """
    try:
        supabase = get_supabase_manager()
        
        if not supabase.is_connected():
            return jsonify({
                'status': 'error',
                'message': 'Database not connected'
            }), 503
        
        data = request.json
        if not data or not data.get('conversation_ids') or data.get('enabled') is None:
            return jsonify({
                'status': 'error',
                'message': 'conversation_ids and enabled are required'
            }), 400
        
        conversation_ids = data['conversation_ids']
        new_status = data['enabled']
        reason = data.get('reason', 'Bulk toggle operation')
        
        if not isinstance(conversation_ids, list) or len(conversation_ids) == 0:
            return jsonify({
                'status': 'error',
                'message': 'conversation_ids must be a non-empty array'
            }), 400
        
        # Update all conversations
        update_result = supabase.client.table('conversations')\
            .update({
                'bot_enabled': new_status,
                'updated_at': datetime.now(timezone.utc).isoformat()
            })\
            .in_('id', conversation_ids)\
            .execute()
        
        updated_count = len(update_result.data) if update_result.data else 0
        
        # Log bulk toggle
        for conv_id in conversation_ids:
            log_bot_toggle(
                conversation_id=conv_id,
                previous_status=not new_status,  # Assume opposite for logging
                new_status=new_status,
                reason=f"Bulk: {reason}"
            )
        
        action = 'enabled' if new_status else 'disabled'
        
        return jsonify({
            'status': 'success',
            'message': f'Bot {action} for {updated_count} conversations',
            'data': {
                'conversation_ids': conversation_ids,
                'new_status': new_status,
                'action': action,
                'updated_count': updated_count,
                'reason': reason,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error in bulk toggle: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Failed to perform bulk toggle'
        }), 500


@bot_control_bp.route('/bot/status-summary', methods=['GET'])
def get_bot_status_summary():
    """
    Get summary of bot status across all conversations with CRM enrichment.
    
    Returns counts of enabled/disabled conversations.
    """
    try:
        supabase = get_supabase_manager()
        
        if not supabase.is_connected():
            return jsonify({
                'status': 'error',
                'message': 'Database not connected'
            }), 503
        
        # Get all conversations with bot status
        result = supabase.client.table('conversations')\
            .select('id, bot_enabled, contacts!inner(phone_number, name, created_at)')\
            .execute()
        
        conversations = result.data or []
        
        # Calculate summary
        total_conversations = len(conversations)
        bot_enabled_count = sum(1 for conv in conversations if conv.get('bot_enabled', True))
        bot_disabled_count = total_conversations - bot_enabled_count
        
        # Get disabled conversations details with CRM enrichment
        disabled_conversations = []
        for conv in conversations:
            if not conv.get('bot_enabled', True):
                # Get phone number and try to enrich with CRM data
                phone_number = conv['contacts']['phone_number']
                base_phone = phone_number.replace('_s_whatsapp_net', '') if phone_number else ''
                
                # Try to get CRM customer context
                crm_context = None
                try:
                    crm_context = supabase.get_customer_context_by_phone(base_phone)
                except Exception as e:
                    logger.debug(f"Could not get CRM context for {base_phone}: {e}")
                
                # Use CRM name if available, otherwise fallback to conversation contact name
                contact_name = conv['contacts']['name'] or 'Unknown'
                contact_info = {
                    'phone_number': phone_number,
                    'name': contact_name
                }
                
                # Add CRM enrichment if available
                if crm_context and not crm_context.get('is_new_customer', True):
                    # CRM context found - use the data directly
                    if crm_context.get('name'):
                        contact_info['name'] = crm_context['name']
                    if crm_context.get('company'):
                        contact_info['company'] = crm_context['company']
                    if crm_context.get('lead_status'):
                        contact_info['lead_status'] = crm_context['lead_status']
                    if crm_context.get('lead_score') is not None:
                        contact_info['lead_score'] = crm_context['lead_score']
                
                disabled_conversations.append({
                    'conversation_id': conv['id'],
                    'contact': contact_info
                })
        
        summary = {
            'status': 'success',
            'data': {
                'summary': {
                    'total_conversations': total_conversations,
                    'bot_enabled': bot_enabled_count,
                    'bot_disabled': bot_disabled_count,
                    'enabled_percentage': round((bot_enabled_count / total_conversations * 100) if total_conversations > 0 else 0, 1)
                },
                'disabled_conversations': disabled_conversations,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        }
        return jsonify(summary)
        
    except Exception as e:
        logger.error(f"Error getting bot status summary: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to get status summary: {str(e)}'
        }), 500


@bot_control_bp.route('/bot/return-to-bot/<conversation_id>', methods=['POST'])
def return_conversation_to_bot(conversation_id):
    """
    Return a conversation from human back to bot mode.
    Sends a confirmation message to the user and re-enables bot responses.
    
    Request body (optional):
    - reason: string - reason for returning to bot
    - send_notification: boolean - whether to send confirmation message to user (default: true)
    """
    try:
        supabase = get_supabase_manager()
        
        if not supabase.is_connected():
            return jsonify({
                'status': 'error',
                'message': 'Database not connected'
            }), 503
        
        # Get request data
        data = request.json or {}
        reason = data.get('reason', 'Conversation returned to bot after human assistance')
        send_notification = data.get('send_notification', True)
        
        # Get current conversation details
        current_result = supabase.client.table('conversations')\
            .select('id, bot_enabled, contacts!inner(phone_number, name)')\
            .eq('id', conversation_id)\
            .execute()
        
        if not current_result.data:
            return jsonify({
                'status': 'error',
                'message': 'Conversation not found'
            }), 404
        
        current_conversation = current_result.data[0]
        current_status = current_conversation.get('bot_enabled', True)
        contact = current_conversation['contacts']
        phone_number = contact['phone_number']
        
        # Update conversation to enable bot
        update_result = supabase.client.table('conversations')\
            .update({
                'bot_enabled': True,
                'updated_at': datetime.now(timezone.utc).isoformat()
            })\
            .eq('id', conversation_id)\
            .execute()
        
        if not update_result.data:
            return jsonify({
                'status': 'error',
                'message': 'Failed to update conversation'
            }), 500
        
        # Log the toggle action
        log_bot_toggle(conversation_id, current_status, True, reason)
        
        # Send confirmation message to user if requested
        notification_sent = False
        if send_notification:
            try:
                from src.handlers.whatsapp_handler import send_complete_message
                
                # Convert phone format for WhatsApp API
                whatsapp_phone = phone_number.replace('_s_whatsapp_net', '@s.whatsapp.net')
                
                confirmation_message = """🤖 Thank you for your patience!

Our team has addressed your request, and I'm back to assist you with any other questions you might have.

✅ Bot mode: ON
📝 Feel free to continue our conversation!

Is there anything else I can help you with? 😊"""
                
                send_success, sent_message_id = send_complete_message(whatsapp_phone, confirmation_message)
                
                if send_success:
                    # Save the confirmation message to conversation history
                    supabase.save_message_with_status(
                        phone_number=phone_number,
                        message_content=confirmation_message,
                        role='assistant',
                        message_id=sent_message_id,
                        status='sent'
                    )
                    notification_sent = True
                    logger.info(f"Return-to-bot confirmation sent to {phone_number}")
                else:
                    logger.warning(f"Failed to send return-to-bot confirmation to {phone_number}")
                    
            except Exception as msg_error:
                logger.error(f"Error sending return-to-bot confirmation: {msg_error}")
        
        # Return success response
        response_data = {
            'conversation_id': conversation_id,
            'bot_enabled': True,
            'contact': {
                'phone_number': phone_number,
                'name': contact.get('name', 'Unknown')
            },
            'status_text': 'Bot responses re-enabled',
            'previous_status': current_status,
            'reason': reason,
            'notification_sent': notification_sent,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"Conversation {conversation_id} returned to bot mode. Notification sent: {notification_sent}")
        
        return jsonify({
            'status': 'success',
            'message': 'Conversation returned to bot successfully',
            'data': response_data
        })
        
    except Exception as e:
        logger.error(f"Error returning conversation to bot: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to return conversation to bot: {str(e)}'
        }), 500

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def log_bot_toggle(conversation_id: str, previous_status: bool, new_status: bool, reason: str = ''):
    """Log bot toggle action for audit trail."""
    try:
        supabase = get_supabase_manager()
        
        if supabase.is_connected():
            # Save to bot_toggle_logs table
            log_data = {
                'conversation_id': conversation_id,
                'previous_status': previous_status,
                'new_status': new_status,
                'reason': reason,
                'toggled_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Insert into audit table
            result = supabase.client.table('bot_toggle_logs').insert(log_data).execute()
            
            if result.data:
                logger.info(f"Bot toggle logged: Conversation {conversation_id} - {previous_status} → {new_status} - Reason: {reason}")
            else:
                logger.warning(f"Failed to log bot toggle to database")
            
    except Exception as e:
        logger.error(f"Error logging bot toggle: {e}")
        
    # Always log to application logs as backup
    logger.info(f"Bot toggle: Conversation {conversation_id} - {previous_status} → {new_status} - Reason: {reason}")


def is_bot_enabled_for_conversation(conversation_id: str) -> bool:
    """
    Check if bot is enabled for a specific conversation.
    Used by webhook to determine if bot should respond.
    """
    try:
        supabase = get_supabase_manager()
        
        if not supabase.is_connected():
            return True  # Default to enabled if DB unavailable
        
        result = supabase.client.table('conversations')\
            .select('bot_enabled')\
            .eq('id', conversation_id)\
            .execute()
        
        if result.data:
            return result.data[0].get('bot_enabled', True)
        
        return True  # Default to enabled for new conversations
        
    except Exception as e:
        logger.error(f"Error checking bot status: {e}")
        return True  # Default to enabled on error