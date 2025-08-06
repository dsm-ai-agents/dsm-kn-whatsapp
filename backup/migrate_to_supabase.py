"""
Migration Script: JSON to Supabase
================================
Migrate existing conversation histories and bulk campaign logs from JSON files to Supabase.

Author: Rian Infotech
Version: 1.0
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict

from supabase_client import get_supabase_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_conversation_histories():
    """Migrate all conversation JSON files to Supabase."""
    conversations_dir = 'conversations'
    supabase = get_supabase_manager()
    
    if not supabase.is_connected():
        logger.error("Supabase not connected. Cannot migrate conversations.")
        return False
    
    if not os.path.exists(conversations_dir):
        logger.warning(f"Conversations directory {conversations_dir} not found.")
        return True
    
    migrated_count = 0
    error_count = 0
    
    logger.info("Starting conversation history migration...")
    
    for filename in os.listdir(conversations_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(conversations_dir, filename)
            
            try:
                # Extract phone number from filename
                # Format: {phone_number}_s_whatsapp_net.json
                phone_number = filename.replace('_s_whatsapp_net.json', '').replace('.json', '')
                
                # Load conversation data
                with open(filepath, 'r', encoding='utf-8') as file:
                    conversation_data = json.load(file)
                
                # Validate data format
                if isinstance(conversation_data, list):
                    # Save to Supabase
                    if supabase.save_conversation_history(phone_number, conversation_data):
                        migrated_count += 1
                        logger.info(f"✓ Migrated conversation: {phone_number}")
                    else:
                        error_count += 1
                        logger.error(f"✗ Failed to migrate conversation: {phone_number}")
                else:
                    error_count += 1
                    logger.error(f"✗ Invalid conversation format in {filename}")
                    
            except Exception as e:
                error_count += 1
                logger.error(f"✗ Error migrating {filename}: {e}")
    
    logger.info(f"Conversation migration completed: {migrated_count} success, {error_count} errors")
    return error_count == 0

def migrate_bulk_campaign_logs():
    """Migrate bulk campaign logs to Supabase."""
    logs_dir = 'logs'
    supabase = get_supabase_manager()
    
    if not supabase.is_connected():
        logger.error("Supabase not connected. Cannot migrate campaign logs.")
        return False
    
    if not os.path.exists(logs_dir):
        logger.warning(f"Logs directory {logs_dir} not found.")
        return True
    
    migrated_count = 0
    error_count = 0
    
    logger.info("Starting bulk campaign logs migration...")
    
    for filename in os.listdir(logs_dir):
        if filename.endswith('.json') and filename.startswith('bulk_'):
            filepath = os.path.join(logs_dir, filename)
            
            try:
                # Load log data
                with open(filepath, 'r', encoding='utf-8') as file:
                    log_data = json.load(file)
                
                # Extract campaign info
                campaign_name = f"Legacy Campaign - {filename}"
                message_content = log_data.get('message', 'Unknown message')
                total_contacts = log_data.get('total_contacts', 0)
                successful_sends = log_data.get('successful_sends', 0)
                failed_sends = log_data.get('failed_sends', 0)
                
                # Create campaign in Supabase
                campaign_id = supabase.create_bulk_campaign(
                    name=campaign_name,
                    message_content=message_content,
                    total_contacts=total_contacts
                )
                
                if campaign_id:
                    # Update campaign with final status
                    supabase.update_campaign_status(
                        campaign_id=campaign_id,
                        status='completed',
                        successful_sends=successful_sends,
                        failed_sends=failed_sends
                    )
                    
                    # Migrate individual message results if available
                    results = log_data.get('results', [])
                    for result in results:
                        contact_phone = result.get('contact', '')
                        success = result.get('success', False)
                        error_msg = result.get('error_message')
                        
                        supabase.log_message_result(
                            campaign_id=campaign_id,
                            phone_number=contact_phone,
                            success=success,
                            error_message=error_msg
                        )
                    
                    migrated_count += 1
                    logger.info(f"✓ Migrated campaign log: {filename}")
                else:
                    error_count += 1
                    logger.error(f"✗ Failed to create campaign from {filename}")
                    
            except Exception as e:
                error_count += 1
                logger.error(f"✗ Error migrating {filename}: {e}")
    
    logger.info(f"Campaign logs migration completed: {migrated_count} success, {error_count} errors")
    return error_count == 0

def create_backup_of_json_files():
    """Create backup of existing JSON files before migration."""
    backup_dir = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        os.makedirs(backup_dir, exist_ok=True)
        
        # Backup conversations
        if os.path.exists('conversations'):
            backup_conversations = os.path.join(backup_dir, 'conversations')
            os.makedirs(backup_conversations, exist_ok=True)
            
            for filename in os.listdir('conversations'):
                if filename.endswith('.json'):
                    src = os.path.join('conversations', filename)
                    dst = os.path.join(backup_conversations, filename)
                    
                    with open(src, 'r') as src_file:
                        with open(dst, 'w') as dst_file:
                            dst_file.write(src_file.read())
        
        # Backup logs
        if os.path.exists('logs'):
            backup_logs = os.path.join(backup_dir, 'logs')
            os.makedirs(backup_logs, exist_ok=True)
            
            for filename in os.listdir('logs'):
                if filename.endswith('.json'):
                    src = os.path.join('logs', filename)
                    dst = os.path.join(backup_logs, filename)
                    
                    with open(src, 'r') as src_file:
                        with open(dst, 'w') as dst_file:
                            dst_file.write(src_file.read())
        
        logger.info(f"✓ Backup created in {backup_dir}")
        return backup_dir
        
    except Exception as e:
        logger.error(f"✗ Failed to create backup: {e}")
        return None

def run_full_migration():
    """Run complete migration process."""
    logger.info("=" * 60)
    logger.info("RIAN INFOTECH WHATSAPP BOT - SUPABASE MIGRATION")
    logger.info("=" * 60)
    
    # Check Supabase connection
    supabase = get_supabase_manager()
    if not supabase.is_connected():
        logger.error("❌ Supabase connection failed. Please check your credentials.")
        return False
    
    logger.info("✅ Supabase connection verified")
    
    # Create backup
    logger.info("\n1. Creating backup of existing JSON files...")
    backup_dir = create_backup_of_json_files()
    if not backup_dir:
        logger.error("❌ Backup creation failed. Aborting migration.")
        return False
    
    # Migrate conversations
    logger.info("\n2. Migrating conversation histories...")
    conversations_success = migrate_conversation_histories()
    
    # Migrate bulk campaigns
    logger.info("\n3. Migrating bulk campaign logs...")
    campaigns_success = migrate_bulk_campaign_logs()
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("MIGRATION SUMMARY")
    logger.info("=" * 60)
    
    if conversations_success and campaigns_success:
        logger.info("✅ Migration completed successfully!")
        logger.info(f"📁 Backup created: {backup_dir}")
        logger.info("🚀 Your bot is now powered by Supabase!")
        return True
    else:
        logger.error("❌ Migration completed with errors.")
        logger.info("💡 Check the logs above for details.")
        logger.info(f"📁 Your original data is safely backed up in: {backup_dir}")
        return False

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check for required environment variables
    required_vars = ['SUPABASE_URL', 'SUPABASE_ANON_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        logger.info("💡 Please add them to your .env file:")
        logger.info("   SUPABASE_URL=your_supabase_project_url")
        logger.info("   SUPABASE_ANON_KEY=your_supabase_anon_key")
        exit(1)
    
    # Run migration
    success = run_full_migration()
    exit(0 if success else 1) 