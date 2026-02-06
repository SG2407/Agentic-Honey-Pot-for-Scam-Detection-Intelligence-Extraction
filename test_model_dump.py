"""Test model_dump with explicit parameters"""

import sys
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()

from app.models import CallbackPayload, ExtractedIntelligence
import json

print("="*80)
print("Testing model_dump with explicit parameters")
print("="*80)

# Create payload exactly as main.py does
intelligence = ExtractedIntelligence(
    bankAccounts=["1234567890123456"],
    upiIds=[],
    phishingLinks=[],
    phoneNumbers=[],
    suspiciousKeywords=["OTP", "urgent", "locked"]
)

payload = CallbackPayload(
    sessionId="test-session-123",
    scamDetected=True,
    totalMessagesExchanged=4,
    extractedIntelligence=intelligence,
    agentNotes="Scammer used requesting sensitive credentials (OTP/PIN/password), urgency tactics, attempting payment redirection"
)

print("\n[Test 1] Default model_dump():")
payload_dict1 = payload.model_dump()
print(f"Keys: {list(payload_dict1.keys())}")
print(f"SessionId present: {'sessionId' in payload_dict1}")
print(f"SessionId value: {payload_dict1.get('sessionId', 'NOT FOUND')}")

print("\n[Test 2] model_dump with explicit parameters:")
payload_dict2 = payload.model_dump(
    mode='json',
    exclude_none=False,
    by_alias=False
)
print(f"Keys: {list(payload_dict2.keys())}")
print(f"SessionId present: {'sessionId' in payload_dict2}")
print(f"SessionId value: {payload_dict2.get('sessionId', 'NOT FOUND')}")

print("\n[Test 3] Complete JSON (what gets sent to GUVI):")
json_output = json.dumps(payload_dict2, indent=2)
print(json_output)

print("\n" + "="*80)
if 'sessionId' in payload_dict2:
    print("✅ SessionId IS present in payload")
else:
    print("❌ SessionId IS MISSING - THIS IS A BUG!")
print("="*80)
