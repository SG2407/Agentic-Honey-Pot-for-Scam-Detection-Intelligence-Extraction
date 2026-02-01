import re
from typing import List, Dict, Any
from app.models import Message, ExtractedIntelligence
from app.utils.logger import setup_logger, log_intelligence_extraction

class IntelligenceExtractor:
    """Extracts actionable intelligence from scam conversations."""
    
    def __init__(self):
        self.logger = setup_logger(__name__)
        
        # Regex patterns for intelligence extraction
        self.patterns = {
            'bank_accounts': [
                r'\b\d{9,18}\b',  # Generic account numbers
                r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # Formatted account numbers
                r'account[:\s]*([\d\-\s]{9,20})',
                r'acc[\s]*no[:\s]*([\d\-\s]{9,20})'
            ],
            'upi_ids': [
                r'\b[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\b',  # Generic UPI format
                r'\b\w+@(?:paytm|phonepe|googlepay|amazonpay|ybl|axl|ibl|okaxis|okhdfcbank|oksbi|okicici)\b',
                r'upi[\s]*id[:\s]*([a-zA-Z0-9._@-]+)',
                r'payment[\s]*id[:\s]*([a-zA-Z0-9._@-]+)'
            ],
            'phone_numbers': [
                r'\+91[\s-]?[6-9]\d{9}',  # Indian mobile numbers
                r'\b[6-9]\d{9}\b',  # 10-digit mobile numbers
                r'(?:call|contact|phone)[:\s]*(\+?\d[\d\s-]{8,15})',
                r'(?:whatsapp|wa)[:\s]*(\+?\d[\d\s-]{8,15})'
            ],
            'phishing_links': [
                r'https?://[^\s<>"]+',  # HTTP/HTTPS URLs
                r'www\.[^\s<>"]+',  # www URLs
                r'[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?',  # Domain-like patterns
                r'(?:click|visit|go to)[:\s]*(\S+\.[a-zA-Z]{2,}(?:/\S*)?)'
            ]
        }
        
        # Suspicious keywords for context
        self.suspicious_keywords = [
            'urgent', 'verify', 'blocked', 'suspended', 'otp', 'pin',
            'account', 'bank', 'upi', 'payment', 'transaction', 'failed',
            'unauthorized', 'suspicious', 'fraud', 'security', 'prize',
            'winner', 'congratulations', 'free', 'reward', 'cashback',
            'lottery', 'claim', 'activate', 'confirm', 'update'
        ]
    
    def extract_from_conversation(self, messages: List[Message], session_id: str = None) -> ExtractedIntelligence:
        """Extract intelligence from entire conversation."""
        
        # Combine all message texts
        full_text = " ".join([msg.text for msg in messages])
        
        # Extract different types of intelligence
        bank_accounts = self._extract_bank_accounts(full_text)
        upi_ids = self._extract_upi_ids(full_text)
        phone_numbers = self._extract_phone_numbers(full_text)
        phishing_links = self._extract_phishing_links(full_text)
        suspicious_keywords = self._extract_suspicious_keywords(full_text)
        
        intelligence = ExtractedIntelligence(
            bankAccounts=bank_accounts,
            upiIds=upi_ids,
            phishingLinks=phishing_links,
            phoneNumbers=phone_numbers,
            suspiciousKeywords=suspicious_keywords
        )
        
        # Log extraction results
        if session_id:
            log_intelligence_extraction(
                self.logger, 
                session_id, 
                intelligence.dict()
            )
        
        return intelligence
    
    def _extract_bank_accounts(self, text: str) -> List[str]:
        """Extract bank account numbers."""
        accounts = set()
        
        for pattern in self.patterns['bank_accounts']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Clean and validate
                clean_account = re.sub(r'[^\d]', '', str(match))
                if 9 <= len(clean_account) <= 18:  # Valid account number length
                    # Send EXACT value, no masking
                    accounts.add(clean_account)
        
        return list(accounts)
    
    def _extract_upi_ids(self, text: str) -> List[str]:
        """Extract UPI IDs."""
        upi_ids = set()
        
        for pattern in self.patterns['upi_ids']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                clean_upi = str(match).strip()
                if '@' in clean_upi and len(clean_upi) > 5:
                    # Send EXACT value, no masking
                    upi_ids.add(clean_upi)
        
        return list(upi_ids)
    
    def _extract_phone_numbers(self, text: str) -> List[str]:
        """Extract phone numbers."""
        phone_numbers = set()
        
        for pattern in self.patterns['phone_numbers']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Clean phone number
                clean_phone = re.sub(r'[^\d+]', '', str(match))
                if len(clean_phone) >= 10:
                    # Send EXACT value, no masking
                    phone_numbers.add(clean_phone)
        
        return list(phone_numbers)
    
    def _extract_phishing_links(self, text: str) -> List[str]:
        """Extract suspicious links."""
        links = set()
        
        for pattern in self.patterns['phishing_links']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                clean_link = str(match).strip()
                if self._is_suspicious_link(clean_link):
                    # Send EXACT value, no masking
                    links.add(clean_link)
        
        return list(links)
    
    def _extract_suspicious_keywords(self, text: str) -> List[str]:
        """Extract suspicious keywords found in text."""
        found_keywords = set()
        text_lower = text.lower()
        
        for keyword in self.suspicious_keywords:
            if keyword in text_lower:
                found_keywords.add(keyword)
        
        # Also look for variations and phrases
        additional_patterns = {
            'verify now': r'verify\s+now',
            'act immediately': r'act\s+immediately',
            'account blocked': r'account\s+blocked',
            'urgent action': r'urgent\s+action',
            'click here': r'click\s+here',
            'call immediately': r'call\s+immediately'
        }
        
        for phrase, pattern in additional_patterns.items():
            if re.search(pattern, text_lower):
                found_keywords.add(phrase)
        
        return list(found_keywords)
    
    def _is_suspicious_link(self, link: str) -> bool:
        """Check if a link appears suspicious."""
        suspicious_indicators = [
            # Suspicious domains
            'bit.ly', 'tinyurl.com', 't.co', 'short.link',
            # Suspicious TLDs
            '.tk', '.ml', '.cf', '.ga',
            # Common scam patterns
            'secure-bank', 'verify-account', 'urgent-update',
            'prize-claim', 'winner-lottery', 'free-reward'
        ]
        
        link_lower = link.lower()
        return any(indicator in link_lower for indicator in suspicious_indicators)
    
    def _mask_domain(self, domain: str) -> str:
        """Mask domain name for safety."""
        if '.' in domain:
            parts = domain.split('.')
            if len(parts) >= 2:
                # Mask the main domain but keep TLD
                main_part = parts[-2]
                tld = parts[-1]
                masked_main = main_part[:2] + 'X' * (len(main_part) - 2) if len(main_part) > 2 else main_part
                return f"{masked_main}.{tld}"
        return domain[:3] + 'X' * max(0, len(domain) - 3)