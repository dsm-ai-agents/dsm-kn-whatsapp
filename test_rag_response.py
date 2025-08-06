#!/usr/bin/env python3
"""
Test RAG-Enhanced Response Generation
Demonstrates the full RAG system with customer context
"""

import os
import sys
import logging

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.handlers.ai_handler_rag import generate_ai_response_with_rag

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_rag_responses():
    """Test RAG-enhanced responses with different customer contexts"""
    
    print("🧠 Testing RAG-Enhanced Response Generation")
    print("=" * 60)
    
    # Test scenarios
    test_scenarios = [
        {
            'name': 'Healthcare Qualified Lead',
            'message': 'What AI automation solutions do you have for healthcare?',
            'customer_context': {
                'name': 'Dr. Sarah Johnson',
                'company': 'Regional Medical Center',
                'industry': 'healthcare',
                'lead_status': 'qualified',
                'phone_number': '+1234567890'
            }
        },
        {
            'name': 'Small Business Pricing Inquiry',
            'message': 'How much does your Business Package cost?',
            'customer_context': {
                'name': 'Mike Chen',
                'company': 'TechStart Inc',
                'industry': 'technology',
                'lead_status': 'new',
                'phone_number': '+1234567891'
            }
        },
        {
            'name': 'General Services Inquiry',
            'message': 'What services do you offer?',
            'customer_context': {
                'name': 'Lisa Rodriguez',
                'company': 'GrowthCorp',
                'lead_status': 'contacted',
                'phone_number': '+1234567892'
            }
        },
        {
            'name': 'Anonymous User',
            'message': 'Tell me about your company',
            'customer_context': None
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n🔍 Test {i}: {scenario['name']}")
        print("-" * 40)
        print(f"Message: {scenario['message']}")
        
        if scenario['customer_context']:
            context = scenario['customer_context']
            print(f"Customer: {context.get('name', 'Unknown')} from {context.get('company', 'Unknown Company')}")
            print(f"Industry: {context.get('industry', 'Unknown')}, Status: {context.get('lead_status', 'Unknown')}")
        else:
            print("Customer: Anonymous")
        
        print("\n🤖 RAG-Enhanced Response:")
        print("-" * 30)
        
        try:
            response = generate_ai_response_with_rag(
                message_text=scenario['message'],
                customer_context=scenario['customer_context']
            )
            
            print(response)
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("\n" + "=" * 60)
    
    print("\n✅ RAG testing completed!")

if __name__ == "__main__":
    test_rag_responses() 