"""
Supabase Client Configuration and Database Operations
===================================================
Handles all database interactions for the WhatsApp Bot using Supabase.

Author: Rian Infotech
Version: 1.0
"""

import os
import json
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Tuple, Any

from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# In-memory cache for bot messages when database tracking is unavailable
_bot_message_cache = {}
_cache_max_size = 1000  # Prevent memory bloat

# ============================================================================
# SUPABASE CONFIGURATION
# ============================================================================

class SupabaseManager:
    """Manages Supabase database operations for the WhatsApp bot."""
    
    def __init__(self):
        """Initialize Supabase client."""
        self.url = os.getenv('SUPABASE_URL')
        self.key = os.getenv('SUPABASE_ANON_KEY')
        
        if not self.url or not self.key:
            logger.error("Supabase URL or API key not found in environment variables")
            self.client = None
        else:
            try:
                self.client: Client = create_client(self.url, self.key)
                logger.info("Supabase client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {e}")
                self.client = None
    
    def is_connected(self) -> bool:
        """Check if Supabase client is properly connected."""
        return self.client is not None
    
    def execute_raw_sql(self, query: str, params: tuple = None) -> List[Dict]:
        """
        Execute raw SQL query with parameters.
        
        Args:
            query: SQL query string with %s placeholders
            params: Tuple of parameters for the query
            
        Returns:
            List of dictionaries representing query results
        """
        if not self.client:
            logger.error("Supabase client not available")
            return []
        
        try:
            # Use the rpc function to execute raw SQL
            # Convert parameterized query to use Supabase RPC functions
            
            logger.debug(f"Executing raw SQL: {query[:100]}... with params: {params}")
            
            if params:
                if len(params) == 1 and 'WHERE u.email = %s' in query:
                    # Login query
                    logger.debug(f"Calling get_user_with_tenant with email: {params[0]}")
                    result = self.client.rpc('get_user_with_tenant', {'email_param': params[0]}).execute()
                    logger.debug(f"Login query result: {result.data}")
                    return result.data or []
                elif len(params) == 2 and ('WHERE u.id = %s AND t.id = %s' in query or 'users u' in query and 'tenants t' in query):
                    # Token verification query (broader pattern matching)
                    logger.debug(f"Calling get_user_by_ids with user_id: {params[0]}, tenant_id: {params[1]}")
                    result = self.client.rpc('get_user_by_ids', {
                        'user_id_param': params[0],
                        'tenant_id_param': params[1]
                    }).execute()
                    logger.debug(f"Token verification query result: {result.data}")
                    return result.data or []
            
            # Handle RAG-specific queries
            if 'knowledge_documents' in query and 'embedding <=> %s::vector' in query:
                # This is a RAG similarity search query
                logger.debug("Executing RAG similarity search query")
                return self._execute_rag_similarity_query(query, params)
            elif 'knowledge_documents' in query and 'COUNT(*)' in query:
                # This is a RAG stats query
                logger.debug("Executing RAG stats query")
                return self._execute_rag_stats_query(query, params)
            elif 'rag_query_logs' in query:
                # This is a RAG analytics query
                logger.debug("Executing RAG analytics query")
                return self._execute_rag_analytics_query(query, params)
            
            # Fallback - return empty for now
            logger.warning(f"Raw SQL execution not fully implemented for query: {query[:100]}...")
            return []
            
        except Exception as e:
            logger.error(f"Error executing raw SQL: {e}")
            return []
    
    def _execute_rag_similarity_query(self, query: str, params: tuple) -> List[Dict]:
        """Execute RAG similarity search using pgvector"""
        try:
            if len(params) >= 3:
                query_embedding = params[0]  # The embedding vector
                similarity_threshold = params[2]  # The similarity threshold
                limit = params[-1] if len(params) > 3 else 5  # The limit
                
                # Use Supabase RPC function for vector similarity
                # First, let's try the direct SQL approach
                try:
                    # Convert embedding to proper format for PostgreSQL
                    embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
                    
                    # Execute the vector similarity query using RPC
                    result = self.client.rpc('match_documents', {
                        'query_embedding': embedding_str,
                        'similarity_threshold': similarity_threshold,
                        'match_count': limit
                    }).execute()
                    
                    return result.data or []
                    
                except Exception as rpc_error:
                    logger.warning(f"RPC call failed, trying direct query: {rpc_error}")
                    
                    # Fallback to getting all documents and computing similarity in Python
                    result = self.client.table('knowledge_documents')\
                        .select('content, source, category, title, metadata, embedding')\
                        .execute()
                    
                    documents = result.data or []
                    
                    # Compute cosine similarity in Python
                    import numpy as np
                    
                    scored_docs = []
                    query_vec = np.array(query_embedding, dtype=float)
                    
                    for doc in documents:
                        if doc.get('embedding'):
                            try:
                                # Handle different embedding formats
                                embedding = doc['embedding']
                                if isinstance(embedding, str):
                                    # Parse string representation of array
                                    embedding = eval(embedding) if embedding.startswith('[') else embedding
                                
                                doc_vec = np.array(embedding, dtype=float)
                                
                                # Cosine similarity: dot product / (norm1 * norm2)
                                similarity = np.dot(query_vec, doc_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(doc_vec))
                                
                                if similarity > similarity_threshold:
                                    doc['similarity_score'] = float(similarity)
                                    # Remove embedding from response to save space
                                    doc.pop('embedding', None)
                                    scored_docs.append(doc)
                                    
                            except Exception as embed_error:
                                logger.warning(f"Error processing embedding for {doc.get('source', 'unknown')}: {embed_error}")
                                continue
                    
                    # Sort by similarity score (highest first) and limit
                    scored_docs.sort(key=lambda x: x['similarity_score'], reverse=True)
                    return scored_docs[:limit]
                
        except Exception as e:
            logger.error(f"Error executing RAG similarity query: {e}")
            return []
    
    def _execute_rag_stats_query(self, query: str, params: tuple) -> List[Dict]:
        """Execute RAG statistics query"""
        try:
            # Get basic stats from knowledge_documents table
            result = self.client.table('knowledge_documents')\
                .select('category, content, updated_at', count='exact')\
                .execute()
            
            documents = result.data or []
            total_docs = len(documents)
            
            if total_docs == 0:
                return [{'total_documents': 0, 'total_categories': 0, 'last_updated': None, 'avg_content_length': 0}]
            
            # Calculate stats
            categories = set(doc.get('category', 'unknown') for doc in documents)
            total_categories = len(categories)
            
            # Get latest update
            latest_update = max((doc.get('updated_at') for doc in documents if doc.get('updated_at')), default=None)
            
            # Calculate average content length
            content_lengths = [len(doc.get('content', '')) for doc in documents]
            avg_content_length = sum(content_lengths) / len(content_lengths) if content_lengths else 0
            
            return [{
                'total_documents': total_docs,
                'total_categories': total_categories,
                'last_updated': latest_update,
                'avg_content_length': avg_content_length
            }]
            
        except Exception as e:
            logger.error(f"Error executing RAG stats query: {e}")
            return []
    
    def _execute_rag_analytics_query(self, query: str, params: tuple) -> List[Dict]:
        """Execute RAG analytics query"""
        try:
            # Get analytics from rag_query_logs table
            result = self.client.table('rag_query_logs')\
                .select('*')\
                .order('created_at', desc=True)\
                .limit(100)\
                .execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error executing RAG analytics query: {e}")
            return []
    
    @property
    def supabase(self) -> Client:
        """Get the Supabase client instance."""
        return self.client

    # ========================================================================
    # CONTACT MANAGEMENT
    # ========================================================================
    
    def get_customer_context_by_phone(self, phone_number: str) -> Optional[Dict]:
        """
        Get comprehensive customer context for AI conversations.
        
        Args:
            phone_number: WhatsApp phone number (with or without @s.whatsapp.net)
            
        Returns:
            Dictionary with customer context or None if not found
        """
        if not self.client:
            logger.error("Supabase client not available")
            return None
        
        try:
            # Try multiple phone number formats
            base_phone = phone_number.replace('@s.whatsapp.net', '').replace('_s_whatsapp_net', '')
            
            # Try different formats: base, with _s_whatsapp_net suffix
            phone_formats = [
                base_phone,
                f"{base_phone}_s_whatsapp_net"
            ]
            
            contact_result = None
            for phone_format in phone_formats:
                contact_result = self.client.table('contacts')\
                    .select('id, phone_number, name, email, company, position, lead_status, lead_score, source, notes, last_contacted_at, next_follow_up_at, created_at')\
                    .eq('phone_number', phone_format)\
                    .execute()
                
                if contact_result.data:
                    logger.debug(f"Found contact with phone format: {phone_format}")
                    break
            
            if not contact_result or not contact_result.data:
                # No contact found - return basic context
                return {
                    'phone_number': phone_number,
                    'name': None,
                    'is_new_customer': True,
                    'context_summary': f"New customer from {phone_number}"
                }
            
            contact = contact_result.data[0]
            contact_id = contact['id']
            
            # Get recent deals
            deals_result = self.client.table('deals')\
                .select('title, value, currency, stage, probability, expected_close_date')\
                .eq('contact_id', contact_id)\
                .order('created_at', desc=True)\
                .limit(3)\
                .execute()
            
            # Get pending tasks
            tasks_result = self.client.table('tasks')\
                .select('title, description, due_date, priority')\
                .eq('contact_id', contact_id)\
                .eq('status', 'pending')\
                .order('due_date')\
                .limit(3)\
                .execute()
            
            # Get recent activities
            activities_result = self.client.table('activities')\
                .select('activity_type, title, description, created_at')\
                .eq('contact_id', contact_id)\
                .order('created_at', desc=True)\
                .limit(3)\
                .execute()
            
            # Build comprehensive context
            context = {
                'phone_number': phone_number,
                'contact_id': contact_id,
                'name': contact.get('name'),
                'email': contact.get('email'),
                'company': contact.get('company'),
                'position': contact.get('position'),
                'lead_status': contact.get('lead_status', 'new'),
                'lead_score': contact.get('lead_score', 0),
                'source': contact.get('source'),
                'notes': contact.get('notes'),
                'last_contacted_at': contact.get('last_contacted_at'),
                'next_follow_up_at': contact.get('next_follow_up_at'),
                'is_new_customer': False,
                'deals': deals_result.data or [],
                'pending_tasks': tasks_result.data or [],
                'recent_activities': activities_result.data or []
            }
            
            # Generate context summary for AI
            context['context_summary'] = self._generate_customer_context_summary(context)
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting customer context for {phone_number}: {e}")
            return None
    
    def _generate_customer_context_summary(self, context: Dict) -> str:
        """Generate a human-readable context summary for AI."""
        summary_parts = []
        
        # Basic info
        if context.get('name'):
            summary_parts.append(f"Customer: {context['name']}")
        else:
            summary_parts.append(f"Customer: {context['phone_number']}")
        
        if context.get('company'):
            summary_parts.append(f"Company: {context['company']}")
        
        if context.get('position'):
            summary_parts.append(f"Position: {context['position']}")
        
        # Lead status and score
        lead_status = context.get('lead_status', 'new')
        lead_score = context.get('lead_score', 0)
        summary_parts.append(f"Lead Status: {lead_status.title()} (Score: {lead_score}/100)")
        
        # Recent deals
        deals = context.get('deals', [])
        if deals:
            deal_info = []
            for deal in deals[:2]:  # Show top 2 deals
                value = deal.get('value', 0)
                currency = deal.get('currency', 'USD')
                stage = deal.get('stage', 'unknown')
                deal_info.append(f"{deal.get('title', 'Untitled Deal')} ({currency} {value:,.0f} - {stage})")
            summary_parts.append(f"Active Deals: {'; '.join(deal_info)}")
        
        # Pending tasks
        tasks = context.get('pending_tasks', [])
        if tasks:
            task_info = []
            for task in tasks[:2]:  # Show top 2 tasks
                task_info.append(f"{task.get('title', 'Untitled Task')} (Due: {task.get('due_date', 'No date')})")
            summary_parts.append(f"Pending Tasks: {'; '.join(task_info)}")
        
        # Notes
        if context.get('notes'):
            notes = context['notes'][:200]  # Limit notes length
            if len(context['notes']) > 200:
                notes += "..."
            summary_parts.append(f"Notes: {notes}")
        
        # Follow-up
        if context.get('next_follow_up_at'):
            summary_parts.append(f"Next Follow-up: {context['next_follow_up_at']}")
        
        return " | ".join(summary_parts)
    
    def get_or_create_contact(self, phone_number: str, name: str = None, 
                             email: str = None, tags: List[str] = None) -> Optional[Dict]:
        """
        Get existing contact or create new one.
        
        Args:
            phone_number: WhatsApp phone number
            name: Contact name (optional)
            email: Contact email (optional)
            tags: List of tags (optional)
            
        Returns:
            Contact record or None if error
        """
        if not self.client:
            logger.error("Supabase client not available")
            return None
        
        try:
            # Clean phone number
            clean_number = phone_number.split('@')[0] if '@' in phone_number else phone_number
            
            # Try to get existing contact
            result = self.client.table('contacts').select('*').eq('phone_number', clean_number).execute()
            
            if result.data:
                # Contact exists, return it
                return result.data[0]
            
            # Create new contact
            contact_data = {
                'phone_number': clean_number,
                'name': name,
                'email': email,
                'tags': tags or []
            }
            
            result = self.client.table('contacts').insert(contact_data).execute()
            
            if result.data:
                logger.info(f"Created new contact: {clean_number}")
                return result.data[0]
            else:
                logger.error(f"Failed to create contact: {clean_number}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting/creating contact {phone_number}: {e}")
            return None
    
    def update_contact(self, contact_id: str, **kwargs) -> bool:
        """
        Update contact information.
        
        Args:
            contact_id: UUID of the contact
            **kwargs: Fields to update
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            return False
        
        try:
            result = self.client.table('contacts').update(kwargs).eq('id', contact_id).execute()
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error updating contact {contact_id}: {e}")
            return False
    
    def get_contacts(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        Get contacts with pagination.
        
        Args:
            limit: Maximum number of contacts to return
            offset: Number of contacts to skip
            
        Returns:
            List of contact records
        """
        if not self.client:
            return []
        
        try:
            result = self.client.table('contacts')\
                .select('*')\
                .order('created_at', desc=True)\
                .range(offset, offset + limit - 1)\
                .execute()
            
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting contacts: {e}")
            return []

    # ========================================================================
    # CONVERSATION MANAGEMENT
    # ========================================================================
    
    def load_conversation_history(self, phone_number: str) -> List[Dict[str, str]]:
        """
        Load conversation history for a phone number.
        
        Args:
            phone_number: WhatsApp phone number
            
        Returns:
            List of conversation messages in OpenAI format
        """
        if not self.client:
            return []
        
        try:
            # Get or create contact
            contact = self.get_or_create_contact(phone_number)
            if not contact:
                return []
            
            # Get conversation
            result = self.client.table('conversations')\
                .select('messages')\
                .eq('contact_id', contact['id'])\
                .execute()
            
            if result.data:
                messages = result.data[0].get('messages', [])
                # Convert to OpenAI format if needed
                return [
                    {'role': msg['role'], 'content': msg['content']}
                    for msg in messages
                    if 'role' in msg and 'content' in msg
                ]
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error loading conversation for {phone_number}: {e}")
            return []
    
    def save_conversation_history(self, phone_number: str, 
                                 messages: List[Dict[str, str]]) -> bool:
        """
        Save conversation history for a phone number.
        
        Args:
            phone_number: WhatsApp phone number
            messages: List of messages in OpenAI format
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            return False
        
        try:
            # Get or create contact
            contact = self.get_or_create_contact(phone_number)
            if not contact:
                return False
            
            # Add timestamps and status to messages
            timestamped_messages = []
            for msg in messages:
                timestamped_msg = {
                    'role': msg['role'],
                    'content': msg['content'],
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'status': msg.get('status', 'sent'),  # Default status
                    'message_id': msg.get('message_id')  # Store message ID if available
                }
                timestamped_messages.append(timestamped_msg)
            
            # Check if conversation exists
            result = self.client.table('conversations')\
                .select('id')\
                .eq('contact_id', contact['id'])\
                .execute()
            
            conversation_data = {
                'contact_id': contact['id'],
                'messages': timestamped_messages,
                'last_message_at': datetime.now(timezone.utc).isoformat()
            }
            
            if result.data:
                # Update existing conversation
                update_result = self.client.table('conversations')\
                    .update(conversation_data)\
                    .eq('contact_id', contact['id'])\
                    .execute()
                success = bool(update_result.data)
            else:
                # Create new conversation
                create_result = self.client.table('conversations')\
                    .insert(conversation_data)\
                    .execute()
                success = bool(create_result.data)
            
            if success:
                logger.info(f"Saved conversation for {phone_number}")
            else:
                logger.error(f"Failed to save conversation for {phone_number}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error saving conversation for {phone_number}: {e}")
            return False

    def update_message_status(self, phone_number: str, message_id: str, status: str) -> bool:
        """
        Update the status of a specific message in conversation history.
        
        Args:
            phone_number: WhatsApp phone number
            message_id: Unique message identifier from WASender
            status: New message status (sent, delivered, read, failed)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            return False
        
        try:
            # Get contact
            contact = self.get_or_create_contact(phone_number)
            if not contact:
                return False
            
            # Get conversation
            result = self.client.table('conversations')\
                .select('id, messages')\
                .eq('contact_id', contact['id'])\
                .execute()
            
            if not result.data:
                logger.warning(f"No conversation found for {phone_number}")
                return False
            
            conversation = result.data[0]
            messages = conversation.get('messages', [])
            
            # Find and update the specific message
            updated = False
            for msg in messages:
                if msg.get('message_id') == message_id:
                    msg['status'] = status
                    msg['status_updated_at'] = datetime.now(timezone.utc).isoformat()
                    updated = True
                    break
            
            if updated:
                # Save updated messages back to conversation
                update_result = self.client.table('conversations')\
                    .update({'messages': messages})\
                    .eq('id', conversation['id'])\
                    .execute()
                
                success = bool(update_result.data)
                if success:
                    logger.info(f"Updated message {message_id} status to {status} for {phone_number}")
                else:
                    logger.error(f"Failed to update message status for {phone_number}")
                return success
            else:
                logger.warning(f"Message {message_id} not found in conversation for {phone_number}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating message status: {e}")
            return False
    
    def log_webhook_event(self, event_type: str, event_data: Dict, status: str = 'processed') -> bool:
        """
        Log webhook events for debugging and monitoring.
        
        Args:
            event_type: Type of webhook event (messages.upsert, message.sent, etc.)
            event_data: Full webhook payload
            status: Processing status (processed, failed, ignored)
            
        Returns:
            True if logged successfully, False otherwise
        """
        if not self.client:
            return False
        
        try:
            # Create webhook_events table if it doesn't exist
            webhook_log = {
                'event_type': event_type,
                'event_data': event_data,
                'status': status,
                'processed_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Try to insert, but don't fail if table doesn't exist
            try:
                result = self.client.table('webhook_events').insert(webhook_log).execute()
                return bool(result.data)
            except Exception as table_error:
                # Table might not exist, log to application logs instead
                logger.info(f"Webhook event logged to app logs (DB table not available): {event_type} - {status}")
                return True
                
        except Exception as e:
            logger.error(f"Error logging webhook event: {e}")
            return False

    def save_message_with_status(self, phone_number: str, message_content: str, 
                               role: str, message_id: str = None, status: str = 'sent') -> bool:
        """
        Save a single message with status to conversation history.
        
        Args:
            phone_number: WhatsApp phone number
            message_content: Message text content
            role: Message role (user, assistant)
            message_id: Unique message identifier from WASender
            status: Message status (sent, delivered, read, failed)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            return False
        
        try:
            # Get or create contact
            contact = self.get_or_create_contact(phone_number)
            if not contact:
                return False
            
            # Get existing conversation
            result = self.client.table('conversations')\
                .select('id, messages')\
                .eq('contact_id', contact['id'])\
                .execute()
            
            # Create new message
            new_message = {
                'role': role,
                'content': message_content,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'status': status,
                'message_id': message_id
            }
            
            if result.data:
                # Update existing conversation
                conversation = result.data[0]
                messages = conversation.get('messages', [])
                messages.append(new_message)
                
                update_result = self.client.table('conversations')\
                    .update({
                        'messages': messages,
                        'last_message_at': datetime.now(timezone.utc).isoformat()
                    })\
                    .eq('id', conversation['id'])\
                    .execute()
                success = bool(update_result.data)
            else:
                # Create new conversation
                conversation_data = {
                    'contact_id': contact['id'],
                    'messages': [new_message],
                    'last_message_at': datetime.now(timezone.utc).isoformat()
                }
                
                create_result = self.client.table('conversations')\
                    .insert(conversation_data)\
                    .execute()
                success = bool(create_result.data)
            
            if success:
                logger.info(f"Saved message with status {status} for {phone_number}")
            else:
                logger.error(f"Failed to save message for {phone_number}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error saving message with status: {e}")
            return False

    # ========================================================================
    # BOT MESSAGE TRACKING
    # ========================================================================
    
    def track_bot_sent_message(self, message_id: str, phone_number: str) -> bool:
        """
        Track a message ID that was sent by the bot to prevent loop processing.
        
        Args:
            message_id: WASender message ID from bot response
            phone_number: Phone number the message was sent to
            
        Returns:
            True if successful, False otherwise
        """
        if not message_id:
            return False
        
        # Try database tracking first
        if self.client:
            try:
                tracking_data = {
                    'message_id': message_id,
                    'phone_number': phone_number,
                    'sent_at': datetime.now(timezone.utc).isoformat(),
                    'expires_at': (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
                }
                
                result = self.client.table('bot_sent_messages').insert(tracking_data).execute()
                if result.data:
                    logger.debug(f"Tracked bot message in database: {message_id}")
                    return True
            except Exception as e:
                logger.debug(f"Database tracking failed for {message_id}, using memory cache: {e}")
        
        # Fallback to in-memory cache
        global _bot_message_cache, _cache_max_size
        
        # Clean up cache if it gets too large
        if len(_bot_message_cache) > _cache_max_size:
            # Remove oldest 20% of entries
            current_time = datetime.now(timezone.utc)
            cutoff_time = current_time - timedelta(hours=1)  # Keep only last hour
            _bot_message_cache = {
                k: v for k, v in _bot_message_cache.items() 
                if v.get('sent_at', datetime.min.replace(tzinfo=timezone.utc)) > cutoff_time
            }
        
        # Add to cache
        _bot_message_cache[message_id] = {
            'phone_number': phone_number,
            'sent_at': datetime.now(timezone.utc),
            'expires_at': datetime.now(timezone.utc) + timedelta(hours=6)  # Shorter expiry for memory
        }
        
        logger.debug(f"Tracked bot message in memory cache: {message_id}")
        return True
    
    def is_bot_sent_message(self, message_id: str) -> bool:
        """
        Check if a message ID was previously sent by the bot.
        
        Args:
            message_id: WASender message ID to check
            
        Returns:
            True if this message was sent by the bot, False otherwise
        """
        if not message_id:
            return False
        
        # Check database first
        if self.client:
            try:
                result = self.client.table('bot_sent_messages')\
                    .select('message_id')\
                    .eq('message_id', message_id)\
                    .gte('expires_at', datetime.now(timezone.utc).isoformat())\
                    .execute()
                
                if result.data:
                    logger.debug(f"Found bot message in database: {message_id}")
                    return True
            except Exception as e:
                logger.debug(f"Database check failed for {message_id}, checking memory cache: {e}")
        
        # Check in-memory cache
        global _bot_message_cache
        cached_entry = _bot_message_cache.get(message_id)
        if cached_entry:
            # Check if expired
            if cached_entry['expires_at'] > datetime.now(timezone.utc):
                logger.debug(f"Found bot message in memory cache: {message_id}")
                return True
            else:
                # Remove expired entry
                del _bot_message_cache[message_id]
                logger.debug(f"Removed expired bot message from cache: {message_id}")
        
        return False
    
    def cleanup_expired_bot_messages(self) -> int:
        """
        Clean up expired bot message tracking entries.
        
        Returns:
            Number of entries cleaned up
        """
        if not self.client:
            return 0
        
        try:
            current_time = datetime.now(timezone.utc).isoformat()
            result = self.client.table('bot_sent_messages')\
                .delete()\
                .lt('expires_at', current_time)\
                .execute()
            
            cleaned_count = len(result.data) if result.data else 0
            logger.info(f"Cleaned up {cleaned_count} expired bot message tracking entries")
            return cleaned_count
            
        except Exception as e:
            logger.debug(f"Could not cleanup expired bot messages: {e}")
            return 0

    # ========================================================================
    # BULK CAMPAIGN MANAGEMENT
    # ========================================================================
    
    def create_bulk_campaign(self, name: str, message_content: str, 
                           total_contacts: int) -> Optional[str]:
        """
        Create a new bulk messaging campaign.
        
        Args:
            name: Campaign name
            message_content: Message to send
            total_contacts: Number of contacts in campaign
            
        Returns:
            Campaign ID if successful, None otherwise
        """
        if not self.client:
            return None
        
        try:
            campaign_data = {
                'name': name,
                'message_content': message_content,
                'total_contacts': total_contacts,
                'status': 'pending',
                'started_at': datetime.now(timezone.utc).isoformat()
            }
            
            result = self.client.table('bulk_campaigns').insert(campaign_data).execute()
            
            if result.data:
                campaign_id = result.data[0]['id']
                logger.info(f"Created bulk campaign: {campaign_id}")
                return campaign_id
            else:
                logger.error("Failed to create bulk campaign")
                return None
                
        except Exception as e:
            logger.error(f"Error creating bulk campaign: {e}")
            return None
    
    def update_campaign_status(self, campaign_id: str, status: str, 
                             successful_sends: int = None, 
                             failed_sends: int = None) -> bool:
        """
        Update campaign status and statistics.
        
        Args:
            campaign_id: Campaign UUID
            status: New status (pending, running, completed, failed)
            successful_sends: Number of successful sends
            failed_sends: Number of failed sends
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            return False
        
        try:
            update_data = {'status': status}
            
            if successful_sends is not None:
                update_data['successful_sends'] = successful_sends
            
            if failed_sends is not None:
                update_data['failed_sends'] = failed_sends
            
            if status in ['completed', 'failed']:
                update_data['completed_at'] = datetime.now(timezone.utc).isoformat()
            
            result = self.client.table('bulk_campaigns')\
                .update(update_data)\
                .eq('id', campaign_id)\
                .execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error updating campaign status: {e}")
            return False
    
    def log_message_result(self, campaign_id: str, phone_number: str, 
                          success: bool, error_message: str = None) -> bool:
        """
        Log individual message delivery result.
        
        Args:
            campaign_id: Campaign UUID
            phone_number: Target phone number
            success: Whether message was sent successfully
            error_message: Error message if failed
            
        Returns:
            True if logged successfully, False otherwise
        """
        if not self.client:
            return False
        
        try:
            # Get or create contact
            contact = self.get_or_create_contact(phone_number)
            if not contact:
                return False
            
            result_data = {
                'campaign_id': campaign_id,
                'contact_id': contact['id'],
                'success': success,
                'error_message': error_message,
                'sent_at': datetime.now(timezone.utc).isoformat()
            }
            
            result = self.client.table('message_results').insert(result_data).execute()
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error logging message result: {e}")
            return False
    
    def get_campaign_summary(self, campaign_id: str) -> Optional[Dict]:
        """
        Get campaign summary with statistics.
        
        Args:
            campaign_id: Campaign UUID
            
        Returns:
            Campaign summary dict or None
        """
        if not self.client:
            return None
        
        try:
            result = self.client.table('campaign_summary')\
                .select('*')\
                .eq('id', campaign_id)\
                .execute()
            
            if result.data:
                return result.data[0]
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error getting campaign summary: {e}")
            return None
    
    def get_recent_campaigns(self, limit: int = 10) -> List[Dict]:
        """
        Get recent bulk campaigns.
        
        Args:
            limit: Maximum number of campaigns to return
            
        Returns:
            List of campaign records
        """
        if not self.client:
            return []
        
        try:
            result = self.client.table('campaign_summary')\
                .select('*')\
                .limit(limit)\
                .execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error getting recent campaigns: {e}")
            return []

    # ========================================================================
    # CRM FUNCTIONALITY
    # ========================================================================
    
    def update_contact_lead_info(self, contact_id: str, name: str = None, email: str = None,
                                lead_status: str = None, lead_score: int = None, source: str = None,
                                company: str = None, position: str = None,
                                notes: str = None, next_follow_up_at: str = None) -> bool:
        """Update contact CRM information."""
        if not self.client:
            return False
        
        try:
            update_data = {}
            if name: update_data['name'] = name
            if email: update_data['email'] = email
            if lead_status: update_data['lead_status'] = lead_status
            if lead_score is not None: update_data['lead_score'] = lead_score
            if source: update_data['source'] = source
            if company: update_data['company'] = company
            if position: update_data['position'] = position
            if notes: update_data['notes'] = notes
            if next_follow_up_at: update_data['next_follow_up_at'] = next_follow_up_at
            
            update_data['last_contacted_at'] = datetime.now(timezone.utc).isoformat()
            
            result = self.client.table('contacts').update(update_data).eq('id', contact_id).execute()
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error updating contact lead info: {e}")
            return False
    
    def create_deal(self, contact_id: str, title: str, description: str = None,
                   value: float = 0, currency: str = 'USD', stage: str = 'prospecting',
                   probability: int = 0, expected_close_date: str = None) -> Optional[str]:
        """Create a new deal."""
        if not self.client:
            return None
        
        try:
            deal_data = {
                'contact_id': contact_id,
                'title': title,
                'description': description,
                'value': value,
                'currency': currency,
                'stage': stage,
                'probability': probability
            }
            
            if expected_close_date:
                deal_data['expected_close_date'] = expected_close_date
            
            result = self.client.table('deals').insert(deal_data).execute()
            return result.data[0]['id'] if result.data else None
        except Exception as e:
            logger.error(f"Error creating deal: {e}")
            return None
    
    def update_deal(self, deal_id: str, **kwargs) -> bool:
        """Update deal information."""
        if not self.client:
            return False
        
        try:
            result = self.client.table('deals').update(kwargs).eq('id', deal_id).execute()
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error updating deal: {e}")
            return False
    
    def get_deals(self, contact_id: str = None, stage: str = None, limit: int = 50) -> List[Dict]:
        """Get deals with optional filtering."""
        if not self.client:
            return []
        
        try:
            query = self.client.table('deals').select('*, contacts!inner(name, phone_number)')
            
            if contact_id:
                query = query.eq('contact_id', contact_id)
            if stage:
                query = query.eq('stage', stage)
            
            result = query.order('created_at', desc=True).limit(limit).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting deals: {e}")
            return []
    
    def create_task(self, contact_id: str = None, deal_id: str = None, title: str = '',
                   description: str = None, task_type: str = 'follow_up',
                   priority: str = 'medium', due_date: str = None) -> Optional[str]:
        """Create a new task."""
        if not self.client:
            return None
        
        try:
            task_data = {
                'title': title,
                'description': description,
                'task_type': task_type,
                'priority': priority
            }
            
            if contact_id: task_data['contact_id'] = contact_id
            if deal_id: task_data['deal_id'] = deal_id
            if due_date: task_data['due_date'] = due_date
            
            result = self.client.table('tasks').insert(task_data).execute()
            return result.data[0]['id'] if result.data else None
        except Exception as e:
            logger.error(f"Error creating task: {e}")
            return None
    
    def get_tasks(self, contact_id: str = None, status: str = None, limit: int = 50) -> List[Dict]:
        """Get tasks with optional filtering."""
        if not self.client:
            return []
        
        try:
            query = self.client.table('tasks').select('*, contacts(name, phone_number), deals(title)')
            
            if contact_id:
                query = query.eq('contact_id', contact_id)
            if status:
                query = query.eq('status', status)
            
            result = query.order('due_date', desc=False).limit(limit).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting tasks: {e}")
            return []
    
    def complete_task(self, task_id: str) -> bool:
        """Mark a task as completed."""
        if not self.client:
            return False
        
        try:
            result = self.client.table('tasks').update({
                'status': 'completed',
                'completed_at': datetime.now(timezone.utc).isoformat()
            }).eq('id', task_id).execute()
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error completing task: {e}")
            return False
    
    def log_activity(self, contact_id: str, activity_type: str, title: str,
                    description: str = None, deal_id: str = None,
                    duration_minutes: int = None, outcome: str = None) -> bool:
        """Log an activity/interaction."""
        if not self.client:
            return False
        
        try:
            activity_data = {
                'contact_id': contact_id,
                'activity_type': activity_type,
                'title': title,
                'description': description
            }
            
            if deal_id: activity_data['deal_id'] = deal_id
            if duration_minutes: activity_data['duration_minutes'] = duration_minutes
            if outcome: activity_data['outcome'] = outcome
            
            result = self.client.table('activities').insert(activity_data).execute()
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error logging activity: {e}")
            return False
    
    def get_contact_activities(self, contact_id: str, limit: int = 20) -> List[Dict]:
        """Get activities for a contact."""
        if not self.client:
            return []
        
        try:
            result = self.client.table('activities')\
                .select('*')\
                .eq('contact_id', contact_id)\
                .order('created_at', desc=True)\
                .limit(limit)\
                .execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting contact activities: {e}")
            return []
    
    def calculate_lead_score(self, contact_id: str) -> int:
        """Calculate and update lead score for a contact."""
        if not self.client:
            return 0
        
        try:
            # Get contact info
            contact = self.client.table('contacts').select('*').eq('id', contact_id).execute()
            if not contact.data:
                return 0
            
            contact_data = contact.data[0]
            score = 0
            
            # Get scoring rules
            rules = self.client.table('lead_scoring_rules').select('*').eq('is_active', True).execute()
            
            for rule in rules.data or []:
                field = rule['condition_field']
                operator = rule['condition_operator']
                value = rule['condition_value']
                points = rule['score_points']
                
                # Simple scoring logic (can be enhanced)
                if field == 'email' and operator == 'is_not_null' and contact_data.get('email'):
                    score += points
                elif field == 'company' and operator == 'is_not_null' and contact_data.get('company'):
                    score += points
                # Add more conditions as needed
            
            # Update contact with new score
            self.client.table('contacts').update({'lead_score': score}).eq('id', contact_id).execute()
            
            return score
        except Exception as e:
            logger.error(f"Error calculating lead score: {e}")
            return 0
    
    def get_crm_dashboard_stats(self) -> Dict[str, Any]:
        """Get CRM-specific dashboard statistics."""
        if not self.client:
            return {}
        
        try:
            stats = {}
            
            # Lead status breakdown
            lead_stats = self.client.table('contacts')\
                .select('lead_status')\
                .execute()
            
            lead_breakdown = {}
            for contact in lead_stats.data or []:
                status = contact.get('lead_status', 'new')
                lead_breakdown[status] = lead_breakdown.get(status, 0) + 1
            
            stats['lead_breakdown'] = lead_breakdown
            
            # Deal pipeline
            deal_stats = self.client.table('deals')\
                .select('stage, value')\
                .execute()
            
            pipeline_value = {}
            for deal in deal_stats.data or []:
                stage = deal.get('stage', 'prospecting')
                value = float(deal.get('value', 0))
                pipeline_value[stage] = pipeline_value.get(stage, 0) + value
            
            stats['pipeline_value'] = pipeline_value
            
            # Pending tasks
            pending_tasks = self.client.table('tasks')\
                .select('id')\
                .eq('status', 'pending')\
                .execute()
            
            stats['pending_tasks'] = len(pending_tasks.data or [])
            
            # High-value deals
            high_value_deals = self.client.table('deals')\
                .select('id')\
                .gte('value', 1000)\
                .execute()
            
            stats['high_value_deals'] = len(high_value_deals.data or [])
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting CRM dashboard stats: {e}")
            return {}

    # ========================================================================
    # ANALYTICS & REPORTING
    # ========================================================================
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """
        Get dashboard statistics.
        
        Returns:
            Dictionary with various statistics
        """
        if not self.client:
            return {}
        
        try:
            stats = {}
            
            # Total contacts
            contacts_result = self.client.table('contacts').select('id', count='exact').execute()
            stats['total_contacts'] = contacts_result.count or 0
            
            # Total conversations
            conversations_result = self.client.table('conversations').select('id', count='exact').execute()
            stats['total_conversations'] = conversations_result.count or 0
            
            # Total campaigns
            campaigns_result = self.client.table('bulk_campaigns').select('id', count='exact').execute()
            stats['total_campaigns'] = campaigns_result.count or 0
            
            # Recent activity (last 24 hours)
            yesterday = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            recent_messages = self.client.table('message_results')\
                .select('id', count='exact')\
                .gte('sent_at', yesterday.isoformat())\
                .execute()
            stats['messages_today'] = recent_messages.count or 0
            
            # Add CRM stats
            crm_stats = self.get_crm_dashboard_stats()
            stats.update(crm_stats)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {e}")
            return {}

# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

# Create global Supabase manager instance
supabase_manager = SupabaseManager()

def get_supabase_manager() -> SupabaseManager:
    """Get the global Supabase manager instance."""
    return supabase_manager 