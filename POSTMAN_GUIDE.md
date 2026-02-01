# 🎯 Postman API Testing Guide

## Available Endpoints

### 1. Health Check (GET)
**URL:** `http://localhost:8000/health`  
**Method:** `GET`  
**Headers:** None required  
**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-02-01T...",
  "environment": "development"
}
```

---

### 2. Honeypot Endpoint (POST) ⚠️ **REQUIRES API KEY**
**URL:** `http://localhost:8000/honeypot`  
**Method:** `POST`  
**Headers:**
```
x-api-key: team_recursives
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "sessionId": "test-session-123",
  "message": {
    "text": "Your bank account will be blocked. Send OTP immediately!",
    "sender": "user",
    "timestamp": "2026-02-01T12:00:00Z"
  },
  "conversationHistory": []
}
```

**Response:**
```json
{
  "sessionId": "test-session-123",
  "reply": "Oh no! What OTP should I send? I'm worried about my account.",
  "scamDetection": {
    "isScam": true,
    "confidence": 0.92,
    "scamType": "banking_fraud",
    "reasoning": "Urgency + OTP request + account blocking threat"
  },
  "conversationActive": true
}
```

---

## 🚨 Common Errors & Solutions

### Error 1: `404 Not Found`
**Causes:**
- ❌ Wrong URL path
- ❌ Using `/api/honeypot` instead of `/honeypot`
- ❌ Extra slashes like `/honeypot/`

**Solution:** Use exact path: `http://localhost:8000/honeypot`

---

### Error 2: `401 Unauthorized`
**Cause:** Missing or wrong API key

**Solution:** Add header:
```
x-api-key: team_recursives
```

---

### Error 3: `422 Unprocessable Entity`
**Cause:** Wrong JSON body format

**Solution:** Ensure body matches this structure:
```json
{
  "sessionId": "string",
  "message": {
    "text": "string",
    "sender": "user",
    "timestamp": "2026-02-01T12:00:00Z"
  },
  "conversationHistory": []
}
```

---

### Error 4: `Connection Refused`
**Cause:** Server not running

**Solution:** Start server:
```bash
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 📝 Postman Collection Setup

### Step-by-Step:

1. **Open Postman**

2. **Test Health Check First:**
   - Create new request
   - Method: `GET`
   - URL: `http://localhost:8000/health`
   - Click "Send"
   - Should return: `{"status": "healthy", ...}`

3. **Test Honeypot:**
   - Create new request
   - Method: `POST`
   - URL: `http://localhost:8000/honeypot`
   - Go to "Headers" tab, add:
     - Key: `x-api-key`
     - Value: `team_recursives`
     - Key: `Content-Type`
     - Value: `application/json`
   - Go to "Body" tab
   - Select "raw" and "JSON"
   - Paste JSON body (see above)
   - Click "Send"

---

## 🎯 Quick Test Examples

### Legitimate Message Test:
```json
{
  "sessionId": "legit-test-1",
  "message": {
    "text": "Hey, meeting at 3pm tomorrow. Don't forget!",
    "sender": "user",
    "timestamp": "2026-02-01T12:00:00Z"
  },
  "conversationHistory": []
}
```

### Scam Message Test:
```json
{
  "sessionId": "scam-test-1",
  "message": {
    "text": "Congratulations! You won 10 lakh rupees. Send your bank details to claim prize.",
    "sender": "user",
    "timestamp": "2026-02-01T12:00:00Z"
  },
  "conversationHistory": []
}
```

---

## 🔍 Debugging Checklist

- [ ] Server running on port 8000?
- [ ] URL is `http://localhost:8000/honeypot` (not `/api/honeypot`)?
- [ ] Header `x-api-key: team_recursives` added?
- [ ] Body is valid JSON?
- [ ] Method is POST (not GET)?
- [ ] Content-Type header is `application/json`?

---

## 📊 Testing on Render (Production)

**URL:** `https://agentic-honey-pot-for-scam-detection-iiv4.onrender.com/honeypot`

Same headers and body as local testing.

**Note:** First request may take 30-50 seconds if service was idle (cold start).
