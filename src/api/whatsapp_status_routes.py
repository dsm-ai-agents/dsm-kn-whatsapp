"""
WhatsApp Status Monitoring Routes
================================
API endpoints to monitor WhatsApp Web connection and message delivery status.
"""

from flask import Blueprint, jsonify, request
import requests
import os
import logging
from datetime import datetime
from src.config.config import WASENDER_API_TOKEN
from src.utils.auth import require_auth

logger = logging.getLogger(__name__)

whatsapp_status_bp = Blueprint('whatsapp_status', __name__)

@whatsapp_status_bp.route('/api/whatsapp/status', methods=['GET'])
@require_auth
def check_whatsapp_status():
    """
    Check WhatsApp Web connection status
    """
    try:
        if not WASENDER_API_TOKEN:
            return jsonify({
                'status': 'error',
                'message': 'WaSender API token not configured'
            }), 500
        
        headers = {
            'Authorization': f'Bearer {WASENDER_API_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        # Check WaSender API status
        response = requests.get('https://wasenderapi.com/api/status', headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            whatsapp_status = data.get('status', 'unknown')
            
            return jsonify({
                'status': 'success',
                'data': {
                    'whatsapp_connected': whatsapp_status == 'connected',
                    'whatsapp_status': whatsapp_status,
                    'api_status': 'active',
                    'last_checked': datetime.now().isoformat(),
                    'message': f'WhatsApp Web is {whatsapp_status}'
                }
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'API request failed: {response.status_code}',
                'data': {
                    'whatsapp_connected': False,
                    'api_status': 'error',
                    'last_checked': datetime.now().isoformat()
                }
            }), 500
            
    except Exception as e:
        logger.error(f"Error checking WhatsApp status: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to check WhatsApp status: {str(e)}',
            'data': {
                'whatsapp_connected': False,
                'api_status': 'error',
                'last_checked': datetime.now().isoformat()
            }
        }), 500

@whatsapp_status_bp.route('/api/whatsapp/test-message', methods=['POST'])
@require_auth
def send_test_message():
    """
    Send a test message to verify WhatsApp delivery
    """
    try:
        data = request.get_json()
        phone_number = data.get('phone_number', '917033009600')  # Default to your number
        
        if not WASENDER_API_TOKEN:
            return jsonify({
                'status': 'error',
                'message': 'WaSender API token not configured'
            }), 500
        
        headers = {
            'Authorization': f'Bearer {WASENDER_API_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        # Format phone number properly
        clean_number = phone_number.replace('+', '').replace('-', '').replace(' ', '')
        if clean_number.startswith('91') and len(clean_number) == 12:
            formatted_number = clean_number
        elif len(clean_number) == 10 and clean_number.startswith(('6', '7', '8', '9')):
            formatted_number = f"91{clean_number}"
        else:
            formatted_number = clean_number
        
        # Send test message
        payload = {
            'to': formatted_number,
            'text': f'🔧 WhatsApp Connection Test - {datetime.now().strftime("%H:%M:%S")}\n\nThis is a test message to verify WhatsApp delivery is working.'
        }
        
        response = requests.post(
            'https://wasenderapi.com/api/send-message',
            headers=headers,
            json=payload,
            timeout=20
        )
        
        if response.status_code == 200:
            response_data = response.json()
            
            if response_data.get('success'):
                message_data = response_data.get('data', {})
                
                return jsonify({
                    'status': 'success',
                    'message': 'Test message sent successfully',
                    'data': {
                        'message_id': message_data.get('msgId'),
                        'recipient': formatted_number,
                        'delivery_status': message_data.get('status', 'unknown'),
                        'sent_at': datetime.now().isoformat(),
                        'instructions': 'Check your WhatsApp to verify message delivery'
                    }
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to send test message',
                    'data': response_data
                }), 500
        else:
            return jsonify({
                'status': 'error',
                'message': f'API request failed: {response.status_code}',
                'data': response.text
            }), 500
            
    except Exception as e:
        logger.error(f"Error sending test message: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to send test message: {str(e)}'
        }), 500

@whatsapp_status_bp.route('/api/whatsapp/diagnostics', methods=['GET'])
@require_auth
def run_diagnostics():
    """
    Run comprehensive WhatsApp connection diagnostics
    """
    try:
        diagnostics = {
            'timestamp': datetime.now().isoformat(),
            'api_token_configured': bool(WASENDER_API_TOKEN),
            'api_token_length': len(WASENDER_API_TOKEN) if WASENDER_API_TOKEN else 0,
            'tests': {}
        }
        
        if not WASENDER_API_TOKEN:
            diagnostics['overall_status'] = 'error'
            diagnostics['message'] = 'WaSender API token not configured'
            return jsonify({
                'status': 'error',
                'data': diagnostics
            }), 500
        
        headers = {
            'Authorization': f'Bearer {WASENDER_API_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        # Test 1: API Connection
        try:
            response = requests.get('https://wasenderapi.com/api/status', headers=headers, timeout=10)
            diagnostics['tests']['api_connection'] = {
                'status': 'success' if response.status_code == 200 else 'error',
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds() if hasattr(response, 'elapsed') else None
            }
            
            if response.status_code == 200:
                data = response.json()
                diagnostics['tests']['whatsapp_status'] = {
                    'status': 'success' if data.get('status') == 'connected' else 'warning',
                    'whatsapp_status': data.get('status', 'unknown'),
                    'connected': data.get('status') == 'connected'
                }
            else:
                diagnostics['tests']['whatsapp_status'] = {
                    'status': 'error',
                    'message': 'Could not retrieve WhatsApp status'
                }
                
        except Exception as e:
            diagnostics['tests']['api_connection'] = {
                'status': 'error',
                'error': str(e)
            }
            diagnostics['tests']['whatsapp_status'] = {
                'status': 'error',
                'error': 'API connection failed'
            }
        
        # Test 2: Rate Limit Check
        try:
            response = requests.get('https://wasenderapi.com/api/status', headers=headers, timeout=5)
            rate_limit_remaining = response.headers.get('X-Ratelimit-Remaining', 'unknown')
            rate_limit_reset = response.headers.get('X-Ratelimit-Reset', 'unknown')
            
            diagnostics['tests']['rate_limits'] = {
                'status': 'success',
                'remaining': rate_limit_remaining,
                'reset_in_seconds': rate_limit_reset,
                'warning': rate_limit_remaining == '0'
            }
        except Exception as e:
            diagnostics['tests']['rate_limits'] = {
                'status': 'error',
                'error': str(e)
            }
        
        # Overall status determination
        api_ok = diagnostics['tests'].get('api_connection', {}).get('status') == 'success'
        whatsapp_ok = diagnostics['tests'].get('whatsapp_status', {}).get('connected', False)
        
        if api_ok and whatsapp_ok:
            diagnostics['overall_status'] = 'healthy'
            diagnostics['message'] = 'WhatsApp connection is working properly'
        elif api_ok and not whatsapp_ok:
            diagnostics['overall_status'] = 'warning'
            diagnostics['message'] = 'API working but WhatsApp Web may be disconnected'
        else:
            diagnostics['overall_status'] = 'error'
            diagnostics['message'] = 'WhatsApp API connection issues detected'
        
        # Recommendations
        recommendations = []
        if not api_ok:
            recommendations.append("Check your WASENDER_API_TOKEN configuration")
        if not whatsapp_ok:
            recommendations.append("Check WhatsApp Web connection in WaSender dashboard")
            recommendations.append("Ensure your phone is online and WhatsApp is active")
            recommendations.append("You may need to scan QR code in WaSender dashboard")
        
        diagnostics['recommendations'] = recommendations
        
        return jsonify({
            'status': 'success',
            'data': diagnostics
        })
        
    except Exception as e:
        logger.error(f"Error running diagnostics: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to run diagnostics: {str(e)}'
        }), 500

@whatsapp_status_bp.route('/api/whatsapp/troubleshoot', methods=['GET'])
def get_troubleshooting_guide():
    """
    Get troubleshooting guide for WhatsApp connection issues
    """
    guide = {
        'title': 'WhatsApp Connection Troubleshooting Guide',
        'last_updated': datetime.now().isoformat(),
        'steps': [
            {
                'step': 1,
                'title': 'Check Your Phone',
                'actions': [
                    'Ensure your phone has internet connection',
                    'WhatsApp is running and active',
                    'Phone is not in airplane mode',
                    'WhatsApp account is not banned or restricted'
                ]
            },
            {
                'step': 2,
                'title': 'Check WhatsApp Web',
                'actions': [
                    'Go to https://web.whatsapp.com',
                    'Ensure you are logged in',
                    'Check if session is active (green circle)',
                    'Look for any error messages'
                ]
            },
            {
                'step': 3,
                'title': 'Check WaSender Dashboard',
                'actions': [
                    'Go to your WaSender dashboard',
                    'Check WhatsApp Web connection status',
                    'Scan QR code if needed',
                    'Verify API token is active'
                ]
            },
            {
                'step': 4,
                'title': 'Reset Connection',
                'actions': [
                    'Logout from WhatsApp Web',
                    'Clear browser cache and cookies',
                    'Login again and scan QR code',
                    'Restart WaSender connection'
                ]
            },
            {
                'step': 5,
                'title': 'Contact Support',
                'actions': [
                    'If issues persist, contact WaSender support',
                    'Provide your API token and error details',
                    'Check WaSender status page for known issues'
                ]
            }
        ],
        'common_issues': [
            {
                'issue': 'Messages show as sent but not delivered',
                'cause': 'WhatsApp Web session disconnected',
                'solution': 'Reconnect WhatsApp Web in WaSender dashboard'
            },
            {
                'issue': 'API returns 422 errors',
                'cause': 'Invalid phone number format',
                'solution': 'Ensure phone numbers include country code (e.g., 917033009600)'
            },
            {
                'issue': 'Rate limit errors',
                'cause': 'Too many API requests',
                'solution': 'Wait for rate limit reset or upgrade plan'
            }
        ]
    }
    
    return jsonify({
        'status': 'success',
        'data': guide
    }) 