"""
API Key Management Routes
========================
Handles CRUD operations for tenant API keys (OpenAI, WhatsApp, etc.)
Includes encryption/decryption and validation.
"""

import logging
import secrets
from datetime import datetime
from flask import Blueprint, request, jsonify
import openai

from src.core.supabase_client import get_supabase_manager
from src.utils.error_handling import handle_api_error
from src.utils.auth import require_auth
from src.utils.encryption import encrypt_api_key, decrypt_api_key

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
api_key_bp = Blueprint('api_keys', __name__, url_prefix='/api/api-keys')

def validate_openai_key(api_key: str) -> bool:
    """Validate OpenAI API key by making a test call."""
    try:
        client = openai.OpenAI(api_key=api_key)
        # Test with a minimal request
        response = client.models.list()
        return True
    except Exception as e:
        logger.error(f"OpenAI key validation failed: {e}")
        return False

@api_key_bp.route('', methods=['GET'])
@require_auth
@handle_api_error
def list_api_keys(current_user):
    """List all API keys for the current tenant."""
    tenant_id = current_user['tenant_id']
    
    supabase = get_supabase_manager()
    
    # Get API keys (without decrypting them)
    result = supabase.supabase.table('tenant_api_keys').select(
        'id, key_type, key_name, is_active, last_used_at, created_at'
    ).eq('tenant_id', tenant_id).execute()
    
    return jsonify({
        'status': 'success',
        'data': {
            'api_keys': result.data
        }
    }), 200

@api_key_bp.route('', methods=['POST'])
@require_auth
@handle_api_error
def add_api_key(current_user):
    """Add a new API key for the tenant."""
    data = request.json
    if not data:
        return jsonify({'status': 'error', 'message': 'No data provided'}), 400
    
    # Validate required fields
    required_fields = ['key_type', 'key_name', 'api_key']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'status': 'error', 'message': f'{field} is required'}), 400
    
    key_type = data['key_type'].lower()
    key_name = data['key_name'].strip()
    api_key = data['api_key'].strip()
    tenant_id = current_user['tenant_id']
    
    # Validate key type
    allowed_key_types = ['openai', 'whatsapp']
    if key_type not in allowed_key_types:
        return jsonify({'status': 'error', 'message': f'Invalid key_type. Allowed: {allowed_key_types}'}), 400
    
    # Validate API key based on type
    if key_type == 'openai':
        if not validate_openai_key(api_key):
            return jsonify({'status': 'error', 'message': 'Invalid OpenAI API key'}), 400
    
    supabase = get_supabase_manager()
    
    try:
        # Check if key name already exists for this tenant
        existing = supabase.supabase.table('tenant_api_keys').select('id').eq(
            'tenant_id', tenant_id
        ).eq('key_name', key_name).execute()
        
        if existing.data:
            return jsonify({'status': 'error', 'message': 'API key name already exists'}), 400
        
        # Encrypt the API key
        encrypted_key = encrypt_api_key(api_key)
        
        # Store the API key
        api_key_data = {
            'tenant_id': tenant_id,
            'key_type': key_type,
            'key_name': key_name,
            'encrypted_key': encrypted_key,
            'is_active': True,
            'created_at': datetime.utcnow().isoformat()
        }
        
        result = supabase.supabase.table('tenant_api_keys').insert(api_key_data).execute()
        
        if not result.data:
            return jsonify({'status': 'error', 'message': 'Failed to store API key'}), 500
        
        # Log the action
        audit_data = {
            'tenant_id': tenant_id,
            'user_id': current_user['user_id'],
            'action': 'api_key_added',
            'resource_type': 'api_key',
            'resource_id': result.data[0]['id'],
            'details': {'key_type': key_type, 'key_name': key_name},
            'ip_address': request.remote_addr
        }
        supabase.supabase.table('audit_logs').insert(audit_data).execute()
        
        logger.info(f"API key added: {key_name} ({key_type}) for tenant {tenant_id}")
        
        return jsonify({
            'status': 'success',
            'message': 'API key added successfully',
            'data': {
                'id': result.data[0]['id'],
                'key_type': key_type,
                'key_name': key_name,
                'is_active': True
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error adding API key: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Failed to add API key'}), 500

@api_key_bp.route('/<key_id>', methods=['PUT'])
@require_auth
@handle_api_error
def update_api_key(current_user, key_id):
    """Update an API key (name or active status)."""
    data = request.json
    if not data:
        return jsonify({'status': 'error', 'message': 'No data provided'}), 400
    
    tenant_id = current_user['tenant_id']
    supabase = get_supabase_manager()
    
    try:
        # Check if API key exists and belongs to tenant
        existing = supabase.supabase.table('tenant_api_keys').select('*').eq(
            'id', key_id
        ).eq('tenant_id', tenant_id).execute()
        
        if not existing.data:
            return jsonify({'status': 'error', 'message': 'API key not found'}), 404
        
        # Prepare update data
        update_data = {'updated_at': datetime.utcnow().isoformat()}
        
        if 'key_name' in data:
            update_data['key_name'] = data['key_name'].strip()
        
        if 'is_active' in data:
            update_data['is_active'] = bool(data['is_active'])
        
        # Update the API key
        result = supabase.supabase.table('tenant_api_keys').update(update_data).eq(
            'id', key_id
        ).execute()
        
        # Log the action
        audit_data = {
            'tenant_id': tenant_id,
            'user_id': current_user['user_id'],
            'action': 'api_key_updated',
            'resource_type': 'api_key',
            'resource_id': key_id,
            'details': update_data,
            'ip_address': request.remote_addr
        }
        supabase.supabase.table('audit_logs').insert(audit_data).execute()
        
        logger.info(f"API key updated: {key_id} for tenant {tenant_id}")
        
        return jsonify({
            'status': 'success',
            'message': 'API key updated successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating API key: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Failed to update API key'}), 500

@api_key_bp.route('/<key_id>', methods=['DELETE'])
@require_auth
@handle_api_error
def delete_api_key(current_user, key_id):
    """Delete an API key."""
    tenant_id = current_user['tenant_id']
    supabase = get_supabase_manager()
    
    try:
        # Check if API key exists and belongs to tenant
        existing = supabase.supabase.table('tenant_api_keys').select('key_name, key_type').eq(
            'id', key_id
        ).eq('tenant_id', tenant_id).execute()
        
        if not existing.data:
            return jsonify({'status': 'error', 'message': 'API key not found'}), 404
        
        key_info = existing.data[0]
        
        # Delete the API key
        supabase.supabase.table('tenant_api_keys').delete().eq('id', key_id).execute()
        
        # Log the action
        audit_data = {
            'tenant_id': tenant_id,
            'user_id': current_user['user_id'],
            'action': 'api_key_deleted',
            'resource_type': 'api_key',
            'resource_id': key_id,
            'details': key_info,
            'ip_address': request.remote_addr
        }
        supabase.supabase.table('audit_logs').insert(audit_data).execute()
        
        logger.info(f"API key deleted: {key_id} for tenant {tenant_id}")
        
        return jsonify({
            'status': 'success',
            'message': 'API key deleted successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting API key: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Failed to delete API key'}), 500

@api_key_bp.route('/test/<key_id>', methods=['POST'])
@require_auth
@handle_api_error
def test_api_key(current_user, key_id):
    """Test an API key to verify it's working."""
    tenant_id = current_user['tenant_id']
    supabase = get_supabase_manager()
    
    try:
        # Get the API key
        result = supabase.supabase.table('tenant_api_keys').select('*').eq(
            'id', key_id
        ).eq('tenant_id', tenant_id).execute()
        
        if not result.data:
            return jsonify({'status': 'error', 'message': 'API key not found'}), 404
        
        api_key_record = result.data[0]
        
        # Decrypt the key
        decrypted_key = decrypt_api_key(api_key_record['encrypted_key'])
        
        # Test based on key type
        if api_key_record['key_type'] == 'openai':
            is_valid = validate_openai_key(decrypted_key)
            
            if is_valid:
                # Update last_used_at
                supabase.supabase.table('tenant_api_keys').update({
                    'last_used_at': datetime.utcnow().isoformat()
                }).eq('id', key_id).execute()
            
            return jsonify({
                'status': 'success',
                'data': {
                    'is_valid': is_valid,
                    'key_type': api_key_record['key_type'],
                    'message': 'API key is valid' if is_valid else 'API key is invalid'
                }
            }), 200
        
        else:
            return jsonify({
                'status': 'error',
                'message': f"Testing not implemented for {api_key_record['key_type']} keys"
            }), 400
        
    except Exception as e:
        logger.error(f"Error testing API key: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Failed to test API key'}), 500 