#!/usr/bin/env python3
"""Debug script to test the exact same request as Postman should send."""

import requests
import json

# Exact configuration that should work in Postman
url = "https://agentic-honey-pot-for-scam-detection-iiv4.onrender.com/honeypot"

headers = {
    "x-api-key": "team_recursives",
    "Content-Type": "application/json"
}

body = {
    "sessionId": "postman-debug-test",
    "message": {
        "text": "Urgent! Your account will be blocked. Send OTP now!",
        "sender": "user",
        "timestamp": "2026-02-01T12:00:00Z"
    },
    "conversationHistory": []
}

print("🔍 Testing endpoint configuration...")
print(f"\n📍 URL: {url}")
print(f"📋 Method: POST")
print(f"\n🔑 Headers:")
for key, value in headers.items():
    print(f"   {key}: {value}")
print(f"\n📦 Body:")
print(json.dumps(body, indent=2))

print("\n" + "="*60)
print("🚀 Sending request...\n")

try:
    response = requests.post(url, json=body, headers=headers, timeout=60)
    
    print(f"✅ Status Code: {response.status_code}")
    print(f"\n📨 Response Headers:")
    for key, value in response.headers.items():
        print(f"   {key}: {value}")
    
    print(f"\n📄 Response Body:")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)
    
    print("\n" + "="*60)
    
    if response.status_code == 200:
        print("✅ SUCCESS! The API is working correctly.")
        print("\n🎯 Your Postman should use EXACTLY these settings:")
        print(f"   • Method: POST")
        print(f"   • URL: {url}")
        print(f"   • Header: x-api-key = team_recursives")
        print(f"   • Header: Content-Type = application/json")
        print(f"   • Body: raw, JSON format")
    else:
        print(f"❌ ERROR: Status code {response.status_code}")
        print("\n🔍 Possible issues:")
        if response.status_code == 404:
            print("   • Wrong URL path")
        elif response.status_code == 401:
            print("   • Missing or wrong API key")
        elif response.status_code == 422:
            print("   • Wrong JSON body format")
        elif response.status_code == 405:
            print("   • Wrong HTTP method (should be POST)")
            
except requests.exceptions.Timeout:
    print("⏱️  TIMEOUT: Request took too long (cold start?)")
    print("   Wait 30-50 seconds and try again")
except requests.exceptions.ConnectionError:
    print("❌ CONNECTION ERROR: Cannot reach server")
    print("   • Check internet connection")
    print("   • Check if URL is correct")
except Exception as e:
    print(f"❌ ERROR: {e}")
