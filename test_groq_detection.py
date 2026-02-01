#!/usr/bin/env python3
"""
Test Groq LLM-based scam detection.
"""

import asyncio
from datetime import datetime, timezone
from app.models import Message
from app.agents.scam_detector import ScamDetector

async def test_groq_detection():
    print("🧪 Testing Groq LLM Scam Detection")
    print("=" * 60)
    
    detector = ScamDetector()
    
    # Test messages
    test_messages = [
        ("Your bank account will be blocked today due to suspicious activity. Verify immediately.", "SCAM"),
        ("Sir, you need to share your UPI PIN to verify your identity or account will be closed.", "SCAM"),
        ("This is urgent! Share your OTP that we sent to complete verification process.", "SCAM"),
        ("Congratulations! You have won Rs 50,000 in our lucky draw lottery.", "SCAM"),
        ("Hey, are you free for lunch tomorrow? Let me know!", "LEGITIMATE"),
        ("Your Amazon order has been shipped. Track your package: amazon.com/track", "LEGITIMATE"),
        ("Meeting scheduled for 3 PM today. Conference room B.", "LEGITIMATE"),
    ]
    
    correct = 0
    total = len(test_messages)
    
    for i, (text, expected) in enumerate(test_messages, 1):
        message = Message(
            sender="scammer",
            text=text,
            timestamp=datetime.now(timezone.utc)
        )
        
        result = await detector.analyze_message(message, session_id=f"test-{i}")
        
        predicted = "SCAM" if result.is_scam else "LEGITIMATE"
        is_correct = predicted == expected
        
        if is_correct:
            correct += 1
            status = "✅"
        else:
            status = "❌"
        
        print(f"\n{status} Test {i}:")
        print(f"   Message: {text[:70]}...")
        print(f"   Expected: {expected}")
        print(f"   Predicted: {predicted}")
        print(f"   Confidence: {result.confidence:.3f}")
        print(f"   Type: {result.scam_type or 'N/A'}")
        print(f"   Reasoning: {result.reasoning[:80]}...")
    
    print(f"\n" + "=" * 60)
    print(f"📊 Results: {correct}/{total} correct ({(correct/total)*100:.1f}% accuracy)")
    
    if correct >= total * 0.85:
        print("🎉 Excellent! Groq LLM working perfectly!")
    elif correct >= total * 0.7:
        print("✅ Good! Acceptable accuracy.")
    else:
        print("⚠️ Needs improvement.")

if __name__ == "__main__":
    asyncio.run(test_groq_detection())
