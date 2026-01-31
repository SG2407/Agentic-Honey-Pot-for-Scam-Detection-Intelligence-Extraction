# AI-Powered Agentic Honeypot for Scam Detection

A sophisticated AI-driven system that detects scam messages and autonomously engages scammers to extract intelligence while maintaining a believable human persona.

## Features

- **Scam Detection**: Advanced AI-powered detection of various scam types
- **Autonomous Agent**: Intelligent AI agent that maintains human-like conversations
- **Intelligence Extraction**: Extracts bank accounts, UPI IDs, phone numbers, and phishing links
- **Multi-turn Conversations**: Handles complex conversation flows
- **RESTful API**: Production-ready FastAPI implementation
- **Security**: API key authentication and secure data handling

## Project Structure

```
/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── models.py            # Pydantic models
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── scam_detector.py # Scam detection logic
│   │   └── conversation_agent.py # AI conversation agent
│   ├── services/
│   │   ├── __init__.py
│   │   ├── intelligence_extractor.py
│   │   └── callback_service.py
│   └── utils/
│       ├── __init__.py
│       └── logger.py
├── config/
│   ├── __init__.py
│   └── settings.py
├── tests/
├── .env.example
├── requirements.txt
└── README.md
```

## Installation

1. Clone the repository
2. Create virtual environment: `python3.11 -m venv venv`
3. Activate environment: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and configure
6. Run: `uvicorn app.main:app --reload`

## Configuration

Set the following environment variables in `.env`:

- `API_KEY`: Your secret API key for authentication
- `OPENAI_API_KEY`: OpenAI API key for AI agent
- `ENVIRONMENT`: development/production
- `LOG_LEVEL`: INFO/DEBUG/ERROR

## API Endpoints

- `POST /honeypot` - Main endpoint for message analysis
- `GET /health` - Health check endpoint

## Usage

The system accepts POST requests to `/honeypot` with the following format:

```json
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
```

## Response Format

```json
{
  "status": "success",
  "reply": "Why is my account being suspended?"
}
```