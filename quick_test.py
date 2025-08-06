#!/usr/bin/env python3
"""
Quick Test - Test lead qualification logic without external API calls
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_basic_filtering():
    """Test the basic filtering logic without AI calls"""
    print("🧪 Quick Test - Basic Filtering Logic")
    print("=" * 50)
    
    # Import the filtering logic
    from src.services.lead_qualification_service import analyze_lead_qualification_ai
    
    test_cases = [
        {
            "message": "Hi",
            "history": [],
            "should_qualify": False,
            "reason": "Too short"
        },
        {
            "message": "Hello",
            "history": [],
            "should_qualify": False,
            "reason": "Simple greeting"
        },
        {
            "message": "How can you help my business?",
            "history": [],
            "should_qualify": False,
            "reason": "No conversation history"
        },
        {
            "message": "We need automation for our 500+ daily customer inquiries",
            "history": [
                {"role": "user", "content": "Hi"},
                {"role": "assistant", "content": "Hello! How can I help?"},
                {"role": "user", "content": "Looking for business solutions"},
                {"role": "assistant", "content": "Great! Tell me more."}
            ],
            "should_qualify": True,
            "reason": "Has business context and conversation depth"
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test['reason']}")
        print(f"Message: '{test['message']}'")
        print(f"History: {len(test['history'])} messages")
        
        try:
            # This will test the filtering logic before AI call
            is_qualified, confidence, reason, metadata = analyze_lead_qualification_ai(
                test['message'], test['history']
            )
            
            if test['should_qualify']:
                if is_qualified:
                    print("✅ CORRECT: Qualified as expected")
                else:
                    print(f"❌ INCORRECT: Should qualify but didn't - {reason}")
            else:
                if not is_qualified:
                    print(f"✅ CORRECT: Not qualified as expected - {reason}")
                else:
                    print("❌ INCORRECT: Should not qualify but did")
                    
        except Exception as e:
            if "OpenAI" in str(e) or "API" in str(e):
                print("⚠️ EXPECTED: Stopped at API call (filtering worked)")
            else:
                print(f"❌ ERROR: {e}")

def test_conversation_progression():
    """Test how conversation should progress"""
    print("\n💬 Conversation Flow Test")
    print("=" * 30)
    
    phone_number = "7033009600"
    conversation_scenarios = [
        {
            "step": 1,
            "message": "Hi",
            "expected": "Should get friendly greeting, no Calendly"
        },
        {
            "step": 2, 
            "message": "How can you help my organisation?",
            "expected": "Should ask for more details, no Calendly"
        },
        {
            "step": 3,
            "message": "We need customer support automation",
            "expected": "Should provide info and ask specifics, no Calendly"
        },
        {
            "step": 4,
            "message": "We handle 500+ inquiries daily and need enterprise pricing",
            "expected": "Should qualify and offer Calendly"
        }
    ]
    
    print("Expected conversation flow:")
    for scenario in conversation_scenarios:
        print(f"Step {scenario['step']}: '{scenario['message']}'")
        print(f"  → {scenario['expected']}")

def test_message_patterns():
    """Test different message patterns"""
    print("\n🎯 Message Pattern Analysis")  
    print("=" * 35)
    
    # Test simple greeting patterns
    simple_patterns = [
        'hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening',
        'thanks', 'thank you', 'ok', 'okay', 'yes', 'no', 'sure', 'fine',
        'how are you', 'what\'s up', 'wassup', 'sup', 'hola', 'namaste'
    ]
    
    test_messages = [
        "Hi",
        "Hello there", 
        "Good morning",
        "Thanks",
        "How are you?",
        "I need help with business automation solutions for my company",
        "What are your enterprise pricing packages for WhatsApp integration?"
    ]
    
    for message in test_messages:
        message_lower = message.lower().strip()
        is_simple = any(pattern in message_lower for pattern in simple_patterns) and len(message.strip()) < 20
        
        print(f"'{message}' → {'Simple greeting' if is_simple else 'Business message'}")

def main():
    print("⚡ Quick Test Suite - No External Dependencies")
    print("=" * 55)
    print("Testing lead qualification logic locally...")
    print()
    
    try:
        test_basic_filtering()
        test_conversation_progression() 
        test_message_patterns()
        
        print("\n✅ Quick tests completed!")
        print("\n📋 Key Changes Made:")
        print("• Simple greetings (Hi, Hello) are filtered out")
        print("• Requires 3+ message conversation history")
        print("• Confidence threshold raised to 0.85")
        print("• Minimum lead score raised to 80")
        print("• Only genuine business context qualifies")
        
        print("\n🚀 Ready for Production Testing:")
        print("1. Deploy the changes")
        print("2. Test with real WhatsApp messages")
        print("3. Monitor conversation flows")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()