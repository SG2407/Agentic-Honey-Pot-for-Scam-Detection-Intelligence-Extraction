"""Quick local test for the clean implementation"""

import asyncio
import os
from datetime import datetime, timezone

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from app.models import HoneypotRequest, Message, Metadata
from app.scam_detector import ScamDetector
from app.intelligence_extractor import IntelligenceExtractor
from app.conversation_agent import ConversationAgent

async def test_clean_implementation():
    print("🧪 Testing Clean Implementation\n")
    print("="*80)
    
    # Check environment
    if not os.getenv("GROQ_API_KEY"):
        print("❌ GROQ_API_KEY not set in environment")
        return
    
    # Initialize components
    detector = ScamDetector()
    extractor = IntelligenceExtractor()
    agent = ConversationAgent()
    
    # Test 1: Hard scam pattern detection
    print("\n✅ TEST 1: Hard Scam Pattern (OTP request)")
    print("-"*80)
    
    test_message = "Your account will be blocked. Please send your OTP immediately to verify."
    result = detector.analyze_message(test_message, [])
    
    print(f"Message: {test_message}")
    print(f"Is Scam: {result.is_scam}")
    print(f"Confidence: {result.confidence}")
    print(f"Type: {result.scam_type}")
    print(f"Reasoning: {result.reasoning}")
    
    assert result.is_scam == True, "Should detect OTP request as scam"
    assert result.confidence == 1.0, "Should have confidence 1.0 (hard rule)"
    print("✓ PASSED")
    
    # Test 2: Intelligence extraction
    print("\n✅ TEST 2: Intelligence Extraction")
    print("-"*80)
    
    msg_with_intel = Message(
        sender="scammer",
        text="Send money to 1234567890123 or use UPI scammer@paytm. Call +919876543210",
        timestamp=datetime.now(timezone.utc)
    )
    
    intel = extractor.extract_from_conversation(msg_with_intel, [])
    
    print(f"Bank Accounts: {intel.bankAccounts}")
    print(f"UPI IDs: {intel.upiIds}")
    print(f"Phone Numbers: {intel.phoneNumbers}")
    
    assert len(intel.bankAccounts) > 0, "Should extract bank account"
    assert len(intel.upiIds) > 0, "Should extract UPI ID"
    assert len(intel.phoneNumbers) > 0, "Should extract phone number"
    print("✓ PASSED")
    
    # Test 3: Has real intelligence check
    print("\n✅ TEST 3: Real Intelligence Check")
    print("-"*80)
    
    has_real = extractor.has_real_intelligence(intel)
    print(f"Has Real Intelligence: {has_real}")
    assert has_real == True, "Should recognize real intelligence"
    print("✓ PASSED")
    
    # Test 4: Neutral reply for non-scam
    print("\n✅ TEST 4: Neutral Reply Generation")
    print("-"*80)
    
    neutral = agent.generate_neutral_reply()
    print(f"Neutral Reply: {neutral}")
    assert len(neutral) > 0, "Should generate neutral reply"
    print("✓ PASSED")
    
    # Test 5: Timestamp parsing (Unix milliseconds)
    print("\n✅ TEST 5: Unix Milliseconds Timestamp Parsing")
    print("-"*80)
    
    unix_ms = 1769938742773
    msg = Message(
        sender="scammer",
        text="Test",
        timestamp=unix_ms
    )
    print(f"Unix MS: {unix_ms}")
    print(f"Parsed: {msg.timestamp}")
    print(f"Timezone Aware: {msg.timestamp.tzinfo is not None}")
    assert msg.timestamp.tzinfo is not None, "Should be timezone-aware"
    print("✓ PASSED")
    
    print("\n" + "="*80)
    print("🎉 ALL TESTS PASSED!")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(test_clean_implementation())
