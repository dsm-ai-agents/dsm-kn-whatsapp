"""
Bulk Messaging Module for Rian Infotech WhatsApp Bot
====================================================
Handles sending messages to multiple recipients using the individual loop method
for maximum reliability and safety.

Author: Rian Infotech
Version: 1.0
"""

import os
import json
import time
import random
import logging
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Callable
from dataclasses import dataclass, asdict
import threading
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION & CONSTANTS
# ============================================================================

# Directories
BULK_LOGS_DIR = 'logs'
CONTACTS_DIR = 'contacts'

# Rate limiting configuration (in seconds)
DEFAULT_MIN_DELAY = 2.0
DEFAULT_MAX_DELAY = 4.0

# Bulk messaging limits
MAX_CONTACTS_PER_BATCH = 100
MAX_RETRIES = 3

# Job status constants
JOB_STATUS_PENDING = 'pending'
JOB_STATUS_IN_PROGRESS = 'in_progress'
JOB_STATUS_COMPLETED = 'completed'
JOB_STATUS_CANCELLED = 'cancelled'
JOB_STATUS_FAILED = 'failed'

# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class ContactResult:
    """Result of sending message to a single contact."""
    contact: str
    success: bool
    timestamp: str
    error_message: Optional[str] = None
    retry_count: int = 0

@dataclass
class BulkJob:
    """Bulk messaging job tracking."""
    job_id: str
    message: str
    contacts: List[str]
    status: str
    total_contacts: int
    successful_sends: int = 0
    failed_sends: int = 0
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    results: List[ContactResult] = None
    
    def __post_init__(self):
        if self.results is None:
            self.results = []

# ============================================================================
# INITIALIZATION
# ============================================================================

def initialize_bulk_messaging() -> None:
    """Initialize bulk messaging directories and logging."""
    
    # Create directories if they don't exist
    for directory in [BULK_LOGS_DIR, CONTACTS_DIR]:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logger.info(f"Created directory: {directory}")

# Initialize on import
initialize_bulk_messaging()

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def generate_job_id() -> str:
    """Generate unique job ID for bulk messaging."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    random_suffix = random.randint(1000, 9999)
    return f"bulk_{timestamp}_{random_suffix}"

def validate_phone_number(phone: str) -> bool:
    """
    Validate phone number format.
    
    Args:
        phone: Phone number to validate
        
    Returns:
        True if valid, False otherwise
    """
    # Remove spaces and common separators
    clean_phone = phone.replace(' ', '').replace('-', '').replace('+', '')
    
    # Basic validation: 10-15 digits
    if not clean_phone.isdigit():
        return False
    
    if len(clean_phone) < 10 or len(clean_phone) > 15:
        return False
    
    return True

def clean_phone_number(phone: str) -> str:
    """
    Clean and format phone number.
    
    Args:
        phone: Raw phone number
        
    Returns:
        Cleaned phone number
    """
    # Remove spaces, dashes, plus signs
    clean = phone.replace(' ', '').replace('-', '').replace('+', '')
    
    # Add WhatsApp suffix if not present
    if '@s.whatsapp.net' not in clean:
        return f"{clean}@s.whatsapp.net"
    
    return clean

def save_bulk_job_log(job: BulkJob) -> None:
    """
    Save bulk job results to log file.
    
    Args:
        job: Completed bulk job
    """
    try:
        log_file = os.path.join(BULK_LOGS_DIR, f"{job.job_id}.json")
        
        # Convert job to dictionary for JSON serialization
        job_data = asdict(job)
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(job_data, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Bulk job log saved: {log_file}")
        
    except Exception as e:
        logger.error(f"Error saving bulk job log: {e}")

# ============================================================================
# CORE BULK MESSAGING FUNCTIONS
# ============================================================================

def send_bulk_message_individual(
    contacts: List[str], 
    message: str,
    send_function: Callable[[str, str], bool],
    delay_range: Tuple[float, float] = (DEFAULT_MIN_DELAY, DEFAULT_MAX_DELAY),
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> BulkJob:
    """
    Send the same message to multiple contacts individually using the loop method.
    
    Args:
        contacts: List of phone numbers
        message: Message to send to all contacts
        send_function: Function to send individual messages (e.g., send_complete_message)
        delay_range: Min/max delay between sends (seconds)
        progress_callback: Optional callback for progress updates
        
    Returns:
        BulkJob object with results
    """
    # Create bulk job
    job = BulkJob(
        job_id=generate_job_id(),
        message=message,
        contacts=contacts.copy(),
        status=JOB_STATUS_IN_PROGRESS,
        total_contacts=len(contacts),
        started_at=datetime.now().isoformat()
    )
    
    logger.info(f"Starting bulk message job {job.job_id} for {len(contacts)} contacts")
    
    # Validate and clean contacts
    valid_contacts = []
    for contact in contacts:
        if validate_phone_number(contact):
            valid_contacts.append(clean_phone_number(contact))
        else:
            # Log invalid contact
            result = ContactResult(
                contact=contact,
                success=False,
                timestamp=datetime.now().isoformat(),
                error_message="Invalid phone number format"
            )
            job.results.append(result)
            job.failed_sends += 1
    
    logger.info(f"Valid contacts: {len(valid_contacts)}/{len(contacts)}")
    
    # Send messages to valid contacts
    for i, contact in enumerate(valid_contacts):
        try:
            logger.info(f"Sending message to {contact} ({i+1}/{len(valid_contacts)})")
            
            # Send message using provided function
            success = send_function(contact, message)
            
            # Create result
            result = ContactResult(
                contact=contact,
                success=success,
                timestamp=datetime.now().isoformat()
            )
            
            if success:
                job.successful_sends += 1
                logger.info(f"✅ Message sent successfully to {contact}")
            else:
                job.failed_sends += 1
                result.error_message = "Send function returned False"
                logger.warning(f"❌ Failed to send message to {contact}")
            
            job.results.append(result)
            
            # Call progress callback if provided
            if progress_callback:
                progress_callback(i + 1, len(valid_contacts))
            
        except Exception as e:
            # Handle unexpected errors
            error_msg = str(e)
            result = ContactResult(
                contact=contact,
                success=False,
                timestamp=datetime.now().isoformat(),
                error_message=error_msg
            )
            job.results.append(result)
            job.failed_sends += 1
            
            logger.error(f"❌ Exception sending message to {contact}: {error_msg}")
        
        # Rate limiting delay (except for last message)
        if i < len(valid_contacts) - 1:
            delay = random.uniform(*delay_range)
            logger.debug(f"Waiting {delay:.1f}s before next message...")
            time.sleep(delay)
    
    # Complete the job
    job.status = JOB_STATUS_COMPLETED
    job.completed_at = datetime.now().isoformat()
    
    # Save job log
    save_bulk_job_log(job)
    
    logger.info(f"Bulk job {job.job_id} completed: {job.successful_sends} successful, {job.failed_sends} failed")
    
    return job

def send_bulk_message_with_retry(
    contacts: List[str], 
    message: str,
    send_function: Callable[[str, str], bool],
    max_retries: int = MAX_RETRIES,
    delay_range: Tuple[float, float] = (DEFAULT_MIN_DELAY, DEFAULT_MAX_DELAY),
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> BulkJob:
    """
    Send bulk messages with retry logic for failed sends.
    
    Args:
        contacts: List of phone numbers
        message: Message to send
        send_function: Function to send individual messages
        max_retries: Maximum retry attempts for failed sends
        delay_range: Min/max delay between sends
        progress_callback: Optional callback for progress updates
        
    Returns:
        BulkJob object with results
    """
    # Initial send
    job = send_bulk_message_individual(contacts, message, send_function, delay_range, progress_callback)
    
    # Retry failed sends
    for retry_attempt in range(1, max_retries + 1):
        # Get failed contacts
        failed_contacts = [
            result.contact for result in job.results 
            if not result.success and result.retry_count < max_retries
        ]
        
        if not failed_contacts:
            break
        
        logger.info(f"Retry attempt {retry_attempt}: {len(failed_contacts)} failed contacts")
        
        # Reset counters for retry
        original_successful = job.successful_sends
        original_failed = job.failed_sends
        
        # Remove failed results that will be retried
        job.results = [r for r in job.results if r.contact not in failed_contacts or r.success]
        
        # Retry failed contacts
        for contact in failed_contacts:
            try:
                logger.info(f"Retrying message to {contact} (attempt {retry_attempt + 1})")
                
                success = send_function(contact, message)
                
                result = ContactResult(
                    contact=contact,
                    success=success,
                    timestamp=datetime.now().isoformat(),
                    retry_count=retry_attempt
                )
                
                if success:
                    job.successful_sends += 1
                    logger.info(f"✅ Retry successful for {contact}")
                else:
                    result.error_message = f"Send function returned False (retry {retry_attempt})"
                    logger.warning(f"❌ Retry failed for {contact}")
                
                job.results.append(result)
                
            except Exception as e:
                result = ContactResult(
                    contact=contact,
                    success=False,
                    timestamp=datetime.now().isoformat(),
                    error_message=f"Exception on retry {retry_attempt}: {str(e)}",
                    retry_count=retry_attempt
                )
                job.results.append(result)
                logger.error(f"❌ Exception on retry for {contact}: {e}")
            
            # Delay between retries
            if contact != failed_contacts[-1]:  # Not last contact
                delay = random.uniform(*delay_range)
                time.sleep(delay)
        
        # Update failed count
        job.failed_sends = len([r for r in job.results if not r.success])
    
    # Update job completion
    job.completed_at = datetime.now().isoformat()
    save_bulk_job_log(job)
    
    logger.info(f"Bulk job {job.job_id} completed with retries: {job.successful_sends} successful, {job.failed_sends} failed")
    
    return job

# ============================================================================
# ASYNC BULK MESSAGING (Background Jobs)
# ============================================================================

class BulkMessageManager:
    """Manager for handling bulk messaging jobs."""
    
    def __init__(self):
        self.active_jobs: Dict[str, BulkJob] = {}
        self.job_threads: Dict[str, threading.Thread] = {}
    
    def start_bulk_job(
        self, 
        contacts: List[str], 
        message: str,
        send_function: Callable[[str, str], bool],
        with_retry: bool = True
    ) -> str:
        """
        Start a bulk messaging job in the background.
        
        Args:
            contacts: List of phone numbers
            message: Message to send
            send_function: Function to send individual messages
            with_retry: Whether to retry failed sends
            
        Returns:
            Job ID for tracking
        """
        job_id = generate_job_id()
        
        # Create initial job object
        job = BulkJob(
            job_id=job_id,
            message=message,
            contacts=contacts.copy(),
            status=JOB_STATUS_PENDING,
            total_contacts=len(contacts)
        )
        
        self.active_jobs[job_id] = job
        
        # Start background thread
        if with_retry:
            target_func = lambda: self._run_bulk_job_with_retry(job_id, contacts, message, send_function)
        else:
            target_func = lambda: self._run_bulk_job(job_id, contacts, message, send_function)
        
        thread = threading.Thread(target=target_func, daemon=True)
        self.job_threads[job_id] = thread
        thread.start()
        
        logger.info(f"Started background bulk job: {job_id}")
        return job_id
    
    def _run_bulk_job(self, job_id: str, contacts: List[str], message: str, send_function: Callable):
        """Run bulk job in background thread."""
        try:
            def progress_callback(current: int, total: int):
                if job_id in self.active_jobs:
                    # Update progress in real-time
                    pass
            
            if job_id in self.active_jobs:
                result_job = send_bulk_message_individual(contacts, message, send_function, progress_callback=progress_callback)
                self.active_jobs[job_id] = result_job
        except Exception as e:
            if job_id in self.active_jobs:
                self.active_jobs[job_id].status = JOB_STATUS_FAILED
                logger.error(f"Bulk job {job_id} failed: {e}")
    
    def _run_bulk_job_with_retry(self, job_id: str, contacts: List[str], message: str, send_function: Callable):
        """Run bulk job with retry in background thread."""
        try:
            if job_id in self.active_jobs:
                result_job = send_bulk_message_with_retry(contacts, message, send_function)
                self.active_jobs[job_id] = result_job
        except Exception as e:
            if job_id in self.active_jobs:
                self.active_jobs[job_id].status = JOB_STATUS_FAILED
                logger.error(f"Bulk job {job_id} failed: {e}")
    
    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Get status of a bulk messaging job."""
        if job_id not in self.active_jobs:
            return None
        
        job = self.active_jobs[job_id]
        return {
            'job_id': job.job_id,
            'status': job.status,
            'total_contacts': job.total_contacts,
            'successful_sends': job.successful_sends,
            'failed_sends': job.failed_sends,
            'started_at': job.started_at,
            'completed_at': job.completed_at
        }
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a running bulk messaging job."""
        if job_id not in self.active_jobs:
            return False
        
        self.active_jobs[job_id].status = JOB_STATUS_CANCELLED
        logger.info(f"Bulk job {job_id} cancelled")
        return True
    
    def get_all_jobs(self) -> List[Dict]:
        """Get status of all jobs."""
        return [self.get_job_status(job_id) for job_id in self.active_jobs.keys()]

# Global bulk message manager instance
bulk_manager = BulkMessageManager()

# ============================================================================
# UTILITY FUNCTIONS FOR INTEGRATION
# ============================================================================

def parse_contacts_from_text(contacts_text: str) -> List[str]:
    """
    Parse contacts from textarea input (one per line).
    
    Args:
        contacts_text: Multi-line string with phone numbers
        
    Returns:
        List of phone numbers
    """
    contacts = []
    for line in contacts_text.strip().split('\n'):
        line = line.strip()
        if line and validate_phone_number(line):
            contacts.append(line)
    
    return contacts

def format_bulk_job_summary(job: BulkJob) -> str:
    """
    Format bulk job results into a readable summary.
    
    Args:
        job: Completed bulk job
        
    Returns:
        Formatted summary string
    """
    duration = "Unknown"
    if job.started_at and job.completed_at:
        start = datetime.fromisoformat(job.started_at)
        end = datetime.fromisoformat(job.completed_at)
        duration = str(end - start).split('.')[0]  # Remove microseconds
    
    summary = f"""
Bulk Message Job: {job.job_id}
Status: {job.status}
Duration: {duration}

Results:
✅ Successful: {job.successful_sends}
❌ Failed: {job.failed_sends}
📊 Total: {job.total_contacts}
📈 Success Rate: {(job.successful_sends / job.total_contacts * 100):.1f}%
"""
    
    return summary.strip() 