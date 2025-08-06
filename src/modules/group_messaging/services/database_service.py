"""
Database Service for Group Messaging Module
===========================================
Handles all database operations for groups, messages, and scheduling.
Integrates with existing Supabase client.
"""

import logging
import time
import functools
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from ..models.group import Group, GroupMessage
from ..models.schedule import ScheduledMessage
from ..core.exceptions import DatabaseError, ValidationError

logger = logging.getLogger(__name__)


def retry_on_connection_error(max_retries=3, delay=1, backoff=2):
    """
    Decorator to retry database operations on connection errors.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            current_delay = delay
            
            while attempt < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempt += 1
                    error_msg = str(e).lower()
                    
                    # Only retry on connection-related errors
                    if any(error in error_msg for error in [
                        'connection reset by peer',
                        'connection timeout',
                        'connection refused',
                        'network error',
                        'timeout'
                    ]):
                        if attempt < max_retries:
                            logger.warning(f"Connection error in {func.__name__} (attempt {attempt}/{max_retries}): {e}. Retrying in {current_delay}s...")
                            time.sleep(current_delay)
                            current_delay *= backoff
                            continue
                    
                    # Re-raise the exception if not a connection error or max retries reached
                    raise e
            
            return None
        return wrapper
    return decorator


class DatabaseService:
    """Service for handling database operations for group messaging."""
    
    def __init__(self, supabase_client):
        """
        Initialize with existing Supabase client.
        
        Args:
            supabase_client: Existing Supabase client instance
        """
        self.supabase = supabase_client
    
    # ===== GROUP OPERATIONS =====
    
    def save_group(self, group: Group) -> Group:
        """
        Save or update a group in the database.
        
        Args:
            group: Group object to save
            
        Returns:
            Saved Group object with database ID
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            group_data = {
                "group_jid": group.group_jid,
                "name": group.name,
                "img_url": group.img_url,
                "status": group.status,
                "member_count": group.member_count,
                "metadata": group.metadata or {}
            }
            
            # Check if group already exists
            existing = self.supabase.table("groups").select("id").eq("group_jid", group.group_jid).execute()
            
            if existing.data:
                # Update existing group
                group_data["updated_at"] = datetime.utcnow().isoformat()
                result = self.supabase.table("groups").update(group_data).eq("group_jid", group.group_jid).execute()
                group.id = existing.data[0]["id"]
            else:
                # Insert new group
                group_data["created_at"] = datetime.utcnow().isoformat()
                result = self.supabase.table("groups").insert(group_data).execute()
                if result.data:
                    group.id = result.data[0]["id"]
            
            logger.info(f"Successfully saved group: {group.name} ({group.group_jid})")
            return group
            
        except Exception as e:
            logger.error(f"Failed to save group: {e}")
            raise DatabaseError(f"Failed to save group: {str(e)}")
    
    def get_group_by_jid(self, group_jid: str) -> Optional[Group]:
        """
        Get a group by its JID.
        
        Args:
            group_jid: Group JID to search for
            
        Returns:
            Group object if found, None otherwise
        """
        try:
            result = self.supabase.table("groups").select("*").eq("group_jid", group_jid).execute()
            
            if result.data:
                group_data = result.data[0]
                return Group(
                    id=group_data["id"],
                    group_jid=group_data["group_jid"],
                    name=group_data["name"],
                    img_url=group_data.get("img_url"),
                    status=group_data["status"],
                    member_count=group_data["member_count"],
                    metadata=group_data.get("metadata", {}),
                    created_at=group_data.get("created_at"),
                    updated_at=group_data.get("updated_at")
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get group by JID: {e}")
            raise DatabaseError(f"Failed to get group: {str(e)}")
    
    def get_all_groups(self, status: Optional[str] = None) -> List[Group]:
        """
        Get all groups from the database.
        
        Args:
            status: Optional status filter
            
        Returns:
            List of Group objects
        """
        try:
            query = self.supabase.table("groups").select("*")
            
            if status:
                query = query.eq("status", status)
            
            result = query.order("created_at", desc=True).execute()
            
            groups = []
            for group_data in result.data:
                group = Group(
                    id=group_data["id"],
                    group_jid=group_data["group_jid"],
                    name=group_data["name"],
                    img_url=group_data.get("img_url"),
                    status=group_data["status"],
                    member_count=group_data["member_count"],
                    metadata=group_data.get("metadata", {}),
                    created_at=group_data.get("created_at"),
                    updated_at=group_data.get("updated_at")
                )
                groups.append(group)
            
            return groups
            
        except Exception as e:
            logger.error(f"Failed to get all groups: {e}")
            raise DatabaseError(f"Failed to get groups: {str(e)}")
    
    # ===== MESSAGE OPERATIONS =====
    
    def save_group_message(self, message: GroupMessage, group_id: Optional[str] = None) -> GroupMessage:
        """
        Save a group message to the database.
        
        Args:
            message: GroupMessage object to save
            group_id: Optional group ID (will be looked up by JID if not provided)
            
        Returns:
            Saved GroupMessage object with database ID
        """
        try:
            # Get group ID if not provided
            if not group_id:
                group = self.get_group_by_jid(message.group_jid)
                if group:
                    group_id = group.id
                else:
                    # Create a placeholder group if it doesn't exist
                    placeholder_group = Group(
                        group_jid=message.group_jid,
                        name=f"Group {message.group_jid}",
                        status="unknown"
                    )
                    saved_group = self.save_group(placeholder_group)
                    group_id = saved_group.id
            
            message_data = {
                "group_id": group_id,
                "message_content": message.message_content,
                "message_type": message.message_type,
                "media_url": message.media_url,
                "status": message.status,
                "wasender_message_id": message.wasender_message_id,
                "error_message": message.error_message,
                "metadata": message.metadata or {},
                "sent_at": message.sent_at.isoformat() if message.sent_at else datetime.utcnow().isoformat()
            }
            
            result = self.supabase.table("group_messages").insert(message_data).execute()
            
            if result.data:
                message.id = result.data[0]["id"]
            
            logger.info(f"Successfully saved group message: {message.id}")
            return message
            
        except Exception as e:
            logger.error(f"Failed to save group message: {e}")
            raise DatabaseError(f"Failed to save group message: {str(e)}")
    
    def get_group_messages(self, group_jid: str, limit: int = 50) -> List[GroupMessage]:
        """
        Get messages for a specific group.
        
        Args:
            group_jid: Group JID to get messages for
            limit: Maximum number of messages to return
            
        Returns:
            List of GroupMessage objects
        """
        try:
            # Get group first
            group = self.get_group_by_jid(group_jid)
            if not group:
                return []
            
            result = self.supabase.table("group_messages")\
                .select("*")\
                .eq("group_id", group.id)\
                .order("sent_at", desc=True)\
                .limit(limit)\
                .execute()
            
            messages = []
            for msg_data in result.data:
                message = GroupMessage(
                    id=msg_data["id"],
                    group_jid=group_jid,
                    message_content=msg_data["message_content"],
                    message_type=msg_data["message_type"],
                    media_url=msg_data.get("media_url"),
                    status=msg_data["status"],
                    wasender_message_id=msg_data.get("wasender_message_id"),
                    error_message=msg_data.get("error_message"),
                    metadata=msg_data.get("metadata", {}),
                    sent_at=datetime.fromisoformat(msg_data["sent_at"]) if msg_data.get("sent_at") else None
                )
                messages.append(message)
            
            return messages
            
        except Exception as e:
            logger.error(f"Failed to get group messages: {e}")
            raise DatabaseError(f"Failed to get group messages: {str(e)}")
    
    # ===== SCHEDULED MESSAGE OPERATIONS =====
    
    def save_scheduled_message(self, scheduled_message: ScheduledMessage) -> ScheduledMessage:
        """
        Save a scheduled message to the database.
        
        Args:
            scheduled_message: ScheduledMessage object to save
            
        Returns:
            Saved ScheduledMessage object with database ID
        """
        try:
            message_data = {
                "message_content": scheduled_message.message_content,
                "message_type": scheduled_message.message_type,
                "media_url": scheduled_message.media_url,
                "target_groups": scheduled_message.target_groups,  # Correct field name
                "scheduled_at": scheduled_message.scheduled_at.isoformat(),  # Correct field name
                "status": scheduled_message.status.value,
                "recurring_pattern": scheduled_message.recurring_pattern.value if scheduled_message.recurring_pattern else None,
                "recurring_interval": scheduled_message.recurring_interval,
                "next_send_at": scheduled_message.next_send_at.isoformat() if scheduled_message.next_send_at else None,
                "total_sent": scheduled_message.total_sent,
                "total_failed": scheduled_message.total_failed,
                "metadata": scheduled_message.metadata or {}
            }
            
            result = self.supabase.table("scheduled_messages").insert(message_data).execute()
            
            if result.data:
                scheduled_message.id = result.data[0]["id"]
            
            logger.info(f"Successfully saved scheduled message: {scheduled_message.id}")
            return scheduled_message
            
        except Exception as e:
            logger.error(f"Failed to save scheduled message: {e}")
            raise DatabaseError(f"Failed to save scheduled message: {str(e)}")
    
    @retry_on_connection_error(max_retries=3, delay=2, backoff=2)
    def get_pending_scheduled_messages(self) -> List[ScheduledMessage]:
        """
        Get all pending scheduled messages that are ready to be sent.
        
        Returns:
            List of ScheduledMessage objects ready for sending
        """
        try:
            now = datetime.utcnow().isoformat()
            
            result = self.supabase.table("scheduled_messages")\
                .select("*")\
                .eq("status", "pending")\
                .lte("scheduled_at", now)\
                .execute()
            
            messages = []
            for msg_data in result.data:
                from ..models.schedule import ScheduleStatus, RecurringPattern
                
                message = ScheduledMessage(
                    id=msg_data["id"],
                    message_content=msg_data["message_content"],
                    message_type=msg_data["message_type"],
                    media_url=msg_data.get("media_url"),
                    target_groups=msg_data["target_groups"],
                    scheduled_at=datetime.fromisoformat(msg_data["scheduled_at"]),
                    status=ScheduleStatus(msg_data["status"]),
                    recurring_pattern=RecurringPattern(msg_data["recurring_pattern"]) if msg_data.get("recurring_pattern") else None,
                    recurring_interval=msg_data.get("recurring_interval"),
                    next_send_at=datetime.fromisoformat(msg_data["next_send_at"]) if msg_data.get("next_send_at") else None,
                    total_sent=msg_data.get("total_sent", 0),
                    total_failed=msg_data.get("total_failed", 0),
                    metadata=msg_data.get("metadata", {})
                )
                messages.append(message)
            
            return messages
            
        except Exception as e:
            logger.error(f"Failed to get pending scheduled messages: {e}")
            raise DatabaseError(f"Failed to get pending scheduled messages: {str(e)}")
    
    def get_all_scheduled_messages(self, status_filter: str = None, limit: int = 100) -> List[dict]:
        """
        Get all scheduled messages from the database.
        
        Args:
            status_filter: Optional status filter (pending, sent, failed, cancelled)
            limit: Maximum number of messages to return
            
        Returns:
            List of scheduled message dictionaries
        """
        try:
            query = self.supabase.table("scheduled_messages").select("*")
            
            if status_filter:
                query = query.eq("status", status_filter)
            
            result = query.order("created_at", desc=True).limit(limit).execute()
            
            # Convert the data to match our frontend interface expectations
            scheduled_messages = []
            for msg_data in result.data:
                # Database and frontend use the same field names, no mapping needed
                scheduled_message = {
                    "id": msg_data["id"],
                    "message_content": msg_data["message_content"],
                    "message_type": msg_data.get("message_type", "text"),
                    "target_groups": msg_data.get("target_groups", []),  # Direct field mapping
                    "scheduled_at": msg_data.get("scheduled_at"),  # Direct field mapping
                    "next_send_at": msg_data.get("next_send_at"),
                    "status": msg_data["status"],
                    "recurring_pattern": msg_data.get("recurring_pattern"),
                    "recurring_interval": msg_data.get("recurring_interval"),
                    "total_sent": msg_data.get("total_sent", 0),
                    "total_failed": msg_data.get("total_failed", 0),
                    "campaign_name": msg_data.get("campaign_name"),
                    "created_at": msg_data["created_at"],
                    "executed_at": msg_data.get("executed_at"),
                    "error_message": msg_data.get("error_message")
                }
                scheduled_messages.append(scheduled_message)
            
            logger.info(f"Retrieved {len(scheduled_messages)} scheduled messages from database")
            return scheduled_messages
            
        except Exception as e:
            logger.error(f"Failed to get scheduled messages: {e}")
            raise DatabaseError(f"Failed to get scheduled messages: {str(e)}")

    def update_scheduled_message_status(self, message_id: str, status: str, **kwargs) -> bool:
        """
        Update the status of a scheduled message.
        
        Args:
            message_id: ID of the scheduled message
            status: New status
            **kwargs: Additional fields to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            update_data = {"status": status, "updated_at": datetime.utcnow().isoformat()}
            update_data.update(kwargs)
            
            result = self.supabase.table("scheduled_messages")\
                .update(update_data)\
                .eq("id", message_id)\
                .execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Failed to update scheduled message status: {e}")
            raise DatabaseError(f"Failed to update scheduled message: {str(e)}")
    
    # ===== CAMPAIGN OPERATIONS =====
    
    def create_group_campaign(self, name: str, message_content: str, target_groups: List[str], **kwargs) -> Dict[str, Any]:
        """
        Create a new group campaign.
        
        Args:
            name: Campaign name
            message_content: Message content
            target_groups: List of target group JIDs
            **kwargs: Additional campaign data
            
        Returns:
            Campaign data with ID
        """
        try:
            campaign_data = {
                "name": name,
                "message_content": message_content,
                "message_type": kwargs.get("message_type", "text"),
                "media_url": kwargs.get("media_url"),
                "target_groups": target_groups,
                "total_groups": len(target_groups),
                "status": "pending"
            }
            
            result = self.supabase.table("group_campaigns").insert(campaign_data).execute()
            
            if result.data:
                logger.info(f"Successfully created group campaign: {result.data[0]['id']}")
                return result.data[0]
            
            raise DatabaseError("Failed to create campaign - no data returned")
            
        except Exception as e:
            logger.error(f"Failed to create group campaign: {e}")
            raise DatabaseError(f"Failed to create group campaign: {str(e)}")
    
    def update_campaign_stats(self, campaign_id: str, successful_sends: int, failed_sends: int) -> bool:
        """
        Update campaign statistics.
        
        Args:
            campaign_id: Campaign ID
            successful_sends: Number of successful sends
            failed_sends: Number of failed sends
            
        Returns:
            True if successful
        """
        try:
            update_data = {
                "successful_sends": successful_sends,
                "failed_sends": failed_sends,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            result = self.supabase.table("group_campaigns")\
                .update(update_data)\
                .eq("id", campaign_id)\
                .execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Failed to update campaign stats: {e}")
            raise DatabaseError(f"Failed to update campaign stats: {str(e)}")
    
    # ===== CONTACT OPERATIONS =====
    
    def save_contact(self, contact) -> dict:
        """
        Save or update a contact in the database.
        
        Args:
            contact: Contact object to save
            
        Returns:
            Saved contact data from database
        """
        try:
            contact_data = {
                "wasender_jid": contact.jid,
                "phone_number": contact.phone_number,
                "name": contact.name,
                "notify": contact.notify,
                "verified_name": contact.verified_name,
                "profile_image_url": contact.img_url,
                "whatsapp_status": contact.status,
                "is_business_account": contact.is_business,
                "raw_wasender_data": contact.metadata,
                "wasender_sync_status": "synced",
                "last_updated_from_wasender": datetime.utcnow().isoformat()
            }
            
            # Check if contact exists by JID
            existing = self.supabase.table("contacts").select("id").eq("wasender_jid", contact.jid).execute()
            
            if existing.data:
                # Update existing contact
                contact_data["updated_at"] = datetime.utcnow().isoformat()
                result = self.supabase.table("contacts").update(contact_data).eq("wasender_jid", contact.jid).execute()
                logger.info(f"Updated existing contact: {contact.display_name} ({contact.jid})")
            else:
                # Insert new contact
                contact_data["created_at"] = datetime.utcnow().isoformat()
                result = self.supabase.table("contacts").insert(contact_data).execute()
                logger.info(f"Saved new contact: {contact.display_name} ({contact.jid})")
            
            if result.data:
                return result.data[0]
            else:
                raise DatabaseError("No data returned from database")
                
        except Exception as e:
            logger.error(f"Failed to save contact {contact.jid}: {e}")
            raise DatabaseError(f"Failed to save contact: {str(e)}")
    
    def save_contacts_bulk(self, contacts: List) -> dict:
        """
        Save multiple contacts to the database in bulk.
        
        Args:
            contacts: List of Contact objects
            
        Returns:
            Dictionary with save results
        """
        try:
            saved_count = 0
            updated_count = 0
            failed_count = 0
            
            logger.info(f"Bulk saving {len(contacts)} contacts to database")
            
            for contact in contacts:
                try:
                    # Check if contact exists
                    existing = self.supabase.table("contacts").select("id").eq("wasender_jid", contact.jid).execute()
                    
                    contact_data = {
                        "wasender_jid": contact.jid,
                        "phone_number": contact.phone_number,
                        "name": contact.name,
                        "notify": contact.notify,
                        "verified_name": contact.verified_name,
                        "profile_image_url": contact.img_url,
                        "whatsapp_status": contact.status,
                        "is_business_account": contact.is_business,
                        "raw_wasender_data": contact.metadata,
                        "wasender_sync_status": "synced",
                        "last_updated_from_wasender": datetime.utcnow().isoformat()
                    }
                    
                    if existing.data:
                        # Update existing
                        contact_data["updated_at"] = datetime.utcnow().isoformat()
                        self.supabase.table("contacts").update(contact_data).eq("wasender_jid", contact.jid).execute()
                        updated_count += 1
                    else:
                        # Insert new
                        contact_data["created_at"] = datetime.utcnow().isoformat()
                        self.supabase.table("contacts").insert(contact_data).execute()
                        saved_count += 1
                        
                except Exception as e:
                    logger.error(f"Failed to save contact {contact.jid}: {e}")
                    failed_count += 1
            
            result = {
                "total_processed": len(contacts),
                "saved_new": saved_count,
                "updated_existing": updated_count,
                "failed": failed_count
            }
            
            logger.info(f"Bulk contact save completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to bulk save contacts: {e}")
            raise DatabaseError(f"Failed to bulk save contacts: {str(e)}")
    
    def get_all_contacts(self, limit: int = None) -> List[dict]:
        """
        Retrieve all contacts from the database.
        
        Args:
            limit: Optional limit on number of contacts to return
            
        Returns:
            List of contact dictionaries
        """
        try:
            query = self.supabase.table("contacts").select("*").order("updated_at", desc=True)
            
            if limit:
                query = query.limit(limit)
            else:
                # Set a high limit to get all contacts (Supabase default is 1000)
                query = query.limit(5000)
            
            result = query.execute()
            
            logger.info(f"Retrieved {len(result.data)} contacts from database")
            return result.data
            
        except Exception as e:
            logger.error(f"Failed to get contacts: {e}")
            raise DatabaseError(f"Failed to get contacts: {str(e)}")
    
    def search_contacts(self, 
                       search_term: str = None, 
                       limit: int = 100, 
                       offset: int = 0,
                       only_wasender: bool = True) -> dict:
        """
        Search contacts with filters and pagination.
        
        Args:
            search_term: Search in name, notify, or phone number
            limit: Number of contacts to return
            offset: Number of contacts to skip
            only_wasender: Only include contacts from Wasender API
            
        Returns:
            Dictionary with contacts and pagination info
        """
        try:
            # Start with base query
            query = self.supabase.table("contacts").select("*")
            
            # Filter by Wasender contacts if requested (skip complex filtering for now)
            # if only_wasender:
            #     query = query.not_.is_("wasender_jid", "null")
            
            # Apply search filter
            if search_term:
                # Search in name, notify, or phone number using OR conditions
                query = query.or_(f"name.ilike.%{search_term}%,notify.ilike.%{search_term}%,phone_number.like.%{search_term}%")
            
            # Apply pagination and ordering
            query = query.order("updated_at", desc=True).range(offset, offset + limit - 1)
            
            result = query.execute()
            
            # Get total count separately for better performance
            count_query = self.supabase.table("contacts").select("id", count="exact")
            # if only_wasender:
            #     count_query = count_query.not_.is_("wasender_jid", "null")
            if search_term:
                count_query = count_query.or_(f"name.ilike.%{search_term}%,notify.ilike.%{search_term}%,phone_number.like.%{search_term}%")
            
            count_result = count_query.execute()
            total_count = count_result.count
            
            logger.info(f"Found {len(result.data)} contacts (total: {total_count})")
            
            return {
                "contacts": result.data,
                "pagination": {
                    "total": total_count,
                    "limit": limit,
                    "offset": offset,
                    "returned": len(result.data),
                    "has_more": offset + len(result.data) < total_count
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to search contacts: {e}")
            raise DatabaseError(f"Failed to search contacts: {str(e)}")
    
    def get_contacts_by_ids(self, contact_ids: List[str]) -> List[dict]:
        """
        Get specific contacts by their database IDs.
        
        Args:
            contact_ids: List of contact database IDs
            
        Returns:
            List of contact dictionaries
        """
        try:
            if not contact_ids:
                return []
            
            # Filter out invalid UUIDs to prevent database errors
            import uuid
            valid_ids = []
            invalid_ids = []
            
            for contact_id in contact_ids:
                try:
                    # Try to parse as UUID to validate format
                    uuid.UUID(contact_id)
                    valid_ids.append(contact_id)
                except (ValueError, TypeError):
                    invalid_ids.append(contact_id)
                    logger.warning(f"Invalid UUID format for contact ID: {contact_id}")
            
            if invalid_ids:
                logger.warning(f"Filtered out {len(invalid_ids)} invalid contact IDs: {invalid_ids}")
            
            if not valid_ids:
                logger.info("No valid contact IDs provided")
                return []
            
            result = self.supabase.table("contacts").select("*").in_("id", valid_ids).execute()
            
            logger.info(f"Retrieved {len(result.data)} contacts by IDs (requested: {len(valid_ids)} valid, {len(invalid_ids)} invalid)")
            return result.data
            
        except Exception as e:
            logger.error(f"Failed to get contacts by IDs: {e}")
            raise DatabaseError(f"Failed to get contacts by IDs: {str(e)}")
    
    def get_contacts_count(self) -> int:
        """
        Get total count of contacts in the database.
        
        Returns:
            Total number of contacts
        """
        try:
            result = self.supabase.table("contacts").select("id", count="exact").execute()
            return result.count
            
        except Exception as e:
            logger.error(f"Failed to get contacts count: {e}")
            raise DatabaseError(f"Failed to get contacts count: {str(e)}")
    
    def get_contact_by_jid(self, jid: str) -> dict:
        """
        Get a specific contact by JID.
        
        Args:
            jid: Contact JID to search for
            
        Returns:
            Contact dictionary or None if not found
        """
        try:
            result = self.supabase.table("contacts").select("*").eq("wasender_jid", jid).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Failed to get contact by JID {jid}: {e}")
            raise DatabaseError(f"Failed to get contact: {str(e)}")
    
    def sync_contacts_from_api(self, contacts: List) -> dict:
        """
        Sync contacts from Wasender API to database.
        This method handles the full sync process including marking inactive contacts.
        
        Args:
            contacts: List of Contact objects from API
            
        Returns:
            Sync results dictionary
        """
        try:
            logger.info(f"Starting contact sync from API for {len(contacts)} contacts")
            
            # Get current JIDs from API
            api_jids = {contact.jid for contact in contacts}
            
            # Mark all contacts with existing wasender_jid as potentially inactive first
            self.supabase.table("contacts").update({
                "wasender_sync_status": "needs_verification",
                "updated_at": datetime.utcnow().isoformat()
            }).neq("wasender_jid", None).execute()
            
            # Save/update contacts from API
            bulk_result = self.save_contacts_bulk(contacts)
            
            # Mark contacts not in API as inactive
            if api_jids:
                # Get all contacts not in current API response
                existing_contacts = self.supabase.table("contacts").select("wasender_jid").execute()
                existing_jids = {c["wasender_jid"] for c in existing_contacts.data if c["wasender_jid"]}
                inactive_jids = existing_jids - api_jids
                
                if inactive_jids:
                    # Mark as inactive
                    for jid in inactive_jids:
                        self.supabase.table("contacts").update({
                            "wasender_sync_status": "inactive",
                            "updated_at": datetime.utcnow().isoformat()
                        }).eq("wasender_jid", jid).execute()
                    
                    bulk_result["marked_inactive"] = len(inactive_jids)
            
            logger.info(f"Contact sync completed: {bulk_result}")
            return bulk_result
            
        except Exception as e:
            logger.error(f"Failed to sync contacts from API: {e}")
            raise DatabaseError(f"Failed to sync contacts: {str(e)}") 

    def get_missing_contact_details(self, missing_contact_ids: List[str]) -> List[dict]:
        """
        Get whatever details we have for missing contact IDs to help with targeted sync.
        
        Args:
            missing_contact_ids: List of contact IDs that need to be synced
            
        Returns:
            List of contact details that could help identify them in WASender API
        """
        try:
            if not missing_contact_ids:
                return []
            
            # Filter out invalid UUIDs
            import uuid
            valid_ids = []
            for contact_id in missing_contact_ids:
                try:
                    uuid.UUID(contact_id)
                    valid_ids.append(contact_id)
                except (ValueError, TypeError):
                    logger.warning(f"Skipping invalid UUID: {contact_id}")
            
            if not valid_ids:
                return []
            
            # Get any existing data for these contact IDs
            result = self.supabase.table("contacts")\
                .select("id, phone_number, name, wasender_jid, email")\
                .in_("id", valid_ids)\
                .execute()
            
            logger.info(f"Found existing data for {len(result.data)} out of {len(valid_ids)} missing contacts")
            return result.data
            
        except Exception as e:
            logger.error(f"Failed to get missing contact details: {e}")
            return []

    def sync_targeted_contacts(self, contacts: List, only_missing_ids: List[str] = None) -> dict:
        """
        Sync only specific contacts instead of bulk sync.
        More efficient when you only need to update a few contacts.
        
        Args:
            contacts: List of Contact objects from WASender API
            only_missing_ids: If provided, only sync contacts that match these missing IDs
            
        Returns:
            Dictionary with sync results
        """
        try:
            if not contacts:
                return {"total_processed": 0, "saved_new": 0, "updated_existing": 0, "failed": 0}
            
            saved_count = 0
            updated_count = 0
            failed_count = 0
            
            logger.info(f"Starting targeted sync for {len(contacts)} contacts")
            
            # If we have specific missing IDs, get their phone numbers for filtering
            target_phones = set()
            if only_missing_ids:
                missing_details = self.get_missing_contact_details(only_missing_ids)
                for detail in missing_details:
                    phone = detail.get('phone_number', '')
                    if phone:
                        # Normalize phone for comparison
                        clean_phone = phone.replace('+', '').replace('-', '').replace(' ', '')
                        clean_phone = clean_phone.replace('@s.whatsapp.net', '').replace('_s_whatsapp_net', '')
                        target_phones.add(clean_phone)
            
            for contact in contacts:
                try:
                    # If we have target phones, filter to only sync those
                    if target_phones:
                        contact_phone = contact.phone_number.replace('+', '').replace('-', '').replace(' ', '')
                        contact_phone = contact_phone.replace('@s.whatsapp.net', '').replace('_s_whatsapp_net', '')
                        
                        if contact_phone not in target_phones:
                            continue  # Skip this contact as it's not in our target list
                    
                    # Check if contact exists by JID
                    existing = self.supabase.table("contacts").select("id").eq("wasender_jid", contact.jid).execute()
                    
                    contact_data = {
                        "wasender_jid": contact.jid,
                        "phone_number": contact.phone_number,
                        "name": contact.name,
                        "notify": contact.notify,
                        "verified_name": contact.verified_name,
                        "profile_image_url": contact.img_url,
                        "whatsapp_status": contact.status,
                        "is_business_account": contact.is_business,
                        "raw_wasender_data": contact.metadata,
                        "wasender_sync_status": "synced",
                        "last_updated_from_wasender": datetime.utcnow().isoformat()
                    }
                    
                    if existing.data:
                        # Update existing
                        contact_data["updated_at"] = datetime.utcnow().isoformat()
                        self.supabase.table("contacts").update(contact_data).eq("wasender_jid", contact.jid).execute()
                        updated_count += 1
                        logger.info(f"Updated targeted contact: {contact.name or 'Unnamed'} ({contact.phone_number})")
                    else:
                        # Insert new
                        contact_data["created_at"] = datetime.utcnow().isoformat()
                        self.supabase.table("contacts").insert(contact_data).execute()
                        saved_count += 1
                        logger.info(f"Saved new targeted contact: {contact.name or 'Unnamed'} ({contact.phone_number})")
                        
                except Exception as e:
                    logger.error(f"Failed to sync targeted contact {contact.jid}: {e}")
                    failed_count += 1
            
            result = {
                "total_processed": len(contacts),
                "saved_new": saved_count,
                "updated_existing": updated_count,
                "failed": failed_count,
                "sync_type": "targeted"
            }
            
            logger.info(f"Targeted contact sync completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to sync targeted contacts: {e}")
            raise DatabaseError(f"Failed to sync targeted contacts: {str(e)}")

    def get_last_sync_timestamp(self) -> Optional[str]:
        """
        Get the timestamp of the last successful contact sync.
        This can be used for incremental sync in the future.
        
        Returns:
            ISO timestamp string of last sync, or None if never synced
        """
        try:
            # Get the most recent sync timestamp from contacts
            result = self.supabase.table("contacts")\
                .select("last_updated_from_wasender")\
                .not_.is_("last_updated_from_wasender", "null")\
                .order("last_updated_from_wasender", desc=True)\
                .limit(1)\
                .execute()
            
            if result.data:
                return result.data[0]["last_updated_from_wasender"]
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get last sync timestamp: {e}")
            return None 