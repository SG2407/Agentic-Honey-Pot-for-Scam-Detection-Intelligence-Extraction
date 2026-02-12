# 🕷️ Honeypot UI - Interactive Demo Interface

> Chat-based UI for demonstrating the Agentic Honey-Pot system. Users can interact as scammers and see real-time intelligence extraction.

## 🎯 Overview

This UI provides a **complete interactive demo** of the honeypot system without modifying any existing code. It consists of:

1. **Streamlit Frontend** - Chat interface for users
2. **FastAPI Backend** - Middleware that calls the main honeypot
3. **SQLite Storage** - Session and message persistence
4. **Intelligence Monitor** - Parallel extraction for UI display

## ✨ Features

- 🔐 **API Key Authentication** - Secure access control
- 💬 **Real-time Chat** - WhatsApp-like interface
- 📊 **Intelligence Display** - Live extraction visualization
- 🚨 **Scam Detection** - Real-time alerts with confidence scores
- 📥 **Export Data** - Download session intelligence as JSON
- 🔄 **Session Management** - Create/delete sessions
- 🎨 **Beautiful UI** - Modern, responsive design

## 🏗️ Architecture

```
┌─────────────────┐
│  Streamlit UI   │ (Port 8501)
│  - Chat UI      │
│  - Intel View   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  UI Backend     │ (Port 8001)
│  - FastAPI      │
│  - Session DB   │
└────────┬────────┘
         │ HTTP Request
         ▼
┌─────────────────┐
│  Main Honeypot  │ (Your existing app)
│  NO CHANGES     │
│  https://...    │
└─────────────────┘
```

## 📦 Installation

### Option 1: Quick Start (Recommended)

#### On macOS/Linux:
```bash
cd ui
chmod +x start_ui.sh
./start_ui.sh
```

#### On Windows:
```cmd
cd ui
start_ui.bat
```

This will:
- Create a virtual environment
- Install dependencies
- Start both UI backend and Streamlit
- Open browser automatically

### Option 2: Manual Setup

1. **Install dependencies:**
```bash
pip install -r ui/requirements_ui.txt
```

2. **Configure environment:**
```bash
cp ui/.env.ui ui/.env
# Edit ui/.env if needed
```

3. **Start UI backend:**
```bash
python -m uvicorn ui.ui_backend:app --host 0.0.0.0 --port 8001
```

4. **Start Streamlit (in another terminal):**
```bash
streamlit run ui/streamlit_app.py --server.port 8501
```

5. **Access UI:**
Open browser to: http://localhost:8501

### Option 3: Docker

#### Using Docker Compose:
```bash
docker-compose up
```

#### Or build manually:
```bash
# Build image
docker build -t honeypot-ui -f ui/Dockerfile .

# Run UI backend
docker run -d -p 8001:8001 --name ui-backend honeypot-ui \
  uvicorn ui.ui_backend:app --host 0.0.0.0 --port 8001

# Run Streamlit
docker run -d -p 8501:8501 --name streamlit-ui honeypot-ui \
  streamlit run ui/streamlit_app.py --server.port 8501
```

## 🚀 Usage

1. **Enter API Key** in the sidebar
   - Default: `team_recursives`
   - Click "Connect" to authenticate

2. **Start Chatting**
   - Type messages as if you're a scammer
   - Click "Try Example" for sample messages

3. **Watch Intelligence Extraction**
   - See real-time updates in the right panel
   - Bank accounts, UPI IDs, phone numbers, links

4. **Monitor Scam Detection**
   - Scam type and confidence score
   - Color-coded alerts

5. **Export Data**
   - Click "Export Intelligence" to download JSON

## 📋 Example Messages

Try these scam messages to see the system in action:

```
"Your account is blocked! Click http://fake-bank.com to verify"
```

```
"Congratulations! You won ₹50,000. Send your bank account: 1234567890"
```

```
"This is SBI customer care. Your card is suspended. Send OTP immediately"
```

```
"Call +91-9876543210 for urgent KYC update or account will be closed"
```

```
"Pay via UPI: scammer@paytm to claim your prize"
```

## 🔧 Configuration

Edit [ui/.env.ui](ui/.env.ui):

```env
# Main honeypot endpoint
HONEYPOT_API_URL=https://agentic-honey-pot-for-scam-detection-iiv4.onrender.com

# API key (must match main app)
API_KEY=team_recursives

# Ports
UI_BACKEND_PORT=8001
STREAMLIT_SERVER_PORT=8501

# Database
DATABASE_PATH=ui/sessions.db
```

## 📚 API Endpoints

The UI backend provides these REST endpoints:

### Chat
```http
POST /chat
```
Send a message and get agent reply + intelligence

### Session Management
```http
POST /session/new
GET /session/{session_id}
GET /session/{session_id}/messages
DELETE /session/{session_id}
```

### Health Check
```http
GET /health
```

## 🌐 Deployment

### Deploy to Streamlit Cloud (Free)

1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo
4. Set main file: `ui/streamlit_app.py`
5. Add secrets in Streamlit settings:
   ```toml
   API_KEY = "team_recursives"
   UI_BACKEND_URL = "your-backend-url"
   ```

### Deploy Backend to Render/Railway

1. Create new Web Service
2. Set build command:
   ```bash
   pip install -r ui/requirements_ui.txt
   ```
3. Set start command:
   ```bash
   uvicorn ui.ui_backend:app --host 0.0.0.0 --port $PORT
   ```
4. Add environment variables:
   - `HONEYPOT_API_URL`
   - `API_KEY`

### Deploy with Docker

1. Build and push to registry:
```bash
docker build -t your-registry/honeypot-ui -f ui/Dockerfile .
docker push your-registry/honeypot-ui
```

2. Deploy to cloud:
   - **AWS ECS/Fargate**
   - **Google Cloud Run**
   - **Azure Container Instances**
   - **DigitalOcean App Platform**

## 🔒 Security

- ✅ API key required for all operations
- ✅ Session isolation per user
- ✅ No data leakage between sessions
- ✅ HTTPS recommended for production
- ✅ CORS configured for security
- ✅ Input validation on all endpoints

## 🗄️ Database

SQLite database schema:

### Sessions Table
```sql
CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    scam_detected INTEGER DEFAULT 0,
    scam_type TEXT,
    confidence REAL,
    intelligence TEXT DEFAULT '{}'
);
```

### Messages Table
```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    sender TEXT NOT NULL,
    text TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);
```

## 🧪 Testing

### Test UI Backend
```bash
curl http://localhost:8001/health
```

### Test Chat Endpoint
```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-123",
    "message": "Your account is blocked!",
    "api_key": "team_recursives"
  }'
```

### Test Session Creation
```bash
curl -X POST http://localhost:8001/session/new \
  -H "x-api-key: team_recursives"
```

## 🐛 Troubleshooting

### Issue: Backend not reachable
**Solution:** Check if UI backend is running on port 8001
```bash
lsof -i :8001  # macOS/Linux
netstat -ano | findstr :8001  # Windows
```

### Issue: Connection timeout to main honeypot
**Solution:** Verify the main honeypot URL is accessible
```bash
curl https://agentic-honey-pot-for-scam-detection-iiv4.onrender.com/health
```

### Issue: Invalid API key
**Solution:** Ensure API key matches in both `.env` and `.env.ui`

### Issue: Port already in use
**Solution:** Change port in `.env.ui` or kill process
```bash
kill -9 $(lsof -ti:8001)  # macOS/Linux
```

## 📊 Monitoring

### Backend Logs
```bash
# View logs in real-time
tail -f logs/ui_backend.log
```

### Database Stats
```bash
sqlite3 ui/sessions.db "SELECT COUNT(*) FROM sessions;"
sqlite3 ui/sessions.db "SELECT COUNT(*) FROM messages;"
```

### Cleanup Old Sessions
Run periodically to remove old data:
```python
from ui.session_store import SessionStore
store = SessionStore()
store.cleanup_old_sessions(days=7)
```

## 🎨 Customization

### Change UI Theme
Edit [ui/streamlit_app.py](ui/streamlit_app.py):
```python
st.set_page_config(
    page_title="Your Title",
    page_icon="🎯",
    layout="wide"
)
```

### Add Custom Styles
Modify the CSS section in `streamlit_app.py`:
```python
st.markdown("""
    <style>
    /* Your custom CSS */
    </style>
""", unsafe_allow_html=True)
```

### Change Backend Port
Edit [ui/.env.ui](ui/.env.ui):
```env
UI_BACKEND_PORT=9000
```

## 📝 Code Structure

```
ui/
├── streamlit_app.py       # Streamlit frontend
├── ui_backend.py          # FastAPI backend service
├── session_store.py       # SQLite database handler
├── intelligence_monitor.py # Intelligence extraction
├── requirements_ui.txt    # Python dependencies
├── .env.ui                # Configuration
├── Dockerfile             # Docker image
├── start_ui.sh            # Unix startup script
├── start_ui.bat           # Windows startup script
└── README_UI.md           # This file
```

## 🤝 Contributing

Want to enhance the UI? Here are some ideas:

- [ ] Add conversation export as PDF
- [ ] Implement session history browser
- [ ] Add charts for intelligence statistics
- [ ] Create admin dashboard
- [ ] Add multi-language support
- [ ] Implement WebSocket for real-time updates
- [ ] Add voice input/output
- [ ] Create mobile-responsive design

## 📄 License

Same as main project - see LICENSE file

## 🆘 Support

For issues specific to the UI:
1. Check this README
2. Verify main honeypot is accessible
3. Check browser console for errors
4. Review backend logs

For main honeypot issues:
- See main [README.md](../README.md)

## 🎉 Credits

Built as a demo interface for the Agentic Honey-Pot system
- **Framework**: Streamlit + FastAPI
- **Database**: SQLite
- **Architecture**: Zero-modification integration

---

**🚀 Ready to go! Start the UI and try it out:**

```bash
cd ui && ./start_ui.sh
```

Then open http://localhost:8501 in your browser!
