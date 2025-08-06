"""
WhatsApp AI Chatbot - Main Application
=====================================
Refactored modular Flask application for WhatsApp AI chatbot.
This is the main entry point that imports and uses all modular components.

Author: Rian Infotech
Version: 2.1 (Refactored & Structured)
"""

import logging
import os
from flask import Flask, request, jsonify
from flask_cors import CORS

# Import configuration and setup
from src.config.config import *
from src.config.persona_manager import load_bot_persona

# Import core functionality
from src.core.conversation_manager import load_conversation_history, save_conversation_history, sanitize_user_id
from src.core.supabase_client import get_supabase_manager

# Import handlers
from src.handlers.ai_handler import generate_ai_response
from src.handlers.whatsapp_handler import send_complete_message
from src.handlers.message_processor import process_incoming_message

# Import API routes
from src.api.api_routes import api_bp
from src.api.bot_control_routes import bot_control_bp
from src.api.lead_routes import lead_bp
from src.api.bulk_messaging_routes import bulk_messaging_bp
from src.api.whatsapp_status_routes import whatsapp_status_bp
from src.api.analytics_routes import analytics_bp

# Import utilities
from src.utils.bulk_messaging import send_bulk_message_individual, parse_contacts_from_text, format_bulk_job_summary

# ============================================================================
# APPLICATION SETUP
# ============================================================================

# Initialize Flask app (API only - no static files)
app = Flask(__name__)

# Configure CORS for Next.js frontend
# Allow requests from localhost:3000 (Next.js dev) and production domains
allowed_origins = [
    "http://localhost:3000",  # Next.js development (default)
    "http://localhost:3001",  # Next.js development (custom port)
    "http://127.0.0.1:3000",  # Alternative localhost
    "http://127.0.0.1:3001",  # Alternative localhost (custom port)
    "https://localhost:3000", # HTTPS dev (if using)
    "https://localhost:3001", # HTTPS dev (custom port)
    "https://whatsapp-cr-mfrontend.vercel.app",  # Production frontend
]

# Add production domain from environment variable if available
production_domain = os.environ.get('FRONTEND_URL')
if production_domain:
    allowed_origins.append(production_domain)

CORS(app, 
     origins=allowed_origins,
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     allow_headers=['Content-Type', 'Authorization'],
     supports_credentials=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load bot persona
PERSONA_NAME, PERSONA_DESCRIPTION = load_bot_persona()

# Register API Blueprints
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(bot_control_bp, url_prefix='/api')
app.register_blueprint(lead_bp, url_prefix='/api')
app.register_blueprint(bulk_messaging_bp, url_prefix='/api')
app.register_blueprint(whatsapp_status_bp)

# Register SaaS Authentication Blueprint
from src.api.auth_routes import auth_bp
app.register_blueprint(auth_bp, url_prefix='/api/auth')

# Register API Key Management Blueprint
from src.api.api_key_routes import api_key_bp
app.register_blueprint(api_key_bp)

# Register RAG Knowledge Management Blueprint
try:
    from src.api.knowledge_routes import knowledge_bp
    app.register_blueprint(knowledge_bp)
    logger.info("RAG Knowledge Management routes registered successfully")
except ImportError as e:
    logger.warning(f"RAG Knowledge Management routes not available: {e}")

# Register Analytics Dashboard Blueprint
try:
    app.register_blueprint(analytics_bp)
    logger.info("Analytics Dashboard routes registered successfully")
except ImportError as e:
    logger.warning(f"Analytics Dashboard routes not available: {e}")

# Initialize Group Messaging Module
try:
    from src.modules.group_messaging.integration import integrate_group_messaging
    supabase_manager = get_supabase_manager()
    
    if integrate_group_messaging(app, supabase_manager.client):
        logger.info("✅ Group messaging module loaded successfully")
    else:
        logger.warning("⚠️ Group messaging module failed to load")
except Exception as e:
    logger.error(f"❌ Failed to load group messaging module: {e}")
    logger.error("Make sure WASENDER_API_TOKEN is set in environment variables")

# ============================================================================
# CORE ROUTES
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
    Enhanced webhook handler for all WASender events.
    
    This endpoint receives webhook events from WaSenderAPI including:
    - messages.upsert: Incoming messages
    - message.sent: Message delivery confirmations
    - message-receipt.update: Read/delivery receipts
    - messages.update: Message updates/edits
    """
    try:
        # Get webhook data with better error handling
        try:
            webhook_data = request.get_json(force=True)
        except Exception as json_error:
            logger.warning(f"Invalid JSON in webhook request: {json_error}")
            return jsonify({'status': 'error', 'message': 'Invalid JSON data'}), 400
        
        if not webhook_data:
            logger.warning("Received webhook with no JSON data")
            return jsonify({'status': 'error', 'message': 'No data received'}), 400
        
        event_type = webhook_data.get('event', 'unknown')
        logger.info(f"Received webhook event: {event_type}")
        
        # Use enhanced webhook processor
        from src.handlers.webhook_handler import process_webhook_event
        success, status_message = process_webhook_event(webhook_data)
        
        return jsonify({
            'status': 'success' if success else 'error',
            'message': status_message,
            'event_type': event_type
        }), 200
            
    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        return jsonify({
            'status': 'error', 
            'message': 'Webhook processing failed',
            'error': str(e)
        }), 500


@app.route('/', methods=['GET'])
def api_info():
    """API information endpoint for Next.js frontend."""
    return jsonify({
        'message': 'WhatsApp AI Chatbot API',
        'version': '2.1',
        'status': 'active',
        'endpoints': {
            'health': '/health',
            'webhook': '/webhook',
            'send_message': '/send-message',
            'start_conversation': '/start-conversation',
            'bulk_message': '/send-bulk-message',
            'api_routes': '/api/*'
        },
        'documentation': 'See API_DOCUMENTATION.md for complete API docs'
    }), 200


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint to verify bot status."""
    from src.handlers.ai_handler import is_openai_configured
    from src.handlers.whatsapp_handler import is_wasender_configured
    
    supabase = get_supabase_manager()
    return jsonify({
        'status': 'healthy',
        'bot_name': PERSONA_NAME,
        'openai_configured': is_openai_configured(),
        'wasender_configured': is_wasender_configured(),
        'supabase_connected': supabase.is_connected()
    }), 200


@app.route('/healthz', methods=['GET'])
def health_check_alt():
    """Alternative health check endpoint for Railway."""
    return jsonify({'status': 'ok'}), 200


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
        send_success, message_id = send_complete_message(recipient_id, message)
        if send_success:
            # Track this message ID as bot-sent to prevent future loop processing
            supabase = get_supabase_manager()
            if message_id and supabase.is_connected():
                supabase.track_bot_sent_message(message_id, recipient_id)
            
            # Save to conversation history as an assistant message with message ID
            if supabase.is_connected():
                supabase.save_message_with_status(
                    phone_number=recipient_id,
                    message_content=message,
                    role='assistant',
                    message_id=message_id,
                    status='sent'
                )
            else:
                # Fallback to old method
                safe_user_id = sanitize_user_id(recipient_id)
                conversation_history = load_conversation_history(safe_user_id)
                conversation_history.append({
                    'role': 'assistant', 
                    'content': message,
                    'message_id': message_id,
                    'status': 'sent'
                })
                save_conversation_history(safe_user_id, conversation_history)
            
            return jsonify({
                'status': 'success',
                'message': f'Message sent successfully to {clean_number}',
                'recipient': clean_number,
                'message_id': message_id
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
        send_success, message_id = send_complete_message(recipient_id, intro_message)
        if send_success:
            # Save to conversation history with message ID
            supabase = get_supabase_manager()
            if supabase.is_connected():
                supabase.save_message_with_status(
                    phone_number=recipient_id,
                    message_content=intro_message,
                    role='assistant',
                    message_id=message_id,
                    status='sent'
                )
            else:
                # Fallback to old method
                safe_user_id = sanitize_user_id(recipient_id)
                conversation_history = load_conversation_history(safe_user_id)
                conversation_history.append({
                    'role': 'assistant', 
                    'content': intro_message,
                    'message_id': message_id,
                    'status': 'sent'
                })
                save_conversation_history(safe_user_id, conversation_history)
            
            return jsonify({
                'status': 'success',
                'message': f'AI conversation started with {clean_number}',
                'recipient': clean_number,
                'intro_message': intro_message,
                'message_id': message_id
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
        from datetime import datetime
        
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


@app.route('/test-handover', methods=['POST'])
def test_handover():
    """
    Test endpoint to debug handover detection.
    
    Expected JSON payload:
    {
        "phone_number": "7033009600",
        "message": "I want to talk to a human"
    }
    """
    try:
        data = request.json
        if not data:
            return jsonify({'status': 'error', 'message': 'No JSON data provided'}), 400
        
        phone_number = data.get('phone_number')
        message = data.get('message')
        
        if not phone_number or not message:
            return jsonify({'status': 'error', 'message': 'phone_number and message are required'}), 400
        
        # Import handover functions
        from src.handlers.message_processor import detect_user_handover_request, handle_user_handover_request
        
        # Test detection (no customer context available for test endpoint)
        detection_result = detect_user_handover_request(message, None)
        
        logger.info(f"🧪 HANDOVER TEST - Phone: {phone_number}, Message: '{message}', Detection: {detection_result}")
        
        if detection_result:
            # Format phone number for processing
            phone_format = f"{phone_number.replace('+', '').replace('-', '').replace(' ', '')}_s_whatsapp_net"
            success, status = handle_user_handover_request(phone_format, message)
            
            return jsonify({
                'status': 'success',
                'detection_result': True,
                'handover_success': success,
                'handover_status': status,
                'phone_format_used': phone_format
            })
        else:
            return jsonify({
                'status': 'success',
                'detection_result': False,
                'message': 'No handover trigger detected'
            })
            
    except Exception as e:
        logger.error(f"Test handover error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ============================================================================
# ERROR HANDLERS
# ============================================================================

# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    from src.handlers.ai_handler import is_openai_configured
    from src.handlers.whatsapp_handler import is_wasender_configured
    
    logger.info(f"Starting {PERSONA_NAME} WhatsApp Bot...")
    logger.info(f"OpenAI configured: {is_openai_configured()}")
    logger.info(f"WaSender configured: {is_wasender_configured()}")
    
    # Get port from environment variable (Railway sets this)
    port = int(os.environ.get('PORT', 5001))
    
    # Run Flask app
    # In production, gunicorn will handle this
    # In development, use Flask's built-in server
    app.run(debug=False, port=port, host='0.0.0.0') 