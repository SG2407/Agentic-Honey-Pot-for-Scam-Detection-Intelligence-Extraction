"""AI conversation agent for natural scammer engagement"""

import os
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
        NEVER explicitly asks for intel - coaxes it organically
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
        
        # Add aggressive elicitation strategies
        elicitation_tactics = [
            "Sometimes ASK DIRECT QUESTIONS that reveal info: 'Should I pay from my bank app or UPI?', 'Which account should I send to?'",
            "Mention YOUR payment methods: 'I have PhonePe, should I use that?', 'My bank account is with SBI'",
            "Ask for THEIR contact details: 'Can you send the official link again?', 'What's your employee ID?'"
        ]
        
        # Build adaptive, detailed system prompt
        persona_behavioral = persona.get('behavioral_traits', [])
        persona_speech = persona.get('speech_patterns', [])
        
        prompt = f"""You are roleplaying as a realistic {persona['style']} person who is unknowingly chatting with a scammer.

=== CURRENT SITUATION (Turn {turn_count}) ===
Scammer's latest message: "{scammer_message}"

=== CONVERSATION HISTORY ===
{context}

=== YOUR CHARACTER PROFILE ===
Personality: {persona['traits']}
Typical speech patterns: {', '.join(persona_speech) if persona_speech else 'natural, conversational'}
Behavioral traits: {', '.join(persona_behavioral) if persona_behavioral else 'adaptive to situation'}

{style_hints}

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

🎯 INTELLIGENCE ELICITATION (Critical for scam detection):
• NATURALLY steer conversation to extract THEIR information:
  - "Which account should I send money to?"
  - "Can you share the payment link again?"
  - "What's your phone number, I'll call you directly"
  - "Send me your UPI ID, I'll pay immediately"
  - "What's the official website? I want to verify this"
• Mention YOUR payment methods to prompt them: "I use PhonePe mostly", "Should I pay via GooglePay?"
• Share partial banking context: "I have HDFC and SBI both", "My account number starts with 1234"

🎭 ADAPTIVE RESPONSES:
• NEVER repeat exact phrases from previous turns - vary your language
• Reference specific things the scammer said in your response
• Build on the conversation - show memory of what was discussed
• Adapt tone based on scammer's urgency/pressure
• If they're aggressive → show more worry/compliance
• If they're friendly → show more trust/openness

✍️ WRITING STYLE:
• Keep responses SHORT: 15-40 words (like real chat messages)
• Use ONE question per message (not multiple)
• Break complex thoughts with "..." or multiple messages feel
• Add emotional reactions: "oh no", "really?", "wow", "omg"
• Include situational context: "im at work now", "my wife is asking", "let me check my phone"

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

=== OUTPUT INSTRUCTION ===
Generate ONLY your natural, realistic chat reply (no labels, no quotes, no explanations - just the message):"""

        # PRIORITY 2: Use LLM manager with automatic fallback
        # Use higher temperature for more variability and human-like responses
        llm_reply = self.llm_manager.generate(
            prompt=prompt,
            model=None,  # Let provider choose model
            temperature=0.85,  # Increased for more natural variation
            max_tokens=120  # Slightly increased for natural responses
        )
        
        if llm_reply:
            logger.info(f"🤖 Agent reply ({persona_key}): {llm_reply}")
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
