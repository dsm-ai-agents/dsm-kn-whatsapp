"""
Authentication API Routes for SaaS System
========================================
Handles user registration, login, and tenant management.
"""

import logging
import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app
from src.core.supabase_client import get_supabase_manager
from src.utils.error_handling import handle_api_error
import re

logger = logging.getLogger(__name__)

# Create authentication blueprint
auth_bp = Blueprint('auth', __name__)

# JWT Configuration
JWT_SECRET = 'your-jwt-secret-key-change-in-production'  # TODO: Move to environment variable
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt."""
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}:{password_hash}"

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash."""
    try:
        salt, password_hash = hashed.split(':')
        return hashlib.sha256((password + salt).encode()).hexdigest() == password_hash
    except ValueError:
        return False

def generate_jwt_token(user_id: str, tenant_id: str) -> str:
    """Generate JWT token for user."""
    payload = {
        'user_id': user_id,
        'tenant_id': tenant_id,
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def generate_workspace_slug(workspace_name: str) -> str:
    """Generate URL-friendly workspace slug."""
    slug = re.sub(r'[^a-zA-Z0-9\s-]', '', workspace_name.lower())
    slug = re.sub(r'\s+', '-', slug.strip())
    return slug[:50]  # Limit length

@auth_bp.route('/register', methods=['POST'])
@handle_api_error
def register():
    """
    Register a new user and create their workspace.
    
    Expected JSON:
    {
        "email": "user@example.com",
        "password": "securepassword",
        "first_name": "John",
        "last_name": "Doe",
        "workspace_name": "My Company"
    }
    """
    data = request.json
    if not data:
        return jsonify({'status': 'error', 'message': 'No data provided'}), 400
    
    # Validate required fields - accept both company_name and workspace_name for compatibility
    required_fields = ['email', 'password', 'first_name']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'status': 'error', 'message': f'{field} is required'}), 400
    
    # Check for workspace name (accept both company_name and workspace_name)
    workspace_name = data.get('company_name') or data.get('workspace_name')
    if not workspace_name:
        return jsonify({'status': 'error', 'message': 'company_name is required'}), 400
    
    email = data['email'].lower().strip()
    password = data['password']
    first_name = data['first_name'].strip()
    last_name = data.get('last_name', '').strip()
    phone = data.get('phone', '').strip() if data.get('phone') else None
    workspace_name = workspace_name.strip()
    
    # Validate email format
    if not validate_email(email):
        return jsonify({'status': 'error', 'message': 'Invalid email format'}), 400
    
    # Validate password strength
    if len(password) < 8:
        return jsonify({'status': 'error', 'message': 'Password must be at least 8 characters'}), 400
    
    supabase = get_supabase_manager()
    
    try:
        # Check if user already exists
        existing_user = supabase.supabase.table('users').select('id').eq('email', email).execute()
        if existing_user.data:
            return jsonify({'status': 'error', 'message': 'User already exists'}), 400
        
        # Generate workspace slug
        workspace_slug = generate_workspace_slug(workspace_name)
        
        # Check if workspace slug is taken
        existing_workspace = supabase.supabase.table('tenants').select('id').eq('workspace_slug', workspace_slug).execute()
        if existing_workspace.data:
            # Add random suffix if slug is taken
            workspace_slug = f"{workspace_slug}-{secrets.token_hex(4)}"
        
        # Hash password
        password_hash = hash_password(password)
        
        # Create user (temporarily removing phone due to schema cache issue)
        user_data = {
            'email': email,
            'password_hash': password_hash,
            'first_name': first_name,
            'last_name': last_name,
            'email_verified': False,  # TODO: Implement email verification
            'is_active': True
        }
        
        user_result = supabase.supabase.table('users').insert(user_data).execute()
        if not user_result.data:
            return jsonify({'status': 'error', 'message': 'Failed to create user'}), 500
        
        user_id = user_result.data[0]['id']
        
        # Create tenant/workspace
        tenant_data = {
            'user_id': user_id,
            'workspace_name': workspace_name,
            'workspace_slug': workspace_slug,
            'subscription_status': 'trial',
            'subscription_plan': 'starter',
            'trial_ends_at': (datetime.utcnow() + timedelta(days=14)).isoformat()
        }
        
        tenant_result = supabase.supabase.table('tenants').insert(tenant_data).execute()
        if not tenant_result.data:
            # Rollback user creation
            supabase.supabase.table('users').delete().eq('id', user_id).execute()
            return jsonify({'status': 'error', 'message': 'Failed to create workspace'}), 500
        
        tenant_id = tenant_result.data[0]['id']
        
        # Generate JWT token
        token = generate_jwt_token(user_id, tenant_id)
        
        # Log registration
        audit_data = {
            'tenant_id': tenant_id,
            'user_id': user_id,
            'action': 'user_registered',
            'resource_type': 'user',
            'resource_id': user_id,
            'details': {'email': email, 'workspace_name': workspace_name},
            'ip_address': request.remote_addr
        }
        supabase.supabase.table('audit_logs').insert(audit_data).execute()
        
        logger.info(f"New user registered: {email} with workspace: {workspace_name}")
        
        return jsonify({
            'status': 'success',
            'message': 'Registration successful',
            'data': {
                'user': {
                    'id': user_id,
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name
                },
                'workspace': {
                    'id': tenant_id,
                    'name': workspace_name,
                    'slug': workspace_slug,
                    'subscription_status': 'trial',
                    'trial_ends_at': tenant_data['trial_ends_at']
                },
                'token': token
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Registration error: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Registration failed'}), 500

@auth_bp.route('/login', methods=['POST'])
@handle_api_error
def login():
    """
    Authenticate user and return JWT token.
    
    Expected JSON:
    {
        "email": "user@example.com",
        "password": "securepassword"
    }
    """
    data = request.json
    if not data:
        return jsonify({'status': 'error', 'message': 'No data provided'}), 400
    
    email = data.get('email', '').lower().strip()
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({'status': 'error', 'message': 'Email and password are required'}), 400
    
    supabase = get_supabase_manager()
    
    try:
        # Get user with tenant info
        user_query = """
            SELECT 
                u.id as user_id,
                u.email,
                u.password_hash,
                u.first_name,
                u.last_name,
                u.is_active,
                t.id as tenant_id,
                t.workspace_name,
                t.workspace_slug,
                t.subscription_status,
                t.subscription_plan
            FROM users u
            JOIN tenants t ON u.id = t.user_id
            WHERE u.email = %s
        """
        
        result = supabase.execute_raw_sql(user_query, (email,))
        if not result:
            return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401
        
        user = result[0]
        
        # Check if user is active
        if not user['is_active']:
            return jsonify({'status': 'error', 'message': 'Account is deactivated'}), 401
        
        # Verify password
        if not verify_password(password, user['password_hash']):
            return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401
        
        # Update last login
        supabase.supabase.table('users').update({
            'last_login_at': datetime.utcnow().isoformat()
        }).eq('id', user['user_id']).execute()
        
        # Generate JWT token
        token = generate_jwt_token(user['user_id'], user['tenant_id'])
        
        # Log login
        audit_data = {
            'tenant_id': user['tenant_id'],
            'user_id': user['user_id'],
            'action': 'user_login',
            'resource_type': 'user',
            'resource_id': user['user_id'],
            'details': {'email': email},
            'ip_address': request.remote_addr
        }
        supabase.supabase.table('audit_logs').insert(audit_data).execute()
        
        logger.info(f"User logged in: {email}")
        
        return jsonify({
            'user': {
                'user_id': user['user_id'],
                'email': user['email'],
                'first_name': user['first_name'],
                'last_name': user['last_name'],
                'company_name': user['workspace_name'],
                'workspace_slug': user['workspace_slug']
            },
            'token': token
        }), 200
        
    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Login failed'}), 500

@auth_bp.route('/verify-token', methods=['POST'])
@handle_api_error
def verify_token():
    """
    Verify JWT token and return user info.
    
    Expected Headers:
    Authorization: Bearer <token>
    """
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'status': 'error', 'message': 'No token provided'}), 401
    
    token = auth_header.split(' ')[1]
    
    try:
        logger.debug(f"Attempting to decode token: {token[:50]}...")
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        logger.debug(f"Token decoded successfully: {payload}")
        
        user_id = payload['user_id']
        tenant_id = payload['tenant_id']
        
        logger.debug(f"Token verification: user_id={user_id}, tenant_id={tenant_id}")
        
        # Get current user info using RPC function directly
        supabase = get_supabase_manager()
        rpc_result = supabase.supabase.rpc('get_user_by_ids', {
            'user_id_param': user_id,
            'tenant_id_param': tenant_id
        }).execute()
        
        logger.debug(f"RPC result: {rpc_result}")
        logger.debug(f"RPC data: {rpc_result.data}")
        
        result = rpc_result.data
        if not result:
            logger.warning(f"No user found for user_id={user_id}, tenant_id={tenant_id}")
            return jsonify({'status': 'error', 'message': 'Invalid token'}), 401
        
        user = result[0]
        
        if not user['is_active']:
            return jsonify({'status': 'error', 'message': 'Account is deactivated'}), 401
        
        return jsonify({
            'status': 'success',
            'data': {
                'user': {
                    'id': user['user_id'],
                    'email': user['email'],
                    'first_name': user['first_name'],
                    'last_name': user['last_name']
                },
                'workspace': {
                    'id': user['tenant_id'],
                    'name': user['workspace_name'],
                    'slug': user['workspace_slug'],
                    'subscription_status': user['subscription_status'],
                    'subscription_plan': user['subscription_plan']
                }
            }
        }), 200
        
    except jwt.ExpiredSignatureError:
        return jsonify({'status': 'error', 'message': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'status': 'error', 'message': 'Invalid token'}), 401
    except Exception as e:
        logger.error(f"Token verification error: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Token verification failed'}), 500

@auth_bp.route('/profile', methods=['GET'])
@handle_api_error
def get_profile():
    """Get user profile information."""
    # This would use the auth middleware to get current user
    # For now, return a placeholder response
    return jsonify({
        'status': 'success',
        'message': 'Profile endpoint - implement auth middleware first'
    }), 200 