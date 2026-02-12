"""
UI Backend Service - Separate FastAPI server for the Streamlit UI
This service acts as a middleware between the UI and the main honeypot app
NO CHANGES TO EXISTING CODE - Completely independent service
"""

import os
import uuid
import logging
import httpx
from datetime import datetime, timezone
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Import our custom modules (new files in ui/ folder)
from ui.session_store import SessionStore
from ui.intelligence_monitor import IntelligenceMonitor

# Load environment variables
load_dotenv("ui/.env.ui")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
# When deployed on same service, use localhost. Otherwise use full URL
HONEYPOT_API_URL = os.getenv("HONEYPOT_API_URL", "http://localhost:10000")
VALID_API_KEY = os.getenv("API_KEY", "team_recursives")

# Initialize components
session_store = SessionStore()
intelligence_monitor = IntelligenceMonitor()

# FastAPI app
app = FastAPI(
    title="Scam Honeypot UI Backend",
    description="Backend service for Streamlit UI - calls main honeypot without modifications",
    version="1.0.0"
)

# Enable CORS for Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models
class ChatMessage(BaseModel):
    """User message from UI"""
    session_id: str
    message: str
    api_key: str

class ChatResponse(BaseModel):
    """Response to UI"""
    success: bool
    agent_reply: str
    session_id: str
    message_count: int
    scam_detected: bool
    scam_type: Optional[str] = None
    confidence: Optional[float] = None
    intelligence: Dict = {}

class SessionInfo(BaseModel):
    """Session information"""
    session_id: str
    created_at: str
    message_count: int
    scam_detected: bool
    intelligence: Dict

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.post("/chat", response_model=ChatResponse)
async def send_message(chat_msg: ChatMessage):
    """
    Send message to honeypot and track intelligence
    Flow:
    1. Validate API key
    2. Get conversation history from session store
    3. Call main honeypot endpoint
    4. Extract intelligence in parallel
    5. Store results and return to UI
    """
    try:
        # Validate API key
        if chat_msg.api_key != VALID_API_KEY:
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        # Get or create session
        session = session_store.get_session(chat_msg.session_id)
        if not session:
            session = session_store.create_session(chat_msg.session_id)
        
        # Get conversation history
        history = session_store.get_conversation_history(chat_msg.session_id)
        
        # Build payload for main honeypot (matches existing format)
        timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)
        honeypot_payload = {
            "sessionId": chat_msg.session_id,
            "message": {
                "sender": "scammer",  # User acts as scammer
                "text": chat_msg.message,
                "timestamp": timestamp
            },
            "conversationHistory": history,
            "metadata": {
                "channel": "ui_demo",
                "locale": "en-IN"
            }
        }
        
        # Call main honeypot endpoint
        logger.info(f"Calling honeypot API for session {chat_msg.session_id}")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{HONEYPOT_API_URL}/honeypot",
                json=honeypot_payload,
                headers={"x-api-key": chat_msg.api_key}
            )
            response.raise_for_status()
            honeypot_response = response.json()
        
        agent_reply = honeypot_response.get("reply", "I'm listening...")
        
        # Store user message
        session_store.add_message(
            chat_msg.session_id,
            sender="scammer",
            text=chat_msg.message,
            timestamp=timestamp
        )
        
        # Store agent reply
        agent_timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)
        session_store.add_message(
            chat_msg.session_id,
            sender="agent",
            text=agent_reply,
            timestamp=agent_timestamp
        )
        
        # Extract intelligence (parallel to main app)
        # This runs independently and doesn't affect the callback
        intelligence = intelligence_monitor.extract_intelligence(
            chat_msg.message,
            history
        )
        
        # Detect scam type
        scam_info = intelligence_monitor.detect_scam(
            chat_msg.message,
            history
        )
        
        # Update session with intelligence
        session_store.update_intelligence(
            chat_msg.session_id,
            intelligence
        )
        
        # Update session with scam detection
        if scam_info["is_scam"]:
            session_store.update_scam_status(
                chat_msg.session_id,
                scam_detected=True,
                scam_type=scam_info["scam_type"],
                confidence=scam_info["confidence"]
            )
        
        # Get updated session info
        session = session_store.get_session(chat_msg.session_id)
        message_count = session_store.get_message_count(chat_msg.session_id)
        
        return ChatResponse(
            success=True,
            agent_reply=agent_reply,
            session_id=chat_msg.session_id,
            message_count=message_count,
            scam_detected=session["scam_detected"],
            scam_type=session.get("scam_type"),
            confidence=session.get("confidence"),
            intelligence=session["intelligence"]
        )
        
    except httpx.HTTPStatusError as e:
        logger.error(f"Honeypot API error: {e.response.status_code}")
        raise HTTPException(status_code=502, detail="Honeypot service error")
    except httpx.RequestError as e:
        logger.error(f"Connection error: {str(e)}")
        raise HTTPException(status_code=503, detail="Cannot connect to honeypot service")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/session/new")
async def create_new_session(api_key: str = Header(None, alias="x-api-key")):
    """Create a new session"""
    if api_key != VALID_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    session_id = f"ui-{uuid.uuid4().hex[:12]}"
    session = session_store.create_session(session_id)
    
    return {
        "success": True,
        "session_id": session_id,
        "created_at": session["created_at"]
    }


@app.get("/session/{session_id}", response_model=SessionInfo)
async def get_session(session_id: str, api_key: str = Header(None, alias="x-api-key")):
    """Get session information"""
    if api_key != VALID_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    message_count = session_store.get_message_count(session_id)
    
    return SessionInfo(
        session_id=session_id,
        created_at=session["created_at"],
        message_count=message_count,
        scam_detected=session["scam_detected"],
        intelligence=session["intelligence"]
    )


@app.get("/session/{session_id}/messages")
async def get_messages(session_id: str, api_key: str = Header(None, alias="x-api-key")):
    """Get conversation history for a session"""
    if api_key != VALID_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    messages = session_store.get_conversation_history(session_id)
    return {
        "success": True,
        "session_id": session_id,
        "messages": messages
    }


@app.delete("/session/{session_id}")
async def delete_session(session_id: str, api_key: str = Header(None, alias="x-api-key")):
    """Delete a session"""
    if api_key != VALID_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    success = session_store.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "success": True,
        "message": "Session deleted"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Check if honeypot is reachable
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{HONEYPOT_API_URL}/health")
            honeypot_status = "healthy" if response.status_code == 200 else "unhealthy"
    except:
        honeypot_status = "unreachable"
    
    return {
        "status": "healthy",
        "service": "UI Backend",
        "honeypot_status": honeypot_status,
        "honeypot_url": HONEYPOT_API_URL,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Scam Honeypot UI Backend",
        "version": "1.0.0",
        "endpoints": {
            "chat": "POST /chat",
            "new_session": "POST /session/new",
            "get_session": "GET /session/{session_id}",
            "get_messages": "GET /session/{session_id}/messages",
            "delete_session": "DELETE /session/{session_id}",
            "health": "GET /health"
        },
        "honeypot_url": HONEYPOT_API_URL
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
