# AI-Powered Agentic Honeypot - System Architecture

## Overview
AI-powered honeypot system that detects scam messages, engages scammers in realistic conversations, and extracts actionable intelligence for law enforcement.

## Core Components

### 1. Scam Detection Engine (`app/agents/scam_detector.py`)
**Technology**: Groq LLM (Llama 3.3 70B Versatile)

**Detection Strategy**:
- **Primary**: Groq LLM with Indian context awareness
- **Fallback**: Pattern-based detection using regex

**Indian Scam Patterns Detected**:
- UPI fraud (UPI ID, UPI PIN requests)
- Banking fraud (SBI, HDFC, ICICI, Axis Bank)
- OTP/verification code phishing
- Account blocking threats
- Prize/lottery scams (Rs/INR)
- KYC verification scams
- Aadhaar/PAN card requests
- Payment refund scams

**Performance**: 85.7% accuracy on test dataset

**Key Features**:
- JSON-based response format
- Confidence scoring (0.0-1.0)
- Scam type classification
- Detailed reasoning for each decision
- Error handling with fallback detection

### 2. Conversation Agent (`app/agents/conversation_agent.py`)
**Technology**: Groq LLM (Llama 3.3 70B Versatile)

**Persona**: Elderly person (vulnerable demographic)

**Capabilities**:
- Context-aware responses using conversation history
- Gradual information disclosure
- Natural hesitation patterns
- Keeps scammers engaged
- Maintains consistent persona

**Strategies**:
- Express initial concern/curiosity
- Ask clarifying questions
- Show reluctance to share sensitive info
- Simulate confusion about technology
- Gradually show interest while hesitating

### 3. Intelligence Extractor (`app/services/intelligence_extractor.py`)
**Purpose**: Extract actionable data from scammer messages

**Extracted Data**:
- Phone numbers (Indian format)
- URLs and domains
- UPI IDs
- Bank account numbers
- Email addresses
- Location references
- Organization names

**Output Format**: Structured JSON for law enforcement

### 4. Callback Service (`app/services/callback_service.py`)
**Purpose**: Validate and log callback attempts from scammers

**Features**:
- Validates URL parameters
- Detects malicious callback patterns
- Prevents XSS/injection attacks
- Tracks callback statistics
- Structured logging

## API Endpoints

### POST `/honeypot/message`
Main endpoint for receiving scam messages

**Request Body**:
```json
{
  "sender": "scammer_id",
  "text": "message content",
  "session_id": "optional_session_id"
}
```

**Response**:
```json
{
  "reply": "agent response",
  "is_scam_detected": true/false,
  "confidence": 0.0-1.0,
  "session_id": "uuid",
  "timestamp": "ISO8601"
}
```

### GET `/honeypot/callback`
Handles scammer callback attempts

**Query Parameters**:
- `user`: User identifier
- `token`: Tracking token
- `action`: Callback action
- Additional custom parameters

### GET `/health`
Health check endpoint

## Technology Stack

### Core Framework
- **FastAPI**: Web framework
- **Uvicorn**: ASGI server
- **Pydantic**: Data validation

### AI/LLM
- **Groq API**: LLM provider
- **Model**: Llama 3.3 70B Versatile

### Utilities
- **python-dotenv**: Environment management
- **python-json-logger**: Structured logging
- **aiofiles**: Async file operations
- **httpx**: Async HTTP client
- **regex**: Advanced pattern matching

### Testing
- **pytest**: Test framework
- **pytest-asyncio**: Async test support

## Configuration

### Environment Variables (`.env`)
```bash
# Required
GROQ_API_KEY=your_groq_api_key

# Optional
GROQ_MODEL=llama-3.3-70b-versatile
ENVIRONMENT=development
```

### Settings (`config/settings.py`)
- LLM model selection
- Temperature settings
- Max tokens
- Response formats
- Logging configuration

## Project Structure
```
Delhi_Hackathon/
├── app/
│   ├── main.py                    # FastAPI application
│   ├── models.py                  # Pydantic data models
│   ├── agents/
│   │   ├── scam_detector.py       # Groq LLM scam detection
│   │   └── conversation_agent.py  # Conversation generation
│   ├── services/
│   │   ├── callback_service.py    # Callback validation
│   │   └── intelligence_extractor.py  # Data extraction
│   └── utils/
│       └── logger.py              # Structured logging
├── config/
│   └── settings.py                # Configuration
├── tests/
│   └── test_honeypot.py          # Unit tests
├── demo.py                        # Demo scenarios
├── test_groq_detection.py        # Detection tests
├── requirements.txt               # Dependencies
└── start_server.sh               # Server startup script
```

## Key Design Decisions

### Why Groq LLM over RoBERTa?
1. **Indian Context**: Better understanding of regional scam patterns
2. **Flexibility**: No need for retraining on new scam types
3. **Accuracy**: 85.7% vs RoBERTa's poor performance on Indian scams
4. **Reasoning**: Provides explanations for decisions
5. **Maintenance**: No model management, automatic updates

### Hybrid Detection Strategy
- **Primary**: Groq LLM for nuanced understanding
- **Fallback**: Pattern-based for API failures
- **Threshold**: 0.15 pattern score triggers scam classification

### Conversation Design
- **Persona**: Elderly person (most vulnerable to scams)
- **Strategy**: Engage without exposing real data
- **Context**: Full conversation history for coherent responses
- **Safety**: Never discloses real sensitive information

## Performance Metrics

### Scam Detection
- **Accuracy**: 85.7% on test dataset
- **True Positives**: 100% for Indian scam patterns
- **False Positives**: 14.3% (mainly on ambiguous shipping messages)
- **Response Time**: ~300ms per message

### System
- **Concurrency**: Async/await throughout
- **Logging**: Structured JSON logs
- **Error Handling**: Graceful fallbacks
- **Scalability**: Stateless design

## Security Considerations

### Input Validation
- URL parameter sanitization
- XSS prevention
- Injection attack prevention
- Length limits on inputs

### Data Protection
- No real user data stored
- Temporary conversation history
- No sensitive info in logs
- Environment-based secrets

### Honeypot Safety
- Isolated environment recommended
- No production data access
- Monitoring for abuse
- Rate limiting on endpoints

## Deployment

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Add your GROQ_API_KEY

# Run server
./start_server.sh
# or
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Testing
```bash
# Test scam detection
python test_groq_detection.py

# Test full scenarios
python demo.py

# Run unit tests
pytest tests/
```

### Production Recommendations
1. **Containerization**: Use Docker for deployment
2. **Reverse Proxy**: nginx/Caddy for SSL/TLS
3. **Rate Limiting**: Prevent abuse
4. **Monitoring**: Track detection accuracy
5. **Logging**: Centralized log aggregation
6. **Secrets**: Use vault for API keys
7. **Scaling**: Multiple workers with load balancer

## Future Enhancements

### Short-term
- [ ] Improve false positive rate on legitimate messages
- [ ] Add more Indian language support (Hindi, Tamil, etc.)
- [ ] Expand scam pattern database
- [ ] Add webhook notifications for high-confidence scams

### Long-term
- [ ] Voice call honeypot integration
- [ ] Multi-language conversation agents
- [ ] Real-time dashboard for monitoring
- [ ] Integration with law enforcement databases
- [ ] Machine learning on collected scam data
- [ ] Automated scammer profiling

## License
[Add your license information]

## Contributors
[Add contributor information]

## Acknowledgments
- **Groq**: LLM API provider
- **Delhi Hackathon 2026**: Competition organizers
- **Indian Cybercrime Coordination Centre**: Pattern research

---

**Last Updated**: February 2026  
**Version**: 2.0 (Groq LLM Integration)
