# Callback Trigger Conditions - Complete Analysis

## 🎯 When Does Our System Send the Callback to GUVI?

The callback is sent when **ALL THREE conditions** are met:

```python
# From app/main.py line 227-232
if (conversation_state.scam_detected and 
    conversation_state.agent_activated and
    not conversation_agent.should_continue_conversation(conversation_state)):
    
    # Schedule callback in background
    background_tasks.add_task(send_final_callback, session_id, conversation_state)
```

---

## ✅ CONDITION 1: `scam_detected = True`

**When this is set:**
- Scam detector analyzes the message
- Confidence score > threshold (default: 0.75)

**Code location:** [app/main.py](app/main.py) lines 157-159
```python
if detection_result.is_scam and detection_result.confidence >= settings.SCAM_CONFIDENCE_THRESHOLD:
    conversation_state.scam_detected = True
    conversation_state.agent_activated = True
```

**Settings:** From [.env](.env)
```
SCAM_CONFIDENCE_THRESHOLD=0.75
```

**What triggers scam detection:**
- Keywords: "urgent", "verify", "blocked", "suspended", "OTP", "PIN", "bank account"
- Phishing patterns: suspicious links, credential requests
- Urgency tactics: "immediately", "today", "now"
- Financial threats: "account blocked", "payment failed"

---

## ✅ CONDITION 2: `agent_activated = True`

**When this is set:**
- At the same time as `scam_detected`
- Agent takes over the conversation
- Starts engaging with believable persona

**Code location:** [app/main.py](app/main.py) line 159
```python
conversation_state.agent_activated = True
```

**What the agent does:**
- Generates human-like responses
- Uses personas: confused elderly, worried customer, excited winner
- Asks probing questions to extract intelligence
- Maintains cover without revealing detection

---

## ✅ CONDITION 3: `should_continue_conversation() = False`

This is the **MOST IMPORTANT** condition - it determines when conversation ends.

**Code location:** [app/agents/conversation_agent.py](app/agents/conversation_agent.py) lines 285-302
```python
def should_continue_conversation(self, conversation_state: ConversationState) -> bool:
    """Determine if conversation should continue."""
    
    # Stop if max turns reached
    if len(conversation_state.messages) >= settings.MAX_CONVERSATION_TURNS:
        return False
    
    # Stop if no new intelligence is being extracted
    last_message = conversation_state.messages[-1].text.lower() if conversation_state.messages else ""
    
    # Continue if scammer is still engaging and providing information
    engagement_indicators = [
        'call', 'contact', 'number', 'id', 'department', 'verify',
        'send', 'share', 'provide', 'give', 'tell', 'confirm'
    ]
    
    has_engagement = any(indicator in last_message for indicator in engagement_indicators)
    
    # Stop if conversation seems to be ending
    ending_indicators = ['goodbye', 'bye', 'later', 'thank you', 'thanks', 'ok bye']
    is_ending = any(indicator in last_message for indicator in ending_indicators)
    
    return has_engagement and not is_ending and len(conversation_state.messages) < 15
```

### Returns `False` (triggers callback) when:

#### 🛑 Max Turns Reached
```python
len(conversation_state.messages) >= settings.MAX_CONVERSATION_TURNS
```
- Default: `MAX_CONVERSATION_TURNS = 20` (from .env)
- If conversation reaches 20 messages → callback sent

#### 🛑 No Engagement Indicators
Scammer's message doesn't contain any of these words:
- `call`, `contact`, `number`, `id`, `department`, `verify`
- `send`, `share`, `provide`, `give`, `tell`, `confirm`

**Example:** If scammer just says "ok" or "fine" → no engagement → callback sent

#### 🛑 Conversation Ending
Scammer's message contains ending phrases:
- `goodbye`, `bye`, `later`, `thank you`, `thanks`, `ok bye`

**Example:** "ok thanks bye" → callback sent

#### 🛑 Message Count Limit (Soft Stop)
```python
len(conversation_state.messages) < 15
```
- If 15+ messages exchanged → returns False → callback sent
- This ensures callback happens even if engagement continues

---

## 📋 Complete Callback Flow

```
1. Message arrives → Scam detection runs
                    ↓
2. Is scam? (confidence >= 0.75)
   ├─ NO → Reply "Message received" → END (no callback)
   └─ YES → Set scam_detected = True
           Set agent_activated = True
           ↓
3. Agent generates human-like response
   Store message in conversation history
   Return response to GUVI
                    ↓
4. Check should_continue_conversation()
   ├─ TRUE → Wait for next message (no callback yet)
   └─ FALSE → 🚀 TRIGGER CALLBACK
                    ↓
5. Background task starts:
   - Extract intelligence (bank accounts, UPI, links, phones)
   - Generate agent notes
   - Create CallbackPayload
   - Send to https://hackathon.guvi.in/api/updateHoneyPotFinalResult
   - Retry up to 3 times if failed
   - Clean up conversation state
```

---

## 🔍 Specific Examples

### Example 1: Callback Sent After 15 Messages
```
Messages: 15 (reached soft limit)
scam_detected: True ✅
agent_activated: True ✅
should_continue: False ✅ (15 >= 15)
→ CALLBACK SENT
```

### Example 2: Callback Sent After "Goodbye"
```
Messages: 8
Last message: "ok goodbye"
scam_detected: True ✅
agent_activated: True ✅
should_continue: False ✅ (contains "goodbye")
→ CALLBACK SENT
```

### Example 3: Callback Sent - No Engagement
```
Messages: 6
Last message: "ok"
scam_detected: True ✅
agent_activated: True ✅
should_continue: False ✅ (no engagement indicators)
→ CALLBACK SENT
```

### Example 4: NO Callback - Still Engaging
```
Messages: 5
Last message: "Please send me your OTP"
scam_detected: True ✅
agent_activated: True ✅
should_continue: True ❌ (contains "send", "OTP" - engagement indicators)
→ CONTINUE CONVERSATION (no callback yet)
```

### Example 5: NO Callback - Not a Scam
```
Messages: 3
Last message: "Hi, how are you?"
scam_detected: False ❌
→ NO CALLBACK (legitimate message)
```

---

## ⚙️ Configuration Parameters

From [.env](.env):
```bash
# Controls when scam is detected
SCAM_CONFIDENCE_THRESHOLD=0.75

# Maximum messages before forcing callback
MAX_CONVERSATION_TURNS=20

# Controls logging detail
LOG_LEVEL=INFO
```

From [app/agents/conversation_agent.py](app/agents/conversation_agent.py):
```python
# Soft limit for conversation length
SOFT_LIMIT = 15  # Returns False if reached

# Engagement indicators (must be present to continue)
engagement_indicators = [
    'call', 'contact', 'number', 'id', 'department', 'verify',
    'send', 'share', 'provide', 'give', 'tell', 'confirm'
]

# Ending indicators (force stop if present)
ending_indicators = [
    'goodbye', 'bye', 'later', 'thank you', 'thanks', 'ok bye'
]
```

---

## 🎯 Summary: When Callback is Sent

| Condition | Logic | Result |
|-----------|-------|--------|
| Scam Detected | confidence >= 0.75 | ✅ Required |
| Agent Activated | Set when scam detected | ✅ Required |
| Max Turns (20) | messages >= 20 | ✅ Callback |
| Soft Limit (15) | messages >= 15 | ✅ Callback |
| Ending Phrase | "bye", "goodbye", etc. | ✅ Callback |
| No Engagement | No engagement keywords | ✅ Callback |
| Still Engaging | Has engagement keywords & < 15 msgs | ❌ Continue |
| Not a Scam | confidence < 0.75 | ❌ No Callback |

---

## 🚨 Current Issues with GUVI

Based on your logs, the callback IS being sent successfully:
```
"Successfully sent callback ... status_code": 200
```

**So the problem is NOT:**
- ❌ Callback not triggering
- ❌ Callback format wrong
- ❌ Callback failing to send

**The problem IS:**
- ⚠️ GUVI may not be reaching our `/honeypot` endpoint initially
- ⚠️ Or GUVI expects different timing for callbacks

The new diagnostic logging will show exactly when GUVI hits your endpoint and what they send.
