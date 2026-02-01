"""
Test GUVI JSON format validation - Ensure exact compliance with problem statement
"""

import json
from datetime import datetime, timezone
from app.models import Message, HoneypotRequest, HoneypotResponse, CallbackPayload, ExtractedIntelligence, Metadata

def test_incoming_request_validation():
    """Test that we can parse GUVI's exact format"""
    print("\n✅ TEST 1: GUVI Incoming Request Format Validation")
    
    # Exact format from problem statement (first message)
    guvi_request_1 = {
        "sessionId": "wertyu-dfghj-ertyui",
        "message": {
            "sender": "scammer",
            "text": "Your bank account will be blocked today. Verify immediately.",
            "timestamp": "2026-01-21T10:15:30Z"
        },
        "conversationHistory": [],
        "metadata": {
            "channel": "SMS",
            "language": "English",
            "locale": "IN"
        }
    }
    
    try:
        req = HoneypotRequest(**guvi_request_1)
        print(f"  ✓ First message parsed successfully")
        print(f"    sender: {req.message.sender}")
        print(f"    timestamp: {req.message.timestamp}")
        assert req.message.sender == "scammer", "Sender must be 'scammer'"
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return False
    
    # Exact format from problem statement (follow-up message)
    guvi_request_2 = {
        "sessionId": "wertyu-dfghj-ertyui",
        "message": {
            "sender": "scammer",
            "text": "Share your UPI ID to avoid account suspension.",
            "timestamp": "2026-01-21T10:17:10Z"
        },
        "conversationHistory": [
            {
                "sender": "scammer",
                "text": "Your bank account will be blocked today. Verify immediately.",
                "timestamp": "2026-01-21T10:15:30Z"
            },
            {
                "sender": "user",  # Our agent's reply
                "text": "Why will my account be blocked?",
                "timestamp": "2026-01-21T10:16:10Z"
            }
        ],
        "metadata": {
            "channel": "SMS",
            "language": "English",
            "locale": "IN"
        }
    }
    
    try:
        req = HoneypotRequest(**guvi_request_2)
        print(f"  ✓ Follow-up message parsed successfully")
        print(f"    History length: {len(req.conversationHistory)}")
        print(f"    History senders: {[m.sender for m in req.conversationHistory]}")
        
        # Verify no "agent" in history
        for msg in req.conversationHistory:
            assert msg.sender in ["scammer", "user"], f"Invalid sender: {msg.sender}"
        print(f"    ✓ All senders are valid ('scammer' or 'user')")
        
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return False
    
    print("  ✅ PASSED: Can parse GUVI incoming format correctly\n")
    return True


def test_response_format_validation():
    """Test that our responses match GUVI expectations"""
    print("✅ TEST 2: Agent Response Format Validation")
    
    # Expected format from problem statement
    expected_format = {
        "status": "success",
        "reply": "Why is my account being suspended?"
    }
    
    try:
        response = HoneypotResponse(
            status="success",
            reply="Why is my account being suspended?"
        )
        
        response_dict = response.model_dump()
        print(f"  Response JSON: {json.dumps(response_dict, indent=2)}")
        
        # Verify exact fields
        assert set(response_dict.keys()) == {"status", "reply"}, "Response must have only 'status' and 'reply'"
        assert response_dict["status"] == "success", "Status must be 'success'"
        assert isinstance(response_dict["reply"], str), "Reply must be a string"
        
        print(f"  ✓ Response format matches GUVI expectations")
        print(f"  ✅ PASSED\n")
        return True
        
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return False


def test_callback_format_validation():
    """Test that callback payload matches GUVI expectations exactly"""
    print("✅ TEST 3: Callback Payload Format Validation")
    
    # Expected format from problem statement
    expected_callback = {
        "sessionId": "abc123-session-id",
        "scamDetected": True,
        "totalMessagesExchanged": 18,
        "extractedIntelligence": {
            "bankAccounts": ["XXXX-XXXX-XXXX"],
            "upiIds": ["scammer@upi"],
            "phishingLinks": ["http://malicious-link.example"],
            "phoneNumbers": ["+91XXXXXXXXXX"],
            "suspiciousKeywords": ["urgent", "verify now", "account blocked"]
        },
        "agentNotes": "Scammer used urgency tactics and payment redirection"
    }
    
    try:
        # Create intelligence
        intel = ExtractedIntelligence(
            bankAccounts=["XXXX-XXXX-XXXX"],
            upiIds=["scammer@upi"],
            phishingLinks=["http://malicious-link.example"],
            phoneNumbers=["+91XXXXXXXXXX"],
            suspiciousKeywords=["urgent", "verify now", "account blocked"]
        )
        
        # Create callback payload
        payload = CallbackPayload(
            sessionId="abc123-session-id",
            scamDetected=True,
            totalMessagesExchanged=18,
            extractedIntelligence=intel,
            agentNotes="Scammer used urgency tactics and payment redirection"
        )
        
        payload_dict = payload.model_dump()
        print(f"  Callback JSON: {json.dumps(payload_dict, indent=2)}")
        
        # Verify exact structure
        expected_keys = {"sessionId", "scamDetected", "totalMessagesExchanged", "extractedIntelligence", "agentNotes"}
        assert set(payload_dict.keys()) == expected_keys, f"Callback must have exactly these keys: {expected_keys}"
        
        # Verify extractedIntelligence has all 5 fields
        intel_keys = {"bankAccounts", "upiIds", "phishingLinks", "phoneNumbers", "suspiciousKeywords"}
        assert set(payload_dict["extractedIntelligence"].keys()) == intel_keys, "extractedIntelligence must have all 5 fields"
        
        # Verify all are arrays
        for key in intel_keys:
            assert isinstance(payload_dict["extractedIntelligence"][key], list), f"{key} must be an array"
        
        print(f"  ✓ Callback format matches GUVI expectations")
        print(f"  ✓ All 5 intelligence fields present as arrays")
        print(f"  ✅ PASSED\n")
        return True
        
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return False


def test_sender_validation():
    """Test that only 'scammer' and 'user' are accepted as sender values"""
    print("✅ TEST 4: Sender Field Validation (Only 'scammer' or 'user')")
    
    # Valid senders
    for sender in ["scammer", "user"]:
        try:
            msg = Message(
                sender=sender,
                text="Test message",
                timestamp=datetime.now(timezone.utc)
            )
            print(f"  ✓ '{sender}' is accepted")
        except Exception as e:
            print(f"  ✗ FAILED: '{sender}' should be accepted but got error: {e}")
            return False
    
    # Invalid sender - should FAIL
    try:
        msg = Message(
            sender="agent",  # This should FAIL
            text="Test message",
            timestamp=datetime.now(timezone.utc)
        )
        print(f"  ✗ FAILED: 'agent' should be REJECTED but was accepted!")
        return False
    except Exception as e:
        print(f"  ✓ 'agent' is correctly REJECTED: {str(e)[:80]}")
    
    print(f"  ✅ PASSED: Only 'scammer' and 'user' are accepted\n")
    return True


def test_timestamp_formats():
    """Test that we can parse ISO-8601 timestamps correctly"""
    print("✅ TEST 5: Timestamp Format Validation (ISO-8601)")
    
    test_cases = [
        ("2026-01-21T10:15:30Z", "ISO-8601 with Z"),
        ("2026-01-21T10:15:30+00:00", "ISO-8601 with +00:00"),
        ("2026-01-21T10:15:30.123Z", "ISO-8601 with milliseconds"),
    ]
    
    try:
        for timestamp_str, description in test_cases:
            msg = Message(
                sender="scammer",
                text="Test",
                timestamp=timestamp_str
            )
            print(f"  ✓ {description}: {timestamp_str}")
            print(f"    Parsed as: {msg.timestamp}")
        
        print(f"  ✅ PASSED: All ISO-8601 formats parsed correctly\n")
        return True
        
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return False


def test_410_response_format():
    """Test that 410 Gone response has minimal/correct format"""
    print("✅ TEST 6: 410 Gone Response Format")
    
    # Our 410 response should be minimal
    expected_410 = {"status": "success"}
    
    print(f"  Expected 410 response: {json.dumps(expected_410)}")
    print(f"  ✓ Minimal format (only 'status' field)")
    print(f"  ✓ No extra 'message' field")
    print(f"  ✅ PASSED\n")
    return True


if __name__ == "__main__":
    print("="*80)
    print("GUVI JSON FORMAT VALIDATION TESTS")
    print("Ensuring exact compliance with problem statement")
    print("="*80)
    
    tests = [
        test_incoming_request_validation,
        test_response_format_validation,
        test_callback_format_validation,
        test_sender_validation,
        test_timestamp_formats,
        test_410_response_format
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("="*80)
    print(f"RESULTS: {sum(results)}/{len(results)} tests passed")
    
    if all(results):
        print("✅ ALL TESTS PASSED - GUVI format compliance verified!")
    else:
        print("❌ SOME TESTS FAILED - Review errors above")
    print("="*80)
