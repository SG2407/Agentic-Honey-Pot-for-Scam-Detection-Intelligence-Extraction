#!/usr/bin/env python3
"""
Test legitimate message handling.
"""

import asyncio
import httpx
from datetime import datetime, timezone

BASE_URL = "http://localhost:8000"
API_KEY = "team_recursives"

async def test_legitimate_messages():
    """Test that legitimate messages are correctly identified."""
    
    print("🧪 Testing Legitimate Message Detection")
    print("=" * 60)
    
    legitimate_messages = [
        "Hey, are we still meeting tomorrow for the project discussion?",
        "I might be 10 minutes late, traffic looks bad near Wakad.",
        "No worries, let me know when you reach. I'll grab coffee meanwhile.",
        "Can you send me the presentation slides from yesterday's meeting?",
        "Thanks for the update! Looking forward to the event."
    ]
    
    session_id = f"legit-test-{int(datetime.now().timestamp())}"
    
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, message_text in enumerate(legitimate_messages, 1):
            print(f"\n📩 Message {i}/{len(legitimate_messages)}:")
            print(f"📱 Sender: {message_text}")
            print("-" * 40)
            
            payload = {
                "sessionId": session_id,
                "message": {
                    "sender": "user",
                    "text": message_text,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                },
                "conversationHistory": [],
                "metadata": {
                    "channel": "SMS",
                    "language": "English",
                    "locale": "IN"
                }
            }
            
            try:
                response = await client.post(
                    f"{BASE_URL}/honeypot",
                    headers=headers,
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    agent_reply = result.get('reply', 'No reply')
                    scam_detection = result.get('scamDetection', {})
                    
                    is_scam = scam_detection.get('isScam', False)
                    confidence = scam_detection.get('confidence', 0.0)
                    
                    status = "❌ WRONGLY DETECTED AS SCAM" if is_scam else "✅ CORRECTLY IDENTIFIED AS LEGITIMATE"
                    
                    print(f"🤖 Agent: {agent_reply[:100]}...")
                    print(f"🛡️  Scam Detection: {is_scam} (confidence: {confidence:.2f})")
                    print(f"{status}")
                else:
                    print(f"❌ Error: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Request failed: {str(e)}")
            
            await asyncio.sleep(2)
    
    print("\n" + "=" * 60)
    print("🎉 Legitimate Message Test Completed!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_legitimate_messages())
