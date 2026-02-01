#!/usr/bin/env python3
"""Quick test to verify new Groq API key works."""

import os
from groq import Groq

# Replace with your NEW API key
NEW_API_KEY = input("Enter your NEW Groq API key: ").strip()

print("\n🔍 Testing new API key...\n")

try:
    client = Groq(api_key=NEW_API_KEY)
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": "Say 'API key works!' in exactly 3 words."}],
        max_tokens=10
    )
    
    print(f"✅ SUCCESS! API Response: {response.choices[0].message.content}")
    print(f"\n✅ Your new API key is working!")
    print(f"📝 Usage: {response.usage.total_tokens} tokens")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    print("\n⚠️ This API key is NOT working. Issues:")
    print("  - Invalid key format")
    print("  - Already exhausted quota")
    print("  - Network/permission issues")

