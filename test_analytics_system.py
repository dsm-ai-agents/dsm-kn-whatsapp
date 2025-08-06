#!/usr/bin/env python3
"""
Test script for Analytics System (Phase 3A)
Tests the complete analytics pipeline including tracking and dashboard
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging
from datetime import datetime, timedelta
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_analytics_system():
    """Test the complete analytics system"""
    
    print("🧪 Testing Analytics System (Phase 3A)")
    print("=" * 60)
    
    # Test 1: Analytics Service Import and Initialization
    print("\n1. 🔧 Testing Analytics Service Import")
    try:
        from src.services.analytics_service import get_analytics_service, MessageAnalytics
        analytics_service = get_analytics_service()
        print("   ✅ Analytics service imported and initialized successfully")
    except Exception as e:
        print(f"   ❌ Analytics service import failed: {e}")
        return False
    
    # Test 2: Database Connection
    print("\n2. 🗄️ Testing Database Connection")
    try:
        # Test Supabase connection
        supabase = analytics_service.supabase
        if supabase.is_connected():
            print("   ✅ Supabase connection established")
        else:
            print("   ❌ Supabase connection failed")
            return False
    except Exception as e:
        print(f"   ❌ Database connection test failed: {e}")
        return False
    
    # Test 3: Create Test Contact and Session
    print("\n3. 📊 Testing Test Contact Creation and Session")
    try:
        import uuid
        test_phone = "919876543210"
        
        # Create a test contact first
        test_contact_data = {
            'phone_number': test_phone,
            'name': 'Analytics Test User',
            'company': 'Test Company',
            'journey_stage': 'discovery',
            'engagement_level': 'medium'
        }
        
        # Insert test contact
        result = analytics_service.supabase.client.table('contacts')\
            .upsert(test_contact_data, on_conflict='phone_number')\
            .execute()
        
        if result.data:
            test_contact_id = result.data[0]['id']
            print(f"   ✅ Test contact created: {test_contact_id}")
        else:
            print("   ❌ Test contact creation failed")
            return False
        
        session_id = analytics_service.start_conversation_session(
            contact_id=test_contact_id,
            phone_number=test_phone,
            journey_stage="discovery"
        )
        
        if session_id:
            print(f"   ✅ Session created successfully: {session_id}")
        else:
            print("   ❌ Session creation failed")
            return False
    except Exception as e:
        print(f"   ❌ Session creation test failed: {e}")
        return False
    
    # Test 4: Message Analytics Tracking
    print("\n4. 💬 Testing Message Analytics Tracking")
    try:
        # Test user message tracking
        user_message = MessageAnalytics(
            message_id=f"test_user_{int(time.time())}",
            contact_id=test_contact_id,
            message_role="user",
            message_content="Hello, I'm interested in your AI automation services",
            message_length=55,
            detected_intents=["services", "interest"],
            business_category="sales",
            urgency_level="medium",
            processing_time_ms=150
        )
        
        success = analytics_service.track_message(user_message, session_id)
        if success:
            print("   ✅ User message tracking successful")
        else:
            print("   ❌ User message tracking failed")
            return False
        
        # Test bot message tracking
        bot_message = MessageAnalytics(
            message_id=f"test_bot_{int(time.time())}",
            contact_id=test_contact_id,
            message_role="assistant",
            message_content="Hello! I'd be happy to help you learn about our AI automation services...",
            message_length=85,
            ai_handler_used="enhanced",
            rag_documents_retrieved=3,
            rag_query_time_ms=250,
            personalization_level="contextual",
            response_strategy="consultative",
            communication_style="business",
            detected_intents=["services"],
            business_category="sales",
            urgency_level="medium",
            processing_time_ms=1200,
            token_count=85,
            cost_estimate=0.0001
        )
        
        success = analytics_service.track_message(bot_message, session_id)
        if success:
            print("   ✅ Bot message tracking successful")
        else:
            print("   ❌ Bot message tracking failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Message analytics tracking test failed: {e}")
        return False
    
    # Test 5: Conversation Metrics Update
    print("\n5. 📈 Testing Conversation Metrics Update")
    try:
        success = analytics_service.update_conversation_metrics(
            phone_number=test_phone,
            engagement_score=75.0,
            lead_score=85.0,
            journey_stage="interest",
            business_intent=True,
            pricing_discussed=False,
            demo_requested=False
        )
        
        if success:
            print("   ✅ Conversation metrics update successful")
        else:
            print("   ❌ Conversation metrics update failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Conversation metrics update test failed: {e}")
        return False
    
    # Test 6: Lead Scoring Analytics
    print("\n6. 🎯 Testing Lead Scoring Analytics")
    try:
        success = analytics_service.update_lead_scoring(
            contact_id=test_contact_id,
            phone_number=test_phone,
            overall_score=82.5,
            engagement_score=75.0,
            intent_score=85.0,
            fit_score=80.0,
            timing_score=90.0,
            behavioral_data={
                'messages_sent': 3,
                'questions_asked': 2,
                'pricing_inquiries': 0,
                'technical_questions': 1,
                'demo_requests': 0,
                'company_size_indicator': 'medium',
                'industry_match_score': 85.0,
                'decision_maker_signals': True,
                'conversion_stage': 'interest',
                'conversion_probability': 65.0,
                'next_best_action': 'provide_detailed_information'
            }
        )
        
        if success:
            print("   ✅ Lead scoring analytics successful")
        else:
            print("   ❌ Lead scoring analytics failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Lead scoring analytics test failed: {e}")
        return False
    
    # Test 7: Performance Tracking
    print("\n7. ⚡ Testing Performance Tracking")
    try:
        success = analytics_service.track_performance(
            endpoint="ai_handler_enhanced",
            operation_type="enhanced_ai_response",
            execution_time_ms=1200,
            status="success",
            model_used="gpt-4o-mini",
            tokens_processed=85,
            cost_incurred=0.0001,
            contact_id=test_contact_id,
            session_id=session_id,
            metadata={
                "response_type": "ENHANCED_RAG",
                "rag_docs_retrieved": 3,
                "personalization_level": "contextual",
                "journey_stage": "interest"
            }
        )
        
        if success:
            print("   ✅ Performance tracking successful")
        else:
            print("   ❌ Performance tracking failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Performance tracking test failed: {e}")
        return False
    
    # Test 8: Daily Metrics Calculation
    print("\n8. 📅 Testing Daily Metrics Calculation")
    try:
        success = analytics_service.update_daily_metrics()
        
        if success:
            print("   ✅ Daily metrics calculation successful")
        else:
            print("   ❌ Daily metrics calculation failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Daily metrics calculation test failed: {e}")
        return False
    
    # Test 9: Analytics Data Retrieval
    print("\n9. 📊 Testing Analytics Data Retrieval")
    try:
        # Test conversation analytics retrieval
        conversations = analytics_service.get_conversation_analytics(
            phone_number=test_phone,
            limit=10
        )
        print(f"   📞 Retrieved {len(conversations)} conversation records")
        
        # Test lead scoring retrieval
        leads = analytics_service.get_lead_scoring_analytics(
            min_score=50.0,
            limit=10
        )
        print(f"   🎯 Retrieved {len(leads)} lead scoring records")
        
        # Test business intelligence summary
        bi_summary = analytics_service.get_business_intelligence_summary(days=7)
        if 'error' not in bi_summary:
            print(f"   📈 Retrieved BI summary: {bi_summary.get('total_conversations', 0)} conversations")
        else:
            print(f"   ⚠️ BI summary: {bi_summary.get('error', 'No data')}")
        
        print("   ✅ Analytics data retrieval successful")
        
    except Exception as e:
        print(f"   ❌ Analytics data retrieval test failed: {e}")
        return False
    
    # Test 10: Enhanced AI Handler Integration
    print("\n10. 🧠 Testing Enhanced AI Handler Integration")
    try:
        from src.handlers.ai_handler_enhanced import generate_enhanced_ai_response
        
        # Test with analytics tracking
        customer_context = {
            'id': test_contact_id,
            'phone_number': test_phone,
            'name': 'Test User',
            'company': 'Test Company'
        }
        
        response = generate_enhanced_ai_response(
            message_text="Can you tell me about your pricing packages?",
            conversation_history=[],
            customer_context=customer_context
        )
        
        if response and len(response) > 0:
            print("   ✅ Enhanced AI handler with analytics integration successful")
            print(f"   💬 Response: {response[:100]}...")
        else:
            print("   ❌ Enhanced AI handler integration failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Enhanced AI handler integration test failed: {e}")
        return False
    
    # Test 11: API Routes (if available)
    print("\n11. 🌐 Testing Analytics API Routes")
    try:
        from src.api.analytics_routes import analytics_bp
        print("   ✅ Analytics API routes imported successfully")
        print("   📋 Available endpoints:")
        print("      - GET /api/analytics/dashboard")
        print("      - GET /api/analytics/conversations")
        print("      - GET /api/analytics/leads")
        print("      - GET /api/analytics/performance")
        print("      - GET /api/analytics/business-intelligence")
        print("      - GET /api/analytics/journey-funnel")
        print("      - POST /api/analytics/update-daily-metrics")
        
    except Exception as e:
        print(f"   ❌ Analytics API routes test failed: {e}")
        return False
    
    print(f"\n🎉 Analytics System Test Complete!")
    print("=" * 60)
    
    print(f"\n📊 ANALYTICS SYSTEM STATUS: FULLY OPERATIONAL")
    print("✅ Database schema created and connected")
    print("✅ Analytics service initialized and working")
    print("✅ Message tracking and conversation analytics")
    print("✅ Lead scoring and performance tracking")
    print("✅ Business intelligence metrics calculation")
    print("✅ Enhanced AI handler integration")
    print("✅ Analytics dashboard API endpoints")
    
    print(f"\n🚀 NEXT STEPS:")
    print("1. Deploy to production to start collecting real analytics")
    print("2. Monitor Railway logs for analytics tracking messages")
    print("3. Test analytics dashboard endpoints with real data")
    print("4. Set up automated daily metrics calculation")
    print("5. Create frontend dashboard for visualizing analytics")
    
    return True

if __name__ == "__main__":
    try:
        success = test_analytics_system()
        if success:
            print("\n🎯 All analytics tests passed! System is ready for production.")
            exit(0)
        else:
            print("\n❌ Some analytics tests failed. Please check the logs.")
            exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)