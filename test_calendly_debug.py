#!/usr/bin/env python3
"""
Debug script to test Calendly configuration and message sending
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_calendly_config():
    """Test if Calendly environment variables are loaded correctly"""
    
    print("🔍 CALENDLY CONFIG DEBUG")
    print("=" * 50)
    
    # Test environment variables
    calendly_url = os.getenv('CALENDLY_DISCOVERY_CALL_URL')
    calendly_enabled = os.getenv('CALENDLY_AUTO_SEND_ENABLED')
    lead_qual_enabled = os.getenv('LEAD_QUALIFICATION_ENABLED')
    
    print(f"CALENDLY_DISCOVERY_CALL_URL: {calendly_url}")
    print(f"CALENDLY_AUTO_SEND_ENABLED: {calendly_enabled}")
    print(f"LEAD_QUALIFICATION_ENABLED: {lead_qual_enabled}")
    
    # Test configuration imports
    try:
        from src.config.config import (
            CALENDLY_DISCOVERY_CALL_URL,
            CALENDLY_AUTO_SEND_ENABLED,
            LEAD_QUALIFICATION_ENABLED
        )
        
        print("\n📋 CONFIG IMPORTS:")
        print(f"CALENDLY_DISCOVERY_CALL_URL: {CALENDLY_DISCOVERY_CALL_URL}")
        print(f"CALENDLY_AUTO_SEND_ENABLED: {CALENDLY_AUTO_SEND_ENABLED}")
        print(f"LEAD_QUALIFICATION_ENABLED: {LEAD_QUALIFICATION_ENABLED}")
        
    except Exception as e:
        print(f"❌ CONFIG IMPORT ERROR: {e}")
    
    # Test lead qualification service
    try:
        from src.services.lead_qualification_service import send_calendly_discovery_call
        
        print("\n🧪 TESTING CALENDLY MESSAGE GENERATION:")
        
        # Test message generation without sending
        test_metadata = {
            'lead_quality': 'HIGH',
            'business_indicators': ['marketing agency', '30 employees'],
            'buying_signals': ['pricing options', 'business automation']
        }
        
        # This should generate the message content
        print("Test metadata:", test_metadata)
        
    except Exception as e:
        print(f"❌ SERVICE IMPORT ERROR: {e}")

if __name__ == "__main__":
    test_calendly_config() 