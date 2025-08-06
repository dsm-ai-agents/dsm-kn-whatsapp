"""
WhatsApp AI Chatbot - API Routes
===============================
All API endpoints organized in a Flask Blueprint.
Handles dashboard stats, conversations, CRM, and campaign endpoints.

Author: Rian Infotech
Version: 2.2 (Structured)
"""

import logging
from flask import Blueprint, request, jsonify

# Import core functionality
from src.core.supabase_client import get_supabase_manager
from src.services.wasender_contact_service import wasender_contact_service

# Configure logging
logger = logging.getLogger(__name__)

# Create Blueprint for API routes
api_bp = Blueprint('api', __name__)

# ============================================================================
# DASHBOARD & STATS API
# ============================================================================

@api_bp.route('/dashboard-stats', methods=['GET'])
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


@api_bp.route('/system-status', methods=['GET'])
def get_system_status():
    """Get detailed system component status."""
    try:
        import os
        from datetime import datetime, timezone
        
        # Check database connection
        supabase = get_supabase_manager()
        database_status = 'operational' if supabase.is_connected() else 'down'
        
        # Check WhatsApp API configuration
        whatsapp_status = 'operational' if os.getenv('WASENDER_API_KEY') else 'not_configured'
        
        # Check AI service configuration
        ai_status = 'operational' if os.getenv('OPENAI_API_KEY') else 'not_configured'
        
        # API is operational if we can respond
        api_status = 'operational'
        
        # Calculate uptime (placeholder - would need actual tracking)
        uptime = '99.9%'
        
        return jsonify({
            'status': 'success',
            'data': {
                'api_status': api_status,
                'database_status': database_status,
                'whatsapp_status': whatsapp_status,
                'ai_status': ai_status,
                'last_updated': datetime.now(timezone.utc).isoformat(),
                'uptime': uptime
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve system status'
        }), 500


@api_bp.route('/contacts', methods=['GET'])
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


@api_bp.route('/campaigns', methods=['GET'])
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


@api_bp.route('/campaign/<campaign_id>', methods=['GET'])
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


# ============================================================================
# CONVERSATIONS API
# ============================================================================

@api_bp.route('/conversations', methods=['GET'])
def get_conversations():
    """Get all conversations with contact details, optimized and deduplicated."""
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
        
        # Query to get conversations with contact details - group by contact to avoid duplicates
        conversations = supabase.client.table('conversations')\
            .select('*, contacts!inner(id, phone_number, name, email, company, position, lead_status, lead_score, created_at)')\
            .order('last_message_at', desc=True)\
            .range(offset, offset + limit - 1)\
            .execute()
        
        # Track seen contacts to avoid duplicates
        seen_contacts = set()
        formatted_conversations = []
        
        for conv in conversations.data:
            contact = conv['contacts']
            contact_id = contact['id']
            
            # Skip if we've already seen this contact
            if contact_id in seen_contacts:
                continue
            seen_contacts.add(contact_id)
            
            # Get last message for preview
            messages = conv.get('messages', [])
            last_message = messages[-1] if messages else None
            
            # Clean phone number formatting
            raw_phone = contact['phone_number'] or ''
            clean_phone = raw_phone.replace('_s_whatsapp_net', '').replace('@s.whatsapp.net', '')
            
            # Auto-sync contact from WASender if enabled and name is missing
            if auto_sync and wasender_contact_service.is_configured() and (not contact.get('name') or contact.get('name', '').endswith('_s_whatsapp_net')):
                try:
                    # Try to sync this contact from WASender
                    wasender_contact_service.sync_single_contact(clean_phone)
                    
                    # Re-fetch the contact to get updated information
                    updated_contact_result = supabase.client.table('contacts')\
                        .select('id, phone_number, name, email, company, position, lead_status, lead_score, created_at, verified_name, profile_image_url, whatsapp_status, is_business_account')\
                        .eq('id', contact['id'])\
                        .execute()
                    
                    if updated_contact_result.data:
                        contact = updated_contact_result.data[0]
                        logger.debug(f"Auto-synced contact {clean_phone} from WASender")
                except Exception as e:
                    logger.debug(f"Failed to auto-sync contact {clean_phone}: {e}")
            
            # Determine display name with fallback hierarchy (prioritize WASender data)
            display_name = None
            if contact.get('verified_name'):
                display_name = contact['verified_name']
            elif contact.get('name') and not contact['name'].endswith('_s_whatsapp_net'):
                display_name = contact['name']
            elif contact.get('company'):
                display_name = f"Contact from {contact['company']}"
            else:
                # Format phone number nicely for display
                if clean_phone.startswith('91') and len(clean_phone) == 12:
                    # Indian number format
                    display_name = f"+91 {clean_phone[2:7]} {clean_phone[7:]}"
                elif len(clean_phone) >= 10:
                    # Generic international format
                    display_name = f"+{clean_phone[:2]} {clean_phone[2:6]} {clean_phone[6:]}"
                else:
                    display_name = f"+{clean_phone}"
            
            # Build clean contact object
            contact_info = {
                'id': contact_id,
                'phone_number': clean_phone,
                'display_phone': f"+{clean_phone}" if clean_phone else raw_phone,
                'name': display_name,
                'email': contact.get('email'),
                'company': contact.get('company'),
                'position': contact.get('position'),
                'lead_status': contact.get('lead_status', 'new'),
                'lead_score': contact.get('lead_score', 0),
                'created_at': contact['created_at']
            }
            
            # Format last message preview
            last_message_preview = 'No messages'
            if last_message:
                content = last_message.get('content', '')
                if len(content) > 80:
                    last_message_preview = content[:80] + '...'
                else:
                    last_message_preview = content
            
            formatted_conversations.append({
                'id': conv['id'],
                'contact': contact_info,
                'last_message_at': conv['last_message_at'],
                'message_count': len(messages),
                'last_message_preview': last_message_preview,
                'last_message_role': last_message.get('role') if last_message else None,
                'unread_count': 0  # Placeholder for future implementation
            })
        
        return jsonify({
            'status': 'success',
            'data': formatted_conversations,
            'pagination': {
                'limit': limit,
                'offset': offset,
                'count': len(formatted_conversations),
                'total_unique_contacts': len(seen_contacts)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting conversations: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve conversations'
        }), 500


@api_bp.route('/conversation/<conversation_id>', methods=['GET'])
def get_conversation_details(conversation_id):
    """Get detailed conversation messages with CRM-enriched contact data."""
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
        
        # Get phone number and try to enrich with CRM data
        phone_number = conversation['contacts']['phone_number']
        base_phone = phone_number.replace('_s_whatsapp_net', '') if phone_number else ''
        
        # Try to get CRM customer context
        crm_context = None
        try:
            crm_context = supabase.get_customer_context_by_phone(base_phone)
        except Exception as e:
            logger.debug(f"Could not get CRM context for {base_phone}: {e}")
        
        # Use CRM name if available, otherwise fallback to conversation contact name
        contact_name = conversation['contacts']['name']
        contact_info = {
            'phone_number': phone_number,
            'name': contact_name or phone_number,
            'created_at': conversation['contacts']['created_at']
        }
        
        # Add CRM enrichment if available
        if crm_context and not crm_context.get('is_new_customer', True):
            # CRM context found - use the data directly
            if crm_context.get('name'):
                contact_info['name'] = crm_context['name']
            if crm_context.get('email'):
                contact_info['email'] = crm_context['email']
            if crm_context.get('company'):
                contact_info['company'] = crm_context['company']
            if crm_context.get('position'):
                contact_info['position'] = crm_context['position']
            if crm_context.get('lead_status'):
                contact_info['lead_status'] = crm_context['lead_status']
            if crm_context.get('lead_score') is not None:
                contact_info['lead_score'] = crm_context['lead_score']
            
            # Add CRM summary for frontend display
            contact_info['crm_summary'] = crm_context.get('context_summary', '')
        
        # Format the response
        formatted_conversation = {
            'id': conversation['id'],
            'contact': contact_info,
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


@api_bp.route('/conversation/search', methods=['GET'])
def search_conversations():
    """Search conversations by contact name or phone number with CRM enrichment."""
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
        
        # Search phone numbers
        phone_conversations = supabase.client.table('conversations')\
            .select('*, contacts!inner(phone_number, name, created_at)')\
            .ilike('contacts.phone_number', f'%{search_query}%')\
            .order('last_message_at', desc=True)\
            .limit(20)\
            .execute()
        
        # Search names
        name_conversations = supabase.client.table('conversations')\
            .select('*, contacts!inner(phone_number, name, created_at)')\
            .ilike('contacts.name', f'%{search_query}%')\
            .order('last_message_at', desc=True)\
            .limit(20)\
            .execute()
        
        # Combine and deduplicate results
        all_conversations = {}
        for conv in phone_conversations.data + name_conversations.data:
            all_conversations[conv['id']] = conv
        
        # Sort by last_message_at and limit
        sorted_conversations = sorted(
            all_conversations.values(), 
            key=lambda x: x['last_message_at'], 
            reverse=True
        )[:20]
        
        # Format the response with CRM enrichment
        formatted_conversations = []
        for conv in sorted_conversations:
            messages = conv.get('messages', [])
            last_message = messages[-1] if messages else None
            
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
            contact_name = conv['contacts']['name']
            contact_info = {
                'phone_number': phone_number,
                'name': contact_name or phone_number,
                'created_at': conv['contacts']['created_at']
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
            
            formatted_conversations.append({
                'id': conv['id'],
                'contact': contact_info,
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


def normalize_phone_number(phone_number):
    """Normalize phone number for deduplication."""
    if not phone_number:
        return ''
    
    # Remove all non-digit characters
    clean = ''.join(filter(str.isdigit, phone_number))
    
    # Handle Indian numbers specifically
    if len(clean) == 12 and clean.startswith('91'):
        return clean[2:]  # Remove country code for Indian numbers
    elif len(clean) == 10:
        return clean  # Already without country code
    elif len(clean) > 10:
        # For other international numbers, keep last 10 digits
        return clean[-10:]
    
    return clean


@api_bp.route('/conversations/unique', methods=['GET'])
def get_unique_conversations():
    """Get unique conversations (one per normalized phone number) with latest activity and WASender enrichment."""
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
        auto_sync = request.args.get('auto_sync', 'false').lower() == 'true'
        
        # Get all conversations with contact details including bot_enabled status
        all_conversations = supabase.client.table('conversations')\
            .select('id, last_message_at, messages, bot_enabled, contacts!inner(id, phone_number, name, email, company, position, lead_status, lead_score, created_at, verified_name, profile_image_url, whatsapp_status, is_business_account)')\
            .order('last_message_at', desc=True)\
            .execute()
        
        # Group by normalized phone number and keep only the latest conversation per phone
        phone_conversations = {}
        for conv in all_conversations.data:
            contact = conv['contacts']
            raw_phone = contact['phone_number'] or ''
            
            # Normalize phone number for deduplication
            normalized_phone = normalize_phone_number(raw_phone)
            
            # Skip if no valid phone number
            if not normalized_phone:
                continue
            
            # Keep only the most recent conversation per normalized phone number
            if normalized_phone not in phone_conversations:
                phone_conversations[normalized_phone] = conv
            else:
                # Compare timestamps and keep the more recent one
                current_time = conv['last_message_at']
                existing_time = phone_conversations[normalized_phone]['last_message_at']
                if current_time > existing_time:
                    phone_conversations[normalized_phone] = conv
        
        # Sort by last_message_at and apply pagination
        unique_conversations = list(phone_conversations.values())
        unique_conversations.sort(key=lambda x: x['last_message_at'], reverse=True)
        
        # Apply pagination
        paginated_conversations = unique_conversations[offset:offset + limit]
        
        # Format the response
        formatted_conversations = []
        for conv in paginated_conversations:
            contact = conv['contacts']
            
            # Get last message for preview
            messages = conv.get('messages', [])
            last_message = messages[-1] if messages else None
            
            # Clean phone number formatting
            raw_phone = contact['phone_number'] or ''
            clean_phone = raw_phone.replace('_s_whatsapp_net', '').replace('@s.whatsapp.net', '')
            normalized_phone = normalize_phone_number(clean_phone)
            
            # Determine display name with fallback hierarchy
            display_name = None
            if contact.get('name') and not contact['name'].endswith('_s_whatsapp_net'):
                display_name = contact['name']
            elif contact.get('company'):
                display_name = f"Contact from {contact['company']}"
            else:
                # Format phone number nicely for display
                if len(normalized_phone) == 10:
                    # Format as +91 XXXXX XXXXX for 10-digit numbers
                    display_name = f"+91 {normalized_phone[:5]} {normalized_phone[5:]}"
                elif len(clean_phone) >= 10:
                    # Generic international format
                    display_name = f"+{clean_phone}"
                else:
                    display_name = f"+{clean_phone}"
            
            # Build clean contact object with WASender enrichment
            contact_info = {
                'id': contact['id'],
                'phone_number': normalized_phone,
                'display_phone': f"+91{normalized_phone}" if len(normalized_phone) == 10 else f"+{clean_phone}",
                'name': display_name,
                'email': contact.get('email'),
                'company': contact.get('company'),
                'position': contact.get('position'),
                'lead_status': contact.get('lead_status', 'new'),
                'lead_score': contact.get('lead_score', 0),
                'created_at': contact['created_at'],
                # WASender enrichment fields
                'verified_name': contact.get('verified_name'),
                'profile_image_url': contact.get('profile_image_url'),
                'whatsapp_status': contact.get('whatsapp_status'),
                'is_business_account': contact.get('is_business_account', False)
            }
            
            # Format last message preview
            last_message_preview = 'No messages'
            if last_message:
                content = last_message.get('content', '')
                if len(content) > 80:
                    last_message_preview = content[:80] + '...'
                else:
                    last_message_preview = content
            
            formatted_conversations.append({
                'id': conv['id'],
                'contact': contact_info,
                'last_message_at': conv['last_message_at'],
                'message_count': len(messages),
                'last_message_preview': last_message_preview,
                'last_message_role': last_message.get('role') if last_message else None,
                'unread_count': 0,  # Placeholder for future implementation
                'bot_enabled': conv.get('bot_enabled', True)  # Include bot status for handover feature
            })
        
        return jsonify({
            'status': 'success',
            'data': formatted_conversations,
            'pagination': {
                'limit': limit,
                'offset': offset,
                'count': len(formatted_conversations),
                'total_unique_contacts': len(unique_conversations)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting unique conversations: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve unique conversations'
        }), 500


# ============================================================================
# CRM API ENDPOINTS
# ============================================================================

@api_bp.route('/crm/contacts', methods=['GET'])
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


@api_bp.route('/crm/contacts/unique', methods=['GET'])
def get_unique_crm_contacts():
    """Get deduplicated CRM contacts with clean phone number formatting."""
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
        
        # Get all contacts first
        query = supabase.client.table('contacts')\
            .select('id, phone_number, name, email, company, position, lead_status, lead_score, source, notes, last_contacted_at, next_follow_up_at, created_at')
        
        if lead_status:
            query = query.eq('lead_status', lead_status)
        
        result = query.order('lead_score', desc=True).execute()
        
        if not result.data:
            return jsonify({
                'status': 'success',
                'data': [],
                'pagination': {
                    'limit': limit,
                    'offset': offset,
                    'count': 0,
                    'total_unique_contacts': 0
                }
            }), 200
        
        # Group contacts by normalized phone number to eliminate duplicates
        phone_groups = {}
        
        for contact in result.data:
            phone_number = contact.get('phone_number', '')
            if not phone_number:
                continue
                
            # Normalize phone number for grouping
            normalized_phone = normalize_phone_number(phone_number)
            
            if normalized_phone not in phone_groups:
                phone_groups[normalized_phone] = []
            phone_groups[normalized_phone].append(contact)
        
        # Select the best contact from each group (prioritize by lead_score, then by having name/company)
        unique_contacts = []
        
        for normalized_phone, contacts in phone_groups.items():
            # Sort contacts by priority: lead_score desc, has name, has company, created_at desc
            best_contact = max(contacts, key=lambda c: (
                c.get('lead_score', 0),
                1 if c.get('name') else 0,
                1 if c.get('company') else 0,
                c.get('created_at', '')
            ))
            
            # Clean up the phone number formatting
            original_phone = best_contact['phone_number']
            clean_phone = original_phone.replace('_s_whatsapp_net', '')
            
            # Format phone number for display
            if clean_phone.startswith('91') and len(clean_phone) == 12:
                # Indian number: 917033009600 -> +91 70330 09600
                formatted_phone = f"+91 {clean_phone[2:7]} {clean_phone[7:]}"
            elif clean_phone.startswith('+'):
                # Already has country code
                formatted_phone = clean_phone
            elif len(clean_phone) == 10:
                # Assume Indian number without country code
                formatted_phone = f"+91 {clean_phone[:5]} {clean_phone[5:]}"
            else:
                # Other formats
                formatted_phone = f"+{clean_phone}" if not clean_phone.startswith('+') else clean_phone
            
            # Create clean contact object
            clean_contact = {
                'id': best_contact['id'],
                'phone_number': clean_phone,
                'display_phone': formatted_phone,
                'name': best_contact.get('name') or formatted_phone,
                'email': best_contact.get('email'),
                'company': best_contact.get('company'),
                'position': best_contact.get('position'),
                'lead_status': best_contact.get('lead_status', 'new'),
                'lead_score': best_contact.get('lead_score', 0),
                'source': best_contact.get('source'),
                'notes': best_contact.get('notes'),
                'last_contacted_at': best_contact.get('last_contacted_at'),
                'next_follow_up_at': best_contact.get('next_follow_up_at'),
                'created_at': best_contact.get('created_at')
            }
            
            unique_contacts.append(clean_contact)
        
        # Sort by lead score descending
        unique_contacts.sort(key=lambda c: c.get('lead_score', 0), reverse=True)
        
        # Apply pagination
        total_unique = len(unique_contacts)
        paginated_contacts = unique_contacts[offset:offset + limit]
        
        return jsonify({
            'status': 'success',
            'data': paginated_contacts,
            'pagination': {
                'limit': limit,
                'offset': offset,
                'count': len(paginated_contacts),
                'total_unique_contacts': total_unique
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting unique CRM contacts: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve unique CRM contacts'
        }), 500


@api_bp.route('/crm/contacts/search', methods=['GET'])
def search_crm_contacts():
    """Search CRM contacts by name, phone number, company, or email."""
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
        
        # Get pagination parameters
        limit = min(int(request.args.get('limit', 20)), 100)
        offset = int(request.args.get('offset', 0))
        
        # Search in name
        name_contacts = supabase.client.table('contacts')\
            .select('id, phone_number, name, email, company, position, lead_status, lead_score, source, notes, last_contacted_at, next_follow_up_at, created_at')\
            .ilike('name', f'%{search_query}%')\
            .order('lead_score', desc=True)\
            .limit(limit)\
            .execute()
        
        # Search in phone number
        phone_contacts = supabase.client.table('contacts')\
            .select('id, phone_number, name, email, company, position, lead_status, lead_score, source, notes, last_contacted_at, next_follow_up_at, created_at')\
            .ilike('phone_number', f'%{search_query}%')\
            .order('lead_score', desc=True)\
            .limit(limit)\
            .execute()
        
        # Search in company
        company_contacts = supabase.client.table('contacts')\
            .select('id, phone_number, name, email, company, position, lead_status, lead_score, source, notes, last_contacted_at, next_follow_up_at, created_at')\
            .ilike('company', f'%{search_query}%')\
            .order('lead_score', desc=True)\
            .limit(limit)\
            .execute()
        
        # Search in email
        email_contacts = supabase.client.table('contacts')\
            .select('id, phone_number, name, email, company, position, lead_status, lead_score, source, notes, last_contacted_at, next_follow_up_at, created_at')\
            .ilike('email', f'%{search_query}%')\
            .order('lead_score', desc=True)\
            .limit(limit)\
            .execute()
        
        # Combine and deduplicate results
        all_contacts = {}
        for contact in (name_contacts.data + phone_contacts.data + company_contacts.data + email_contacts.data):
            all_contacts[contact['id']] = contact
        
        # Sort by lead_score and apply pagination
        sorted_contacts = sorted(
            all_contacts.values(), 
            key=lambda x: x.get('lead_score', 0), 
            reverse=True
        )[offset:offset + limit]
        
        # Format the response
        formatted_contacts = []
        for contact in sorted_contacts:
            # Clean up phone number formatting
            original_phone = contact.get('phone_number', '')
            clean_phone = original_phone.replace('_s_whatsapp_net', '')
            
            # Format phone number for display
            if clean_phone.startswith('91') and len(clean_phone) == 12:
                formatted_phone = f"+91 {clean_phone[2:7]} {clean_phone[7:]}"
            elif clean_phone.startswith('+'):
                formatted_phone = clean_phone
            elif len(clean_phone) == 10:
                formatted_phone = f"+91 {clean_phone[:5]} {clean_phone[5:]}"
            else:
                formatted_phone = f"+{clean_phone}" if clean_phone and not clean_phone.startswith('+') else clean_phone
            
            formatted_contacts.append({
                'id': contact['id'],
                'phone_number': clean_phone,
                'display_phone': formatted_phone,
                'name': contact.get('name') or formatted_phone,
                'email': contact.get('email'),
                'company': contact.get('company'),
                'position': contact.get('position'),
                'lead_status': contact.get('lead_status', 'new'),
                'lead_score': contact.get('lead_score', 0),
                'source': contact.get('source'),
                'notes': contact.get('notes'),
                'last_contacted_at': contact.get('last_contacted_at'),
                'next_follow_up_at': contact.get('next_follow_up_at'),
                'created_at': contact.get('created_at')
            })
        
        return jsonify({
            'status': 'success',
            'data': formatted_contacts,
            'query': search_query,
            'pagination': {
                'limit': limit,
                'offset': offset,
                'count': len(formatted_contacts)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error searching CRM contacts: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Failed to search CRM contacts'
        }), 500


@api_bp.route('/crm/contacts', methods=['POST'])
def create_crm_contact():
    """Create a new CRM contact."""
    try:
        supabase = get_supabase_manager()
        
        if not supabase.is_connected():
            return jsonify({
                'status': 'error',
                'message': 'Database not connected'
            }), 503
        
        # Get request data
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
        
        # Validate required fields
        required_fields = ['name', 'phone_number']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'status': 'error',
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Normalize phone number
        phone_number = data['phone_number'].strip()
        if not phone_number.startswith('+'):
            # Assume Indian number if no country code
            if len(phone_number) == 10:
                phone_number = f"91{phone_number}"
            elif not phone_number.startswith('91'):
                phone_number = f"91{phone_number}"
        
        # Check if contact already exists
        existing_contact = supabase.client.table('contacts')\
            .select('id')\
            .eq('phone_number', phone_number)\
            .execute()
        
        if existing_contact.data:
            return jsonify({
                'status': 'error',
                'message': 'Contact with this phone number already exists'
            }), 409
        
        # Prepare contact data
        contact_data = {
            'name': data['name'].strip(),
            'phone_number': phone_number,
            'email': data.get('email', '').strip() if data.get('email') else None,
            'company': data.get('company', '').strip() if data.get('company') else None,
            'position': data.get('position', '').strip() if data.get('position') else None,
            'source': data.get('source', 'manual').strip(),
            'lead_status': data.get('lead_status', 'new'),
            'notes': data.get('notes', '').strip() if data.get('notes') else None,
            'lead_score': 0,  # Default score for new contacts
        }
        
        # Handle tags if provided
        tags = data.get('tags', [])
        if tags and isinstance(tags, list):
            contact_data['tags'] = tags
        
        # Insert contact into database
        result = supabase.client.table('contacts')\
            .insert(contact_data)\
            .execute()
        
        if not result.data:
            return jsonify({
                'status': 'error',
                'message': 'Failed to create contact'
            }), 500
        
        created_contact = result.data[0]
        
        # Format response
        response_contact = {
            'id': created_contact['id'],
            'name': created_contact['name'],
            'phone_number': created_contact['phone_number'],
            'email': created_contact.get('email'),
            'company': created_contact.get('company'),
            'position': created_contact.get('position'),
            'source': created_contact.get('source'),
            'lead_status': created_contact.get('lead_status'),
            'lead_score': created_contact.get('lead_score', 0),
            'notes': created_contact.get('notes'),
            'tags': created_contact.get('tags', []),
            'created_at': created_contact.get('created_at')
        }
        
        return jsonify({
            'status': 'success',
            'data': response_contact,
            'message': 'Contact created successfully'
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating CRM contact: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Failed to create contact: {str(e)}'
        }), 500


@api_bp.route('/crm/user/<user_id>', methods=['GET'])
def get_crm_user(user_id):
    """Get single contact/user by ID."""
    try:
        supabase = get_supabase_manager()
        
        if not supabase.is_connected():
            return jsonify({
                'status': 'error',
                'message': 'Database not connected'
            }), 503
        
        # Get contact by ID
        result = supabase.client.table('contacts')\
            .select('id, phone_number, name, email, company, position, lead_status, lead_score, source, notes, last_contacted_at, next_follow_up_at, created_at')\
            .eq('id', user_id)\
            .execute()
        
        if not result.data:
            return jsonify({
                'status': 'error',
                'message': 'Contact not found'
            }), 404
        
        contact = result.data[0]
        
        # Format for frontend compatibility
        user_data = {
            'id': contact['id'],
            'name': contact.get('name', 'Unknown'),
            'company': contact.get('company'),
            'email': contact.get('email'),
            'phone_number': contact['phone_number'],
            'position': contact.get('position'),
            'lead_status': contact.get('lead_status'),
            'lead_score': contact.get('lead_score'),
            'crm_summary': contact.get('notes', ''),
            'avatar_url': None,
            'tags': []
        }
        
        return jsonify(user_data), 200
        
    except Exception as e:
        logger.error(f"Error getting CRM user: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve user'
        }), 500


@api_bp.route('/crm/user/<user_id>/stats', methods=['GET'])
def get_crm_user_stats(user_id):
    """Get stats for a specific user."""
    try:
        supabase = get_supabase_manager()
        
        if not supabase.is_connected():
            return jsonify({
                'status': 'error',
                'message': 'Database not connected'
            }), 503
        
        # Get contact to verify it exists
        contact_result = supabase.client.table('contacts')\
            .select('id, phone_number')\
            .eq('id', user_id)\
            .execute()
        
        if not contact_result.data:
            return jsonify({
                'status': 'error',
                'message': 'Contact not found'
            }), 404
        
        contact = contact_result.data[0]
        contact_id = contact['id']
        
        # Get conversations for this contact
        conversations_result = supabase.client.table('conversations')\
            .select('id, last_message_at, messages')\
            .eq('contact_id', contact_id)\
            .execute()
        
        total_messages = 0
        last_activity = None
        
        if conversations_result.data:
            # Count messages in all conversations for this contact
            for conv in conversations_result.data:
                messages = conv.get('messages', [])
                total_messages += len(messages)
            
            # Get most recent activity
            last_activities = [conv['last_message_at'] for conv in conversations_result.data if conv['last_message_at']]
            if last_activities:
                last_activity = max(last_activities)
        
        stats = {
            'total_messages': total_messages,
            'last_activity': last_activity,
            'avg_response_time': '2 hours'  # Placeholder
        }
        
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"Error getting user stats: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve user stats'
        }), 500


@api_bp.route('/crm/user/<user_id>/activity', methods=['GET'])
def get_crm_user_activity(user_id):
    """Get activity history for a specific user."""
    try:
        supabase = get_supabase_manager()
        
        if not supabase.is_connected():
            return jsonify({
                'status': 'error',
                'message': 'Database not connected'
            }), 503
        
        # Get activities for this contact (if activities table exists)
        try:
            activities_result = supabase.client.table('activities')\
                .select('*')\
                .eq('contact_id', user_id)\
                .order('created_at', desc=True)\
                .limit(20)\
                .execute()
            
            activities = []
            for activity in activities_result.data or []:
                activities.append({
                    'date': activity['created_at'],
                    'description': f"{activity.get('activity_type', 'Activity')}: {activity.get('title', 'No title')}"
                })
        except Exception:
            # If activities table doesn't exist, get conversation history instead
            conversations_result = supabase.client.table('conversations')\
                .select('messages, created_at, last_message_at')\
                .eq('contact_id', user_id)\
                .order('last_message_at', desc=True)\
                .limit(5)\
                .execute()
            
            activities = []
            for conv in conversations_result.data or []:
                messages = conv.get('messages', [])
                if messages:
                    last_message = messages[-1]
                    activities.append({
                        'date': conv['last_message_at'],
                        'description': f"WhatsApp: {last_message.get('content', 'Message')[:50]}..."
                    })
                else:
                    activities.append({
                        'date': conv['created_at'],
                        'description': 'Conversation started'
                    })
        
        return jsonify(activities), 200
        
    except Exception as e:
        logger.error(f"Error getting user activity: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve user activity'
        }), 500


@api_bp.route('/crm/contact/<contact_id>', methods=['PUT'])
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


@api_bp.route('/crm/deals', methods=['GET'])
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


@api_bp.route('/crm/deals', methods=['POST'])
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


@api_bp.route('/crm/deal/<deal_id>', methods=['PUT'])
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


@api_bp.route('/crm/tasks', methods=['GET'])
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


@api_bp.route('/crm/tasks', methods=['POST'])
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


@api_bp.route('/crm/task/<task_id>/complete', methods=['POST'])
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


@api_bp.route('/crm/task/<task_id>', methods=['DELETE'])
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


@api_bp.route('/crm/contact/<contact_id>/activities', methods=['GET'])
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


@api_bp.route('/crm/activity', methods=['POST'])
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


@api_bp.route('/crm/lead-score/<contact_id>', methods=['POST'])
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
# SYSTEM API ENDPOINTS
# ============================================================================

@api_bp.route('/customer-context/<phone_number>', methods=['GET'])
def get_customer_context(phone_number):
    """Get customer context for AI conversations (for testing/debugging)."""
    try:
        supabase = get_supabase_manager()
        
        if not supabase.is_connected():
            return jsonify({
                'status': 'error',
                'message': 'Database not connected'
            }), 503
        
        # Add WhatsApp format if not present
        if not phone_number.endswith('@s.whatsapp.net') and not phone_number.endswith('_s_whatsapp_net'):
            phone_number = f"{phone_number}@s.whatsapp.net"
        
        customer_context = supabase.get_customer_context_by_phone(phone_number)
        
        if customer_context:
            return jsonify({
                'status': 'success',
                'data': customer_context
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Customer context not found'
            }), 404
            
    except Exception as e:
        logger.error(f"Error getting customer context: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500


@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'success',
        'message': 'API is healthy',
        'timestamp': datetime.now(timezone.utc).isoformat()
    }), 200

# ============================================================================
# WASENDER CONTACT SYNC ENDPOINTS
# ============================================================================

@api_bp.route('/sync/wasender-contacts', methods=['POST'])
def sync_wasender_contacts():
    """Sync all contacts from WASender API to local database."""
    try:
        if not wasender_contact_service.is_configured():
            return jsonify({
                'status': 'error',
                'message': 'WASender API not configured'
            }), 503
        
        # Trigger contact sync
        stats = wasender_contact_service.sync_all_contacts()
        
        if 'error' in stats:
            return jsonify({
                'status': 'error',
                'message': stats['error']
            }), 500
        
        return jsonify({
            'status': 'success',
            'message': 'Contact sync completed',
            'stats': stats
        }), 200
        
    except Exception as e:
        logger.error(f"Error syncing WASender contacts: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Failed to sync contacts'
        }), 500


@api_bp.route('/sync/wasender-contact/<phone_number>', methods=['POST'])
def sync_single_wasender_contact(phone_number):
    """Sync a single contact from WASender API."""
    try:
        if not wasender_contact_service.is_configured():
            return jsonify({
                'status': 'error',
                'message': 'WASender API not configured'
            }), 503
        
        # Sync single contact
        contact_info = wasender_contact_service.sync_single_contact(phone_number)
        
        if contact_info:
            return jsonify({
                'status': 'success',
                'message': f'Contact {phone_number} synced successfully',
                'contact': contact_info
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': f'Contact {phone_number} not found or failed to sync'
            }), 404
        
    except Exception as e:
        logger.error(f"Error syncing single contact {phone_number}: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Failed to sync contact'
        }), 500


@api_bp.route('/sync/conversation-contacts', methods=['POST'])
def sync_conversation_contacts():
    """Sync contacts for active conversations."""
    try:
        if not wasender_contact_service.is_configured():
            return jsonify({
                'status': 'error',
                'message': 'WASender API not configured'
            }), 503
        
        # Get conversation IDs from request (optional)
        data = request.get_json() or {}
        conversation_ids = data.get('conversation_ids')
        
        # Sync conversation contacts
        stats = wasender_contact_service.sync_contacts_for_conversations(conversation_ids)
        
        if 'error' in stats:
            return jsonify({
                'status': 'error',
                'message': stats['error']
            }), 500
        
        return jsonify({
            'status': 'success',
            'message': 'Conversation contact sync completed',
            'stats': stats
        }), 200
        
    except Exception as e:
        logger.error(f"Error syncing conversation contacts: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Failed to sync conversation contacts'
        }), 500


@api_bp.route('/sync/status', methods=['GET'])
def get_sync_status():
    """Get WASender sync configuration status."""
    try:
        return jsonify({
            'status': 'success',
            'data': {
                'wasender_configured': wasender_contact_service.is_configured(),
                'sync_available': wasender_contact_service.is_configured(),
                'last_sync': 'Not implemented yet'  # TODO: Add last sync tracking
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting sync status: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Failed to get sync status'
        }), 500


# ============================================================================
# LEAD ANALYSIS API ENDPOINTS
# ============================================================================

@api_bp.route('/debug-lead/<phone_number>', methods=['GET'])
def debug_lead_analysis(phone_number):
    """Debug lead analysis for a phone number."""
    try:
        supabase = get_supabase_manager()
        
        if not supabase.is_connected():
            return jsonify({
                'status': 'error',
                'message': 'Database not connected'
            }), 503
        
        # Normalize phone number
        clean_phone = phone_number.replace('_s_whatsapp_net', '').replace('@s.whatsapp.net', '')
        
        # Get conversation data
        conversations = supabase.client.table('conversations')\
            .select('*, contacts!inner(phone_number, name, email, company, position, lead_status, lead_score)')\
            .ilike('contacts.phone_number', f'%{clean_phone}%')\
            .order('last_message_at', desc=True)\
            .execute()
        
        return jsonify({
            'status': 'success',
            'phone_searched': clean_phone,
            'conversations_found': len(conversations.data) if conversations.data else 0,
            'first_conversation': conversations.data[0] if conversations.data else None
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'phone_searched': phone_number
        }), 500

@api_bp.route('/lead-analysis/<phone_number>', methods=['GET'])
def get_lead_analysis(phone_number):
    """Get comprehensive lead analysis for a phone number."""
    try:
        from src.services.lead_qualification_service import analyze_lead_qualification_ai
        from src.services.analytics_service import get_analytics_service
        
        supabase = get_supabase_manager()
        
        if not supabase.is_connected():
            return jsonify({
                'status': 'error',
                'message': 'Database not connected'
            }), 503
        
        # Normalize phone number
        clean_phone = phone_number.replace('_s_whatsapp_net', '').replace('@s.whatsapp.net', '')
        
        # Get conversation data
        conversations = supabase.client.table('conversations')\
            .select('*, contacts!inner(phone_number, name, email, company, position, lead_status, lead_score)')\
            .ilike('contacts.phone_number', f'%{clean_phone}%')\
            .order('last_message_at', desc=True)\
            .execute()
        
        if not conversations.data:
            return jsonify({
                'status': 'error',
                'message': 'No conversation found for this phone number'
            }), 404
        
        conversation = conversations.data[0]
        contact = conversation['contacts']
        
        # Get messages for this conversation separately if needed
        messages = conversation.get('messages', [])
        if not messages:
            # Try to get messages from a separate query
            try:
                messages_data = supabase.client.table('messages')\
                    .select('*')\
                    .eq('conversation_id', conversation.get('id'))\
                    .order('created_at', desc=False)\
                    .execute()
                messages = messages_data.data or []
            except Exception as msg_error:
                logger.warning(f"Could not fetch messages: {msg_error}")
                messages = []
        
        # Get lead qualification logs
        lead_logs = supabase.client.table('lead_qualification_log')\
            .select('*')\
            .order('created_at', desc=True)\
            .limit(10)\
            .execute()
        
        # Analyze conversation for lead qualification
        conversation_history = []
        for msg in messages[-10:]:  # Last 10 messages for context
            conversation_history.append({
                'role': msg.get('role', 'user'),
                'content': msg.get('content', '')
            })
        
        # Get the latest message for analysis
        latest_message = messages[-1].get('content', '') if messages else ""
        
        # Run AI analysis with fallback
        try:
            is_qualified, confidence, reason, metadata = analyze_lead_qualification_ai(
                latest_message, conversation_history
            )
        except Exception as ai_error:
            logger.warning(f"AI analysis failed, using fallback: {ai_error}")
            # Fallback values
            is_qualified = False
            confidence = 0.5
            reason = "Unable to analyze conversation"
            metadata = {
                'lead_score': 50,
                'business_indicators': [],
                'buying_signals': [],
                'recommended_action': 'review_manually'
            }
        
        # Calculate conversation metrics
        total_messages = len(messages)
        user_messages = [m for m in messages if m.get('role') == 'user']
        bot_messages = [m for m in messages if m.get('role') == 'assistant']
        
        # Calculate engagement level
        engagement_level = min(100, (total_messages * 10) + (confidence * 100))
        
        # Extract topics from conversation
        topics = []
        all_text = ' '.join([m.get('content', '') for m in user_messages])
        business_keywords = ['business', 'company', 'automation', 'whatsapp', 'api', 'integration', 'pricing', 'service']
        for keyword in business_keywords:
            if keyword.lower() in all_text.lower():
                topics.append(keyword.title())
        
        # Calculate scores
        overall_score = metadata.get('lead_score', 0)
        business_intent_score = min(100, confidence * 100)
        
        # Determine qualification status
        if overall_score >= 80:
            qualification_status = 'qualified'
        elif overall_score >= 50:
            qualification_status = 'potential'
        else:
            qualification_status = 'unqualified'
        
        # Build timeline from lead qualification logs
        timeline = []
        for log in (lead_logs.data or []):
            timeline.append({
                'date': log.get('created_at', ''),
                'event': f"Lead qualification: {log.get('reason', 'Unknown')}",
                'type': 'qualification',
                'score': log.get('lead_score', 0)
            })
        
        # Add conversation milestones
        if len(messages) >= 1:
            timeline.append({
                'date': conversation.get('created_at', ''),
                'event': 'Initial conversation started',
                'type': 'message'
            })
        
        # Sort timeline by date
        timeline.sort(key=lambda x: x['date'], reverse=True)
        
        # Generate recommendations based on lead score
        if overall_score >= 80:
            immediate = ["Send detailed pricing proposal", "Schedule technical demo", "Provide ROI calculator"]
            follow_up = ["Share case studies from similar companies", "Arrange team presentation"]
            long_term = ["Quarterly business reviews", "Expansion opportunities"]
        elif overall_score >= 50:
            immediate = ["Nurture with valuable content", "Understand specific needs", "Provide general information"]
            follow_up = ["Regular check-ins", "Educational content sharing"]
            long_term = ["Monitor for buying signals", "Relationship building"]
        else:
            immediate = ["Provide basic information", "Understand their challenges"]
            follow_up = ["Educational content", "Stay in touch"]
            long_term = ["Long-term nurturing", "Monitor for future interest"]
        
        # Build response
        analysis_data = {
            'phoneNumber': clean_phone,
            'contactName': contact.get('name') or clean_phone,
            'overallScore': overall_score,
            'qualificationStatus': qualification_status,
            'businessIntent': {
                'score': business_intent_score,
                'indicators': metadata.get('business_indicators', []),
                'confidence': int(confidence * 100)
            },
            'buyingSignals': {
                'score': min(100, len(metadata.get('buying_signals', [])) * 20),
                'signals': [
                    {
                        'type': signal,
                        'strength': 'high' if confidence > 0.8 else 'medium' if confidence > 0.5 else 'low',
                        'message': f"Detected: {signal}",
                        'timestamp': conversation['last_message_at']
                    }
                    for signal in metadata.get('buying_signals', [])
                ]
            },
            'conversationAnalysis': {
                'totalMessages': total_messages,
                'avgResponseTime': 2.5,  # Placeholder
                'engagementLevel': int(engagement_level),
                'topics': topics or ['General Inquiry'],
                'sentiment': 'positive' if confidence > 0.6 else 'neutral'
            },
            'identifiedNeeds': {
                'primary': ['Customer service automation', 'Lead qualification system'] if is_qualified else ['General information'],
                'secondary': ['Analytics and reporting', 'Multi-agent support'] if is_qualified else [],
                'painPoints': ['Manual processes', 'Response time issues'] if is_qualified else []
            },
            'timeline': timeline[:10],  # Limit to 10 most recent events
            'recommendations': {
                'immediate': immediate,
                'followUp': follow_up,
                'longTerm': long_term
            },
            'predictiveInsights': {
                'conversionProbability': min(100, overall_score + 10),
                'bestContactTime': '10:00 AM - 12:00 PM',
                'recommendedApproach': metadata.get('recommended_action', 'nurture').replace('_', ' ').title(),
                'estimatedValue': 25000 if is_qualified else 5000
            }
        }
        
        return jsonify({
            'status': 'success',
            'data': analysis_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting lead analysis: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve lead analysis'
        }), 500


@api_bp.route('/conversations/lead-summary', methods=['GET'])
def get_lead_qualification_summary():
    """Get lead qualification summary for all conversations."""
    try:
        supabase = get_supabase_manager()
        
        if not supabase.is_connected():
            return jsonify({
                'status': 'error', 
                'message': 'Database not connected'
            }), 503
        
        # Get recent conversations with lead qualification data
        conversations = supabase.client.table('conversations')\
            .select('id, last_message_at, messages, contacts!inner(phone_number, name, lead_status, lead_score)')\
            .order('last_message_at', desc=True)\
            .limit(50)\
            .execute()
        
        summaries = []
        for conv in conversations.data:
            contact = conv['contacts']
            messages = conv.get('messages', [])
            
            # Clean phone number
            clean_phone = contact['phone_number'].replace('_s_whatsapp_net', '').replace('@s.whatsapp.net', '')
            
            # Basic lead qualification based on message count and lead score
            message_count = len(messages)
            lead_score = contact.get('lead_score', 0)
            
            is_qualified = lead_score >= 70 and message_count >= 5
            has_business_intent = lead_score >= 50 or message_count >= 3
            
            summaries.append({
                'phoneNumber': clean_phone,
                'contactName': contact.get('name') or clean_phone,
                'messageCount': message_count,
                'lastMessageAt': conv['last_message_at'],
                'leadScore': lead_score,
                'leadStatus': contact.get('lead_status', 'new'),
                'isQualifiedLead': is_qualified,
                'hasBusinessIntent': has_business_intent
            })
        
        return jsonify({
            'status': 'success',
            'data': summaries
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting lead qualification summary: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve lead qualification summary'
        }), 500


@api_bp.route('/analytics/lead-qualification', methods=['GET'])
def get_lead_qualification_analytics():
    """Get lead qualification analytics and logs."""
    try:
        supabase = get_supabase_manager()
        
        if not supabase.is_connected():
            return jsonify({
                'status': 'error',
                'message': 'Database not connected'
            }), 503
        
        # Get query parameters
        min_score = float(request.args.get('min_score', 0))
        limit = int(request.args.get('limit', 100))
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Build query for lead qualification logs
        query = supabase.client.table('lead_qualification_log')\
            .select('*')\
            .gte('lead_score', min_score)
        
        if start_date:
            query = query.gte('created_at', start_date)
        if end_date:
            query = query.lte('created_at', end_date)
        
        logs = query.order('created_at', desc=True)\
            .limit(limit)\
            .execute()
        
        # Calculate analytics
        total_analyzed = len(logs.data) if logs.data else 0
        qualified_leads = len([log for log in (logs.data or []) if log.get('final_decision', False)])
        
        qualification_rate = (qualified_leads / total_analyzed * 100) if total_analyzed > 0 else 0
        
        # Group by lead quality
        quality_distribution = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'NOT_QUALIFIED': 0}
        for log in (logs.data or []):
            quality = log.get('lead_quality', 'NOT_QUALIFIED')
            quality_distribution[quality] = quality_distribution.get(quality, 0) + 1
        
        return jsonify({
            'status': 'success',
            'data': {
                'analytics': {
                    'totalAnalyzed': total_analyzed,
                    'qualifiedLeads': qualified_leads,
                    'qualificationRate': round(qualification_rate, 1),
                    'qualityDistribution': quality_distribution
                },
                'logs': logs.data or [],
                'filters': {
                    'minScore': min_score,
                    'limit': limit,
                    'startDate': start_date,
                    'endDate': end_date
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting lead qualification analytics: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve lead qualification analytics'
        }), 500


# ============================================================================
# HANDOVER RESCUE ENDPOINTS  
# ============================================================================

@api_bp.route('/handover/rescue', methods=['POST'])
def manual_handover_rescue():
    """Manually trigger emergency handover rescue operation."""
    try:
        from src.services.handover_management_service import get_handover_management_service
        
        # Get handover service
        handover_service = get_handover_management_service()
        
        # Run rescue operation
        results = handover_service.rescue_abandoned_customers()
        
        # Return results
        return jsonify({
            'status': 'success',
            'data': {
                'rescued_customers': results.get('rescued', 0),
                'notified_customers': results.get('notified', 0),
                'errors': results.get('errors', 0),
                'message': f"Rescue complete: {results.get('rescued', 0)} rescued, {results.get('notified', 0)} notified"
            }
        })
        
    except Exception as e:
        logger.error(f"Manual handover rescue failed: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Handover rescue operation failed: {str(e)}'
        }), 500

@api_bp.route('/handover/status', methods=['GET'])
def get_handover_status():
    """Get current handover queue status and statistics."""
    try:
        from src.services.handover_management_service import get_handover_management_service
        
        # Get handover service
        handover_service = get_handover_management_service()
        
        # Get statistics
        stats = handover_service.get_handover_statistics()
        
        if 'error' in stats:
            return jsonify({
                'status': 'error',
                'message': stats['error']
            }), 500
        
        return jsonify({
            'status': 'success',
            'data': {
                'queue_status': stats,
                'message': f"Currently {stats.get('total_waiting', 0)} customers waiting for human support"
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to get handover status: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to retrieve handover status: {str(e)}'
        }), 500