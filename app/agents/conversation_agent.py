import asyncio
import random
from typing import List, Optional, Dict, Any
from app.models import Message, ConversationState, ExtractedIntelligence
from app.utils.logger import setup_logger, log_conversation_event
from config.settings import settings
from groq import Groq
from datetime import datetime

class ConversationAgent:
    """AI agent that engages with scammers to extract intelligence."""
    
    def __init__(self):
        self.logger = setup_logger(__name__)
        self.client = Groq(api_key=settings.GROQ_API_KEY) if settings.GROQ_API_KEY else None
        
        # Conversation strategies based on scam type
        self.strategies = {
            'credential_phishing': {
                'persona': 'confused_elderly',
                'responses': [
                    "I'm not sure what you mean by OTP. Can you explain?",
                    "Why do you need my PIN? I thought that was secret.",
                    "I don't understand these technical terms. Can you help me?",
                    "My grandson usually helps me with these things. Is this urgent?"
                ]
            },
            'financial_threat': {
                'persona': 'worried_customer',
                'responses': [
                    "Oh no! Why is my account being blocked? What did I do wrong?",
                    "I'm so worried. How can I fix this? Please help me.",
                    "I have all my salary in this account. What should I do?",
                    "Can you please explain what suspicious activity you found?"
                ]
            },
            'prize_scam': {
                'persona': 'excited_winner',
                'responses': [
                    "Really? I won a prize? That's amazing! What did I win?",
                    "I can't believe it! How do I claim my prize?",
                    "This is the best news ever! What do I need to do?",
                    "Are you sure it's me? I never entered any lottery."
                ]
            },
            'payment_fraud': {
                'persona': 'confused_user',
                'responses': [
                    "I don't remember making any payment. Can you check again?",
                    "Which transaction failed? I made several payments today.",
                    "How much money are we talking about?",
                    "Can you send me the transaction details?"
                ]
            },
            'default': {
                'persona': 'cautious_user',
                'responses': [
                    "I'm not sure I understand. Can you explain more?",
                    "Who is this? How did you get my number?",
                    "I want to verify this with my bank first.",
                    "Can you provide some identification?"
                ]
            }
        }
        
        # Probing questions to extract intelligence
        self.probing_questions = [
            "What's your employee ID or reference number?",
            "Which bank department are you calling from?",
            "Can you give me the customer service number to verify?",
            "What's the specific issue with my account?",
            "Can you send me the details via SMS?",
            "What information do you need to fix this?",
            "How long will this process take?",
            "Is there a fee for this service?"
        ]
    
    async def generate_response(self, conversation_state: ConversationState, scam_type: str = None) -> str:
        """Generate appropriate response based on conversation context."""
        
        if not conversation_state.messages:
            return "Hello, who is this?"
        
        last_message = conversation_state.messages[-1]
        
        # Use AI if available, otherwise use rule-based responses
        if self.client:
            response = await self._ai_generate_response(conversation_state, scam_type)
        else:
            response = self._rule_based_response(conversation_state, scam_type)
        
        # Log conversation event
        log_conversation_event(
            self.logger, 
            'agent_response_generated', 
            conversation_state.sessionId,
            {'response': response, 'scam_type': scam_type}
        )
        
        return response
    
    async def _ai_generate_response(self, conversation_state: ConversationState, scam_type: str = None) -> str:
        """Use AI to generate contextual responses."""
        try:
            # Build conversation context
            context = self._build_conversation_context(conversation_state)
            
            # Create persona-based system prompt
            system_prompt = self._get_system_prompt(scam_type)
            
            response = self.client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": context}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Ensure response is appropriate length and tone
            if len(ai_response) > 200:
                ai_response = ai_response[:200] + "..."
            
            return ai_response
            
        except Exception as e:
            self.logger.error(f"AI response generation failed: {str(e)}")
            return self._rule_based_response(conversation_state, scam_type)
    
    def _rule_based_response(self, conversation_state: ConversationState, scam_type: str = None) -> str:
        """Generate rule-based responses for reliability."""
        
        strategy = self.strategies.get(scam_type or 'default', self.strategies['default'])
        
        # Get last message for context
        last_message = conversation_state.messages[-1].text.lower()
        
        # Context-aware response selection
        if any(word in last_message for word in ['otp', 'pin', 'password', 'code']):
            responses = [
                "I don't have the OTP right now. Can you wait a moment?",
                "I'm not comfortable sharing that over the phone. Is there another way?",
                "Can you explain why you need this information?"
            ]
        elif any(word in last_message for word in ['urgent', 'immediate', 'now']):
            responses = [
                "Why is this so urgent? I'm a bit confused.",
                "Can this wait? I want to discuss with my family first.",
                "I'm not comfortable rushing into this."
            ]
        elif any(word in last_message for word in ['click', 'link', 'website']):
            responses = [
                "I don't use internet much. Can you help me another way?",
                "I'm not good with computers. What should I do?",
                "Can someone call me instead?"
            ]
        else:
            responses = strategy['responses']
        
        # Add probing questions occasionally
        if len(conversation_state.messages) > 2 and random.random() < 0.3:
            response = random.choice(responses) + " " + random.choice(self.probing_questions)
        else:
            response = random.choice(responses)
        
        return response
    
    def _get_system_prompt(self, scam_type: str = None) -> str:
        """Get system prompt for AI persona."""
        base_prompt = """
You are roleplaying as a potential scam victim. Your goal is to engage with the scammer to extract information while appearing vulnerable and believable.

Persona guidelines:
- Act confused, worried, or excited depending on the scam type
- Ask clarifying questions to get more details
- Show some hesitation but remain engaged
- Use simple, non-technical language
- Occasionally express concerns or ask for verification
- Keep responses short (1-2 sentences max)

DO NOT:
- Immediately agree to provide sensitive information
- Sound too knowledgeable about scams
- Be overly suspicious right away
- Use technical jargon
"""
        
        if scam_type == 'financial_threat':
            return base_prompt + "\nScenario: Someone claims your bank account has issues. Act worried and confused about what to do."
        elif scam_type == 'prize_scam':
            return base_prompt + "\nScenario: Someone says you won a prize. Act excited but ask for details about how to claim it."
        elif scam_type == 'payment_fraud':
            return base_prompt + "\nScenario: Someone mentions failed payments or refunds. Act confused about transactions."
        else:
            return base_prompt + "\nScenario: Respond appropriately to the conversation context. Show mild confusion and ask for clarification."
    
    def _build_conversation_context(self, conversation_state: ConversationState) -> str:
        """Build context string for AI."""
        context = "Conversation history:\n"
        
        # Include last 5 messages for context
        recent_messages = conversation_state.messages[-5:]
        for msg in recent_messages:
            context += f"{msg.sender}: {msg.text}\n"
        
        context += "\nGenerate an appropriate response as the user (victim)."
        return context
    
    def _get_system_prompt(self, scam_type: str = None) -> str:
        """Get system prompt based on scam type and persona."""
        
        strategy = self.strategies.get(scam_type or 'default', self.strategies['default'])
        persona = strategy['persona']
        
        base_prompt = """
You are roleplaying as a potential scam victim to extract information from scammers for cybersecurity research.

IMPORTANT GUIDELINES:
- Act as a believable victim who is initially confused but gradually becomes more trusting
- Ask clarifying questions that might reveal scammer information
- Show concern and willingness to help, but ask for verification
- Occasionally ask for their employee ID, department, or contact information
- Never provide real personal information
- Keep responses natural and conversational
- Show appropriate emotions (worry, confusion, excitement) based on the scam type
- Gradually become more trusting as conversation progresses
"""
        
        persona_prompts = {
            'confused_elderly': "You are an elderly person who is not very tech-savvy and needs things explained simply. You're worried about technology and often ask for help.",
            'worried_customer': "You are a concerned customer who is worried about their account. You want to resolve issues quickly but ask questions for verification.",
            'excited_winner': "You are excited about winning a prize but also surprised. You ask questions about the prize and how to claim it.",
            'confused_user': "You are confused about the situation and want more details. You ask clarifying questions and want to understand what's happening.",
            'cautious_user': "You are naturally cautious and want to verify information before proceeding. You ask for proof and identification."
        }
        
        return base_prompt + "\n\nPersona: " + persona_prompts.get(persona, persona_prompts['cautious_user'])
    
    async def generate_casual_response(self, message: str, conversation_state: ConversationState) -> str:
        """Generate a casual, friendly response for non-scam messages."""
        
        if self.client:
            try:
                system_prompt = """You are a friendly, helpful person responding to casual messages.
Keep responses natural, brief, and conversational. Show interest and ask follow-up questions.
Examples:
- Meeting: "Sure! What time works for you?"
- Location: "Sounds good. I'll see you there!"
- Plans: "That works for me. Let me know if anything changes."
"""
                
                response = self.client.chat.completions.create(
                    model=settings.GROQ_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message}
                    ],
                    max_tokens=100,
                    temperature=0.8
                )
                
                return response.choices[0].message.content.strip()
            except Exception as e:
                self.logger.error(f"Casual response generation failed: {str(e)}")
        
        # Fallback responses
        casual_responses = [
            "That sounds good! Tell me more.",
            "Sure, I'm available. What time works for you?",
            "Got it. Thanks for letting me know!",
            "Okay, sounds like a plan!",
            "Thanks for the update. See you then!"
        ]
        
        return random.choice(casual_responses)
    
    def should_continue_conversation(self, conversation_state: ConversationState) -> bool:
        """Determine if conversation should continue."""
        
        # Stop if max turns reached
        if len(conversation_state.messages) >= settings.MAX_CONVERSATION_TURNS:
            return False
        
        # Stop if no new intelligence is being extracted
        last_message = conversation_state.messages[-1].text.lower() if conversation_state.messages else ""
        
        # Continue if scammer is still engaging and providing information
        engagement_indicators = [
            'call', 'contact', 'number', 'id', 'department', 'verify',
            'send', 'share', 'provide', 'give', 'tell', 'confirm'
        ]
        
        has_engagement = any(indicator in last_message for indicator in engagement_indicators)
        
        # Stop if conversation seems to be ending
        ending_indicators = ['goodbye', 'bye', 'later', 'thank you', 'thanks', 'ok bye']
        is_ending = any(indicator in last_message for indicator in ending_indicators)
        
        return has_engagement and not is_ending and len(conversation_state.messages) < 15