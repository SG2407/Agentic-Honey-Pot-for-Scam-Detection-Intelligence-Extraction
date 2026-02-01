import re
from typing import List, Dict, Any
from app.models import ScamDetectionResult, Message
from app.utils.logger import setup_logger, log_scam_detection
from config.settings import settings
from groq import Groq
import json

class ScamDetector:
    """Advanced scam detection using Groq LLM with pattern-based fallback."""
    
    def __init__(self):
        self.logger = setup_logger(__name__)
        self.client = Groq(api_key=settings.GROQ_API_KEY) if settings.GROQ_API_KEY else None
        
        if self.client:
            self.logger.info("✅ Groq LLM client initialized for scam detection")
        else:
            self.logger.warning("⚠️ Groq API key not found - using pattern-based fallback only")
        
        # Common scam patterns
        self.scam_patterns = {
            'urgency': [
                r'urgent(?:ly)?',
                r'immediate(?:ly)?',
                r'act now',
                r'expires today',
                r'limited time',
                r'hurry',
                r'asap'
            ],
            'financial_threat': [
                r'account (?:will be )?(?:blocked|suspended|closed)',
                r'bank account',
                r'credit card',
                r'transaction',
                r'payment failed',
                r'verify (?:your )?account',
                r'unauthorized',
                r'suspicious activity'
            ],
            'credential_request': [
                r'(?:share|send|provide) (?:your )?(?:otp|pin|password)',
                r'upi (?:id|pin)',
                r'account (?:number|details)',
                r'cvv',
                r'expiry date',
                r'verification code'
            ],
            'impersonation': [
                r'(?:from )?(?:bank|sbi|hdfc|icici|axis)',
                r'customer (?:care|service)',
                r'security team',
                r'fraud (?:detection|prevention)',
                r'rbi',
                r'government'
            ],
            'reward_bait': [
                r'congratulations',
                r'(?:you )?(?:won|win)',
                r'prize',
                r'lottery',
                r'cash(?:back)?',
                r'reward',
                r'free (?:money|gift)'
            ]
        }
        
        # Individual scam keywords with weights
        self.scam_keywords = {
            'verify': 0.3,
            'blocked': 0.4,
            'suspended': 0.4,
            'otp': 0.5,
            'pin': 0.5,
            'urgent': 0.3,
            'winner': 0.4,
            'prize': 0.4,
            'congratulations': 0.3,
            'bank': 0.2,
            'account': 0.2,
            'payment': 0.2,
            'refund': 0.3,
            'claim': 0.3,
            'customer care': 0.4
        }
    
    def _ml_based_detection(self, text: str) -> Dict[str, Any]:
        """Use RoBERTa model for scam detection."""
        try:
            # Tokenize input
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True
            )
            
            # Get model prediction
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                probabilities = torch.softmax(logits, dim=1)
            
            # Get prediction (0=ham/legitimate, 1=spam/scam)
            spam_probability = probabilities[0][1].item()
            ham_probability = probabilities[0][0].item()
            
            is_scam = spam_probability > 0.5
            confidence = spam_probability if is_scam else ham_probability
            
            reasoning = f"RoBERTa ML model: {'SCAM' if is_scam else 'LEGITIMATE'} (spam_prob: {spam_probability:.3f}, ham_prob: {ham_probability:.3f})"
            
            return {
                'is_scam': is_scam,
                'confidence': confidence,
                'reasoning': reasoning,
                'spam_probability': spam_probability,
                'ham_probability': ham_probability
            }
            
        except Exception as e:
            self.logger.error(f"ML detection failed: {str(e)}")
            # Fallback to pattern-based
            pattern_score = self._pattern_based_detection(text)
            return {
                'is_scam': pattern_score > 0.5,
                'confidence': pattern_score,
                'reasoning': f"ML model error, fallback pattern: {pattern_score:.2f}"
            }
    
    async def analyze_message(self, message: Message, conversation_history: List[Message] = None, session_id: str = None) -> ScamDetectionResult:
        """Analyze message for scam indicators using Groq LLM with pattern-based fallback."""
        
        # HARD OVERRIDE: Check for guaranteed scam patterns FIRST
        hard_scam_check = self._check_hard_scam_patterns(message.text)
        if hard_scam_check['is_definite_scam']:
            # This is 100% a scam - override any LLM decision
            self.logger.info(f"Hard scam pattern detected: {hard_scam_check['pattern']}")
            return ScamDetectionResult(
                is_scam=True,
                confidence=1.0,
                scam_type=hard_scam_check['scam_type'],
                reasoning=f"HARD OVERRIDE: {hard_scam_check['reasoning']}"
            )
        
        # Primary detection using Groq LLM
        if self.client:
            llm_result = await self._llm_based_detection(message.text)
            is_scam = llm_result['is_scam']
            confidence = llm_result['confidence']
            reasoning = llm_result['reasoning']
            scam_type = llm_result.get('scam_type')
        else:
            # Fallback to pattern-based if LLM not available
            self.logger.warning("Groq LLM not available, using pattern-based fallback")
            pattern_score = self._pattern_based_detection(message.text)
            threshold = getattr(settings, 'SCAM_CONFIDENCE_THRESHOLD', 0.5)
            is_scam = pattern_score >= threshold
            confidence = pattern_score
            reasoning = f"Pattern-based fallback: {pattern_score:.2f}"
            scam_type = self._classify_scam_type(message.text) if is_scam else None
        
        result = ScamDetectionResult(
            is_scam=is_scam,
            confidence=confidence,
            scam_type=scam_type,
            reasoning=reasoning
        )
        
        # Log result
        if session_id:
            log_scam_detection(self.logger, session_id, is_scam, confidence, scam_type)
        
        return result
    
    async def _llm_based_detection(self, text: str) -> Dict[str, Any]:
        """Use Groq LLM for scam detection with Indian context awareness."""
        try:
            system_prompt = """You are an expert Indian scam detection system. Analyze messages for scam indicators specific to India.

INDIAN SCAM PATTERNS TO DETECT:
- UPI fraud (UPI ID, UPI PIN requests)
- Banking fraud (SBI, HDFC, ICICI, Axis Bank impersonation)
- OTP/verification code phishing
- Account blocking threats
- Prize/lottery scams (Rs/INR amounts)
- Payment failure/refund scams
- KYC verification scams
- Aadhaar/PAN card requests
- Customer care impersonation
- Urgency tactics in Hindi/English

SCAM TYPES:
- credential_phishing: Asking for OTP, PIN, passwords, CVV
- financial_threat: Account blocking, suspicious activity warnings
- prize_scam: Lottery, cashback, rewards
- payment_fraud: UPI payment failures, refund requests
- impersonation: Bank, government, customer care
- general_scam: Other scam patterns

Respond ONLY with valid JSON:
{
  "is_scam": true/false,
  "confidence": 0.0-1.0,
  "scam_type": "credential_phishing" or null,
  "reasoning": "Brief explanation"
}"""
            
            response = self.client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Analyze this message:\n\n{text}"}
                ],
                max_tokens=200,
                temperature=0.1
            )
            
            llm_response = response.choices[0].message.content.strip()
            
            # Parse JSON response
            try:
                result = json.loads(llm_response)
                return {
                    'is_scam': result.get('is_scam', False),
                    'confidence': result.get('confidence', 0.5),
                    'scam_type': result.get('scam_type'),
                    'reasoning': f"Groq LLM: {result.get('reasoning', 'Analyzed')}"
                }
            except json.JSONDecodeError:
                # Fallback parsing if JSON is invalid
                is_scam = 'true' in llm_response.lower() or 'scam' in llm_response.lower()
                confidence = 0.7 if is_scam else 0.3
                return {
                    'is_scam': is_scam,
                    'confidence': confidence,
                    'scam_type': None,
                    'reasoning': f"Groq LLM (parsed): {llm_response[:100]}"
                }
                
        except Exception as e:
            self.logger.error(f"LLM detection failed: {str(e)}")
            # Fallback to pattern-based
            pattern_score = self._pattern_based_detection(text)
            return {
                'is_scam': pattern_score > 0.15,
                'confidence': min(pattern_score * 3.5, 0.95),
                'scam_type': self._classify_scam_type(text) if pattern_score > 0.15 else None,
                'reasoning': f"LLM error, pattern fallback: {pattern_score:.2f}"
            }
    
    def _check_hard_scam_patterns(self, text: str) -> Dict[str, Any]:
        """Check for guaranteed scam patterns that always indicate scam."""
        text_lower = text.lower()
        
        # HARD RULES: These patterns ALWAYS mean scam
        hard_scam_rules = [
            {
                'patterns': [r'(?:send|share|provide|give).*?(?:otp|pin|password|cvv)', r'otp.*?(?:send|share|verify)', r'pin.*?(?:send|share)'],
                'scam_type': 'credential_phishing',
                'reasoning': 'Requesting OTP/PIN/password - definite credential phishing'
            },
            {
                'patterns': [r'account.*?(?:blocked|suspended|closed|frozen).*?(?:verify|urgent|immediate)', r'(?:urgent|immediate).*?account.*?(?:blocked|suspended)'],
                'scam_type': 'financial_threat',
                'reasoning': 'Account blocking threat with urgency - definite financial threat scam'
            },
            {
                'patterns': [r'upi.*?(?:pin|id|password)', r'(?:send|share).*?upi.*?(?:id|pin)'],
                'scam_type': 'credential_phishing',
                'reasoning': 'Requesting UPI credentials - definite UPI phishing'
            },
            {
                'patterns': [r'bank account.*?(?:details|number)', r'(?:send|share).*?bank.*?(?:account|details)'],
                'scam_type': 'credential_phishing',
                'reasoning': 'Requesting bank account details - definite phishing'
            },
            {
                'patterns': [r'won.*?(?:prize|lottery|reward)', r'congratulations.*?won', r'winner.*?(?:claim|prize)'],
                'scam_type': 'prize_scam',
                'reasoning': 'Prize/lottery notification - definite prize scam'
            }
        ]
        
        for rule in hard_scam_rules:
            for pattern in rule['patterns']:
                if re.search(pattern, text_lower):
                    return {
                        'is_definite_scam': True,
                        'pattern': pattern,
                        'scam_type': rule['scam_type'],
                        'reasoning': rule['reasoning']
                    }
        
        return {'is_definite_scam': False}
    
    def _pattern_based_detection(self, text: str) -> float:
        """Detect scam patterns using regex matching."""
        text_lower = text.lower()
        total_score = 0.0
        matches = 0
        
        # Check scam patterns
        for category, patterns in self.scam_patterns.items():
            category_matches = 0
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    category_matches += 1
            
            if category_matches > 0:
                # Weight different categories
                category_weights = {
                    'urgency': 0.2,
                    'financial_threat': 0.3,
                    'credential_request': 0.4,
                    'impersonation': 0.25,
                    'reward_bait': 0.15
                }
                total_score += category_weights.get(category, 0.2) * min(category_matches / len(patterns), 1.0)
                matches += 1
        
        # Check individual keywords
        for keyword, weight in self.scam_keywords.items():
            if keyword in text_lower:
                total_score += weight * 0.1  # Reduced weight for individual keywords
        
        return min(total_score, 1.0)
    
    def _classify_scam_type(self, text: str) -> str:
        """Classify the type of scam based on content."""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['otp', 'pin', 'password', 'verify']):
            return 'credential_phishing'
        elif any(word in text_lower for word in ['account blocked', 'suspended', 'unauthorized']):
            return 'financial_threat'
        elif any(word in text_lower for word in ['prize', 'winner', 'congratulations', 'lottery']):
            return 'prize_scam'
        elif any(word in text_lower for word in ['upi', 'payment', 'transaction']):
            return 'payment_fraud'
        elif any(word in text_lower for word in ['bank', 'customer care', 'security team']):
            return 'impersonation'
        else:
            return 'general_scam'