#!/usr/bin/env python3
"""
Demo script to test the AI-Powered Agentic Honeypot system.
This script simulates scam conversations to demonstrate the system's capabilities.
"""

import asyncio
import httpx
import json
from datetime import datetime, timezone
from typing import List, Dict

# Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "team_recursives"

class HoneypotDemo:
    def __init__(self, base_url: str = BASE_URL, api_key: str = API_KEY):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }
    
    async def test_health_check(self):
        """Test the health check endpoint."""
        print("\n🔍 Testing health check...")
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/health")
            if response.status_code == 200:
                print("✅ Health check passed")
                print(f"   Response: {response.json()}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
    
    async def simulate_scam_conversation(self, scenario: Dict):
        """Simulate a complete scam conversation."""
        print(f"\n🎭 Simulating scenario: {scenario['name']}")
        print(f"   Description: {scenario['description']}")
        
        session_id = f"demo-{scenario['name'].lower().replace(' ', '-')}-{int(datetime.now().timestamp())}"
        conversation_history = []
        
        async with httpx.AsyncClient() as client:
            for i, message_text in enumerate(scenario['messages']):
                print(f"\n📩 Message {i+1}: {message_text}")
                
                payload = {
                    "sessionId": session_id,
                    "message": {
                        "sender": "scammer",
                        "text": message_text,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    },
                    "conversationHistory": conversation_history,
                    "metadata": {
                        "channel": "SMS",
                        "language": "English",
                        "locale": "IN"
                    }
                }
                
                try:
                    response = await client.post(
                        f"{self.base_url}/honeypot",
                        headers=self.headers,
                        json=payload,
                        timeout=30.0
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        print(f"🤖 Agent Reply: {result['reply']}")
                        
                        # Add messages to conversation history
                        conversation_history.append({
                            "sender": "scammer",
                            "text": message_text,
                            "timestamp": payload["message"]["timestamp"]
                        })
                        conversation_history.append({
                            "sender": "user",
                            "text": result['reply'],
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        })
                    else:
                        print(f"❌ Error: {response.status_code} - {response.text}")
                        break
                        
                except Exception as e:
                    print(f"❌ Request failed: {str(e)}")
                    break
                
                # Wait between messages to simulate realistic timing
                await asyncio.sleep(2)
        
        print(f"\n✅ Scenario '{scenario['name']}' completed with {len(conversation_history)} messages")
    
    async def run_demo(self):
        """Run the complete demonstration."""
        print("🚀 Starting AI-Powered Agentic Honeypot Demo")
        print("=" * 50)
        
        # Test health check first
        if not await self.test_health_check():
            print("❌ Server is not running. Please start the server first with: ./start_server.sh")
            return
        
        # Define demo scenarios
        scenarios = [
            {
                "name": "Bank Account Threat",
                "description": "Scammer threatens to block bank account",
                "messages": [
                    "Your bank account will be blocked today due to suspicious activity. Verify immediately.",
                    "Sir, you need to share your UPI PIN to verify your identity or account will be closed.",
                    "This is urgent! Share your OTP that we sent to complete verification process.",
                    "Call our customer care at 9876543210 for immediate assistance."
                ]
            },
            {
                "name": "Prize Lottery Scam",
                "description": "Fake lottery winning notification",
                "messages": [
                    "Congratulations! You have won Rs 50,000 in our lucky draw lottery.",
                    "To claim your prize, please share your bank account details and UPI ID.",
                    "Visit https://fake-lottery-claim.com/winner to complete the process.",
                    "Hurry! Offer expires today. Contact winner@lottery.com for details."
                ]
            },
            {
                "name": "UPI Payment Fraud",
                "description": "Fake payment failure notification",
                "messages": [
                    "Your UPI payment of Rs 2500 has failed. Please verify to get refund.",
                    "Share your UPI ID and last 4 digits of your card for refund process.",
                    "Customer care number: +91-9999888777. Call immediately for refund.",
                    "If not resolved today, money will be forfeited as per RBI guidelines."
                ]
            }
        ]
        
        # Run all scenarios
        for scenario in scenarios:
            await self.simulate_scam_conversation(scenario)
            await asyncio.sleep(3)  # Pause between scenarios
        
        print("\n🎉 Demo completed successfully!")
        print("\n📊 Check the server logs to see:")
        print("   - Scam detection results")
        print("   - Intelligence extraction")
        print("   - Conversation flow")
        print("   - Callback attempts")

async def main():
    """Main demo function."""
    demo = HoneypotDemo()
    await demo.run_demo()

if __name__ == "__main__":
    asyncio.run(main())