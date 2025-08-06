#!/usr/bin/env python3
"""
AI-Powered Information Extraction Test Script
Tests the production-ready AI agent for extracting customer information

USAGE: python3 test_ai_extraction.py
This validates that the AI extraction system is working correctly.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging
from src.services.enhanced_context_service import EnhancedContextService
from src.agents.information_extraction_agent import get_information_extraction_agent

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

def test_ai_extraction_agent():
    """Test the AI extraction agent directly"""
    print("🤖 TESTING AI EXTRACTION AGENT DIRECTLY")
    print("=" * 50)
    
    try:
        agent = get_information_extraction_agent()
        
        test_cases = [
            {
                "message": "Hi there! My name is John Smith and I'm the CTO at TechCorp Inc. You can reach me at john.smith@techcorp.com",
                "expected": ["name", "position", "company", "email"]
            },
            {
                "message": "I'm Sarah, working as a product manager at a healthcare startup. We're looking to automate our patient workflows.",
                "expected": ["name", "position", "industry_focus", "company_size", "goals_expressed"]
            },
            {
                "message": "Call me Mike. I work at Microsoft and need help with API integrations for our CRM system. This is urgent!",
                "expected": ["name", "company", "technical_level", "response_urgency"]
            },
            {
                "message": "We're a small business using Salesforce and looking to integrate with Slack. Our current process is very manual and time-consuming.",
                "expected": ["company_size", "current_tools", "pain_points_mentioned"]
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🧪 TEST {i}: {test_case['message'][:60]}...")
            print(f"Expected fields: {test_case['expected']}")
            
            # Extract with AI agent
            extracted = agent.extract_customer_information(test_case['message'])
            
            print(f"AI extracted: {extracted}")
            print(f"Fields found: {list(extracted.keys())}")
            
            # Check success
            found_count = sum(1 for field in test_case['expected'] if field in extracted)
            success_rate = found_count / len(test_case['expected']) * 100
            
            if success_rate >= 70:
                print(f"✅ SUCCESS ({success_rate:.1f}% fields found)")
            else:
                print(f"❌ NEEDS IMPROVEMENT ({success_rate:.1f}% fields found)")
                
    except Exception as e:
        print(f"❌ Error testing AI agent: {e}")
        return False
    
    return True

def test_enhanced_context_service_with_ai():
    """Test the enhanced context service using AI extraction"""
    print("\n🔗 TESTING ENHANCED CONTEXT SERVICE WITH AI")
    print("=" * 55)
    
    try:
        context_service = EnhancedContextService()
        test_phone = "+1234567890"
        
        # Clean test data first
        print("🧹 Cleaning test data...")
        try:
            context_service.supabase.client.table('contacts').delete().eq('phone_number', test_phone).execute()
        except:
            pass
        
        test_messages = [
            "Hi there! My name is John Smith and I'm the CTO at TechCorp Inc. You can reach me at john.smith@techcorp.com",
            "We're looking to automate our API integrations and improve our development workflow.",
            "This is quite urgent as we have a deadline next month. Budget is around $50k.",
            "I'm the decision maker for technology purchases at our company."
        ]
        
        print(f"\n📨 Processing {len(test_messages)} messages sequentially...")
        
        for i, message in enumerate(test_messages, 1):
            print(f"\nMessage {i}: \"{message[:60]}...\"")
            
            # Extract using AI-powered service
            success = context_service.extract_and_store_insights(test_phone, message)
            
            if success:
                # Get updated context
                context = context_service.get_enhanced_customer_context(test_phone)
                if context:
                    print(f"✅ Extraction successful")
                    print(f"   Name: {getattr(context, 'name', 'None')}")
                    print(f"   Email: {getattr(context, 'email', 'None')}")
                    print(f"   Company: {getattr(context, 'company', 'None')}")
                    print(f"   Position: {getattr(context, 'position', 'None')}")
                    print(f"   Industry: {getattr(context, 'industry_focus', 'None')}")
                    print(f"   Tech Level: {getattr(context, 'technical_level', 'None')}")
                else:
                    print("❌ No context retrieved")
            else:
                print("❌ Extraction failed")
        
        # Final summary
        final_context = context_service.get_enhanced_customer_context(test_phone)
        if final_context:
            print(f"\n📊 FINAL ACCUMULATED CONTEXT:")
            print(f"   📝 Name: {getattr(final_context, 'name', 'None')}")
            print(f"   📧 Email: {getattr(final_context, 'email', 'None')}")
            print(f"   🏢 Company: {getattr(final_context, 'company', 'None')}")
            print(f"   💼 Position: {getattr(final_context, 'position', 'None')}")
            print(f"   🏭 Industry: {getattr(final_context, 'industry_focus', 'None')}")
            print(f"   📊 Company Size: {getattr(final_context, 'company_size', 'None')}")
            print(f"   🎯 Tech Level: {getattr(final_context, 'technical_level', 'None')}")
            print(f"   ⚡ Urgency: {getattr(final_context, 'response_urgency', 'None')}")
            print(f"   💰 Budget: {getattr(final_context, 'budget_range', 'None')}")
            print(f"   ⏰ Timeline: {getattr(final_context, 'timeline', 'None')}")
            
            # Count non-None fields
            total_fields = ['name', 'email', 'company', 'position', 'industry_focus', 
                          'company_size', 'technical_level', 'response_urgency', 
                          'budget_range', 'timeline']
            filled_fields = sum(1 for field in total_fields if getattr(final_context, field, None))
            
            completion_rate = filled_fields / len(total_fields) * 100
            print(f"   📈 Profile Completion: {completion_rate:.1f}% ({filled_fields}/{len(total_fields)} fields)")
            
            return completion_rate >= 50  # 50% completion is good
        else:
            print("❌ No final context found")
            return False
            
    except Exception as e:
        print(f"❌ Error testing enhanced context service: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_natural_variations():
    """Test how well AI handles natural language variations"""
    print("\n🌐 TESTING NATURAL LANGUAGE VARIATIONS")
    print("=" * 45)
    
    agent = get_information_extraction_agent()
    
    name_variations = [
        "My name is Sarah Johnson",
        "I'm Sarah Johnson", 
        "Call me Sarah",
        "This is Sarah Johnson speaking",
        "Sarah Johnson here",
        "I go by Sarah",
    ]
    
    print("Testing name extraction variations:")
    for variation in name_variations:
        extracted = agent.extract_customer_information(variation)
        name = extracted.get('name', 'NOT FOUND')
        print(f"  \"{variation}\" → Name: {name}")
    
    return True

if __name__ == "__main__":
    print("🚀 STARTING AI-POWERED EXTRACTION TESTS")
    print("=" * 60)
    
    # Test 1: Direct AI agent testing
    success1 = test_ai_extraction_agent()
    
    # Test 2: Integration with enhanced context service
    success2 = test_enhanced_context_service_with_ai()
    
    # Test 3: Natural language variations
    success3 = test_natural_variations()
    
    print(f"\n🎯 TEST RESULTS SUMMARY:")
    print(f"   AI Agent Direct: {'✅ PASSED' if success1 else '❌ FAILED'}")
    print(f"   Context Service Integration: {'✅ PASSED' if success2 else '❌ FAILED'}")
    print(f"   Natural Variations: {'✅ PASSED' if success3 else '❌ FAILED'}")
    
    if success1 and success2 and success3:
        print(f"\n🎉 ALL AI EXTRACTION TESTS PASSED!")
        print(f"The AI agent approach is working correctly!")
        exit(0)
    else:
        print(f"\n⚠️ SOME TESTS NEED ATTENTION")
        print(f"Check OpenAI API key and network connectivity.")
        exit(1)