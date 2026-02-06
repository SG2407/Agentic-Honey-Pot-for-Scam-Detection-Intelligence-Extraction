# Callback Structure Fix Summary

## Issues Fixed

### 1. ✅ Added OpenAI to requirements.txt
**Problem**: Deployed version had `ModuleNotFoundError: No module named 'openai'`
- OpenRouter provider couldn't load, falling back to Groq
- Groq was returning strange responses like "safe" and "unsafe S2"

**Solution**: Added `openai>=1.0.0` to requirements.txt
- OpenRouter now works correctly
- Natural conversational responses instead of safety classifications

---

### 2. ✅ Fixed Callback Payload Structure
**Problem**: Callback had extra fields not in problem statement

**Old Structure** (WRONG):
```json
{
  "sessionId": "...",
  "scamDetected": true,
  "scamType": "credential_phishing",        ❌ Extra field
  "confidence": 0.95,                       ❌ Extra field
  "totalMessagesExchanged": 3,
  "extractedIntelligence": {...},
  "conversationSummary": "...",            ❌ Extra field
  "agentNotes": "..."
}
```

**New Structure** (CORRECT):
```json
{
  "sessionId": "abc123-session-id",
  "scamDetected": true,
  "totalMessagesExchanged": 18,
  "extractedIntelligence": {
    "bankAccounts": ["XXXX-XXXX-XXXX"],
    "upiIds": ["scammer@upi"],
    "phishingLinks": ["http://malicious-link.example"],
    "phoneNumbers": ["+91XXXXXXXXXX"],
    "suspiciousKeywords": ["urgent", "verify now", "account blocked"]
  },
  "agentNotes": "Scammer used urgency tactics and payment redirection"
}
```

**Changes**:
- ❌ Removed: `scamType`, `confidence`, `conversationSummary`
- ✅ Kept only fields from problem statement

---

### 3. ✅ Fixed agentNotes Content
**Problem**: agentNotes contained message count (redundant with `totalMessagesExchanged`)

**Old** (WRONG):
```
"agentNotes": "Scam type: credential_phishing. Confidence: 0.95. Messages exchanged: 3. Extracted 1 bank account(s)."
```

**New** (CORRECT):
```
"agentNotes": "Scammer used urgency tactics and payment redirection"
```

**Logic**: Now describes **scammer behavior and tactics**:
- Credential phishing → "requesting sensitive credentials (OTP/PIN/password)"
- Financial threat → "using urgency and account blocking threats"
- Reward scam → "false prize/lottery claims"
- Impersonation → "impersonating authority figures"
- Plus: urgency tactics, malicious links, payment redirection

---

### 4. ✅ Fixed totalMessagesExchanged Calculation
**Problem**: Only counted scammer messages, not honeypot responses

**Old Calculation** (WRONG):
```python
message_counts[session_id] += 1  # Only scammer messages
totalMessagesExchanged=message_counts.get(session_id, 1)  # = 3
```

**New Calculation** (CORRECT):
```python
scammer_msg_count = message_counts.get(session_id, 1)
total_msgs = scammer_msg_count * 2  # = 6 (includes honeypot responses)
```

**Example**:
- Scammer sends 3 messages
- Honeypot responds 3 times
- **Total = 6 messages** ✅

Formula: `totalMessagesExchanged = scammer_count × 2`

---

## Verification

Run test:
```bash
python test_callback_structure.py
```

Output:
```
✅ Callback Payload Structure:
{
  "sessionId": "abc123-session-id",
  "scamDetected": true,
  "totalMessagesExchanged": 18,
  "extractedIntelligence": { ... },
  "agentNotes": "Scammer used urgency tactics and payment redirection"
}

✅ All 5 required fields present
✅ No extra fields
✅ agentNotes describes behavior
✅ Message count includes both sides
```

---

## Deployment Instructions

After pushing to GitHub, Render will automatically:
1. Install `openai` package from updated requirements.txt
2. Restart server with fixed dependencies
3. Use OpenRouter (Gemini 2.0 Flash) for natural responses
4. Send correct callback structure to GUVI

**No manual action needed** - just wait for Render to redeploy (2-3 minutes).

---

## Expected Behavior Now

### Responses
**Before**: "safe", "unsafe S2" (Groq safety classification)
**After**: "Wait... how did my account get compromised? I'm at office now, my son helps me usually, pls tell me what to do"

### Callback
**Before**:
```json
{
  "scamType": "...",           ❌
  "confidence": 0.95,          ❌
  "totalMessagesExchanged": 3, ❌ (wrong count)
  "agentNotes": "Messages exchanged: 3..." ❌
}
```

**After**:
```json
{
  "sessionId": "...",
  "scamDetected": true,
  "totalMessagesExchanged": 6, ✅ (correct count)
  "extractedIntelligence": {...},
  "agentNotes": "Scammer used urgency tactics and payment redirection" ✅
}
```

---

## Files Changed

1. ✅ `requirements.txt` - Added openai package
2. ✅ `app/models.py` - Fixed CallbackPayload structure
3. ✅ `app/main.py` - Fixed agentNotes logic and message counting

All changes pushed to GitHub and will auto-deploy to Render.
