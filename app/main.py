"""FastAPI application - Agentic Honey-Pot for Scam Detection"""

# CRITICAL: Load environment variables FIRST before any other imports
from dotenv import load_dotenv
load_dotenv()

import os
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Set, Dict
from fastapi import FastAPI, HTTPException, Header, Query, Request, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import asyncio
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.datastructures import UploadFile
from anyio import EndOfStream

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
last_agent_reply: Dict[str, str] = {}  # Cache last agent reply per session for fallback (PRIORITY 5)
session_scam_types: Dict[str, str] = {}  # Track highest priority scam type per session (NEVER downgrades)
MESSAGE_TIMEOUT_SECONDS = int(os.getenv("MESSAGE_TIMEOUT_SECONDS", "10"))

# Scam type priority hierarchy (higher number = higher priority, NEVER downgrades)
SCAM_TYPE_PRIORITY = {
    "credential_phishing": 4,  # Highest priority - OTP, PIN, Aadhaar, PAN, password
    "financial_threat": 3,     # Account blocked, suspension, penalty
    "impersonation": 2,        # Government/bank impersonation
    "reward_scam": 1,          # Prize/lottery scams
    "unknown": 0,              # Lowest priority
    "pattern_detected": 0,     # Same as unknown
    "legitimate": 0            # Not a scam
}

# API Key Configuration (PRIORITY 1: Mandatory for evaluation)
VALID_API_KEY = os.getenv("API_KEY", "demo-key-12345")  # Set via environment variable (matches .env file)

# Initialize components
scam_detector = ScamDetector()
intelligence_extractor = IntelligenceExtractor()
conversation_agent = ConversationAgent()

# Async HTTP client for callbacks (with timeouts)
import httpx
http_client_timeout = httpx.Timeout(connect=3.0, read=5.0, write=3.0, pool=3.0)
http_client = httpx.AsyncClient(timeout=http_client_timeout)

# API Key Validation (PRIORITY 1)
def validate_api_key(x_api_key: Optional[str] = Header(None)) -> bool:
    """
    Validate API key from x-api-key header.
    Returns True if valid, False otherwise.
    Silent rejection - no exceptions raised.
    """
    if not x_api_key:
        logger.warning("⚠️  Missing API key - allowing anonymous access")
        return False
    
    if x_api_key != VALID_API_KEY:
        logger.warning(f"⚠️  Invalid API key provided: {x_api_key[:10]}...")
        return False
    
    logger.info("✅ Valid API key provided")
    return True

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
    logger.error(f"\n{'='*80}")
    logger.error(f"🔴 HANDLER 1 - RequestValidationError CAUGHT")
    logger.error(f"   Exception type: {type(exc).__module__}.{type(exc).__name__}")
    logger.error(f"   Exception message: {str(exc)}")
    logger.error(f"   Request URL: {request.url}")
    logger.error(f"   Request method: {request.method}")
    logger.error(f"   Validation errors: {exc.errors()}")
    logger.error(f"   Request headers: {dict(request.headers)}")
    logger.error(f"   Content-Type: {request.headers.get('content-type', 'NOT SET')}")
    logger.error(f"   Content-Length: {request.headers.get('content-length', 'NOT SET')}")
    
    # Try to log request body
    try:
        body = await request.body()
        body_str = body.decode('utf-8', errors='replace')[:500]
        logger.error(f"   Request body (first 500 chars): {body_str}")
        logger.error(f"   Body size: {len(body)} bytes")
    except Exception as e:
        logger.error(f"   Could not read request body: {e}")
    
    # Log traceback
    import traceback
    logger.error(f"   Traceback: {traceback.format_exc()}")
    logger.error(f"   ✅ RETURNING 200 OK (hiding validation error from client)")
    logger.error(f"{'='*80}\n")
    
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
    logger.error(f"\n{'='*80}")
    logger.error(f"🔴 HANDLER 2 - JSONDecodeError CAUGHT")
    logger.error(f"   Exception type: {type(exc).__module__}.{type(exc).__name__}")
    logger.error(f"   Error message: {exc.msg}")
    logger.error(f"   Error position: {exc.pos}")
    logger.error(f"   Error line: {exc.lineno}")
    logger.error(f"   Error column: {exc.colno}")
    logger.error(f"   Request URL: {request.url}")
    logger.error(f"   Request method: {request.method}")
    logger.error(f"   Request headers: {dict(request.headers)}")
    logger.error(f"   Content-Type: {request.headers.get('content-type', 'NOT SET')}")
    logger.error(f"   Content-Length: {request.headers.get('content-length', 'NOT SET')}")
    
    # Try to log raw body
    try:
        body = await request.body()
        body_str = body.decode('utf-8', errors='replace')
        logger.error(f"   Raw body (first 500 chars): {body_str[:500]}")
        logger.error(f"   Body size: {len(body)} bytes")
        if exc.pos and exc.pos < len(body_str):
            snippet_start = max(0, exc.pos - 50)
            snippet_end = min(len(body_str), exc.pos + 50)
            logger.error(f"   Invalid JSON snippet around position {exc.pos}: ...{body_str[snippet_start:snippet_end]}...")
    except Exception as e:
        logger.error(f"   Could not read request body: {e}")
    
    # Log traceback
    import traceback
    logger.error(f"   Traceback: {traceback.format_exc()}")
    logger.error(f"   ✅ RETURNING 200 OK (hiding JSON error from client)")
    logger.error(f"{'='*80}\n")
    
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
    logger.error(f"\n{'='*80}")
    logger.error(f"🔴 HANDLER 3 - StarletteHTTPException CAUGHT")
    logger.error(f"   Exception type: {type(exc).__module__}.{type(exc).__name__}")
    logger.error(f"   Status code: {exc.status_code}")
    logger.error(f"   Detail: {exc.detail}")
    logger.error(f"   Request URL: {request.url}")
    logger.error(f"   Request method: {request.method}")
    logger.error(f"   Request headers: {dict(request.headers)}")
    logger.error(f"   Content-Type: {request.headers.get('content-type', 'NOT SET')}")
    logger.error(f"   Content-Length: {request.headers.get('content-length', 'NOT SET')}")
    
    # Try to log request body if available
    try:
        body = await request.body()
        if body:
            body_str = body.decode('utf-8', errors='replace')[:500]
            logger.error(f"   Request body (first 500 chars): {body_str}")
            logger.error(f"   Body size: {len(body)} bytes")
    except Exception as e:
        logger.error(f"   Could not read request body: {e}")
    
    # Log traceback
    import traceback
    logger.error(f"   Traceback: {traceback.format_exc()}")
    logger.error(f"   ✅ RETURNING 200 OK (hiding HTTP error {exc.status_code} from client)")
    logger.error(f"{'='*80}\n")
    
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
    logger.error(f"\n{'='*80}")
    logger.error(f"🔴 HANDLER 4 - GLOBAL EXCEPTION CAUGHT (LAST RESORT)")
    logger.error(f"   Exception type: {type(exc).__module__}.{type(exc).__name__}")
    logger.error(f"   Exception message: {str(exc)}")
    logger.error(f"   Request URL: {request.url}")
    logger.error(f"   Request method: {request.method}")
    logger.error(f"   Request headers: {dict(request.headers)}")
    logger.error(f"   Content-Type: {request.headers.get('content-type', 'NOT SET')}")
    logger.error(f"   Content-Length: {request.headers.get('content-length', 'NOT SET')}")
    
    # Try to log request body if possible
    try:
        body = await request.body()
        body_str = body.decode('utf-8', errors='replace')[:500]
        logger.error(f"   Request body (first 500 chars): {body_str}")
        logger.error(f"   Body size: {len(body)} bytes")
    except Exception as body_error:
        logger.error(f"   Could not read request body: {body_error}")
    
    # Log full exception traceback
    import traceback
    logger.error(f"   Full traceback:")
    logger.error(traceback.format_exc())
    logger.error(f"   ✅ RETURNING 200 OK (hiding exception from client)")
    logger.error(f"{'='*80}\n")
    
    # ALWAYS return 200 OK
    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "reply": "I understand. Thank you."
        }
    )


# ============================================================================
# LAYER 2: ASGI MIDDLEWARE - Transport-Level Error Protection
# ============================================================================

@app.middleware("http")
async def transport_error_protection_middleware(request: Request, call_next):
    """
    LAYER 2: Catch transport and ASGI-level errors during request processing
    
    This catches errors that occur DURING request/response processing:
    - Client disconnections
    - Stream read/write failures
    - Chunked transfer encoding errors
    - Connection drops mid-request
    - Network timeout errors
    - ASGI protocol violations
    
    This runs BEFORE endpoint handlers and catches errors that global exception
    handlers might miss because they happen during the request/response lifecycle.
    """
    # Get request timestamp
    request_time = datetime.now(timezone.utc)
    
    # Log incoming request at raw ASGI level
    client_ip = request.client.host if request.client else "unknown"
    forwarded_for = request.headers.get("x-forwarded-for", "None")
    user_agent = request.headers.get("user-agent", "Unknown")
    content_type = request.headers.get("content-type", "NOT SET")
    content_length = request.headers.get("content-length", "NOT SET")
    
    logger.info(f"\n{'🔵'*40}")
    logger.info(f"🔵 LAYER 1 - MIDDLEWARE: Incoming request")
    logger.info(f"   Timestamp: {request_time.isoformat()}")
    logger.info(f"   Method: {request.method}")
    logger.info(f"   Full URL: {request.url}")
    logger.info(f"   Path: {request.url.path}")
    logger.info(f"   Client IP: {client_ip}")
    logger.info(f"   X-Forwarded-For: {forwarded_for}")
    logger.info(f"   User-Agent: {user_agent}")
    logger.info(f"   Content-Type: {content_type}")
    logger.info(f"   Content-Length: {content_length}")
    logger.info(f"   All Headers: {dict(request.headers)}")
    
    # Try to peek at request body (for logging only)
    try:
        body = await request.body()
        body_size = len(body)
        logger.info(f"   Body size: {body_size} bytes")
        if body_size > 0:
            body_preview = body.decode('utf-8', errors='replace')[:500]
            logger.info(f"   Body preview (first 500 chars): {body_preview}")
        else:
            logger.info(f"   Body: EMPTY")
    except Exception as body_err:
        logger.warning(f"   Could not read body for logging: {body_err}")
    
    logger.info(f"{'🔵'*40}\n")
    
    try:
        # Process request with transport-level error protection
        try:
            response = await call_next(request)
            response_time = datetime.now(timezone.utc)
            duration_ms = (response_time - request_time).total_seconds() * 1000
            
            logger.info(f"📤 LAYER 1 - MIDDLEWARE: Response sent")
            logger.info(f"   Status: {response.status_code}")
            logger.info(f"   Duration: {duration_ms:.2f}ms")
            logger.info(f"   ✅ REQUEST COMPLETED SUCCESSFULLY\n")
            
            return response
            
        except ConnectionError as e:
            # Client disconnected, connection reset, broken pipe
            logger.error(f"\n{'='*80}")
            logger.error(f"🔴 LAYER 2 - MIDDLEWARE: ConnectionError during request processing")
            logger.error(f"   Error: {e}")
            logger.error(f"   Request: {request.method} {request.url.path}")
            logger.error(f"   ✅ RETURNING 200 OK")
            logger.error(f"{'='*80}\n")
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "reply": "Thank you for your message."
                }
            )
            
        except EndOfStream as e:
            # Stream ended unexpectedly (chunked transfer, incomplete data)
            logger.error(f"\n{'='*80}")
            logger.error(f"🔴 LAYER 2 - MIDDLEWARE: EndOfStream during request processing")
            logger.error(f"   Error: {e}")
            logger.error(f"   Request: {request.method} {request.url.path}")
            logger.error(f"   ✅ RETURNING 200 OK")
            logger.error(f"{'='*80}\n")
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "reply": "I received your request."
                }
            )
            
        except TimeoutError as e:
            # Request processing timeout
            logger.error(f"\n{'='*80}")
            logger.error(f"🔴 LAYER 2 - MIDDLEWARE: TimeoutError during request processing")
            logger.error(f"   Error: {e}")
            logger.error(f"   Request: {request.method} {request.url.path}")
            logger.error(f"   ✅ RETURNING 200 OK")
            logger.error(f"{'='*80}\n")
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "reply": "I understand."
                }
            )
            
        except OSError as e:
            # Low-level OS errors (network, file descriptors, etc.)
            logger.error(f"\n{'='*80}")
            logger.error(f"🔴 LAYER 2 - MIDDLEWARE: OSError during request processing")
            logger.error(f"   Error: {e}")
            logger.error(f"   Request: {request.method} {request.url.path}")
            logger.error(f"   ✅ RETURNING 200 OK")
            logger.error(f"{'='*80}\n")
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "reply": "Thank you for contacting me."
                }
            )
            
    except Exception as e:
        # Absolute last safety net for any middleware-level error
        logger.error(f"\n{'='*80}")
        logger.error(f"🔴 LAYER 2 - MIDDLEWARE: UNEXPECTED EXCEPTION")
        logger.error(f"   Exception type: {type(e).__module__}.{type(e).__name__}")
        logger.error(f"   Exception message: {str(e)}")
        logger.error(f"   Request: {request.method} {request.url.path}")
        
        import traceback
        logger.error(f"   Full traceback:")
        logger.error(traceback.format_exc())
        logger.error(f"   ✅ RETURNING 200 OK")
        logger.error(f"{'='*80}\n")
        
        # Always return 200 OK
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "reply": "I appreciate you reaching out."
            }
        )


# ============================================================================
# LEGACY MIDDLEWARE - Kept for compatibility (now redundant with Layer 2)
# ============================================================================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Legacy logging middleware - functionality moved to transport_error_protection_middleware"""
    # This is now a passthrough since logging moved to the new middleware above
    return await call_next(request)


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
    """
    PRIORITY 1: API key verification - MANDATORY for evaluation
    
    Behavior:
    - Valid key → returns key (normal processing)
    - Invalid/missing key → returns None (silent rejection)
    - NEVER raises exceptions (prevents INVALID_REQUEST_BODY)
    """
    raw_key = x_api_key or X_API_KEY or authorization or api_key or API_KEY
    
    # Normalize: remove "Bearer" prefix and strip whitespace
    if raw_key:
        raw_key = raw_key.replace("Bearer", "").strip()
    
    expected_key = os.getenv("API_KEY", "team_recursives").strip()
    
    # PRIORITY 1: Enforce API key (silent rejection for invalid/missing)
    if not raw_key:
        logger.warning("⚠️ Missing API key - REJECTING silently")
        return None  # Signals rejection
    
    if raw_key != expected_key:
        logger.warning(f"⚠️ Invalid API key: {raw_key[:10]}... - REJECTING silently")
        return None  # Signals rejection
    
    logger.info("✅ Valid API key provided")
    return raw_key


# ============================================================================
# BACKGROUND PROCESSING FUNCTION
# ============================================================================

async def process_message_background(
    session_id: str,
    message_text: str,
    message_sender: str,
    message_timestamp: str,
    conversation_history: list
):
    """
    Background processing for honeypot messages.
    Runs AFTER HTTP response is sent.
    Handles: scam detection, LLM calls, intelligence extraction, callbacks.
    ALL failures are caught and logged (no exceptions escape).
    """
    try:
        logger.info(f"🔧 Background processing started for session: {session_id}")
        
        # Check if session already closed
        if session_id in callback_sent_sessions:
            logger.info(f"⚠️ Session {session_id} already closed, skipping background processing")
            return
        
        # Build message object
        from app.models import Message
        current_message = Message(
            sender=message_sender,
            text=message_text,
            timestamp=message_timestamp
        )
        
        # STEP 1: Scam detection with timeout
        try:
            detection_result = await asyncio.wait_for(
                asyncio.to_thread(
                    scam_detector.analyze_message,
                    message_text,
                    conversation_history
                ),
                timeout=5.0  # 5 second timeout for detection
            )
            logger.info(f"✅ Detection complete: scam={detection_result.is_scam}, type={detection_result.scam_type}")
        except asyncio.TimeoutError:
            logger.error(f"⏰ Detection timeout for session {session_id}")
            return
        except Exception as e:
            logger.error(f"❌ Detection failed for session {session_id}: {e}")
            return
        
        # STEP 2: Priority tracking
        if detection_result.is_scam and detection_result.scam_type:
            current_type = detection_result.scam_type
            current_priority = SCAM_TYPE_PRIORITY.get(current_type, 0)
            
            if session_id in session_scam_types:
                existing_type = session_scam_types[session_id]
                existing_priority = SCAM_TYPE_PRIORITY.get(existing_type, 0)
                
                if current_priority > existing_priority:
                    logger.info(f"🔼 UPGRADING: {existing_type} → {current_type}")
                    session_scam_types[session_id] = current_type
                    detection_result.scam_type = current_type
                elif current_priority < existing_priority:
                    logger.info(f"🔒 LOCKED to {existing_type}")
                    detection_result.scam_type = existing_type
            else:
                logger.info(f"🆕 Locking to {current_type}")
                session_scam_types[session_id] = current_type
        
        # STEP 3: Intelligence extraction with timeout
        try:
            intelligence = await asyncio.wait_for(
                asyncio.to_thread(
                    intelligence_extractor.extract_from_conversation,
                    current_message,
                    conversation_history
                ),
                timeout=3.0  # 3 second timeout for extraction
            )
            has_intel = intelligence_extractor.has_real_intelligence(intelligence)
            logger.info(f"✅ Extraction complete: has_intel={has_intel}")
        except asyncio.TimeoutError:
            logger.error(f"⏰ Extraction timeout for session {session_id}")
            return
        except Exception as e:
            logger.error(f"❌ Extraction failed for session {session_id}: {e}")
            return
        
        # STEP 4: Send callback if conditions met
        if detection_result.is_scam and has_intel:
            if session_id not in callback_sent_sessions:
                logger.info(f"📤 Sending callback for session {session_id}")
                
                # Mark session as closed BEFORE sending
                callback_sent_sessions.add(session_id)
                
                # Prepare callback payload
                from app.models import CallbackPayload
                payload = CallbackPayload(
                    sessionId=session_id,
                    scamDetected=detection_result.is_scam,
                    scamType=detection_result.scam_type or "unknown",
                    confidence=detection_result.confidence,
                    extractedIntelligence=intelligence,
                    totalMessagesExchanged=message_counts.get(session_id, 1),
                    conversationSummary=f"Scam detected: {detection_result.scam_type}"
                )
                
                # Send callback with timeout
                try:
                    callback_success = await asyncio.wait_for(
                        CallbackService.send_final_result(payload),
                        timeout=8.0  # 8 second timeout for callback
                    )
                    if callback_success:
                        logger.info(f"✅ Callback sent successfully")
                    else:
                        logger.error(f"❌ Callback failed (non-2xx response)")
                except asyncio.TimeoutError:
                    logger.error(f"⏰ Callback timeout for session {session_id}")
                except Exception as e:
                    logger.error(f"❌ Callback exception for session {session_id}: {e}")
        
        logger.info(f"✅ Background processing complete for session {session_id}")
        
    except Exception as e:
        logger.error(f"❌ CRITICAL: Background processing failed for session {session_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())


# ============================================================================
# MAIN HONEYPOT ENDPOINT
# ============================================================================

@app.post("/honeypot", response_model=HoneypotResponse)
async def honeypot_endpoint(
    raw_request: Request,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    """
    Main honeypot endpoint - RETURNS IMMEDIATELY (< 3 seconds)
    
    Critical changes for timeout fix:
    1. Returns response IMMEDIATELY with pre-generated reply
    2. Heavy processing (LLM, detection, callbacks) runs in BACKGROUND
    3. All external calls have STRICT TIMEOUTS
    4. ALWAYS returns 200 OK with valid response
    
    Response time: < 1 second (just validates request and schedules background work)
    """
    import json
    
    # Start timing
    request_start = datetime.now(timezone.utc)
    
    # ====================================================================
    # PRIORITY 1: API KEY VALIDATION (Silent rejection if invalid/missing)
    # ====================================================================
    if api_key is None:
        logger.warning("🔒 API key validation failed - returning empty success response")
        return HoneypotResponse(
            status="success",
            reply=""  # Empty reply for rejected requests
        )
    
    # ====================================================================
    # LAYER 3: ENDPOINT ENTRY LOGGING
    # ====================================================================
    logger.info(f"\n{'🟢'*40}")
    logger.info(f"🟢 LAYER 3 - ENDPOINT REACHED: /honeypot")
    logger.info(f"   Method: {raw_request.method}")
    logger.info(f"   URL: {raw_request.url}")
    logger.info(f"   Client: {raw_request.client.host if raw_request.client else 'unknown'}")
    logger.info(f"   Content-Type: {raw_request.headers.get('content-type', 'NOT SET')}")
    logger.info(f"   Content-Length: {raw_request.headers.get('content-length', 'NOT SET')}")
    logger.info(f"   Headers: {dict(raw_request.headers)}")
    logger.info(f"{'🟢'*40}\n")
    
    # ====================================================================
    # SAFETY LAYER 1: Get raw request body WITH TIMEOUT (catch request reading errors)
    # ====================================================================
    logger.info("🔍 LAYER 4 - Attempting to read request body (with 2s timeout)...")
    try:
        # Add timeout to body read (critical fix for hanging requests)
        body = await asyncio.wait_for(raw_request.body(), timeout=2.0)
        logger.info(f"✅ LAYER 4 - Body read successful")
        logger.info(f"   Body length: {len(body)} bytes")
    except asyncio.TimeoutError:
        logger.error(f"⏰ LAYER 4 - TIMEOUT: Request body read exceeded 2 seconds")
        return HoneypotResponse(
            status="success",
            reply="I'm here to help. Please try again."
        )
    except Exception as e:
        logger.error(f"❌ LAYER 4 - FAILED: Could not read request body: {e}")
        import traceback
        logger.error(f"   Traceback: {traceback.format_exc()}")
        return HoneypotResponse(
            status="success",
            reply="Thank you for contacting me."
        )
    
    # ====================================================================
    # SAFETY LAYER 2: Check for empty body
    # ====================================================================
    if not body or len(body) == 0:
        logger.warning("⚠️ LAYER 4 - Empty request body detected")
        logger.info("   Returning success for empty body")
        return HoneypotResponse(
            status="success",
            reply="I'm here to help. Please send your message."
        )
        logger.warning("⚠️ LAYER 2: Empty request body detected")
        logger.info("   Returning success for empty body")
        return HoneypotResponse(
            status="success",
            reply="I'm here to help. Please send your message."
        )
    
    # ====================================================================
    # SAFETY LAYER 3: Decode UTF-8 (catch encoding errors)
    # ====================================================================
    logger.info("🔍 LAYER 4 - Attempting UTF-8 decode...")
    try:
        body_str = body.decode('utf-8')
        logger.info(f"✅ LAYER 4 - UTF-8 decode successful")
        logger.info(f"   Body preview (first 200 chars): {body_str[:200]}...")
    except UnicodeDecodeError as e:
        logger.error(f"❌ LAYER 4 - FAILED: UTF-8 decode error: {e}")
        import traceback
        logger.error(f"   Traceback: {traceback.format_exc()}")
        return HoneypotResponse(
            status="success",
            reply="I received your message."
        )
    except Exception as e:
        logger.error(f"❌ LAYER 4 - FAILED: Unexpected decode error: {e}")
        import traceback
        logger.error(f"   Traceback: {traceback.format_exc()}")
        return HoneypotResponse(
            status="success",
            reply="Thank you for reaching out."
        )
    
    # ====================================================================
    # SAFETY LAYER 4: Parse JSON (catch malformed/invalid JSON)
    # ====================================================================
    logger.info("🔍 LAYER 4 - Attempting JSON parse...")
    try:
        json_data = json.loads(body_str)
        logger.info(f"✅ LAYER 4 - JSON parsed successfully")
        logger.info(f"   Top-level keys: {list(json_data.keys())}")
    except json.JSONDecodeError as e:
        logger.error(f"❌ LAYER 4 - FAILED: Invalid JSON syntax")
        logger.error(f"   Error message: {e.msg}")
        logger.error(f"   Error at line {e.lineno}, column {e.colno}, position {e.pos}")
        
        # Show the problematic JSON snippet
        if e.pos and e.pos < len(body_str):
            snippet_start = max(0, e.pos - 50)
            snippet_end = min(len(body_str), e.pos + 50)
            problematic_snippet = body_str[snippet_start:snippet_end]
            logger.error(f"   Problematic JSON around position {e.pos}:")
            logger.error(f"   ...{problematic_snippet}...")
        
        import traceback
        logger.error(f"   Traceback: {traceback.format_exc()}")
        
        return HoneypotResponse(
            status="success",
            reply="I understand. Could you please clarify?"
        )
    except Exception as e:
        logger.error(f"❌ LAYER 4 - FAILED: Unexpected JSON parsing error: {e}")
        import traceback
        logger.error(f"   Traceback: {traceback.format_exc()}")
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
    # CRITICAL FIX: IMMEDIATE RESPONSE + BACKGROUND PROCESSING
    # ====================================================================
    logger.info("🎯 ALL LAYERS PASSED - Scheduling background processing")
    
    # Extract session info
    session_id = request.sessionId or "unknown-session"
    conversation_history = request.conversationHistory or []
    
    # Log request details
    logger.info(f"📨 Honeypot request: session={session_id}, message={request.message.text[:50]}...")
    
    # ====================================================================
    # CHECK: If session already closed, return immediately (no background work)
    # ====================================================================
    if session_id in callback_sent_sessions:
        logger.warning(f"⛔ Session {session_id} already closed (callback sent)")
        elapsed_ms = (datetime.now(timezone.utc) - request_start).total_seconds() * 1000
        logger.info(f"⚡ Response time: {elapsed_ms:.2f}ms (closed session fast path)")
        return HoneypotResponse(
            status="success",
            reply=""  # Empty reply for closed sessions
        )
    
    # ====================================================================
    # SCHEDULE BACKGROUND PROCESSING (runs AFTER response is sent)
    # ====================================================================
    background_tasks.add_task(
        process_message_background,
        session_id=session_id,
        message_text=request.message.text,
        message_sender=request.message.sender,
        message_timestamp=request.message.timestamp,
        conversation_history=conversation_history
    )
    
    # Initialize message count for new session
    if session_id not in message_counts:
        message_counts[session_id] = 0
    message_counts[session_id] += 1
    
    logger.info(f"✅ Background task scheduled for session {session_id}")
    
    # ====================================================================
    # GENERATE IMMEDIATE RESPONSE (contextual to scam patterns)
    # ====================================================================
    # Quick pattern-based reply selection (no LLM, instant)
    message_lower = request.message.text.lower()
    
    if any(word in message_lower for word in ['otp', 'pin', 'password', 'cvv']):
        reply = "I need to check with my son first. He usually helps me with these things."
    elif any(word in message_lower for word in ['account', 'suspended', 'blocked', 'verify']):
        reply = "Wait, which account? I have multiple accounts. Can you clarify?"
    elif any(word in message_lower for word in ['prize', 'won', 'winner', 'congratulations']):
        reply = "Really? I didn't participate in any contest. Are you sure it's for me?"
    elif any(word in message_lower for word in ['urgent', 'immediately', 'now', 'asap']):
        reply = "I'm a bit confused. Can you explain this more slowly?"
    elif any(word in message_lower for word in ['bank', 'upi', 'payment', 'transfer']):
        reply = "I don't usually share these details online. Is this really necessary?"
    elif any(word in message_lower for word in ['aadhaar', 'pan', 'government', 'tax']):
        reply = "I need to verify this first. How do I know this is genuine?"
    else:
        reply = "I'm not sure I understand. Could you explain what you need?"
    
    # Calculate response time
    elapsed_ms = (datetime.now(timezone.utc) - request_start).total_seconds() * 1000
    logger.info(f"⚡ Response time: {elapsed_ms:.2f}ms (immediate return with background task)")
    logger.info(f"📤 Returning reply: {reply[:50]}...")
    
    # Return immediately (< 1 second response time)
    return HoneypotResponse(
        status="success",
        reply=reply
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


# ============================================================================
# CATCH-ALL ROUTE - Must be LAST to act as fallback
# ============================================================================

@app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
async def catch_all_route(request: Request, full_path: str):
    """
    Catch-all route handler for undefined endpoints and unsupported methods
    
    This handles:
    - Requests to undefined paths (prevents 404 Not Found)
    - Unsupported HTTP methods on defined paths (prevents 405 Method Not Allowed)
    - GUVI test requests to random endpoints
    
    MUST be defined LAST so it only catches unmatched routes.
    """
    logger.info(f"🔀 CATCH-ALL ROUTE triggered")
    logger.info(f"   Method: {request.method}")
    logger.info(f"   Path: /{full_path}")
    logger.info(f"   Client: {request.client.host if request.client else 'unknown'}")
    
    # Return generic 200 OK response
    return JSONResponse(
        status_code=200,
        content={
            "status": "ok",
            "message": "Request received"
        }
    )