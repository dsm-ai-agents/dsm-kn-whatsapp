#!/usr/bin/env python3
"""
WhatsApp Connection Monitor
==========================
Monitor and diagnose WhatsApp Web connection issues with WaSender API.
"""

import requests
import json
import os
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class WhatsAppConnectionMonitor:
    def __init__(self):
        self.api_token = os.getenv('WASENDER_API_TOKEN')
        self.base_url = "https://wasenderapi.com/api"
        self.headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        } if self.api_token else None
        
    def check_connection_status(self):
        """Check current WhatsApp Web connection status"""
        print("🔍 Checking WhatsApp Web Connection Status...")
        print("=" * 50)
        
        try:
            response = requests.get(f"{self.base_url}/status", headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'unknown')
                
                if status == 'connected':
                    print("✅ WhatsApp Web Status: CONNECTED")
                    return True
                else:
                    print(f"❌ WhatsApp Web Status: {status.upper()}")
                    return False
            else:
                print(f"❌ API Error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Connection Error: {e}")
            return False
    
    def send_test_message(self, test_number="917033009600"):
        """Send a test message and monitor delivery"""
        print(f"\n📱 Sending Test Message to {test_number}...")
        print("=" * 50)
        
        payload = {
            'to': test_number,
            'text': f'🔧 Connection Test - {datetime.now().strftime("%H:%M:%S")}'
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/send-message", 
                headers=self.headers, 
                json=payload, 
                timeout=20
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    msg_id = data['data'].get('msgId')
                    status = data['data'].get('status')
                    print(f"✅ Message Sent: ID={msg_id}, Status={status}")
                    
                    if status == 'in_progress':
                        print("⏳ Message queued - checking delivery...")
                        return self.monitor_message_delivery(msg_id, test_number)
                    else:
                        return True
                else:
                    print(f"❌ Send Failed: {data}")
                    return False
            else:
                print(f"❌ API Error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            return False
    
    def monitor_message_delivery(self, message_id, phone_number, timeout=30):
        """Monitor message delivery status"""
        print(f"🔍 Monitoring delivery for message {message_id}...")
        
        start_time = time.time()
        
        while (time.time() - start_time) < timeout:
            # Check if message was delivered by looking at WhatsApp Web
            print(f"⏳ Waiting... ({int(time.time() - start_time)}s elapsed)")
            time.sleep(5)
            
            # In a real scenario, you would check delivery receipts
            # For now, we'll just wait and ask the user to check
        
        print("\n🤔 Please check your WhatsApp manually:")
        print(f"   - Open WhatsApp on your phone")
        print(f"   - Look for the test message to {phone_number}")
        print(f"   - Check if it was delivered")
        
        delivered = input("\n❓ Did you receive the test message? (y/n): ").lower().strip()
        return delivered in ['y', 'yes', '1', 'true']
    
    def get_troubleshooting_steps(self):
        """Provide troubleshooting steps"""
        print("\n🛠️  TROUBLESHOOTING STEPS")
        print("=" * 50)
        
        print("1. 📱 Check Your Phone:")
        print("   ✓ Ensure your phone has internet connection")
        print("   ✓ WhatsApp is running and active")
        print("   ✓ Phone is not in airplane mode")
        
        print("\n2. 💻 Check WhatsApp Web:")
        print("   ✓ Go to https://web.whatsapp.com")
        print("   ✓ Ensure you're logged in")
        print("   ✓ Check if session is active (green circle)")
        
        print("\n3. 🔧 Check WaSender Dashboard:")
        print("   ✓ Go to your WaSender dashboard")
        print("   ✓ Check WhatsApp Web connection status")
        print("   ✓ Scan QR code if needed")
        print("   ✓ Verify API token is active")
        
        print("\n4. 🔄 Reset Connection:")
        print("   ✓ Logout from WhatsApp Web")
        print("   ✓ Clear browser cache")
        print("   ✓ Login again and scan QR code")
        print("   ✓ Restart WaSender connection")
        
        print("\n5. 📞 Contact Support:")
        print("   ✓ If issues persist, contact WaSender support")
        print("   ✓ Provide your API token and error details")
    
    def run_full_diagnosis(self):
        """Run complete diagnosis"""
        print("🔧 WhatsApp Connection Monitor")
        print("=" * 50)
        print(f"Timestamp: {datetime.now()}")
        
        # Step 1: Check API connection
        api_connected = self.check_connection_status()
        
        # Step 2: Send test message
        if api_connected:
            message_delivered = self.send_test_message()
        else:
            message_delivered = False
        
        # Step 3: Provide summary and recommendations
        print("\n📊 DIAGNOSIS SUMMARY")
        print("=" * 50)
        print(f"API Connected: {'✅' if api_connected else '❌'}")
        print(f"Message Delivered: {'✅' if message_delivered else '❌'}")
        
        if not api_connected:
            print("\n🚨 CRITICAL ISSUE: API Connection Failed")
            print("   - Check your WASENDER_API_TOKEN")
            print("   - Verify your WaSender account is active")
            
        elif not message_delivered:
            print("\n🚨 DELIVERY ISSUE: Messages Not Reaching WhatsApp")
            print("   - WhatsApp Web session may be disconnected")
            print("   - Phone may be offline")
            print("   - WaSender connection needs reset")
            
            self.get_troubleshooting_steps()
        else:
            print("\n✅ ALL GOOD: WhatsApp connection is working!")
            print("   - Messages should be delivered normally")
            print("   - Monitor delivery for any future issues")

if __name__ == "__main__":
    monitor = WhatsAppConnectionMonitor()
    monitor.run_full_diagnosis() 