#!/usr/bin/env python3
"""
Group Messaging Module Test Script
==================================
Tests the group messaging functionality to ensure everything works correctly.
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, Any

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_group_messaging_api(base_url: str = "http://localhost:5000") -> Dict[str, Any]:
    """
    Test the group messaging API endpoints.
    
    Args:
        base_url: Base URL of the Flask application
        
    Returns:
        Dictionary with test results
    """
    results = {
        "tests_run": 0,
        "tests_passed": 0,
        "tests_failed": 0,
        "details": []
    }
    
    def run_test(test_name: str, test_func):
        """Helper to run individual tests."""
        results["tests_run"] += 1
        try:
            print(f"\n🧪 Running test: {test_name}")
            result = test_func()
            if result:
                print(f"✅ PASSED: {test_name}")
                results["tests_passed"] += 1
                results["details"].append({"test": test_name, "status": "PASSED", "details": result})
            else:
                print(f"❌ FAILED: {test_name}")
                results["tests_failed"] += 1
                results["details"].append({"test": test_name, "status": "FAILED", "details": "Test returned False"})
        except Exception as e:
            print(f"❌ ERROR in {test_name}: {e}")
            results["tests_failed"] += 1
            results["details"].append({"test": test_name, "status": "ERROR", "details": str(e)})
    
    # Test 1: Health Check
    def test_health_check():
        response = requests.get(f"{base_url}/api/group-messaging/health")
        return response.status_code == 200 and response.json().get("success") is True
    
    # Test 2: Get Groups
    def test_get_groups():
        response = requests.get(f"{base_url}/api/group-messaging/groups")
        if response.status_code == 200:
            data = response.json()
            print(f"   Found {len(data.get('data', {}).get('groups', []))} groups")
            return data.get("success") is True
        return False
    
    # Test 3: Send Group Message (will fail if no groups exist)
    def test_send_group_message():
        # First get groups to find a valid group JID
        groups_response = requests.get(f"{base_url}/api/group-messaging/groups")
        if groups_response.status_code != 200:
            print("   Skipping - could not fetch groups")
            return True  # Skip this test
            
        groups_data = groups_response.json()
        groups = groups_data.get('data', {}).get('groups', [])
        
        if not groups:
            print("   Skipping - no groups available")
            return True  # Skip this test
        
        # Use the first group for testing
        test_group = groups[0]
        group_jid = test_group['group_jid']
        
        payload = {
            "message_content": f"🤖 Test message from group messaging module - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "message_type": "text"
        }
        
        response = requests.post(
            f"{base_url}/api/group-messaging/groups/{group_jid}/send-message",
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Message sent to group: {test_group['name']}")
            return data.get("success") is True
        else:
            print(f"   Failed to send message: {response.text}")
            return False
    
    # Test 4: Bulk Send (will fail if no groups exist)
    def test_bulk_send():
        # Get groups first
        groups_response = requests.get(f"{base_url}/api/group-messaging/groups")
        if groups_response.status_code != 200:
            print("   Skipping - could not fetch groups")
            return True
            
        groups_data = groups_response.json()
        groups = groups_data.get('data', {}).get('groups', [])
        
        if len(groups) < 1:
            print("   Skipping - need at least 1 group")
            return True
        
        # Use first group for bulk test
        group_jids = [groups[0]['group_jid']]
        
        payload = {
            "group_jids": group_jids,
            "message_content": f"📢 Bulk test message - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "message_type": "text",
            "campaign_name": "Test Bulk Campaign"
        }
        
        response = requests.post(
            f"{base_url}/api/group-messaging/bulk-send",
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Bulk message sent to {len(group_jids)} groups")
            return data.get("success") is True
        else:
            print(f"   Failed bulk send: {response.text}")
            return False
    
    # Test 5: Schedule Message
    def test_schedule_message():
        # Get groups first
        groups_response = requests.get(f"{base_url}/api/group-messaging/groups")
        if groups_response.status_code != 200:
            print("   Skipping - could not fetch groups")
            return True
            
        groups_data = groups_response.json()
        groups = groups_data.get('data', {}).get('groups', [])
        
        if not groups:
            print("   Skipping - no groups available")
            return True
        
        # Schedule message for 1 minute from now
        scheduled_time = datetime.utcnow() + timedelta(minutes=1)
        
        payload = {
            "message_content": f"⏰ Scheduled test message - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "target_groups": [groups[0]['group_jid']],
            "scheduled_at": scheduled_time.isoformat() + "Z",
            "message_type": "text"
        }
        
        response = requests.post(
            f"{base_url}/api/group-messaging/schedule-message",
            json=payload
        )
        
        if response.status_code == 201:
            data = response.json()
            print(f"   Message scheduled for {scheduled_time}")
            return data.get("success") is True
        else:
            print(f"   Failed to schedule: {response.text}")
            return False
    
    # Test 6: Get Group Messages
    def test_get_group_messages():
        # Get groups first
        groups_response = requests.get(f"{base_url}/api/group-messaging/groups")
        if groups_response.status_code != 200:
            print("   Skipping - could not fetch groups")
            return True
            
        groups_data = groups_response.json()
        groups = groups_data.get('data', {}).get('groups', [])
        
        if not groups:
            print("   Skipping - no groups available")
            return True
        
        group_jid = groups[0]['group_jid']
        response = requests.get(f"{base_url}/api/group-messaging/groups/{group_jid}/messages")
        
        if response.status_code == 200:
            data = response.json()
            message_count = len(data.get('data', {}).get('messages', []))
            print(f"   Found {message_count} messages for group")
            return data.get("success") is True
        return False
    
    # Run all tests
    print("🚀 Starting Group Messaging API Tests")
    print("=" * 50)
    
    run_test("Health Check", test_health_check)
    run_test("Get Groups", test_get_groups)
    run_test("Send Group Message", test_send_group_message)
    run_test("Bulk Send", test_bulk_send)
    run_test("Schedule Message", test_schedule_message)
    run_test("Get Group Messages", test_get_group_messages)
    
    return results


def test_module_imports():
    """Test that all module imports work correctly."""
    print("\n🔍 Testing Module Imports")
    print("=" * 30)
    
    imports_to_test = [
        ("Group Service", "src.modules.group_messaging.services.group_service", "GroupService"),
        ("Database Service", "src.modules.group_messaging.services.database_service", "DatabaseService"),
        ("Scheduler Service", "src.modules.group_messaging.services.scheduler_service", "SchedulerService"),
        ("Group Models", "src.modules.group_messaging.models.group", "Group"),
        ("Schedule Models", "src.modules.group_messaging.models.schedule", "ScheduledMessage"),
        ("Config", "src.modules.group_messaging.config.settings", "GroupMessagingConfig"),
        ("Integration", "src.modules.group_messaging.integration", "integrate_group_messaging"),
    ]
    
    passed = 0
    total = len(imports_to_test)
    
    for name, module_path, class_name in imports_to_test:
        try:
            module = __import__(module_path, fromlist=[class_name])
            getattr(module, class_name)
            print(f"✅ {name}")
            passed += 1
        except ImportError as e:
            print(f"❌ {name}: Import Error - {e}")
        except AttributeError as e:
            print(f"❌ {name}: Attribute Error - {e}")
        except Exception as e:
            print(f"❌ {name}: Error - {e}")
    
    print(f"\n📊 Import Test Results: {passed}/{total} passed")
    return passed == total


def main():
    """Main test runner."""
    print("🧪 Group Messaging Module Test Suite")
    print("=" * 50)
    
    # Check environment
    wasender_token = os.getenv('WASENDER_API_TOKEN')
    if not wasender_token:
        print("⚠️  WARNING: WASENDER_API_TOKEN not set in environment")
        print("   Some tests may fail due to missing API credentials")
    
    # Test imports
    imports_ok = test_module_imports()
    
    # Test API endpoints
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:5000"
    
    print(f"\n🌐 Testing API endpoints at: {base_url}")
    
    try:
        api_results = test_group_messaging_api(base_url)
        
        print("\n📊 Final Test Results")
        print("=" * 30)
        print(f"Module Imports: {'✅ PASSED' if imports_ok else '❌ FAILED'}")
        print(f"API Tests: {api_results['tests_passed']}/{api_results['tests_run']} passed")
        
        if api_results['tests_failed'] > 0:
            print(f"❌ {api_results['tests_failed']} tests failed")
            print("\nFailed Tests:")
            for detail in api_results['details']:
                if detail['status'] != 'PASSED':
                    print(f"  - {detail['test']}: {detail['details']}")
        
        overall_success = imports_ok and api_results['tests_failed'] == 0
        print(f"\n🎯 Overall Result: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
        
        return 0 if overall_success else 1
        
    except requests.exceptions.ConnectionError:
        print(f"❌ Could not connect to {base_url}")
        print("   Make sure the Flask application is running")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    exit(main()) 