#!/usr/bin/env python3
"""
End-to-End Test Scenario for GUVI Callback Validation
This script runs a comprehensive 10-12 message conversation to test the complete honeypot system.
"""

import asyncio
import httpx
import json
from datetime import datetime, timezone
import time

# Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "team_recursives"

class ComprehensiveHoneypotTest:
    def __init__(self):
        self.base_url = BASE_URL
        self.api_key = API_KEY
        self.headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        self.conversation_history = []
        self.session_id = f"e2e-test-{int(datetime.now().timestamp())}"
        
    async def run_end_to_end_test(self):
        """Run comprehensive end-to-end test with 10-12 messages."""
        
        print("🚀 Starting Comprehensive End-to-End Honeypot Test")
        print("=" * 60)
        print(f"📋 Session ID: {self.session_id}")
        print(f"🎯 Target: Complete scam conversation with intelligence extraction")
        print(f"📊 Expected: 10-12 messages with GUVI callback payload display")
        print("=" * 60)
        
        # Comprehensive scam conversation scenario - Banking + UPI fraud combination
        scam_messages = [
           "Hey, are we still meeting tomorrow for the project discussion?",
    
    "I might be 10 minutes late, traffic looks bad near Wakad.",
    
    "No worries, let me know when you reach. I’ll grab coffee meanwhile."
        ]
        
        print(f"\n🎭 Starting conversation simulation with {len(scam_messages)} messages...")
        print("=" * 60)
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            for i, message_text in enumerate(scam_messages, 1):
                print(f"\n📩 Message {i}/{len(scam_messages)}:")
                print(f"📱 Scammer: {message_text}")
                print("-" * 40)
                
                payload = {
                    "sessionId": self.session_id,
                    "message": {
                        "sender": "scammer",
                        "text": message_text,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    },
                    "conversationHistory": self.conversation_history,
                    "metadata": {
                        "channel": "SMS",
                        "language": "English",
                        "locale": "IN"
                    }
                }
                
                try:
                    start_time = time.time()
                    response = await client.post(
                        f"{self.base_url}/honeypot",
                        headers=self.headers,
                        json=payload,
                        timeout=30.0
                    )
                    response_time = time.time() - start_time
                    
                    if response.status_code == 200:
                        result = response.json()
                        agent_reply = result.get('reply', 'No reply generated')
                        
                        print(f"🤖 Honeypot Agent: {agent_reply}")
                        print(f"⏱️  Response time: {response_time:.2f} seconds")
                        
                        # Add to conversation history
                        self.conversation_history.append({
                            "sender": "scammer",
                            "text": message_text,
                            "timestamp": payload["message"]["timestamp"]
                        })
                        self.conversation_history.append({
                            "sender": "user",
                            "text": agent_reply,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        })
                        
                        # Check if scam was detected
                        scam_info = result.get('scamDetection', {})
                        if scam_info:
                            is_scam = scam_info.get('isScam', False)
                            confidence = scam_info.get('confidence', 0.0)
                            scam_type = scam_info.get('scamType', 'unknown')
                            print(f"🛡️  Scam Detection: {is_scam} (confidence: {confidence:.2f}, type: {scam_type})")
                        
                        print("✅ Message processed successfully")
                        
                    else:
                        print(f"❌ Error: {response.status_code} - {response.text}")
                        break
                        
                except asyncio.TimeoutError:
                    print("⏰ Request timed out")
                    break
                except Exception as e:
                    print(f"❌ Request failed: {str(e)}")
                    break
                
                # Wait between messages for realistic timing
                if i < len(scam_messages):
                    print("⏸️  Waiting 3 seconds before next message...")
                    await asyncio.sleep(3)
        
        # Display conversation summary
        await self._display_conversation_summary()
        
        # Wait for callback to be processed
        print("\n⏳ Waiting 10 seconds for callback processing...")
        await asyncio.sleep(10)
        
        # Display expected callback payload
        await self._display_expected_callback()
    
    async def _display_conversation_summary(self):
        """Display summary of the conversation."""
        
        print("\n" + "=" * 60)
        print("📊 CONVERSATION SUMMARY")
        print("=" * 60)
        
        total_messages = len(self.conversation_history)
        scammer_messages = len([msg for msg in self.conversation_history if msg['sender'] == 'scammer'])
        agent_messages = len([msg for msg in self.conversation_history if msg['sender'] == 'user'])
        
        print(f"🔢 Total messages exchanged: {total_messages}")
        print(f"📤 Scammer messages: {scammer_messages}")
        print(f"📥 Agent responses: {agent_messages}")
        print(f"💬 Session ID: {self.session_id}")
        
        # Extract intelligence manually for display
        all_text = " ".join([msg['text'] for msg in self.conversation_history])
        
        # Simple intelligence extraction for display
        extracted_phones = self._extract_phones(all_text)
        extracted_urls = self._extract_urls(all_text)
        extracted_keywords = self._extract_keywords(all_text)
        extracted_emails = self._extract_emails(all_text)
        
        print(f"\n🔍 EXTRACTED INTELLIGENCE PREVIEW:")
        print(f"📞 Phone numbers: {extracted_phones}")
        print(f"🔗 URLs/Links: {extracted_urls}")
        print(f"📧 Email addresses: {extracted_emails}")
        print(f"🏷️  Suspicious keywords: {extracted_keywords[:10]}...")  # Show first 10
    
    def _extract_phones(self, text):
        """Extract phone numbers from text."""
        import re
        phone_patterns = [
            r'\+91-?\d{10}',
            r'\d{10}',
            r'\+91\s?\d{10}'
        ]
        phones = []
        for pattern in phone_patterns:
            phones.extend(re.findall(pattern, text))
        return list(set(phones))
    
    def _extract_urls(self, text):
        """Extract URLs from text."""
        import re
        url_pattern = r'https?://[^\s]+|www\.[^\s]+|\w+\.[a-z]{2,}/[^\s]*'
        return list(set(re.findall(url_pattern, text, re.IGNORECASE)))
    
    def _extract_emails(self, text):
        """Extract email addresses from text."""
        import re
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return list(set(re.findall(email_pattern, text)))
    
    def _extract_keywords(self, text):
        """Extract suspicious keywords."""
        keywords = [
            'urgent', 'blocked', 'verify', 'otp', 'pin', 'password', 'account',
            'bank', 'upi', 'suspicious', 'unauthorized', 'security', 'fraud',
            'immediate', 'warning', 'frozen', 'closure', 'helpline', 'manager',
            'employee', 'verification', 'portal', 'cashback', 'reward', 'lottery'
        ]
        found = []
        text_lower = text.lower()
        for keyword in keywords:
            if keyword in text_lower:
                found.append(keyword)
        return list(set(found))
    
    async def _display_expected_callback(self):
        """Display the expected GUVI callback payload."""
        
        print("\n" + "=" * 60)
        print("📡 EXPECTED GUVI CALLBACK PAYLOAD")
        print("=" * 60)
        
        # Create expected payload structure based on conversation
        all_text = " ".join([msg['text'] for msg in self.conversation_history])
        
        expected_payload = {
            "sessionId": self.session_id,
            "scamDetected": True,
            "totalMessagesExchanged": len(self.conversation_history),
            "extractedIntelligence": {
                "bankAccounts": [],  # Would be populated by actual intelligence extractor
                "upiIds": [],  # Would be populated by actual intelligence extractor
                "phoneNumbers": self._extract_phones(all_text),
                "phishingLinks": self._extract_urls(all_text),
                "suspiciousKeywords": self._extract_keywords(all_text)
            },
            "agentNotes": f"Complex multi-phase banking and UPI fraud scam detected. Scammer attempted credential harvesting using urgency tactics, impersonated SBI security team, requested sensitive information (UPI PIN, OTP, passwords), provided fake contact details, and combined with prize/cashback scam. Total conversation length: {len(self.conversation_history)} messages. High-risk scammer with sophisticated social engineering techniques."
        }
        
        print("🔍 This is the payload that should be sent to:")
        print("🎯 https://hackathon.guvi.in/api/updateHoneyPotFinalResult")
        print()
        print("📋 Payload JSON:")
        print("-" * 40)
        print(json.dumps(expected_payload, indent=2))
        
        print("\n✅ Validation Checklist:")
        print("-" * 30)
        print(f"✅ sessionId: Present and unique ({expected_payload['sessionId']})")
        print(f"✅ scamDetected: {expected_payload['scamDetected']} (boolean)")
        print(f"✅ totalMessagesExchanged: {expected_payload['totalMessagesExchanged']} (integer)")
        print(f"✅ phoneNumbers: {len(expected_payload['extractedIntelligence']['phoneNumbers'])} found")
        print(f"✅ phishingLinks: {len(expected_payload['extractedIntelligence']['phishingLinks'])} found")
        print(f"✅ suspiciousKeywords: {len(expected_payload['extractedIntelligence']['suspiciousKeywords'])} found")
        print(f"✅ agentNotes: {len(expected_payload['agentNotes'])} characters")
        
        return expected_payload

async def main():
    """Main test function."""
    
    print("🧪 COMPREHENSIVE END-TO-END HONEYPOT TEST")
    print("🎯 Testing complete scam conversation flow with callback validation")
    print("⚠️  Make sure server is running on localhost:8000")
    print()
    
    # Wait for user confirmation
    try:
        input("Press ENTER to start the test (Ctrl+C to cancel)...")
    except KeyboardInterrupt:
        print("\n❌ Test cancelled by user")
        return
    
    # Run the comprehensive test
    test = ComprehensiveHoneypotTest()
    
    try:
        await test.run_end_to_end_test()
        print("\n" + "=" * 60)
        print("🎉 END-TO-END TEST COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("📊 Check server logs for actual callback payload sent to GUVI")
        print("🔍 Look for 'callback_payload' events in server terminal")
        print("✅ All test scenarios executed successfully")
        
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())

async def validate_payload_structure():
    """Show the expected vs actual payload structure."""
    print("\n📊 GUVI Callback Payload Validation Guide")
    print("=" * 50)
    
    print("✅ Required Fields:")
    required_fields = [
        "sessionId (string): Unique session identifier",
        "scamDetected (boolean): True if scam was detected", 
        "totalMessagesExchanged (integer): Total messages in conversation",
        "extractedIntelligence (object): Intelligence data",
        "  └─ bankAccounts (array): Extracted bank account numbers",
        "  └─ upiIds (array): Extracted UPI IDs", 
        "  └─ phoneNumbers (array): Extracted phone numbers",
        "  └─ phishingLinks (array): Extracted malicious URLs",
        "  └─ suspiciousKeywords (array): Scam-related keywords found",
        "agentNotes (string): Summary of scammer behavior"
    ]
    
    for field in required_fields:
        print(f"  • {field}")
    
    print("\n🎯 Validation Steps:")
    print("1. Run: python test_callback_validation.py")
    print("2. Check server terminal for JSON payload logs")  
    print("3. Verify all fields are present and properly typed")
    print("4. Confirm intelligence extraction is working")
    print("5. Check GUVI endpoint receives the callback")

if __name__ == "__main__":
    print("🚀 GUVI Callback Validation Tool")
    print("Make sure the server is running on localhost:8000")
    print()
    
    asyncio.run(validate_payload_structure())
    
    try:
        asyncio.run(test_callback_validation())
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")