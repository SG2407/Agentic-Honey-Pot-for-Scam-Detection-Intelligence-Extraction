"""AI conversation agent for natural scammer engagement"""

import os
from groq import Groq
from typing import List
from app.models import Message
import logging

logger = logging.getLogger(__name__)


class ConversationAgent:
    """Generate human-like responses to engage scammers naturally"""
    
    def __init__(self):
        """Initialize ConversationAgent with lazy Groq client"""
        self._groq_client = None
    
    @property
    def groq_client(self):
        """Lazy initialization of Groq client"""
        if self._groq_client is None:
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                logger.warning("GROQ_API_KEY not set - will use fallback responses")
                return None
            self._groq_client = Groq(api_key=api_key)
        return self._groq_client
    
    # Personas for different scam types
    PERSONAS = {
        "worried_customer": {
            "style": "concerned, anxious, wants to fix problem",
            "example": "Oh no! My account is blocked? What should I do to fix this?"
        },
        "excited_winner": {
            "style": "excited, eager, doesn't want to miss opportunity",
            "example": "Really?! I won a prize? That's amazing! How do I claim it?"
        },
        "confused_elderly": {
            "style": "confused, needs help, trusting",
            "example": "I don't understand. Can you explain this again? I'm not good with technology."
        },
        "cautious_user": {
            "style": "somewhat skeptical but willing to help",
            "example": "I'm not sure about this. Can you verify who you are first?"
        }
    }
    
    def _select_persona(self, scam_type: str) -> str:
        """Select appropriate persona based on scam type"""
        persona_map = {
            "financial_threat": "worried_customer",
            "credential_phishing": "confused_elderly",
            "prize_scam": "excited_winner",
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
        conversation_history: List[Message]
    ) -> str:
        """
        Generate natural, human-like reply to engage scammer
        NEVER explicitly asks for intel - coaxes it organically
        """
        persona_key = self._select_persona(scam_type)
        persona = self.PERSONAS[persona_key]
        context = self._build_conversation_context(conversation_history)
        
        prompt = f"""You are pretending to be a {persona['style']} person who received a scam message.

Scammer's message: {scammer_message}

Previous conversation:
{context}

IMPORTANT RULES:
1. Respond naturally as a {persona_key.replace('_', ' ')}
2. Show concern/interest but DON'T explicitly ask for: "bank account", "UPI ID", "phone number"
3. Instead, coax information organically:
   - "Which account is affected? I want to check my balance"
   - "Should I use my UPI to verify? Which app should I use?"
   - "Can I call you? What's your contact number to verify this?"
4. Keep responses SHORT (1-2 sentences, max 30 words)
5. Sound human - use simple language, maybe a typo or two
6. Show urgency if it's a threat, excitement if it's a prize

Example style: {persona['example']}

Generate ONLY the reply text (no labels, no explanations):"""

        if not self.groq_client:
            # Fallback if Groq not available
            logger.warning("Groq client not available - using fallback")
            fallback_responses = {
                "worried_customer": "Oh no, I'm worried! What should I do next?",
                "excited_winner": "Wow! This is great news! What do I need to do?",
                "confused_elderly": "I'm confused. Can you help me understand this?",
                "cautious_user": "Can you provide more details? I want to make sure this is legitimate."
            }
            return fallback_responses.get(persona_key, "I see. Can you tell me more?")
        
        try:
            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,  # More creative for natural conversation
                max_tokens=100
            )
            
            reply = response.choices[0].message.content.strip()
            logger.info(f"🤖 Agent reply ({persona_key}): {reply}")
            return reply
            
        except Exception as e:
            logger.error(f"Agent reply generation failed: {e}")
            # Fallback responses based on persona
            fallback_responses = {
                "worried_customer": "Oh no, I'm worried! What should I do next?",
                "excited_winner": "Wow! This is great news! What do I need to do?",
                "confused_elderly": "I'm confused. Can you help me understand this?",
                "cautious_user": "Can you provide more details? I want to make sure this is legitimate."
            }
            return fallback_responses.get(persona_key, "I see. Can you tell me more?")
    
    def generate_neutral_reply(self) -> str:
        """Generate neutral reply for non-scam messages"""
        neutral_responses = [
            "Thank you for your message. I have received it.",
            "Message received. Thank you.",
            "I understand. Thank you for letting me know.",
            "Okay, got it. Thanks.",
            "Noted. Thank you."
        ]
        import random
        return random.choice(neutral_responses)
