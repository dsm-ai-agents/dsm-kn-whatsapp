#!/usr/bin/env python3
"""
AI Message Formatting Test
==========================
Test script to demonstrate the new AI message formatting feature
for the bulk messaging system.
"""

import requests
import json
import sys

def test_ai_formatting():
    """Test the AI message formatting endpoint."""
    
    # Test endpoint URL
    url = "http://127.0.0.1:5001/api/bulk-send/format-message"
    
    # Test messages with different scenarios
    test_cases = [
        {
            "name": "Basic Marketing Message",
            "message": "hey there! we have new products that might interest you. check them out on our website. let me know if you want more info",
            "tone": "professional",
            "purpose": "marketing"
        },
        {
            "name": "Support Follow-up",
            "message": "hi, just wanted to check if your issue was resolved. please let us know if you need more help",
            "tone": "friendly", 
            "purpose": "support"
        },
        {
            "name": "Urgent Announcement",
            "message": "important update: our service will be down for maintenance tomorrow from 2-4pm. sorry for inconvenience",
            "tone": "urgent",
            "purpose": "announcement"
        },
        {
            "name": "Casual Follow-up",
            "message": "hope you're doing well! wanted to touch base about the proposal we discussed last week",
            "tone": "casual",
            "purpose": "follow-up"
        }
    ]
    
    print("🤖 AI Message Formatting Test")
    print("=" * 50)
    print()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['name']}")
        print("-" * 30)
        print(f"📝 Original: {test_case['message']}")
        print(f"🎯 Tone: {test_case['tone'].title()}")
        print(f"📋 Purpose: {test_case['purpose'].title()}")
        print()
        
        try:
            # Make API request
            response = requests.post(url, json={
                'message': test_case['message'],
                'tone': test_case['tone'],
                'purpose': test_case['purpose']
            }, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result['status'] == 'success':
                    formatted = result['data']['formatted_message']
                    char_count = result['data']['character_count']
                    improved = result['data']['improvement_applied']
                    
                    print(f"✅ Formatted: {formatted}")
                    print(f"📊 Characters: {char_count}")
                    print(f"🔄 Improved: {'Yes' if improved else 'No'}")
                    print("✅ SUCCESS")
                else:
                    print(f"❌ API Error: {result['message']}")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Connection Error: Backend server is not running")
            print("💡 Please start the Flask backend first:")
            print("   cd whatsapp-python-chatbot && python3 app.py")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            
        print()
        print("=" * 50)
        print()
    
    return True

if __name__ == "__main__":
    print("Starting AI Message Formatting Test...")
    print("Make sure the Flask backend is running on port 5001")
    print()
    
    success = test_ai_formatting()
    
    if success:
        print("🎉 Test completed! Check the formatted messages above.")
        print()
        print("💡 To use this feature:")
        print("1. Open the bulk send page in your frontend")
        print("2. Type a message in the text area")
        print("3. Click the 'AI Format' button (sparkles icon)")
        print("4. Watch your message get professionally formatted!")
    else:
        print("❌ Test failed. Please check the backend server.")
        sys.exit(1) 