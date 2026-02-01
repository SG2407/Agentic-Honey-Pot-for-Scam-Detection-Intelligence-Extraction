from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class Message(BaseModel):
    """Represents a single message in the conversation."""
    sender: str = Field(..., description="Message sender: 'scammer' or 'user'")
    text: str = Field(..., description="Message content")
    timestamp: datetime = Field(..., description="Message timestamp in ISO-8601 format")

class Metadata(BaseModel):
    """Message metadata."""
    channel: Optional[str] = Field(None, description="Communication channel (SMS, WhatsApp, Email, Chat)")
    language: Optional[str] = Field(None, description="Language used")
    locale: Optional[str] = Field(None, description="Country or region")

class HoneypotRequest(BaseModel):
    """Request model for honeypot API."""
    sessionId: str = Field(..., description="Unique session identifier")
    message: Message = Field(..., description="Latest incoming message")
    conversationHistory: List[Message] = Field(default=[], description="Previous messages in conversation")
    metadata: Optional[Metadata] = Field(None, description="Message metadata")

class HoneypotResponse(BaseModel):
    """Response model for honeypot API."""
    status: str = Field(..., description="Response status")
    reply: str = Field(..., description="Agent's reply message")
    scamDetection: Optional[Dict[str, Any]] = Field(None, description="Scam detection results")

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