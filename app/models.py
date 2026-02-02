"""Pydantic models for request/response validation with timezone-aware timestamp handling"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator, ConfigDict


class Message(BaseModel):
    """Message model with flexible timestamp parsing (Unix ms, ISO-8601, datetime)"""
    model_config = ConfigDict(extra='ignore')  # Ignore unknown fields from GUVI
    
    sender: str  # Will be normalized by validator
    text: str
    timestamp: Union[str, int, datetime]  # Accept str | int before validation
    
    @field_validator('sender', mode='before')
    @classmethod
    def normalize_sender(cls, value):
        """Normalize sender to lowercase and trim whitespace (accepts Scammer, scammer, user, User)"""
        if isinstance(value, str):
            value = value.strip().lower()
        if value not in {"scammer", "user"}:
            raise ValueError(f"Invalid sender: {value}. Must be 'scammer' or 'user'")
        return value
    
    @field_validator('timestamp', mode='before')
    @classmethod
    def parse_timestamp(cls, value):
        """Parse Unix milliseconds, ISO-8601 string, or datetime object to timezone-aware datetime"""
        if isinstance(value, datetime):
            # If already datetime, ensure timezone-aware
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value
        elif isinstance(value, int):
            # Unix milliseconds from GUVI (e.g., 1769938742773)
            return datetime.fromtimestamp(value / 1000, tz=timezone.utc)
        elif isinstance(value, str):
            # Handle numeric strings (e.g., "1738408530000")
            if value.isdigit():
                return datetime.fromtimestamp(int(value) / 1000, tz=timezone.utc)
            # ISO-8601 string (e.g., "2026-01-21T10:15:30Z")
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt
        else:
            raise ValueError(f"Unsupported timestamp format: {type(value)}")


class Metadata(BaseModel):
    """Metadata about the message"""
    model_config = ConfigDict(extra='ignore')  # Ignore unknown fields from GUVI
    
    channel: Optional[str] = None
    language: Optional[str] = None
    locale: Optional[str] = None


class HoneypotRequest(BaseModel):
    """Incoming request from GUVI"""
    model_config = ConfigDict(extra='ignore')  # Ignore unknown fields from GUVI
    
    sessionId: Optional[str] = Field(default="unknown-session")  # Optional - GUVI sometimes omits on retries
    message: Message
    conversationHistory: Optional[List[Message]] = Field(default_factory=list)  # Optional, handles null
    metadata: Optional[Metadata] = None  # Optional
    
    @field_validator('conversationHistory', mode='before')
    @classmethod
    def normalize_conversation_history(cls, value):
        """Convert null to empty list"""
        if value is None:
            return []
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
    sessionId: str
    scamDetected: bool
    totalMessagesExchanged: int
    extractedIntelligence: ExtractedIntelligence
    agentNotes: str


class ScamDetectionResult(BaseModel):
    """Internal model for scam detection results"""
    is_scam: bool
    confidence: float  # 0.0 to 1.0
    scam_type: Optional[str] = None  # credential_phishing, financial_threat, prize_scam, etc.
    reasoning: str
