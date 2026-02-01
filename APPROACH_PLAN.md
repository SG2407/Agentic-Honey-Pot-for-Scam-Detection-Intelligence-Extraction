# 🎯 Agentic Honey-Pot: Clean Implementation Approach Plan

## 📋 GUVI Requirements (Confirmed)

### Core Behavior
- ✅ **Respond to EVERY message** with valid JSON (never silent)
- ✅ **One callback per session** (strict enforcement)
- ✅ **410 Gone after callback** (session closed)
- ✅ **10-second timeout** (inactivity trigger)

### Intelligence & Detection
- ✅ **Extract from ALL messages** (current + history)
- ✅ **Hard rules FIRST** (guaranteed scam patterns)
- ✅ **LLM secondary** (never rely solely on LLM)
- ✅ **Natural coaxing** (agent induces intel organically)

### Message Count Formula
```
totalMessagesExchanged = scammer_messages + agent_replies
```
❌ Do NOT count conversationHistory separately

---

## 🏗️ Clean Architecture

### File Structure
```
app/
├── main.py                  # FastAPI app, /honeypot endpoint
├── models.py                # Pydantic models
├── scam_detector.py         # Hard rules → LLM detection
├── conversation_agent.py    # Natural AI engagement
├── intelligence_extractor.py # Extract intel from all messages
└── callback_service.py      # Send final result to GUVI
```

### Single Execution Flow
```
1. Parse request (Unix ms timestamps + ISO-8601)
2. Check if callback already sent → 410 Gone
3. Check timeout (10 seconds) → trigger callback if exceeded
4. Hard scam pattern check (FIRST, confidence 1.0)
5. LLM scam detection (secondary)
6. Extract intelligence from ALL messages
7. If intel found → send callback → mark session closed
8. Generate AI reply (engage if scam, neutral if not)
9. Return 200 OK with reply
```

---

## 🔒 Hard Scam Patterns (Guaranteed Detection)

Execute **BEFORE** LLM call, return `confidence = 1.0`:

| Pattern | Keywords | Scam Type |
|---------|----------|-----------|
| **Credential Phishing** | "send/share OTP", "provide PIN/password" | credential_phishing |
| **Account Urgency** | "account blocked" + "urgent/immediate/verify" | financial_threat |
| **UPI Credentials** | "UPI PIN", "UPI ID" + "share/send" | credential_phishing |
| **Bank Details** | "bank account number", "IFSC code" | credential_phishing |
| **Prize Scam** | "won prize/lottery", "congratulations" | prize_scam |

**Why First?**
- LLMs can rate-limit or fail
- GUVI penalizes API instability
- Guaranteed 100% accuracy on obvious scams

---

## 📞 Callback Logic (CRITICAL)

### Trigger Conditions (ANY ONE)
```python
send_callback_when = (
    has_real_intelligence()  # bank/UPI/phone/link found
    OR
    timeout_exceeded()       # 10 seconds since last message
)
```

### Real Intelligence Definition
- ✅ Bank account numbers
- ✅ UPI IDs
- ✅ Phone numbers
- ✅ Phishing links
- ❌ NOT just keywords (must be actual values)

### After Callback Sent
```python
callback_sent_sessions.add(session_id)  # Mark immediately
return JSONResponse(status_code=410, content={"error": "Session closed"})
```

### Timeout Behavior
- **Scam session**: 10-second timeout triggers callback
- **Non-scam session**: NO timeout callback (keep open forever)
- **Why?**: Non-scams don't need final result

---

## 💬 Message Response Strategy

### Scam Detected
```python
if scam_confidence >= 0.7:
    # Activate agent, engage naturally
    reply = agent.generate_reply(
        message=scammer_message,
        persona="worried_customer",  # Choose appropriate persona
        conversation_history=history
    )
    # Agent coaxes intel: "Oh no! Which account should I verify?"
```

### Non-Scam
```python
else:
    # Neutral, generic response
    reply = "Thank you for your message. I have received it."
    # No callback, no timeout trigger
```

### Key Points
- ✅ ALWAYS return valid JSON
- ✅ Agent never explicitly asks for intel ("Give me your UPI")
- ✅ Coax organically ("Oh no! How do I fix this?")

---

## 🕐 Timestamp Handling

### Input Formats Supported
1. **Unix milliseconds** (integer): `1769938742773`
2. **ISO-8601 string**: `"2026-01-21T10:15:30Z"`
3. **Datetime object**: `datetime(2026, 1, 21, 10, 15, 30)`

### All Operations Timezone-Aware
```python
from datetime import datetime, timezone

# ✅ Always use timezone.utc
current_time = datetime.now(timezone.utc)
last_msg_time = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
timeout_check = (current_time - last_msg_time).total_seconds() > 10
```

**Why?**
- Prevents "can't subtract offset-naive and offset-aware" errors
- GUVI sends Unix milliseconds (integers)

---

## 📤 Callback Payload (Exact Format)

```json
{
  "sessionId": "string",
  "scamDetected": true,
  "totalMessagesExchanged": 5,
  "extractedIntelligence": {
    "bankAccounts": ["123456789012"],
    "upiIds": ["scammer@paytm"],
    "phishingLinks": ["https://fake-bank.com"],
    "phoneNumbers": ["+919876543210"]
  },
  "agentNotes": "Scammer requested OTP sharing..."
}
```

### Rules
- ✅ Send exact values (no masking: "123XXXX789" ❌)
- ✅ Remove empty arrays (if no UPI IDs, omit `upiIds` key)
- ✅ `totalMessagesExchanged` = scammer_msgs + agent_replies
- ✅ ONLY send these 5 fields (no extras)

### HTTP Configuration
```python
timeout = httpx.Timeout(connect=5, read=10, write=5, pool=5)
headers = {"Content-Type": "application/json"}
endpoint = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"
```

---

## 🎭 Conversation Agent Personas

### Personas (Choose Based on Scam Type)
| Scam Type | Persona | Behavior |
|-----------|---------|----------|
| Financial threat | `worried_customer` | "Oh no! My account! What should I do?" |
| Prize/lottery | `excited_winner` | "Really?! I won?! How do I claim it?" |
| Tech support | `confused_elderly` | "I don't understand. Can you help me?" |

### Natural Coaxing Examples
❌ **Wrong**: "Please provide your bank account number"
✅ **Right**: "Which account is affected? I want to check my balance"

❌ **Wrong**: "Give me the UPI ID"
✅ **Right**: "Should I use my UPI to verify? Which one?"

---

## 🔍 Intelligence Extraction

### Regex Patterns
```python
bank_account = r'\b\d{9,18}\b'  # 9-18 digit numbers
upi_id = r'\b[\w\.-]+@[\w\.-]+\b'  # user@provider
phone = r'\b(\+91|0)?[6-9]\d{9}\b'  # Indian phone numbers
phishing_link = r'https?://[^\s]+'  # URLs
```

### Extraction Scope
```python
# Combine ALL message texts
all_text = (
    current_message.text +
    " ".join([msg.text for msg in conversation_history])
)
extract_intelligence(all_text)  # Scan everything
```

**Why?**
- GUVI may embed intel in early turns
- Agent's replies may contain scammer intel

---

## 🛡️ Error Handling

### Strategy
```python
try:
    # Main logic
except ValidationError as e:
    # Pydantic validation failed
    raise HTTPException(status_code=422, detail=str(e))
except Exception as e:
    # Unexpected error
    logger.error(f"Error: {e}")
    raise HTTPException(status_code=500, detail="Internal server error")
```

### Never Return 200 on Errors
❌ **Wrong**: `return HoneypotResponse(status="success", reply="Error occurred")`
✅ **Right**: `raise HTTPException(status_code=500, detail=str(e))`

---

## 🔐 API Key Verification

### Flexible, Case-Insensitive
```python
def get_api_key(
    x_api_key: Optional[str] = Header(None),
    X_API_KEY: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None),
    api_key: Optional[str] = Query(None)
):
    key = x_api_key or X_API_KEY or authorization or api_key
    if not key:
        raise HTTPException(status_code=401, detail="Missing API key")
    # Validate against environment variable
```

---

## 📊 Global State Management

### Session Tracking
```python
callback_sent_sessions: Set[str] = set()  # Sessions that received callback
last_message_time: Dict[str, datetime] = {}  # Timeout tracking
```

### Thread Safety
- FastAPI runs in async context
- Use Python sets/dicts (GIL protection for simple ops)
- For production: Consider Redis/database

---

## 🚀 Deployment Checklist

### Environment Variables
```bash
GROQ_API_KEY=your_groq_key
API_KEY=team_recursives
CALLBACK_URL=https://hackathon.guvi.in/api/updateHoneyPotFinalResult
MESSAGE_TIMEOUT_SECONDS=10
```

### Render Configuration
```yaml
# render.yaml
services:
  - type: web
    name: agentic-honey-pot
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

---

## ✅ Success Criteria

- [ ] All GUVI requests return valid JSON
- [ ] One callback per session (strictly enforced)
- [ ] 410 Gone after callback sent
- [ ] Hard scam patterns detected (confidence 1.0)
- [ ] LLM detection works (with fallback)
- [ ] Intelligence extracted from all messages
- [ ] Exact values sent (no masking)
- [ ] Empty arrays removed from callback
- [ ] Timeout works (10 seconds)
- [ ] Timezone-aware datetime throughout
- [ ] Proper error handling (500, not 200)
- [ ] Clean, understandable code flow

---

## 📝 Implementation Order

1. **models.py** - Pydantic models with timestamp handling
2. **scam_detector.py** - Hard rules + LLM detection
3. **intelligence_extractor.py** - Regex extraction from all messages
4. **callback_service.py** - GUVI callback with exact format
5. **conversation_agent.py** - Natural AI engagement
6. **main.py** - FastAPI endpoint with single execution flow

---

## 🧪 Testing Strategy

### Test Cases
1. **Hard scam pattern** → Immediate detection, confidence 1.0
2. **LLM scam** → Detection via Groq API
3. **Intelligence extraction** → Find bank/UPI/phone/link
4. **Timeout trigger** → 10-second callback
5. **Non-scam message** → Neutral reply, no callback
6. **After callback** → 410 Gone
7. **Unix milliseconds** → Parse correctly
8. **Timezone operations** → No mixing errors

---

## 🎯 Final Notes

- **Simplicity over complexity**: Single execution path, clear flow
- **Hard rules over LLM**: Guaranteed accuracy, no rate limits
- **All messages, not just current**: GUVI may embed intel early
- **Natural coaxing**: Agent induces, never explicitly asks
- **410 after callback**: Session lifecycle compliance
- **No masking**: Send exact values found
- **Timeout for scams only**: Non-scams stay open forever

---

**Ready to implement? Let's build this cleanly from scratch!** 🚀
