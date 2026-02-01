import asyncio
from typing import Dict
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Depends, Header, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.models import (
    HoneypotRequest, 
    HoneypotResponse, 
    ConversationState, 
    Message,
    CallbackPayload
)
from app.agents.scam_detector import ScamDetector
from app.agents.conversation_agent import ConversationAgent
from app.services.intelligence_extractor import IntelligenceExtractor
from app.services.callback_service import CallbackService
from app.utils.logger import setup_logger, log_conversation_event
from config.settings import settings

# Initialize FastAPI app
app = FastAPI(
    title="AI-Powered Agentic Honeypot",
    description="Scam Detection & Intelligence Extraction System",
    version="1.0.0",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.is_development else [],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Initialize components
logger = setup_logger(__name__)
scam_detector = ScamDetector()
conversation_agent = ConversationAgent()
intelligence_extractor = IntelligenceExtractor()
callback_service = CallbackService()

# In-memory storage for conversation states (in production, use Redis/Database)
conversation_store: Dict[str, ConversationState] = {}

# API Key dependency
async def verify_api_key(x_api_key: str = Header(...)):
    """Verify API key from request headers."""
    if x_api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Custom handler for validation errors to help debug GUVI portal requests."""
    body = await request.body()
    logger.error(f"Validation error for request body: {body.decode('utf-8')}")
    logger.error(f"Validation errors: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "message": "INVALID_REQUEST_BODY",
            "details": exc.errors(),
            "body_received": body.decode('utf-8')
        }
    )

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.ENVIRONMENT
    }

@app.post("/honeypot")
async def honeypot_endpoint(
    request_body: dict,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    """Main honeypot endpoint for processing scam messages (POST with JSON body)."""
    
    try:
        # Log the raw incoming request for debugging
        logger.info(f"📥 Raw request body: {request_body}")
        
        # Validate required fields with detailed error messages
        if "sessionId" not in request_body:
            logger.error("❌ Missing field: sessionId")
            raise HTTPException(status_code=400, detail="Missing required field: sessionId")
        
        if "message" not in request_body:
            logger.error("❌ Missing field: message")
            raise HTTPException(status_code=400, detail="Missing required field: message")
        
        message_data = request_body.get("message", {})
        for field in ["sender", "text", "timestamp"]:
            if field not in message_data:
                logger.error(f"❌ Missing field: message.{field}")
                raise HTTPException(status_code=400, detail=f"Missing required field: message.{field}")
        
        # Parse into Pydantic model
        request = HoneypotRequest(**request_body)
        session_id = request.sessionId
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Request parsing failed: {e}")
        logger.error(f"📄 Received body: {request_body}")
        raise HTTPException(status_code=400, detail=f"INVALID_REQUEST_BODY: {str(e)}")
    
    try:
        # Log incoming request
        log_conversation_event(
            logger, 
            'message_received', 
            session_id,
            {'message': request.message.text, 'sender': request.message.sender}
        )
        
        # Get or create conversation state
        conversation_state = conversation_store.get(
            session_id,
            ConversationState(sessionId=session_id)
        )
        
        # Add message to conversation history
        conversation_state.add_message(request.message)
        conversation_store[session_id] = conversation_state
        
        # Detect scam intent
        detection_result = await scam_detector.analyze_message(
            request.message,
            request.conversationHistory,
            session_id
        )
        
        # If scam detected and agent not yet activated
        if detection_result.is_scam and not conversation_state.agent_activated:
            conversation_state.scam_detected = True
            conversation_state.agent_activated = True
            
            log_conversation_event(
                logger,
                'agent_activated',
                session_id,
                {
                    'scam_type': detection_result.scam_type,
                    'confidence': detection_result.confidence
                }
            )
        
        # Generate response ONLY for scam messages
        if conversation_state.agent_activated and detection_result.is_scam:
            # AI agent handles scam conversation
            reply = await conversation_agent.generate_response(
                conversation_state,
                detection_result.scam_type
            )
            
            # Add agent response to conversation
            agent_message = Message(
                sender="user",
                text=reply,
                timestamp=datetime.now(timezone.utc)
            )
            conversation_state.add_message(agent_message)
            
        else:
            # Legitimate message - just log, no AI engagement
            log_conversation_event(
                logger,
                'legitimate_message_logged',
                session_id,
                {
                    'message': request.message.text,
                    'confidence': detection_result.confidence,
                    'reason': 'Not detected as scam, no agent activation'
                }
            )
            reply = "Message received. Thank you."
        
        # Update conversation state
        conversation_store[session_id] = conversation_state
        
        # Check if scam conversation should end and send callback
        if (conversation_state.scam_detected and 
            conversation_state.agent_activated and
            not conversation_agent.should_continue_conversation(conversation_state)):
            
            log_conversation_event(
                logger,
                'conversation_ending',
                session_id,
                {'total_messages': len(conversation_state.messages)}
            )
            
            # Schedule background task to send callback with extracted intelligence
            background_tasks.add_task(
                send_final_callback,
                session_id,
                conversation_state
            )
        
        # Return minimal response as per GUVI specification
        return HoneypotResponse(
            status="success",
            reply=reply
        )
        
    except Exception as e:
        logger.error(
            f"Error processing request for session {session_id}: {str(e)}",
            extra={'session_id': session_id, 'error': str(e)}
        )
        
        # Return a neutral response even on error to maintain cover
        return HoneypotResponse(
            status="success",
            reply="I'm having trouble understanding. Could you please repeat that?"
        )

async def send_final_callback(session_id: str, conversation_state: ConversationState):
    """Send final intelligence callback (background task)."""
    
    try:
        # Extract intelligence from conversation
        intelligence = intelligence_extractor.extract_from_conversation(
            conversation_state.messages,
            session_id
        )
        
        # Generate agent notes
        agent_notes = generate_agent_notes(conversation_state)
        
        # Create callback payload
        payload = CallbackPayload(
            sessionId=session_id,
            scamDetected=conversation_state.scam_detected,
            totalMessagesExchanged=conversation_state.total_messages,
            extractedIntelligence=intelligence,
            agentNotes=agent_notes
        )
        
        # Send callback with retry
        success = await callback_service.send_with_retry(payload)
        
        if success:
            log_conversation_event(
                logger,
                'callback_sent',
                session_id,
                {'intelligence_extracted': intelligence.dict()}
            )
        else:
            logger.error(f"Failed to send callback for session {session_id}")
            
        # Clean up conversation state after callback
        if session_id in conversation_store:
            del conversation_store[session_id]
            
    except Exception as e:
        logger.error(
            f"Error in background callback for session {session_id}: {str(e)}",
            extra={'session_id': session_id, 'error': str(e)}
        )

def generate_agent_notes(conversation_state: ConversationState) -> str:
    """Generate summary notes about scammer behavior."""
    
    notes = []
    
    # Analyze conversation patterns
    scammer_messages = [msg for msg in conversation_state.messages if msg.sender == "scammer"]
    
    if len(scammer_messages) > 5:
        notes.append("Scammer was persistent with multiple follow-up messages")
    
    # Check for urgency tactics
    urgency_keywords = ['urgent', 'immediate', 'now', 'quickly', 'asap']
    urgency_count = sum(1 for msg in scammer_messages 
                       for keyword in urgency_keywords 
                       if keyword in msg.text.lower())
    
    if urgency_count > 0:
        notes.append(f"Used urgency tactics ({urgency_count} instances)")
    
    # Check for credential requests
    credential_keywords = ['otp', 'pin', 'password', 'account number', 'upi']
    credential_requests = sum(1 for msg in scammer_messages 
                            for keyword in credential_keywords 
                            if keyword in msg.text.lower())
    
    if credential_requests > 0:
        notes.append(f"Requested credentials ({credential_requests} instances)")
    
    # Check for impersonation
    impersonation_keywords = ['bank', 'customer care', 'security', 'government']
    impersonation_count = sum(1 for msg in scammer_messages 
                            for keyword in impersonation_keywords 
                            if keyword in msg.text.lower())
    
    if impersonation_count > 0:
        notes.append("Attempted impersonation of official entities")
    
    # Add conversation duration info
    if conversation_state.messages:
        try:
            start_time = conversation_state.messages[0].timestamp
            end_time = conversation_state.messages[-1].timestamp
            
            # Ensure both are timezone-aware or both are naive
            if start_time.tzinfo is None and end_time.tzinfo is not None:
                from datetime import timezone
                start_time = start_time.replace(tzinfo=timezone.utc)
            elif start_time.tzinfo is not None and end_time.tzinfo is None:
                from datetime import timezone
                end_time = end_time.replace(tzinfo=timezone.utc)
            
            duration = end_time - start_time
            notes.append(f"Conversation lasted {duration.total_seconds():.0f} seconds")
        except Exception as e:
            logger.warning(f"Could not calculate conversation duration: {e}")
            notes.append(f"Conversation lasted {len(conversation_state.messages)} message exchanges")
    
    return ". ".join(notes) if notes else "Standard scam conversation pattern detected"

@app.get("/stats")
async def get_stats(api_key: str = Depends(verify_api_key)):
    """Get system statistics (development only)."""
    if not settings.is_development:
        raise HTTPException(status_code=404, detail="Not found")
    
    return {
        "active_conversations": len(conversation_store),
        "total_sessions": len(conversation_store),
        "environment": settings.ENVIRONMENT
    }

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
        log_level=settings.LOG_LEVEL.lower()
    )