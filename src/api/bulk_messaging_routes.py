"""
Bulk Messaging API Routes
========================
Handles CSV contact import and bulk message sending endpoints.

Author: Rian Infotech
Version: 1.0
"""

import logging
import csv
import io
import re
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple
from flask import Blueprint, request, jsonify

# Import core functionality
from src.core.supabase_client import get_supabase_manager
from src.utils.bulk_messaging import (
    send_bulk_message_individual, 
    send_bulk_message_with_retry,
    bulk_manager,
    validate_phone_number,
    clean_phone_number
)
from src.handlers.whatsapp_handler import send_complete_message

# Configure logging
logger = logging.getLogger(__name__)

# Create Blueprint for bulk messaging routes
bulk_messaging_bp = Blueprint('bulk_messaging', __name__)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def validate_csv_file(file) -> Tuple[bool, str]:
    """
    Validate uploaded CSV file.
    
    Args:
        file: Flask file object
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not file:
        return False, "No file provided"
    
    if not file.filename:
        return False, "No filename provided"
    
    if not file.filename.lower().endswith('.csv'):
        return False, "File must be a CSV file"
    
    # Check file size (max 5MB)
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)  # Reset to beginning
    
    if file_size > 5 * 1024 * 1024:  # 5MB
        return False, "File size must be less than 5MB"
    
    return True, ""

def parse_csv_contacts(file_content: str) -> Tuple[List[Dict], List[str]]:
    """
    Parse CSV content and extract contacts.
    
    Args:
        file_content: CSV file content as string
        
    Returns:
        Tuple of (valid_contacts, errors)
    """
    valid_contacts = []
    errors = []
    
    try:
        # Parse CSV
        csv_reader = csv.DictReader(io.StringIO(file_content))
        
        # Check if CSV has headers
        if not csv_reader.fieldnames:
            errors.append("CSV file appears to be empty or has no headers")
            return valid_contacts, errors
        
        # Common phone number field names
        phone_fields = ['phone', 'phone_number', 'mobile', 'whatsapp', 'number', 'contact']
        name_fields = ['name', 'full_name', 'contact_name', 'customer_name']
        email_fields = ['email', 'email_address', 'mail']
        company_fields = ['company', 'organization', 'business']
        
        # Find the phone field
        phone_field = None
        for field in csv_reader.fieldnames:
            if field.lower() in phone_fields:
                phone_field = field
                break
        
        if not phone_field:
            errors.append(f"No phone number column found. Expected one of: {', '.join(phone_fields)}")
            return valid_contacts, errors
        
        # Find other fields
        name_field = None
        email_field = None
        company_field = None
        
        for field in csv_reader.fieldnames:
            field_lower = field.lower()
            if not name_field and field_lower in name_fields:
                name_field = field
            elif not email_field and field_lower in email_fields:
                email_field = field
            elif not company_field and field_lower in company_fields:
                company_field = field
        
        # Process each row
        row_number = 1
        for row in csv_reader:
            row_number += 1
            
            # Get phone number
            phone = row.get(phone_field, '').strip()
            if not phone:
                errors.append(f"Row {row_number}: Phone number is empty")
                continue
            
            # Clean and validate phone number
            cleaned_phone = clean_phone_number(phone)
            if not validate_phone_number(cleaned_phone):
                errors.append(f"Row {row_number}: Invalid phone number format: {phone}")
                continue
            
            # Extract other fields
            name = row.get(name_field, '').strip() if name_field else ''
            email = row.get(email_field, '').strip() if email_field else ''
            company = row.get(company_field, '').strip() if company_field else ''
            
            # Validate email if provided
            if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                errors.append(f"Row {row_number}: Invalid email format: {email}")
                email = ''  # Clear invalid email
            
            # Create contact object
            contact = {
                'phone_number': cleaned_phone,
                'name': name or None,
                'email': email or None,
                'company': company or None,
                'row_number': row_number
            }
            
            # Check for duplicates in current batch
            if any(c['phone_number'] == cleaned_phone for c in valid_contacts):
                errors.append(f"Row {row_number}: Duplicate phone number: {phone}")
                continue
            
            valid_contacts.append(contact)
        
        logger.info(f"Parsed CSV: {len(valid_contacts)} valid contacts, {len(errors)} errors")
        
    except Exception as e:
        errors.append(f"Error parsing CSV: {str(e)}")
        logger.error(f"CSV parsing error: {e}")
    
    return valid_contacts, errors

def import_contacts_to_database(contacts: List[Dict]) -> Tuple[List[Dict], List[str]]:
    """
    Import contacts to Supabase database.
    
    Args:
        contacts: List of contact dictionaries
        
    Returns:
        Tuple of (imported_contacts, errors)
    """
    supabase = get_supabase_manager()
    
    if not supabase.is_connected():
        return [], ["Database not connected"]
    
    imported_contacts = []
    errors = []
    
    for contact in contacts:
        try:
            # Try to get or create contact
            db_contact = supabase.get_or_create_contact(
                phone_number=contact['phone_number'],
                name=contact['name'],
                email=contact['email']
            )
            
            if db_contact:
                # Update additional fields if provided
                if contact.get('company'):
                    supabase.update_contact(db_contact['id'], company=contact['company'])
                
                imported_contacts.append({
                    'id': db_contact['id'],
                    'phone_number': contact['phone_number'],
                    'name': contact['name'] or contact['phone_number'],
                    'email': contact['email'],
                    'company': contact['company'],
                    'status': 'imported'
                })
            else:
                errors.append(f"Failed to import contact: {contact['phone_number']}")
                
        except Exception as e:
            errors.append(f"Error importing {contact['phone_number']}: {str(e)}")
            logger.error(f"Contact import error: {e}")
    
    return imported_contacts, errors

# ============================================================================
# API ENDPOINTS
# ============================================================================

@bulk_messaging_bp.route('/bulk-send/import-contacts', methods=['POST'])
def import_contacts():
    """
    Import contacts from CSV file.
    
    Expected form data:
    - file: CSV file with contact information
    
    Returns:
        JSON response with imported contacts and any errors
    """
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'No file provided'
            }), 400
        
        file = request.files['file']
        
        # Validate file
        is_valid, error_message = validate_csv_file(file)
        if not is_valid:
            return jsonify({
                'status': 'error',
                'message': error_message
            }), 400
        
        # Read file content
        try:
            file_content = file.read().decode('utf-8')
        except UnicodeDecodeError:
            return jsonify({
                'status': 'error',
                'message': 'File must be UTF-8 encoded'
            }), 400
        
        # Parse CSV
        valid_contacts, parse_errors = parse_csv_contacts(file_content)
        
        if not valid_contacts and parse_errors:
            return jsonify({
                'status': 'error',
                'message': 'No valid contacts found in CSV',
                'errors': parse_errors
            }), 400
        
        # Import to database
        imported_contacts, import_errors = import_contacts_to_database(valid_contacts)
        
        # Prepare response
        response = {
            'status': 'success',
            'message': f'Imported {len(imported_contacts)} contacts',
            'data': {
                'imported_contacts': imported_contacts,
                'total_processed': len(valid_contacts),
                'successfully_imported': len(imported_contacts),
                'errors': parse_errors + import_errors
            }
        }
        
        # Set status based on results
        if import_errors and not imported_contacts:
            response['status'] = 'error'
            response['message'] = 'Failed to import any contacts'
            return jsonify(response), 500
        elif import_errors:
            response['status'] = 'partial_success'
            response['message'] = f'Imported {len(imported_contacts)} contacts with {len(import_errors)} errors'
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error in import_contacts: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Internal server error during import'
        }), 500

@bulk_messaging_bp.route('/bulk-send/send', methods=['POST'])
def send_bulk_message():
    """
    Send bulk messages to a list of contacts.
    
    Expected JSON body:
    {
        "message": "Message content",
        "contacts": ["phone1", "phone2", ...] or [{"phone_number": "...", "name": "..."}, ...],
        "campaign_name": "Optional campaign name",
        "with_retry": true/false (default: true)
    }
    
    Returns:
        JSON response with job details and results
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No JSON data provided'
            }), 400
        
        # Validate required fields
        message = data.get('message', '').strip()
        contacts = data.get('contacts', [])
        
        if not message:
            return jsonify({
                'status': 'error',
                'message': 'Message content is required'
            }), 400
        
        if not contacts or not isinstance(contacts, list):
            return jsonify({
                'status': 'error',
                'message': 'Contacts list is required'
            }), 400
        
        # Process contacts - handle both string and object formats
        phone_numbers = []
        for contact in contacts:
            if isinstance(contact, str):
                phone_numbers.append(contact)
            elif isinstance(contact, dict) and contact.get('phone_number'):
                phone_numbers.append(contact['phone_number'])
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid contact format'
                }), 400
        
        if not phone_numbers:
            return jsonify({
                'status': 'error',
                'message': 'No valid phone numbers found'
            }), 400
        
        # Optional parameters
        campaign_name = data.get('campaign_name', f'Bulk Send {datetime.now().strftime("%Y-%m-%d %H:%M")}')
        with_retry = data.get('with_retry', True)
        
        # Create campaign in database
        supabase = get_supabase_manager()
        campaign_id = None
        
        if supabase.is_connected():
            campaign_id = supabase.create_bulk_campaign(
                name=campaign_name,
                message_content=message,
                total_contacts=len(phone_numbers)
            )
            
            if campaign_id:
                supabase.update_campaign_status(campaign_id, 'running')
        
        # Send messages
        if with_retry:
            bulk_job = send_bulk_message_with_retry(
                contacts=phone_numbers,
                message=message,
                send_function=send_complete_message
            )
        else:
            bulk_job = send_bulk_message_individual(
                contacts=phone_numbers,
                message=message,
                send_function=send_complete_message
            )
        
        # Update campaign status
        if campaign_id and supabase.is_connected():
            supabase.update_campaign_status(
                campaign_id=campaign_id,
                status='completed',
                successful_sends=bulk_job.successful_sends,
                failed_sends=bulk_job.failed_sends
            )
            
            # Log individual results
            for result in bulk_job.results:
                supabase.log_message_result(
                    campaign_id=campaign_id,
                    phone_number=result.contact,
                    success=result.success,
                    error_message=result.error_message if not result.success else None
                )
        
        # Prepare response
        response = {
            'status': 'success',
            'message': f'Bulk send completed: {bulk_job.successful_sends} sent, {bulk_job.failed_sends} failed',
            'data': {
                'job_id': bulk_job.job_id,
                'campaign_id': campaign_id,
                'total_contacts': bulk_job.total_contacts,
                'successful_sends': bulk_job.successful_sends,
                'failed_sends': bulk_job.failed_sends,
                'started_at': bulk_job.started_at,
                'completed_at': bulk_job.completed_at,
                'results': [
                    {
                        'contact': result.contact,
                        'success': result.success,
                        'error_message': result.error_message,
                        'timestamp': result.timestamp
                    }
                    for result in bulk_job.results
                ]
            }
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error in send_bulk_message: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Internal server error during bulk send'
        }), 500

@bulk_messaging_bp.route('/bulk-send/status/<job_id>', methods=['GET'])
def get_bulk_job_status(job_id):
    """
    Get status of a bulk messaging job.
    
    Args:
        job_id: Job ID to check
        
    Returns:
        JSON response with job status
    """
    try:
        status = bulk_manager.get_job_status(job_id)
        
        if not status:
            return jsonify({
                'status': 'error',
                'message': 'Job not found'
            }), 404
        
        return jsonify({
            'status': 'success',
            'data': status
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting job status: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500

@bulk_messaging_bp.route('/bulk-send/jobs', methods=['GET'])
def get_all_bulk_jobs():
    """
    Get status of all bulk messaging jobs.
    
    Returns:
        JSON response with all job statuses
    """
    try:
        jobs = bulk_manager.get_all_jobs()
        
        return jsonify({
            'status': 'success',
            'data': jobs
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting all jobs: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500 

@bulk_messaging_bp.route('/bulk-send/format-message', methods=['POST'])
def format_message_with_ai():
    """
    Format and improve a message using AI.
    
    Expected JSON body:
    {
        "message": "Raw message text to be formatted",
        "tone": "professional" | "friendly" | "casual" | "urgent" (optional),
        "purpose": "marketing" | "support" | "announcement" | "follow-up" (optional)
    }
    
    Returns:
        JSON response with formatted message
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No JSON data provided'
            }), 400
        
        # Validate required fields
        original_message = data.get('message', '').strip()
        tone = data.get('tone', 'professional').lower()
        purpose = data.get('purpose', 'marketing').lower()
        
        if not original_message:
            return jsonify({
                'status': 'error',
                'message': 'Message content is required'
            }), 400
        
        # Validate tone options
        valid_tones = ['professional', 'friendly', 'casual', 'urgent']
        if tone not in valid_tones:
            tone = 'professional'
        
        # Validate purpose options
        valid_purposes = ['marketing', 'support', 'announcement', 'follow-up']
        if purpose not in valid_purposes:
            purpose = 'marketing'
        
        # Create AI prompt for message formatting
        formatting_prompt = f"""You are an expert copywriter specializing in WhatsApp business messaging. Your task is to improve and format the following message for bulk sending.

ORIGINAL MESSAGE:
"{original_message}"

FORMATTING REQUIREMENTS:
- Tone: {tone.title()}
- Purpose: {purpose.title()}
- Platform: WhatsApp Business
- Format: Plain text (no markdown)
- Length: Optimize for readability and engagement
- Keep it concise but impactful

GUIDELINES:
1. Make the message clear and engaging
2. Use appropriate emojis sparingly (1-3 max)
3. Ensure proper grammar and spelling
4. Structure for easy reading on mobile
5. Include a clear call-to-action if appropriate
6. Maintain the core message intent
7. Make it suitable for bulk sending to multiple contacts

Please provide ONLY the improved message text, nothing else."""

        # Import the AI handler function
        from src.handlers.ai_handler import generate_ai_response
        
        # Generate formatted message using existing AI infrastructure
        formatted_message = generate_ai_response(formatting_prompt)
        
        if not formatted_message or "trouble connecting" in formatted_message.lower():
            return jsonify({
                'status': 'error',
                'message': 'AI formatting service is currently unavailable'
            }), 503
        
        # Clean up the response (remove any extra formatting)
        formatted_message = formatted_message.strip()
        
        # Remove quotes if AI wrapped the response
        if formatted_message.startswith('"') and formatted_message.endswith('"'):
            formatted_message = formatted_message[1:-1]
        
        return jsonify({
            'status': 'success',
            'data': {
                'original_message': original_message,
                'formatted_message': formatted_message,
                'tone': tone,
                'purpose': purpose,
                'character_count': len(formatted_message),
                'improvement_applied': len(formatted_message) != len(original_message)
            }
        })
        
    except Exception as e:
        logger.error(f"Error formatting message with AI: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Failed to format message'
        }), 500 