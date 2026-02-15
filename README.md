# 🕷️ Agentic Honey-Pot for Scam Detection & Intelligence Extraction

> **GUVI Hackathon 2026** - An AI-powered honeypot system that detects scam intent, autonomously engages scammers, and extracts actionable intelligence without revealing detection. Now includes an **Interactive UI** for real-time testing and intelligence monitoring!

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green.svg)](https://fastapi.tiangolo.com)
[![Pydantic](https://img.shields.io/badge/Pydantic-V2-blue.svg)](https://docs.pydantic.dev)
[![OpenRouter](https://img.shields.io/badge/OpenRouter-Gemini%202.0-orange.svg)](https://openrouter.ai)
[![Groq](https://img.shields.io/badge/Groq-Llama%203.3-red.svg)](https://groq.com)
[![Deployed](https://img.shields.io/badge/Deployed-Render-purple.svg)](https://agentic-honey-pot-for-scam-detection-iiv4.onrender.com)

## 🎯 Problem Statement

Online scams (bank fraud, UPI fraud, phishing, fake offers) are becoming increasingly adaptive. Scammers change tactics based on user responses, making traditional detection ineffective. This system uses an **Agentic Honey-Pot** approach - an AI-powered system that detects scam intent and autonomously engages scammers to extract intelligence without revealing detection.

## 🚀 Live Deployment

### API Endpoint
- **Honeypot API**: `https://agentic-honey-pot-for-scam-detection-iiv4.onrender.com/honeypot`
- **API Key**: `team_recursives`
- **Health Check**: `https://agentic-honey-pot-for-scam-detection-iiv4.onrender.com/health`
- **Repository**: [GitHub - SG2407/Agentic-Honey-Pot](https://github.com/SG2407/Agentic-Honey-Pot-for-Scam-Detection-Intelligence-Extraction)

### 🎨 Interactive UI (Local Development)
**Test the system locally** and watch intelligence extraction in real-time:
- **Run Locally**: `cd ui && streamlit run streamlit_app.py`
- **Access**: `http://localhost:8501`
- **Features**: Real-time chat, session management, intelligence monitoring dashboard

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
- **AI-Powered Fallback**: Groq Llama 3.3 70B (70b-versatile) for semantic understanding when hard rules don't match
- **Confidence Scoring**: 0.0-1.0 scale with 0.85 threshold for scam confirmation
- **Scam Type Classification**: Financial threat, credential phishing, prize scam, tech support, etc.

### 🤖 **Autonomous AI Agent**
- **Powered by OpenRouter**: Google Gemini 2.0 Flash (primary), Groq Llama 3.3 70B (fallback)
- **Multi-Persona Engagement**: 
  - Confused Elderly (slow to understand, asks for clarification)
  - Worried Parent (concerned about family, emotional responses)
  - Busy Professional (distracted, provides info in fragments)
- **Enhanced Human-like Responses**: Frequency penalty (0.6), presence penalty (0.4), nucleus sampling (Top-P: 0.92)
- **Context-Aware**: Uses full conversation history for natural flow
- **Never Reveals Detection**: Maintains believable persona throughout

### 📊 **Intelligence Extraction**
Automatically extracts and tracks from entire conversation history:
- 🏦 Bank Account Numbers (regex patterns for various formats)
- 💳 UPI IDs (e.g., scammer@upi, scammer@paytm)
- 📞 Phone Numbers (international format, +91-XXXXXXXXXX)
- 🔗 Phishing Links (malicious URLs with suspicious TLDs)
- ✉️ Email Addresses (scammer@domain.com)
- 🔑 Suspicious Keywords (26+ patterns: urgent, verify, OTP, blocked, click here, etc.)

### ⏱️ **Smart Session Management**
- **In-Memory Session Store**: Tracks active sessions, callback status, and last message timestamps
- **Intelligence-Based Callbacks**: Sends final report to GUVI when non-empty intelligence extracted
- **Session Tracking**: Prevents duplicate callbacks for closed sessions
- **Conversation Limits**: Max 12 turns per conversation for optimal engagement

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
├── app/                             # Core honeypot system
│   ├── main.py                      # FastAPI app & /honeypot endpoint
│   ├── models.py                    # Pydantic V2 models (robust validation)
│   ├── scam_detector.py             # Hybrid detection (regex + AI)
│   ├── conversation_agent.py        # Multi-persona AI agent
│   ├── intelligence_extractor.py    # Extract bank/UPI/phone/links/emails
│   ├── callback_service.py          # GUVI callback integration
│   └── llm_provider.py              # OpenRouter + Groq providers
├── config/                          # Configuration
│   └── settings.py                  # Environment settings
├── ui/                              # 🎨 Interactive UI (Local Development)
│   ├── streamlit_app.py             # Streamlit chat interface
│   ├── ui_backend.py                # FastAPI UI backend service
│   ├── session_store.py             # SQLite session management
│   ├── intelligence_monitor.py      # Real-time intelligence extraction
│   ├── requirements_ui.txt          # UI dependencies
│   ├── start_ui.sh / .bat           # Startup scripts
│   └── Dockerfile                   # Container configuration
├── .env                             # Environment variables
├── .env.example                     # Environment template
├── requirements.txt                 # Main app dependencies
├── render.yaml                      # Render deployment config
├── Procfile                         # Process configuration  
├── docker-compose.yml               # Docker multi-service setup
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
- OpenRouter API Key (primary, from [openrouter.ai](https://openrouter.ai))
- Groq API Key (fallback, from [console.groq.com](https://console.groq.com))

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

# OpenRouter Configuration (Primary - for conversations)
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_CONVERSATION_MODEL=google/gemini-2.0-flash-exp:free

# Groq Configuration (Fallback - for scam detection)
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile

# GUVI Integration
GUVI_CALLBACK_URL=https://hackathon.guvi.in/api/updateHoneyPotFinalResult

# Conversation Settings
MAX_CONVERSATION_TURNS=12
MAX_TOKENS_PER_REPLY=120
CONVERSATION_TEMPERATURE=0.85
SCAM_CONFIDENCE_THRESHOLD=0.85

# LLM Enhancement (Human-like responses)
LLM_FREQUENCY_PENALTY=0.6
LLM_PRESENCE_PENALTY=0.4
LLM_TOP_P=0.92

# Environment
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### 3. Run Locally

#### Start Main Honeypot API
```bash
# Start main honeypot server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Server will be available at http://localhost:8000
# Health check: http://localhost:8000/health
# API endpoint: http://localhost:8000/honeypot
```

#### Start UI (Optional - for local testing)
```bash
# Navigate to UI directory
cd ui

# Option 1: Start both services using scripts
./start_ui.sh  # macOS/Linux
start_ui.bat   # Windows

# Option 2: Start services manually
# Terminal 1: Start UI backend
cd ui && python ui_backend.py

# Terminal 2: Start Streamlit
cd ui && streamlit run streamlit_app.py

# Access UI at: http://localhost:8501
```

**Note**: UI is for local development and testing. Production deployment uses the main API only.

## 🌐 Deployment

### Main Honeypot API (Render)
Deployed on Render's free tier:

**Deployment Configuration:**
- **Service Type**: Web Service
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Branch**: `main`
- **Auto-Deploy**: Enabled

**Required Environment Variables on Render:**
```env
API_KEY=team_recursives
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_CONVERSATION_MODEL=google/gemini-2.0-flash-exp:free
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile
GUVI_CALLBACK_URL=https://hackathon.guvi.in/api/updateHoneyPotFinalResult
MAX_CONVERSATION_TURNS=12
MAX_TOKENS_PER_REPLY=120
CONVERSATION_TEMPERATURE=0.85
SCAM_CONFIDENCE_THRESHOLD=0.85
LLM_FREQUENCY_PENALTY=0.6
LLM_PRESENCE_PENALTY=0.4
LLM_TOP_P=0.92
ENVIRONMENT=production
LOG_LEVEL=INFO
```

**Deployment Steps:**
1. Fork/clone repository to GitHub
2. Create new Web Service on [Render](https://render.com)
3. Connect your GitHub repository
4. Configure environment variables above
5. Deploy!

### Interactive UI (Local Only)
The Streamlit UI is designed for local development and testing:
- Run locally using instructions in "Quick Start" section
- Not deployed separately (use main API endpoint for production)
- Useful for demonstrating the system and testing conversations

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
- **Hard Rules Check**: 26+ regex patterns for urgent, verify, OTP, blocked, phishing URLs
- **AI Analysis**: If hard rules don't trigger, Groq Llama 3.3 70B analyzes semantically
- **Threshold**: 0.85 confidence required to activate honeypot engagement
- **Result**: `is_scam`, `confidence` (0.0-1.0), `scam_type`, `reasoning`

### 3. **Session Management**
- **In-Memory Store**: Tracks active sessions and callback status
- **Non-Scam**: Neutral acknowledgment, session stays open
- **Scam Detected**: Engage with AI agent, track conversation turns (max 12)

### 4. **Intelligence Extraction**
- **Comprehensive Scan**: Analyzes current message + entire conversation history
- **Parallel Processing**: Uses asyncio for fast extraction
- **Extracts**: Bank accounts, UPI IDs, phone numbers, phishing links, email addresses, suspicious keywords
- **Format**: All 6 fields always present in response (empty arrays if nothing found)

### 5. **Callback Decision**
Send callback to GUVI when:
- ✅ Real intelligence extracted (non-empty bank/UPI/phone/link/email data found)
- ✅ Prevents duplicate callbacks using session tracking

### 6. **AI Response Generation**
- **Primary**: OpenRouter with Google Gemini 2.0 Flash for natural conversations
- **Fallback**: Groq Llama 3.3 70B if OpenRouter unavailable
- **Enhanced Parameters**: Frequency/presence penalties and nucleus sampling for human-like variety
- **Multi-Persona**: Randomly selects from confused elderly, worried parent, or busy professional
- **Always 200 OK**: Never returns HTTP errors, maintains conversation flow

## 🧪 Testing

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

```

## 🛠️ Technical Details

### Key Technologies

#### Backend Framework
- **FastAPI 0.104.1**: Modern async web framework with OpenAPI documentation
- **Uvicorn 0.24.0**: ASGI server for production deployment
- **Pydantic V2 (>=2.5.0)**: Robust data validation with `model_dump()`, `ConfigDict`, `Field`
- **Python 3.11+**: Latest async/await features

#### AI/LLM Providers
- **OpenRouter API**: Primary provider for conversation generation
  - Model: Google Gemini 2.0 Flash (free, fast, reliable)
  - Used for: Multi-persona honeypot responses
- **Groq API**: Fallback provider for scam detection
  - Model: Llama 3.3 70B Versatile
  - Used for: Semantic scam analysis when hard rules don't match
- **openai >=1.0.0**: Client library (compatible with both providers)
- **groq >=0.4.1**: Official Groq SDK

#### Data Processing
- **regex 2023.10.3**: Advanced pattern matching for intelligence extraction
- **httpx 0.25.2**: Async HTTP client for GUVI callbacks
- **requests 2.31.0**: Sync HTTP client for compatibility
- **aiofiles 23.2.1**: Async file I/O operations

#### UI Components (Local Development)
- **Streamlit 1.31.0**: Interactive web UI for testing
- **SQLite**: Lightweight session storage (sessions.db)
- **python-json-logger 2.0.7**: Structured logging

#### Configuration & Environment
- **python-dotenv 1.0.0**: Environment variable management
- **Settings**: Centralized config in `config/settings.py`

#### Deployment
- **Render**: Main honeypot API (free tier)
- **Procfile**: Process configuration for Render
- **Docker**: Multi-service setup with docker-compose.yml

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
| `OPENROUTER_API_KEY` | *Required* | OpenRouter API key (primary) |
| `OPENROUTER_CONVERSATION_MODEL` | `google/gemini-2.0-flash-exp:free` | Conversation model |
| `GROQ_API_KEY` | *Required* | Groq API key (fallback) |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Scam detection model |
| `GUVI_CALLBACK_URL` | GUVI endpoint | Final result callback URL |
| `MAX_CONVERSATION_TURNS` | `12` | Maximum conversation turns |
| `MAX_TOKENS_PER_REPLY` | `120` | Max tokens per AI response |
| `CONVERSATION_TEMPERATURE` | `0.85` | AI creativity (0.0-1.0) |
| `SCAM_CONFIDENCE_THRESHOLD` | `0.85` | Scam detection threshold |
| `LLM_FREQUENCY_PENALTY` | `0.6` | Reduce repetition (0.0-2.0) |
| `LLM_PRESENCE_PENALTY` | `0.4` | Encourage diversity (0.0-2.0) |
| `LLM_TOP_P` | `0.92` | Nucleus sampling (0.0-1.0) |
| `ENVIRONMENT` | `development` | Environment mode |
| `LOG_LEVEL` | `INFO` | Logging level |

#### UI Configuration (Local Only)

**Local Development** (ui/.env.ui):
```env
HONEYPOT_API_URL=http://localhost:8000
API_KEY=team_recursives
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
    "emailAddresses": ["scammer@fake.com"],
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
4. Test manually with curl command (see Testing section)

#### INVALID_REQUEST_BODY Error?
- ✅ Robust validation: All 6 intelligence fields always present
- ✅ conversationHistory optional with `Field(default_factory=list)`
- ✅ Timestamp handles Unix ms, ISO-8601, numeric strings
- ✅ Sender normalized (case-insensitive)
- ✅ Metadata fields all optional
- ✅ Extra fields ignored with `extra='ignore'`

#### AI Providers Not Working?
```bash
# Check environment variables
echo $OPENROUTER_API_KEY
echo $GROQ_API_KEY

# Test OpenRouter connection
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"

# Check Render logs for provider errors
```

#### Server Not Responding Locally?
```bash
# Check if port 8000 is in use
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Restart server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Interactive UI (Local Development)

#### UI Not Starting?
1. **Check dependencies**: `pip install -r ui/requirements_ui.txt`
2. **Verify ports**: Ensure 8000 (main API) and 8501 (Streamlit) are not in use
3. **Check configuration**: Verify `ui/.env.ui` or environment variables

#### "Connection Error" in UI?
1. **Ensure main API is running**: `curl http://localhost:8000/health`
2. **Check API key**: Verify `team_recursives` in UI input
3. **Restart both services**: Main API and Streamlit

#### Sessions Not Persisting?
- SQLite database (`ui/sessions.db`) created automatically
- Check file permissions in `ui/` directory
- Database resets when services restart (by design)

## 📝 License

MIT License - See [LICENSE](LICENSE) for details

---

## 🙏 Acknowledgments

- **GUVI & Delhi Hackathon 2026** for the challenge opportunity
- **OpenRouter** for accessible, reliable AI model APIs
- **Groq** for ultra-fast AI inference
- **Google** for Gemini 2.0 Flash model
- **Meta** for Llama 3.3 70B model
- **FastAPI** for excellent async Python framework
- **Streamlit** for rapid UI prototyping
- **Render** for simple, free hosting

---

## 📊 Project Highlights

### What Makes This Special?

✅ **Hybrid AI Approach**: 
- Hard rules (regex) for speed and reliability
- AI fallback (Groq) for semantic understanding
- Primary AI (OpenRouter) for natural conversations

✅ **Advanced AI Techniques**:
- Frequency & presence penalties for less repetition
- Nucleus sampling (Top-P) for varied responses
- Multi-persona engagement for realistic interactions
- Temperature tuning (0.85) for human-like creativity

✅ **Production-Ready**:
- Deployed on Render (free tier)
- Robust Pydantic V2 validation
- Comprehensive error handling
- Flexible timestamp and header parsing

✅ **Comprehensive Intelligence**:
- Extracts 6 types of data (bank, UPI, phone, links, emails, keywords)
- Analyzes entire conversation history
- Async parallel processing for speed

✅ **Developer-Friendly**:
- Clean architecture with separation of concerns
- Environment-based configuration
- Detailed documentation
- Easy local development setup

✅ **Security & Privacy**:
- API key authentication
- No persistent storage of conversation data
- In-memory session management

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

### 🎨 Try It Yourself

Clone the repo and run locally to experience the honeypot in action!

```bash
git clone https://github.com/SG2407/Agentic-Honey-Pot-for-Scam-Detection-Intelligence-Extraction.git
cd Agentic-Honey-Pot-for-Scam-Detection-Intelligence-Extraction
pip install -r requirements.txt
cp .env.example .env  # Add your API keys
uvicorn app.main:app --reload
```

---

**AI Models**: Gemini 2.0 Flash (OpenRouter) • Llama 3.3 70B (Groq)

**Tech Stack**: Python 3.11+ • FastAPI • Pydantic V2 • httpx • Render

**Features**: Hybrid Scam Detection • Multi-Persona AI Agent • 6-Type Intelligence Extraction • GUVI Compliant

</div>