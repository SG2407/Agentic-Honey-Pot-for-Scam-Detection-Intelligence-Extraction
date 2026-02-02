"""Test handling of missing required fields that GUVI tester sometimes omits"""

from datetime import datetime, timezone
from app.models import HoneypotRequest, Message

print("="*70)
print("TESTING MISSING FIELD HANDLING")
print("="*70)

# Test 1: Missing timestamp (should auto-fill)
print("\n✅ TEST 1: Missing timestamp (auto-fill to now)")
try:
    msg = Message(sender="scammer", text="Test without timestamp")
    assert msg.timestamp is not None
    assert isinstance(msg.timestamp, datetime)
    assert msg.timestamp.tzinfo is not None
    print(f"   ✅ Auto-filled timestamp: {msg.timestamp}")
except Exception as e:
    print(f"   ❌ FAILED: {e}")

# Test 2: Null timestamp (should auto-fill)
print("\n✅ TEST 2: Null timestamp (auto-fill to now)")
try:
    msg = Message(sender="scammer", text="Test", timestamp=None)
    assert msg.timestamp is not None
    print(f"   ✅ Auto-filled null timestamp: {msg.timestamp}")
except Exception as e:
    print(f"   ❌ FAILED: {e}")

# Test 3: Missing conversationHistory (should default to [])
print("\n✅ TEST 3: Missing conversationHistory entirely")
try:
    req = HoneypotRequest.model_validate({
        "sessionId": "test-123",
        "message": {
            "sender": "scammer",
            "text": "Test"
            # No timestamp - should auto-fill
        }
        # No conversationHistory - should default to []
    })
    assert req.conversationHistory == []
    assert req.message.timestamp is not None
    print(f"   ✅ Default empty history: {req.conversationHistory}")
    print(f"   ✅ Auto-filled message timestamp: {req.message.timestamp}")
except Exception as e:
    print(f"   ❌ FAILED: {e}")

# Test 4: Missing sessionId (should default to "unknown-session")
print("\n✅ TEST 4: Missing sessionId (default to 'unknown-session')")
try:
    req = HoneypotRequest.model_validate({
        "message": {
            "sender": "scammer",
            "text": "Test"
        }
        # No sessionId - should default
    })
    assert req.sessionId == "unknown-session"
    print(f"   ✅ Default sessionId: {req.sessionId}")
except Exception as e:
    print(f"   ❌ FAILED: {e}")

# Test 5: Completely minimal request (only message.text and message.sender)
print("\n✅ TEST 5: Absolutely minimal request")
try:
    req = HoneypotRequest.model_validate({
        "message": {
            "sender": "scammer",
            "text": "Minimal test"
        }
    })
    assert req.sessionId == "unknown-session"
    assert req.conversationHistory == []
    assert req.message.timestamp is not None
    assert req.metadata is None
    print(f"   ✅ Parsed minimal request:")
    print(f"      sessionId: {req.sessionId}")
    print(f"      history: {len(req.conversationHistory)} messages")
    print(f"      timestamp: {req.message.timestamp}")
    print(f"      metadata: {req.metadata}")
except Exception as e:
    print(f"   ❌ FAILED: {e}")

# Test 6: Message with only text (no sender - should fail)
print("\n✅ TEST 6: Missing sender (should fail - truly required)")
try:
    msg = Message(text="Test")
    print(f"   ❌ UNEXPECTED: Should have failed for missing sender")
except Exception as e:
    print(f"   ✅ EXPECTED FAIL: {type(e).__name__}")

print("\n" + "="*70)
print("🎉 MISSING FIELD HANDLING TESTS COMPLETE!")
print("="*70)
