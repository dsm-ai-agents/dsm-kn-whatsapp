"""
Flask API Routes for Group Messaging Module
===========================================
Provides REST API endpoints for group messaging functionality.
"""

import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from typing import Dict, Any

from ..services.group_service import GroupService
from ..services.database_service import DatabaseService
from ..services.scheduler_service import SchedulerService
from ..config.settings import GroupMessagingConfig
from ..models.group import Group, GroupMessage
from ..models.schedule import ScheduledMessage, ScheduleStatus, RecurringPattern
from ..core.exceptions import GroupMessagingError, APIError, ValidationError

logger = logging.getLogger(__name__)


def create_group_messaging_blueprint(supabase_client, wasender_api_token: str) -> Blueprint:
    """
    Create Flask blueprint for group messaging routes.
    
    Args:
        supabase_client: Existing Supabase client
        wasender_api_token: Wasender API token
        
    Returns:
        Flask Blueprint with all group messaging routes
    """
    
    # Create blueprint
    bp = Blueprint('group_messaging', __name__, url_prefix='/api/group-messaging')
    
    # Initialize services
    config = GroupMessagingConfig(whatsapp_api_token=wasender_api_token)
    group_service = GroupService(config)
    db_service = DatabaseService(supabase_client)
    scheduler_service = SchedulerService(group_service, db_service)
    
    def handle_api_error(func):
        """Decorator to handle API errors consistently."""
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ValidationError as e:
                logger.warning(f"Validation error in {func.__name__}: {e}")
                return jsonify({
                    "success": False,
                    "error": "validation_error",
                    "message": str(e)
                }), 400
            except APIError as e:
                logger.error(f"API error in {func.__name__}: {e}")
                return jsonify({
                    "success": False,
                    "error": "api_error",
                    "message": str(e)
                }), 500
            except GroupMessagingError as e:
                logger.error(f"Group messaging error in {func.__name__}: {e}")
                return jsonify({
                    "success": False,
                    "error": "group_messaging_error",
                    "message": str(e)
                }), 500
            except Exception as e:
                logger.error(f"Unexpected error in {func.__name__}: {e}")
                return jsonify({
                    "success": False,
                    "error": "internal_error",
                    "message": "An unexpected error occurred"
                }), 500
        wrapper.__name__ = func.__name__
        return wrapper
    
    # ===== GROUP MANAGEMENT ROUTES =====
    
    @bp.route('/groups', methods=['GET'])
    @handle_api_error
    def get_groups():
        """Get all WhatsApp groups."""
        try:
            # Sync groups from Wasender API
            api_groups = group_service.get_all_groups()
            
            # Save/update groups in database
            db_groups = []
            for group in api_groups:
                saved_group = db_service.save_group(group)
                db_groups.append({
                    "id": saved_group.id,
                    "group_jid": saved_group.group_jid,
                    "name": saved_group.name,
                    "img_url": saved_group.img_url,
                    "status": saved_group.status,
                    "member_count": saved_group.member_count,
                    "created_at": saved_group.created_at,
                    "updated_at": saved_group.updated_at
                })
            
            return jsonify({
                "success": True,
                "data": {
                    "groups": db_groups,
                    "total": len(db_groups)
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting groups: {e}")
            raise
    
    @bp.route('/groups', methods=['POST'])
    @handle_api_error
    def create_group():
        """Create a new WhatsApp group."""
        data = request.get_json()
        
        if not data:
            raise ValidationError("Request body is required")
        
        name = data.get('name', '').strip()
        participants = data.get('participants', [])
        
        if not name:
            raise ValidationError("Group name is required")
        
        if not participants or len(participants) == 0:
            raise ValidationError("At least one participant is required")
        
        # Create group via API
        group = group_service.create_group(name, participants)
        
        # Save to database
        saved_group = db_service.save_group(group)
        
        return jsonify({
            "success": True,
            "data": {
                "id": saved_group.id,
                "group_jid": saved_group.group_jid,
                "name": saved_group.name,
                "member_count": saved_group.member_count,
                "created_at": saved_group.created_at
            }
        }), 201
    
    # ===== GROUP MESSAGING ROUTES =====
    
    @bp.route('/groups/<group_jid>/send-message', methods=['POST'])
    @handle_api_error
    def send_group_message(group_jid: str):
        """Send a message to a specific group."""
        data = request.get_json()
        
        if not data:
            raise ValidationError("Request body is required")
        
        message_content = data.get('message_content', '').strip()
        message_type = data.get('message_type', 'text')
        media_url = data.get('media_url')
        
        if not message_content:
            raise ValidationError("Message content is required")
        
        # Send message via API
        group_message = group_service.send_group_message(
            group_jid=group_jid,
            message_content=message_content,
            message_type=message_type,
            media_url=media_url
        )
        
        # Save to database
        saved_message = db_service.save_group_message(group_message)
        
        return jsonify({
            "success": True,
            "data": {
                "message_id": saved_message.id,
                "group_jid": saved_message.group_jid,
                "status": saved_message.status,
                "wasender_message_id": saved_message.wasender_message_id,
                "sent_at": saved_message.sent_at.isoformat() if saved_message.sent_at else None,
                "error_message": saved_message.error_message
            }
        })
    
    @bp.route('/bulk-send', methods=['POST'])
    @handle_api_error
    def send_bulk_group_messages():
        """Send the same message to multiple groups."""
        data = request.get_json()
        
        if not data:
            raise ValidationError("Request body is required")
        
        group_jids = data.get('group_jids', [])
        message_content = data.get('message_content', '').strip()
        message_type = data.get('message_type', 'text')
        media_url = data.get('media_url')
        campaign_name = data.get('campaign_name', f'Bulk Campaign {datetime.now().strftime("%Y-%m-%d %H:%M")}')
        
        if not group_jids or len(group_jids) == 0:
            raise ValidationError("At least one group JID is required")
        
        if not message_content:
            raise ValidationError("Message content is required")
        
        # Create campaign record
        campaign = db_service.create_group_campaign(
            name=campaign_name,
            message_content=message_content,
            target_groups=group_jids,
            message_type=message_type,
            media_url=media_url
        )
        
        # Send bulk messages
        results = group_service.send_bulk_group_messages(
            group_jids=group_jids,
            message_content=message_content,
            message_type=message_type,
            media_url=media_url
        )
        
        # Save results and update campaign stats
        successful_sends = 0
        failed_sends = 0
        
        for result in results:
            db_service.save_group_message(result)
            if result.status == "sent":
                successful_sends += 1
            else:
                failed_sends += 1
        
        # Update campaign statistics
        db_service.update_campaign_stats(campaign['id'], successful_sends, failed_sends)
        
        return jsonify({
            "success": True,
            "data": {
                "campaign_id": campaign['id'],
                "total_groups": len(group_jids),
                "successful_sends": successful_sends,
                "failed_sends": failed_sends,
                "results": [
                    {
                        "group_jid": r.group_jid,
                        "status": r.status,
                        "wasender_message_id": r.wasender_message_id,
                        "error_message": r.error_message
                    } for r in results
                ]
            }
        })
    
    # ===== SCHEDULING ROUTES =====
    
    @bp.route('/schedule-message', methods=['POST'])
    @handle_api_error
    def schedule_message():
        """Schedule a message for future delivery."""
        data = request.get_json()
        
        if not data:
            raise ValidationError("Request body is required")
        
        message_content = data.get('message_content', '').strip()
        target_groups = data.get('target_groups', [])
        scheduled_at_str = data.get('scheduled_at')
        message_type = data.get('message_type', 'text')
        media_url = data.get('media_url')
        recurring_pattern = data.get('recurring_pattern')
        recurring_interval = data.get('recurring_interval')
        
        if not message_content:
            raise ValidationError("Message content is required")
        
        if not target_groups or len(target_groups) == 0:
            raise ValidationError("At least one target group is required")
        
        if not scheduled_at_str:
            raise ValidationError("Scheduled time is required")
        
        try:
            scheduled_at = datetime.fromisoformat(scheduled_at_str.replace('Z', '+00:00'))
        except ValueError:
            raise ValidationError("Invalid scheduled_at format. Use ISO format (YYYY-MM-DDTHH:MM:SS)")
        
        # Handle timezone-aware datetime comparison
        current_time = datetime.utcnow()
        if scheduled_at.tzinfo is not None:
            # scheduled_at is timezone-aware, make current_time timezone-aware too
            from datetime import timezone
            current_time = current_time.replace(tzinfo=timezone.utc)
        elif current_time.tzinfo is not None:
            # current_time is timezone-aware, make scheduled_at timezone-aware
            scheduled_at = scheduled_at.replace(tzinfo=timezone.utc)
        
        if scheduled_at <= current_time:
            raise ValidationError("Scheduled time must be in the future")
        
        # Create scheduled message
        scheduled_message = ScheduledMessage(
            message_content=message_content,
            message_type=message_type,
            media_url=media_url,
            target_groups=target_groups,
            scheduled_at=scheduled_at,
            status=ScheduleStatus.PENDING,
            recurring_pattern=RecurringPattern(recurring_pattern) if recurring_pattern else None,
            recurring_interval=recurring_interval
        )
        
        # Calculate next send time for recurring messages
        if scheduled_message.recurring_pattern:
            scheduled_message.next_send_at = scheduler_service.calculate_next_send_time(
                scheduled_at, scheduled_message.recurring_pattern, recurring_interval
            )
        
        # Save to database
        saved_message = db_service.save_scheduled_message(scheduled_message)
        
        return jsonify({
            "success": True,
            "data": {
                "scheduled_message_id": saved_message.id,
                "scheduled_at": saved_message.scheduled_at.isoformat(),
                "next_send_at": saved_message.next_send_at.isoformat() if saved_message.next_send_at else None,
                "target_groups": saved_message.target_groups,
                "recurring_pattern": saved_message.recurring_pattern.value if saved_message.recurring_pattern else None,
                "status": saved_message.status.value
            }
        }), 201
    
    @bp.route('/scheduled-messages', methods=['GET'])
    @handle_api_error
    def get_scheduled_messages():
        """Get all scheduled messages."""
        status_filter = request.args.get('status')
        limit = min(int(request.args.get('limit', 100)), 200)  # Cap at 200
        
        # Get scheduled messages from database
        scheduled_messages = db_service.get_all_scheduled_messages(
            status_filter=status_filter,
            limit=limit
        )
        
        return jsonify({
            "success": True,
            "data": {
                "scheduled_messages": scheduled_messages,
                "total": len(scheduled_messages)
            }
        })
    
    @bp.route('/scheduled-messages/<message_id>', methods=['DELETE'])
    @handle_api_error
    def cancel_scheduled_message(message_id: str):
        """Cancel a scheduled message."""
        success = db_service.update_scheduled_message_status(message_id, "cancelled")
        
        if not success:
            raise ValidationError("Scheduled message not found or already processed")
        
        return jsonify({
            "success": True,
            "message": "Scheduled message cancelled successfully"
        })
    
    # ===== UTILITY ROUTES =====
    
    @bp.route('/groups/<group_jid>/messages', methods=['GET'])
    @handle_api_error
    def get_group_messages(group_jid: str):
        """Get message history for a specific group."""
        limit = min(int(request.args.get('limit', 50)), 100)  # Cap at 100
        
        messages = db_service.get_group_messages(group_jid, limit)
        
        return jsonify({
            "success": True,
            "data": {
                "group_jid": group_jid,
                "messages": [
                    {
                        "id": msg.id,
                        "message_content": msg.message_content,
                        "message_type": msg.message_type,
                        "status": msg.status,
                        "sent_at": msg.sent_at.isoformat() if msg.sent_at else None,
                        "error_message": msg.error_message
                    } for msg in messages
                ],
                "total": len(messages)
            }
        })
    
    @bp.route('/process-scheduled', methods=['POST'])
    @handle_api_error
    def process_scheduled_messages():
        """Manual trigger to process pending scheduled messages."""
        processed_count = scheduler_service.process_pending_messages()
        
        return jsonify({
            "success": True,
            "data": {
                "processed_count": processed_count,
                "message": f"Processed {processed_count} scheduled messages"
            }
        })
    
    @bp.route('/contacts', methods=['GET'])
    @handle_api_error
    def get_contacts():
        """Get contacts with efficient options - database first, WASender API only if needed."""
        
        # Check if full sync is explicitly requested
        force_api_sync = request.args.get('force_api_sync', 'false').lower() == 'true'
        limit = request.args.get('limit', type=int)
        
        if force_api_sync:
            logger.warning("Full WASender API sync explicitly requested - this will be slow!")
            # Get contacts from Wasender API (expensive operation)
            contacts = group_service.get_all_contacts()
            
            # Sync contacts to database
            sync_result = db_service.sync_contacts_from_api(contacts)
            
            # Convert contacts to dictionary format
            contacts_data = [contact.to_dict() for contact in contacts]
            
            return jsonify({
                "success": True,
                "data": {
                    "contacts": contacts_data,
                    "total": len(contacts_data),
                    "sync_result": sync_result,
                    "source": "wasender_api",
                    "warning": "Full API sync performed - this was expensive!"
                }
            })
        else:
            # Efficient approach: Get contacts from database only
            logger.info("Using efficient database-only contact retrieval")
            
            # Get contacts from database with optional limit
            contacts_data = db_service.get_all_contacts(limit=limit)
            
            # Get total count from database
            total_count = db_service.get_contacts_count()
            
            # Get last sync time for information
            last_sync = db_service.get_last_sync_timestamp()
            
            return jsonify({
                "success": True,
                "data": {
                    "contacts": contacts_data,
                    "returned": len(contacts_data),
                    "total": total_count,
                    "source": "database",
                    "limited": limit is not None,
                    "last_sync": last_sync,
                    "sync_result": {
                        "message": "No sync performed - using efficient database retrieval",
                        "api_calls_avoided": True
                    }
                },
                "info": "Efficient mode: Use ?force_api_sync=true for full WASender sync (slow)"
            })

    @bp.route('/contacts/force-sync', methods=['POST'])
    @handle_api_error  
    def force_full_sync():
        """Force a full contact sync from WASender API - use with caution!"""
        logger.warning("FORCE FULL SYNC requested - this will sync all contacts from WASender API")
        
        # Get contacts from Wasender API (expensive operation)
        contacts = group_service.get_all_contacts()
        
        # Sync contacts to database
        sync_result = db_service.sync_contacts_from_api(contacts)
        
        return jsonify({
            "success": True,
            "data": {
                "sync_result": sync_result,
                "total_contacts_processed": len(contacts),
                "warning": "Full sync completed - this was an expensive operation!"
            }
        })

    @bp.route('/contacts/database', methods=['GET'])
    @handle_api_error
    def get_contacts_from_database():
        """Get contacts from local database (cached from Wasender API)."""
        limit = request.args.get('limit', type=int)
        
        # Get contacts with optional limit
        contacts_data = db_service.get_all_contacts(limit=limit)
        
        # Get total count from database
        total_count = db_service.get_contacts_count()
        
        return jsonify({
            "success": True,
            "data": {
                "contacts": contacts_data,
                "returned": len(contacts_data),
                "total": total_count,
                "source": "database",
                "limited": limit is not None
            }
        })

    @bp.route('/contacts/search', methods=['GET'])
    @handle_api_error
    def search_contacts():
        """Search contacts with filters and pagination."""
        search_term = request.args.get('q', '').strip()
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        only_wasender = request.args.get('only_wasender', 'true').lower() == 'true'
        
        # Limit the maximum results to prevent overload
        limit = min(limit, 200)
        
        result = db_service.search_contacts(
            search_term=search_term if search_term else None,
            limit=limit,
            offset=offset,
            only_wasender=only_wasender
        )
        
        return jsonify({
            "success": True,
            "data": result
        })

    @bp.route('/groups/create-with-contacts', methods=['POST'])
    @handle_api_error
    def create_group_with_contacts():
        """Create a WhatsApp group using selected contact IDs with enhanced validation."""
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        group_name = data.get('group_name', '').strip()
        contact_ids = data.get('contact_ids', [])
        auto_sync_missing = data.get('auto_sync_missing', True)  # New option to auto-sync missing contacts
        
        if not group_name:
            return jsonify({"success": False, "error": "Group name is required"}), 400
        
        if not contact_ids or not isinstance(contact_ids, list):
            return jsonify({"success": False, "error": "contact_ids must be a non-empty list"}), 400
        
        if len(contact_ids) < 1:
            return jsonify({"success": False, "error": "At least 1 contact is required to create a group"}), 400
        
        # Get contacts by IDs from local database
        contacts = db_service.get_contacts_by_ids(contact_ids)
        
        # Check for missing contacts
        found_ids = [c['id'] for c in contacts]
        missing_ids = [cid for cid in contact_ids if cid not in found_ids]
        
        if missing_ids:
            if auto_sync_missing:
                logger.warning(f"Missing contact IDs detected: {missing_ids}. Attempting to sync from WASender API...")
                
                # Try to sync missing contacts from WASender API (EFFICIENT TARGETED SYNC)
                try:
                    # Use efficient targeted sync instead of syncing all 2500+ contacts
                    sync_result = group_service.sync_missing_contacts_only(missing_ids, db_service)
                    logger.info(f"Targeted contact sync result: {sync_result}")
                    
                    # Retry getting contacts after sync
                    contacts = db_service.get_contacts_by_ids(contact_ids)
                    found_ids = [c['id'] for c in contacts]
                    still_missing_ids = [cid for cid in contact_ids if cid not in found_ids]
                    
                    if still_missing_ids:
                        return jsonify({
                            "success": False, 
                            "error": f"Contacts not found even after sync: {still_missing_ids}",
                            "details": {
                                "missing_contact_ids": still_missing_ids,
                                "sync_performed": True,
                                "sync_result": sync_result
                            }
                        }), 400
                    else:
                        logger.info(f"Successfully synced and found all contacts after sync")
                        
                except Exception as sync_error:
                    logger.error(f"Failed to sync contacts from WASender API: {sync_error}")
                    return jsonify({
                        "success": False, 
                        "error": f"Contacts not found and sync failed: {missing_ids}",
                        "details": {
                            "missing_contact_ids": missing_ids,
                            "sync_attempted": True,
                            "sync_error": str(sync_error)
                        }
                    }), 400
            else:
                return jsonify({
                    "success": False, 
                    "error": f"Some contacts not found in database: {missing_ids}",
                    "details": {
                        "missing_contact_ids": missing_ids,
                        "found_contact_ids": found_ids,
                        "suggestion": "Enable auto_sync_missing or sync contacts manually"
                    }
                }), 400
        
        # Validate we have enough valid contacts
        if len(contacts) < 1:
            return jsonify({
                "success": False, 
                "error": "Not enough valid contacts found for group creation"
            }), 400
        
        # Extract phone numbers and validate them
        participants = []
        contact_info = []
        invalid_contacts = []
        
        for contact in contacts:
            phone_number = contact.get('phone_number', '').replace('+', '').strip()
            
            # Validate phone number format
            if not phone_number or not phone_number.replace('+', '').replace('-', '').replace(' ', '').isdigit():
                invalid_contacts.append({
                    "id": contact['id'],
                    "name": contact.get('name', 'Unknown'),
                    "phone_number": phone_number,
                    "reason": "Invalid phone number format"
                })
                continue
            
            # Clean phone number for WhatsApp API
            clean_phone = phone_number.replace('_s_whatsapp_net', '').replace('@s.whatsapp.net', '')
            
            if clean_phone:
                participants.append(clean_phone)
                contact_info.append({
                    "id": contact['id'],
                    "name": contact.get('name') or contact.get('notify') or contact.get('verified_name') or f"Contact {clean_phone}",
                    "phone_number": clean_phone,
                    "original_phone": contact.get('phone_number', '')
                })
        
        # Check if we have invalid contacts
        if invalid_contacts:
            logger.warning(f"Found {len(invalid_contacts)} invalid contacts: {invalid_contacts}")
        
        # Check if we have enough valid participants after validation
        if len(participants) < 1:
            return jsonify({
                "success": False, 
                "error": "Not enough valid phone numbers found in selected contacts",
                "details": {
                    "total_contacts_selected": len(contacts),
                    "valid_phone_numbers": len(participants),
                    "invalid_contacts": invalid_contacts
                }
            }), 400
        
        # Create the group using GroupService
        try:
            logger.info(f"Creating group '{group_name}' with {len(participants)} participants: {participants}")
            
            # GroupService.create_group returns a Group object
            created_group = group_service.create_group(
                name=group_name,
                participants=participants
            )
            
            # Update the group metadata with contact selection info
            created_group.metadata.update({
                "created_via": "contact_selection",
                "selected_contacts": contact_info,
                "invalid_contacts": invalid_contacts,
                "auto_sync_performed": bool(missing_ids and auto_sync_missing)
            })
            
            # Save group to database
            saved_group = db_service.save_group(created_group)
            
            logger.info(f"Successfully created group '{group_name}' with JID: {created_group.group_jid}")
            
            return jsonify({
                "success": True,
                "data": {
                    "group": {
                        "id": saved_group.id,
                        "group_jid": saved_group.group_jid,
                        "name": saved_group.name,
                        "member_count": saved_group.member_count,
                        "created_at": saved_group.created_at.isoformat() if saved_group.created_at else None
                    },
                    "participants": contact_info,
                    "wasender_group_jid": created_group.group_jid,
                    "validation_summary": {
                        "total_contacts_requested": len(contact_ids),
                        "valid_contacts_found": len(contact_info),
                        "invalid_contacts": len(invalid_contacts),
                        "missing_contacts_synced": len(missing_ids) if missing_ids else 0
                    }
                }
            })
            
        except Exception as e:
            logger.error(f"Error creating group with contacts: {e}")
            return jsonify({
                "success": False,
                "error": f"Failed to create group: {str(e)}",
                "details": {
                    "group_name": group_name,
                    "participants_count": len(participants),
                    "participants": participants[:5]  # Show first 5 for debugging
                }
            }), 500

    @bp.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint."""
        # Check if background scheduler is available (optional)
        scheduler_status = "not_available"
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            scheduler_status = "available"
        except ImportError:
            scheduler_status = "not_installed"
        
        return jsonify({
            "success": True,
            "service": "group_messaging",
            "status": "healthy",
            "scheduler_status": scheduler_status,
            "manual_processing": "/api/group-messaging/process-scheduled",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    return bp 