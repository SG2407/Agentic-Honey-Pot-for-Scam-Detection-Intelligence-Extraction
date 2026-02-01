#!/usr/bin/env python3
"""
Comprehensive test showing the difference between scam and legitimate message handling.
"""

import asyncio
import httpx
from datetime import datetime, timezone

BASE_URL = "http://localhost:8000"
API_KEY = "team_recursives"

async def test_message(message_type: str, text: str, session_id: str):
    """Test a single message."""
    
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "sessionId": session_id,
        "message": {
            "sender": "user",
            "text": text,
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        "conversationHistory": [],
        "metadata": {
            "channel": "SMS",
            "language": "English",
            "locale": "IN"
        }
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{BASE_URL}/honeypot",
                headers=headers,
                json=payload,
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                agent_reply = result.get('reply', '')
                scam_detection = result.get('scamDetection', {})
                
                is_scam = scam_detection.get('isScam', False)
                confidence = scam_detection.get('confidence', 0.0)
                
                return {
                    'type': message_type,
                    'text': text,
                    'is_scam': is_scam,
                    'confidence': confidence,
                    'reply': agent_reply,
                    'ai_engaged': len(agent_reply) > 50 and agent_reply != "Message received. Thank you."
                }
        except Exception as e:
            return {'error': str(e)}

async def main():
    """Run comprehensive comparison test."""
    
    print("🧪 COMPREHENSIVE BEHAVIOR TEST")
    print("=" * 80)
    print("Testing: AI Agent Activation for Scams vs No Activation for Legitimate Messages")
    print("=" * 80)
    
    test_cases = [
        # Legitimate messages
        ("LEGITIMATE", "Hey, are we meeting at 5pm today?"),
        ("LEGITIMATE", "Thanks for the update! See you tomorrow."),
        ("LEGITIMATE", "Can you send me those files we discussed?"),
        
        # Scam messages
        ("SCAM", "URGENT! Your bank account will be blocked today. Verify now!"),
        ("SCAM", "Share your UPI PIN to complete KYC verification."),
        ("SCAM", "Congratulations! You won Rs 50,000. Share bank details to claim."),
    ]
    
    print("\n📊 TESTING LEGITIMATE MESSAGES")
    print("-" * 80)
    
    legitimate_results = []
    for i, (msg_type, text) in enumerate([tc for tc in test_cases if tc[0] == "LEGITIMATE"], 1):
        session_id = f"test-legit-{int(datetime.now().timestamp())}-{i}"
        result = await test_message(msg_type, text, session_id)
        legitimate_results.append(result)
        
        print(f"\n{i}. Message: {text[:60]}...")
        print(f"   Detection: {'SCAM' if result['is_scam'] else 'LEGITIMATE'} (confidence: {result['confidence']:.2f})")
        print(f"   Response: {result['reply']}")
        print(f"   AI Agent: {'❌ NOT ACTIVATED (Logged only)' if not result['ai_engaged'] else '✅ ACTIVATED'}")
        
        await asyncio.sleep(1)
    
    print("\n" + "=" * 80)
    print("📊 TESTING SCAM MESSAGES")
    print("-" * 80)
    
    scam_results = []
    for i, (msg_type, text) in enumerate([tc for tc in test_cases if tc[0] == "SCAM"], 1):
        session_id = f"test-scam-{int(datetime.now().timestamp())}-{i}"
        result = await test_message(msg_type, text, session_id)
        scam_results.append(result)
        
        print(f"\n{i}. Message: {text[:60]}...")
        print(f"   Detection: {'SCAM' if result['is_scam'] else 'LEGITIMATE'} (confidence: {result['confidence']:.2f})")
        print(f"   Response: {result['reply'][:100]}...")
        print(f"   AI Agent: {'✅ ACTIVATED (Engaging conversation)' if result['ai_engaged'] else '❌ NOT ACTIVATED'}")
        
        await asyncio.sleep(1)
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    
    legit_correct = sum(1 for r in legitimate_results if not r['is_scam'] and not r['ai_engaged'])
    scam_correct = sum(1 for r in scam_results if r['is_scam'] and r['ai_engaged'])
    
    print(f"\n✅ Legitimate Messages:")
    print(f"   - Correctly detected as legitimate: {sum(1 for r in legitimate_results if not r['is_scam'])}/{len(legitimate_results)}")
    print(f"   - AI Agent NOT activated (logged only): {sum(1 for r in legitimate_results if not r['ai_engaged'])}/{len(legitimate_results)}")
    print(f"   - Behavior: Simple acknowledgment, no conversation")
    
    print(f"\n✅ Scam Messages:")
    print(f"   - Correctly detected as scam: {sum(1 for r in scam_results if r['is_scam'])}/{len(scam_results)}")
    print(f"   - AI Agent ACTIVATED: {sum(1 for r in scam_results if r['ai_engaged'])}/{len(scam_results)}")
    print(f"   - Behavior: Engaging conversation to extract intelligence")
    
    print(f"\n🎯 Overall System Behavior: {'✅ CORRECT' if legit_correct == len(legitimate_results) and scam_correct == len(scam_results) else '❌ NEEDS ADJUSTMENT'}")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
