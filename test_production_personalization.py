#!/usr/bin/env python3
"""
Production Test Script for Enhanced Personalization System
Tests the deployed system with real API calls
"""

import requests
import json
import time
from datetime import datetime

# Configuration
RAILWAY_BASE_URL = "https://your-railway-domain.com"  # Replace with your Railway URL
API_KEY = "your-api-key"  # Replace with your API key

def test_production_personalization():
    """Test the production enhanced personalization system"""
    
    print("🚀 Testing Production Enhanced Personalization System")
    print("=" * 60)
    
    # Test customer journey simulation
    test_phone = "919876543999"  # Use a test number
    
    journey_messages = [
        {
            "stage": "Discovery",
            "message": "Hi, I heard about your AI automation services. What do you do?",
            "expected_journey": "discovery"
        },
        {
            "stage": "Interest",
            "message": "That's exciting! We have manual processes that are time-consuming. How can AI help?",
            "expected_journey": "interest"
        },
        {
            "stage": "Evaluation", 
            "message": "We're comparing AI solutions. What makes you different? Show me technical specs and ROI.",
            "expected_journey": "evaluation"
        },
        {
            "stage": "Decision",
            "message": "I'm the CEO and decision maker. We're ready to proceed. What are the next steps?",
            "expected_journey": "decision"
        }
    ]
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    conversation_history = []
    
    for i, test_case in enumerate(journey_messages, 1):
        print(f"\n{i}. 🎭 Testing {test_case['stage']} Stage")
        print("-" * 40)
        print(f"📝 Message: {test_case['message']}")
        
        # Prepare test data
        test_data = {
            "message": test_case['message'],
            "customer_context": {
                "phone_number": test_phone,
                "name": "Production Test User",
                "company": "Test Corp"
            }
        }
        
        # If we have conversation history, include it
        if conversation_history:
            test_data["conversation_history"] = conversation_history
        
        try:
            # Call the test RAG endpoint
            response = requests.post(
                f"{RAILWAY_BASE_URL}/api/knowledge/test-rag",
                headers=headers,
                json=test_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result['data']['response']
                
                print(f"✅ Status: Success")
                print(f"💬 AI Response: {ai_response[:200]}...")
                
                # Update conversation history
                conversation_history.extend([
                    {"role": "user", "content": test_case['message']},
                    {"role": "assistant", "content": ai_response}
                ])
                
                # Check for personalization indicators
                personalization_indicators = {
                    "name_used": "Production Test User" in ai_response,
                    "company_mentioned": "Test Corp" in ai_response,
                    "calendly_link": "calendly.com" in ai_response,
                    "technical_content": any(word in ai_response.lower() for word in ["api", "integration", "technical", "specifications"]),
                    "business_content": any(word in ai_response.lower() for word in ["roi", "business", "efficiency", "automation"])
                }
                
                print(f"🎯 Personalization Indicators:")
                for indicator, present in personalization_indicators.items():
                    status = "✅" if present else "❌"
                    print(f"   {status} {indicator.replace('_', ' ').title()}: {present}")
                
            else:
                print(f"❌ Status: Failed ({response.status_code})")
                print(f"Error: {response.text}")
                
        except Exception as e:
            print(f"💥 Error: {e}")
        
        # Wait between requests
        if i < len(journey_messages):
            print("⏳ Waiting 3 seconds...")
            time.sleep(3)
    
    print(f"\n🎉 Production Test Complete!")
    print("=" * 60)

def test_knowledge_base_stats():
    """Test knowledge base statistics endpoint"""
    print("\n📊 Testing Knowledge Base Stats")
    print("-" * 30)
    
    try:
        headers = {"Authorization": f"Bearer {API_KEY}"}
        response = requests.get(f"{RAILWAY_BASE_URL}/api/knowledge/stats", headers=headers)
        
        if response.status_code == 200:
            stats = response.json()['data']
            print(f"✅ Knowledge Base Status: {stats.get('status', 'unknown')}")
            print(f"📄 Total Documents: {stats.get('total_documents', 0)}")
            print(f"📁 Total Categories: {stats.get('total_categories', 0)}")
            print(f"🕐 Last Updated: {stats.get('last_updated', 'never')}")
        else:
            print(f"❌ Failed to get stats: {response.status_code}")
            
    except Exception as e:
        print(f"💥 Error: {e}")

def test_knowledge_search():
    """Test knowledge base search functionality"""
    print("\n🔍 Testing Knowledge Search")
    print("-" * 30)
    
    test_queries = [
        "pricing packages",
        "healthcare solutions", 
        "AI automation services",
        "technical requirements"
    ]
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    for query in test_queries:
        try:
            response = requests.post(
                f"{RAILWAY_BASE_URL}/api/knowledge/search",
                headers=headers,
                json={"query": query}
            )
            
            if response.status_code == 200:
                results = response.json()['data']
                print(f"✅ Query: '{query}' → {results['total_results']} results")
            else:
                print(f"❌ Query: '{query}' → Failed ({response.status_code})")
                
        except Exception as e:
            print(f"💥 Query: '{query}' → Error: {e}")

if __name__ == "__main__":
    print("🔧 Production Testing Configuration:")
    print(f"   Railway URL: {RAILWAY_BASE_URL}")
    print(f"   API Key: {'*' * (len(API_KEY) - 4) + API_KEY[-4:] if len(API_KEY) > 4 else 'NOT_SET'}")
    print()
    
    if RAILWAY_BASE_URL == "https://your-railway-domain.com" or API_KEY == "your-api-key":
        print("⚠️  Please update RAILWAY_BASE_URL and API_KEY in the script before running!")
        print("   1. Replace RAILWAY_BASE_URL with your actual Railway domain")
        print("   2. Replace API_KEY with your actual API key")
        exit(1)
    
    try:
        # Run all tests
        test_knowledge_base_stats()
        test_knowledge_search()
        test_production_personalization()
        
        print(f"\n🎯 Next Steps:")
        print("1. Test with real WhatsApp messages")
        print("2. Monitor Railway logs for ENHANCED SUCCESS messages")
        print("3. Check Supabase database for context updates")
        print("4. Verify journey stage progression in real conversations")
        
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")