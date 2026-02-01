"""Send final result callback to GUVI endpoint"""

import os
import httpx
from app.models import CallbackPayload, ExtractedIntelligence
import logging

logger = logging.getLogger(__name__)

# GUVI callback endpoint
CALLBACK_URL = os.getenv("CALLBACK_URL", "https://hackathon.guvi.in/api/updateHoneyPotFinalResult")


class CallbackService:
    """Handle sending final results to GUVI"""
    
    @staticmethod
    async def send_final_result(payload: CallbackPayload) -> bool:
        """
        Send callback to GUVI endpoint
        Returns True if successful, False otherwise
        ALWAYS includes all 5 intelligence fields (even if empty)
        """
        try:
            # Use model_dump to get dict - KEEP ALL FIELDS (including empty arrays)
            payload_dict = payload.model_dump()
            
            logger.info(f"📤 Sending callback for session: {payload.sessionId}")
            logger.info(f"   Scam detected: {payload.scamDetected}")
            logger.info(f"   Messages exchanged: {payload.totalMessagesExchanged}")
            logger.info(f"   Intelligence: {payload_dict['extractedIntelligence']}")
            
            # Configure timeout
            timeout = httpx.Timeout(
                connect=5.0,  # 5 seconds to establish connection
                read=10.0,    # 10 seconds to read response
                write=5.0,    # 5 seconds to write request
                pool=5.0      # 5 seconds to get connection from pool
            )
            
            # Send POST request to GUVI
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    CALLBACK_URL,
                    json=payload_dict,
                    headers={"Content-Type": "application/json"}
                )
                
                logger.info(f"✓ Callback response: {response.status_code}")
                logger.info(f"  Response body: {response.text}")
                
                return response.status_code in [200, 201, 204]
                
        except httpx.TimeoutException as e:
            logger.error(f"❌ Callback timeout: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Callback failed: {e}")
            return False
