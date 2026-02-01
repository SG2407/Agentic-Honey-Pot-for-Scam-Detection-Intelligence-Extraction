#!/usr/bin/env python3
"""
Test deployed API endpoint.
Replace YOUR_DEPLOYED_URL with your actual deployment URL.
"""

import asyncio
import httpx
from datetime import datetime, timezone

# UPDATE THIS WITH YOUR DEPLOYED URL
DEPLOYED_URL = "https://your-app-name.onrender.com"  # or .railway.app, etc.
API_KEY = "team_recursives"

async def test_deployed_api():
    """Test the deployed API."""
    
    print("🧪 Testing Deployed Honeypot API")
    print("=" * 70)
    print(f"🌐 URL: {DEPLOYED_URL}")
    print("=" * 70)
    
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    # Test 1: Health Check
    print("\n1️⃣ Testing Health Endpoint...")
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(f"{DEPLOYED_URL}/health")
            if response.status_code == 200:
                print(f"   ✅ Health check passed")
                print(f"   Response: {response.json()}")
            else:
                print(f"   ❌ Health check failed: {response.status_code}")
                return
    except Exception as e:
        print(f"   ❌ Connection failed: {str(e)}")
        print(f"   💡 Make sure your app is deployed and URL is correct")
        return
    
    # Test 2: Scam Message
    print("\n2️⃣ Testing Scam Detection...")
    scam_payload = {
        "sessionId": f"deploy-test-{int(datetime.now().timestamp())}",
        "message": {
            "sender": "scammer",
            "text": "URGENT! Your bank account will be blocked. Share your UPI PIN now!",
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        "conversationHistory": [],
        "metadata": {
            "channel": "SMS",
            "language": "English",
            "locale": "IN"
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{DEPLOYED_URL}/honeypot",
                headers=headers,
                json=scam_payload
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Scam message processed")
                print(f"   Response: {result['reply'][:100]}...")
                
                scam_detection = result.get('scamDetection', {})
                if scam_detection.get('isScam'):
                    print(f"   ✅ Correctly detected as SCAM (confidence: {scam_detection.get('confidence', 0):.2f})")
                else:
                    print(f"   ⚠️  Not detected as scam")
            else:
                print(f"   ❌ Request failed: {response.status_code}")
                print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Request failed: {str(e)}")
        return
    
    # Test 3: Legitimate Message
    print("\n3️⃣ Testing Legitimate Message...")
    legit_payload = {
        "sessionId": f"deploy-test-legit-{int(datetime.now().timestamp())}",
        "message": {
            "sender": "user",
            "text": "Hey, are we still meeting at 5pm today?",
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        "conversationHistory": [],
        "metadata": {
            "channel": "SMS",
            "language": "English",
            "locale": "IN"
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{DEPLOYED_URL}/honeypot",
                headers=headers,
                json=legit_payload
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Legitimate message processed")
                print(f"   Response: {result['reply']}")
                
                scam_detection = result.get('scamDetection', {})
                if not scam_detection.get('isScam'):
                    print(f"   ✅ Correctly identified as LEGITIMATE")
                else:
                    print(f"   ⚠️  Incorrectly detected as scam")
            else:
                print(f"   ❌ Request failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Request failed: {str(e)}")
    
    print("\n" + "=" * 70)
    print("🎉 Deployment Test Completed!")
    print("=" * 70)
    print("\n📋 Share these details with hackathon officials:")
    print(f"   🌐 Base URL: {DEPLOYED_URL}")
    print(f"   🔑 API Key: {API_KEY}")
    print(f"   📍 Endpoint: POST /honeypot")
    print(f"   ❤️  Health Check: GET /health")

if __name__ == "__main__":
    print("\n⚠️  UPDATE THE DEPLOYED_URL VARIABLE FIRST!")
    print("   Edit this file and replace 'your-app-name' with your actual app name\n")
    
    if "your-app-name" in DEPLOYED_URL:
        print("❌ Please update DEPLOYED_URL with your actual deployment URL")
        print("   Example: https://honeypot-api.onrender.com")
    else:
        asyncio.run(test_deployed_api())
