# System Architecture Diagram

## Complete System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE LAYER                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │         Streamlit Chat UI (Port 8501)                       │   │
│  │  ┌──────────────────────────────────────────────────────┐  │   │
│  │  │  • Chat Interface                                     │  │   │
│  │  │  • API Key Input                                      │  │   │
│  │  │  • Session Management                                 │  │   │
│  │  │  • Intelligence Display Panel                         │  │   │
│  │  │    - Bank Accounts                                    │  │   │
│  │  │    - UPI IDs                                          │  │   │
│  │  │    - Phone Numbers                                    │  │   │
│  │  │    - Phishing Links                                   │  │   │
│  │  │    - Suspicious Keywords                              │  │   │
│  │  │  • Scam Detection Alerts                              │  │   │
│  │  │  • Export Functionality                               │  │   │
│  │  └──────────────────────────────────────────────────────┘  │   │
│  └──────────────────────┬───────────────────────────────────────┘   │
│                         │ HTTP Requests                             │
└─────────────────────────┼───────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    UI BACKEND SERVICE LAYER                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │      FastAPI Backend (Port 8001)                            │   │
│  │  ┌──────────────────────────────────────────────────────┐  │   │
│  │  │  REST API Endpoints:                                  │  │   │
│  │  │  • POST /chat           - Send messages               │  │   │
│  │  │  • POST /session/new    - Create session              │  │   │
│  │  │  • GET /session/{id}    - Get session info            │  │   │
│  │  │  • GET /health          - Health check                │  │   │
│  │  └──────────────────────────────────────────────────────┘  │   │
│  │                                                              │   │
│  │  ┌──────────────────────────────────────────────────────┐  │   │
│  │  │  Components:                                          │  │   │
│  │  │  • SessionStore (SQLite)                              │  │   │
│  │  │  • IntelligenceMonitor (Parallel Extraction)          │  │   │
│  │  │  • API Key Validator                                  │  │   │
│  │  │  • HTTP Client                                        │  │   │
│  │  └──────────────────────────────────────────────────────┘  │   │
│  └──────────────────────┬───────────────────────────────────────┘   │
│                         │                                           │
│  ┌──────────────────────▼───────────────────────────────────────┐  │
│  │      SQLite Database (sessions.db)                           │  │
│  │  • sessions table     - Session metadata                     │  │
│  │  • messages table     - Conversation history                 │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                         │ HTTP POST /honeypot                       │
└─────────────────────────┼───────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   EXISTING HONEYPOT SYSTEM                           │
│                        (NO CHANGES)                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│    https://agentic-honey-pot-for-scam-detection-iiv4.onrender.com  │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │  FastAPI Honeypot Application                               │   │
│  │  ┌──────────────────────────────────────────────────────┐  │   │
│  │  │  • POST /honeypot       - Main endpoint               │  │   │
│  │  │  • GET /health          - Health check                │  │   │
│  │  └──────────────────────────────────────────────────────┘  │   │
│  │                                                              │   │
│  │  ┌──────────────────────────────────────────────────────┐  │   │
│  │  │  Core Components:                                     │  │   │
│  │  │  • ScamDetector         - Pattern + AI detection      │  │   │
│  │  │  • ConversationAgent    - LLM-powered responses       │  │   │
│  │  │  • IntelligenceExtractor - Data extraction            │  │   │
│  │  │  • CallbackService      - GUVI integration            │  │   │
│  │  └──────────────────────────────────────────────────────┘  │   │
│  └──────────────────────┬───────────────────────────────────────┘   │
│                         │                                           │
│                         ▼                                           │
│              ┌──────────────────────┐                               │
│              │   GUVI Callback      │                               │
│              │   (Still works! ✅)  │                               │
│              └──────────────────────┘                               │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
User Action: "Send Message"
     │
     ▼
[1] Streamlit UI validates API key
     │
     ▼
[2] POST /chat to UI Backend
     │
     ├─── [3a] Store message in SQLite
     │
     └─── [3b] POST /honeypot to Main App
              │
              ▼
         [4] Main App processes:
              ├─ Detect scam
              ├─ Generate agent reply
              ├─ Extract intelligence
              └─ Send callback to GUVI ✅
              │
              ▼
         [5] Response received
              │
     ┌────────┴────────┐
     │                 │
     ▼                 ▼
[6a] UI Backend    [6b] Main App
  extracts           continues normal
  intelligence       operation
  for UI display     (unchanged)
     │
     ▼
[7] Store in SQLite
     │
     ▼
[8] Return to Streamlit
     │
     ▼
[9] Display in UI:
    - Agent reply
    - Intelligence
    - Scam alerts
```

## Deployment Architecture

### Local Development
```
┌─────────────────────┐
│   Your Computer     │
├─────────────────────┤
│ Port 8501: Streamlit│
│ Port 8001: UI Back  │
└──────────┬──────────┘
           │
           ▼
    ┌──────────────┐
    │   Internet   │
    └──────┬───────┘
           │
           ▼
┌──────────────────────┐
│   Render Cloud       │
├──────────────────────┤
│ Main Honeypot App    │
│ (Unchanged)          │
└──────────────────────┘
```

### Cloud Deployment
```
┌──────────────────────┐
│  Streamlit Cloud     │
├──────────────────────┤
│ Streamlit UI         │
│ (Public Access)      │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Render/Railway      │
├──────────────────────┤
│ UI Backend           │
│ + SQLite DB          │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Render Cloud        │
├──────────────────────┤
│ Main Honeypot App    │
│ (Unchanged)          │
└──────────────────────┘
```

## Component Interaction Matrix

| Component | Calls | Called By | Database | Purpose |
|-----------|-------|-----------|----------|---------|
| Streamlit UI | UI Backend | User | None | Display interface |
| UI Backend | Main Honeypot | Streamlit UI | SQLite | API middleware |
| Session Store | None | UI Backend | SQLite | Data persistence |
| Intelligence Monitor | None | UI Backend | None | Extract intel for UI |
| Main Honeypot | GUVI Callback | UI Backend, External | In-memory | Process scams |

## Security Architecture

```
┌──────────────────────────────────────────────────┐
│              Security Layers                      │
├──────────────────────────────────────────────────┤
│                                                   │
│  Layer 1: API Key Validation                     │
│  ┌────────────────────────────────────────────┐ │
│  │ • Streamlit: Check API key on connect      │ │
│  │ • UI Backend: Validate every request       │ │
│  │ • Main App: Independent validation         │ │
│  └────────────────────────────────────────────┘ │
│                                                   │
│  Layer 2: Session Isolation                      │
│  ┌────────────────────────────────────────────┐ │
│  │ • Each session has unique ID               │ │
│  │ • No cross-session data leakage            │ │
│  │ • SQLite provides ACID guarantees          │ │
│  └────────────────────────────────────────────┘ │
│                                                   │
│  Layer 3: HTTPS/TLS (Production)                 │
│  ┌────────────────────────────────────────────┐ │
│  │ • Streamlit Cloud: Auto HTTPS              │ │
│  │ • Render: Auto HTTPS                       │ │
│  │ • All traffic encrypted                    │ │
│  └────────────────────────────────────────────┘ │
│                                                   │
│  Layer 4: CORS Protection                        │
│  ┌────────────────────────────────────────────┐ │
│  │ • UI Backend: Configured CORS              │ │
│  │ • Main App: Configured CORS                │ │
│  └────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────┘
```

## File System Structure

```
Delhi_Hackathon/
│
├── app/                           # Existing (UNCHANGED)
│   ├── main.py                    # ✓ Untouched
│   ├── models.py                  # ✓ Untouched
│   ├── scam_detector.py           # ✓ Untouched
│   └── ...                        # ✓ Untouched
│
├── ui/                            # NEW DIRECTORY
│   ├── streamlit_app.py           # ★ Streamlit frontend
│   ├── ui_backend.py              # ★ FastAPI backend
│   ├── session_store.py           # ★ SQLite handler
│   ├── intelligence_monitor.py    # ★ Intel extractor
│   ├── requirements_ui.txt        # ★ Dependencies
│   ├── .env.ui                    # ★ Configuration
│   ├── Dockerfile                 # ★ Container image
│   ├── start_ui.sh                # ★ Unix launcher
│   ├── start_ui.bat               # ★ Windows launcher
│   ├── test_ui_components.py      # ★ Test suite
│   ├── README_UI.md               # ★ Documentation
│   ├── .gitignore                 # ★ Git rules
│   └── .streamlit/
│       └── config.toml            # ★ Streamlit config
│
├── docker-compose.yml             # ★ Container orchestration
├── UI_QUICKSTART.md               # ★ Quick start guide
├── UI_IMPLEMENTATION_SUMMARY.md   # ★ Implementation summary
└── ARCHITECTURE.md                # ★ This file
```

## Network Ports

| Service | Port | Protocol | Access |
|---------|------|----------|--------|
| Streamlit UI | 8501 | HTTP | Public |
| UI Backend | 8001 | HTTP | Internal |
| Main Honeypot | 8000 | HTTP | Remote (Render) |
| SQLite DB | - | File | Local |

## Technology Stack

```
┌─────────────────────────────────────────────┐
│           Technology Stack                   │
├─────────────────────────────────────────────┤
│                                              │
│  Frontend Layer                              │
│  • Streamlit 1.31.0                         │
│  • HTML/CSS (via Streamlit)                 │
│  • JavaScript (via Streamlit)               │
│                                              │
│  Backend Layer                               │
│  • FastAPI 0.104.1                          │
│  • Uvicorn 0.24.0 (ASGI server)            │
│  • Pydantic 2.5+ (validation)              │
│                                              │
│  Database Layer                              │
│  • SQLite 3 (embedded)                      │
│                                              │
│  HTTP Client Layer                           │
│  • httpx 0.25.2 (async)                    │
│  • requests 2.31.0 (sync)                  │
│                                              │
│  Configuration                               │
│  • python-dotenv 1.0.0                     │
│                                              │
│  Deployment                                  │
│  • Docker (containerization)                │
│  • Streamlit Cloud (UI hosting)            │
│  • Render/Railway (backend hosting)        │
│                                              │
└─────────────────────────────────────────────┘
```

---

**Note**: This architecture maintains complete separation between the UI system and the existing honeypot, ensuring zero interference with production functionality while providing a rich demonstration interface.
