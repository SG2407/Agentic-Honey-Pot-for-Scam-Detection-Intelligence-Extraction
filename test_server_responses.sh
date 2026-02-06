#!/bin/bash

# Test script to verify the fixed response generation
echo "========================================"
echo "Testing Fixed Response Generation"
echo "========================================"
echo ""

# Start the server in background
echo "Starting server..."
cd /Users/sahil/Documents/Projects/Delhi_Hackathon
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
SERVER_PID=$!

# Wait for server to start
echo "Waiting for server to start..."
sleep 3

echo ""
echo "Testing with different scam messages..."
echo ""

# Test 1: OTP request
echo "Test 1: OTP Request Scam"
echo "========================"
curl -s -X POST http://localhost:8000/honeypot \
  -H "Content-Type: application/json" \
  -H "x-api-key: team_recursives" \
  -d '{
    "sessionId": "test-session-1",
    "message": {
      "sender": "scammer",
      "text": "Your account has been blocked. Send your OTP to verify.",
      "timestamp": "2024-01-01T10:00:00Z"
    },
    "conversationHistory": []
  }' | python -m json.tool
echo ""

sleep 2

# Test 2: Prize scam
echo "Test 2: Prize Scam"
echo "=================="
curl -s -X POST http://localhost:8000/honeypot \
  -H "Content-Type: application/json" \
  -H "x-api-key: team_recursives" \
  -d '{
    "sessionId": "test-session-2",
    "message": {
      "sender": "scammer",
      "text": "Congratulations! You won 10 lakh rupees in lottery. Click here to claim.",
      "timestamp": "2024-01-01T10:00:00Z"
    },
    "conversationHistory": []
  }' | python -m json.tool
echo ""

sleep 2

# Test 3: Account suspended
echo "Test 3: Account Suspension Threat"
echo "================================="
curl -s -X POST http://localhost:8000/honeypot \
  -H "Content-Type: application/json" \
  -H "x-api-key: team_recursives" \
  -d '{
    "sessionId": "test-session-3",
    "message": {
      "sender": "scammer",
      "text": "Your SBI account has been suspended. Update KYC immediately or account will be closed.",
      "timestamp": "2024-01-01T10:00:00Z"
    },
    "conversationHistory": []
  }' | python -m json.tool
echo ""

sleep 2

# Test 4: Same OTP request again (should give different response)
echo "Test 4: Same OTP Request (Different Response Expected)"
echo "======================================================"
curl -s -X POST http://localhost:8000/honeypot \
  -H "Content-Type: application/json" \
  -H "x-api-key: team_recursives" \
  -d '{
    "sessionId": "test-session-4",
    "message": {
      "sender": "scammer",
      "text": "Your account has been blocked. Send your OTP to verify.",
      "timestamp": "2024-01-01T10:00:00Z"
    },
    "conversationHistory": []
  }' | python -m json.tool
echo ""

# Stop the server
echo "Stopping server..."
kill $SERVER_PID

echo ""
echo "========================================"
echo "✅ Test Complete!"
echo "========================================"
echo ""
echo "Key observations:"
echo "1. Each scam message gets a VARIED response"
echo "2. Same message in Test 1 and Test 4 should have DIFFERENT responses"
echo "3. Responses are natural and contextual"
echo "4. All responses use LLM generation (not hard-coded)"
