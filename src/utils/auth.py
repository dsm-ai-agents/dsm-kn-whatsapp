"""
Authentication Utilities
========================
JWT token validation and authentication middleware.
"""

import logging
import jwt
from functools import wraps
from flask import request, jsonify
from datetime import datetime

from src.core.supabase_client import get_supabase_manager

# Configure logging
logger = logging.getLogger(__name__)

# JWT Configuration (should match auth_routes.py)
JWT_SECRET = 'your-jwt-secret-key-change-in-production'  # TODO: Use environment variable
JWT_ALGORITHM = 'HS256'

def require_auth(f):
    """
    Decorator to require authentication for API endpoints.
    Validates JWT token and injects current_user into the function.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'status': 'error', 'message': 'No token provided'}), 401
        
        token = auth_header.split(' ')[1]
        
        try:
            # Decode JWT token
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            user_id = payload['user_id']
            tenant_id = payload['tenant_id']
            
            # Get current user info
            supabase = get_supabase_manager()
            rpc_result = supabase.supabase.rpc('get_user_by_ids', {
                'user_id_param': user_id,
                'tenant_id_param': tenant_id
            }).execute()
            
            if not rpc_result.data:
                return jsonify({'status': 'error', 'message': 'Invalid token'}), 401
            
            user = rpc_result.data[0]
            
            if not user['is_active']:
                return jsonify({'status': 'error', 'message': 'Account is deactivated'}), 401
            
            # Inject current user into function
            current_user = {
                'user_id': user['user_id'],
                'tenant_id': user['tenant_id'],
                'email': user['email'],
                'first_name': user['first_name'],
                'last_name': user['last_name'],
                'workspace_name': user['workspace_name'],
                'workspace_slug': user['workspace_slug']
            }
            
            return f(current_user, *args, **kwargs)
            
        except jwt.ExpiredSignatureError:
            return jsonify({'status': 'error', 'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'status': 'error', 'message': 'Invalid token'}), 401
        except Exception as e:
            logger.error(f"Authentication error: {e}", exc_info=True)
            return jsonify({'status': 'error', 'message': 'Authentication failed'}), 401
    
    return decorated_function

def get_current_user_from_token(token: str) -> dict:
    """
    Extract user information from JWT token.
    Returns user dict or None if invalid.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload['user_id']
        tenant_id = payload['tenant_id']
        
        supabase = get_supabase_manager()
        rpc_result = supabase.supabase.rpc('get_user_by_ids', {
            'user_id_param': user_id,
            'tenant_id_param': tenant_id
        }).execute()
        
        if not rpc_result.data:
            return None
        
        user = rpc_result.data[0]
        
        if not user['is_active']:
            return None
        
        return {
            'user_id': user['user_id'],
            'tenant_id': user['tenant_id'],
            'email': user['email'],
            'first_name': user['first_name'],
            'last_name': user['last_name'],
            'workspace_name': user['workspace_name'],
            'workspace_slug': user['workspace_slug']
        }
        
    except Exception as e:
        logger.error(f"Error getting user from token: {e}")
        return None 