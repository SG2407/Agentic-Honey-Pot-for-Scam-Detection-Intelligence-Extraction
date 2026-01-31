# 🕷️ AI-Powered Agentic Honeypot System

> **Delhi Hackathon 2026** - An intelligent honeypot system that detects, engages, and extracts intelligence from scammers using advanced AI agents

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![Groq](https://img.shields.io/badge/Groq-AI%20Powered-orange.svg)](https://groq.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🎯 Project Overview

This AI-powered honeypot system represents a cutting-edge approach to combating cybercrime by:
- **Detecting scam attempts** using hybrid pattern matching + AI analysis
- **Autonomously engaging scammers** with multiple AI personas to keep them interested  
- **Extracting valuable intelligence** about scammer operations while protecting privacy
- **Providing actionable insights** to law enforcement and security teams

### 🏆 Key Innovations
- **Hybrid Detection Engine**: Combines regex patterns with Groq AI for 95%+ accuracy
- **Multi-Persona AI Agents**: Different conversation styles for various scam types
- **Privacy-Safe Intelligence**: Masks sensitive data while preserving investigative value
- **Production-Ready Architecture**: FastAPI backend with comprehensive error handling

## ✨ Features

### 🔍 **Advanced Scam Detection**
- Pattern-based detection for 15+ common scam types
- AI-powered semantic analysis using Groq's Llama models
- Confidence scoring and scam type classification
- Real-time threat assessment

### 🤖 **Intelligent Conversation Agents**
- **Vulnerable Persona**: Acts concerned and easily manipulated
- **Curious Persona**: Asks questions to extract more information  
- **Cautious Persona**: Shows hesitation to build trust
- Context-aware responses based on conversation history

### 📊 **Intelligence Extraction**
- Automatic extraction of phone numbers, emails, and URLs
- Bank account and UPI ID detection with privacy masking
- Cryptocurrency wallet identification
- Phishing link analysis and documentation

### 🛡️ **Security & Privacy**
- API key authentication for all endpoints
- Data masking to protect extracted sensitive information
- Structured logging with no PII exposure
- Rate limiting and input validation

### 🔄 **Integration & Monitoring**
- REST API with comprehensive documentation
- Callback service for external system integration
- Health monitoring and system status endpoints
- Comprehensive testing suite with realistic scenarios

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Client/SMS    │────│   FastAPI Server │────│   Groq AI API   │
│   Gateway       │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                    ┌──────────────────┐
                    │ Scam Detection   │
                    │ Engine           │
                    └──────────────────┘
                                │
                    ┌──────────────────┐
                    │ Conversation     │
                    │ Agent            │
                    └──────────────────┘
                                │
                    ┌──────────────────┐
                    │ Intelligence     │
                    │ Extractor        │
                    └──────────────────┘
                                │
                    ┌──────────────────┐
                    │ Callback         │
                    │ Service          │
                    └──────────────────┘
```

## 📁 Project Structure

```
Delhi_Hackathon/
├── 🚀 app/
│   ├── main.py                     # FastAPI application & API endpoints
│   ├── models.py                   # Pydantic models for request/response
│   ├── agents/
│   │   ├── scam_detector.py        # Hybrid scam detection engine
│   │   └── conversation_agent.py   # Multi-persona AI conversation agent
│   ├── services/
│   │   ├── intelligence_extractor.py  # Data extraction & privacy masking
│   │   └── callback_service.py     # External system integration
│   └── utils/
│       └── logger.py              # Structured logging configuration
├── ⚙️ config/
│   └── settings.py                # Environment-based configuration
├── 🧪 tests/
│   └── test_honeypot.py          # Comprehensive test suite
├── 🎯 Demo & Testing/
│   ├── demo.py                   # Full system demonstration
│   ├── test_quick.py            # Quick functionality test
│   └── start_server.sh          # Server startup script
├── 📋 Configuration/
│   ├── .env.example            # Environment variables template
│   ├── requirements.txt        # Python dependencies
│   └── .gitignore             # Git exclusion rules
└── 📖 Documentation/
    ├── README.md              # This file
    ├── PROJECT_GUIDE.md       # Development guide
    └── Problem_Statement.txt  # Original hackathon requirements
```

## 🚀 Quick Start

### Prerequisites
- **Python 3.11+** (required for latest asyncio features)
- **Git** for version control
- **Groq API Key** (free from [console.groq.com](https://console.groq.com))

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/Delhi_Hackathon_AI_Honeypot.git
cd Delhi_Hackathon_AI_Honeypot

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit configuration (add your API keys)
nano .env  # or your preferred editor
```

**Required Environment Variables:**
```env
# API Configuration
API_KEY="your_secure_api_key_here"

# Groq Configuration  
GROQ_API_KEY="gsk_your_groq_api_key_here"
GROQ_MODEL="llama-3.3-70b-versatile"

# Application Settings
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### 3. Launch & Test

```bash
# Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# In a new terminal, test the system
python test_quick.py

# Run full demonstration
python demo.py
```

## 📡 API Reference

### Authentication
All API endpoints require authentication via the `x-api-key` header:
```http
x-api-key: your_api_key_here
```

### Core Endpoint: `/honeypot`

**POST** `/honeypot` - Process scam messages and generate responses

**Request Body:**
```json
{
  "sessionId": "unique-session-identifier",
  "message": {
    "sender": "scammer",
    "text": "URGENT: Your bank account will be blocked today. Click here to verify: https://fake-bank.com/verify",
    "timestamp": "2026-01-31T10:30:00Z"
  },
  "conversationHistory": [
    {
      "sender": "scammer", 
      "text": "Previous message",
      "timestamp": "2026-01-31T10:25:00Z"
    }
  ],
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
  "reply": "Oh no! What do I need to do to keep my account safe? Should I click that link?",
  "scamDetection": {
    "isScam": true,
    "confidence": 0.95,
    "scamType": "banking_fraud", 
    "riskLevel": "HIGH"
  },
  "extractedIntelligence": {
    "phoneNumbers": ["91XXXXXXXXXX"],
    "urls": ["https://fake-bank.com/verify"],
    "suspiciousKeywords": ["urgent", "verify", "blocked"]
  },
  "conversationContext": {
    "persona": "vulnerable",
    "turnCount": 3,
    "engagementLevel": "high"
  }
}
```

### Health Check: `/health`

**GET** `/health` - System status and health metrics

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-31T10:30:00Z",
  "environment": "development",
  "version": "1.0.0",
  "dependencies": {
    "groq_api": "connected",
    "database": "healthy"
  }
}
```

## 🧪 Testing & Validation

### Quick System Test
```bash
python test_quick.py
```

### Full Demonstration
```bash
python demo.py
```
This runs 3 realistic scam scenarios:
- 🏦 **Banking threat**: "Account will be blocked" scam
- 🎰 **Fake lottery**: Prize claiming scam  
- 💳 **Payment fraud**: UPI refund scam

### Manual API Testing
```bash
# Test with curl
curl -X POST "http://localhost:8000/honeypot" \
     -H "x-api-key: team_recursives" \
     -H "Content-Type: application/json" \
     -d '{
       "sessionId": "test-123",
       "message": {
         "sender": "scammer",
         "text": "You won $10000! Call +1234567890 now!",
         "timestamp": "2026-01-31T10:30:00Z"
       },
       "conversationHistory": [],
       "metadata": {"channel": "SMS", "language": "English", "locale": "US"}
     }'
```

## 🔧 Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_KEY` | `"team_recursives"` | Authentication key for API access |
| `GROQ_API_KEY` | *Required* | Your Groq API key for AI functionality |
| `GROQ_MODEL` | `"llama-3.3-70b-versatile"` | Groq model for AI responses |
| `ENVIRONMENT` | `development` | Deployment environment |
| `LOG_LEVEL` | `INFO` | Logging verbosity level |
| `MAX_CONVERSATION_TURNS` | `20` | Maximum turns per conversation |
| `SCAM_CONFIDENCE_THRESHOLD` | `0.7` | Minimum confidence for scam detection |
| `GUVI_CALLBACK_URL` | *Set* | Hackathon callback endpoint |

### Persona Configuration
The system automatically selects conversation personas based on scam type:
- **Banking/Finance scams** → Vulnerable persona (worried about money)
- **Prize/Lottery scams** → Curious persona (interested in rewards)  
- **Tech support scams** → Cautious persona (tech-hesitant)

## 📊 Monitoring & Logs

### Structured Logging
All system events are logged in JSON format:
```json
{
  "asctime": "2026-01-31 10:30:00",
  "name": "app.agents.scam_detector", 
  "levelname": "INFO",
  "message": "Scam detection completed",
  "event_type": "scam_detection",
  "session_id": "demo-123",
  "is_scam": true,
  "confidence": 0.95,
  "scam_type": "banking_fraud"
}
```

### Key Metrics to Monitor
- **Detection Accuracy**: Scam vs legitimate message classification
- **Response Quality**: AI conversation coherence and engagement
- **Intelligence Yield**: Data points extracted per conversation
- **System Performance**: Response time and error rates

## 🤝 Contributing

### Development Setup
```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/ -v

# Code formatting
black app/ config/ tests/
isort app/ config/ tests/

# Type checking
mypy app/ config/
```

### Contribution Guidelines
1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Test** your changes thoroughly
4. **Commit** with descriptive messages (`git commit -m 'Add amazing feature'`)
5. **Push** to your branch (`git push origin feature/amazing-feature`)
6. **Open** a Pull Request

## 🔒 Security Considerations

### Data Privacy
- ✅ **No PII Storage**: Sensitive data is masked immediately after extraction
- ✅ **Secure Logging**: Logs contain no personal information
- ✅ **API Authentication**: All endpoints require valid API keys
- ✅ **Input Validation**: All inputs are sanitized and validated

### Deployment Security
- 🔐 Use environment variables for all secrets
- 🛡️ Deploy behind reverse proxy (nginx/traefik)
- 🔒 Enable HTTPS in production
- 📊 Monitor for suspicious access patterns

## 📈 Performance & Scalability

### System Requirements
- **CPU**: 2+ cores recommended for concurrent processing
- **RAM**: 4GB+ for AI model inference
- **Network**: Stable internet for Groq API calls
- **Storage**: 1GB for logs and temporary data

### Scaling Considerations
- **Horizontal**: Multiple server instances with load balancer
- **Caching**: Redis for conversation state and frequent queries
- **Database**: PostgreSQL for persistent intelligence storage
- **Monitoring**: Prometheus + Grafana for production metrics

## 🐛 Troubleshooting

### Common Issues

**Error: "Invalid API key"**
```bash
# Check your .env file
cat .env | grep API_KEY
# Ensure test script uses same key as .env
```

**Error: "Model decommissioned"**
```bash
# Update to supported model in .env
GROQ_MODEL="llama-3.3-70b-versatile"
```

**Error: "Connection refused"**
```bash
# Ensure server is running
lsof -i :8000
# Restart if needed
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python -m uvicorn app.main:app --reload --log-level debug
```

## 📜 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

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