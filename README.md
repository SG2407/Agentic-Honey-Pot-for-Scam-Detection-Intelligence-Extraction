# 🕷️ Agentic Honey-Pot for Scam Detection & Intelligence Extraction

> **GUVI Hackathon 2026** - An AI-powered honeypot system that detects scam intent, autonomously engages scammers, and extracts actionable intelligence without revealing detection. Now includes an **Interactive UI** for real-time testing and intelligence monitoring!

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.31+-red.svg)](https://streamlit.io)
[![Groq](https://img.shields.io/badge/Groq-AI%20Powered-orange.svg)](https://groq.com)
[![Deployed](https://img.shields.io/badge/Deployed-Render-purple.svg)](https://agentic-honey-pot-for-scam-detection-iiv4.onrender.com)

## 🎯 Problem Statement

Online scams (bank fraud, UPI fraud, phishing, fake offers) are becoming increasingly adaptive. Scammers change tactics based on user responses, making traditional detection ineffective. This system uses an **Agentic Honey-Pot** approach - an AI-powered system that detects scam intent and autonomously engages scammers to extract intelligence without revealing detection.

## 🚀 Live Deployment

### API Endpoint
- **Honeypot API**: `https://agentic-honey-pot-for-scam-detection-iiv4.onrender.com/honeypot`
- **API Key**: `team_recursives`
- **Health Check**: `https://agentic-honey-pot-for-scam-detection-iiv4.onrender.com/health`

### 🎨 Interactive UI
**NEW!** Test the system as a scammer and watch intelligence extraction in real-time:
- **Streamlit UI**: [Your Streamlit App URL]
- **Features**: Real-time chat, session management, intelligence monitoring
- **Access**: Requires API key authentication

## ✨ Features

### 🎨 **Interactive UI** (NEW!)
- **Real-Time Chat Interface**: Act as a scammer and interact with the honeypot system
- **Session Management**: Create new sessions, view history, track conversations
- **Live Intelligence Display**: Watch as intelligence is extracted in real-time
  - 🏦 Bank Account Numbers
  - 💳 UPI IDs
  - 📞 Phone Numbers
  - 🔗 Phishing Links
  - 🔑 Suspicious Keywords
- **Visual Scam Detection**: See when the system detects scam behavior
- **Secure Access**: API key authentication required
- **Responsive Design**: Dark theme for better readability

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

### System Overview
```
┌──────────────────┐            ┌──────────────────────┐
│  Streamlit UI    │◄──────────►│   UI Backend (8001)  │
│  (Web Browser)   │  REST API  │   FastAPI Service    │
│                  │            │   • Session Store    │
│  • Chat Interface│            │   • Intelligence     │
│  • Intelligence  │            │     Monitor          │
│    Display       │            └──────────┬───────────┘
└──────────────────┘                       │
                                          │ Proxy via /ui-api/*
┌─────────────────┐                       │
│  GUVI Platform  │◄──────────────────────┼──────────────┐
└────────┬────────┘                       ▼              │
         │                     ┌────────────────────┐    │
         │                     │  Main Honeypot API │    │
         │                     │  (Port $PORT)      │    │
         ▼                     │                    │    │
┌─────────────────────────────────────────────────┐     │
│           FastAPI Server (main.py)              │     │
│  • Raw request logging                          │     │
│  • API key verification (flexible headers)      │     │
│  • Pydantic validation (robust input handling)  │     │
│  • /ui-api/* proxy endpoints (NEW)              │     │
└────────┬────────────────────────────────────────┘     │
         │                                               │
         ▼                                               │
┌─────────────────────────────────────────────────┐     │
│        Scam Detector (scam_detector.py)         │     │
│  1. Hard rules check (regex patterns)           │     │
│  2. AI analysis (Groq Llama 3.3 70B)            │     │
│  → Returns: is_scam, confidence, type           │     │
└────────┬────────────────────────────────────────┘     │
         │                                               │
         ├─────────────────┬──────────────────────┐     │
         │                 │                      │     │
    [Non-Scam]        [Scam Detected]            │     │
         │                 │                      │     │
         ▼                 ▼                      ▼     │
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
         │        │   Callback Service               │────┘
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

### UI Architecture
```
┌────────────────────────────────────────────────┐
│           Streamlit UI (streamlit_app.py)      │
│  • Chat interface with message history         │
│  • API key authentication                      │
│  • Session management (new/existing)           │
│  • Real-time intelligence display panels       │
└────────┬───────────────────────────────────────┘
         │ HTTP REST API
         ▼
┌────────────────────────────────────────────────┐
│         UI Backend (ui_backend.py)             │
│  • FastAPI service on port 8001 (internal)     │
│  • Session storage (SQLite)                    │
│  • Intelligence monitoring & extraction        │
│  • Communicates with main honeypot             │
└────────┬───────────────────────────────────────┘
         │ Calls main honeypot API
         ▼
┌────────────────────────────────────────────────┐
│      Main Honeypot API (main.py)               │
│  • Exposed via /ui-api/* proxy endpoints       │
│  • Port 8001 not externally accessible         │
│  • Proxy forwards requests to localhost:8001   │
└────────────────────────────────────────────────┘
```
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
│   ├── main.py                      # FastAPI app & /honeypot endpoint + UI proxy
│   ├── models.py                    # Pydantic models (robust validation)
│   ├── scam_detector.py             # Hard rules + AI detection
│   ├── conversation_agent.py        # Multi-persona AI agent
│   ├── intelligence_extractor.py    # Extract bank/UPI/phone/links
│   ├── callback_service.py          # Send results to GUVI
│   └── llm_provider.py              # LLM abstraction layer
├── ui/                              # 🎨 NEW: Interactive UI
│   ├── streamlit_app.py             # Streamlit chat interface
│   ├── ui_backend.py                # FastAPI UI backend service
│   ├── session_store.py             # SQLite session management
│   ├── intelligence_monitor.py      # Real-time intelligence extraction
│   ├── requirements_ui.txt          # UI-specific dependencies
│   ├── .env.ui                      # UI configuration
│   ├── Dockerfile                   # Container configuration
│   ├── start_ui.sh / .bat           # Startup scripts
│   └── README_UI.md                 # UI documentation
├── config/
│   └── settings.py                  # Environment configuration
├── tests/
│   ├── test_honeypot.py
│   ├── test_guvi_compliance.py      # GUVI format compliance tests
│   └── test_*.py                    # Various test suites
├── demo.py                          # Full system demo
├── requirements.txt                 # Main app dependencies
├── render.yaml                      # Render deployment config
├── Procfile                         # Process configuration
└── README.md                        # This file
```

## 🎮 Using the Interactive UI

### Access the Web Interface
1. Visit the Streamlit UI (deployed separately): `[Your Streamlit App URL]`
2. Enter your API key: `team_recursives`
3. Choose to start a new session or continue an existing one

### Features
- **💬 Chat Interface**: Type messages as if you're a scammer
- **🔍 Scam Detection**: Visual indicator shows when scam behavior is detected
- **📊 Intelligence Dashboard**: Real-time display of extracted data:
  - Bank Account Numbers
  - UPI IDs
  - Phone Numbers
  - Phishing Links
  - Suspicious Keywords
- **📝 Session History**: View all messages in the current conversation
- **🔄 Session Management**: Create new sessions or load existing ones

### Example Workflow
1. **Start New Session**: Click "New Session" to begin
2. **Send Scam Message**: Try: *"Your bank account will be blocked. Verify now at http://fake-bank.com"*
3. **Watch Detection**: See the scam indicator turn red
4. **View Intelligence**: Bank links and keywords appear in the side panel
5. **Continue Chat**: The honeypot responds naturally to keep engagement
6. **Monitor Extraction**: Watch as more intelligence is extracted with each message

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

#### Start Main Honeypot API
```bash
# Start main honeypot server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Test with demo
python demo.py
```

#### Start UI (Optional - for local testing)
```bash
# Navigate to UI directory
cd ui

# Start both UI backend and Streamlit (runs on ports 8001 & 8501)
./start_ui.sh  # macOS/Linux
# OR
start_ui.bat   # Windows

# Access UI at: http://localhost:8501
```

**Note**: For production, both services run together on Render automatically.

## 🌐 Deployment

### Main Honeypot API (Render)
The main honeypot API is deployed on Render and runs both:
1. **Main Honeypot Service** - Handles GUVI callbacks on port `$PORT`
2. **UI Backend Service** - Runs internally on port `8001` (not externally accessible)
3. **Proxy Endpoints** - `/ui-api/*` routes forward requests from main app to UI backend

**Environment Variables on Render:**
```env
API_KEY=team_recursives
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile
CALLBACK_URL=https://hackathon.guvi.in/api/updateHoneyPotFinalResult
MESSAGE_TIMEOUT_SECONDS=10
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### Interactive UI (Streamlit Cloud)
Deploy the Streamlit UI separately:

1. **Fork/Clone** this repository to your GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click **"New app"**
4. **Repository**: `your-username/Delhi_Hackathon`
5. **Branch**: `main`
6. **Main file path**: `ui/streamlit_app.py`
7. **App URL**: Choose a custom name

**Add Secrets** (Settings → Secrets):
```toml
UI_BACKEND_URL = "https://agentic-honey-pot-for-scam-detection-iiv4.onrender.com/ui-api"
```

**Note**: The `UI_BACKEND_URL` points to the proxy endpoints on the main Render deployment, which forwards requests to the internal UI backend service.

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

### UI API Endpoints

All UI endpoints are proxied through `/ui-api/*` on the main Render deployment:

#### POST `/ui-api/session/new`
Create a new UI session

**Headers:**
```http
x-api-key: team_recursives
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": 1707736800000
}
```

#### POST `/ui-api/chat`
Send a message and get honeypot response

**Request:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Your account will be blocked"
}
```

**Response:**
```json
{
  "reply": "Why will my account be blocked?",
  "scam_detected": true,
  "intelligence": {
    "bankAccounts": [],
    "upiIds": [],
    "phoneNumbers": [],
    "phishingLinks": [],
    "suspiciousKeywords": ["account", "blocked"]
  }
}
```

#### GET `/ui-api/session/{session_id}`
Get session details

#### GET `/ui-api/session/{session_id}/messages`
Get conversation history

#### DELETE `/ui-api/session/{session_id}`
Delete a session

#### GET `/ui-api/health`
UI backend health check

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
python test_guvi_compliance.py

# Full system demo
python demo.py

# UI component tests
cd ui && python test_ui_components.py
```

### Test API Manually
```bash
# Test main honeypot endpoint
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

# Test UI backend health
curl https://agentic-honey-pot-for-scam-detection-iiv4.onrender.com/ui-api/health
```

### Test UI Locally
```bash
# Start local UI
cd ui && ./start_ui.sh

# Visit http://localhost:8501
# Enter API key: team_recursives
# Start chatting!
```

## 🛠️ Technical Details

### Key Technologies

#### Backend
- **FastAPI**: Modern async web framework for both main API and UI backend
- **Pydantic V2**: Robust data validation with `model_dump()`, `ConfigDict`
- **Groq API**: Llama 3.3 70B model for AI responses
- **httpx**: Async HTTP client for callbacks and inter-service communication
- **Python 3.11+**: Latest async/await features

#### Frontend & UI
- **Streamlit 1.31.0**: Interactive web UI for chat interface
- **SQLite**: Lightweight database for session storage
- **Asyncio**: Parallel intelligence extraction

#### Deployment
- **Render**: Main honeypot + UI backend (single service, dual process)
- **Streamlit Cloud**: Frontend UI hosting (free tier)
- **Proxy Pattern**: Main app exposes `/ui-api/*` endpoints to forward to internal port 8001

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

#### Main Honeypot API

| Variable | Default | Description |
|----------|---------|-------------|
| `API_KEY` | `team_recursives` | API authentication key |
| `GROQ_API_KEY` | *Required* | Groq API key for AI |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | AI model |
| `CALLBACK_URL` | GUVI endpoint | Final result callback URL |
| `MESSAGE_TIMEOUT_SECONDS` | `10` | Timeout for scam sessions |
| `ENVIRONMENT` | `development` | Environment mode |
| `LOG_LEVEL` | `INFO` | Logging level |

#### UI Configuration (Streamlit Secrets)

| Variable | Default | Description |
|----------|---------|-------------|
| `UI_BACKEND_URL` | *Required* | URL to UI backend proxy endpoints |

**Local Development** (ui/.env.ui):
```env
HONEYPOT_API_URL=http://localhost:8000
API_KEY=team_recursives
UI_BACKEND_URL=http://localhost:8001
```

**Production** (Streamlit Secrets):
```toml
UI_BACKEND_URL = "https://agentic-honey-pot-for-scam-detection-iiv4.onrender.com/ui-api"
```

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

### Main Honeypot API

#### No Logs from GUVI?
1. Check endpoint URL: `https://agentic-honey-pot-for-scam-detection-iiv4.onrender.com/honeypot`
2. Verify API key: `team_recursives`
3. Check Render logs for incoming requests
4. Test manually with curl/Postman

#### INVALID_REQUEST_BODY Error?
- ✅ Fixed: All 5 intelligence fields always present
- ✅ Fixed: conversationHistory uses `Field(default_factory=list)`
- ✅ Fixed: Timestamp handles str/int/datetime
- ✅ Fixed: Sender normalized (lowercase, trimmed)
- ✅ Fixed: Metadata fields all optional

#### Server Not Responding?
```bash
# Check if port is in use
lsof -i :8000

# Restart server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Interactive UI

#### "Invalid API key" Error?
1. **Check Streamlit Secrets**: Go to app Settings → Secrets
2. **Verify UI_BACKEND_URL**: Should be `https://agentic-honey-pot-for-scam-detection-iiv4.onrender.com/ui-api`
3. **Test Backend**: `curl https://agentic-honey-pot-for-scam-detection-iiv4.onrender.com/ui-api/health`
4. **Check API Key**: Make sure you're entering `team_recursives` correctly (no extra spaces)

#### "Not Connected" Status?
1. **Check Render Deployment**: Ensure latest code is deployed
2. **Verify Proxy Endpoints**: Check `/ui-api/health` returns `{"status":"healthy"}`
3. **Check Logs**: Look for errors in Render dashboard
4. **Restart Streamlit**: Settings → Reboot app

#### UI Not Loading?
1. **Clear Browser Cache**: Hard refresh (Ctrl+Shift+R / Cmd+Shift+R)
2. **Check Streamlit Status**: Visit Streamlit dashboard
3. **Verify Deployment**: Ensure `ui/streamlit_app.py` is the main file path
4. **Check Secrets**: Confirm `UI_BACKEND_URL` is set correctly

#### Sessions Not Persisting?
- SQLite database (`ui/sessions.db`) is created automatically
- For local development, check file permissions
- On Render, database is ephemeral (resets on deploy)
- Consider using persistent storage for production

## 📝 License

MIT License - See [LICENSE](LICENSE) for details

---

## 🙏 Acknowledgments

- **GUVI Hackathon 2026** for the challenge
- **Groq** for fast AI inference
- **FastAPI** for excellent async framework
- **Streamlit** for rapid UI development
- **Render** for reliable hosting

---

## 📊 Project Highlights

### What Makes This Special?

✅ **Dual Interface**: 
- RESTful API for GUVI integration
- Interactive web UI for testing and demonstration

✅ **Real-Time Intelligence**:
- Live extraction and display as conversations progress
- Visual indicators for scam detection

✅ **Production-Ready**:
- Deployed on Render with automatic scaling
- Robust error handling and validation
- Comprehensive logging and monitoring

✅ **Developer-Friendly**:
- Clear architecture with separation of concerns
- Extensive documentation
- Easy local development setup

✅ **Security-First**:
- API key authentication on all endpoints
- No storage of sensitive data
- Privacy-conscious intelligence masking

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

- **Issues**: [GitHub Issues](https://github.com/SG2407/Agentic-Honey-Pot-for-Scam-Detection-Intelligence-Extraction/issues)
- **Discussions**: [GitHub Discussions](https://github.com/SG2407/Agentic-Honey-Pot-for-Scam-Detection-Intelligence-Extraction/discussions)
- **Hackathon**: [GUVI Delhi Hackathon 2026](https://hackathon.guvi.in)

---

<div align="center">

**🏆 Built for Delhi Hackathon 2026 🏆**

*Protecting people from scams with the power of AI*

### 🎨 Try the Interactive UI
Experience the honeypot in action at our Streamlit deployment!

[**Launch Interactive Demo →**](https://your-streamlit-app-url)

---

**Tech Stack**: Python • FastAPI • Streamlit • Groq AI • SQLite • Render

**Features**: Scam Detection • AI Agent • Intelligence Extraction • Real-Time UI

</div>