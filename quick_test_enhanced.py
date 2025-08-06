#!/usr/bin/env python3
"""
Quick test to verify Enhanced Personalization System is working
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_enhanced_system():
    """Test if the enhanced system can be imported and used"""
    
    print("🔍 Testing Enhanced Personalization System Components")
    print("=" * 60)
    
    # Test 1: Enhanced Context Service
    try:
        from src.services.enhanced_context_service import get_enhanced_context_service
        context_service = get_enhanced_context_service()
        print("✅ Enhanced Context Service: OK")
    except Exception as e:
        print(f"❌ Enhanced Context Service: FAILED - {e}")
        return False
    
    # Test 2: Personalization Engine
    try:
        from src.services.personalization_engine import get_personalization_engine
        personalization_engine = get_personalization_engine()
        print("✅ Personalization Engine: OK")
    except Exception as e:
        print(f"❌ Personalization Engine: FAILED - {e}")
        return False
    
    # Test 3: Enhanced AI Handler
    try:
        from src.handlers.ai_handler_enhanced import generate_enhanced_ai_response
        print("✅ Enhanced AI Handler: OK")
    except Exception as e:
        print(f"❌ Enhanced AI Handler: FAILED - {e}")
        return False
    
    # Test 4: Database Connection
    try:
        from src.core.supabase_client import get_supabase_manager
        supabase = get_supabase_manager()
        if supabase.is_connected():
            print("✅ Supabase Connection: OK")
        else:
            print("❌ Supabase Connection: FAILED - Not connected")
            return False
    except Exception as e:
        print(f"❌ Supabase Connection: FAILED - {e}")
        return False
    
    # Test 5: Test with actual phone number
    try:
        test_phone = "917033009600"  # Your test number
        context = context_service.get_enhanced_customer_context(test_phone)
        
        if context:
            print(f"✅ Context Retrieval: OK")
            print(f"   📊 Current Data:")
            print(f"      - Name: {context.name}")
            print(f"      - Journey Stage: {context.journey_stage}")
            print(f"      - Engagement Level: {context.engagement_level}")
            print(f"      - Conversation Count: {context.conversation_count}")
            print(f"      - Total Interactions: {context.total_interactions}")
        else:
            print("❌ Context Retrieval: FAILED - No context found")
            return False
            
    except Exception as e:
        print(f"❌ Context Retrieval: FAILED - {e}")
        return False
    
    # Test 6: Generate Enhanced Response
    try:
        test_message = "What are your AI automation services?"
        customer_context = {
            'phone_number': test_phone,
            'name': context.name or 'Test User',
            'company': context.company or 'Test Company'
        }
        
        print(f"\n🧪 Testing Enhanced Response Generation...")
        print(f"   📝 Message: {test_message}")
        
        response = generate_enhanced_ai_response(
            message_text=test_message,
            customer_context=customer_context
        )
        
        if response and len(response) > 50:
            print(f"✅ Enhanced Response Generation: OK")
            print(f"   💬 Response Preview: {response[:150]}...")
            
            # Check for personalization indicators
            personalization_found = any([
                context.name and context.name in response,
                "enhanced" in response.lower(),
                "personalized" in response.lower()
            ])
            
            if personalization_found:
                print(f"   🎯 Personalization Detected: YES")
            else:
                print(f"   ⚠️  Personalization Detected: UNCLEAR")
                
        else:
            print(f"❌ Enhanced Response Generation: FAILED - Invalid response")
            return False
            
    except Exception as e:
        print(f"❌ Enhanced Response Generation: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print(f"\n🎉 All Enhanced System Components Working!")
    return True

if __name__ == "__main__":
    try:
        success = test_enhanced_system()
        if success:
            print("\n✅ Enhanced Personalization System is operational!")
            print("\n🔍 Next Steps:")
            print("1. Check Railway logs for 'ENHANCED SUCCESS' messages")
            print("2. Verify message processor is calling enhanced handler")
            print("3. Test with fresh WhatsApp conversation")
        else:
            print("\n❌ Enhanced System has issues that need to be resolved")
    except Exception as e:
        print(f"\n💥 Test failed: {e}")
        import traceback
        traceback.print_exc()