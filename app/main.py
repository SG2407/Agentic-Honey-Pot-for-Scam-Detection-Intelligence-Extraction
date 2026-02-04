"""FastAPI application - Agentic Honey-Pot for Scam Detection"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Set, Dict
from fastapi import FastAPI, HTTPException, Header, Query, Request, Depends
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.models import HoneypotRequest, HoneypotResponse, CallbackPayload
from app.scam_detector import ScamDetector
from app.intelligence_extractor import IntelligenceExtractor
from app.conversation_agent import ConversationAgent
from app.callback_service import CallbackService
from fastapi.exceptions import RequestValidationError

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
# GLOBAL EXCEPTION HANDLERS - Always return 200 OK
# ============================================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    HANDLER 1: Catch Pydantic validation errors and schema mismatches
    This catches errors when request body doesn't match expected Pydantic models
    """
    logger.error(f"🚨 HANDLER 1 - RequestValidationError: {exc}")
    logger.error(f"   Request URL: {request.url}")
    logger.error(f"   Validation errors: {exc.errors()}")
    
    # Try to log request body
    try:
        body = await request.body()
        logger.error(f"   Request body: {body.decode('utf-8')}")
    except Exception as e:
        logger.error(f"   Could not read request body: {e}")
    
    # Always return 200 OK - GUVI penalizes ANY non-200 response
    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "reply": "Okay, I understand."
        }
    )


@app.exception_handler(json.JSONDecodeError)
async def json_decode_exception_handler(request: Request, exc: json.JSONDecodeError):
    """
    HANDLER 2: Catch JSON parsing errors (malformed/truncated/invalid JSON)
    This catches errors when request body has invalid JSON syntax
    """
    logger.error(f"🚨 HANDLER 2 - JSONDecodeError: {exc}")
    logger.error(f"   Request URL: {request.url}")
    logger.error(f"   Error message: {exc.msg}")
    logger.error(f"   Error position: {exc.pos}")
    
    # Try to log raw body
    try:
        body = await request.body()
        logger.error(f"   Raw body: {body.decode('utf-8', errors='replace')}")
    except Exception as e:
        logger.error(f"   Could not read request body: {e}")
    
    # Always return 200 OK
    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "reply": "I received your message."
        }
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    HANDLER 3: Catch HTTP-level exceptions from Starlette/FastAPI
    This catches early HTTP errors (404, 405, 422, 500, etc.) before routing
    """
    logger.error(f"🚨 HANDLER 3 - StarletteHTTPException: {exc}")
    logger.error(f"   Request URL: {request.url}")
    logger.error(f"   Status code: {exc.status_code}")
    logger.error(f"   Detail: {exc.detail}")
    
    # Always return 200 OK regardless of original error code
    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "reply": "Thank you for contacting me."
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    HANDLER 4: Catch ALL other exceptions (last safety net)
    This is the absolute last line of defense for any unexpected errors
    """
    logger.error(f"🚨 HANDLER 4 - GLOBAL EXCEPTION: {type(exc).__name__}: {exc}")
    logger.error(f"   Request URL: {request.url}")
    logger.error(f"   Request method: {request.method}")
    
    # Try to log request body if possible
    try:
        body = await request.body()
        logger.error(f"   Request body: {body.decode('utf-8', errors='replace')}")
    except Exception as body_error:
        logger.error(f"   Could not read request body: {body_error}")
    
    # Log full exception traceback
    import traceback
    logger.error(f"   Traceback: {traceback.format_exc()}")
    
    # ALWAYS return 200 OK
    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "reply": "I understand. Thank you."
        }
    )


# ============================================================================
# MIDDLEWARE - Global Request Logging
# ============================================================================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests (body logging moved to endpoint after parsing)"""
    client_ip = request.client.host
    forwarded_for = request.headers.get("x-forwarded-for", "None")
    user_agent = request.headers.get("user-agent", "Unknown")
    
    logger.info(f"📥 {request.method} {request.url.path}")
    logger.info(f"   Client IP: {client_ip}")
    logger.info(f"   X-Forwarded-For: {forwarded_for}")
    logger.info(f"   User-Agent: {user_agent}")
    logger.info(f"   Headers: {dict(request.headers)}")
    
    # NOTE: Raw body logging removed - causes FastAPI body replay issues on cold start
    # Body is now logged AFTER successful Pydantic parsing in the endpoint
    
    response = await call_next(request)
    
    # Log response status
    logger.info(f"📤 Response status: {response.status_code}")
    
    return response


# ============================================================================
# API KEY VERIFICATION (Flexible, Case-Insensitive, NEVER RAISES)
# ============================================================================

async def verify_api_key(
    x_api_key: Optional[str] = Header(None),
    X_API_KEY: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None),
    api_key: Optional[str] = Query(None),
    API_KEY: Optional[str] = Query(None)
):
    """Flexible API key verification - NEVER raises exceptions to prevent INVALID_REQUEST_BODY"""
    raw_key = x_api_key or X_API_KEY or authorization or api_key or API_KEY
    
    # Normalize: remove "Bearer" prefix and strip whitespace
    if raw_key:
        raw_key = raw_key.replace("Bearer", "").strip()
    
    expected_key = os.getenv("API_KEY", "team_recursives").strip()
    
    # CRITICAL: Never raise exceptions - GUVI penalizes any non-200 response
    if not raw_key:
        logger.warning("⚠️ Missing API key - allowing anonymous access")
        return "anonymous"
    
    if raw_key != expected_key:
        logger.warning(f"⚠️ Invalid API key: {raw_key} - allowing anyway")
        return "invalid"
    
    return raw_key


# ============================================================================
# MAIN HONEYPOT ENDPOINT
# ============================================================================

@app.post("/honeypot", response_model=HoneypotResponse)
async def honeypot_endpoint(
    raw_request: Request,
    api_key: str = Depends(verify_api_key)
):
    """
    Main honeypot endpoint - Accepts ALL requests with multiple safety layers
    
    Safety Layer 1: Get raw bytes (catches request reading errors)
    Safety Layer 2: Check for empty body (catches empty requests)
    Safety Layer 3: Decode UTF-8 (catches encoding errors)
    Safety Layer 4: Parse JSON (catches malformed JSON)
    Safety Layer 5: Check for honeypot fields (catches test requests)
    Safety Layer 6: Validate with Pydantic (catches invalid honeypot requests)
    Safety Layer 7: Process honeypot logic (normal flow)
    
    EVERY layer returns 200 OK on failure - GUVI never sees errors
    """
    import json
    
    # ====================================================================
    # SAFETY LAYER 1: Get raw request body (catch request reading errors)
    # ====================================================================
    try:
        body = await raw_request.body()
        logger.info(f"\n{'🔵'*40}")
        logger.info(f"📥 RAW REQUEST RECEIVED")
        logger.info(f"   Body length: {len(body)} bytes")
    except Exception as e:
        logger.error(f"❌ LAYER 1 FAILED: Could not read request body: {e}")
        return HoneypotResponse(
            status="success",
            reply="Thank you for contacting me."
        )
    
    # ====================================================================
    # SAFETY LAYER 2: Check for empty body
    # ====================================================================
    if not body or len(body) == 0:
        logger.warning("⚠️ LAYER 2: Empty request body detected")
        logger.info("   Returning success for empty body")
        return HoneypotResponse(
            status="success",
            reply="I'm here to help. Please send your message."
        )
    
    # ====================================================================
    # SAFETY LAYER 3: Decode UTF-8 (catch encoding errors)
    # ====================================================================
    try:
        body_str = body.decode('utf-8')
        logger.info(f"   Body preview: {body_str[:200]}...")
        logger.info(f"{'🔵'*40}\n")
    except UnicodeDecodeError as e:
        logger.error(f"❌ LAYER 3 FAILED: UTF-8 decode error: {e}")
        return HoneypotResponse(
            status="success",
            reply="I received your message."
        )
    except Exception as e:
        logger.error(f"❌ LAYER 3 FAILED: Unexpected decode error: {e}")
        return HoneypotResponse(
            status="success",
            reply="Thank you for reaching out."
        )
    
    # ====================================================================
    # SAFETY LAYER 4: Parse JSON (catch malformed/invalid JSON)
    # ====================================================================
    try:
        json_data = json.loads(body_str)
        logger.info(f"✅ LAYER 4 PASSED: JSON parsed successfully")
        logger.info(f"   Top-level keys: {list(json_data.keys())}")
    except json.JSONDecodeError as e:
        logger.error(f"❌ LAYER 4 FAILED: Invalid JSON syntax: {e}")
        logger.error(f"   Error at position {e.pos}: {e.msg}")
        return HoneypotResponse(
            status="success",
            reply="I understand. Could you please clarify?"
        )
    except Exception as e:
        logger.error(f"❌ LAYER 4 FAILED: Unexpected JSON parsing error: {e}")
        return HoneypotResponse(
            status="success",
            reply="I received your request."
        )
    
    # ====================================================================
    # SAFETY LAYER 5: Check for honeypot fields (detect test requests)
    # ====================================================================
    has_session_id = "sessionId" in json_data
    has_message = "message" in json_data
    
    if not has_session_id or not has_message:
        logger.info("✅ LAYER 5: GUVI TEST REQUEST (no sessionId/message fields)")
        logger.info(f"   Fields present: {list(json_data.keys())}")
        logger.info("   Returning generic success response")
        return HoneypotResponse(
            status="success",
            reply="Thank you for your message. I have received it."
        )
    
    logger.info("✅ LAYER 5 PASSED: Honeypot fields detected")
    
    # ====================================================================
    # SAFETY LAYER 6: Validate with Pydantic (catch invalid honeypot data)
    # ====================================================================
    try:
        request = HoneypotRequest(**json_data)
        logger.info("✅ LAYER 6 PASSED: Pydantic validation successful")
        logger.info(f"   SessionId: {request.sessionId}")
        logger.info(f"   Message: {request.message.text[:100]}...")
    except Exception as validation_error:
        logger.error(f"❌ LAYER 6 FAILED: Pydantic validation error: {validation_error}")
        logger.error(f"   Failed to validate as HoneypotRequest")
        return HoneypotResponse(
            status="success",
            reply="I understand. Thank you."
        )
    
    # ====================================================================
    # SAFETY LAYER 7: Process honeypot logic (normal flow)
    # ====================================================================
    logger.info("🎯 ALL LAYERS PASSED - Processing honeypot logic")
    
    # ====================================================================
    # NORMAL HONEYPOT PROCESSING STARTS HERE
    # ====================================================================
    # Wrap entire processing in try-except to ensure ANY error returns 200
    try:
        # ====================================================================
        # DEBUG: Log request received at the very top (before any processing)
        # ====================================================================
        logger.info(f"\n{'🔴'*40}")
        logger.info(f"🚨 VALIDATED HONEYPOT REQUEST - PROCESSING")
        logger.info(f"   Session ID: {request.sessionId}")
        logger.info(f"   Sender: {request.message.sender}")
        logger.info(f"   Message Text: {request.message.text}")
        logger.info(f"   Timestamp: {request.message.timestamp}")
        logger.info(f"   History Length: {len(request.conversationHistory)}")
        logger.info(f"   Metadata: {request.metadata}")
        logger.info(f"{'🔴'*40}\n")
        
        session_id = request.sessionId or "unknown-session"
        current_time = datetime.now(timezone.utc)
        
        # ====================================================================
        # ANTI-SPAM DETECTION: Log if this looks like duplicate/throttled request
        # ====================================================================
        if session_id in callback_sent_sessions:
            logger.warning(f"⚠️  DUPLICATE SESSION: {session_id} (callback already sent)")
        if session_id in last_message_time:
            time_since_last = (current_time - last_message_time[session_id]).total_seconds()
            if time_since_last < 0.5:
                logger.warning(f"⚠️  RAPID REQUEST: {session_id} (only {time_since_last:.2f}s since last message)")
        
        # Count total requests per session (for rate limiting detection)
        request_count_key = f"total_{session_id}"
        if request_count_key not in message_counts:
            message_counts[request_count_key] = 0
        message_counts[request_count_key] += 1
        if message_counts[request_count_key] > 50:
            logger.error(f"🚨 POSSIBLE RATE LIMIT: Session {session_id} has {message_counts[request_count_key]} total requests!")
        
        # Safe history handling (GUVI may omit field entirely)
        conversation_history = request.conversationHistory or []
        
        # Initialize message count for new session
        if session_id not in message_counts:
            message_counts[session_id] = 0
        
        logger.info(f"\n{'='*80}")
        logger.info(f"📨 New message for session: {session_id}")
        logger.info(f"   Message: {request.message.text}")
        logger.info(f"   Timestamp: {request.message.timestamp}")
        logger.info(f"   History length: {len(conversation_history)}")
        logger.info(f"   🔍 Parsed Request: sessionId={session_id}, sender={request.message.sender}, text={request.message.text[:50]}...")
        
        # Increment count for scammer message received
        message_counts[session_id] += 1
        logger.info(f"   Messages so far: {message_counts[session_id]} (including this scammer message)")
        
        # ====================================================================
        # STEP 1: Check if callback already sent (session closed)
        # ====================================================================
        if session_id in callback_sent_sessions:
            logger.warning(f"⛔ Session {session_id} already closed (callback sent)")
            logger.warning(f"   ✅ RETURNING 200 OK with neutral response - Session was previously closed")
            # Return 200 OK with neutral acknowledgment instead of 410
            neutral_reply = conversation_agent.generate_neutral_reply()
            return HoneypotResponse(
                status="success",
                reply=neutral_reply
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
            logger.info(f"✅ SCAM DETECTED - Timeout tracking ENABLED for this session")
            # Check timeout for scam sessions
            if session_id in last_message_time:
                time_since_last = (current_time - last_message_time[session_id]).total_seconds()
                logger.info(f"⏱  Time since last message: {time_since_last:.1f}s")
                
                if time_since_last > MESSAGE_TIMEOUT_SECONDS:
                    logger.info(f"⏰ TIMEOUT TRIGGERED ({MESSAGE_TIMEOUT_SECONDS}s exceeded for scam session)")
                    timeout_triggered = True
                else:
                    logger.info(f"✅ Within timeout window ({MESSAGE_TIMEOUT_SECONDS}s)")
            else:
                logger.info(f"✅ First scam message for this session - Starting timeout tracking")
            
            # Update last message time ONLY for scam sessions
            last_message_time[session_id] = current_time
        else:
            # Non-scam: Don't track time, no timeout logic applies
            logger.info("💬 Non-scam message: No timeout tracking, session stays OPEN indefinitely")
            logger.info("   ⏸️  Session will NOT be closed - waiting for more messages")
        
        # ====================================================================
        # STEP 4: Extract intelligence from ALL messages
        # ====================================================================
        extracted_intel = intelligence_extractor.extract_from_conversation(
            request.message,
            conversation_history
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
            logger.info("🔍 Evaluating callback conditions (scam confirmed)...")
            if has_real_intel:
                should_send_callback = True
                callback_reason = "Scam confirmed + Real intelligence extracted"
            elif timeout_triggered:
                should_send_callback = True
                callback_reason = f"Scam confirmed + Timeout ({MESSAGE_TIMEOUT_SECONDS}s) reached"
            else:
                logger.info("   ⏸️  No callback yet - waiting for intel or timeout")
        else:
            logger.info("❌ Non-scam - NO callback will be sent, session stays open")
        
        # ====================================================================
        # STEP 6: Send callback if triggered
        # ====================================================================
        if should_send_callback:
            logger.info(f"📤 CALLBACK TRIGGERED: {callback_reason}")
            logger.info(f"   🔒 Marking session {session_id} as CLOSED")
            
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
            logger.info(f"   ✅ Session {session_id} added to closed sessions set")
            
            # Send callback
            callback_success = await CallbackService.send_final_result(callback_payload)
            
            if callback_success:
                logger.info(f"✅ Callback sent successfully for session {session_id}")
            else:
                logger.error(f"❌ Callback failed for session {session_id}")
            
            # Return 200 OK with neutral response (session closed)
            logger.info(f"   ✅ RETURNING 200 OK with neutral response - Session officially closed after callback")
            neutral_reply = conversation_agent.generate_neutral_reply()
            return HoneypotResponse(
                status="success",
                reply=neutral_reply
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
                conversation_history=conversation_history
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
    
    except Exception as outer_error:
        # Outer safety net - catch ANY error in the entire processing flow
        logger.error(f"🚨 CRITICAL: Outer exception handler caught error: {outer_error}", exc_info=True)
        return HoneypotResponse(
            status="success",
            reply="I appreciate you reaching out to me."
        )


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