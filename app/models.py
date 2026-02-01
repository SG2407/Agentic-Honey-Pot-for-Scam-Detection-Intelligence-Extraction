from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator

class Message(BaseModel):
    """Represents a single message in the conversation."""
    sender: str = Field(..., description="Message sender: 'scammer' or 'user'")
    text: str = Field(..., description="Message content")
    timestamp: Union[datetime, str] = Field(..., description="Message timestamp in ISO-8601 format")
    
    class Config:
        extra = "allow"  # Allow any extra fields GUVI might send
    
    @field_validator('timestamp', mode='before')
    @classmethod
    def parse_timestamp(cls, v):
        """Flexible timestamp parsing to accept multiple formats."""
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            # Try parsing with various formats
            formats = [
                "%Y-%m-%dT%H:%M:%S.%fZ",
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%d %H:%M:%S",
            ]
            for fmt in formats:
                try:
                    return datetime.strptime(v, fmt)
                except ValueError:
                    continue
            # If none work, try ISO format parsing
            try:
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except:
                pass
        # If all parsing fails, use current time
        return datetime.utcnow()

class Metadata(BaseModel):
    """Message metadata."""
    channel: Optional[str] = Field(None, description="Communication channel (SMS, WhatsApp, Email, Chat)")
    language: Optional[str] = Field(None, description="Language used")
    locale: Optional[str] = Field(None, description="Country or region")

class HoneypotRequest(BaseModel):
    """Request model for honeypot API."""
    sessionId: str = Field(..., description="Unique session identifier")
    message: Message = Field(..., description="Latest incoming message")
    conversationHistory: Optional[List[Message]] = Field(default_factory=list, description="Previous messages in conversation")
    metadata: Optional[Metadata] = Field(None, description="Message metadata")
    
    class Config:
        # Allow extra fields that GUVI portal might send
        extra = "allow"
        # Be flexible with field names
        populate_by_name = True

class HoneypotResponse(BaseModel):
    """Response model for honeypot API - STRICT format as per GUVI specification."""
    status: str = Field(..., description="Response status")
    reply: str = Field(..., description="Agent's reply message")
    
    class Config:
        # Ensure clean JSON output, no extra fields
        extra = "forbid"

class ExtractedIntelligence(BaseModel):
    """Extracted intelligence from scam conversation."""
    bankAccounts: List[str] = Field(default=[], description="Bank account numbers found")
    upiIds: List[str] = Field(default=[], description="UPI IDs found")
    phishingLinks: List[str] = Field(default=[], description="Malicious links found")
    phoneNumbers: List[str] = Field(default=[], description="Phone numbers found")
    suspiciousKeywords: List[str] = Field(default=[], description="Scam-related keywords")

class CallbackPayload(BaseModel):
    """Payload for final result callback to GUVI."""
    sessionId: str = Field(..., description="Session identifier")
    scamDetected: bool = Field(..., description="Whether scam was detected")
    totalMessagesExchanged: int = Field(..., description="Total messages in conversation")
    extractedIntelligence: ExtractedIntelligence = Field(..., description="Intelligence extracted")
    agentNotes: str = Field(..., description="Summary of scammer behavior")

class ScamDetectionResult(BaseModel):
    """Result of scam detection analysis."""
    is_scam: bool = Field(..., description="Whether message is likely a scam")
    confidence: float = Field(..., description="Confidence score (0.0-1.0)")
    scam_type: Optional[str] = Field(None, description="Type of scam detected")
    reasoning: str = Field(..., description="Explanation of detection")

class ConversationState(BaseModel):
    """Tracks conversation state for a session."""
    sessionId: str
    messages: List[Message] = Field(default=[])
    scam_detected: bool = Field(default=False)
    agent_activated: bool = Field(default=False)
    intelligence: ExtractedIntelligence = Field(default_factory=ExtractedIntelligence)
    agent_notes: str = Field(default="")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def add_message(self, message: Message):
        """Add a message to the conversation."""
        self.messages.append(message)
        self.updated_at = datetime.utcnow()
    
    @property
    def total_messages(self) -> int:
        """Get total number of messages exchanged."""
        return len(self.messages)