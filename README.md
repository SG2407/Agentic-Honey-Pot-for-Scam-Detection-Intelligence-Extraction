# 🕷️ Agentic Honey-Pot for Scam Detection & Intelligence Extraction

> **GUVI Hackathon 2026** - An AI-powered honeypot system that detects scam intent, autonomously engages scammers, and extracts actionable intelligence without revealing detection.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![Groq](https://img.shields.io/badge/Groq-AI%20Powered-orange.svg)](https://groq.com)
[![Deployed](https://img.shields.io/badge/Deployed-Render-purple.svg)](https://agentic-honey-pot-for-scam-detection-iiv4.onrender.com)

## 🎯 Problem Statement

Online scams (bank fraud, UPI fraud, phishing, fake offers) are becoming increasingly adaptive. Scammers change tactics based on user responses, making traditional detection ineffective. This system uses an **Agentic Honey-Pot** approach - an AI-powered system that detects scam intent and autonomously engages scammers to extract intelligence without revealing detection.

## 🚀 Live Deployment

- **Endpoint**: `https://agentic-honey-pot-for-scam-detection-iiv4.onrender.com/honeypot`
- **API Key**: `team_recursives`
- **Health Check**: `https://agentic-honey-pot-for-scam-detection-iiv4.onrender.com/health`

## ✨ Features

### 🔍 **Hybrid Scam Detection**
- **Hard Rules First**: Regex patterns for 20+ scam indicators (urgent, verify, OTP, blocked, suspicious URLs)
- **AI-Powered Analysis**: Groq Llama 3.3 70B for semantic understanding
- **Confidence Scoring**: 0.0-1.0 scale with 0.7 threshold for scam confirmation
- **Scam Type Classification**: Financial threat, credential phishing, prize scam, tech support, etc.

### 🤖 **Autonomous AI Agent**
- **Multi-Persona Engagement**: 
  - Confused Elderly (slow to understand, asks for clarification)
  - Worried Parent (concerned about family, emotional responses)
  - Busy Professional (distracted, provides info in fragments)
- **Context-Aware Responses**: Uses conversation history for natural flow
- **Never Reveals Detection**: Maintains human-like persona throughout

### 📊 **Intelligence Extraction**
Automatically extracts and tracks:
- 🏦 Bank Account Numbers (with privacy masking)
- 💳 UPI IDs (e.g., scammer@upi)
- 📞 Phone Numbers (international format support)
- 🔗 Phishing Links (malicious URLs)
- 🔑 Suspicious Keywords (urgent, verify, OTP, blocked, click here, etc.)

### ⏱️ **Smart Session Management**
- **No Timeout for Non-Scam**: Sessions stay open indefinitely for non-scam messages
- **Timeout Only for Scams**: 10-second timeout after scam detection
- **Callback Triggers**: Sends final report when intelligence extracted OR timeout reached
- **Session Tracking**: Prevents duplicate callbacks for closed sessions

### 🛡️ **Robust Input Handling**
- ✅ Flexible timestamp parsing (Unix ms, ISO-8601, numeric strings)
- ✅ Optional fields (conversationHistory, metadata)
- ✅ Case-insensitive sender normalization ("Scammer" → "scammer")
- ✅ Extra field tolerance (extra='ignore')
- ✅ Multiple API key header support (x-api-key, X-API-KEY, Authorization)

## 🏗️ Architecture

```
┌─────────────────┐
│  GUVI Platform  │  Sends suspected scam messages
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│           FastAPI Server (main.py)              │
│  • Raw request logging                          │
│  • API key verification (flexible headers)      │
│  • Pydantic validation (robust input handling)  │
└────────┬────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│        Scam Detector (scam_detector.py)         │
│  1. Hard rules check (regex patterns)           │
│  2. AI analysis (Groq Llama 3.3 70B)            │
│  → Returns: is_scam, confidence, type           │
└────────┬────────────────────────────────────────┘
         │
         ├─────────────────┬──────────────────────┐
         │                 │                      │
    [Non-Scam]        [Scam Detected]            │
         │                 │                      │
         ▼                 ▼                      ▼
  ┌──────────┐    ┌────────────────┐    ┌────────────────┐
  │ Neutral  │    │ Start Timeout  │    │ Intelligence   │
  │ Reply    │    │ Tracking (10s) │    │ Extractor      │
  │          │    │                │    │ (extract data) │
  └──────────┘    └────────────────┘    └────────┬───────┘
         │                 │                      │
         │                 ▼                      │
         │        ┌─────────────────┐             │
         │        │ Conversation    │             │
         │        │ Agent (AI)      │             │
         │        │ • Multi-persona │             │
         │        │ • Context-aware │             │
         │        └────────┬────────┘             │
         │                 │                      │
         │                 │    [Intel Found      │
         │                 │     OR Timeout]      │
         │                 │         │            │
         │                 ▼         ▼            ▼
         │        ┌──────────────────────────────────┐
         │        │   Callback Service               │
         │        │   POST to GUVI with results      │
         │        │   • sessionId                    │
         │        │   • scamDetected                 │
         │        │   • totalMessagesExchanged       │
         │        │   • extractedIntelligence (5 fields) │
         │        │   • agentNotes                   │
         │        └────────┬─────────────────────────┘
         │                 │
         ▼                 ▼
  ┌──────────────────────────────┐
  │  Return 200 OK with reply    │
  │  (neutral or engagement text) │
  └───────────────────────────────┘
```

## 📁 Project Structure

```
Delhi_Hackathon/
├── app/
│   ├── main.py                      # FastAPI app & /honeypot endpoint
│   ├── models.py                    # Pydantic models (robust validation)
│   ├── agents/
│   │   ├── scam_detector.py         # Hard rules + AI detection
│   │   └── conversation_agent.py    # Multi-persona AI agent
│   ├── services/
│   │   ├── intelligence_extractor.py  # Extract bank/UPI/phone/links
│   │   └── callback_service.py      # Send results to GUVI
│   └── utils/
│       └── logger.py                # Structured logging
├── config/
│   └── settings.py                  # Environment configuration
├── tests/
│   ├── test_honeypot.py
│   ├── test_guvi_validation.py      # GUVI format compliance tests
│   └── test_minimal_fixes.py        # Robustness validation
├── demo.py                          # Full system demo
├── requirements.txt                 # Python dependencies
├── render.yaml                      # Render deployment config
└── README.md                        # This file
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Groq API Key (free from [console.groq.com](https://console.groq.com))

### 1. Installation

```bash
# Clone repository
git clone https://github.com/SG2407/Agentic-Honey-Pot-for-Scam-Detection-Intelligence-Extraction.git
cd Agentic-Honey-Pot-for-Scam-Detection-Intelligence-Extraction

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create `.env` file:
```env
# API Configuration
API_KEY=team_recursives

# Groq Configuration  
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile

# Callback Configuration
CALLBACK_URL=https://hackathon.guvi.in/api/updateHoneyPotFinalResult
MESSAGE_TIMEOUT_SECONDS=10

# Environment
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### 3. Run Locally

```bash
# Start server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Test with demo
python demo.py
```

## 📡 API Reference

### Authentication
```http
x-api-key: team_recursives
Content-Type: application/json
```

### POST `/honeypot`

**Request:**
```json
{
  "sessionId": "unique-session-id",
  "message": {
    "sender": "scammer",
    "text": "Your bank account will be blocked. Verify now.",
    "timestamp": "2026-02-01T10:15:30Z"
  },
  "conversationHistory": [],
  "metadata": {
    "channel": "SMS",
    "language": "English",
    "locale": "IN"
  }
```

**Response:**
```json
{
  "status": "success",
  "reply": "Why will my account be blocked?"
}
```

### GET `/health`

**Response:**
```json
{
  "status": "healthy",
  "service": "Agentic Honey-Pot",
  "version": "2.0.0",
  "timestamp": "2026-02-01T10:30:00Z"
}
```

## 🔄 How It Works

### 1. **Message Received**
- GUVI sends POST to `/honeypot`
- System logs raw request for debugging
- Pydantic validates with robust error handling

### 2. **Scam Detection**
- **Hard Rules Check**: Regex patterns for urgent, verify, OTP, blocked, phishing URLs
- **AI Analysis**: If hard rules don't trigger, Groq AI analyzes semantically
- **Result**: `is_scam`, `confidence` (0-1), `scam_type`, `reasoning`

### 3. **Session Management**
- **Non-Scam**: No timeout, session stays open, neutral reply sent
- **Scam Detected**: Start 10s timeout tracking, engage with AI agent

### 4. **Intelligence Extraction**
- Extract from current message + entire conversation history
- Find: bank accounts, UPI IDs, phone numbers, phishing links, keywords
- All 5 fields always present (empty arrays if nothing found)

### 5. **Callback Decision**
Send callback to GUVI when:
- ✅ Real intelligence extracted (non-empty data found)
- ✅ Timeout reached (10s since last message in scam session)

### 6. **Return Response**
- Always 200 OK (never HTTP errors)
- Closed sessions: Neutral acknowledgment
- Active sessions: AI-generated engagement or neutral reply

## 🧪 Testing

### Run Tests
```bash
# GUVI format compliance
python test_guvi_validation.py

# Minimal fixes validation
python test_minimal_fixes.py

# Full demo
python demo.py
```

### Manual Testing
```bash
curl -X POST "https://agentic-honey-pot-for-scam-detection-iiv4.onrender.com/honeypot" \
  -H "x-api-key: team_recursives" \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "test-123",
    "message": {
      "sender": "scammer",
      "text": "Your account will be blocked. Click here to verify.",
      "timestamp": "2026-02-01T10:15:30Z"
    },
    "conversationHistory": []
  }'
```

## 🛠️ Technical Details

### Key Technologies
- **FastAPI**: Modern async web framework
- **Pydantic V2**: Robust data validation with `model_dump()`, `ConfigDict`
- **Groq API**: Llama 3.3 70B model for AI responses
- **httpx**: Async HTTP client for callbacks
- **Python 3.11+**: Latest async/await features

### Robustness Features
✅ **Flexible Input Handling**:
- Timestamp: Unix ms, ISO-8601, numeric strings
- Sender: Case-insensitive, auto-normalized
- conversationHistory: Optional with `Field(default_factory=list)`
- metadata: All fields optional
- Extra fields: Ignored via `extra='ignore'`

✅ **Multi-Header API Key Support**:
- `x-api-key`
- `X-API-KEY`
- `Authorization`
- Query parameter `api_key`

✅ **Smart Session Tracking**:
- In-memory dictionaries (callback_sent_sessions, last_message_time)
- Prevents duplicate callbacks
- Timeout only for scam sessions

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_KEY` | `team_recursives` | API authentication key |
| `GROQ_API_KEY` | *Required* | Groq API key for AI |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | AI model |
| `CALLBACK_URL` | GUVI endpoint | Final result callback URL |
| `MESSAGE_TIMEOUT_SECONDS` | `10` | Timeout for scam sessions |
| `ENVIRONMENT` | `development` | Environment mode |
| `LOG_LEVEL` | `INFO` | Logging level |

## 📊 GUVI Compliance

### ✅ All Requirements Met
- [x] Detect scam intent
- [x] Activate autonomous AI Agent
- [x] Maintain believable human-like persona
- [x] Handle multi-turn conversations
- [x] Extract scam-related intelligence
- [x] Return structured JSON response
- [x] Secure access using API key
- [x] Send final result callback to GUVI

### Callback Format
```json
{
  "sessionId": "xxx",
  "scamDetected": true,
  "totalMessagesExchanged": 5,
  "extractedIntelligence": {
    "bankAccounts": [],
    "upiIds": ["scammer@upi"],
    "phishingLinks": ["http://evil.com"],
    "phoneNumbers": ["+91XXXXXXXXXX"],
    "suspiciousKeywords": ["urgent", "verify", "blocked"]
  },
  "agentNotes": "Scammer used urgency tactics"
}
```

## 🐛 Troubleshooting

### No Logs from GUVI?
1. Check endpoint URL: `https://agentic-honey-pot-for-scam-detection-iiv4.onrender.com/honeypot`
2. Verify API key: `team_recursives`
3. Check Render logs for incoming requests
4. Test manually with curl/Postman

### INVALID_REQUEST_BODY Error?
- ✅ Fixed: All 5 intelligence fields always present
- ✅ Fixed: conversationHistory uses `Field(default_factory=list)`
- ✅ Fixed: Timestamp handles str/int/datetime
- ✅ Fixed: Sender normalized (lowercase, trimmed)
- ✅ Fixed: Metadata fields all optional

### Server Not Responding?
```bash
# Check if port is in use
lsof -i :8000

# Restart server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 📝 License

MIT License - See [LICENSE](LICENSE) for details

---

## 🙏 Acknowledgments

- **GUVI Hackathon 2026** for the challenge
- **Groq** for fast AI inference
- **FastAPI** for excellent async framework
- **Render** for reliable hosting

---

**Built with ❤️ by Team Recursives**

## 👥 Team & Acknowledgments

**Developed for Delhi Hackathon 2026**
- **Challenge**: AI-Powered Agentic Honeypot for Scam Detection
- **Organization**: GUVI & Technical Partners

**Special Thanks:**
- 🤖 **Groq** for providing powerful AI inference APIs
- 🚀 **FastAPI** team for the excellent web framework
- 🔧 **Python Community** for the robust ecosystem

## 📞 Support & Contact

- **Issues**: [GitHub Issues](https://github.com/YOUR_USERNAME/Delhi_Hackathon_AI_Honeypot/issues)
- **Discussions**: [GitHub Discussions](https://github.com/YOUR_USERNAME/Delhi_Hackathon_AI_Honeypot/discussions)
- **Hackathon**: [GUVI Delhi Hackathon 2026](https://hackathon.guvi.in)

---

<div align="center">

**🏆 Built for Delhi Hackathon 2026 🏆**

*Protecting people from scams with the power of AI*

</div>