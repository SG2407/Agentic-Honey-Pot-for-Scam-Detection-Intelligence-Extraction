"""Pydantic models for request/response validation with timezone-aware timestamp handling"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator, ConfigDict
import logging

logger = logging.getLogger(__name__)


class Message(BaseModel):
    """Message model with flexible timestamp parsing (Unix ms, ISO-8601, datetime)"""
    model_config = ConfigDict(extra='ignore')  # Ignore unknown fields from GUVI
    
    sender: str  # Will be normalized by validator
    text: str
    timestamp: Optional[Union[str, int, datetime]] = Field(default_factory=lambda: datetime.now(timezone.utc))  # Auto-fill if missing
    
    @field_validator('sender', mode='before')
    @classmethod
    def normalize_sender(cls, value):
        """Normalize sender - accept any case variation, never fail"""
        if not isinstance(value, str):
            # If not a string, try to convert
            try:
                value = str(value)
            except:
                logger.warning(f"Could not convert sender to string: {value}, defaulting to 'scammer'")
                return "scammer"
        
        value = value.strip().lower()
        
        # Accept common variations
        if value in {"scammer", "user"}:
            return value
        
        # Fallback: default to 'scammer' if unclear (NEVER raise exception)
        logger.warning(f"Unexpected sender value: '{value}', defaulting to 'scammer'")
        return "scammer"
    
    @field_validator('timestamp', mode='before')
    @classmethod
    def parse_timestamp(cls, value):
        """Parse Unix milliseconds, ISO-8601 string, or datetime object to timezone-aware datetime - NEVER FAILS"""
        # Auto-fill if missing
        if value is None or value == "":
            return datetime.now(timezone.utc)
        
        # Already a datetime object
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value
        
        # Unix timestamp (milliseconds) as int or float
        if isinstance(value, (int, float)):
            try:
                return datetime.fromtimestamp(value / 1000, tz=timezone.utc)
            except (ValueError, OSError) as e:
                logger.warning(f"Invalid Unix timestamp: {value}, using current time. Error: {e}")
                return datetime.now(timezone.utc)
        
        # String handling
        if isinstance(value, str):
            # Handle numeric strings (Unix timestamp in milliseconds)
            if value.isdigit():
                try:
                    return datetime.fromtimestamp(int(value) / 1000, tz=timezone.utc)
                except (ValueError, OSError) as e:
                    logger.warning(f"Invalid Unix timestamp string: {value}, using current time. Error: {e}")
                    return datetime.now(timezone.utc)
            
            # Try ISO-8601 formats
            try:
                # Handle 'Z' suffix (UTC indicator)
                clean_value = value.replace('Z', '+00:00')
                dt = datetime.fromisoformat(clean_value)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except ValueError:
                pass  # Try next format
            
            # Try parsing without milliseconds: "2026-01-21T10:15:30"
            try:
                dt = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
                return dt.replace(tzinfo=timezone.utc)
            except ValueError:
                pass  # Try next format
            
            # Try parsing with milliseconds: "2026-01-21T10:15:30.123"
            try:
                dt = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f")
                return dt.replace(tzinfo=timezone.utc)
            except ValueError:
                pass  # Try next format
            
            # Last resort: return current time
            logger.warning(f"Could not parse timestamp string: '{value}', using current time")
            return datetime.now(timezone.utc)
        
        # Fallback for any other unexpected type
        logger.warning(f"Unsupported timestamp type: {type(value)} (value: {value}), using current time")
        return datetime.now(timezone.utc)


class Metadata(BaseModel):
    """Metadata about the message"""
    model_config = ConfigDict(extra='ignore')  # Ignore unknown fields from GUVI
    
    channel: Optional[str] = None
    language: Optional[str] = None
    locale: Optional[str] = None


class HoneypotRequest(BaseModel):
    """Incoming request from GUVI with maximum flexibility"""
    model_config = ConfigDict(extra='ignore')  # Ignore unknown fields from GUVI
    
    sessionId: Optional[str] = Field(default="unknown-session")  # Optional - GUVI sometimes omits on retries
    message: Message
    conversationHistory: Optional[List[Message]] = Field(default_factory=list)  # Optional, handles null
    metadata: Optional[Metadata] = Field(default_factory=Metadata)  # Changed from None to default factory
    
    @field_validator('conversationHistory', mode='before')
    @classmethod
    def normalize_conversation_history(cls, value):
        """Convert null/None to empty list, handle malformed data - NEVER FAILS"""
        if value is None or value == "null" or value == "":
            return []
        if not isinstance(value, list):
            logger.warning(f"conversationHistory is not a list: {type(value)} (value: {value}), using empty list")
            return []
        return value
    
    @field_validator('metadata', mode='before')
    @classmethod
    def normalize_metadata(cls, value):
        """Ensure metadata is always valid - NEVER FAILS"""
        if value is None or value == "null" or value == "":
            return {}
        if not isinstance(value, dict):
            logger.warning(f"metadata is not a dict: {type(value)}, using empty dict")
            return {}
        return value


class HoneypotResponse(BaseModel):
    """Response to GUVI - STRICT format (only status and reply)"""
    status: str = Field(default="success")
    reply: str


class ExtractedIntelligence(BaseModel):
    """Intelligence extracted from conversation - empty arrays will be removed before sending"""
    bankAccounts: List[str] = Field(default_factory=list)
    upiIds: List[str] = Field(default_factory=list)
    phishingLinks: List[str] = Field(default_factory=list)
    phoneNumbers: List[str] = Field(default_factory=list)
    suspiciousKeywords: List[str] = Field(default_factory=list)


class CallbackPayload(BaseModel):
    """Final result payload sent to GUVI callback endpoint"""
    model_config = ConfigDict(extra='forbid')  # Strict: only defined fields
    
    sessionId: str = Field(..., description="Session ID from GUVI platform")
    scamDetected: bool = Field(..., description="Whether scam was detected")
    totalMessagesExchanged: int = Field(..., description="Total messages: scammer + honeypot")
    extractedIntelligence: ExtractedIntelligence = Field(..., description="Extracted intelligence")
    agentNotes: str = Field(..., description="Description of scammer behavior and tactics")


class ScamDetectionResult(BaseModel):
    """Internal model for scam detection results"""
    is_scam: bool
    confidence: float  # 0.0 to 1.0
    scam_type: Optional[str] = None  # credential_phishing, financial_threat, prize_scam, etc.
    reasoning: str