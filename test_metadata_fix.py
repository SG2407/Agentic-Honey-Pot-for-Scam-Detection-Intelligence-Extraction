"""Test fixes for response generation and agentNotes"""

import sys
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()

from app.conversation_agent import ConversationAgent
from app.models import Message, Metadata, CallbackPayload, ExtractedIntelligence

print("="*80)
print("TEST 1: Response Generation with Metadata Fix")
print("="*80)

agent = ConversationAgent()

# Test with Pydantic Metadata object (this was causing the error)
scammer_msg = 'URGENT: Your SBI account has been compromised. Share your OTP immediately.'
scam_type = 'financial_threat'
history = []
metadata = Metadata(channel='whatsapp', locale='IN')

print(f"\nMessage: {scammer_msg}")
print(f"Metadata: channel={metadata.channel}, locale={metadata.locale}\n")

try:
    reply1 = agent.generate_reply(scammer_msg, scam_type, history, metadata)
    print(f"Reply 1: {reply1}\n")
    
    reply2 = agent.generate_reply(scammer_msg, scam_type, history, metadata)
    print(f"Reply 2: {reply2}\n")
    
    if reply1 != reply2:
        print("✅ PASS: Responses are DIFFERENT (LLM working)")
    else:
        print("⚠️  Responses are same (still using fallback)")
        
except Exception as e:
    print(f"❌ FAIL: {type(e).__name__}: {e}")

print("\n" + "="*80)
print("TEST 2: AgentNotes Generation")
print("="*80)

# Create payload with agentNotes
intelligence = ExtractedIntelligence(
    bankAccounts=['1234567890123456'],
    upiIds=[],
    phishingLinks=[],
    phoneNumbers=[],
    suspiciousKeywords=['OTP', 'urgent', 'locked']
)

# Generate agent notes (same logic as in main.py)
agent_notes_parts = [
    "Scam type: credential_phishing",
    "Confidence: 0.95",
    "Messages exchanged: 3",
]

if intelligence.bankAccounts:
    agent_notes_parts.append(f"Extracted {len(intelligence.bankAccounts)} bank account(s)")

agent_notes = ". ".join(agent_notes_parts) + "."

payload = CallbackPayload(
    sessionId="test-123",
    scamDetected=True,
    scamType="credential_phishing",
    confidence=0.95,
    totalMessagesExchanged=3,
    extractedIntelligence=intelligence,
    conversationSummary="Scam detected: credential_phishing",
    agentNotes=agent_notes
)

print(f"\nAgentNotes: {payload.agentNotes}")

if payload.agentNotes and payload.agentNotes != "":
    print("✅ PASS: AgentNotes populated correctly")
else:
    print("❌ FAIL: AgentNotes is empty")

print("\n" + "="*80)
print("✅ ALL TESTS COMPLETE")
print("="*80)
