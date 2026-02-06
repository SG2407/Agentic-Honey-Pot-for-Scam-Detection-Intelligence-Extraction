"""Test LLM providers after installing openai package"""

import sys
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()

from app.llm_provider import LLMManager
from app.conversation_agent import ConversationAgent
from app.models import Metadata

print("="*80)
print("Testing LLM Providers After OpenAI Installation")
print("="*80)

# Test 1: Direct LLM Manager
print("\n[TEST 1] Direct LLM Manager Test")
print("-"*80)

llm = LLMManager()

test_prompt = """You are a worried customer chatting with a scammer.

Scammer said: Your account is blocked. Send OTP now.

Generate ONLY your natural reply (no labels):"""

print("Testing prompt...")
reply = llm.generate(test_prompt, temperature=0.7, max_tokens=100)
print(f"Response: {reply}\n")

if reply and 'safe' not in reply.lower() and 'unsafe' not in reply.lower():
    print("✅ Response looks natural and conversational")
else:
    print("⚠️ Response still contains 'safe'/'unsafe' keywords")

# Test 2: Conversation Agent
print("\n[TEST 2] Conversation Agent Test")
print("-"*80)

agent = ConversationAgent()

scammer_msg = "URGENT: Your SBI account has been compromised. Share your OTP immediately."
scam_type = "financial_threat"
metadata = Metadata()

print(f"Scammer: {scammer_msg}\n")

for i in range(3):
    reply = agent.generate_reply(scammer_msg, scam_type, [], metadata)
    print(f"Reply {i+1}: {reply}")
    
    # Check for issues
    if 'safe' in reply.lower() or 'unsafe' in reply.lower():
        print(f"  ⚠️ WARNING: Contains 'safe'/'unsafe'")
    else:
        print(f"  ✅ Natural response")
    print()

print("="*80)
print("Test Complete")
print("="*80)
