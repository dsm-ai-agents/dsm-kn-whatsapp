#!/usr/bin/env python3
"""
Interactive Test for WhatsApp Bot Conversation Flow
Simulate real conversation with the bot using phone number 7033009600
"""

import sys
import os
import json
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_conversation_interactive():
    """
    Interactive conversation test - simulates real WhatsApp interaction
    """
    phone_number = "7033009600"
    conversation_history = []
    
    print("🤖 WhatsApp Bot Interactive Test")
    print("=" * 40)
    print(f"Testing with phone number: {phone_number}")
    print("Type messages as if you're chatting on WhatsApp")
    print("Type 'quit' to exit, 'history' to see conversation")
    print("=" * 40)
    
    while True:
        # Get user input
        user_message = input(f"\n📱 You ({phone_number}): ").strip()
        
        if user_message.lower() == 'quit':
            print("👋 Ending test session...")
            break
        
        if user_message.lower() == 'history':
            print("\n📜 Conversation History:")
            for i, msg in enumerate(conversation_history, 1):
                role_emoji = "👤" if msg['role'] == 'user' else "🤖"
                print(f"  {i}. {role_emoji} {msg['role'].title()}: {msg['content']}")
            continue
        
        if not user_message:
            continue
        
        print(f"\n🔍 Processing message: '{user_message}'")
        
        # Test lead qualification
        try:
            from src.services.lead_qualification_service import detect_and_process_qualified_lead
            
            is_qualified, status_message = detect_and_process_qualified_lead(
                user_message, phone_number, conversation_history
            )
            
            print(f"🎯 Lead Qualification: {'✅ QUALIFIED' if is_qualified else '❌ NOT QUALIFIED'}")
            print(f"📋 Status: {status_message}")
            
            if is_qualified:
                print("📅 Calendly link would be sent!")
                bot_response = f"🎯 Thanks for your interest in our business solutions!\n\nI'd love to schedule a quick 15-minute discovery call to discuss your specific needs.\n\nBook your call here: https://calendly.com/rianinfotech/discovery-call\n\nLooking forward to speaking with you! 🚀"
            else:
                # Simulate normal bot response
                bot_response = simulate_bot_response(user_message, conversation_history)
            
        except Exception as e:
            print(f"❌ Error in lead qualification: {e}")
            bot_response = "I'm here to help! How can I assist you today?"
        
        # Display bot response
        print(f"🤖 Bot: {bot_response}")
        
        # Update conversation history
        conversation_history.append({"role": "user", "content": user_message})
        conversation_history.append({"role": "assistant", "content": bot_response})
        
        # Show conversation stats
        print(f"📊 Conversation depth: {len(conversation_history)} messages")

def simulate_bot_response(message: str, history: list) -> str:
    """
    Simulate what the bot would respond (simplified version)
    """
    message_lower = message.lower()
    
    # Simple greeting responses
    if any(greeting in message_lower for greeting in ['hi', 'hello', 'hey']):
        return "Hello! Thank you for reaching out. How can I assist you today? If you have any questions about AI automation solutions or how they can benefit your organization, feel free to ask!"
    
    # Business-related responses
    if any(word in message_lower for word in ['business', 'automation', 'help', 'service']):
        return "I'd be happy to help! We specialize in AI automation solutions that can transform how businesses operate. What specific challenges is your organization facing? Are you looking to automate customer service, streamline workflows, or improve efficiency in a particular area?"
    
    # Pricing inquiries
    if any(word in message_lower for word in ['price', 'cost', 'pricing', 'package']):
        return "Great question! Our pricing depends on your specific needs and volume. We offer three main packages:\n\n• Starter ($299/month) - Up to 1,000 conversations\n• Business ($799/month) - Up to 5,000 conversations \n• Enterprise (Custom) - Unlimited conversations\n\nTo provide you with the most accurate pricing, I'd need to understand your requirements better. What's your expected message volume and what features are most important to you?"
    
    # Default response
    return "I understand you're interested in learning more. Could you tell me a bit more about what you're looking for? Are you exploring automation solutions for your business?"

def run_predefined_scenarios():
    """
    Run predefined test scenarios
    """
    print("\n🧪 Running Predefined Test Scenarios")
    print("=" * 45)
    
    scenarios = [
        {
            "name": "New User - Simple Greeting",
            "messages": ["Hi"],
            "expected_qualified": False
        },
        {
            "name": "Casual Inquiry",
            "messages": ["Hi", "How can you help?"],
            "expected_qualified": False
        },
        {
            "name": "Business Interest Development",
            "messages": [
                "Hi",
                "I'm looking for business automation solutions", 
                "We need to automate customer support for our e-commerce business",
                "We handle 500+ inquiries daily and need enterprise pricing options"
            ],
            "expected_qualified": True
        }
    ]
    
    for scenario in scenarios:
        print(f"\n📋 Scenario: {scenario['name']}")
        print("-" * 30)
        
        conversation_history = []
        final_qualified = False
        
        for i, message in enumerate(scenario['messages'], 1):
            print(f"Message {i}: '{message}'")
            
            try:
                from src.services.lead_qualification_service import detect_and_process_qualified_lead
                
                is_qualified, status = detect_and_process_qualified_lead(
                    message, "7033009600", conversation_history
                )
                
                if is_qualified:
                    final_qualified = True
                    print(f"  🎯 QUALIFIED at message {i}")
                    break
                else:
                    print(f"  ❌ Not qualified: {status}")
                
                # Update history
                conversation_history.append({"role": "user", "content": message})
                conversation_history.append({"role": "assistant", "content": "Bot response"})
                
            except Exception as e:
                print(f"  ❌ Error: {e}")
        
        # Check result
        if final_qualified == scenario['expected_qualified']:
            print(f"✅ CORRECT: {'Qualified' if final_qualified else 'Not qualified'} as expected")
        else:
            print(f"❌ INCORRECT: Expected {'qualified' if scenario['expected_qualified'] else 'not qualified'}, got {'qualified' if final_qualified else 'not qualified'}")

def main():
    print("🚀 WhatsApp Bot Testing Suite")
    print("Choose testing mode:")
    print("1. Interactive conversation test")
    print("2. Run predefined scenarios")
    print("3. Both")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice in ['1', '3']:
        test_conversation_interactive()
    
    if choice in ['2', '3']:
        run_predefined_scenarios()
    
    print("\n✅ Testing completed!")

if __name__ == "__main__":
    main()