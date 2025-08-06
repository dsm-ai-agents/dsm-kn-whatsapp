#!/usr/bin/env python3
"""
Test script to verify lead qualification fixes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.lead_qualification_service import analyze_lead_qualification_ai

def test_simple_greetings():
    """Test that simple greetings are not qualified as leads"""
    print("🧪 Testing Simple Greetings (Should NOT qualify)")
    print("=" * 50)
    
    simple_messages = [
        "Hi",
        "Hello",
        "Hey there",
        "Good morning",
        "How are you?",
        "Thanks",
        "Ok",
        "Yes"
    ]
    
    for message in simple_messages:
        is_qualified, confidence, reason, metadata = analyze_lead_qualification_ai(message, [])
        status = "❌ QUALIFIED (ERROR)" if is_qualified else "✅ NOT QUALIFIED (CORRECT)"
        print(f"{status} - '{message}' - Reason: {reason}")
    
    print()

def test_insufficient_conversation():
    """Test that messages without conversation history are not qualified"""
    print("🧪 Testing Insufficient Conversation Depth (Should NOT qualify)")
    print("=" * 60)
    
    business_messages = [
        "I need help with my business automation",
        "What are your pricing packages?",
        "Can you help with WhatsApp integration?"
    ]
    
    for message in business_messages:
        # Test with no conversation history
        is_qualified, confidence, reason, metadata = analyze_lead_qualification_ai(message, [])
        status = "❌ QUALIFIED (ERROR)" if is_qualified else "✅ NOT QUALIFIED (CORRECT)"
        print(f"{status} - '{message}' - Reason: {reason}")
    
    print()

def test_qualified_leads():
    """Test that genuine business leads with conversation history are qualified"""
    print("🧪 Testing Qualified Business Leads (Should qualify)")
    print("=" * 50)
    
    # Simulate a conversation history
    conversation_history = [
        {"role": "user", "content": "Hi, I'm looking for business automation solutions"},
        {"role": "assistant", "content": "Hello! I'd be happy to help with business automation. What specific challenges are you facing?"},
        {"role": "user", "content": "We need to automate our customer support for our e-commerce business"},
        {"role": "assistant", "content": "That's great! WhatsApp automation can really help with customer support. What's your current volume?"},
    ]
    
    qualified_messages = [
        "We handle about 500 customer inquiries per day and need to reduce response time. What are your pricing options for enterprise?",
        "I'm the CTO at TechCorp and we're evaluating automation solutions. Can we schedule a demo to discuss implementation?",
        "We're looking to integrate WhatsApp with our existing CRM. What's the timeline for implementation and what would it cost?"
    ]
    
    for message in qualified_messages:
        is_qualified, confidence, reason, metadata = analyze_lead_qualification_ai(message, conversation_history)
        status = "✅ QUALIFIED (CORRECT)" if is_qualified else "❌ NOT QUALIFIED (ERROR)"
        print(f"{status} - '{message[:50]}...' - Confidence: {confidence:.2f} - Score: {metadata.get('lead_score', 0)}")
    
    print()

def main():
    print("🔧 Lead Qualification Fix Test")
    print("=" * 40)
    print("Testing the updated lead qualification logic...")
    print()
    
    try:
        test_simple_greetings()
        test_insufficient_conversation()
        test_qualified_leads()
        
        print("✅ All tests completed!")
        print("\n📋 Summary:")
        print("- Simple greetings should NOT trigger Calendly")
        print("- Messages without conversation depth should NOT qualify")
        print("- Only genuine business leads with context should qualify")
        print("- Confidence threshold is now 0.85 (was 0.75)")
        print("- Minimum lead score is now 80 (was 70)")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()