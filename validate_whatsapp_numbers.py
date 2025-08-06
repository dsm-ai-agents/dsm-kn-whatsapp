#!/usr/bin/env python3
"""
WhatsApp Number Validation Tool
==============================
Validate if phone numbers have WhatsApp before sending messages.
"""

import requests
import json
import os
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class WhatsAppNumberValidator:
    def __init__(self):
        self.api_token = os.getenv('WASENDER_API_TOKEN')
        self.base_url = "https://wasenderapi.com/api"
        self.headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        } if self.api_token else None
        
    def format_phone_number(self, phone_number):
        """Format phone number with proper country code"""
        clean_number = phone_number.replace('+', '').replace('-', '').replace(' ', '')
        
        if clean_number.startswith('91') and len(clean_number) == 12:
            return clean_number  # Already has country code
        elif len(clean_number) == 10 and clean_number.startswith(('6', '7', '8', '9')):
            return f"91{clean_number}"  # Add India country code
        else:
            return clean_number  # Use as-is for other formats
    
    def check_whatsapp_number(self, phone_number):
        """
        Check if a phone number has WhatsApp by attempting to send a minimal message
        """
        formatted_number = self.format_phone_number(phone_number)
        
        print(f"🔍 Checking: {phone_number} → {formatted_number}")
        
        # Send a very small test message
        payload = {
            'to': formatted_number,
            'text': '.'  # Minimal message to test
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/send-message",
                headers=self.headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    msg_id = data['data'].get('msgId')
                    status = data['data'].get('status')
                    
                    # Wait a bit to see if it fails quickly
                    time.sleep(2)
                    
                    return {
                        'number': formatted_number,
                        'original': phone_number,
                        'has_whatsapp': True,
                        'status': status,
                        'message_id': msg_id,
                        'result': 'success'
                    }
                else:
                    return {
                        'number': formatted_number,
                        'original': phone_number,
                        'has_whatsapp': False,
                        'status': 'failed',
                        'error': data.get('message', 'Unknown error'),
                        'result': 'failed'
                    }
            else:
                return {
                    'number': formatted_number,
                    'original': phone_number,
                    'has_whatsapp': False,
                    'status': 'api_error',
                    'error': f"HTTP {response.status_code}",
                    'result': 'error'
                }
                
        except Exception as e:
            return {
                'number': formatted_number,
                'original': phone_number,
                'has_whatsapp': False,
                'status': 'exception',
                'error': str(e),
                'result': 'error'
            }
    
    def validate_numbers_batch(self, phone_numbers):
        """Validate multiple phone numbers"""
        results = []
        
        print(f"📋 Validating {len(phone_numbers)} phone numbers...")
        print("=" * 60)
        
        for i, number in enumerate(phone_numbers, 1):
            print(f"\n[{i}/{len(phone_numbers)}] ", end="")
            result = self.check_whatsapp_number(number)
            results.append(result)
            
            # Show result
            if result['has_whatsapp']:
                print(f"✅ {result['original']} → {result['number']} (WhatsApp: YES)")
            else:
                print(f"❌ {result['original']} → {result['number']} (WhatsApp: NO - {result.get('error', 'Unknown')})")
            
            # Rate limiting delay
            if i < len(phone_numbers):
                time.sleep(1)
        
        return results
    
    def generate_report(self, results):
        """Generate validation report"""
        valid_numbers = [r for r in results if r['has_whatsapp']]
        invalid_numbers = [r for r in results if not r['has_whatsapp']]
        
        print(f"\n📊 VALIDATION REPORT")
        print("=" * 60)
        print(f"Total Numbers Checked: {len(results)}")
        print(f"✅ Valid WhatsApp Numbers: {len(valid_numbers)}")
        print(f"❌ Invalid/No WhatsApp: {len(invalid_numbers)}")
        print(f"Success Rate: {len(valid_numbers)/len(results)*100:.1f}%")
        
        if valid_numbers:
            print(f"\n✅ VALID NUMBERS (Send messages to these):")
            for result in valid_numbers:
                print(f"   {result['number']} (from {result['original']})")
        
        if invalid_numbers:
            print(f"\n❌ INVALID NUMBERS (Don't send messages to these):")
            for result in invalid_numbers:
                print(f"   {result['number']} (from {result['original']}) - {result.get('error', 'No WhatsApp')}")
        
        return {
            'total': len(results),
            'valid': len(valid_numbers),
            'invalid': len(invalid_numbers),
            'valid_numbers': [r['number'] for r in valid_numbers],
            'invalid_numbers': [r['number'] for r in invalid_numbers]
        }

def main():
    """Main function to run validation"""
    validator = WhatsAppNumberValidator()
    
    print("📱 WhatsApp Number Validation Tool")
    print("=" * 60)
    print(f"Timestamp: {datetime.now()}")
    
    # Test numbers from your CRM (replace with actual numbers from your system)
    test_numbers = [
        "7033009600",      # Your number (works)
        "917033009600",    # Same with country code
        "918294526021",    # Failed number from dashboard
        "919661810305",    # Your connected number
        "9876543210",      # Random test number
    ]
    
    print(f"\n🧪 Testing with sample numbers from your system:")
    for num in test_numbers:
        print(f"   - {num}")
    
    # Run validation
    results = validator.validate_numbers_batch(test_numbers)
    
    # Generate report
    report = validator.generate_report(results)
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    print("=" * 60)
    print("1. ✅ Only send messages to VALID numbers above")
    print("2. 🗑️  Remove INVALID numbers from your CRM contact lists")
    print("3. 📋 Before bulk campaigns, validate numbers first")
    print("4. 🔄 Re-validate numbers periodically (people change phones)")
    print("5. 📞 For business contacts, ask them to confirm their WhatsApp number")

if __name__ == "__main__":
    main() 