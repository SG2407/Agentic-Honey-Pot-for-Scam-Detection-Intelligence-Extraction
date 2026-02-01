#!/usr/bin/env python3
"""Test with EXACT format from GUVI problem statement."""

import requests
import json

# Test with EXACT format from problem statement
url = "https://agentic-honey-pot-for-scam-detection-iiv4.onrender.com/honeypot"

headers = {
    "x-api-key": "team_recursives",
    "Content-Type": "application/json"
}

# EXACT format from problem statement (First Message)
body_first_message = {
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

print("🧪 Testing with EXACT format from GUVI problem statement...")
print(f"\n📍 URL: {url}")
print(f"\n📦 Request Body:")
print(json.dumps(body_first_message, indent=2))
print("\n" + "="*60)

try:
    response = requests.post(url, json=body_first_message, headers=headers, timeout=60)
    
    print(f"\n✅ Status Code: {response.status_code}")
    print(f"\n📄 Response:")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)
    
    if response.status_code == 200:
        print("\n✅ SUCCESS! API accepts GUVI format correctly")
    else:
        print(f"\n❌ ERROR: Status {response.status_code}")
        
except Exception as e:
    print(f"\n❌ ERROR: {e}")
