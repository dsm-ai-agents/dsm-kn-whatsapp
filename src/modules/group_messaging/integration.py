"""
Group Messaging Integration
===========================
Integrates the group messaging module with the main Flask application.
"""

import logging
import os
from flask import Flask
from typing import Optional

from .api.routes import create_group_messaging_blueprint
from .config.settings import GroupMessagingConfig

logger = logging.getLogger(__name__)


def integrate_group_messaging(app: Flask, supabase_client) -> bool:
    """
    Integrate group messaging module with Flask application.
    
    Args:
        app: Flask application instance
        supabase_client: Existing Supabase client
        
    Returns:
        True if integration successful, False otherwise
    """
    try:
        # Get Wasender API token from environment or config
        wasender_api_token = os.getenv('WASENDER_API_TOKEN')
        
        if not wasender_api_token:
            logger.error("WASENDER_API_TOKEN environment variable is required")
            return False
        
        # Create and register blueprint
        group_messaging_bp = create_group_messaging_blueprint(
            supabase_client=supabase_client,
            wasender_api_token=wasender_api_token
        )
        
        app.register_blueprint(group_messaging_bp)
        
        logger.info("Group messaging module integrated successfully")
        logger.info("Available endpoints:")
        logger.info("  GET    /api/group-messaging/groups")
        logger.info("  POST   /api/group-messaging/groups")
        logger.info("  POST   /api/group-messaging/groups/<group_jid>/send-message")
        logger.info("  POST   /api/group-messaging/bulk-send")
        logger.info("  POST   /api/group-messaging/schedule-message")
        logger.info("  GET    /api/group-messaging/scheduled-messages")
        logger.info("  DELETE /api/group-messaging/scheduled-messages/<message_id>")
        logger.info("  GET    /api/group-messaging/groups/<group_jid>/messages")
        logger.info("  POST   /api/group-messaging/process-scheduled")
        logger.info("  GET    /api/group-messaging/contacts")
        logger.info("  GET    /api/group-messaging/contacts/database")
        logger.info("  GET    /api/group-messaging/contacts/search")
        logger.info("  POST   /api/group-messaging/groups/create-with-contacts")
        logger.info("  GET    /api/group-messaging/health")
        
        # Setup background scheduler for automatic message processing
        background_job = setup_scheduler_background_job(app, supabase_client)
        
        if background_job:
            logger.info("✅ Background scheduler started for automatic message processing")
        else:
            logger.warning("⚠️ Background scheduler failed to start - scheduled messages won't be processed automatically")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to integrate group messaging module: {e}")
        return False


def setup_scheduler_background_job(app: Flask, supabase_client) -> Optional[object]:
    """
    Setup background job for processing scheduled messages using APScheduler.
    
    Args:
        app: Flask application instance
        supabase_client: Existing Supabase client
        
    Returns:
        APScheduler BackgroundScheduler instance or None
    """
    import os
    
    # Skip scheduler in production if workers > 1 to avoid conflicts
    workers = int(os.getenv('WEB_CONCURRENCY', '1'))
    if workers > 1:
        logger.info("⚠️ Multiple workers detected - skipping background scheduler to avoid conflicts")
        logger.info("📝 Use manual API endpoint /api/group-messaging/process-scheduled or external cron")
        return None
    
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from .services.scheduler_service import SchedulerService
        from .services.group_service import GroupService
        from .services.database_service import DatabaseService
        from .config.settings import GroupMessagingConfig
        
        # Get configuration from environment
        config = GroupMessagingConfig.from_env()
        
        # Check if scheduler is explicitly disabled
        if not config.scheduler_enabled:
            logger.info("📝 Scheduler disabled in configuration")
            return None
        
        # Create scheduler instance with better error handling
        scheduler = BackgroundScheduler(
            timezone='UTC',
            job_defaults={
                'coalesce': True,
                'max_instances': 1,
                'misfire_grace_time': 30
            }
        )
        
        def process_scheduled_messages():
            """Process pending scheduled messages in Flask app context."""
            try:
                with app.app_context():
                    # Initialize services
                    group_service = GroupService(config)
                    db_service = DatabaseService(supabase_client)
                    scheduler_service = SchedulerService(group_service, db_service)
                    
                    # Process pending messages
                    processed_count = scheduler_service.process_pending_messages()
                    
                    if processed_count > 0:
                        logger.info(f"✅ Processed {processed_count} scheduled messages")
                    else:
                        logger.debug("No scheduled messages to process")
                        
            except Exception as e:
                error_msg = str(e).lower()
                
                # Handle connection errors more gracefully
                if any(error in error_msg for error in [
                    'connection reset by peer',
                    'connection timeout',
                    'connection refused',
                    'network error',
                    'timeout'
                ]):
                    logger.warning(f"⚠️ Database connection issue during scheduled message processing: {e}")
                    logger.info("Will retry on next scheduled run...")
                else:
                    logger.error(f"❌ Error processing scheduled messages: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
        
        # Add job to run every 5 minutes (reduced frequency to prevent connection issues)
        scheduler.add_job(
            func=process_scheduled_messages,
            trigger="interval",
            minutes=5,
            id='process_scheduled_messages',
            name='Process Scheduled WhatsApp Messages'
        )
        
        # Add handover rescue job to run every 5 minutes
        def process_handover_rescue():
            """Process abandoned handover requests in Flask app context."""
            try:
                with app.app_context():
                    # Import here to avoid circular imports
                    from src.services.handover_management_service import HandoverManagementService
                    
                    # Initialize handover service with existing supabase client
                    handover_service = HandoverManagementService(supabase_client)
                    
                    # Process abandoned customers
                    results = handover_service.rescue_abandoned_customers()
                    
                    if results.get('rescued', 0) > 0 or results.get('notified', 0) > 0:
                        logger.info(f"🚨 HANDOVER RESCUE - Rescued: {results.get('rescued', 0)}, Notified: {results.get('notified', 0)}")
                    else:
                        logger.debug("No abandoned handovers to rescue")
                        
                    if results.get('errors', 0) > 0:
                        logger.warning(f"⚠️ HANDOVER RESCUE - {results.get('errors', 0)} errors occurred during rescue operation")
                        
            except Exception as e:
                error_msg = str(e).lower()
                
                # Handle connection errors more gracefully (same pattern as scheduled messages)
                if any(error in error_msg for error in [
                    'connection reset by peer',
                    'connection timeout',
                    'connection refused',
                    'network error',
                    'timeout'
                ]):
                    logger.warning(f"⚠️ Database connection issue during handover rescue: {e}")
                    logger.info("Will retry handover rescue on next scheduled run...")
                else:
                    logger.error(f"❌ Error processing handover rescue: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
        
        scheduler.add_job(
            func=process_handover_rescue,
            trigger="interval",
            minutes=2,  # More frequent for progressive 10min intervals
            id='process_handover_rescue',
            name='Progressive Handover Management'
        )
        
        # Start the scheduler with error handling
        scheduler.start()
        logger.info("🚀 APScheduler background jobs started - scheduled messages & progressive handover management running every 2 minutes")
        
        # Register shutdown handler
        import atexit
        atexit.register(lambda: scheduler.shutdown())
        
        return scheduler
        
    except ImportError as e:
        logger.warning(f"⚠️ APScheduler not available: {e}")
        logger.info("📝 Scheduled messages can be processed manually via API endpoint")
        return None
    except Exception as e:
        logger.error(f"❌ Failed to setup scheduler background job: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None 