"""Test callback payload format to ensure all 5 fields are always present"""

import asyncio
from datetime import datetime, timezone

from app.models import CallbackPayload, ExtractedIntelligence

def test_callback_payload():
    print("🧪 Testing Callback Payload Format\n")
    print("="*80)
    
    # Test 1: Empty intelligence (all fields should still be present)
    print("\n✅ TEST 1: Empty Intelligence (All 5 Fields Must Be Present)")
    print("-"*80)
    
    empty_intel = ExtractedIntelligence()
    payload1 = CallbackPayload(
        sessionId="test-001",
        scamDetected=True,
        totalMessagesExchanged=3,
        extractedIntelligence=empty_intel,
        agentNotes="Scam detected but no intelligence extracted yet"
    )
    
    payload_dict = payload1.model_dump()
    print(f"Payload: {payload_dict}")
    
    intel_keys = set(payload_dict["extractedIntelligence"].keys())
    expected_keys = {"bankAccounts", "upiIds", "phishingLinks", "phoneNumbers", "suspiciousKeywords"}
    
    print(f"\nExpected fields: {expected_keys}")
    print(f"Actual fields: {intel_keys}")
    
    assert intel_keys == expected_keys, f"Missing fields: {expected_keys - intel_keys}"
    
    # Verify all are empty arrays
    for key in expected_keys:
        value = payload_dict["extractedIntelligence"][key]
        assert isinstance(value, list), f"{key} should be a list"
        print(f"  {key}: {value}")
    
    print("✓ PASSED - All 5 fields present with empty arrays")
    
    # Test 2: Partial intelligence (all fields should still be present)
    print("\n✅ TEST 2: Partial Intelligence (All 5 Fields Must Be Present)")
    print("-"*80)
    
    partial_intel = ExtractedIntelligence(
        bankAccounts=["1234567890123"],
        phoneNumbers=["+919876543210"]
        # upiIds, phishingLinks, suspiciousKeywords are empty
    )
    
    payload2 = CallbackPayload(
        sessionId="test-002",
        scamDetected=True,
        totalMessagesExchanged=5,
        extractedIntelligence=partial_intel,
        agentNotes="Extracted bank account and phone number"
    )
    
    payload_dict2 = payload2.model_dump()
    print(f"Payload: {payload_dict2}")
    
    intel_keys2 = set(payload_dict2["extractedIntelligence"].keys())
    print(f"\nExpected fields: {expected_keys}")
    print(f"Actual fields: {intel_keys2}")
    
    assert intel_keys2 == expected_keys, f"Missing fields: {expected_keys - intel_keys2}"
    
    for key, value in payload_dict2["extractedIntelligence"].items():
        print(f"  {key}: {value}")
    
    print("✓ PASSED - All 5 fields present (some empty, some with data)")
    
    # Test 3: Full intelligence
    print("\n✅ TEST 3: Full Intelligence (All 5 Fields With Data)")
    print("-"*80)
    
    full_intel = ExtractedIntelligence(
        bankAccounts=["1234567890123", "9876543210123"],
        upiIds=["scammer@paytm", "fraud@phonepe"],
        phishingLinks=["https://fake-bank.com", "http://phishing-site.xyz"],
        phoneNumbers=["+919876543210", "+918765432109"],
        suspiciousKeywords=["OTP", "PIN", "urgent", "blocked"]
    )
    
    payload3 = CallbackPayload(
        sessionId="test-003",
        scamDetected=True,
        totalMessagesExchanged=8,
        extractedIntelligence=full_intel,
        agentNotes="Full intelligence extracted from scammer"
    )
    
    payload_dict3 = payload3.model_dump()
    
    intel_keys3 = set(payload_dict3["extractedIntelligence"].keys())
    assert intel_keys3 == expected_keys, f"Missing fields: {expected_keys - intel_keys3}"
    
    for key, value in payload_dict3["extractedIntelligence"].items():
        print(f"  {key}: {value}")
    
    print("✓ PASSED - All 5 fields present with data")
    
    print("\n" + "="*80)
    print("🎉 ALL CALLBACK PAYLOAD TESTS PASSED!")
    print("="*80)

if __name__ == "__main__":
    test_callback_payload()
