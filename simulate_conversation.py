#!/usr/bin/env python3
"""
Simulate Conversation Flow - Test how the bot will behave with phone number 7033009600
"""

def simulate_conversation_with_7033009600():
    """
    Simulate the exact conversation flow that will happen with your number
    """
    phone_number = "7033009600"
    print(f"📱 Simulating WhatsApp Conversation with {phone_number}")
    print("=" * 60)
    
    # Simulate conversation history building
    conversation_history = []
    
    test_messages = [
        "Hi",
        "How can you help my organisation?",
        "We need to automate our customer support",
        "We handle about 500 customer inquiries per day and need enterprise pricing options"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n📨 Message {i}: User sends '{message}'")
        
        # Test lead qualification logic
        will_qualify = check_if_qualifies(message, conversation_history)
        
        if will_qualify:
            print("🎯 RESULT: ✅ QUALIFIED - Calendly link will be sent!")
            print("📅 Bot Response: Calendly invitation message")
            break
        else:
            print("🎯 RESULT: ❌ NOT QUALIFIED - Normal bot conversation continues")
            bot_response = generate_bot_response(message, i)
            print(f"🤖 Bot Response: {bot_response}")
        
        # Update conversation history
        conversation_history.append({"role": "user", "content": message})
        conversation_history.append({"role": "assistant", "content": "Bot response here"})
        
        print(f"📊 Conversation depth: {len(conversation_history)} messages")

def check_if_qualifies(message, history):
    """
    Check if message qualifies based on our new logic (without API calls)
    """
    # Check message length
    if not message or len(message.strip()) < 5:
        return False
    
    # Check for simple greetings
    simple_patterns = [
        'hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening',
        'thanks', 'thank you', 'ok', 'okay', 'yes', 'no', 'sure', 'fine',
        'how are you', 'what\'s up', 'wassup', 'sup', 'hola', 'namaste'
    ]
    
    message_lower = message.lower().strip()
    if any(pattern in message_lower for pattern in simple_patterns) and len(message.strip()) < 20:
        return False
    
    # Check conversation depth
    if not history or len(history) < 3:
        return False
    
    # Check for business indicators (simplified)
    business_keywords = [
        'business', 'company', 'enterprise', 'organization', 'pricing', 
        'automation', 'customer', 'inquiries', 'support', 'integration'
    ]
    
    has_business_context = any(keyword in message_lower for keyword in business_keywords)
    has_numbers = any(char.isdigit() for char in message)  # Volume indicators like "500"
    
    return has_business_context and has_numbers

def generate_bot_response(message, step):
    """
    Generate what the bot would respond at each step
    """
    message_lower = message.lower()
    
    if step == 1:  # First message
        return "Hello! Thank you for reaching out. How can I assist you today? If you have any questions about AI automation solutions or how they can benefit your organization, feel free to ask!"
    
    elif step == 2:  # Second message
        return "I'd be happy to help! We specialize in AI automation solutions that can transform how businesses operate. What specific challenges is your organization facing? Are you looking to automate customer service, streamline workflows, or improve efficiency in a particular area?"
    
    elif step == 3:  # Third message
        return "That's exactly what we help with! Our WhatsApp AI automation can handle high-volume customer support efficiently. We can automate responses, qualify leads, and seamlessly hand over to human agents when needed. What's your current customer inquiry volume, and what's your biggest challenge with support right now?"
    
    else:
        return "Based on your volume and needs, this sounds like a perfect fit for our Business or Enterprise package. Let me provide you with detailed information..."

def show_expected_behavior():
    """
    Show what the expected behavior should be
    """
    print("\n📋 Expected Behavior Summary")
    print("=" * 35)
    
    expectations = [
        {
            "message": "Hi",
            "behavior": "❌ No Calendly - Friendly greeting response"
        },
        {
            "message": "How can you help my organisation?", 
            "behavior": "❌ No Calendly - Ask for more details"
        },
        {
            "message": "We need to automate our customer support",
            "behavior": "❌ No Calendly - Provide info, ask specifics"
        },
        {
            "message": "We handle 500+ inquiries daily and need enterprise pricing",
            "behavior": "✅ CALENDLY - Qualified business lead!"
        }
    ]
    
    for i, exp in enumerate(expectations, 1):
        print(f"{i}. '{exp['message'][:40]}...'")
        print(f"   → {exp['behavior']}")

def main():
    print("🤖 WhatsApp Bot Conversation Simulation")
    print("Testing with your number: 7033009600")
    print()
    
    simulate_conversation_with_7033009600()
    show_expected_behavior()
    
    print("\n✅ Simulation Complete!")
    print("\n🚀 What happens next:")
    print("1. Deploy these changes to your production server")
    print("2. Send 'Hi' to your WhatsApp bot - should get normal response")
    print("3. Continue the conversation naturally")
    print("4. Only when you mention business needs + volume should you get Calendly")
    
    print(f"\n📱 Test it with: 7033009600")
    print("Expected: Natural conversation → Business discussion → Calendly offer")

if __name__ == "__main__":
    main()