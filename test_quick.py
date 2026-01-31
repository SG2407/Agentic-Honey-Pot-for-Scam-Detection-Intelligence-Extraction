#!/usr/bin/env python3
"""
Quick test script to verify the honeypot system works.
"""

import requests
import json
from datetime import datetime, timezone

# Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "team_recursives"

def test_health():
    """Test health endpoint."""
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_honeypot():
    """Test honeypot endpoint with a scam message."""
    try:
        headers = {
            "x-api-key": API_KEY,
            "Content-Type": "application/json"
        }
        
        payload = {
            "sessionId": "test-session-123",
            "message": {
                "sender": "scammer",
                "text": "Your bank account will be blocked today. Share your OTP immediately to verify.",
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            "conversationHistory": [],
            "metadata": {
                "channel": "SMS",
                "language": "English",
                "locale": "IN"
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/honeypot",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Honeypot test passed")
            print(f"   Agent Reply: {result['reply']}")
            return True
        else:
            print(f"❌ Honeypot test failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Honeypot test error: {e}")
        return False

def main():
    print("🔍 Testing AI-Powered Agentic Honeypot System")
    print("=" * 50)
    
    # Test health first
    if not test_health():
        print("❌ Server is not running. Please start the server first.")
        return
    
    print()
    
    # Test honeypot functionality
    test_honeypot()
    
    print("\n🎉 Testing completed!")

if __name__ == "__main__":
    main()