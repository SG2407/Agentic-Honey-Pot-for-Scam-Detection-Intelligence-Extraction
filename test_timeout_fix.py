#!/usr/bin/env python3
"""
Test script to verify the /honeypot endpoint responds quickly (<3 seconds)
"""
import requests
import time
import json

def test_honeypot_endpoint():
    """Test the honeypot endpoint"""
    url = "http://127.0.0.1:8000/honeypot"
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": "test-key-123"
    }
    
    payload = {
        "sessionId": "test-session-001",
        "message": {
            "text": "You have won a prize! Share your OTP to claim it.",
            "sender": "scammer",
            "timestamp": "2026-02-05T15:55:00Z"
        },
        "conversationHistory": []
    }
    
    print("🧪 Testing /honeypot endpoint...")
    print("=" * 80)
    
    # Measure response time
    start_time = time.time()
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=5)
        elapsed = time.time() - start_time
        
        print(f"✅ HTTP Status: {response.status_code}")
        print(f"⏱  Response Time: {elapsed:.3f} seconds")
        print(f"📦 Response Body: {json.dumps(response.json(), indent=2)}")
        
        # Check response time
        if elapsed < 3.0:
            print(f"\n✅ SUCCESS: Response time {elapsed:.3f}s < 3 seconds ✅")
        else:
            print(f"\n❌ FAILED: Response time {elapsed:.3f}s > 3 seconds ❌")
        
        # Check response format
        data = response.json()
        if data.get("status") == "success" and "reply" in data:
            print(f"✅ Response format is correct")
        else:
            print(f"❌ Response format is incorrect")
            
    except requests.exceptions.Timeout:
        elapsed = time.time() - start_time
        print(f"❌ Request timed out after {elapsed:.3f} seconds")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("=" * 80)

if __name__ == "__main__":
    test_honeypot_endpoint()
