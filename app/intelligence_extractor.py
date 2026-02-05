"""Intelligence extraction from ALL messages (current + conversation history)"""

import re
from typing import List
from app.models import Message, ExtractedIntelligence
import logging

logger = logging.getLogger(__name__)


class IntelligenceExtractor:
    """Extract bank accounts, UPI IDs, phone numbers, and phishing links"""
    
    # Enhanced regex patterns with precision rules
    BANK_ACCOUNT_PATTERN = r'\b\d{9,18}\b'  # 9-18 digit numbers
    UPI_ID_PATTERN = r'\b[\w\.-]+@(?:paytm|phonepe|googlepay|gpay|ybl|oksbi|okaxis|okicici|okhdfcbank|okbizaxis|ikwik|apl|axl|barodampay|ibl|yesbank)\b'  # UPI with valid PSPs
    PHONE_PATTERN = r'(?:(?:\+91[\s-]?)|(?:0)?)?[6-9]\d{9}\b'  # Indian phone numbers with flexible formatting
    PHISHING_LINK_PATTERN = r'https?://[^\s]+'  # URLs
    
    # Context keywords to distinguish number types
    BANK_ACCOUNT_KEYWORDS = ['account', 'ifsc', 'savings', 'current', 'bank', 'a/c', 'acct']
    PHONE_KEYWORDS = ['call', 'phone', 'mobile', 'number', 'contact', 'whatsapp', 'sms']
    
    # Suspicious keywords (not intelligence, but indicators)
    SUSPICIOUS_KEYWORDS = [
        "OTP", "PIN", "password", "CVV", "account blocked", "verify now",
        "urgent", "suspended", "locked", "prize", "lottery", "winner",
        "claim", "refund", "cashback", "KYC", "update details"
    ]
    
    def extract_bank_accounts(self, text: str, exclude_numbers: List[str] = None) -> List[str]:
        """Extract bank account numbers (9-18 digits) with context-aware filtering"""
        if exclude_numbers is None:
            exclude_numbers = []
        
        matches = re.findall(self.BANK_ACCOUNT_PATTERN, text)
        valid_accounts = []
        
        for acc in matches:
            # Skip if already identified as phone number
            if acc in exclude_numbers:
                continue
            
            # For 10-digit numbers: distinguish phones (6-9 prefix) from bank accounts
            if len(acc) == 10:
                if acc[0] in '6789':
                    # Likely phone - only include if bank context present
                    text_lower = text.lower()
                    acc_pos = text_lower.find(acc)
                    if acc_pos >= 0:
                        context_window = text_lower[max(0, acc_pos-30):min(len(text_lower), acc_pos+len(acc)+30)]
                        if any(kw in context_window for kw in self.BANK_ACCOUNT_KEYWORDS):
                            valid_accounts.append(acc)
                    # Skip if no bank context (definitely phone)
                else:
                    # Starts with 0-5: Not a valid phone, likely bank account
                    valid_accounts.append(acc)
                continue
            
            # 9-digit or 11-18 digit numbers: likely bank accounts
            if len(acc) >= 9:
                valid_accounts.append(acc)
        
        return list(set(valid_accounts))  # Remove duplicates
    
    def extract_upi_ids(self, text: str) -> List[str]:
        """Extract UPI IDs (user@psp format) with boundary checks"""
        # Use improved regex that only matches valid PSPs
        matches = re.findall(self.UPI_ID_PATTERN, text, re.IGNORECASE)
        
        # Additional validation: UPI format is typically 4-50 characters
        valid_upis = [
            upi for upi in matches 
            if 4 <= len(upi) <= 50 and '@' in upi
        ]
        return list(set(valid_upis))
    
    def extract_phone_numbers(self, text: str) -> List[str]:
        """Extract Indian phone numbers with strict validation"""
        matches = re.findall(self.PHONE_PATTERN, text)
        normalized = []
        
        for phone in matches:
            # Clean formatting (remove spaces, hyphens, leading zeros)
            phone = phone.replace(' ', '').replace('-', '').lstrip('0')
            
            # Remove +91 prefix for validation
            if phone.startswith('+91'):
                phone = phone[3:]
            
            # Validate: must be exactly 10 digits starting with 6-9
            if len(phone) == 10 and phone[0] in '6789' and phone.isdigit():
                normalized.append(f"+91{phone}")
        
        return list(set(normalized))  # Remove duplicates
    
    def extract_phishing_links(self, text: str) -> List[str]:
        """Extract URLs (potential phishing links)"""
        matches = re.findall(self.PHISHING_LINK_PATTERN, text)
        return list(set(matches))
    
    def extract_suspicious_keywords(self, text: str) -> List[str]:
        """Extract suspicious keywords found in text"""
        found_keywords = []
        text_lower = text.lower()
        for keyword in self.SUSPICIOUS_KEYWORDS:
            if keyword.lower() in text_lower:
                found_keywords.append(keyword)
        return list(set(found_keywords))
    
    def extract_from_conversation(
        self, 
        current_message: Message, 
        conversation_history: List[Message]
    ) -> ExtractedIntelligence:
        """
        Extract intelligence from ALL messages (current + history)
        Returns ExtractedIntelligence with exact values (no masking)
        """
        # Combine all message texts
        all_texts = [msg.text for msg in conversation_history]
        all_texts.append(current_message.text)
        combined_text = " ".join(all_texts)
        
        logger.info(f"Extracting intelligence from {len(all_texts)} messages")
        
        # Extract phones FIRST to avoid double-counting with bank accounts
        phone_numbers = self.extract_phone_numbers(combined_text)
        
        # Extract bank accounts EXCLUDING numbers already identified as phones
        phone_numbers_raw = [p.replace('+91', '') for p in phone_numbers]
        bank_accounts = self.extract_bank_accounts(combined_text, exclude_numbers=phone_numbers_raw)
        
        # Extract other intelligence
        upi_ids = self.extract_upi_ids(combined_text)
        phishing_links = self.extract_phishing_links(combined_text)
        suspicious_keywords = self.extract_suspicious_keywords(combined_text)
        
        # Log findings
        if bank_accounts:
            logger.info(f"✓ Found {len(bank_accounts)} bank account(s)")
        if upi_ids:
            logger.info(f"✓ Found {len(upi_ids)} UPI ID(s)")
        if phone_numbers:
            logger.info(f"✓ Found {len(phone_numbers)} phone number(s)")
        if phishing_links:
            logger.info(f"✓ Found {len(phishing_links)} phishing link(s)")
        if suspicious_keywords:
            logger.info(f"✓ Found keywords: {', '.join(suspicious_keywords)}")
        
        return ExtractedIntelligence(
            bankAccounts=bank_accounts,
            upiIds=upi_ids,
            phishingLinks=phishing_links,
            phoneNumbers=phone_numbers,
            suspiciousKeywords=suspicious_keywords
        )
    
    def has_real_intelligence(self, intelligence: ExtractedIntelligence) -> bool:
        """
        Check if real intelligence was extracted (not just keywords)
        Real intelligence = bank accounts, UPI IDs, phone numbers, or links
        """
        return bool(
            intelligence.bankAccounts or 
            intelligence.upiIds or 
            intelligence.phoneNumbers or 
            intelligence.phishingLinks
        )
