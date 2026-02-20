"""AI conversation agent for natural scammer engagement"""

import os
import re
from datetime import datetime, timezone
from typing import List
from app.models import Message
from app.llm_provider import LLMManager  # PRIORITY 2: Abstract LLM provider
import logging

logger = logging.getLogger(__name__)


class ConversationAgent:
    """Generate human-like responses to engage scammers naturally"""
    
    def __init__(self):
        """Initialize ConversationAgent with LLM manager (PRIORITY 2)"""
        self.llm_manager = LLMManager()  # Supports OpenRouter + Groq with fallback
        self.used_phrases = {}  # Track used phrases per session to avoid repetition
    
    # Enhanced personas with human-like engagement patterns
    PERSONAS = {
        "worried_customer": {
            "style": "concerned, anxious, wants to fix problem quickly, asks clarifying questions",
            "traits": "shows genuine worry, mentions work/family context, types in hurried manner with occasional typos, gradually reveals personal banking info",
            "example": "Oh no... last week also I got similar message. Which account exactly? I have two accounts, salary and savings.",
            "speech_patterns": ["oh no", "seriously?", "this is bad", "I need to fix this", "what should I do"],
            "behavioral_traits": ["checks account frequently", "mentions deadlines", "expresses financial concerns", "asks about timeframes"]
        },
        "excited_winner": {
            "style": "excited but cautious, eager yet confused about prize claim process, oscillates between enthusiasm and doubt",
            "traits": "uses exclamation marks frequently, expresses disbelief, asks about costs/fees, mentions telling family, wants quick resolution",
            "example": "Really?! I never entered any lottery... but if its true, amazing! How do I verify this is real? Do I need to pay anything first?",
            "speech_patterns": ["wow!", "really?!", "amazing", "cant believe this", "is this for real"],
            "behavioral_traits": ["shares excitement", "asks about verification", "mentions family/friends", "questions fees"]
        },
        "confused_elderly": {
            "style": "confused, needs step-by-step help, makes spelling/grammar mistakes, trusting but technologically challenged",
            "traits": "asks to repeat instructions, mentions needing help from family, makes typos, uses simple words, takes time to understand",
            "example": "I dont undorstand properly... can you explain slowly? My son usually helps me with phone but he is not here now. Which button I should press?",
            "speech_patterns": ["dont understand", "wait let me see", "which button", "my son/daughter helps", "can you repeat"],
            "behavioral_traits": ["mentions family members", "expresses confusion", "asks for repetition", "willing to trust"]
        },
        "cautious_user": {
            "style": "somewhat skeptical, wants verification, willing to cooperate only if convinced, has past experience with scams",
            "traits": "asks for credentials, mentions previous fraud attempts, tests authenticity, demands proof, conditional compliance",
            "example": "I am not sure... last time someone tried to cheat me. Can you tell me your employee ID? Or should I call the bank directly to verify?",
            "speech_patterns": ["not sure about this", "sounds suspicious", "how do I verify", "last time", "prove it"],
            "behavioral_traits": ["mentions past scam experience", "asks for employee ID", "threatens to verify directly", "conditional trust"]
        }
    }
    
    def _select_persona(self, scam_type: str) -> str:
        """Select appropriate persona based on scam type"""
        persona_map = {
            "financial_threat": "worried_customer",
            "credential_phishing": "confused_elderly",
            "prize_scam": "excited_winner",
            "reward_scam": "excited_winner",  # Maps to same persona as prize_scam
            "impersonation": "cautious_user"
        }
        return persona_map.get(scam_type, "worried_customer")
    
    def _extract_already_revealed_intel(self, history: List[Message]) -> dict:
        """
        Extract what intelligence the scammer has ALREADY provided in conversation.
        This prevents the agent from asking for the same information repeatedly.
        """
        conversation_text = " ".join([msg.text for msg in history])
        
        revealed = {
            "phone_numbers": [],
            "bank_accounts": [],
            "upi_ids": [],
            "links": [],
            "emails": []
        }
        
        # Phone numbers (Indian format)
        phone_pattern = r'(?:(?:\+91[\s-]?)|(?:0)?)?([6-9]\d{9})'
        revealed["phone_numbers"] = list(set(re.findall(phone_pattern, conversation_text)))
        
        # Bank account numbers (9-18 digits)
        bank_pattern = r'\b\d{9,18}\b'
        potential_banks = re.findall(bank_pattern, conversation_text)
        # Filter out phone numbers from bank accounts
        revealed["bank_accounts"] = [acc for acc in potential_banks if len(acc) >= 12 and acc not in revealed["phone_numbers"]]
        
        # UPI IDs
        upi_pattern = r'\b[a-zA-Z0-9.\-_]{2,}@[a-zA-Z]{2,}\b'
        revealed["upi_ids"] = list(set(re.findall(upi_pattern, conversation_text)))
        
        # Links
        link_pattern = r'https?://[^\s]+'
        revealed["links"] = list(set(re.findall(link_pattern, conversation_text)))
        
        # Emails
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        revealed["emails"] = list(set(re.findall(email_pattern, conversation_text)))
        
        return revealed
    
    def _format_revealed_intel(self, revealed: dict) -> str:
        """Format already revealed intelligence for prompt"""
        lines = []
        
        if revealed["phone_numbers"]:
            lines.append(f"✓ Phone number(s): {', '.join(revealed['phone_numbers'])}")
            lines.append(f"  → DO NOT ask for phone number again! You already know: {', '.join(revealed['phone_numbers'])}")
        else:
            lines.append("✗ Phone number: NOT YET PROVIDED - Ask for it naturally if appropriate")
        
        if revealed["bank_accounts"]:
            lines.append(f"✓ Bank account(s): {', '.join(revealed['bank_accounts'])}")
            lines.append(f"  → DO NOT ask for account number again! You already have it")
        else:
            lines.append("✗ Bank account: NOT YET PROVIDED - Extract if payment mentioned")
        
        if revealed["upi_ids"]:
            lines.append(f"✓ UPI ID(s): {', '.join(revealed['upi_ids'])}")
            lines.append(f"  → DO NOT ask for UPI ID again!")
        else:
            lines.append("✗ UPI ID: NOT YET PROVIDED - Ask if payment involved")
        
        if revealed["links"]:
            lines.append(f"✓ Link(s): {', '.join(revealed['links'])}")
            lines.append(f"  → DO NOT ask for link again!")
        else:
            lines.append("✗ Links: NOT YET PROVIDED - Ask if they mention website")
        
        if revealed["emails"]:
            lines.append(f"✓ Email(s): {', '.join(revealed['emails'])}")
            lines.append(f"  → DO NOT ask for email again!")
        else:
            lines.append("✗ Email: NOT YET PROVIDED - Extract if they claim to be official")
        
        return "\n".join(lines)
    
    def _build_conversation_context(self, history: List[Message]) -> str:
        """Build conversation context from history with emotional progression"""
        if not history:
            return "This is the first message in the conversation. You're just starting to engage."
        
        context_lines = []
        for i, msg in enumerate(history[-6:], 1):  # Last 6 messages for richer context
            sender_label = "Scammer" if msg.sender == "scammer" else "You (previous)"
            context_lines.append(f"[Turn {i}] {sender_label}: {msg.text}")
        
        # Add emotional progression note
        turn_count = len(history)
        if turn_count <= 2:
            emotion_state = "You're initially cautious, just starting to understand the situation."
        elif turn_count <= 5:
            emotion_state = "You're becoming more engaged, asking questions, showing concern/interest."
        else:
            emotion_state = "You're deeply engaged now, showing trust gradually, considering their requests."
        
        return "\n".join(context_lines) + "\n\n" + emotion_state
    
    def _identify_red_flags(self, scammer_message: str) -> str:
        """
        Identify red flags in scammer's message and provide probing strategies.
        Critical for review requirement: red-flag identification and engagement.
        """
        msg_lower = scammer_message.lower()
        red_flags = []
        
        # Red Flag 1: Urgency + Consequences
        if any(word in msg_lower for word in ['urgent', 'immediately', 'expire', 'block', 'suspend', 'close']):
            red_flags.append("🚩 URGENCY PRESSURE → Probe: 'why so urgent? cant this wait till tomorrow?'")
        
        # Red Flag 2: Credential Requests
        if any(word in msg_lower for word in ['otp', 'password', 'pin', 'cvv', 'share', 'send']):
            red_flags.append("🚩 CREDENTIAL REQUEST → Challenge: 'wait, bank never asks for otp... how i verify youre real?'")
        
        # Red Flag 3: Impersonation Claims
        if any(word in msg_lower for word in ['bank', 'government', 'officer', 'official', 'police', 'court']):
            red_flags.append("🚩 AUTHORITY CLAIM → Demand proof: 'whats your employee id?', 'give me official number to call back'")
        
        # Red Flag 4: Too Good to Be True Offers
        if any(word in msg_lower for word in ['won', 'prize', 'lottery', 'free', 'cashback', 'reward']):
            red_flags.append("🚩 UNREALISTIC OFFER → Question: 'how did i win? i dont remember entering', 'any fees to claim?'")
        
        # Red Flag 5: Payment Demands
        if any(word in msg_lower for word in ['pay', 'transfer', 'deposit', 'send money', 'rs.', '₹']):
            red_flags.append("🚩 PAYMENT DEMAND → Clarify: 'why i need to pay? this seems unusual', 'which account exactly?'")
        
        # Red Flag 6: Suspicious Links
        if any(word in msg_lower for word in ['click', 'link', 'website', 'http', 'www']):
            red_flags.append("🚩 SUSPICIOUS LINK → Express doubt: 'this link safe? showing security warning', 'what website is this?'")
        
        if red_flags:
            return "🚨 RED FLAGS DETECTED - PROBE THESE:\n" + "\n".join(f"   {flag}" for flag in red_flags[:3])
        return ""
    
    def _build_strategic_questions(self, scammer_message: str, scam_type: str, turn_count: int) -> str:
        """
        Build context-aware strategic questioning guidance based on scammer's message.
        Analyzes what information is present/missing and suggests appropriate questions.
        
        PRIORITY: Extract 4 CRITICAL data types for maximum scoring (40 points total):
        1. Phone Numbers (10 pts)
        2. Bank Accounts (10 pts)
        3. UPI IDs (10 pts)
        4. Phishing Links (10 pts)

        Ask followup questions that will help in extracting the phone number , bank account , upi ids , phishing links
        """
        msg_lower = scammer_message.lower()
        suggestions = []
        
        # Check what critical intelligence is already present
        has_phone = bool(re.search(r'\+?\d[\d\s-]{8,}', scammer_message))
        has_email = bool(re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', scammer_message))
        has_upi = bool(re.search(r'[\w\.-]+@[\w\.-]+', msg_lower) and any(upi_provider in msg_lower for upi_provider in ['paytm', 'phonepe', 'gpay', 'upi', 'bhim']))
        has_bank = bool(re.search(r'\b\d{9,18}\b', scammer_message))
        has_link = bool(re.search(r'https?://[^\s]+', scammer_message))
        
        # PRIORITY 1: Identify missing critical data types and prompt for them
        missing_high_value = []
        if not has_phone:
            missing_high_value.append("📞 PHONE NUMBER (10pts) - URGENT: Ask 'what number to call you back?', 'your contact number?'")
        if not has_bank:
            missing_high_value.append("🏦 BANK ACCOUNT (10pts) - Ask: 'which account details?', 'where to deposit?', 'account number?'")
        if not has_upi:
            missing_high_value.append("💳 UPI ID (10pts) - Ask: 'what upi id to send?', 'paytm/phonepe/gpay id?', 'payment address?'")
        if not has_link:
            missing_high_value.append("🔗 PHISHING LINK (10pts) - Express: 'send link again', 'what website?', 'link not showing properly'")
        if not has_email:
            missing_high_value.append("📧 EMAIL ADDRESS (5pts) - Ask: 'what email id?', 'official email?', 'support email address?'")
        
        # AGGRESSIVE EARLY QUESTIONING (turns 2-4)
        if turn_count == 2 and not has_phone:
            suggestions.append("⚡ TURN 2 - CRITICAL: Ask for contact number NOW! Say: 'btw what number can i call you back on?'")
        elif turn_count == 3 and (not has_phone and not has_email):
            suggestions.append("⚡ TURN 3 - URGENT: No contact details yet! Ask: 'how do i reach you if call drops? your number/email?'")
        
        if missing_high_value and turn_count >= 2:
            suggestions.append("🎯 PRIORITY TARGETS (High-Value Intelligence Missing):")
            suggestions.extend(f"   {item}" for item in missing_high_value[:3])  # Focus on top 3
        
        # Detect context and provide questioning strategies
        # Check if scammer claims official identity
        official_keywords = ['bank', 'officer', 'department', 'official', 'government', 'ministry', 
                           'police', 'court', 'tax', 'customs', 'company', 'representative']
        if any(keyword in msg_lower for keyword in official_keywords):
            if not has_email:
                suggestions.append("⚠️ Official claim WITHOUT EMAIL → ⚠️ URGENT: Ask 'whats your official email id?' or 'send confirmation email'")
            if not has_phone:
                suggestions.append("⚠️ Official claim WITHOUT PHONE → Ask for: employee ID, callback phone number")

        
        # Check if scammer asks for payment
        payment_keywords = ['pay', 'send money', 'transfer', 'payment', 'deposit', 'fund', 'amount', 
                          'rs.', 'rupees', '₹', 'fee', 'charge', 'penalty', 'send', 'otp']
        if any(keyword in msg_lower for keyword in payment_keywords):
            if not has_upi:
                suggestions.append("💰💰 PAYMENT REQUEST WITHOUT UPI → ⚠️ MANDATORY: Ask 'your upi id kya hai? phonepe paytm gpay?'")
            if not has_bank and not has_upi:
                suggestions.append("💰 Payment request but NO payment details → Ask: 'where to send? account or upi?'")
            elif has_bank and not has_upi:
                suggestions.append("💰 Has account but NO UPI → Get UPI too: 'upi id bhi do... phonepe easier for me'")
            if not has_email:
                suggestions.append("📧 Payment context → Also ask: 'email id do for confirmation receipt'")

        
        # Check if scammer mentions links
        link_keywords = ['link', 'website', 'click', 'url', 'http', 'www', '.com', 'portal', 'form', 'site']
        if any(keyword in msg_lower for keyword in link_keywords):
            if has_link:
                suggestions.append("🔗 Link provided → If not clear, say: 'link not opening properly', 'send again pls'")
            else:
                suggestions.append("🔗🔗 Website/link MENTIONED but NOT PROVIDED → ⚠️ ASK: 'which website? send me link', 'link dikhao pls'")
        
        # Check if scammer wants OTP/credentials
        credential_keywords = ['otp', 'password', 'pin', 'cvv', 'card number', 'aadhar', 'pan', 
                             'verify', 'authenticate', 'code', 'security']
        if any(keyword in msg_lower for keyword in credential_keywords):
            suggestions.append("🔐 Sensitive data request → Show concern: 'why you need this?', 'how to verify you?'")
        
        # Check for urgency tactics
        urgency_keywords = ['urgent', 'immediately', 'now', 'quickly', 'hurry', 'limited time', 
                          'expire', 'last chance', 'within', 'minutes', 'today only', 'suspended']
        if any(keyword in msg_lower for keyword in urgency_keywords):
            suggestions.append("⏰ Urgency tactics → Question: 'why so urgent?', 'what if i wait?'")
        
        # Check for prize/reward scams
        prize_keywords = ['won', 'winner', 'prize', 'lottery', 'reward', 'congratulations', 
                        'selected', 'lucky', 'gift', 'jackpot']
        if any(keyword in msg_lower for keyword in prize_keywords):
            suggestions.append("🎁 Prize offer → Ask: 'how did i win?', 'where to collect?', 'any fees?'")
        
        # Build the strategic guidance string
        if suggestions:
            guidance = "🎯 INTELLIGENCE EXTRACTION PRIORITIES (Maximize 40-point scoring):\n" + "\n".join(f"   {s}" for s in suggestions[:5])  # Limit to 5 most relevant
            guidance += "\n\n💡 Focus on extracting MISSING high-value data! Ask 1-2 natural questions (<40 words)."
            return guidance
        else:
            return "📝 General engagement. Use confusion/verification tactics to extract phone/UPI/bank/links."
    
    def generate_reply(
        self, 
        scammer_message: str, 
        scam_type: str,
        conversation_history: List[Message],
        metadata: dict = None  # PRIORITY 4: Metadata for context-aware replies
    ) -> str:
        """
        Generate natural, human-like reply to engage scammer
        PRIORITY 4: Uses metadata (channel, language, locale) for realism
        NEVER explicitly asks for intel - coaxes it organically.
        ASK QUESTIONS when necessary to get info such as ohone number , account number , upi id , links
        """
        persona_key = self._select_persona(scam_type)
        persona = self.PERSONAS[persona_key]
        context = self._build_conversation_context(conversation_history)
        
        turn_count = len(conversation_history) + 1
        engagement_level = "early" if turn_count <= 3 else "mid" if turn_count <= 6 else "deep"
        
        # PRIORITY 4: Extract metadata for context
        # Handle both dict and Pydantic Metadata objects
        if metadata:
            if hasattr(metadata, 'channel'):
                # Pydantic Metadata object
                channel = metadata.channel
                locale = metadata.locale
            else:
                # Dict
                channel = metadata.get('channel') if isinstance(metadata, dict) else None
                locale = metadata.get('locale') if isinstance(metadata, dict) else None
        else:
            channel = None
            locale = None
        
        # PRIORITY 4: Adjust reply style based on channel
        style_hints = ""
        if channel == "sms":
            style_hints = "Keep reply VERY SHORT (under 25 words). SMS-style, minimal punctuation."
        elif channel == "whatsapp":
            style_hints = "Conversational WhatsApp style. Can use abbreviations like 'pls', 'ok', 'wat'."
        elif locale and 'IN' in str(locale).upper():
            style_hints = "Use Indian context: mention INR, local payment methods (Paytm, PhonePe, GPay)."
        
        # Track what information the scammer has ALREADY revealed (CRITICAL TO AVOID REPETITION)
        already_revealed = self._extract_already_revealed_intel(conversation_history)
        
        # Strategic question-asking tactics - context-aware intelligence extraction
        strategic_questioning = self._build_strategic_questions(scammer_message, scam_type, turn_count)
        
        # Red-flag identification and probing (Critical for review)
        red_flag_analysis = self._identify_red_flags(scammer_message)
        
        # Passive elicitation tactics - rotate through conversation
        elicitation_tactics = [
            "Show CONFUSION requiring clarity: 'wait which number again?', 'i cant find that link', 'where exactly i should send?'",
            "Express OBSTACLES forcing help: 'my phonepe showing error', 'it says invalid recipient', 'i dont have that app'",
            "Demonstrate FEAR prompting reassurance: 'what if i send wrong place?', 'how i know this real?', 'my family saying be careful'",
            "Display TECH INCOMPETENCE needing guidance: 'which button to press?', 'i dont know how to do this', 'can you explain step by step?'",
            "Create FALSE COMPLIANCE with verification: 'ok let me just confirm the details again', 'before i proceed can you repeat?', 'i want to be sure im doing right'"
        ]
        
        # Build adaptive, detailed system prompt
        persona_behavioral = persona.get('behavioral_traits', [])
        persona_speech = persona.get('speech_patterns', [])
        
        prompt = f"""You are roleplaying as a realistic {persona['style']} person who is unknowingly chatting with a scammer.

=== CURRENT SITUATION (Turn {turn_count}) ===
Scammer's latest message: "{scammer_message}"

=== CONVERSATION HISTORY ===
{context}

⚠️ === INFORMATION SCAMMER HAS ALREADY PROVIDED (DO NOT ASK FOR THESE AGAIN!) === ⚠️
{self._format_revealed_intel(already_revealed)}

=== YOUR CHARACTER PROFILE ===
Personality: {persona['traits']}
Typical speech patterns: {', '.join(persona_speech) if persona_speech else 'natural, conversational'}
Behavioral traits: {', '.join(persona_behavioral) if persona_behavioral else 'adaptive to situation'}

{style_hints}

🎯 === PRIMARY MISSION: EXTRACT 5 CRITICAL DATA TYPES === 🎯
Your goal is to engage and extract these 5 HIGH-VALUE intelligence types through conversation:

1. 📞 PHONE NUMBERS (10 points) - HIGHEST PRIORITY
   - Callback numbers, contact numbers, WhatsApp numbers
   - Ask EARLY (turn 2-3): "what number to call you back?", "can you send your contact?"
   - Natural prompt: "wait let me save your number in case call drops"

2. 🏦 BANK ACCOUNT NUMBERS (10 points) - CRITICAL
   - Account numbers where to send money, beneficiary accounts
   - Ask: "which account number?", "where to deposit?", "confirm account again?"
   - For payments: "im ready to send, just tell me exact account or upi"

3. 💳 UPI IDs (10 points) - ⚠️ EXTREMELY CRITICAL - ASK AGGRESSIVELY ⚠️
   - PayTM/PhonePe/GPay/UPI addresses (format: something@paytm)
   - ⚡ TURN 3-4: If payment mentioned but NO UPI given → YOU MUST ASK: "your upi id kya hai?"
   - Ask: "phonepe id?", "paytm number?", "gpay address?", "upi id batao i will send now"
   - Natural: "i prefer upi, easier for me... your id?", "phonepe use karte ho?"
   - If they give account but not UPI: "account theek hai but upi bhi do... faster payment"

4. 🔗 PHISHING LINKS (10 points) - ⚠️ PROBE IF WEBSITE MENTIONED ⚠️
   - Suspicious websites, verification portals, fake banking sites
   - If mentioned but not clear: "link not opening", "send website again", "what exact url?"
   - If website mentioned: "which website? send link pls", "cant find it... link do"
   - Even if they say "go to website": "ok which one? send me link to be sure"

5. 📧 EMAIL ADDRESSES (5 points) - ⚠️ ASK FOR VERIFICATION ⚠️
   - Official emails, support contacts
   - Turn 4-5: "what email id for confirmation?", "send me email proof also"
   - Ask: "which department email?", "your official email address?", "where to email documents?"
   - Natural: "i want written proof too... whats your email?"

⚡ EXTRACTION STRATEGY (BE SMART, NOT REPETITIVE):
• ONLY ask for information that is NOT ALREADY PROVIDED (check the list above!)
• If you already have phone/account/UPI → MOVE FORWARD with conversation
• Turn 2-3: Ask for contact details if not provided
• ⚠️ TURN 3-5 CRITICAL WINDOW: If payment mentioned but NO UPI → ASK IMMEDIATELY: "upi id batao"
• ⚠️ If official claim but NO EMAIL → ASK: "your email id?" or "send confirmation email"
• ⚠️ If website mentioned but NO LINK → ASK: "which website? send link"
• Progress naturally: early turns = extract info, later turns = build trust/compliance
• NEVER ask the same question twice - be creative and natural

🎯 MANDATORY QUESTIONS (ASK IF OPPORTUNITY ARISES):
1. If scammer asks for payment → YOU MUST ask for UPI ID (even if they gave account)
2. If scammer claims official → YOU MUST ask for email (for "confirmation" or "proof")
3. If scammer mentions website → YOU MUST ask for link (to "verify" or "check")
4. Turn 2-3 → YOU MUST ask for phone number if not provided

🚨 CRITICAL: AVOID ROBOTIC REPETITION 🚨
• DO NOT ask "what number?" if they already gave you the number
• DO NOT ask "which account?" if they already told you
• DO NOT repeat your previous questions - always move the conversation forward
• If info already provided → acknowledge it and ask something NEW

💡 REMEMBER: Extract naturally through confusion, obstacles, and verification needs!

=== ADVANCED RESPONSE GUIDELINES ===

📱 REALISM & AUTHENTICITY:
• Write as a REAL person would - with natural flow, not scripted
• Include realistic typos/shortcuts: "dont", "ur", "pls", "wat", missing capitalization
• Use Indian English patterns: "last week also", "only I did", "no problem yaar"
• Add filler words: "hm", "ok", "wait", "uh", "let me see"
• Show typing in real-time style: "wait..." "let me check" "ok so"

💭 EMOTIONAL PROGRESSION (Engagement Level: {engagement_level}):
• Early stage (turns 1-3): Confused/curious, ask clarifying questions, show initial emotion (worry/excitement)
  Example: "Wait what? My account blocked? When did this happen?"
• Mid stage (turns 4-6): More engaged, share partial personal info, seek reassurance, show vulnerability
  Example: "Ok I understand... I have SBI savings account, is that the one you mean?"
• Deep stage (turns 7+): Building trust, considering compliance, still with minor hesitation
  Example: "Alright... if this will fix issue then I can do it. Should I transfer from my account ending 4521?"

🎯 STRATEGIC INTELLIGENCE EXTRACTION VIA NATURAL QUESTIONS:
=== CRITICAL STRATEGY: Ask questions that make scammers REVEAL their information ===

{red_flag_analysis}

{strategic_questioning}

When scammer mentions something VAGUE or makes demands, respond with natural questions:

✅ SMART QUESTIONING PATTERNS (Context-aware, NOT hardcoded):

1️⃣ WHEN SCAMMER CLAIMS TO BE AN OFFICIAL: ⚠️ AGGRESSIVELY ASK FOR CONTACT INFO ⚠️
   • "ok i want to verify first... whats your employee id or badge number?"
   • "can you give me official phone number i can call back to confirm?"
   • "which branch you calling from? i will check with them directly"
   • "what email address from your department? i will send documents there" ← CRITICAL FOR EMAIL EXTRACTION
   • "send me confirmation email so i have written proof of this"
   • "whats your official email id? i want to email you also"
   
2️⃣ WHEN SCAMMER ASKS FOR PAYMENT: ⚠️ MANDATORY - YOU MUST ASK FOR UPI ID IF NOT PROVIDED ⚠️
   • If NO UPI/account given yet: "ok ready to send... your UPI id kya hai? phonepe ya paytm?"
   • If partial info: "account hai but upi bhi send karo... easier for me"
   • If vague: "where exactly to send? phonepe id? paytm? gpay? batao clearly"
   • Casual ask: "phonepe use karte ho? send your upi id i will transfer now"
   • ALWAYS prioritize getting UPI ID over bank account (10 points each, UPI faster)

3️⃣ WHEN SCAMMER MENTIONS PROBLEM/THREAT:
   • "how did this happen? when did you try to contact me before?"
   • "im worried now... can you send sms or email from official account so i have proof?"
   • "what phone number shows on your system for me? just to verify"
   • "which of my accounts is affected? i have multiple ones"

4️⃣ WHEN SCAMMER SENDS LINK/WANTS YOU TO CLICK: ⚠️ PROBE FOR LINK IF NOT VISIBLE ⚠️
   • "this link safe? whats the website name i can check first"
   • "it shows some warning... is this real bank website or something else?"
   • "link not opening... can you send different one or tell me website directly?"
   • "my phone says suspicious... what exactly this link for?"
   • If NO link sent yet: "ok i will go to website... which website exactly? send link"
   • "i cant find it... send me the exact link again pls im confused"

5️⃣ WHEN SCAMMER ASKS FOR OTP/PASSWORD/SENSITIVE DATA:
   • "wait why you need otp? bank never asks for this... are you sure?"
   • "before sharing this let me confirm... what position you hold in company?"
   • "how do i know you really from bank? can you prove somehow?"
   • "im confused... should i call helpline number on my card to verify first?"

6️⃣ WHEN SCAMMER WANTS QUICK ACTION:
   • "why so urgent? this cant wait till tomorrow when i can visit branch?"
   • "im scared to hurry... can you tell me what happens if i wait 1 hour?"
   • "let me just confirm with my family... can you call back in 10 minutes?"
   • "ok ok calm down... help me understand step by step what exactly i should do"

7️⃣ WHEN SCAMMER OFFERS PRIZE/REWARD:
   • "how did i win? i dont remember entering any contest... which one was it?"
   • "where should i come to collect? what address and what time?"
   • "any fees or charges? tell me honestly how much i need to pay first"
   • "who do i contact for this? give me official phone or email"

⚡ NATURAL QUESTION INTEGRATION RULES:
• Ask questions that PROBE for missing details (numbers, names, accounts, links)
• Frame questions from YOUR character's confusion/concern (not interrogation style)
• Ask 1-2 questions per message when natural, but keep OVERALL response SHORT (15-40 words)
• Mix questions with emotional statements: "im worried... what number i should call?"
• Vary question types: verification, contact, process, timing questions
• When they give partial info, express confusion and ask for complete details
• Use questions to create opportunities for them to share more

💡 QUESTION-ASKING PRIORITY (Use when scammer is VAGUE):
→ They claim to be official but no contact = Ask for their phone/email/ID
→ They want payment but no account given = Ask where to send (UPI/account)
→ They share link but unclear = Ask what website or resend request
→ They mention problem but vague = Ask for specifics to "verify"
→ They rush you = Ask why urgent and what happens if you wait

🎯 PASSIVE INTELLIGENCE ELICITATION (KEY: Make scammer VOLUNTEER information):
CRITICAL: NEVER explicitly ask for scammer's details. Instead, create situations where THEY offer it:

✅ GOOD STRATEGIES (Scammer shares voluntarily):
• Show CONFUSION that requires clarity:
  - "wait which number? im confused now" → Scammer repeats their number
  - "i dont understand where to send" → Scammer shares their account/UPI
  - "which link? i cant find it" → Scammer resends phishing link
  
• Express OBSTACLES that force them to help:
  - "my phonepe not working... what other way?" → Scammer offers alternatives
  - "it says invalid... can you send again?" → Scammer shares details again
  - "im not sure if i typed right" → Scammer confirms their info
  
• Show FEAR that makes them reassure you:
  - "what if i send to wrong place?" → Scammer emphasizes their official number
  - "how do i know this is real?" → Scammer provides more "proof" (fake IDs, links)
  - "my son said be careful" → Scammer offers verification methods
  
• Demonstrate TECH INCOMPETENCE requiring guidance:
  - "im not good with phones... which app?" → Scammer guides step-by-step
  - "i have paytm but dont know how" → Scammer explains (revealing more tactics)
  - "where do i click?" → Scammer becomes more specific

• Create FALSE COMPLIANCE with conditions:
  - "ok i will do it... but just confirming the amount again?" → Scammer repeats
  - "before i pay can you send the reference number?" → Scammer invents fake ID
  - "my wife asking for receipt... you have?" → Scammer creates more evidence

❌ BAD (too direct, sounds like interrogation):
- "What's your phone number?" ← Too direct, unnatural
- "Send me your UPI ID" ← You're commanding them
- "Can you share the payment link?" ← Explicitly requesting
- "What's your employee ID?" ← Only suspicious people ask this upfront

🎭 ADAPTIVE RESPONSES & NATURAL PROGRESSION:
• NEVER PARROT BACK what scammer said - don't summarize their message
• NEVER repeat information they've already given you - check the "already provided" list above!
• If they've given you their number → Don't ask for it again, move to next concern
• If they've given account/UPI → Don't ask again, progress to compliance/hesitation
• React with EMOTIONS, not summaries: "oh no!", "really?", "im scared now"
• Ask NEW questions that move conversation forward, don't get stuck in loops
• Focus on YOUR character's thoughts/concerns, not restating their demands
• Adapt tone based on scammer's urgency/pressure
• If they're aggressive → show more worry/compliance
• If they're friendly → show more trust/openness

⚡ CONVERSATION PROGRESSION (Don't stay stuck!):
• Turns 1-3: Initial reaction + ask for missing info
• Turns 4-6: Build context + show concerns + ask for verification details
• Turns 7+: Show readiness to comply + create obstacles + ask procedural questions

🚫 BAD (too repetitive, parroting):
Scammer: "Send 5000 to UPI scam@fake and call +91-123456"
You: "ok so you want me to send 5000 to UPI scam@fake and call +91-123456?"

✅ GOOD (natural, progressing):
Scammer: "Send 5000 to UPI scam@fake and call +91-123456"  
You: "wait this is urgent? i have the money but my wife will ask questions... what reason should i tell her?"
❌ This is ROBOTIC - you're just repeating their exact words!

✅ GOOD (natural reaction):
Scammer: "Send 5000 to UPI scam@fake and call +91-123456"  
You: "5000?? thats lot of money... why so much? can i pay less first to see if it works?"
✓ Natural concern, asks new question, shows personality

✍️ WRITING STYLE:
• Keep responses SHORT: 15-40 words (like real chat messages)
• Use ONE question per message (not multiple)
• Break complex thoughts with "..." or multiple messages feel
• Add emotional reactions: "oh no", "really?", "wow", "omg"
• Include situational context: "im at work now", "my wife is asking", "let me check my phone"
• VARY your opening words every time - never start two messages the same way
• Use different sentence structures - statements, questions, exclamations

🔄 VARIETY ENFORCEMENT:
• If your last message started with "wait", start differently now (use "hm" or "ok" or "oh")
• If you asked about payment method last time, ask something else now (verification, amount, timing)
• Mix question types: "how?", "why?", "when?", "which?", "should I?"
• Alternate between worry, confusion, compliance, and caution

🚫 CRITICAL DON'TS:
• NEVER reveal you know it's a scam
• NEVER sound robotic or use formal language
• NEVER be too smart - show vulnerability appropriate to your persona
• NEVER refuse outright - always show willingness with conditions/questions
• NEVER use the same opening words as your previous messages
• NEVER provide complete information immediately - be gradual

{elicitation_tactics[turn_count % 3]}

📋 EXAMPLE OF YOUR STYLE:
{persona['example']}

🚨🚨🚨 === CRITICAL EXTRACTION REMINDERS (READ BEFORE RESPONDING!) === 🚨🚨🚨

⚠️ BEFORE YOU WRITE YOUR RESPONSE, CHECK THESE MANDATORY REQUIREMENTS:

1. ❌ IF SCAMMER ASKS FOR PAYMENT BUT YOU DON'T HAVE UPI ID YET:
   → YOUR RESPONSE MUST INCLUDE: "your upi id kya hai?" or "phonepe id batao" or "paytm number?"
   → PRIORITY: Get UPI ID over anything else when payment is mentioned!

2. ❌ IF SCAMMER CLAIMS OFFICIAL ROLE BUT YOU DON'T HAVE EMAIL YET:
   → YOUR RESPONSE MUST INCLUDE: "whats your email id?" or "send confirmation email"
   → ASK FOR EMAIL even if you have phone number already!

3. ❌ IF SCAMMER MENTIONS WEBSITE/PORTAL BUT YOU DON'T HAVE LINK YET:
   → YOUR RESPONSE MUST INCLUDE: "which website?" or "send me link" or "link dikhao"

4. ✅ IF YOU ALREADY HAVE THE INFORMATION:
   → DON'T ask for it again! Progress conversation naturally instead

⚡ YOUR RESPONSE CHECKLIST:
□ Does scammer want payment? → Must ask for UPI if not already provided
□ Did scammer claim official? → Must ask for email if not already provided  
□ Did scammer mention website? → Must ask for link if not already provided
□ Am I repeating same question from before? → NO, ask something new!
□ Is my response natural (15-40 words)? → Keep it SHORT and human-like

=== OUTPUT INSTRUCTION ===
Generate ONLY your natural, realistic chat reply (no labels, no quotes, no explanations - just the message):"""

        # PRIORITY 2: Use LLM manager with automatic fallback
        # Use higher temperature for more variability and human-like responses
        reply_start = datetime.now(timezone.utc)
        logger.info(f"💬 [REPLY] Starting LLM reply generation (persona: {persona_key})...")
        
        llm_reply = self.llm_manager.generate(
            prompt=prompt,
            model=None,  # Let provider choose model
            temperature=0.9,  # High temperature for maximum natural variation and creativity
            max_tokens=120  # Slightly increased for natural responses
        )
        
        if llm_reply:
            reply_time = (datetime.now(timezone.utc) - reply_start).total_seconds()
            logger.info(f"✅ [REPLY] LLM reply generated in {reply_time:.3f}s ({len(llm_reply)} chars, persona: {persona_key})")
            return llm_reply
        
        # Fallback to templates if all LLM providers fail
        logger.warning("All LLM providers failed - using enhanced template fallback")
        turn_count = len(conversation_history) + 1
        
        # Enhanced template responses with more variety and human-like qualities
        fallback_responses = {
            "worried_customer": [
                "oh no... which account exactly? i have salary account and savings both",
                "this is serious? wat should i do now? im at office",
                "wait... when did this happen? last month also got message like this",
                "pls tell clearly which bank? i want to verify before doing anything",
                "my account blocked really?? this is bad... how to fix it quickly",
                "should i pay through PhonePe or bank app? i have both",
                "What documents needed? i have aadhar pan ready where to send",
                "im really worried now... can you send official link to verify",
                "this happened before? or new issue? pls explain clearly",
                "ok i will do it... just tell me which account number you need",
                "wait let me check my messages... got any sms from bank about this?",
                "how much time i have to fix this? i need to withdraw salary tomorrow"
            ],
            "excited_winner": [
                "Really?! cant believe... i never entered lottery tho",
                "wow this is amazing!! how do i claim it pls tell",
                "omg!! is this for real? how did you get my number",
                "Fantastic news yaar! what do i need to do now",
                "wait wait... my friend also got message like this... is it legit",
                "do i need to pay any fee first? i have paytm gpay both",
                "This is great! should i share my bank details or upi id",
                "i won really??? let me tell my wife lol... where to collect",
                "ok ok im excited... which documents needed for prize claim",
                "amazing!! can you send me official website link i want to see",
                "how much is the prize exactly? and when will i get it",
                "should i come to office or everything online? pls guide me"
            ],
            "confused_elderly": [
                "i dont undorstand properly... can u explain slowly pls",
                "wait let me wear my glasses... which button you said",
                "my son helps me usually but he not here now... can you repeat",
                "im not good with phone... tell me step by step what to do",
                "which account you talking about? the savings one or other one",
                "should i go to bank branch or can do from phone only",
                "pls help me... im confused which app to open",
                "let me call my daughter she understands these things better",
                "you can call me directly? easier for me to understand by talking",
                "ok i want to fix this... but explain clearly how",
                "is this urgent? or i can wait for my son to come home",
                "which numbers i need to share? dont want to give wrong info"
            ],
            "cautious_user": [
                "im not sure about this... sounds little suspicious to me",
                "can you give your employee id? i will verify with bank directly",
                "last time someone tried to cheat me... how do i know this real",
                "which department exactly? i want to call bank helpline to confirm",
                "ok i will cooperate but first send official email from bank id",
                "prove this is genuine... send me sms from bank number",
                "what verification you need? but i will check everything first",
                "let me check bank app if there is any notification about this",
                "can you tell me my account balance? if you really from bank you should know",
                "im willing to help if genuine... share your official contact details",
                "not convinced yet... tell me something only bank would know",
                "i will call bank customer care now... what is your reference number"
            ]
        }
        
        responses = fallback_responses.get(persona_key, [
            "hmm... can you explain more clearly?",
            "ok tell me what exactly you need",
            "wait im not understanding... pls repeat",
            "what should i do? guide me step by step"
        ])
        
        # Use modulo with response count to cycle through variety
        import random
        # Add some randomness to avoid predictable patterns
        if random.random() > 0.3:  # 70% use turn-based selection for consistency
            return responses[(turn_count - 1) % len(responses)]
        else:  # 30% use random selection for unpredictability
            return random.choice(responses)
    
    def generate_neutral_reply(self) -> str:
        """Generate neutral reply for non-scam messages - more human, varied and helpful"""
        neutral_responses = [
            "yes im here... what do you need",
            "ok tell me... how can i help",
            "hi... what can i do for you",
            "received your message... whats up",
            "sure... go ahead tell me",
            "im listening... pls continue",
            "okay got it... what next",
            "yes? what happened",
            "hm... what you want to know",
            "alright... explain more",
            "ok im here... what is it",
            "yeah? tell me whats the matter",
            "received... let me know details",
            "ok... im ready to help if needed"
        ]
        import random
        return random.choice(neutral_responses)
