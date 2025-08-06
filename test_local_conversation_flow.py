#!/usr/bin/env python3
"""
Local Test Script for Lead Qualification Conversation Flow
Test the new conversation flow with a specific phone number
"""

import sys
import os
import json
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.lead_qualification_service import detect_and_process_qualified_lead, analyze_lead_qualification_ai
from src.handlers.message_processor import process_incoming_message
from src.core.supabase_client import get_supabase_manager

def simulate_conversation_flow(phone_number: str):
    """
    Simulate a realistic conversation flow to test lead qualification
    """
    print(f"🧪 Testing Conversation Flow with {phone_number}")
    print("=" * 60)
    
    # Test scenarios
    scenarios = [
        {
            "name": "Simple Greeting (Should NOT qualify)",
            "messages": ["Hi"],
            "conversation_history": []
        },
        {
            "name": "Basic Inquiry (Should NOT qualify - insufficient depth)",
            "messages": ["How can you help my organisation?"],
            "conversation_history": []
        },
        {
            "name": "Progressive Business Conversation (Should qualify after depth)",
            "messages": [
                "Hi",
                "How can you help my organisation?", 
                "We need to automate our customer support",
                "We handle about 500 customer inquiries per day and need pricing for enterprise solution"
            ],
            "conversation_history": []
        }
    ]
    
    for scenario in scenarios:
        print(f"\n📋 Scenario: {scenario['name']}")
        print("-" * 50)
        
        conversation_history = scenario['conversation_history'].copy()
        
        for i, message in enumerate(scenario['messages']):
            print(f"\n💬 Message {i+1}: '{message}'")
            
            # Test lead qualification
            is_qualified, status_message = detect_and_process_qualified_lead(
                message, phone_number, conversation_history
            )
            
            # Display result
            if is_qualified:
                print(f"🎯 RESULT: ✅ QUALIFIED - {status_message}")
            else:
                print(f"🎯 RESULT: ❌ NOT QUALIFIED - {status_message}")
            
            # Simulate conversation history building
            conversation_history.append({"role": "user", "content": message})
            conversation_history.append({"role": "assistant", "content": "Bot response here"})
            
            print(f"📊 Conversation depth: {len(conversation_history)} messages")

def test_ai_analysis_directly():
    """
    Test the AI analysis function directly with various message types
    """
    print("\n🤖 Direct AI Analysis Testing")
    print("=" * 40)
    
    test_cases = [
        {
            "message": "Hi",
            "history": [],
            "expected": False,
            "description": "Simple greeting"
        },
        {
            "message": "Hello, how are you?",
            "history": [],
            "expected": False,
            "description": "Greeting with question"
        },
        {
            "message": "What services do you offer?",
            "history": [],
            "expected": False,
            "description": "General inquiry without conversation depth"
        },
        {
            "message": "We need WhatsApp automation for our e-commerce business with 500+ daily inquiries. What are your enterprise pricing options?",
            "history": [
                {"role": "user", "content": "Hi, I'm looking for business automation"},
                {"role": "assistant", "content": "Hello! I'd be happy to help. What challenges are you facing?"},
                {"role": "user", "content": "We need customer support automation"},
                {"role": "assistant", "content": "Great! Tell me more about your current volume and needs."}
            ],
            "expected": True,
            "description": "Qualified business lead with context"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['description']}")
        print(f"Message: '{test_case['message']}'")
        print(f"History depth: {len(test_case['history'])} messages")
        
        is_qualified, confidence, reason, metadata = analyze_lead_qualification_ai(
            test_case['message'], test_case['history']
        )
        
        expected_str = "SHOULD QUALIFY" if test_case['expected'] else "SHOULD NOT QUALIFY"
        actual_str = "QUALIFIED" if is_qualified else "NOT QUALIFIED"
        
        if is_qualified == test_case['expected']:
            print(f"✅ CORRECT: {actual_str} ({expected_str})")
        else:
            print(f"❌ INCORRECT: {actual_str} (but {expected_str})")
        
        print(f"   Confidence: {confidence:.2f}")
        print(f"   Reason: {reason}")
        if metadata:
            print(f"   Lead Score: {metadata.get('lead_score', 0)}")
            print(f"   Quality: {metadata.get('lead_quality', 'N/A')}")

def simulate_message_processing(phone_number: str):
    """
    Simulate the full message processing pipeline
    """
    print(f"\n🔄 Full Message Processing Simulation for {phone_number}")
    print("=" * 60)
    
    # Simulate different message types
    test_messages = [
        {
            "message": "Hi",
            "description": "Simple greeting - should get normal bot response"
        },
        {
            "message": "Hello, I need help with business automation",
            "description": "Business inquiry - should engage in conversation"
        }
    ]
    
    for test in test_messages:
        print(f"\n📨 Testing: {test['description']}")
        print(f"Message: '{test['message']}'")
        
        # Create message info structure similar to webhook
        message_info = {
            'conversation_contact': phone_number,
            'message_text': test['message'],
            'message_role': 'user',
            'message_id': f"test_{datetime.now().timestamp()}",
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # This would normally process through the full pipeline
            print("📋 Would process through full message pipeline...")
            print("   - Lead qualification check")
            print("   - Bot response generation")
            print("   - Message saving to database")
            
        except Exception as e:
            print(f"❌ Error in processing: {e}")

def check_configuration():
    """
    Display current configuration settings
    """
    print("\n⚙️ Current Configuration")
    print("=" * 30)
    
    from src.config.config import (
        LEAD_QUALIFICATION_ENABLED,
        LEAD_QUALIFICATION_CONFIDENCE_THRESHOLD,
        QUALIFIED_LEAD_MIN_SCORE,
        CALENDLY_AUTO_SEND_ENABLED,
        CALENDLY_COOLDOWN_HOURS
    )
    
    print(f"Lead Qualification Enabled: {LEAD_QUALIFICATION_ENABLED}")
    print(f"Confidence Threshold: {LEAD_QUALIFICATION_CONFIDENCE_THRESHOLD}")
    print(f"Minimum Lead Score: {QUALIFIED_LEAD_MIN_SCORE}")
    print(f"Calendly Auto-Send: {CALENDLY_AUTO_SEND_ENABLED}")
    print(f"Calendly Cooldown: {CALENDLY_COOLDOWN_HOURS} hours")

def main():
    print("🚀 Local Conversation Flow Testing")
    print("=" * 40)
    print("Testing the updated lead qualification system...")
    print(f"Test Phone Number: 7033009600")
    print()
    
    try:
        # Check configuration
        check_configuration()
        
        # Test AI analysis directly
        test_ai_analysis_directly()
        
        # Test conversation flow simulation
        simulate_conversation_flow("7033009600")
        
        # Test message processing
        simulate_message_processing("7033009600")
        
        print("\n✅ Local Testing Complete!")
        print("\n📋 Next Steps:")
        print("1. Review the test results above")
        print("2. If satisfied, deploy to production")
        print("3. Test with real WhatsApp messages")
        print("4. Monitor conversation flows in the dashboard")
        
    except Exception as e:
        print(f"❌ Testing failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()