#!/usr/bin/env python3
"""
Direct callback payload inspector - shows exactly what would be sent to GUVI.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import CallbackPayload, ExtractedIntelligence, ConversationState, Message
from datetime import datetime, timezone
import json

def create_sample_callback_payload():
    """Create a sample callback payload to show structure."""
    
    # Create sample messages
    messages = [
        Message(
            sender="scammer",
            text="Your bank account will be blocked today. Verify with your UPI PIN.",
            timestamp=datetime.now(timezone.utc)
        ),
        Message(
            sender="user", 
            text="Oh no! What should I do? I'm so worried about my account.",
            timestamp=datetime.now(timezone.utc)
        ),
        Message(
            sender="scammer",
            text="Call our customer care at +91-9876543210 immediately with your details.",
            timestamp=datetime.now(timezone.utc)
        ),
        Message(
            sender="user",
            text="Okay, should I share my OTP with you to fix this?",
            timestamp=datetime.now(timezone.utc)
        )
    ]
    
    # Create sample intelligence
    intelligence = ExtractedIntelligence(
        bankAccounts=[],
        upiIds=[],
        phoneNumbers=["+91-9876543210", "9876543210"],
        phishingLinks=[],
        suspiciousKeywords=["blocked", "verify", "urgent", "account", "customer care", "otp"]
    )
    
    # Create conversation state
    conversation_state = ConversationState(
        sessionId="sample-validation-session",
        messages=messages,
        scam_detected=True,
        agent_activated=True,
        intelligence=intelligence,
        agent_notes="Scammer attempted to harvest banking credentials through urgency tactics. Used phone number for contact and requested OTP/UPI PIN. Typical banking impersonation scam pattern detected."
    )
    
    # Create callback payload
    payload = CallbackPayload(
        sessionId=conversation_state.sessionId,
        scamDetected=conversation_state.scam_detected,
        totalMessagesExchanged=conversation_state.total_messages,
        extractedIntelligence=intelligence,
        agentNotes=conversation_state.agent_notes
    )
    
    return payload

def validate_payload(payload: CallbackPayload):
    """Validate the callback payload against GUVI requirements."""
    
    print("🔍 GUVI Callback Payload Validation")
    print("=" * 50)
    
    payload_dict = payload.dict()
    
    # Show the complete payload
    print("📋 Complete Callback Payload:")
    print("-" * 30)
    print(json.dumps(payload_dict, indent=2, default=str))
    
    print("\n✅ Validation Checklist:")
    print("-" * 30)
    
    # Required field validation
    required_fields = [
        ("sessionId", str, "Session identifier"),
        ("scamDetected", bool, "Scam detection result"),
        ("totalMessagesExchanged", int, "Message count"),
        ("extractedIntelligence", dict, "Intelligence data"),
        ("agentNotes", str, "Agent observations")
    ]
    
    all_valid = True
    
    for field_name, field_type, description in required_fields:
        if field_name in payload_dict:
            value = payload_dict[field_name]
            if isinstance(value, field_type):
                print(f"✅ {field_name}: {type(value).__name__} - {description}")
            else:
                print(f"❌ {field_name}: Wrong type (expected {field_type.__name__}, got {type(value).__name__})")
                all_valid = False
        else:
            print(f"❌ {field_name}: Missing required field")
            all_valid = False
    
    # Validate intelligence subfields
    print("\n🔍 Intelligence Subfield Validation:")
    print("-" * 30)
    
    intelligence = payload_dict.get('extractedIntelligence', {})
    intelligence_fields = [
        ("bankAccounts", list, "Bank account numbers"),
        ("upiIds", list, "UPI identifiers"), 
        ("phoneNumbers", list, "Phone numbers"),
        ("phishingLinks", list, "Malicious URLs"),
        ("suspiciousKeywords", list, "Scam keywords")
    ]
    
    for field_name, field_type, description in intelligence_fields:
        if field_name in intelligence:
            value = intelligence[field_name]
            if isinstance(value, field_type):
                count = len(value) if hasattr(value, '__len__') else 0
                print(f"✅ {field_name}: {type(value).__name__} with {count} items - {description}")
            else:
                print(f"❌ {field_name}: Wrong type (expected {field_type.__name__}, got {type(value).__name__})")
                all_valid = False
        else:
            print(f"❌ {field_name}: Missing intelligence field")
            all_valid = False
    
    print("\n🎯 Overall Validation:", "✅ PASSED" if all_valid else "❌ FAILED")
    
    if all_valid:
        print("\n🏆 Payload is ready for GUVI evaluation!")
        print("💡 This payload will be sent to: https://hackathon.guvi.in/api/updateHoneyPotFinalResult")
    else:
        print("\n⚠️ Payload needs fixes before submission")
    
    return all_valid

def show_monitoring_guide():
    """Show how to monitor callbacks in real-time."""
    
    print("\n📊 Real-time Callback Monitoring Guide")
    print("=" * 50)
    
    print("🔧 Method 1: Server Logs")
    print("1. Start server: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
    print("2. Run test: python test_callback_validation.py")  
    print("3. Watch for 'callback_payload' in server output")
    
    print("\n🔧 Method 2: Log File Analysis")
    print("1. Check application logs for callback events")
    print("2. Filter by event_type: 'callback_payload'")
    print("3. Inspect the JSON payload field")
    
    print("\n🔧 Method 3: Direct Testing")
    print("1. Run: python inspect_callback_payload.py")
    print("2. Review the generated payload structure")
    print("3. Verify all required fields are present")
    
    print("\n🎯 Key Things to Verify:")
    print("• sessionId is unique and meaningful")
    print("• scamDetected is True when scams are detected")
    print("• totalMessagesExchanged matches conversation length")
    print("• extractedIntelligence contains relevant data")
    print("• agentNotes provide meaningful insights")

if __name__ == "__main__":
    print("🛠️ GUVI Callback Payload Inspector")
    print()
    
    # Create and validate sample payload
    sample_payload = create_sample_callback_payload()
    is_valid = validate_payload(sample_payload)
    
    # Show monitoring guide
    show_monitoring_guide()
    
    print("\n" + "=" * 50)
    print("✨ Use this tool to validate your callback implementation!")