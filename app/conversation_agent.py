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
    
    # Enhanced personas with human-like engagement patterns
    PERSONAS = {
        "worried_customer": {
            "style": "concerned, anxious, wants to fix problem, asks follow-up questions",
            "traits": "shows hesitation, mentions personal context, gradually reveals info",
            "example": "Oh no... last week also I got similar message. Which account exactly? I have two accounts, salary and savings."
        },
        "excited_winner": {
            "style": "excited but cautious, eager but confused about process",
            "traits": "expresses disbelief, asks verification questions, delays action",
            "example": "Really?! I never entered any lottery... but if its true, amazing! How do I verify this is real? Do I need to pay anything first?"
        },
        "confused_elderly": {
            "style": "confused, needs step-by-step help, makes small errors, trusting",
            "traits": "asks to repeat info, mentions difficulty with technology, seeks reassurance",
            "example": "I dont undorstand properly... can you explain slowly? My son usually helps me with phone but he is not here now. Which button I should press?"
        },
        "cautious_user": {
            "style": "somewhat skeptical but willing to cooperate if convinced",
            "traits": "asks for proof, mentions past scam experiences, tests authenticity",
            "example": "I am not sure... last time someone tried to cheat me. Can you tell me your employee ID? Or should I call the bank directly to verify?"
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
        """Build conversation context from history"""
        if not history:
            return "This is the first message in the conversation."
        
        context_lines = []
        for msg in history[-5:]:  # Last 5 messages for context
            sender_label = "Scammer" if msg.sender == "scammer" else "You"
            context_lines.append(f"{sender_label}: {msg.text}")
        
        return "\n".join(context_lines)
    
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
        
        prompt = f"""You are a {persona['style']} person chatting with a scammer (turn {turn_count}).

Scammer said: {scammer_message}

Conversation so far:
{context}

Your personality traits: {persona['traits']}

{style_hints}

ENGAGEMENT RULES (engagement level: {engagement_level}):
1. ALWAYS ask a follow-up question or express confusion/concern
2. Show hesitation before complying: "wait...", "but...", "I'm not sure..."
3. Reveal vulnerability GRADUALLY:
   - Early turns (1-3): Ask clarifying questions, express worry/excitement
   - Mid turns (4-6): Share partial context ("I have two accounts..."), seek reassurance
   - Deep turns (7+): Show more trust, consider complying but still hesitant
4. BE PROACTIVE - steer conversation to extract their info:
   - "Which account you mean? Savings or current?"
   - "Should I pay through my Paytm UPI or PhonePe?"
   - "Can you send me the official link again?"
   - "What's your employee ID for verification?"
5. Keep it SHORT (20-35 words max)
6. Use simple language, occasional typos ("dont" instead of "don't", missing punctuation)
7. Add personal context: "my son helps me usually", "last week also got message", "I'm at office now"

{elicitation_tactics[turn_count % 3]}

Style example: {persona['example']}

Generate ONLY your natural reply (no labels):"""

        # PRIORITY 2: Use LLM manager with automatic fallback
        llm_reply = self.llm_manager.generate(
            prompt=prompt,
            model=None,  # Let provider choose model
            temperature=0.7,
            max_tokens=100
        )
        
        if llm_reply:
            logger.info(f"🤖 Agent reply ({persona_key}): {llm_reply}")
            return llm_reply
        
        # Fallback to templates if all LLM providers fail
        logger.warning("All LLM providers failed - using template fallback")
        turn_count = len(conversation_history) + 1
        fallback_responses = {
            "worried_customer": [
                # Variant 1: Confused tone
                "Oh no... I'm really worried. Which account is blocked? I have salary and savings both.",
                # Variant 2: Compliant tone
                "This is serious? I will do whatever needed. Should I pay through my PhonePe UPI?",
                # Variant 3: Cautious tone
                "Please tell me clearly... which bank you are calling from? I want to verify first.",
                # Variant 4: Proactive tone
                "What documents you need? I have my Aadhaar and PAN ready. Where should I send?",
                # Variant 5: Hesitant tone
                "Wait... last month also got such message. Is this same issue or new problem?"
            ],
            "excited_winner": [
                # Variant 1: Excited/confused
                "Really?! I never entered any lottery but if its true, amazing! How do I claim?",
                # Variant 2: Eager/compliant
                "Wow! Tell me what to do quickly. Should I pay processing fee from my bank account?",
                # Variant 3: Excited/cautious
                "This is great news! But how did you get my number? Should I verify this somewhere?",
                # Variant 4: Proactive
                "Fantastic! Do I need to share my UPI ID? I use Paytm usually, is that okay?",
                # Variant 5: Hesitant excitement
                "I cant believe this... my friend also got such message. Where should I collect prize?"
            ],
            "confused_elderly": [
                # Variant 1: Very confused
                "I dont undorstand properly... can you explain slowly? Which button should I press?",
                # Variant 2: Compliant/helpless
                "Please help me... I'm not good with phone. Tell me step by step what to do.",
                # Variant 3: Seeking help
                "My son usually helps but he is not here. Can you call me and explain?",
                # Variant 4: Trying to understand
                "Wait, let me get my reading glasses... which account you said? The savings one?",
                # Variant 5: Willing but confused
                "I want to fix this. Should I go to bank branch or can do from phone only?"
            ],
            "cautious_user": [
                # Variant 1: Skeptical
                "I'm not sure about this... can you give me your employee ID to verify?",
                # Variant 2: Testing authenticity
                "Last time someone tried to cheat me. How do I know this is real? Give me proof.",
                # Variant 3: Seeking verification
                "Which department you are calling from exactly? I will call bank directly to confirm.",
                # Variant 4: Conditional compliance
                "Okay, I will help but first send me official email or SMS from bank number.",
                # Variant 5: Cautious but willing
                "Let me check... if this is genuine, I will provide details. What verification you need?"
            ]
        }
        responses = fallback_responses.get(persona_key, ["I see... can you explain more clearly?"])
        return responses[(turn_count - 1) % len(responses)]
    
    def generate_neutral_reply(self) -> str:
        """Generate neutral reply for non-scam messages - more human and helpful"""
        neutral_responses = [
            "Sure, I can help with that. What would you like to know?",
            "Yes, I'm here. What do you need?",
            "I understand. How can I assist you?",
            "Okay, got it. What's next?",
            "Thanks for reaching out. What can I do for you?",
            "Alright, I'm listening. Please go ahead.",
            "Received. Let me know what you need."
        ]
        import random
        return random.choice(neutral_responses)
