# 🚀 AI-Powered Agentic Honeypot System - COMPLETE PROJECT

## 🎯 Project Overview

This is a complete, industry-standard implementation of an AI-powered honeypot system for scam detection and intelligence extraction, built according to the Delhi Hackathon problem statement.

### ✨ Key Features

- **Advanced Scam Detection**: AI + pattern-based detection with 70% confidence threshold
- **Autonomous AI Agent**: Engages scammers with human-like personas
- **Intelligence Extraction**: Extracts bank accounts, UPI IDs, phone numbers, and phishing links
- **Multi-turn Conversations**: Handles complex conversation flows up to 20 turns
- **Secure API**: FastAPI with API key authentication
- **Callback Integration**: Mandatory final result callback to GUVI endpoint
- **Structured Logging**: JSON-based logging for monitoring
- **Production Ready**: Error handling, retries, and graceful degradation

## 🏗️ Architecture

```
AI-Powered Honeypot System
├── Scam Detection Engine (AI + Pattern Matching)
├── Conversation Agent (OpenAI GPT-powered)
├── Intelligence Extractor (Regex + NLP)
├── Callback Service (Retry mechanism)
└── RESTful API (FastAPI)
```

## 📁 Project Structure

```
Delhi_Hackathon/
├── venv/                      # Python 3.11 virtual environment
├── app/
│   ├── __init__.py
│   ├── main.py               # FastAPI application
│   ├── models.py             # Pydantic data models
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── scam_detector.py  # AI-powered scam detection
│   │   └── conversation_agent.py # Intelligent conversation agent
│   ├── services/
│   │   ├── __init__.py
│   │   ├── intelligence_extractor.py # Intelligence extraction
│   │   └── callback_service.py # GUVI callback service
│   └── utils/
│       ├── __init__.py
│       └── logger.py         # Structured logging
├── config/
│   ├── __init__.py
│   └── settings.py           # Configuration management
├── tests/
│   └── test_honeypot.py      # Unit tests
├── .env                      # Environment configuration
├── requirements.txt          # Dependencies
├── start_server.sh           # Server startup script
├── demo.py                   # Demonstration script
├── test_quick.py            # Quick test script
└── README.md                # Documentation
```

## 🚀 Quick Start

### 1. Environment Setup
```bash
cd Delhi_Hackathon
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configuration
Edit `.env` file:
```bash
# Required
API_KEY=honeypot_secret_key_2026
GROQ_API_KEY=gsk_your_groq_api_key_here

# Optional
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### 3. Start Server
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Test System
```bash
python test_quick.py
```

### 5. Run Demo
```bash
python demo.py
```

## 🔧 API Endpoints

### Health Check
```
GET /health
Response: {"status": "healthy", "timestamp": "...", "environment": "..."}
```

### Main Honeypot Endpoint
```
POST /honeypot
Headers: {"x-api-key": "your_secret_key", "Content-Type": "application/json"}

Request Body:
{
  "sessionId": "unique-session-id",
  "message": {
    "sender": "scammer",
    "text": "Your bank account will be blocked today. Verify immediately.",
    "timestamp": "2026-01-21T10:15:30Z"
  },
  "conversationHistory": [],
  "metadata": {
    "channel": "SMS",
    "language": "English",
    "locale": "IN"
  }
}

Response:
{
  "status": "success",
  "reply": "Why is my account being blocked? What did I do wrong?"
}
```

## 🤖 AI Agent Personas

The system uses different personas based on scam type:

- **Confused Elderly**: For credential phishing attacks
- **Worried Customer**: For financial threat scenarios  
- **Excited Winner**: For prize/lottery scams
- **Confused User**: For payment fraud attempts
- **Cautious User**: Default persona for unknown scams

## 🎯 Scam Detection Capabilities

### Pattern-Based Detection
- Urgency tactics ("urgent", "immediate", "act now")
- Financial threats ("account blocked", "suspicious activity")
- Credential requests (OTP, PIN, passwords)
- Impersonation (banks, government)
- Reward baits (prizes, cashbacks)

### AI-Enhanced Analysis
- Context-aware analysis using OpenAI GPT
- Conversation history consideration
- Confidence scoring (0.0-1.0)
- Scam type classification

## 📊 Intelligence Extraction

The system automatically extracts and masks:

- **Bank Account Numbers**: `1234XXXXXXXX5678`
- **UPI IDs**: `usXXXXX@paytm`
- **Phone Numbers**: `987XXXX123`
- **Phishing Links**: `http://faXXXX.com/path`
- **Suspicious Keywords**: List of scam indicators

## 🔄 Callback Integration

Automatically sends final results to GUVI endpoint:

```json
{
  "sessionId": "session-123",
  "scamDetected": true,
  "totalMessagesExchanged": 8,
  "extractedIntelligence": {
    "bankAccounts": ["1234XXXX5678"],
    "upiIds": ["scXXX@paytm"],
    "phishingLinks": ["http://faXXX.com"],
    "phoneNumbers": ["987XXXX123"],
    "suspiciousKeywords": ["urgent", "otp", "verify"]
  },
  "agentNotes": "Used urgency tactics (2 instances). Requested credentials (3 instances)."
}
```

## 🧪 Testing

### Unit Tests
```bash
python -m pytest tests/test_honeypot.py -v
```

### Quick Test
```bash
python test_quick.py
```

### Full Demo
```bash
python demo.py
```

## 🔒 Security Features

- API key authentication
- Input validation with Pydantic
- Data masking for privacy
- Error handling without information leakage
- Rate limiting ready (configurable)
- CORS protection

## 📈 Production Considerations

### Scalability
- Use Redis/Database for conversation storage
- Implement proper session management
- Add load balancing
- Use proper logging aggregation

### Monitoring
- Structured JSON logging
- Conversation event tracking
- Performance metrics
- Error tracking

### Deployment
- Docker containerization ready
- Environment-based configuration
- Health check endpoint
- Graceful shutdown handling

## 🎯 Problem Statement Compliance

✅ **Scam Detection**: Advanced AI + pattern matching  
✅ **Autonomous Agent**: Multi-turn conversations with human personas  
✅ **Intelligence Extraction**: Bank accounts, UPI IDs, phone numbers, links  
✅ **RESTful API**: FastAPI with proper authentication  
✅ **Callback Integration**: Mandatory GUVI endpoint callback  
✅ **Multi-turn Support**: Up to 20 conversation turns  
✅ **Structured Response**: JSON format as specified  
✅ **Error Handling**: Graceful degradation and logging  

## 📝 Usage Examples

### Basic Scam Detection
```python
# The system detects various scam types:
# 1. Financial threats
# 2. Credential phishing
# 3. Prize scams
# 4. Payment fraud
# 5. Impersonation
```

### Conversation Flow
```
Scammer: "Your account will be blocked. Share OTP."
Agent: "Why is my account being blocked? I'm confused."
Scammer: "Suspicious activity detected. Send OTP 123456."
Agent: "I don't understand. What employee ID are you using?"
... (conversation continues with intelligence extraction)
```

## 🚨 Important Notes

1. **OpenAI API Key**: Required for full AI capabilities
2. **GUVI Callback**: Mandatory for evaluation
3. **Session Management**: In-memory storage (use Redis in production)
4. **Rate Limiting**: Not implemented (add for production)
5. **Data Privacy**: All sensitive data is masked

## 🎉 Success Metrics

The system successfully:
- Detects scam messages with high accuracy
- Engages scammers with believable personas
- Extracts actionable intelligence
- Maintains conversation flow for multiple turns
- Provides structured results via API
- Sends mandatory callbacks to evaluation endpoint

## 🤝 Support

For questions or issues:
1. Check the logs for detailed error information
2. Verify environment configuration
3. Test with the provided demo scripts
4. Ensure OpenAI API key is valid

---

**Built with ❤️ for Delhi Hackathon 2026 - AI-Powered Cybersecurity Solution**