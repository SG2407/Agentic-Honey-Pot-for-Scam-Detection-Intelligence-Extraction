"""Test sessionId is included in callback payload"""

import sys
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()

from app.models import CallbackPayload, ExtractedIntelligence
import json

print("="*80)
print("Testing sessionId in Callback Payload")
print("="*80)

# Create test payload exactly as it's done in main.py
session_id = "test-session-abc123"
intelligence = ExtractedIntelligence(
    bankAccounts=["1234567890123456"],
    upiIds=[],
    phishingLinks=[],
    phoneNumbers=[],
    suspiciousKeywords=["urgent", "OTP", "locked"]
)

agent_notes = "Scammer used using urgency and account blocking threats, urgency tactics, attempting payment redirection"

payload = CallbackPayload(
    sessionId=session_id,
    scamDetected=True,
    totalMessagesExchanged=4,
    extractedIntelligence=intelligence,
    agentNotes=agent_notes
)

# Convert to dict (same as callback service does)
payload_dict = payload.model_dump()

print("\n✅ Payload as Python dict:")
print(f"Keys: {list(payload_dict.keys())}")
print()

print("✅ Payload as JSON (what gets sent to GUVI):")
payload_json = json.dumps(payload_dict, indent=2)
print(payload_json)
print()

# Check for sessionId
if 'sessionId' in payload_dict:
    print(f"✅ sessionId is present: {payload_dict['sessionId']}")
else:
    print("❌ ERROR: sessionId is MISSING!")

# Verify all required fields
required_fields = ["sessionId", "scamDetected", "totalMessagesExchanged", 
                   "extractedIntelligence", "agentNotes"]

print("\n📋 Field Validation:")
all_present = True
for field in required_fields:
    if field in payload_dict:
        print(f"  ✅ {field}")
    else:
        print(f"  ❌ {field} - MISSING!")
        all_present = False

if all_present:
    print("\n✅ ALL REQUIRED FIELDS PRESENT")
else:
    print("\n❌ SOME FIELDS ARE MISSING")

print("\n" + "="*80)
