import httpx
import asyncio
from typing import Optional
from app.models import CallbackPayload
from app.utils.logger import setup_logger, log_conversation_event
from config.settings import settings

class CallbackService:
    """Service for making callbacks to GUVI evaluation endpoint."""
    
    def __init__(self):
        self.logger = setup_logger(__name__)
        self.callback_url = settings.GUVI_CALLBACK_URL
    
    async def send_final_result(self, payload: CallbackPayload) -> bool:
        """Send final intelligence result to GUVI endpoint."""
        
        try:
            # Convert to dict - KEEP all fields (GUVI requires all 5 intelligence fields)
            payload_dict = payload.model_dump()  # Use model_dump() instead of deprecated dict()
            
            # CRITICAL: GUVI expects ALL 5 fields present (even if empty arrays)
            # Do NOT remove empty arrays - this causes INVALID_REQUEST_BODY
            intel = payload_dict['extractedIntelligence']
            
            # Ensure only required fields (no extra fields)
            final_payload = {
                'sessionId': payload_dict['sessionId'],
                'scamDetected': payload_dict['scamDetected'],
                'totalMessagesExchanged': payload_dict['totalMessagesExchanged'],
                'extractedIntelligence': intel,  # Keep all 5 fields
                'agentNotes': payload_dict['agentNotes']
            }
            
            self.logger.info(
                f"Sending callback payload for session {payload.sessionId}",
                extra={
                    'event_type': 'callback_payload',
                    'session_id': payload.sessionId,
                    'payload': final_payload,
                    'callback_url': self.callback_url
                }
            )
            
            # Configure timeout with granular control
            timeout = httpx.Timeout(
                connect=5.0,
                read=10.0,
                write=5.0,
                pool=5.0
            )
            
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    self.callback_url,
                    json=final_payload,
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code == 200:
                    self.logger.info(
                        f"Successfully sent callback for session {payload.sessionId}",
                        extra={
                            'event_type': 'callback_success',
                            'session_id': payload.sessionId,
                            'status_code': response.status_code
                        }
                    )
                    return True
                else:
                    self.logger.error(
                        f"Callback failed for session {payload.sessionId}: {response.status_code}",
                        extra={
                            'event_type': 'callback_error',
                            'session_id': payload.sessionId,
                            'status_code': response.status_code,
                            'response_text': response.text
                        }
                    )
                    return False
                    
        except httpx.TimeoutException:
            self.logger.error(
                f"Callback timeout for session {payload.sessionId}",
                extra={
                    'event_type': 'callback_timeout',
                    'session_id': payload.sessionId
                }
            )
            return False
            
        except Exception as e:
            self.logger.error(
                f"Callback error for session {payload.sessionId}: {str(e)}",
                extra={
                    'event_type': 'callback_exception',
                    'session_id': payload.sessionId,
                    'error': str(e)
                }
            )
            return False
    
    async def send_with_retry(self, payload: CallbackPayload, max_retries: int = 3) -> bool:
        """Send callback with retry logic (no delay between retries)."""
        
        for attempt in range(max_retries):
            success = await self.send_final_result(payload)
            
            if success:
                return True
            
            if attempt < max_retries - 1:
                self.logger.info(
                    f"Retrying callback for session {payload.sessionId} immediately (attempt {attempt + 1}/{max_retries})"
                )
        
        self.logger.error(
            f"All callback attempts failed for session {payload.sessionId}",
            extra={
                'event_type': 'callback_failed_final',
                'session_id': payload.sessionId,
                'max_retries': max_retries
            }
        )
        return False