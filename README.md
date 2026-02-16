# 🕷️ Agentic Honey-Pot for Scam Detection & Intelligence Extraction

> **GUVI Delhi Hackathon 2026** - An AI-powered honeypot system that detects scam intent, autonomously engages scammers, and extracts actionable intelligence without revealing detection.

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green.svg)](https://fastapi.tiangolo.com)
[![Pydantic](https://img.shields.io/badge/Pydantic-V2-blue.svg)](https://docs.pydantic.dev)
[![Groq](https://img.shields.io/badge/Groq-Llama%203.3%2070B-red.svg)](https://groq.com)
[![Deployed](https://img.shields.io/badge/Deployed-Render-purple.svg)](https://agentic-honey-pot-for-scam-detection-iiv4.onrender.com)

## 🎯 Problem Statement

Online scams (bank fraud, UPI fraud, phishing, fake offers) are becoming increasingly adaptive. Scammers change tactics based on user responses, making traditional detection ineffective. This system employs an **Agentic Honey-Pot** approach - an AI-powered system that detects scam intent and autonomously engages scammers to extract intelligence without revealing detection.

## 🚀 Live Deployment

### API Endpoint
- **Honeypot API**: `https://agentic-honey-pot-for-scam-detection-iiv4.onrender.com/honeypot`
- **API Key**: `team_recursives`
- **Health Check**: `https://agentic-honey-pot-for-scam-detection-iiv4.onrender.com/health`
- **Repository**: [GitHub Repository](https://github.com/SG2407/Agentic-Honey-Pot-for-Scam-Detection-Intelligence-Extraction)

## ✨ Core Features

### 🔍 **Hybrid Scam Detection**
- **Hard Rules First**: Regex patterns for 20+ scam indicators (urgent, verify, OTP, blocked, suspicious URLs)
- **AI-Powered Fallback**: Groq Llama 3.3 70B for semantic understanding when hard rules don't trigger
- **Confidence Scoring**: 0.0-1.0 scale with configurable threshold (default 0.7)
- **Scam Type Classification**: Financial threat, credential phishing, prize scam, impersonation, reward scam

### 🤖 **Autonomous AI Agent**
- **Multi-Provider Architecture**: OpenRouter (primary) and Groq (fallback) with automatic failover
- **Supported Models**: Google Gemini 2.0 Flash, Llama 3.3 70B, GPT-4o-mini
- **Multi-Persona Engagement**: 
  - Worried Customer (concerned, anxious, asks clarifying questions)
  - Excited Winner (eager about prizes, cautiously optimistic)
  - Confused Elderly (needs step-by-step help, trusting)
  - Cautious User (skeptical, demands verification)
- **Enhanced Human-like Responses**: Frequency penalty, presence penalty, nucleus sampling (Top-P)
- **Context-Aware**: Uses conversation history for natural, progressive engagement
- **Persona Selection**: Automatically matches persona to detected scam type
- **Never Reveals Detection**: Maintains believable persona throughout

### 📊 **Intelligence Extraction**
Automatically extracts and tracks from entire conversation history:
- 🏦 **Bank Account Numbers** - Various formats using regex patterns
- 💳 **UPI IDs** - e.g., scammer@upi, scammer@paytm
- 📞 **Phone Numbers** - International format (+91-XXXXXXXXXX)
- 🔗 **Phishing Links** - Malicious URLs with suspicious TLDs
- ✉️ **Email Addresses** - scammer@domain.com patterns
- 🔑 **Suspicious Keywords** - 26+ patterns (urgent, verify, OTP, blocked, click here, etc.)

### ⏱️ **Smart Session Management**
- **In-Memory Session Store**: Tracks active sessions, callback status, and message timestamps
- **Intelligence-Based Callbacks**: Sends final report to GUVI when actionable intelligence is extracted
- **Session Tracking**: Prevents duplicate callbacks for closed sessions
- **Conversation Limits**: Configurable max turns per conversation (default: 20 turns)

### 🎯 **GUVI Scoring System** (45-Point Intelligence Scoring)
**Dual Callback Trigger**: Sends callback when **EITHER** condition is met:
1. ✅ **Intelligence Score ≥ 80%** (36+ points out of 45) - High-value data extracted
2. ✅ **Message Limit Reached** (20 turns default) - Maximum conversation length

**Scoring Breakdown** (45 points maximum):
- 📞 **Phone Numbers**: 10 points (highest priority - contact tracing)
- 🏦 **Bank Account Numbers**: 10 points (financial fraud evidence)
- 💳 **UPI IDs**: 10 points (payment fraud tracking)
- 🔗 **Phishing Links**: 10 points (malicious infrastructure)
- 📧 **Email Addresses**: 5 points (secondary contact method)

**Strategic Extraction Features**:
- ⚡ **Early-turn questioning** (turns 2-4): Aggressively asks for contact details
- 🎭 **Context-aware prompts**: AI explicitly guided to extract 5 intelligence types
- 🔄 **Link re-request strategies**: Asks scammer to resend unclear/broken links
- 🧠 **Adaptive questioning**: Identifies missing high-value data and prompts accordingly

**Example Score Calculation**:
```
Scenario: Bank fraud scam
Extracted: +91-9876543210 (phone), 1234567890123456 (bank), scammer@upi (UPI)
Score: 10 + 10 + 10 = 30/45 points (67%)
Result: Below 80% threshold → Continues conversation to extract more
```

### 🛡️ **Robust Input Handling**
- ✅ Flexible timestamp parsing (Unix milliseconds, ISO-8601, numeric strings)
- ✅ Optional fields (conversationHistory, metadata)
- ✅ Case-insensitive sender normalization ("Scammer" → "scammer")
- ✅ Extra field tolerance (`extra='ignore'` in Pydantic models)
- ✅ Multiple API key header support (x-api-key, X-API-KEY, Authorization)

## 🏗️ System Architecture

```
┌─────────────────┐
│  GUVI Platform  │◄──────────────────────────────────────────┐
└────────┬────────┘                                           │
         │ POST /honeypot                                     │
         ▼                                                    │
┌─────────────────────────────────────────────────┐          │
│           FastAPI Server (main.py)              │          │
│  • API key verification (flexible headers)      │          │
│  • Pydantic V2 validation (robust)              │          │
│  • Request logging                              │          │
└────────┬────────────────────────────────────────┘          │
         │                                                    │
         ▼                                                    │
┌─────────────────────────────────────────────────┐          │
│        Scam Detector (scam_detector.py)         │          │
│  1. Hard rules check (regex patterns)           │          │
│  2. AI fallback (Groq Llama 3.3 70B)            │          │
│  → Returns: is_scam, confidence, type           │          │
└────────┬────────────────────────────────────────┘          │
         │                                                    │
         ├─────────────────┬──────────────────────┐          │
         │                 │                      │          │
    [Non-Scam]        [Scam Detected]            │          │
         │                 │                      │          │
         ▼                 ▼                      ▼          │
  ┌──────────┐    ┌────────────────┐    ┌────────────────┐  │
  │ Neutral  │    │ Conversation   │    │ Intelligence   │  │
  │ Response │    │ Agent (AI)     │    │ Extractor      │  │
  │          │    │ Multi-persona  │    │                │  │
  └──────────┘    └────────┬───────┘    └────────┬───────┘  │
         │                 │                      │          │
         │                 │                      │          │
         │                 ▼                      │          │
         │        ┌─────────────────────────┐    │          │
         │        │   LLM Manager           │    │          │
         │        │   • OpenRouter          │    │          │
         │        │   • Groq Fallback       │    │          │
         │        └─────────────────────────┘    │          │
         │                 │                      │          │
         │                 │    [Intel Found]     │          │
         │                 │         │            │          │
         │                 ▼         ▼            ▼          │
         │        ┌──────────────────────────────────┐       │
         │        │   Callback Service               │───────┘
         │        │   POST to GUVI                   │
         │        │   • sessionId                    │
         │        │   • scamDetected                 │
         │        │   • totalMessagesExchanged       │
         │        │   • extractedIntelligence        │
         │        │   • agentNotes                   │
         │        └──────────────────────────────────┘
         │                 │
         ▼                 ▼
  ┌──────────────────────────────┐
  │  Return 200 OK with reply    │
  └───────────────────────────────┘
```

## 📁 Project Structure

```
Delhi_Hackathon/
├── app/                          # Core honeypot system
│   ├── main.py                   # FastAPI server & /honeypot endpoint
│   ├── models.py                 # Pydantic V2 data models
│   ├── scam_detector.py          # Hybrid detection (regex + AI)
│   ├── conversation_agent.py     # Multi-persona AI agent
│   ├── intelligence_extractor.py # Intelligence extraction logic
│   ├── callback_service.py       # GUVI callback integration
│   └── llm_provider.py           # Multi-provider LLM manager
├── config/
│   └── settings.py               # Environment configuration
├── ui/                           # Optional: Local testing UI
│   ├── streamlit_app.py          # Streamlit interface
│   ├── ui_backend.py             # UI backend service
│   ├── session_store.py          # Session management
│   ├── intelligence_monitor.py   # Intelligence display
│   ├── requirements_ui.txt       # UI dependencies
│   └── Dockerfile                # UI container config
├── .env                          # Environment variables (not in repo)
├── .env.example                  # Environment template
├── requirements.txt              # Main dependencies
├── runtime.txt                   # Python version
├── Procfile                      # Render deployment config
├── docker-compose.yml            # Docker orchestration
└── README.md                     # Documentation
```

## 🚀 Quick Start & Comprehensive Setup Guide

### Prerequisites

**Required:**
- **Python 3.11** (exact version for compatibility)
  - Check: `python --version` should show `3.11.x`
  - Install: [python.org/downloads](https://www.python.org/downloads/)
- **OpenRouter API Key** (Primary LLM) - [openrouter.ai](https://openrouter.ai)
  - Free tier available
  - Used for: Conversation generation, summarization
- **Groq API Key** (Fallback LLM) - [console.groq.com](https://console.groq.com)
  - Free tier available
  - Used for: Scam detection, pattern matching

**Optional:**
- **Docker & Docker Compose** (for containerized deployment)
- **Git** (for version control)

### Step-by-Step Installation

#### 1. Clone Repository

```bash
git clone https://github.com/SG2407/Agentic-Honey-Pot-for-Scam-Detection-Intelligence-Extraction.git
cd Agentic-Honey-Pot-for-Scam-Detection-Intelligence-Extraction
```

#### 2. Create Virtual Environment

**macOS/Linux:**
```bash
python3.11 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Verify activation:** Your prompt should show `(venv)` prefix

#### 3. Install Dependencies

```bash
pip install --upgrade pip  # Ensure pip is up to date
pip install -r requirements.txt
```

**Verify installation:**
```bash
python -c "import fastapi; print('FastAPI:', fastapi.__version__)"
# Should print: FastAPI: 0.104.1
```

#### 4. Configure Environment Variables

**Create `.env` file:**
```bash
cp .env.example .env
nano .env  # or use your preferred editor
```

**Essential Configuration:**
```env
# API Configuration
API_KEY=team_recursives

# OpenRouter (Primary - Conversation generation)
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_CONVERSATION_MODEL=google/gemini-2.0-flash-exp:free

# Groq (Fallback - Scam detection)
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile

# GUVI Integration
GUVI_CALLBACK_URL=https://hackathon.guvi.in/api/updateHoneyPotFinalResult

# Conversation Settings
MAX_CONVERSATION_TURNS=20
SCAM_CONFIDENCE_THRESHOLD=0.7

# LLM Enhancement Parameters
LLM_FREQUENCY_PENALTY=0.3
LLM_PRESENCE_PENALTY=0.2
LLM_TOP_P=0.95

# Application Settings
ENVIRONMENT=development
LOG_LEVEL=INFO
```

#### 5. Validate API Keys

**Test OpenRouter:**
```bash
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer YOUR_OPENROUTER_API_KEY"
```
Expected: JSON list of available models

**Test Groq:**
```bash
curl https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer YOUR_GROQ_API_KEY"
```
Expected: JSON list of Groq models

#### 6. Run Application

**Start FastAPI server:**
```bash
# Start the honeypot API
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Server available at http://localhost:8000
# Health check: http://localhost:8000/health
# API endpoint: http://localhost:8000/honeypot
```

**Expected startup logs:**
```
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

#### 7. Test the API

**Health check:**
```bash
curl http://localhost:8000/health
```
Expected response: `{"status": "healthy"}`

**Test honeypot endpoint:**
```bash
curl -X POST http://localhost:8000/honeypot \
  -H "Content-Type: application/json" \
  -H "x-api-key: team_recursives" \
  -d '{
    "sessionId": "test-session-123",
    "message": {
      "sender": "scammer",
      "text": "Your bank account has been blocked! Share your OTP immediately.",
      "timestamp": 1708070400000
    }
  }'
```

**Expected response:**
```json
{
  "status": "success",
  "reply": "oh no really? which account? i have two accounts"
}
```

#### 8. Verify Intelligence Extraction

Check server logs for intelligence extraction:
```
✓ Scam detected: credential_phishing (confidence: 1.0)
✓ Found suspicious pattern: 'share.*otp'
📞 Phone numbers: []
🏦 Bank accounts: []
💳 UPI IDs: []
🔗 Phishing links: []
🎯 GUVI Score: 0/45 points (0%)
ℹ️  Continuing engagement to gather more intelligence...
```

### Optional: Test with UI

```bash
# In a separate terminal, start UI backend
python ui/ui_backend.py

# In another terminal, start Streamlit
cd ui && streamlit run streamlit_app.py

# Access UI at http://localhost:8501
```

## 🌐 Deployment on Render

The system is deployed on Render's free tier.

### Deployment Configuration

- **Service Type**: Web Service
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Branch**: `main`
- **Auto-Deploy**: Enabled

### Required Environment Variables

```env
API_KEY=team_recursives
OPENROUTER_API_KEY=<your_key>
OPENROUTER_CONVERSATION_MODEL=google/gemini-2.0-flash-exp:free
GROQ_API_KEY=<your_key>
GROQ_MODEL=llama-3.3-70b-versatile
GUVI_CALLBACK_URL=https://hackathon.guvi.in/api/updateHoneyPotFinalResult
MAX_CONVERSATION_TURNS=20
SCAM_CONFIDENCE_THRESHOLD=0.7
LLM_FREQUENCY_PENALTY=0.3
LLM_PRESENCE_PENALTY=0.2
LLM_TOP_P=0.95
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### Deployment Steps

1. Fork/clone repository to GitHub
2. Create new Web Service on [Render](https://render.com)
3. Connect GitHub repository
4. Configure environment variables
5. Deploy

## 📡 API Reference

### Authentication

All API requests require an API key in the header:

```http
x-api-key: team_recursives
Content-Type: application/json
```

### POST `/honeypot`

Main endpoint for processing scam messages.

**Request Body:**
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
}
```

**Response:**
```json
{
  "status": "success",
  "reply": "Why will my account be blocked? Which account exactly?"
}
```

### GET `/health`

Health check endpoint.

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

### 1. Message Reception
- GUVI platform sends POST request to `/honeypot` endpoint
- FastAPI validates request with Pydantic V2 models
- System logs request for debugging

### 2. Scam Detection
- **Primary**: Regex-based hard rules check (20+ patterns)
- **Fallback**: AI semantic analysis using Groq Llama 3.3 70B
- **Output**: `is_scam`, `confidence` (0.0-1.0), `scam_type`, `reasoning`

### 3. Session Management
- In-memory store tracks active sessions and callback status
- **Non-Scam**: Returns neutral acknowledgment
- **Scam Detected**: Activates conversational agent

### 4. Intelligence Extraction
- Scans current message and full conversation history
- Extracts: bank accounts, UPI IDs, phone numbers, phishing links, emails, keywords
- Uses async processing for performance

### 5. Callback Trigger
Sends callback to GUVI when:
- Actionable intelligence is extracted (non-empty fields)
- Session closes after max turns or intelligence found
- Prevents duplicate callbacks per session

### 6. AI Response Generation
- **Primary Provider**: OpenRouter (Google Gemini 2.0 Flash, GPT-4o-mini)
- **Fallback Provider**: Groq (Llama 3.3 70B)
- **Enhancement**: Frequency/presence penalties, nucleus sampling
- **Persona**: Selected based on scam type
- **Always Returns 200 OK**: Maintains conversation flow

## 🧪 Testing

Test the API using curl:

```bash
curl -X POST "https://agentic-honey-pot-for-scam-detection-iiv4.onrender.com/honeypot" \
  -H "x-api-key: team_recursives" \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "test-session-001",
    "message": {
      "sender": "scammer",
      "text": "Your account will be blocked. Click here to verify: http://fake-bank.com",
      "timestamp": "2026-02-16T10:00:00Z"
    },
    "conversationHistory": []
  }'
```

Expected response:
- Scam detected
- AI-generated natural response
- Session activated for intelligence gathering

## 🛠️ Technical Details

### Core Technologies

**Backend Framework:**
- **FastAPI 0.104.1**: Async web framework with automatic API documentation
- **Uvicorn 0.24.0**: ASGI server for production deployment
- **Pydantic V2 (>=2.5.0)**: Robust data validation with strict typing
- **Python 3.11**: Latest async/await features

**AI/LLM Providers:**
- **OpenRouter API**: Primary conversation generation provider
  - Model: Google Gemini 2.0 Flash (fast, cost-effective)
  - Fallback: GPT-4o-mini (high quality)
- **Groq API**: Scam detection and fallback provider
  - Model: Llama 3.3 70B Versatile
- **openai >=1.0.0**: OpenAI-compatible client library
- **groq >=0.4.1**: Official Groq SDK

**Data Processing:**
- **regex 2023.10.3**: Pattern matching for intelligence extraction
- **httpx 0.25.2**: Async HTTP client for GUVI callbacks
- **requests 2.31.0**: Sync HTTP client for API calls
- **aiofiles 23.2.1**: Async file I/O

**Configuration:**
- **python-dotenv 1.0.0**: Environment variable management
- **Centralized Settings**: `config/settings.py` module

**Deployment:**
- **Render**: Cloud hosting platform (free tier)
- **Procfile**: Process configuration
- **Docker**: Optional containerized deployment

### Key Features

**Robust Input Handling:**
- Flexible timestamp parsing (Unix ms, ISO-8601, numeric strings)
- Case-insensitive sender normalization
- Optional conversation history and metadata
- Pydantic `extra='ignore'` for forward compatibility
- Multiple API key header support

**Multi-Provider LLM Architecture:**
- Automatic failover between providers
- Configurable models per provider
- Enhanced response parameters (frequency/presence penalties, Top-P sampling)
- Template-based fallback responses

**Session Management:**
- In-memory session tracking
- Callback status monitoring
- Message counting and timeout handling
- Prevents duplicate callbacks

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_KEY` | `team_recursives` | API authentication key |
| `OPENROUTER_API_KEY` | *Required* | OpenRouter API key |
| `OPENROUTER_CONVERSATION_MODEL` | `google/gemini-2.0-flash-exp:free` | Primary conversation model |
| `GROQ_API_KEY` | *Required* | Groq API key |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Scam detection model |
| `GUVI_CALLBACK_URL` | GUVI endpoint | Final result callback URL |
| `MAX_CONVERSATION_TURNS` | `20` | Maximum conversation turns |
| `SCAM_CONFIDENCE_THRESHOLD` | `0.7` | Scam detection threshold (0.0-1.0) |
| `LLM_FREQUENCY_PENALTY` | `0.3` | Reduce repetition (0.0-2.0) |
| `LLM_PRESENCE_PENALTY` | `0.2` | Encourage topic diversity (0.0-2.0) |
| `LLM_TOP_P` | `0.95` | Nucleus sampling (0.0-1.0) |
| `ENVIRONMENT` | `development` | Environment mode |
| `LOG_LEVEL` | `INFO` | Logging level |

## 📊 GUVI Compliance

### ✅ All Requirements Met

- [x] **Detect scam intent** - Hybrid detection (regex + AI)
- [x] **Activate autonomous AI Agent** - Multi-persona conversational agent
- [x] **Maintain believable persona** - Context-aware, human-like responses
- [x] **Handle multi-turn conversations** - Session management with history
- [x] **Extract scam intelligence** - 6 types of data extraction
- [x] **Return structured JSON** - Pydantic-validated responses
- [x] **Secure API access** - API key authentication
- [x] **Send final callback** - GUVI integration with intelligence report

### Callback Payload Format

```json
{
  "sessionId": "unique-session-id",
  "scamDetected": true,
  "totalMessagesExchanged": 5,
  "extractedIntelligence": {
    "bankAccounts": ["1234567890"],
    "upiIds": ["scammer@paytm"],
    "phishingLinks": ["http://fake-bank.com"],
    "phoneNumbers": ["+919876543210"],
    "emailAddresses": ["scammer@fake.com"],
    "suspiciousKeywords": ["urgent", "verify", "blocked", "click here"]
  },
  "agentNotes": "Scammer used urgency tactics and impersonated bank official"
}
```

## 🐛 Comprehensive Troubleshooting Guide

### Installation Issues

**Python Version Mismatch**
```bash
# Check Python version
python --version  # Must be 3.11.x

# If wrong version, install Python 3.11:
# macOS: brew install python@3.11
# Ubuntu: sudo apt-get install python3.11
# Windows: Download from python.org

# Use specific version
python3.11 -m venv venv
```

**Dependency Installation Fails**
```bash
# Update pip first
pip install --upgrade pip setuptools wheel

# Install with verbose output
pip install -r requirements.txt -v

# If specific package fails
pip install pydantic==2.5.0 --force-reinstall
```

### API Issues

**401 Unauthorized**
- Verify API key is set correctly: `team_recursives`
- Check header format: `x-api-key: team_recursives` (case-insensitive)
- Alternative headers: `X-API-KEY`, `Authorization`

**Validation Errors**
- Ensure `sender` field is lowercase: `"scammer"` not `"Scammer"`
- Timestamp must be valid ISO-8601 or Unix milliseconds
- Required fields: `sessionId`, `message.sender`, `message.text`, `message.timestamp`

**Empty Response**
- Session already closed (callback sent) - use new sessionId
- Check server logs for session status

**LLM Provider Errors**
```bash
# Verify OpenRouter (returns model list if OK)
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"

# Verify Groq (returns model list if OK)
curl https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer $GROQ_API_KEY"

# Get new keys:
# OpenRouter: https://openrouter.ai/keys
# Groq: https://console.groq.com/keys
```

### Runtime Issues

**Port Already in Use**
```bash
# macOS/Linux
lsof -i :8000 && kill -9 <PID>

# Windows
netstat -ano | findstr :8000 && taskkill /PID <PID> /F

# Or use different port
uvicorn app.main:app --port 8001
```

**Module Import Errors**
```bash
# Ensure virtual environment is active
which python  # Should show venv/bin/python

# Reinstall
pip install -r requirements.txt --force-reinstall
```

**Intelligence Not Extracting**
- Scammer must explicitly share: phone, UPI, account, links
- Check logs: `📊 Current extraction: Phone=0, Bank=0...`
- Conversation needs 3-5 turns for natural extraction

**Callback Not Sending**
- Score must be ≥ 36/45 points (80%) OR 20 turns reached
- Check: `🎯 GUVI Score: X/45 points`
- Verify GUVI_CALLBACK_URL in .env

**Render Deployment Issues**
- Cold start may take 30-50 seconds on free tier
- Check Render logs for deployment errors
- Verify all environment variables are set

### Local Development Issues

**Port Already in Use**
```bash
# Check what's using port 8000
lsof -i :8000          # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill the process or use different port
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

**Module Import Errors**
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Verify Python version
python --version  # Should be 3.11 or higher
```

## � Project Highlights

### Technical Excellence

✅ **Hybrid AI Approach**: 
- Regex-based hard rules for speed and reliability
- AI fallback for semantic understanding
- Multi-provider architecture for resilience

✅ **Advanced AI Techniques**:
- Frequency & presence penalties for natural responses
- Nucleus sampling (Top-P) for response variety
- Multi-persona engagement for realistic interactions
- Context-aware conversation management

✅ **Production-Ready**:
- Deployed on Render with global accessibility
- Robust Pydantic V2 data validation
- Comprehensive error handling
- Flexible input parsing (timestamps, headers, fields)

✅ **Comprehensive Intelligence Extraction**:
- 6 types of data extraction (bank, UPI, phone, links, emails, keywords)
- Full conversation history analysis
- Async parallel processing

✅ **Clean Architecture**:
- Separation of concerns (detection, extraction, conversation, callback)
- Environment-based configuration
- Modular and testable design

---

## 👥 Team

**Team Recursives**  
Developed for GUVI Delhi Hackathon 2026

---

## 🙏 Acknowledgments

- **GUVI & Delhi Hackathon 2026** - For the challenge opportunity
- **OpenRouter** - For accessible AI model APIs
- **Groq** - For ultra-fast AI inference
- **Google** - For Gemini 2.0 Flash model
- **Meta** - For Llama 3.3 70B model
- **FastAPI** - For excellent async Python framework

---

## 📞 Support

- **GitHub Repository**: [Agentic-Honey-Pot](https://github.com/SG2407/Agentic-Honey-Pot-for-Scam-Detection-Intelligence-Extraction)
- **Issues**: [Report Issues](https://github.com/SG2407/Agentic-Honey-Pot-for-Scam-Detection-Intelligence-Extraction/issues)
- **Hackathon**: [GUVI Delhi Hackathon 2026](https://hackathon.guvi.in)

---

<div align="center">

**🏆 Built for Delhi Hackathon 2026 🏆**

*Protecting people from scams with the power of AI*

**Tech Stack**: Python 3.11 • FastAPI • Pydantic V2 • OpenRouter • Groq • Render

**AI Models**: Gemini 2.0 Flash • Llama 3.3 70B • GPT-4o-mini

</div>