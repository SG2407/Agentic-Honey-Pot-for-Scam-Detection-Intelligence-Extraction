"""Scam detection with hard rules (FIRST) then LLM fallback"""

import os
import re
from app.models import ScamDetectionResult
from app.llm_provider import LLMManager  # PRIORITY 2: Abstract LLM provider
import logging

logger = logging.getLogger(__name__)


class ScamDetector:
    """Multi-layer scam detection: Hard rules → LLM → Pattern fallback"""
    
    def __init__(self):
        """Initialize ScamDetector with LLM manager (PRIORITY 2)"""
        self.llm_manager = LLMManager()  # Supports OpenRouter + Groq with fallback
    
    # Hard scam patterns - GUARANTEED detection (confidence = 1.0)
    HARD_PATTERNS = [
        # Credential Phishing - Direct credential/identity requests (PRIORITY)
        {
            "pattern": r"(?i)(send|share|provide|give|tell|enter|submit)\s+(me\s+)?(your\s+)?(otp|pin|password|cvv|code)",
            "scam_type": "credential_phishing",
            "reasoning": "Explicit request for credentials (OTP/PIN/password/CVV)"
        },
        {
            "pattern": r"(?i)(send|share|provide|give|tell|enter).*(aadh?aar|pan\s+card|pan\s+number)",
            "scam_type": "credential_phishing",
            "reasoning": "Identity document request (Aadhaar/PAN)"
        },
        {
            "pattern": r"(?i)(upi\s+(pin|id|password)|share.*upi|send.*upi\s+(pin|id)|enter.*upi)",
            "scam_type": "credential_phishing",
            "reasoning": "UPI credential request"
        },
        {
            "pattern": r"(?i)(bank\s+account\s+(number|details)|ifsc\s+code|account\s+number|cvv\s+number).*(provide|share|send|give|tell|enter)",
            "scam_type": "credential_phishing",
            "reasoning": "Bank account details request"
        },
        {
            "pattern": r"(?i)(verify|update|confirm).*(aadh?aar|pan\s+card|kyc).*(link|click|submit|send|share)",
            "scam_type": "credential_phishing",
            "reasoning": "Identity verification phishing attempt"
        },
        
        # Financial Threat - Urgency + consequences
        {
            "pattern": r"(?i)(account|card).*(blocked|suspended|locked|frozen|compromised|deactivated)",
            "scam_type": "financial_threat",
            "reasoning": "Account status threat detected"
        },
        {
            "pattern": r"(?i)(last\s+(chance|warning|day)|expire|cancel|close).*(account|service|card)",
            "scam_type": "financial_threat",
            "reasoning": "Urgency-based account threat"
        },
        {
            "pattern": r"(?i)(unauthorized|suspicious|fraud).*(transaction|activity|payment).*(verify|confirm|block)",
            "scam_type": "financial_threat",
            "reasoning": "Fraudulent transaction scare tactic"
        },
        
        # Reward Scam - Prize/lottery/cashback
        {
            "pattern": r"(?i)(won|winner|congratulations|selected).*(prize|lottery|reward|gift|lakh|crore|cashback)",
            "scam_type": "reward_scam",
            "reasoning": "Prize/lottery win notification"
        },
        {
            "pattern": r"(?i)(claim|collect|receive).*(prize|reward|cashback|refund|amount).*(click|link|verify)",
            "scam_type": "reward_scam",
            "reasoning": "Reward claiming scam"
        },
        
        # Impersonation - Authority figures
        {
            "pattern": r"(?i)(income\s+tax|tax\s+department|rbi|customs|police|court).*(notice|summon|refund|pending|action)",
            "scam_type": "impersonation",
            "reasoning": "Government authority impersonation"
        },
        {
            "pattern": r"(?i)(official|authorized|government).*(representative|agent|officer).*(verify|update|confirm)",
            "scam_type": "impersonation",
            "reasoning": "Official authority impersonation"
        }
    ]
    
    # Soft patterns for fallback (confidence varies)
    SOFT_PATTERNS = {
        "urgency": r"(?i)(urgent|immediate|now|today|expire|limited time|act fast)",
        "financial_threat": r"(?i)(blocked|suspended|locked|frozen|deactivate|close|cancel)",
        "credential_request": r"(?i)(verify|confirm|update|validate).*(account|card|details|information)",
        "impersonation": r"(?i)(bank|government|tax|police|court|rbi|income tax|customs)",
        "reward_bait": r"(?i)(win|won|prize|gift|cashback|reward|refund|claim)"
    }
    
    def _check_hard_patterns(self, text: str) -> ScamDetectionResult:
        """Check hard patterns FIRST - guaranteed scam detection"""
        for pattern_def in self.HARD_PATTERNS:
            if re.search(pattern_def["pattern"], text):
                logger.info(f"🔴 HARD SCAM DETECTED: {pattern_def['reasoning']}")
                return ScamDetectionResult(
                    is_scam=True,
                    confidence=1.0,  # Guaranteed
                    scam_type=pattern_def["scam_type"],
                    reasoning=f"HARD RULE: {pattern_def['reasoning']}"
                )
        return None  # No hard pattern matched
    
    def _detect_with_llm(self, message_text: str, conversation_context: str) -> ScamDetectionResult:
        """Use LLM for scam detection (secondary layer) - PRIORITY 2: OpenRouter + Groq"""
        
        prompt = f"""You are a scam detection expert. Analyze this message and determine if it's a scam attempt.

Current message: {message_text}

Conversation context: {conversation_context if conversation_context else "No prior context"}

Analyze for:
- Credential phishing (OTP, PIN, password, bank details)
- Financial threats (account blocked, urgent action)
- Prize/lottery scams
- Impersonation (bank, government, official)
- Urgency tactics

Respond in this exact format:
IS_SCAM: yes/no
CONFIDENCE: 0.0-1.0
TYPE: credential_phishing/financial_threat/prize_scam/impersonation/legitimate
REASONING: Brief explanation"""

        # PRIORITY 2: Use LLM manager with automatic fallback
        result_text = self.llm_manager.generate(
            prompt=prompt,
            model=None,  # Let provider choose model
            temperature=0.1,
            max_tokens=200
        )
        
        if not result_text:
            logger.warning("LLM failed, using pattern-based fallback")
            return None
        
        try:
            logger.info(f"LLM Response: {result_text}")
            
            # Parse LLM response
            is_scam = "yes" in result_text.split("IS_SCAM:")[1].split("\n")[0].lower()
            confidence_match = re.search(r"CONFIDENCE:\s*([\d.]+)", result_text)
            confidence = float(confidence_match.group(1)) if confidence_match else 0.5
            
            type_match = re.search(r"TYPE:\s*(\w+)", result_text)
            scam_type = type_match.group(1) if type_match else "unknown"
            
            reasoning_match = re.search(r"REASONING:\s*(.+)", result_text, re.DOTALL)
            reasoning = reasoning_match.group(1).strip() if reasoning_match else "LLM detection"
            
            return ScamDetectionResult(
                is_scam=is_scam,
                confidence=confidence,
                scam_type=scam_type if is_scam else None,
                reasoning=f"LLM: {reasoning}"
            )
            
        except Exception as e:
            logger.error(f"LLM detection failed: {e}")
            return None  # Fallback to pattern-based
    
    def _pattern_based_detection(self, text: str) -> ScamDetectionResult:
        """Fallback pattern-based detection (if LLM fails)"""
        pattern_matches = []
        for pattern_name, pattern_regex in self.SOFT_PATTERNS.items():
            if re.search(pattern_regex, text):
                pattern_matches.append(pattern_name)
        
        # Calculate confidence based on pattern matches
        if len(pattern_matches) >= 3:
            confidence = 0.85
            is_scam = True
        elif len(pattern_matches) == 2:
            confidence = 0.65
            is_scam = True
        elif len(pattern_matches) == 1:
            confidence = 0.4
            is_scam = False  # Not enough evidence
        else:
            confidence = 0.1
            is_scam = False
        
        return ScamDetectionResult(
            is_scam=is_scam,
            confidence=confidence,
            scam_type="pattern_detected" if is_scam else None,
            reasoning=f"Pattern-based: matched {len(pattern_matches)} indicators - {', '.join(pattern_matches)}"
        )
    
    def analyze_message(self, message_text: str, conversation_history: list) -> ScamDetectionResult:
        """
        Main detection method - executes in order:
        1. Hard patterns (guaranteed scams)
        2. LLM detection (Groq)
        3. Pattern-based fallback
        """
        # Build conversation context
        conversation_context = " ".join([msg.text for msg in conversation_history]) if conversation_history else ""
        full_text = f"{conversation_context} {message_text}"
        
        logger.info(f"Analyzing message: {message_text[:100]}...")
        
        # STEP 1: Check hard patterns FIRST
        hard_result = self._check_hard_patterns(full_text)
        if hard_result:
            return hard_result
        
        # STEP 2: Try LLM detection
        llm_result = self._detect_with_llm(message_text, conversation_context)
        if llm_result:
            return llm_result
        
        # STEP 3: Fallback to pattern-based
        logger.warning("LLM failed, using pattern-based fallback")
        return self._pattern_based_detection(full_text)
