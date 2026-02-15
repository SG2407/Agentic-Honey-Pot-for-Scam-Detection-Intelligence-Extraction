"""Intelligence extraction from ALL messages (current + conversation history)"""

import re
from typing import List
from app.models import Message, ExtractedIntelligence
import logging

logger = logging.getLogger(__name__)


class IntelligenceExtractor:
    """Extract bank accounts, UPI IDs, phone numbers, and phishing links with strict validation"""
    
    # PRIORITY 1: Enhanced patterns with Indian-specific validation
    BANK_ACCOUNT_PATTERN = r'\b\d{9,18}\b'  # 9-18 digit numbers
    
    # PAN card: [A-Z]{5}[0-9]{4}[A-Z] (e.g., ABCDE1234F)
    PAN_PATTERN = r'\b[A-Z]{5}[0-9]{4}[A-Z]\b'
    
    # Aadhaar: 12 digits with optional spaces (e.g., 1234 5678 9012)
    AADHAAR_PATTERN = r'\b\d{4}\s?\d{4}\s?\d{4}\b'
    
    # UPI: strict format ^[a-zA-Z0-9.\-_]{2,}@[a-zA-Z]{2,}$
    UPI_ID_PATTERN = r'\b[a-zA-Z0-9.\-_]{2,}@[a-zA-Z]{2,}\b'
    
    # Indian phone: +91 followed by 10 digits starting with 6-9
    PHONE_PATTERN = r'(?<!\d)(?:(?:\+91[\s-]?)|(?:0)?)?[6-9]\d{9}(?!\d)'
    
    # Email addresses
    EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    
    PHISHING_LINK_PATTERN = r'https?://[^\s]+'
    
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
        """Extract bank account numbers with length validation and phone/Aadhaar disambiguation"""
        if exclude_numbers is None:
            exclude_numbers = []
        
        matches = re.findall(self.BANK_ACCOUNT_PATTERN, text)
        valid_accounts = []
        
        for acc in matches:
            # Skip if already identified as phone/PAN/Aadhaar
            if acc in exclude_numbers:
                continue
            
            acc_len = len(acc)
            
            # Length validation: Indian bank accounts are typically 9-18 digits
            if acc_len < 9 or acc_len > 18:
                continue
            
            # For 10-digit numbers: strict disambiguation
            if acc_len == 10:
                if acc[0] in '6789':
                    # Likely phone - only include if explicit bank context
                    text_lower = text.lower()
                    acc_pos = text_lower.find(acc)
                    if acc_pos >= 0:
                        context_window = text_lower[max(0, acc_pos-30):min(len(text_lower), acc_pos+len(acc)+30)]
                        if any(kw in context_window for kw in self.BANK_ACCOUNT_KEYWORDS):
                            valid_accounts.append(acc)
                    continue  # Skip if no bank context
                else:
                    # Starts with 0-5: Not a valid phone, likely bank account
                    valid_accounts.append(acc)
            
            # 12-digit: Could be Aadhaar - skip if matches Aadhaar pattern
            elif acc_len == 12:
                # Check if it's formatted like Aadhaar (might have been without spaces)
                if re.match(r'^\d{12}$', acc):
                    # Skip - likely Aadhaar without spaces
                    continue
                valid_accounts.append(acc)
            
            # 9, 11, 13-18 digits: likely valid bank accounts
            else:
                valid_accounts.append(acc)
        
        return list(set(valid_accounts))
    
    def extract_upi_ids(self, text: str) -> List[str]:
        """
        PRIORITY 1: Extract UPI IDs with strict format validation
        Pattern: ^[a-zA-Z0-9.\-_]{2,}@[a-zA-Z]{2,}$
        """
        matches = re.findall(self.UPI_ID_PATTERN, text, re.IGNORECASE)
        
        valid_upis = []
        for upi in matches:
            # Length validation: 4-50 characters total
            if not (4 <= len(upi) <= 50):
                continue
            
            # Split and validate parts
            parts = upi.split('@')
            if len(parts) != 2:
                continue
            
            username, domain = parts
            
            # Username validation: 2+ chars, alphanumeric with .-_
            if len(username) < 2 or not re.match(r'^[a-zA-Z0-9.\-_]+$', username):
                continue
            
            # Domain validation: 2+ chars, alphabetic only
            if len(domain) < 2 or not re.match(r'^[a-zA-Z]+$', domain):
                continue
            
            # Additional robustness: common PSPs (paytm, phonepe, gpay, ybl, etc.)
            valid_upis.append(upi.lower())
        
        return list(set(valid_upis))
    
    def extract_phone_numbers(self, text: str) -> List[str]:
        """
        PRIORITY 1: Extract Indian phone numbers with strict validation
        Format: +91 followed by 10 digits starting with 6-9
        """
        matches = re.findall(self.PHONE_PATTERN, text)
        normalized = []
        
        for phone in matches:
            # Clean formatting (remove spaces, hyphens)
            phone = phone.replace(' ', '').replace('-', '')
            
            # Remove leading zeros
            phone = phone.lstrip('0')
            
            # Remove +91 prefix for validation
            if phone.startswith('+91'):
                phone = phone[3:]
            elif phone.startswith('91') and len(phone) == 12:
                phone = phone[2:]
            
            # Strict validation: exactly 10 digits starting with 6-9
            if len(phone) == 10 and phone[0] in '6789' and phone.isdigit():
                normalized.append(f"+91{phone}")
        
        return list(set(normalized))
    
    def extract_emails(self, text: str) -> List[str]:
        """Extract email addresses from text"""
        matches = re.findall(self.EMAIL_PATTERN, text, re.IGNORECASE)
        # Normalize to lowercase and remove duplicates
        normalized = [email.lower() for email in matches]
        return list(set(normalized))
    
    def extract_pan_cards(self, text: str) -> List[str]:
        """Extract PAN card numbers: [A-Z]{5}[0-9]{4}[A-Z]"""
        matches = re.findall(self.PAN_PATTERN, text)
        return list(set(matches))
    
    def extract_aadhaar_numbers(self, text: str) -> List[str]:
        """Extract Aadhaar numbers: 12 digits with optional spaces"""
        matches = re.findall(self.AADHAAR_PATTERN, text)
        # Normalize: remove spaces
        normalized = [match.replace(' ', '') for match in matches]
        # Validate: exactly 12 digits
        validated = [num for num in normalized if len(num) == 12 and num.isdigit()]
        return list(set(validated))
    
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
        
        # Extract PAN and Aadhaar (identity documents)
        pan_cards = self.extract_pan_cards(combined_text)
        aadhaar_numbers = self.extract_aadhaar_numbers(combined_text)
        
        # Build exclusion list: phones + PAN + Aadhaar
        exclude_numbers = [p.replace('+91', '') for p in phone_numbers]
        exclude_numbers.extend(aadhaar_numbers)
        
        # Extract bank accounts EXCLUDING phones/Aadhaar
        bank_accounts = self.extract_bank_accounts(combined_text, exclude_numbers=exclude_numbers)
        
        # Extract other intelligence
        upi_ids = self.extract_upi_ids(combined_text)
        phishing_links = self.extract_phishing_links(combined_text)
        email_addresses = self.extract_emails(combined_text)
        suspicious_keywords = self.extract_suspicious_keywords(combined_text)
        
        # Add PAN/Aadhaar to suspicious keywords if found (for logging)
        if pan_cards:
            suspicious_keywords.extend([f"PAN:{p}" for p in pan_cards])
        if aadhaar_numbers:
            suspicious_keywords.extend([f"Aadhaar:{a}" for a in aadhaar_numbers])
        
        # Log findings
        if bank_accounts:
            logger.info(f"✓ Found {len(bank_accounts)} bank account(s)")
        if upi_ids:
            logger.info(f"✓ Found {len(upi_ids)} UPI ID(s)")
        if phone_numbers:
            logger.info(f"✓ Found {len(phone_numbers)} phone number(s)")
        if phishing_links:
            logger.info(f"✓ Found {len(phishing_links)} phishing link(s)")
        if email_addresses:
            logger.info(f"✓ Found {len(email_addresses)} email address(es)")
        if suspicious_keywords:
            logger.info(f"✓ Found keywords: {', '.join(suspicious_keywords)}")
        
        return ExtractedIntelligence(
            bankAccounts=bank_accounts,
            upiIds=upi_ids,
            phishingLinks=phishing_links,
            phoneNumbers=phone_numbers,
            emailAddresses=email_addresses,
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
    
    def calculate_intelligence_quality(self, intelligence: ExtractedIntelligence) -> float:
        """
        Calculate intelligence quality as a percentage (0.0 to 1.0)
        Based on how many of the 4 critical intel fields have data
        (excludes suspiciousKeywords as it's less valuable)
        
        Returns:
            float: Quality percentage (0.0 = no intel, 1.0 = all 4 fields populated)
        """
        critical_fields = [
            bool(intelligence.bankAccounts),
            bool(intelligence.upiIds),
            bool(intelligence.phoneNumbers),
            bool(intelligence.phishingLinks)
        ]
        
        populated_fields = sum(critical_fields)
        total_fields = len(critical_fields)  # 4 fields
        
        quality = populated_fields / total_fields if total_fields > 0 else 0.0
        return quality

