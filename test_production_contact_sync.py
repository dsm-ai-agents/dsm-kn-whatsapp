#!/usr/bin/env python3
"""
Production Test Script for WASender Contact Sync
=================================================
This script tests the WASender contact synchronization in production
to ensure contacts are properly fetched and displayed.

Usage:
    python test_production_contact_sync.py
"""

import requests
import json
import time
from datetime import datetime

# Production API base URL - update this with your actual production URL
PRODUCTION_API_BASE = "https://whatsapp-ai-chatbot-production-bc92.up.railway.app/"  # Update this!

def test_sync_status():
    """Test the sync status endpoint."""
    print("🔧 Testing WASender Sync Status...")
    
    try:
        response = requests.get(f"{PRODUCTION_API_BASE}/api/sync/status")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Sync Status: {data}")
            return data.get('data', {}).get('wasender_configured', False)
        else:
            print(f"❌ Sync Status Failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Sync Status Error: {e}")
        return False

def test_conversation_sync():
    """Test conversation contact sync."""
    print("\n📱 Testing Conversation Contact Sync...")
    
    try:
        response = requests.post(f"{PRODUCTION_API_BASE}/api/sync/conversation-contacts")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Conversation Sync: {data}")
            return True
        else:
            print(f"❌ Conversation Sync Failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Conversation Sync Error: {e}")
        return False

def test_conversations_api():
    """Test the conversations API to see if contacts are enriched."""
    print("\n💬 Testing Conversations API with Contact Enrichment...")
    
    try:
        response = requests.get(f"{PRODUCTION_API_BASE}/api/conversations/unique?limit=5")
        if response.status_code == 200:
            data = response.json()
            conversations = data.get('data', {}).get('conversations', [])
            
            print(f"📊 Found {len(conversations)} conversations")
            
            for i, conv in enumerate(conversations[:3]):  # Show first 3
                contact = conv.get('contact', {})
                print(f"\n📞 Conversation {i+1}:")
                print(f"   Phone: {contact.get('display_phone', 'N/A')}")
                print(f"   Name: {contact.get('name', 'N/A')}")
                print(f"   Verified Name: {contact.get('verified_name', 'N/A')}")
                print(f"   Business Account: {contact.get('is_business_account', False)}")
                print(f"   Sync Status: {contact.get('wasender_sync_status', 'N/A')}")
                
            return True
        else:
            print(f"❌ Conversations API Failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Conversations API Error: {e}")
        return False

def test_manual_contact_sync():
    """Test manual contact sync for a specific phone number."""
    print("\n🔄 Testing Manual Contact Sync...")
    
    # You can update this with a real phone number from your system
    test_phone = "917033009600"  # Update with a real number
    
    try:
        response = requests.post(f"{PRODUCTION_API_BASE}/api/sync/wasender-contact/{test_phone}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Manual Sync: {data}")
            return True
        else:
            print(f"❌ Manual Sync Failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Manual Sync Error: {e}")
        return False

def main():
    """Run all production tests."""
    print("🚀 Starting Production WASender Contact Sync Tests")
    print("=" * 60)
    
    # Update the production URL
    global PRODUCTION_API_BASE
    production_url = input(f"Enter production URL (current: {PRODUCTION_API_BASE}): ").strip()
    if production_url:
        PRODUCTION_API_BASE = production_url
    
    print(f"🌐 Testing against: {PRODUCTION_API_BASE}")
    print("=" * 60)
    
    # Test results
    results = []
    
    # Test 1: Sync Status
    results.append(("Sync Status", test_sync_status()))
    
    # Test 2: Conversation Sync
    results.append(("Conversation Sync", test_conversation_sync()))
    
    # Test 3: Conversations API
    results.append(("Conversations API", test_conversations_api()))
    
    # Test 4: Manual Contact Sync
    results.append(("Manual Contact Sync", test_manual_contact_sync()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! WASender contact sync is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")
    
    print("\n📝 Next Steps:")
    print("1. Check your frontend at http://localhost:3000/conversations")
    print("2. Verify that contact names are displayed instead of phone numbers")
    print("3. Look for verified business names and profile images")
    print("4. Test with different WhatsApp contacts")

if __name__ == "__main__":
    main() 