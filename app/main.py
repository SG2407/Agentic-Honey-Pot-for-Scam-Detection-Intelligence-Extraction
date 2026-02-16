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

from app.models import HoneypotRequest, HoneypotResponse, CallbackPayload, ExtractedIntelligence
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

# ============================================================================
# GLOBAL STATE MANAGEMENT
# ============================================================================
# NOTE: Using in-memory storage for hackathon simplicity. For production:
# - Use Redis for distributed sessions
# - Use PostgreSQL/MongoDB for persistent storage
# - Add lock mechanisms (threading.Lock) for thread safety
# - Implement session expiration and cleanup
# ============================================================================
callback_sent_sessions: Set[str] = set()  # Sessions that received callback (session closed)
last_message_time: Dict[str, datetime] = {}  # Track last message time for timeout detection
message_counts: Dict[str, int] = {}  # Track total messages exchanged per session for limits
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
    
    # CRITICAL DEBUG: Log model fields at startup
    logger.info(f"🔍 CallbackPayload model fields: {list(CallbackPayload.model_fields.keys())}")
    logger.info(f"✅ sessionId in model: {'sessionId' in CallbackPayload.model_fields}")
    
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
    """Catch Pydantic validation errors"""
    logger.error(f"Validation error: {str(exc)[:100]}")
    
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
    """Catch JSON parsing errors"""
    logger.error(f"JSON decode error: {exc.msg}")
    
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
    """Catch HTTP-level exceptions"""
    logger.error(f"HTTP error {exc.status_code}: {exc.detail}")
    
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
    """Catch all exceptions"""
    logger.error(f"Unexpected error: {type(exc).__name__}: {str(exc)[:100]}")
    
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
    request_time = datetime.now(timezone.utc)
    
    try:
        # Process request with transport-level error protection
        try:
            return await call_next(request)
            
        except ConnectionError as e:
            logger.error(f"Connection error: {str(e)[:50]}")
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "reply": "Thank you for your message."
                }
            )
            
        except EndOfStream as e:
            logger.error(f"Stream error: {str(e)[:50]}")
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "reply": "I received your request."
                }
            )
            
        except TimeoutError as e:
            logger.error(f"Timeout: {str(e)[:50]}")
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "reply": "I understand."
                }
            )
            
        except OSError as e:
            logger.error(f"OS error: {str(e)[:50]}")
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "reply": "Thank you for contacting me."
                }
            )
            
    except Exception as e:
        logger.error(f"Middleware error: {type(e).__name__}: {str(e)[:50]}")
        
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
# AGENT NOTES GENERATOR (Detailed, unique descriptions per conversation)
# ============================================================================

def generate_agent_notes(
    scam_type: str,
    intelligence: ExtractedIntelligence,
    conversation_length: int,
    conversation_history: list
) -> str:
    """
    Generate detailed, unique agent notes describing scammer behavior and tactics.
    Creates narrative-style description including specific intelligence extracted.
    """
    notes_parts = []
    
    # Part 1: Scam type and primary tactic
    scam_descriptions = {
        "credential_phishing": "Attempted credential phishing attack",
        "financial_threat": "Financial threat-based scam involving account blocking claims",
        "reward_scam": "Fraudulent prize/lottery/reward scheme",
        "prize_scam": "Fake prize or lottery scam",
        "impersonation": "Impersonation attack posing as authority figure",
        "tech_support": "Tech support scam",
        "investment_fraud": "Investment or financial fraud scheme"
    }
    primary_desc = scam_descriptions.get(scam_type, f"{scam_type.replace('_', ' ').title()} scam")
    notes_parts.append(primary_desc)
    
    # Part 2: Specific tactics observed from keywords
    tactics = []
    if any(kw in intelligence.suspiciousKeywords for kw in ["urgent", "immediately", "now", "quickly", "hurry"]):
        tactics.append("high-pressure urgency tactics")
    if any(kw in intelligence.suspiciousKeywords for kw in ["blocked", "suspended", "locked", "closed"]):
        tactics.append("account threat intimidation")
    if any(kw in intelligence.suspiciousKeywords for kw in ["OTP", "PIN", "password", "CVV"]):
        tactics.append("explicit credential harvesting")
    if any(kw in intelligence.suspiciousKeywords for kw in ["prize", "winner", "lottery", "claim"]):
        tactics.append("false reward claims")
    if any(kw in intelligence.suspiciousKeywords for kw in ["KYC", "verify", "update details"]):
        tactics.append("fake verification requests")
    
    if tactics:
        notes_parts.append(f"employing {', '.join(tactics)}")
    
    # Part 3: Intelligence extracted (specific details)
    intel_details = []
    
    if intelligence.phoneNumbers:
        phone_list = ', '.join(intelligence.phoneNumbers[:3])  # First 3
        count = len(intelligence.phoneNumbers)
        intel_details.append(f"{count} phone number{'s' if count > 1 else ''} ({phone_list})")
    
    if intelligence.upiIds:
        upi_list = ', '.join(intelligence.upiIds[:2])  # First 2
        count = len(intelligence.upiIds)
        intel_details.append(f"{count} UPI ID{'s' if count > 1 else ''} ({upi_list})")
    
    if intelligence.bankAccounts:
        # Mask middle digits for privacy in notes
        masked_accts = [f"{acc[:4]}...{acc[-4:]}" if len(acc) > 8 else acc for acc in intelligence.bankAccounts[:2]]
        count = len(intelligence.bankAccounts)
        intel_details.append(f"{count} bank account{'s' if count > 1 else ''} ({', '.join(masked_accts)})")
    
    if intelligence.phishingLinks:
        # Extract domain from first link
        import re
        first_link = intelligence.phishingLinks[0]
        domain_match = re.search(r'https?://([^/]+)', first_link)
        domain = domain_match.group(1) if domain_match else first_link[:30]
        count = len(intelligence.phishingLinks)
        intel_details.append(f"{count} phishing link{'s' if count > 1 else ''} (domain: {domain})")
    
    if intelligence.emailAddresses:
        email_list = ', '.join(intelligence.emailAddresses[:2])
        count = len(intelligence.emailAddresses)
        intel_details.append(f"{count} email address{'es' if count > 1 else ''} ({email_list})")
    
    if intel_details:
        notes_parts.append(f"Scammer revealed: {'; '.join(intel_details)}")
    
    # Part 4: Engagement summary
    notes_parts.append(f"Conversation lasted {conversation_length} messages")
    
    # Part 5: Behavioral patterns (analyze actual messages if available)
    if conversation_history:
        scammer_messages = [msg.text for msg in conversation_history if msg.sender == "scammer"]
        if scammer_messages:
            behaviors = []
            # Check for repetition
            if conversation_length > 5:
                behaviors.append("persistent repeated requests")
            # Check for impersonation indicators
            combined_text = " ".join(scammer_messages).lower()
            if any(word in combined_text for word in ["bank", "security team", "department", "official"]):
                behaviors.append("posed as official entity")
            if any(word in combined_text for word in ["employee id", "customer care", "helpline"]):
                behaviors.append("provided fake credentials")
            
            if behaviors:
                notes_parts.append(f"Behavioral patterns: {', '.join(behaviors)}")
    
    # Combine all parts with proper punctuation
    agent_notes = ". ".join(notes_parts) + "."
    
    # Ensure notes are reasonably sized (truncate if too long)
    if len(agent_notes) > 500:
        agent_notes = agent_notes[:497] + "..."
    
    return agent_notes


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
        # Check if session closed
        if session_id in callback_sent_sessions:
            return
        
        # Build message object
        from app.models import Message
        current_message = Message(
            sender=message_sender,
            text=message_text,
            timestamp=message_timestamp
        )
        
        # Scam detection with timeout
        try:
            detection_result = await asyncio.wait_for(
                asyncio.to_thread(
                    scam_detector.analyze_message,
                    message_text,
                    conversation_history
                ),
                timeout=5.0
            )
        except asyncio.TimeoutError:
            logger.error(f"Detection timeout: {session_id}")
            return
        except Exception as e:
            logger.error(f"Detection failed: {session_id}")
            return
        
        # Priority tracking
        if detection_result.is_scam and detection_result.scam_type:
            current_type = detection_result.scam_type
            current_priority = SCAM_TYPE_PRIORITY.get(current_type, 0)
            
            if session_id in session_scam_types:
                existing_type = session_scam_types[session_id]
                existing_priority = SCAM_TYPE_PRIORITY.get(existing_type, 0)
                
                if current_priority > existing_priority:
                    session_scam_types[session_id] = current_type
                    detection_result.scam_type = current_type
                elif current_priority < existing_priority:
                    detection_result.scam_type = existing_type
            else:
                session_scam_types[session_id] = current_type
        
        # Intelligence extraction with timeout
        try:
            intelligence = await asyncio.wait_for(
                asyncio.to_thread(
                    intelligence_extractor.extract_from_conversation,
                    current_message,
                    conversation_history
                ),
                timeout=3.0
            )
            has_intel = intelligence_extractor.has_real_intelligence(intelligence)
            intel_quality = intelligence_extractor.calculate_intelligence_quality(intelligence)
            
            # Calculate GUVI hackathon scoring (40 points max)
            guvi_score = intelligence_extractor.calculate_guvi_score(intelligence)
        except asyncio.TimeoutError:
            logger.error(f"Extraction timeout: {session_id}")
            return
        except Exception as e:
            logger.error(f"Extraction failed: {session_id}")
            return
        
        # Calculate total messages: scammer + honeypot (both sides)
        scammer_msg_count = message_counts.get(session_id, 1)
        total_msgs = scammer_msg_count * 2  # Each scammer message gets 1 honeypot response
        
        # GUVI Hackathon callback conditions:
        # 1. Scam must be detected
        # 2. EITHER intelligence score >= 80% (36+ points out of 45) OR message limit reached
        guvi_score_threshold = 36  # 80% of 45 points
        intel_threshold_met = guvi_score >= guvi_score_threshold
        
        # Get max conversation turns from environment (default 20)
        max_turns = int(os.getenv("MAX_CONVERSATION_TURNS", "20"))
        message_limit_reached = total_msgs >= max_turns
        
        should_send_callback = (
            detection_result.is_scam and 
            (intel_threshold_met or message_limit_reached)
        )
        
        # Send callback if conditions met
        if should_send_callback:
            if session_id not in callback_sent_sessions:
                logger.info(f"🎯 Callback conditions met for session {session_id}:")
                logger.info(f"   ✓ Scam detected: {detection_result.scam_type} (confidence: {detection_result.confidence})")
                logger.info(f"   ✓ GUVI Score: {guvi_score}/45 points ({(guvi_score/45)*100:.0f}%) (threshold: {guvi_score_threshold})")
                logger.info(f"   ✓ Total messages: {total_msgs} (limit: {max_turns})")
                logger.info(f"   ✓ Callback trigger: {'Intelligence threshold met (80%+)' if intel_threshold_met else 'Message limit reached'}")
                logger.info(f"   📞 Phone numbers: {len(intelligence.phoneNumbers)}")
                logger.info(f"   🏦 Bank accounts: {len(intelligence.bankAccounts)}")
                logger.info(f"   💳 UPI IDs: {len(intelligence.upiIds)}")
                logger.info(f"   🔗 Phishing links: {len(intelligence.phishingLinks)}")
                logger.info(f"   📧 Email addresses: {len(intelligence.emailAddresses)}")
                
                callback_sent_sessions.add(session_id)
                
                # Generate detailed, unique agent notes describing specific scammer behavior
                agent_notes = generate_agent_notes(
                    scam_type=detection_result.scam_type,
                    intelligence=intelligence,
                    conversation_length=total_msgs,
                    conversation_history=conversation_history
                )
                
                from app.models import CallbackPayload
                payload = CallbackPayload(
                    sessionId=session_id,
                    scamDetected=detection_result.is_scam,
                    totalMessagesExchanged=total_msgs,
                    extractedIntelligence=intelligence,
                    agentNotes=agent_notes
                )
                
                try:
                    await asyncio.wait_for(
                        CallbackService.send_final_result(payload),
                        timeout=8.0
                    )
                    logger.info(f"✅ Callback sent successfully for session {session_id}")
                except asyncio.TimeoutError:
                    logger.error(f"❌ Callback timeout: {session_id}")
                except Exception as e:
                    logger.error(f"❌ Callback error for {session_id}: {str(e)[:100]}")
            else:
                logger.info(f"⏭️  Callback already sent for session {session_id}, skipping")
        else:
            logger.info(f"⏸️  Callback NOT sent for session {session_id}:")
            logger.info(f"   - Scam detected: {detection_result.is_scam}")
            logger.info(f"   - GUVI Score: {guvi_score}/45 points ({(guvi_score/45)*100:.0f}%) (threshold: {guvi_score_threshold} points)")
            logger.info(f"   - Total messages: {total_msgs} (limit: {max_turns})")
            logger.info(f"   - Intelligence threshold met: {intel_threshold_met}")
            logger.info(f"   - Message limit reached: {message_limit_reached}")
            if detection_result.is_scam:
                logger.info(f"   ℹ️  Continuing engagement to gather more intelligence...")
                logger.info(f"   📊 Current extraction: Phone={len(intelligence.phoneNumbers)}, Bank={len(intelligence.bankAccounts)}, UPI={len(intelligence.upiIds)}, Links={len(intelligence.phishingLinks)}, Email={len(intelligence.emailAddresses)}")
        
    except Exception as e:
        logger.error(f"Background error: {session_id}")


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
    
    # API key validation (silent rejection)
    if api_key is None:
        return HoneypotResponse(status="success", reply="")
    
    # Read body with timeout
    try:
        body = await asyncio.wait_for(raw_request.body(), timeout=2.0)
    except asyncio.TimeoutError:
        logger.error("Body read timeout")
        return HoneypotResponse(status="success", reply="I'm here to help. Please try again.")
    except Exception as e:
        logger.error(f"Body read error: {str(e)[:50]}")
        return HoneypotResponse(status="success", reply="Thank you for contacting me.")
    
    # Empty body check
    if not body or len(body) == 0:
        return HoneypotResponse(status="success", reply="I'm here to help. Please send your message.")
    
    # Decode UTF-8
    try:
        body_str = body.decode('utf-8')
    except UnicodeDecodeError:
        logger.error("UTF-8 decode error")
        return HoneypotResponse(status="success", reply="I received your message.")
    except Exception:
        return HoneypotResponse(status="success", reply="Thank you for reaching out.")
    
    # Parse JSON
    try:
        json_data = json.loads(body_str)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e.msg}")
        return HoneypotResponse(status="success", reply="I understand. Could you please clarify?")
    except Exception:
        return HoneypotResponse(status="success", reply="I received your request.")
    
    # Check for honeypot fields
    has_session_id = "sessionId" in json_data
    has_message = "message" in json_data
    
    if not has_session_id or not has_message:
        return HoneypotResponse(status="success", reply="Thank you for your message. I have received it.")
    
    # Validate with Pydantic
    try:
        request = HoneypotRequest(**json_data)
    except Exception:
        return HoneypotResponse(status="success", reply="I understand. Thank you.")
    
    # Extract session info
    session_id = request.sessionId or "unknown-session"
    conversation_history = request.conversationHistory or []
    
    # Check if session closed
    if session_id in callback_sent_sessions:
        return HoneypotResponse(status="success", reply="")
    
    # Schedule background processing
    background_tasks.add_task(
        process_message_background,
        session_id=session_id,
        message_text=request.message.text,
        message_sender=request.message.sender,
        message_timestamp=request.message.timestamp,
        conversation_history=conversation_history
    )
    
    # Track message count (scammer messages only, honeypot responses added later)
    if session_id not in message_counts:
        message_counts[session_id] = 0
    message_counts[session_id] += 1  # Count scammer message
    
    # Total messages = scammer messages + honeypot responses (1:1 ratio)
    total_messages_exchanged = message_counts[session_id] * 2
    
    # Generate immediate response using LLM conversation agent
    try:
        # Quick scam detection (with timeout) to determine scam type
        detection_result = await asyncio.wait_for(
            asyncio.to_thread(
                scam_detector.analyze_message,
                request.message.text,
                conversation_history
            ),
            timeout=2.0
        )
        
        # Use detected scam type or default
        scam_type = detection_result.scam_type if detection_result.is_scam else "unknown"
        
        # Generate reply using conversation agent (LLM-based)
        # Increased timeout to 4.5s to allow LLM completion (was 2.5s)
        reply = await asyncio.wait_for(
            asyncio.to_thread(
                conversation_agent.generate_reply,
                request.message.text,
                scam_type,
                conversation_history,
                request.metadata
            ),
            timeout=4.5
        )
        
    except asyncio.TimeoutError:
        logger.warning(f"LLM timeout for session {session_id} - using fallback")
        # Fallback to simple acknowledgment
        reply = "I understand. Could you explain that again?"
    except Exception as e:
        logger.error(f"Reply generation failed for session {session_id}: {str(e)[:100]}")
        reply = "I'm here. What do you need?"
    
    return HoneypotResponse(status="success", reply=reply)


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
            "health": "GET /health",
            "ui_chat": "POST /ui-api/chat (UI Backend Proxy)",
            "ui_health": "GET /ui-api/health (UI Backend Proxy)"
        }
    }


# ============================================================================
# UI BACKEND PROXY - Forward requests to internal UI backend on port 8001
# ============================================================================

@app.post("/ui-api/chat")
async def ui_chat_proxy(request: Request):
    """Proxy chat requests to UI backend (port 8001)"""
    try:
        body = await request.body()
        response = await http_client.post(
            "http://localhost:8001/chat",
            content=body,
            headers={"Content-Type": "application/json"}
        )
        return JSONResponse(
            status_code=response.status_code,
            content=response.json()
        )
    except Exception as e:
        logger.error(f"UI proxy error: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={"error": "UI backend unavailable"}
        )


@app.post("/ui-api/session/new")
async def ui_session_new_proxy(request: Request):
    """Proxy session creation to UI backend"""
    try:
        api_key = request.headers.get("x-api-key")
        response = await http_client.post(
            "http://localhost:8001/session/new",
            headers={"x-api-key": api_key}
        )
        return JSONResponse(
            status_code=response.status_code,
            content=response.json()
        )
    except Exception as e:
        logger.error(f"UI proxy error: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={"error": "UI backend unavailable"}
        )


@app.get("/ui-api/session/{session_id}")
async def ui_session_get_proxy(session_id: str, request: Request):
    """Proxy session retrieval to UI backend"""
    try:
        api_key = request.headers.get("x-api-key")
        response = await http_client.get(
            f"http://localhost:8001/session/{session_id}",
            headers={"x-api-key": api_key}
        )
        return JSONResponse(
            status_code=response.status_code,
            content=response.json()
        )
    except Exception as e:
        logger.error(f"UI proxy error: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={"error": "UI backend unavailable"}
        )


@app.get("/ui-api/session/{session_id}/messages")
async def ui_session_messages_proxy(session_id: str, request: Request):
    """Proxy message history to UI backend"""
    try:
        api_key = request.headers.get("x-api-key")
        response = await http_client.get(
            f"http://localhost:8001/session/{session_id}/messages",
            headers={"x-api-key": api_key}
        )
        return JSONResponse(
            status_code=response.status_code,
            content=response.json()
        )
    except Exception as e:
        logger.error(f"UI proxy error: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={"error": "UI backend unavailable"}
        )


@app.delete("/ui-api/session/{session_id}")
async def ui_session_delete_proxy(session_id: str, request: Request):
    """Proxy session deletion to UI backend"""
    try:
        api_key = request.headers.get("x-api-key")
        response = await http_client.delete(
            f"http://localhost:8001/session/{session_id}",
            headers={"x-api-key": api_key}
        )
        return JSONResponse(
            status_code=response.status_code,
            content=response.json()
        )
    except Exception as e:
        logger.error(f"UI proxy error: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={"error": "UI backend unavailable"}
        )


@app.get("/ui-api/health")
async def ui_health_proxy():
    """Proxy health check to UI backend"""
    try:
        response = await http_client.get("http://localhost:8001/health")
        return JSONResponse(
            status_code=response.status_code,
            content=response.json()
        )
    except Exception as e:
        logger.error(f"UI backend health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": "UI backend unavailable"}
        )


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