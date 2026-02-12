# 🎉 Quick Start Guide - UI Demo

This guide will get you started with the **interactive UI demo** in under 5 minutes!

## 🚀 What You'll Get

A beautiful chat interface where you can:
- ✅ **Act as a scammer** and send messages
- ✅ **See AI responses** from the honeypot agent
- ✅ **Watch intelligence extraction** in real-time
- ✅ **Monitor scam detection** with confidence scores
- ✅ **Export session data** as JSON

## ⚡ Quick Start

### One Command Start (macOS/Linux)
```bash
cd ui && ./start_ui.sh
```

### One Command Start (Windows)
```cmd
cd ui
start_ui.bat
```

That's it! The browser will open automatically to http://localhost:8501

## 🎯 First Steps

1. **Enter API Key**: `team_recursives` (in the sidebar)
2. **Click Connect**: ✅ You'll see "Connected" status
3. **Start Chatting**: Try clicking "Try Example" button
4. **Watch the Magic**: Intelligence appears on the right panel!

## 💡 Example Messages to Try

### Financial Threat Scam
```
Your bank account is blocked! Verify immediately at http://fake-bank.com
```

### Credential Phishing
```
We need your OTP to unblock your card. Please share the 6-digit code.
```

### Prize/Reward Scam
```
Congratulations! You won ₹1,00,000! Send your bank account: 1234567890
```

### Impersonation
```
This is Income Tax Department. Your PAN ABCDE1234F has issues. Call +91-9876543210
```

## 🛠️ What's Running?

Two services will start:

1. **UI Backend** (http://localhost:8001)
   - FastAPI server
   - Handles chat logic
   - Stores sessions in SQLite
   - Calls your main honeypot API

2. **Streamlit UI** (http://localhost:8501)
   - Chat interface
   - Intelligence visualization
   - Session management

## 🔍 Behind the Scenes

```
Your Browser (Chat UI)
    ↓
UI Backend (Port 8001)
    ↓
Main Honeypot API (https://agentic-honey-pot-for-scam-detection-iiv4.onrender.com)
    ↓
AI Agent Response + Intelligence Extraction
    ↓
Back to UI (Display Results)
```

**Important**: Your existing honeypot code is **NOT modified** at all!

## 📱 What You'll See

### Chat Interface
- Your messages on the right (as scammer)
- Agent responses on the left
- Beautiful, smooth animations
- Message history

### Intelligence Panel
- 🏦 Bank Accounts detected
- 💳 UPI IDs found
- 📞 Phone Numbers extracted
- 🔗 Phishing Links caught
- 🔑 Suspicious Keywords tracked

### Scam Detection
- 🚨 Real-time alerts
- Scam type classification
- Confidence percentage
- Color-coded warnings

## 🎨 Screenshots (What to Expect)

**Before Scam Detection:**
```
Status: ✅ Clean
Messages: 2
Intelligence: None yet
```

**After Scam Detection:**
```
Status: 🚨 Scam Detected!
Type: credential_phishing
Confidence: 95%
Intelligence:
  - Keywords: OTP, verify, urgent
  - Phone: +91-9876543210
```

## ⚙️ Troubleshooting

### Port Already in Use?
```bash
# Kill existing process
lsof -i :8001 | grep LISTEN | awk '{print $2}' | xargs kill -9
lsof -i :8501 | grep LISTEN | awk '{print $2}' | xargs kill -9

# Then restart
./start_ui.sh
```

### Backend Not Connecting?
Check if main honeypot is up:
```bash
curl https://agentic-honey-pot-for-scam-detection-iiv4.onrender.com/health
```

### Dependencies Missing?
```bash
pip install -r ui/requirements_ui.txt
```

## 🎓 Learn More

- **Full UI Documentation**: [ui/README_UI.md](ui/README_UI.md)
- **Main Honeypot Docs**: [README.md](README.md)
- **API Documentation**: http://localhost:8001/docs (when running)

## 🚀 Deploy to Cloud

Want to share this with others? Deploy for free:

### Streamlit Cloud (Free)
1. Push to GitHub
2. Go to share.streamlit.io
3. Connect repo → ui/streamlit_app.py
4. Done! Get public URL

### Render/Railway (Backend)
1. Create new service
2. Point to your repo
3. Set start command: `uvicorn ui.ui_backend:app --host 0.0.0.0 --port $PORT`
4. Done! Get API URL

Full deployment guide in [ui/README_UI.md](ui/README_UI.md)

## 🎉 You're Ready!

Now run:
```bash
cd ui && ./start_ui.sh
```

Open http://localhost:8501 and start chatting! 🕷️

---

**Need Help?** Check [ui/README_UI.md](ui/README_UI.md) for detailed documentation.
