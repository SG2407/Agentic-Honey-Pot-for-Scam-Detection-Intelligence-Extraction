#!/usr/bin/env python3
"""
Quick test for scam detection and AI agent activation.
"""

import asyncio
import httpx
from datetime import datetime, timezone

BASE_URL = "http://localhost:8000"
API_KEY = "team_recursives"

async def test_scam_agent_activation():
    """Test that scam messages activate the AI agent."""
    
    print("🧪 Testing Scam Detection & AI Agent Activation")
    print("=" * 60)
    
    scam_messages = [
        "URGENT! Your bank account will be blocked. Verify at http://fake-bank.com",
        "Share your UPI PIN to verify your identity.",
        "You have won Rs 50,000! Share your bank details to claim prize."
    ]
    
    session_id = f"scam-test-{int(datetime.now().timestamp())}"
    
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    conversation_history = []
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, message_text in enumerate(scam_messages, 1):
            print(f"\n📩 Message {i}/{len(scam_messages)}:")
            print(f"📱 Scammer: {message_text}")
            print("-" * 40)
            
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
                    scam_type = scam_detection.get('scamType', 'unknown')
                    
                    # Check if agent is engaging (not just acknowledgment)
                    is_engaged = len(agent_reply) > 50 and agent_reply != "Message received. Thank you."
                    
                    status = "✅ AI AGENT ACTIVATED" if is_engaged else "❌ AI AGENT NOT ACTIVATED"
                    
                    print(f"🤖 Agent: {agent_reply[:120]}...")
                    print(f"🛡️  Scam Detection: {is_scam} (confidence: {confidence:.2f}, type: {scam_type})")
                    print(f"{status}")
                    
                    # Update conversation history
                    conversation_history.append({
                        "sender": "scammer",
                        "text": message_text,
                        "timestamp": payload["message"]["timestamp"]
                    })
                    conversation_history.append({
                        "sender": "user",
                        "text": agent_reply,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                else:
                    print(f"❌ Error: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Request failed: {str(e)}")
            
            await asyncio.sleep(2)
    
    print("\n" + "=" * 60)
    print("🎉 Scam Detection Test Completed!")
    print(f"📊 Total conversation messages: {len(conversation_history)}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_scam_agent_activation())
