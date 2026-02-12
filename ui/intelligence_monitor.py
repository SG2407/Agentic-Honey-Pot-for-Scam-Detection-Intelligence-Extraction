"""
Intelligence Monitor - Parallel extraction for UI display
This runs independently from the main app's intelligence extraction
Reuses detection logic but doesn't interfere with callbacks
"""

import re
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

class IntelligenceMonitor:
    """Extract intelligence for UI display (parallel to main app)"""
    
    # Reuse patterns from main app's intelligence_extractor.py
    BANK_ACCOUNT_PATTERN = r'\b\d{9,18}\b'
    UPI_ID_PATTERN = r'\b[a-zA-Z0-9.\-_]{2,}@[a-zA-Z]{2,}\b'
    PHONE_PATTERN = r'(?<!\d)(?:(?:\+91[\s-]?)|(?:0)?)?[6-9]\d{9}(?!\d)'
    PHISHING_LINK_PATTERN = r'https?://[^\s]+'
    PAN_PATTERN = r'\b[A-Z]{5}[0-9]{4}[A-Z]\b'
    AADHAAR_PATTERN = r'\b\d{4}\s?\d{4}\s?\d{4}\b'
    
    BANK_KEYWORDS = ['account', 'ifsc', 'savings', 'current', 'bank', 'a/c', 'acct']
    PHONE_KEYWORDS = ['call', 'phone', 'mobile', 'number', 'contact', 'whatsapp', 'sms']
    
    SUSPICIOUS_KEYWORDS = [
        "OTP", "PIN", "password", "CVV", "account blocked", "verify now",
        "urgent", "suspended", "locked", "prize", "lottery", "winner",
        "claim", "refund", "cashback", "KYC", "update details", "immediately",
        "click here", "link", "verify account", "confirm identity", "expire"
    ]
    
    # Scam detection patterns
    SCAM_PATTERNS = {
        "credential_phishing": [
            r'\b(OTP|PIN|password|CVV|card\s*number|expiry|Aadhaar|PAN)\b',
            r'(share|send|provide|tell|give)\s+(me|us)?\s*(your|the)?\s*(OTP|PIN|password)',
            r'verify\s+(your\s+)?(account|identity|details)'
        ],
        "financial_threat": [
            r'\b(account|card)\s+(blocked|suspended|locked|frozen|deactivated)\b',
            r'\b(urgent|immediate|within|expire)\b',
            r'penalty|fine|legal\s+action|arrest'
        ],
        "reward_scam": [
            r'\b(won|winner|prize|lottery|congratulations|cashback|refund)\b',
            r'\b(claim|collect|redeem)\s+(your|the)?\s*(prize|reward|amount)\b'
        ],
        "impersonation": [
            r'\b(bank|government|police|tax|department|officer|agent|official)\b',
            r'\b(RBI|Income\s*Tax|GST|Aadhaar|PAN)\b'
        ]
    }
    
    def extract_intelligence(self, current_message: str, history: List[Dict]) -> Dict:
        """
        Extract intelligence from current message + history
        Returns dict with all intelligence fields
        """
        # Combine all messages
        all_text = current_message + " "
        for msg in history:
            all_text += msg.get("text", "") + " "
        
        all_text_lower = all_text.lower()
        
        # Extract bank accounts
        bank_accounts = []
        potential_accounts = re.findall(self.BANK_ACCOUNT_PATTERN, all_text)
        for acc in potential_accounts:
            # Validate length (9-18 digits)
            if 9 <= len(acc) <= 18:
                # Check context for bank keywords
                if any(kw in all_text_lower for kw in self.BANK_KEYWORDS):
                    if acc not in bank_accounts:
                        bank_accounts.append(acc)
        
        # Extract UPI IDs
        upi_ids = []
        potential_upis = re.findall(self.UPI_ID_PATTERN, all_text)
        for upi in potential_upis:
            # Validate format
            if '@' in upi and len(upi.split('@')[0]) >= 2:
                if upi not in upi_ids:
                    upi_ids.append(upi)
        
        # Extract phone numbers
        phone_numbers = []
        potential_phones = re.findall(self.PHONE_PATTERN, all_text)
        for phone in potential_phones:
            # Clean and normalize
            phone_clean = re.sub(r'[\s\-]', '', phone)
            if phone_clean.startswith('+91'):
                phone_clean = phone_clean[3:]
            elif phone_clean.startswith('0'):
                phone_clean = phone_clean[1:]
            
            # Validate Indian mobile (starts with 6-9, 10 digits)
            if len(phone_clean) == 10 and phone_clean[0] in '6789':
                formatted = f"+91{phone_clean}"
                if formatted not in phone_numbers:
                    phone_numbers.append(formatted)
        
        # Extract phishing links
        phishing_links = []
        potential_links = re.findall(self.PHISHING_LINK_PATTERN, all_text)
        for link in potential_links:
            # Basic validation
            if link.startswith(('http://', 'https://')):
                if link not in phishing_links:
                    phishing_links.append(link)
        
        # Extract suspicious keywords
        suspicious_keywords = []
        for keyword in self.SUSPICIOUS_KEYWORDS:
            if keyword.lower() in all_text_lower:
                if keyword not in suspicious_keywords:
                    suspicious_keywords.append(keyword)
        
        return {
            "bankAccounts": bank_accounts,
            "upiIds": upi_ids,
            "phoneNumbers": phone_numbers,
            "phishingLinks": phishing_links,
            "suspiciousKeywords": suspicious_keywords
        }
    
    def detect_scam(self, current_message: str, history: List[Dict]) -> Dict:
        """
        Detect scam type and confidence
        Returns: {is_scam: bool, scam_type: str, confidence: float}
        """
        # Combine all messages
        all_text = current_message + " "
        for msg in history:
            all_text += msg.get("text", "") + " "
        
        all_text_lower = all_text.lower()
        
        # Check patterns for each scam type
        scam_scores = {
            "credential_phishing": 0,
            "financial_threat": 0,
            "reward_scam": 0,
            "impersonation": 0
        }
        
        for scam_type, patterns in self.SCAM_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, all_text, re.IGNORECASE):
                    scam_scores[scam_type] += 1
        
        # Find highest score
        max_score = max(scam_scores.values())
        
        if max_score == 0:
            return {
                "is_scam": False,
                "scam_type": "unknown",
                "confidence": 0.0
            }
        
        # Get scam type with highest score
        scam_type = max(scam_scores.items(), key=lambda x: x[1])[0]
        
        # Calculate confidence (simple heuristic)
        confidence = min(0.5 + (max_score * 0.15), 0.95)
        
        return {
            "is_scam": True,
            "scam_type": scam_type,
            "confidence": round(confidence, 2)
        }
    
    def has_real_intelligence(self, intelligence: Dict) -> bool:
        """Check if intelligence contains real data (not just keywords)"""
        return bool(
            intelligence.get("bankAccounts") or
            intelligence.get("upiIds") or
            intelligence.get("phoneNumbers") or
            intelligence.get("phishingLinks")
        )
