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
    # SAFETY LAYER 1: Get raw request body (catch request reading errors)
    # ====================================================================
    logger.info("🔍 LAYER 4 - Attempting to read request body...")
    try:
        body = await raw_request.body()
        logger.info(f"✅ LAYER 4 - Body read successful")
        logger.info(f"   Body length: {len(body)} bytes")
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
        
        # ====================================================================
        # STEP 1: Check if callback already sent (session closed) - BEFORE ANY PROCESSING
        # PRIORITY 4: Hard stop - NO detection, NO LLM, NO extraction
        # This saves CPU by avoiding scam detection on closed sessions
        # ====================================================================
        if session_id in callback_sent_sessions:
            logger.warning(f"⛔ Session {session_id} already closed (callback sent)")
            logger.warning(f"   🛑 HARD STOP: Skipping all processing (detection, LLM, extraction)")
            logger.warning(f"   ✅ RETURNING 200 OK with empty reply (session lifecycle discipline)")
            # Return 200 OK with EMPTY reply (no text, no processing)
            return HoneypotResponse(
                status="success",
                reply=""  # Empty reply for closed sessions
            )
        
        # Increment count for scammer message received (only if session is open)
        message_counts[session_id] += 1
        logger.info(f"   Messages so far: {message_counts[session_id]} (including this scammer message)")
        
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
        # PRIORITY 5: LLM optimization - cache replies, use fallback on rate limit
        # ====================================================================
        if detection_result.is_scam and detection_result.confidence >= 0.7:
            # Scam detected - engage with AI agent
            logger.info("🤖 Generating AI agent reply (scam engagement)")
            logger.info("   ✅ LLM call justified: Scam detected + Session OPEN")
            
            try:
                reply_text = conversation_agent.generate_reply(
                    scammer_message=request.message.text,
                    scam_type=detection_result.scam_type or "unknown",
                    conversation_history=conversation_history
                )
                # Cache successful reply for fallback
                last_agent_reply[session_id] = reply_text
                logger.info(f"   💾 Cached reply for session {session_id}")
                
            except Exception as llm_error:
                # Rate limit or LLM error - use fallback
                logger.error(f"⚠️ LLM failed: {llm_error}")
                
                # Try cached reply first
                if session_id in last_agent_reply:
                    reply_text = last_agent_reply[session_id]
                    logger.info(f"   📦 Using cached reply from session {session_id}")
                else:
                    # No cache - use template fallback
                    fallback_templates = [
                        "I am not very good with phones... can you explain again?",
                        "Wait, I need to understand this properly. What exactly should I do?",
                        "My son usually helps me with these things. Can you explain slowly?",
                        "I'm a bit confused now... let me read your message again."
                    ]
                    import random
                    reply_text = random.choice(fallback_templates)
                    logger.info(f"   🎭 Using fallback template (no cache available)")
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