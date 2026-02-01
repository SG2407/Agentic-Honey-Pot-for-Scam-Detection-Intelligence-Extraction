"""Intelligence extraction from ALL messages (current + conversation history)"""

import re
from typing import List
from app.models import Message, ExtractedIntelligence
import logging

logger = logging.getLogger(__name__)


class IntelligenceExtractor:
    """Extract bank accounts, UPI IDs, phone numbers, and phishing links"""
    
    # Regex patterns for intelligence extraction
    BANK_ACCOUNT_PATTERN = r'\b\d{9,18}\b'  # 9-18 digit numbers
    UPI_ID_PATTERN = r'\b[\w\.-]+@[\w\.-]+\b'  # user@provider format
    PHONE_PATTERN = r'(?:\+91|0)?[6-9]\d{9}\b'  # Indian phone numbers (removed leading \b for + support)
    PHISHING_LINK_PATTERN = r'https?://[^\s]+'  # URLs
    
    # Suspicious keywords (not intelligence, but indicators)
    SUSPICIOUS_KEYWORDS = [
        "OTP", "PIN", "password", "CVV", "account blocked", "verify now",
        "urgent", "suspended", "locked", "prize", "lottery", "winner",
        "claim", "refund", "cashback", "KYC", "update details"
    ]
    
    def extract_bank_accounts(self, text: str) -> List[str]:
        """Extract bank account numbers (9-18 digits)"""
        matches = re.findall(self.BANK_ACCOUNT_PATTERN, text)
        # Filter out common numbers that aren't bank accounts (like years, phone parts)
        valid_accounts = [acc for acc in matches if len(acc) >= 10]
        return list(set(valid_accounts))  # Remove duplicates
    
    def extract_upi_ids(self, text: str) -> List[str]:
        """Extract UPI IDs (user@provider format)"""
        matches = re.findall(self.UPI_ID_PATTERN, text)
        # Filter to only keep valid UPI patterns (must have @ and common providers)
        upi_providers = ['paytm', 'phonepe', 'googlepay', 'gpay', 'ybl', 'oksbi', 'okaxis', 'okicici']
        valid_upis = [
            upi for upi in matches 
            if any(provider in upi.lower() for provider in upi_providers)
        ]
        return list(set(valid_upis))
    
    def extract_phone_numbers(self, text: str) -> List[str]:
        """Extract Indian phone numbers"""
        matches = re.findall(self.PHONE_PATTERN, text)
        # Normalize format (remove leading 0, add +91)
        normalized = []
        for phone in matches:
            phone = phone.lstrip('0')
            if not phone.startswith('+91'):
                phone = f"+91{phone}"
            normalized.append(phone)
        return list(set(normalized))
    
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
        
        # Extract all types of intelligence
        bank_accounts = self.extract_bank_accounts(combined_text)
        upi_ids = self.extract_upi_ids(combined_text)
        phone_numbers = self.extract_phone_numbers(combined_text)
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
