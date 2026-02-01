"""FastAPI application - Agentic Honey-Pot for Scam Detection"""

import os
import logging
from datetime import datetime, timezone
from typing import Optional, Set, Dict
from fastapi import FastAPI, HTTPException, Header, Query, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.models import HoneypotRequest, HoneypotResponse, CallbackPayload
from app.scam_detector import ScamDetector
from app.intelligence_extractor import IntelligenceExtractor
from app.conversation_agent import ConversationAgent
from app.callback_service import CallbackService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global state for session tracking
callback_sent_sessions: Set[str] = set()  # Sessions that received callback (session closed)
last_message_time: Dict[str, datetime] = {}  # Track last message time for timeout
message_counts: Dict[str, int] = {}  # Track actual messages exchanged per session
MESSAGE_TIMEOUT_SECONDS = int(os.getenv("MESSAGE_TIMEOUT_SECONDS", "10"))

# Initialize components
scam_detector = ScamDetector()
intelligence_extractor = IntelligenceExtractor()
conversation_agent = ConversationAgent()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    logger.info("🚀 Agentic Honey-Pot starting...")
    logger.info(f"⏱  Timeout configured: {MESSAGE_TIMEOUT_SECONDS} seconds")
    yield
    logger.info("🛑 Agentic Honey-Pot shutting down...")

app = FastAPI(
    title="Agentic Honey-Pot for Scam Detection",
    description="AI-powered honeypot system for scam detection and intelligence gathering",
    version="2.0.0",
    lifespan=lifespan
)


# ============================================================================
# MIDDLEWARE - Global Request Logging
# ============================================================================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests with raw body"""
    logger.info(f"📥 {request.method} {request.url.path} from {request.client.host}")
    logger.info(f"   Headers: {dict(request.headers)}")
    
    # Log raw request body for debugging GUVI format issues
    if request.method == "POST":
        body = await request.body()
        logger.info(f"🔍 Raw Request Body: {body.decode('utf-8')}")
        # Important: Store body for later use since it can only be read once
        async def receive():
            return {"type": "http.request", "body": body}
        request._receive = receive
    
    response = await call_next(request)
    return response


# ============================================================================
# API KEY VERIFICATION (Flexible, Case-Insensitive)
# ============================================================================

async def verify_api_key(
    x_api_key: Optional[str] = Header(None),
    X_API_KEY: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None),
    api_key: Optional[str] = Query(None)
):
    """Flexible API key verification - checks multiple headers and query params"""
    provided_key = x_api_key or X_API_KEY or authorization or api_key
    expected_key = os.getenv("API_KEY", "team_recursives")
    
    if not provided_key:
        logger.error("❌ Missing API key")
        raise HTTPException(status_code=401, detail="Missing API key")
    
    if provided_key != expected_key:
        logger.error(f"❌ Invalid API key: {provided_key}")
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return provided_key


# ============================================================================
# MAIN HONEYPOT ENDPOINT
# ============================================================================

@app.post("/honeypot", response_model=HoneypotResponse)
async def honeypot_endpoint(
    request: HoneypotRequest,
    api_key: str = Header(None, alias="x-api-key")
):
    """
    Main honeypot endpoint - Single execution flow:
    1. Check if callback already sent → 410 Gone
    2. Check timeout → trigger callback if exceeded
    3. Detect scam (hard rules → LLM)
    4. Extract intelligence from ALL messages
    5. If intel found → send callback → mark closed
    6. Generate reply (engage if scam, neutral if not)
    7. Return 200 OK with reply
    """
    session_id = request.sessionId
    current_time = datetime.now(timezone.utc)
    
    # Initialize message count for new session
    if session_id not in message_counts:
        message_counts[session_id] = 0
    
    logger.info(f"\n{'='*80}")
    logger.info(f"📨 New message for session: {session_id}")
    logger.info(f"   Message: {request.message.text}")
    logger.info(f"   History length: {len(request.conversationHistory)}")
    
    # Increment count for scammer message received
    message_counts[session_id] += 1
    logger.info(f"   Messages so far: {message_counts[session_id]} (including this scammer message)")
    
    try:
        # ====================================================================
        # STEP 1: Check if callback already sent (session closed)
        # ====================================================================
        if session_id in callback_sent_sessions:
            logger.warning(f"⛔ Session {session_id} already closed (callback sent)")
            return JSONResponse(
                status_code=410,
                content={"status": "success"}
            )
        
        # ====================================================================
        # STEP 2: Detect scam (hard rules FIRST, then LLM)
        # ====================================================================
        detection_result = scam_detector.analyze_message(
            request.message.text,
            request.conversationHistory
        )
        
        logger.info(f"🔍 Detection result:")
        logger.info(f"   Is scam: {detection_result.is_scam}")
        logger.info(f"   Confidence: {detection_result.confidence}")
        logger.info(f"   Type: {detection_result.scam_type}")
        logger.info(f"   Reasoning: {detection_result.reasoning}")
        
        # ====================================================================
        # STEP 3: Check timeout (ONLY for scam sessions)
        # Non-scam sessions: NO timeout tracking, NO callback, stay OPEN
        # Scam sessions: Track time, can trigger timeout callback
        # ====================================================================
        timeout_triggered = False
        if detection_result.is_scam and detection_result.confidence >= 0.7:
            # Check timeout for scam sessions
            if session_id in last_message_time:
                time_since_last = (current_time - last_message_time[session_id]).total_seconds()
                logger.info(f"⏱  Time since last message: {time_since_last:.1f}s")
                
                if time_since_last > MESSAGE_TIMEOUT_SECONDS:
                    logger.info(f"⏰ TIMEOUT TRIGGERED ({MESSAGE_TIMEOUT_SECONDS}s exceeded for scam session)")
                    timeout_triggered = True
            
            # Update last message time ONLY for scam sessions
            last_message_time[session_id] = current_time
        else:
            # Non-scam: Don't track time, no timeout logic applies
            logger.info("💬 Non-scam message: No timeout tracking, session stays open")
        
        # ====================================================================
        # STEP 4: Extract intelligence from ALL messages
        # ====================================================================
        extracted_intel = intelligence_extractor.extract_from_conversation(
            request.message,
            request.conversationHistory
        )
        
        has_real_intel = intelligence_extractor.has_real_intelligence(extracted_intel)
        logger.info(f"🔎 Real intelligence found: {has_real_intel}")
        
        # ====================================================================
        # STEP 5: Determine if callback should be sent
        # Callback ONLY when: Scam confirmed AND (Real intel OR Timeout)
        # ====================================================================
        should_send_callback = False
        callback_reason = ""
        
        # Only send callback if scam is confirmed (confidence >= 0.7)
        if detection_result.is_scam and detection_result.confidence >= 0.7:
            if has_real_intel:
                should_send_callback = True
                callback_reason = "Scam confirmed + Real intelligence extracted"
            elif timeout_triggered:
                should_send_callback = True
                callback_reason = f"Scam confirmed + Timeout ({MESSAGE_TIMEOUT_SECONDS}s) reached"
        
        # ====================================================================
        # STEP 6: Send callback if triggered
        # ====================================================================
        if should_send_callback:
            logger.info(f"📤 CALLBACK TRIGGERED: {callback_reason}")
            
            # Use actual tracked message count
            # This is the count BEFORE we send the reply (if we were to send one)
            # Since callback is sent, no reply will be sent, so count stays as is
            total_messages = message_counts[session_id]
            
            # Build callback payload
            callback_payload = CallbackPayload(
                sessionId=session_id,
                scamDetected=detection_result.is_scam,
                totalMessagesExchanged=total_messages,
                extractedIntelligence=extracted_intel,
                agentNotes=detection_result.reasoning
            )
            
            # Mark session as closed BEFORE sending (prevent race conditions)
            callback_sent_sessions.add(session_id)
            
            # Send callback
            callback_success = await CallbackService.send_final_result(callback_payload)
            
            if callback_success:
                logger.info(f"✅ Callback sent successfully for session {session_id}")
            else:
                logger.error(f"❌ Callback failed for session {session_id}")
            
            # Return 410 Gone (session closed)
            return JSONResponse(
                status_code=410,
                content={"status": "success"}
            )
        
        # ====================================================================
        # STEP 7: Generate reply (no callback sent yet, keep conversation going)
        # ====================================================================
        if detection_result.is_scam and detection_result.confidence >= 0.7:
            # Scam detected - engage with AI agent
            logger.info("🤖 Generating AI agent reply (scam engagement)")
            reply_text = conversation_agent.generate_reply(
                scammer_message=request.message.text,
                scam_type=detection_result.scam_type or "unknown",
                conversation_history=request.conversationHistory
            )
        else:
            # Not a scam (or low confidence) - neutral response
            logger.info("💬 Generating neutral reply (non-scam)")
            reply_text = conversation_agent.generate_neutral_reply()
        
        # Increment count for agent reply that we're about to send
        message_counts[session_id] += 1
        logger.info(f"   Total messages after reply: {message_counts[session_id]}")
        
        # ====================================================================
        # STEP 8: Return response (200 OK with reply)
        # ====================================================================
        logger.info(f"✅ Responding with: {reply_text}")
        logger.info(f"{'='*80}\n")
        
        return HoneypotResponse(
            status="success",
            reply=reply_text
        )
    
    except Exception as e:
        logger.error(f"❌ Unexpected error in honeypot endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Agentic Honey-Pot",
        "version": "2.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Agentic Honey-Pot for Scam Detection",
        "version": "2.0.0",
        "endpoints": {
            "honeypot": "POST /honeypot",
            "health": "GET /health"
        }
    }
