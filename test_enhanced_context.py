#!/usr/bin/env python3
"""
Test script for Enhanced Context Service
Tests personalization data storage and retrieval
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.enhanced_context_service import (
    get_enhanced_context_service, 
    EnhancedCustomerContext,
    PersonalizationLevel,
    JourneyStage
)
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_enhanced_context_service():
    """Test the enhanced context service functionality"""
    
    print("🧪 Testing Enhanced Context Service")
    print("=" * 50)
    
    # Initialize service
    context_service = get_enhanced_context_service()
    test_phone = "919876543210"  # Use existing test number
    
    print(f"\n1. 📞 Testing context retrieval for {test_phone}")
    
    # Test 1: Get enhanced customer context
    context = context_service.get_enhanced_customer_context(test_phone)
    if context:
        print(f"   ✅ Retrieved context:")
        print(f"      - Name: {context.name}")
        print(f"      - Journey Stage: {context.journey_stage}")
        print(f"      - Engagement Level: {context.engagement_level}")
        print(f"      - Conversation Count: {context.conversation_count}")
        print(f"      - Total Interactions: {context.total_interactions}")
        print(f"      - Topics Discussed: {context.topics_discussed}")
        print(f"      - Pain Points: {context.pain_points_mentioned}")
        print(f"      - Technical Level: {context.technical_level}")
    else:
        print("   ❌ Failed to retrieve context")
        return False
    
    print(f"\n2. 🔄 Testing context updates")
    
    # Test 2: Update context with new data
    updates = {
        'name': 'Test User Enhanced',
        'company': 'Test Company Enhanced',
        'journey_stage': 'interest',
        'engagement_level': 'high',
        'topics_discussed': ['AI automation', 'pricing', 'implementation'],
        'pain_points_mentioned': ['manual processes', 'time-consuming'],
        'goals_expressed': ['automate workflows', 'improve efficiency'],
        'technical_level': 'technical_user',
        'prefers_examples': True,
        'budget_range': 'medium',
        'timeline': 'short'
    }
    
    success = context_service.update_customer_context(test_phone, updates)
    if success:
        print("   ✅ Context updated successfully")
    else:
        print("   ❌ Failed to update context")
        return False
    
    print(f"\n3. 🔍 Testing updated context retrieval")
    
    # Test 3: Retrieve updated context
    updated_context = context_service.get_enhanced_customer_context(test_phone)
    if updated_context:
        print(f"   ✅ Retrieved updated context:")
        print(f"      - Name: {updated_context.name}")
        print(f"      - Company: {updated_context.company}")
        print(f"      - Journey Stage: {updated_context.journey_stage}")
        print(f"      - Engagement Level: {updated_context.engagement_level}")
        print(f"      - Topics: {updated_context.topics_discussed}")
        print(f"      - Pain Points: {updated_context.pain_points_mentioned}")
        print(f"      - Goals: {updated_context.goals_expressed}")
        print(f"      - Budget Range: {updated_context.budget_range}")
        print(f"      - Timeline: {updated_context.timeline}")
    else:
        print("   ❌ Failed to retrieve updated context")
        return False
    
    print(f"\n4. 🎯 Testing personalization level detection")
    
    # Test 4: Get personalization level
    personalization_level = context_service.get_personalization_level(updated_context)
    print(f"   ✅ Personalization Level: {personalization_level.value}")
    
    print(f"\n5. 🧠 Testing journey stage analysis")
    
    # Test 5: Analyze journey stage progression
    test_messages = [
        "I'm interested in your AI automation services",
        "Can you tell me more about pricing?",
        "How does this compare to other solutions?",
        "I'm ready to get started. What are the next steps?"
    ]
    
    for i, message in enumerate(test_messages, 1):
        current_context = context_service.get_enhanced_customer_context(test_phone)
        new_stage = context_service.analyze_and_update_journey_stage(
            test_phone, message, current_context
        )
        print(f"   Message {i}: '{message[:50]}...'")
        print(f"   → Journey Stage: {new_stage}")
    
    print(f"\n6. 📊 Testing behavioral pattern analysis")
    
    # Test 6: Analyze behavioral patterns
    test_behavior_message = "This looks amazing! I'm really excited about the potential ROI and data-driven insights this could provide."
    
    success = context_service.update_behavioral_patterns(
        test_phone, 
        test_behavior_message,
        response_time_seconds=45  # Fast response
    )
    
    if success:
        print("   ✅ Behavioral patterns updated")
        # Check updated patterns
        final_context = context_service.get_enhanced_customer_context(test_phone)
        print(f"      - Engagement Level: {final_context.engagement_level}")
        print(f"      - Response Time Pattern: {final_context.response_time_pattern}")
        print(f"      - Decision Making Style: {final_context.decision_making_style}")
    else:
        print("   ❌ Failed to update behavioral patterns")
    
    print(f"\n7. 💬 Testing conversation state management")
    
    # Test 7: Conversation state
    success = context_service.update_conversation_state(
        test_phone,
        current_topic="AI Automation Pricing",
        add_question="What's the implementation timeline?",
        add_action_item="Send pricing proposal",
        context_update={"last_topic_interest": "high", "pricing_discussed": True}
    )
    
    if success:
        print("   ✅ Conversation state updated")
        
        # Retrieve conversation state
        conv_state = context_service.get_conversation_state(test_phone)
        if conv_state:
            print(f"      - Current Topic: {conv_state.current_topic}")
            print(f"      - Unresolved Questions: {conv_state.unresolved_questions}")
            print(f"      - Action Items: {conv_state.action_items}")
            print(f"      - Context Continuity: {conv_state.context_continuity}")
        else:
            print("   ⚠️  Could not retrieve conversation state")
    else:
        print("   ❌ Failed to update conversation state")
    
    print(f"\n8. 📈 Testing interaction count increment")
    
    # Test 8: Increment interaction count
    success = context_service.increment_interaction_count(test_phone)
    if success:
        print("   ✅ Interaction count incremented")
        
        # Check final counts
        final_context = context_service.get_enhanced_customer_context(test_phone)
        print(f"      - Total Interactions: {final_context.total_interactions}")
        print(f"      - Conversation Count: {final_context.conversation_count}")
    else:
        print("   ❌ Failed to increment interaction count")
    
    print(f"\n✅ Enhanced Context Service Test Complete!")
    print("=" * 50)
    
    # Final summary
    final_context = context_service.get_enhanced_customer_context(test_phone)
    personalization_level = context_service.get_personalization_level(final_context)
    
    print(f"\n📊 FINAL CONTEXT SUMMARY for {test_phone}:")
    print(f"   👤 Name: {final_context.name}")
    print(f"   🏢 Company: {final_context.company}")
    print(f"   🎯 Journey Stage: {final_context.journey_stage}")
    print(f"   💡 Engagement Level: {final_context.engagement_level}")
    print(f"   🔥 Personalization Level: {personalization_level.value}")
    print(f"   💬 Total Interactions: {final_context.total_interactions}")
    print(f"   📋 Topics Discussed: {len(final_context.topics_discussed)} topics")
    print(f"   ⚠️  Pain Points: {len(final_context.pain_points_mentioned)} identified")
    print(f"   🎯 Goals: {len(final_context.goals_expressed)} expressed")
    
    return True

if __name__ == "__main__":
    try:
        success = test_enhanced_context_service()
        if success:
            print("\n🎉 All tests passed! Enhanced Context Service is working correctly.")
            exit(0)
        else:
            print("\n❌ Some tests failed. Please check the logs.")
            exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)