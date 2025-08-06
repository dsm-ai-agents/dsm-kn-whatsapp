#!/usr/bin/env python3
"""
Test script for WASender Contact Sync functionality
===================================================
This script tests the WASender contact synchronization features
to ensure contacts are properly fetched and updated.

Usage:
    python test_wasender_contact_sync.py
"""

import sys
import os
import json
import requests
import time
from datetime import datetime

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.services.wasender_contact_service import wasender_contact_service
from src.core.supabase_client import get_supabase_manager

def test_wasender_configuration():
    """Test WASender API configuration."""
    print("🔧 Testing WASender Configuration...")
    
    if wasender_contact_service.is_configured():
        print("✅ WASender API is configured")
        return True
    else:
        print("❌ WASender API is not configured")
        print("   Please set WASENDER_API_TOKEN in your .env file")
        return False

def test_database_connection():
    """Test database connection."""
    print("\n📊 Testing Database Connection...")
    
    supabase = get_supabase_manager()
    if supabase.is_connected():
        print("✅ Database connection successful")
        return True
    else:
        print("❌ Database connection failed")
        return False

def test_fetch_contacts():
    """Test fetching contacts from WASender API."""
    print("\n📱 Testing WASender Contact Fetch...")
    
    try:
        contacts = wasender_contact_service.fetch_contacts_from_wasender()
        
        if contacts:
            print(f"✅ Successfully fetched {len(contacts)} contacts")
            
            # Show sample contact
            if len(contacts) > 0:
                sample_contact = contacts[0]
                print(f"   Sample contact: {json.dumps(sample_contact, indent=2)}")
                
                # Test contact info extraction
                contact_info = wasender_contact_service.extract_contact_info(sample_contact)
                print(f"   Extracted info: {json.dumps(contact_info, indent=2, default=str)}")
            
            return True
        else:
            print("⚠️  No contacts fetched (this might be normal if no contacts exist)")
            return True
            
    except Exception as e:
        print(f"❌ Error fetching contacts: {e}")
        return False

def test_single_contact_sync():
    """Test syncing a single contact."""
    print("\n🔄 Testing Single Contact Sync...")
    
    # Try to get a phone number from existing conversations
    try:
        supabase = get_supabase_manager()
        result = supabase.client.table('conversations')\
            .select('contacts!inner(phone_number)')\
            .limit(1)\
            .execute()
        
        if result.data:
            phone_number = result.data[0]['contacts']['phone_number']
            clean_phone = wasender_contact_service.normalize_phone_number(phone_number)
            
            print(f"   Testing with phone number: {clean_phone}")
            
            contact_info = wasender_contact_service.sync_single_contact(clean_phone)
            
            if contact_info:
                print("✅ Single contact sync successful")
                print(f"   Contact info: {json.dumps(contact_info, indent=2, default=str)}")
                return True
            else:
                print("⚠️  Contact not found in WASender (this might be normal)")
                return True
        else:
            print("⚠️  No conversations found to test with")
            return True
            
    except Exception as e:
        print(f"❌ Error testing single contact sync: {e}")
        return False

def test_conversation_contact_sync():
    """Test syncing contacts for conversations."""
    print("\n💬 Testing Conversation Contact Sync...")
    
    try:
        stats = wasender_contact_service.sync_contacts_for_conversations()
        
        if 'error' in stats:
            print(f"⚠️  Sync completed with note: {stats['error']}")
        else:
            print("✅ Conversation contact sync completed")
            print(f"   Stats: {json.dumps(stats, indent=2)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing conversation contact sync: {e}")
        return False

def test_api_endpoints():
    """Test API endpoints for contact sync."""
    print("\n🌐 Testing API Endpoints...")
    
    base_url = "http://localhost:5001"
    
    # Test sync status endpoint
    try:
        response = requests.get(f"{base_url}/api/sync/status")
        if response.status_code == 200:
            print("✅ Sync status endpoint working")
            print(f"   Status: {response.json()}")
        else:
            print(f"❌ Sync status endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"⚠️  Could not test API endpoints (server may not be running): {e}")

def test_database_migration():
    """Test if database has WASender fields."""
    print("\n🗄️  Testing Database Schema...")
    
    try:
        supabase = get_supabase_manager()
        
        # Try to query WASender fields
        result = supabase.client.table('contacts')\
            .select('id, phone_number, name, verified_name, profile_image_url, wasender_sync_status')\
            .limit(1)\
            .execute()
        
        print("✅ Database schema supports WASender fields")
        
        if result.data:
            sample = result.data[0]
            print(f"   Sample contact with WASender fields: {json.dumps(sample, indent=2)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database schema issue: {e}")
        print("   Run the migration script: database_migration_wasender_contacts.sql")
        return False

def main():
    """Run all tests."""
    print("🧪 WASender Contact Sync Test Suite")
    print("=" * 50)
    
    test_results = []
    
    # Run all tests
    test_results.append(("Configuration", test_wasender_configuration()))
    test_results.append(("Database Connection", test_database_connection()))
    test_results.append(("Database Schema", test_database_migration()))
    test_results.append(("Fetch Contacts", test_fetch_contacts()))
    test_results.append(("Single Contact Sync", test_single_contact_sync()))
    test_results.append(("Conversation Contact Sync", test_conversation_contact_sync()))
    test_results.append(("API Endpoints", test_api_endpoints()))
    
    # Print summary
    print("\n📋 Test Summary")
    print("=" * 50)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! WASender contact sync is ready to use.")
        print("\nNext steps:")
        print("1. Run the database migration if you haven't already")
        print("2. Call POST /api/sync/wasender-contacts to sync all contacts")
        print("3. Use ?auto_sync=true parameter in conversations API for automatic sync")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues before using contact sync.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 