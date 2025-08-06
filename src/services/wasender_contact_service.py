"""
WASender Contact Sync Service
============================
Handles fetching and syncing contact information from WASender API
to enrich contact data with proper names and profile information.

Author: Rian Infotech
Version: 1.0
"""

import logging
import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
import time
import threading
import schedule

from src.config.config import WASENDER_API_TOKEN
from src.core.supabase_client import get_supabase_manager

# Configure logging
logger = logging.getLogger(__name__)

class WASenderContactService:
    """Service to sync contacts from WASender API to local database."""
    
    def __init__(self):
        self.api_token = WASENDER_API_TOKEN
        self.base_url = "https://wasenderapi.com/api"
        self.headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        } if self.api_token else None
        
    def is_configured(self) -> bool:
        """Check if WASender API is properly configured."""
        return self.api_token is not None
    
    def fetch_contacts_from_wasender(self) -> List[Dict]:
        """
        Fetch all contacts from WASender API.
        
        Returns:
            List of contact dictionaries from WASender API
        """
        if not self.is_configured():
            logger.error("WASender API not configured")
            return []
        
        try:
            response = requests.get(
                f"{self.base_url}/contacts",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Handle different response formats
            if isinstance(data, dict):
                if data.get('success') and 'data' in data:
                    contacts = data['data']
                elif 'contacts' in data:
                    contacts = data['contacts']
                else:
                    contacts = []
            elif isinstance(data, list):
                contacts = data
            else:
                contacts = []
            
            logger.info(f"Fetched {len(contacts)} contacts from WASender API")
            return contacts
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching contacts from WASender API: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching contacts: {e}")
            return []
    
    def normalize_phone_number(self, phone: str) -> str:
        """
        Normalize phone number to match database format.
        
        Args:
            phone: Phone number in various formats
            
        Returns:
            Normalized phone number
        """
        if not phone:
            return ""
        
        # Remove common suffixes and prefixes
        clean_phone = phone.replace('@s.whatsapp.net', '').replace('@c.us', '')
        
        # Remove any non-digit characters except +
        import re
        clean_phone = re.sub(r'[^\d+]', '', clean_phone)
        
        # Remove leading + if present
        if clean_phone.startswith('+'):
            clean_phone = clean_phone[1:]
        
        return clean_phone
    
    def extract_contact_info(self, wasender_contact: Dict) -> Dict:
        """
        Extract relevant contact information from WASender contact object.
        
        Args:
            wasender_contact: Contact data from WASender API
            
        Returns:
            Dictionary with extracted contact information
        """
        try:
            # Extract phone number (id field typically contains phone@s.whatsapp.net)
            jid = wasender_contact.get('id', wasender_contact.get('jid', ''))
            phone_number = self.normalize_phone_number(jid)
            
            # Extract name - prioritize verifiedName, then name, then notify
            display_name = (
                wasender_contact.get('verifiedName') or 
                wasender_contact.get('name') or 
                wasender_contact.get('notify') or 
                None
            )
            
            # Only use name if it's not the same as phone number
            if display_name and display_name != phone_number and not display_name.endswith('_s_whatsapp_net'):
                name = display_name
            else:
                name = None
            
            return {
                'phone_number': phone_number,
                'name': name,
                'profile_image_url': wasender_contact.get('imgUrl'),
                'whatsapp_status': wasender_contact.get('status'),
                'is_business': wasender_contact.get('isBusiness', False),
                'verified_name': wasender_contact.get('verifiedName'),
                'last_seen': wasender_contact.get('lastSeen'),
                'wasender_jid': jid,
                'raw_contact_data': wasender_contact  # Store original data for reference
            }
            
        except Exception as e:
            logger.error(f"Error extracting contact info: {e}")
            return {}
    
    def update_contact_in_database(self, contact_info: Dict) -> bool:
        """
        Update or create contact in database with WASender information.
        
        Args:
            contact_info: Extracted contact information
            
        Returns:
            True if successful, False otherwise
        """
        if not contact_info.get('phone_number'):
            return False
        
        try:
            supabase = get_supabase_manager()
            if not supabase.is_connected():
                logger.error("Database not connected")
                return False
            
            phone_number = contact_info['phone_number']
            
            # Try to find existing contact with various phone number formats
            phone_formats = [
                phone_number,
                f"{phone_number}_s_whatsapp_net",
                f"{phone_number}@s.whatsapp.net"
            ]
            
            existing_contact = None
            for phone_format in phone_formats:
                result = supabase.client.table('contacts')\
                    .select('*')\
                    .eq('phone_number', phone_format)\
                    .execute()
                
                if result.data:
                    existing_contact = result.data[0]
                    break
            
            # Prepare update data
            update_data = {
                'last_updated_from_wasender': datetime.now(timezone.utc).isoformat(),
                'wasender_sync_status': 'synced'
            }
            
            # Only update name if we have a valid name from WASender
            if contact_info.get('name'):
                update_data['name'] = contact_info['name']
            
            # Add other WASender specific fields
            if contact_info.get('profile_image_url'):
                update_data['profile_image_url'] = contact_info['profile_image_url']
            
            if contact_info.get('whatsapp_status'):
                update_data['whatsapp_status'] = contact_info['whatsapp_status']
            
            if contact_info.get('is_business'):
                update_data['is_business_account'] = contact_info['is_business']
            
            if contact_info.get('verified_name'):
                update_data['verified_name'] = contact_info['verified_name']
            
            if existing_contact:
                # Update existing contact
                result = supabase.client.table('contacts')\
                    .update(update_data)\
                    .eq('id', existing_contact['id'])\
                    .execute()
                
                if result.data:
                    logger.debug(f"Updated contact {phone_number} with WASender data")
                    return True
            else:
                # Create new contact
                update_data.update({
                    'phone_number': f"{phone_number}_s_whatsapp_net",  # Standardize format for new contacts
                    'lead_status': 'new',
                    'lead_score': 0,
                    'source': 'wasender_sync',
                    'created_at': datetime.now(timezone.utc).isoformat()
                })
                
                result = supabase.client.table('contacts')\
                    .insert(update_data)\
                    .execute()
                
                if result.data:
                    logger.debug(f"Created new contact {phone_number} from WASender")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error updating contact in database: {e}")
            return False
    
    def sync_all_contacts(self) -> Dict[str, int]:
        """
        Sync all contacts from WASender API to local database.
        
        Returns:
            Dictionary with sync statistics
        """
        logger.info("Starting WASender contact sync...")
        
        if not self.is_configured():
            logger.error("WASender API not configured, skipping sync")
            return {'error': 'WASender API not configured'}
        
        # Fetch contacts from WASender
        wasender_contacts = self.fetch_contacts_from_wasender()
        
        if not wasender_contacts:
            logger.warning("No contacts fetched from WASender API")
            return {'error': 'No contacts fetched from WASender API'}
        
        # Process each contact
        stats = {
            'total_fetched': len(wasender_contacts),
            'successful_updates': 0,
            'failed_updates': 0,
            'contacts_with_names': 0,
            'contacts_without_names': 0
        }
        
        for wasender_contact in wasender_contacts:
            try:
                # Extract contact information
                contact_info = self.extract_contact_info(wasender_contact)
                
                if not contact_info.get('phone_number'):
                    stats['failed_updates'] += 1
                    continue
                
                # Track contacts with/without names
                if contact_info.get('name'):
                    stats['contacts_with_names'] += 1
                else:
                    stats['contacts_without_names'] += 1
                
                # Update in database
                if self.update_contact_in_database(contact_info):
                    stats['successful_updates'] += 1
                else:
                    stats['failed_updates'] += 1
                
                # Small delay to avoid overwhelming the database
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error processing contact: {e}")
                stats['failed_updates'] += 1
        
        logger.info(f"WASender contact sync completed: {stats}")
        return stats
    
    def sync_single_contact(self, phone_number: str) -> Optional[Dict]:
        """
        Sync a single contact by phone number.
        
        Args:
            phone_number: Phone number to sync
            
        Returns:
            Contact information if found, None otherwise
        """
        if not self.is_configured():
            logger.error("WASender API not configured")
            return None
        
        # Fetch all contacts and find the specific one
        wasender_contacts = self.fetch_contacts_from_wasender()
        
        normalized_phone = self.normalize_phone_number(phone_number)
        
        for wasender_contact in wasender_contacts:
            contact_jid = wasender_contact.get('id', wasender_contact.get('jid', ''))
            contact_phone = self.normalize_phone_number(contact_jid)
            
            if contact_phone == normalized_phone:
                contact_info = self.extract_contact_info(wasender_contact)
                if self.update_contact_in_database(contact_info):
                    logger.info(f"Successfully synced contact {phone_number}")
                    return contact_info
                break
        
        logger.warning(f"Contact {phone_number} not found in WASender contacts")
        return None

    def start_periodic_sync(self, interval_hours: int = 6):
        """
        Start periodic contact sync in background.
        
        Args:
            interval_hours: Hours between sync operations
        """
        if not self.is_configured():
            logger.warning("WASender API not configured, periodic sync disabled")
            return
        
        def sync_job():
            try:
                logger.info("Starting periodic WASender contact sync...")
                stats = self.sync_all_contacts()
                logger.info(f"Periodic sync completed: {stats}")
            except Exception as e:
                logger.error(f"Periodic sync failed: {e}")
        
        # Schedule the sync job
        schedule.every(interval_hours).hours.do(sync_job)
        
        # Run scheduler in background thread
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        
        logger.info(f"Periodic WASender contact sync started (every {interval_hours} hours)")
    
    def sync_contacts_for_conversations(self, conversation_ids: List[str] = None) -> Dict[str, int]:
        """
        Sync contacts specifically for active conversations.
        
        Args:
            conversation_ids: List of conversation IDs to sync, or None for all
            
        Returns:
            Dictionary with sync statistics
        """
        try:
            supabase = get_supabase_manager()
            if not supabase.is_connected():
                return {'error': 'Database not connected'}
            
            # Get conversations to sync
            query = supabase.client.table('conversations')\
                .select('id, contacts!inner(phone_number, name)')
            
            if conversation_ids:
                query = query.in_('id', conversation_ids)
            else:
                # Only sync recent conversations (last 30 days)
                thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
                query = query.gte('last_message_at', thirty_days_ago)
            
            conversations = query.execute()
            
            if not conversations.data:
                return {'error': 'No conversations found'}
            
            # Extract unique phone numbers
            phone_numbers = set()
            for conv in conversations.data:
                phone = conv['contacts']['phone_number']
                if phone:
                    clean_phone = self.normalize_phone_number(phone)
                    phone_numbers.add(clean_phone)
            
            # Sync each phone number
            stats = {
                'total_conversations': len(conversations.data),
                'unique_phone_numbers': len(phone_numbers),
                'successful_syncs': 0,
                'failed_syncs': 0,
                'contacts_updated': 0
            }
            
            for phone in phone_numbers:
                try:
                    contact_info = self.sync_single_contact(phone)
                    if contact_info:
                        stats['successful_syncs'] += 1
                        if contact_info.get('name'):
                            stats['contacts_updated'] += 1
                    else:
                        stats['failed_syncs'] += 1
                except Exception as e:
                    logger.error(f"Failed to sync contact {phone}: {e}")
                    stats['failed_syncs'] += 1
            
            logger.info(f"Conversation contact sync completed: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error syncing conversation contacts: {e}")
            return {'error': str(e)}

# Global service instance
wasender_contact_service = WASenderContactService()

# Enhanced global service instance with auto-start option
def get_wasender_contact_service(auto_start_periodic: bool = False) -> WASenderContactService:
    """
    Get the global WASender contact service instance.
    
    Args:
        auto_start_periodic: Whether to start periodic sync automatically
        
    Returns:
        WASenderContactService instance
    """
    global wasender_contact_service
    
    if auto_start_periodic and wasender_contact_service.is_configured():
        try:
            wasender_contact_service.start_periodic_sync(interval_hours=6)
        except Exception as e:
            logger.error(f"Failed to start periodic sync: {e}")
    
    return wasender_contact_service 