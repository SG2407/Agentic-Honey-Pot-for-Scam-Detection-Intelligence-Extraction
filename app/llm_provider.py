"""
PRIORITY 2: Abstract LLM Provider Interface
Supports multiple providers (OpenRouter, Groq) with fallback
"""

import os
import logging
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    def generate(self, prompt: str, model: str, temperature: float, max_tokens: int) -> Optional[str]:
        """Generate text from prompt"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available"""
        pass


class OpenRouterProvider(LLMProvider):
    """OpenRouter LLM Provider - Primary provider for stability"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1"
        self.default_model = os.getenv("OPENROUTER_CONVERSATION_MODEL", "google/gemini-2.0-flash-exp:free")
        self._client = None
        
        # Read LLM enhancement settings from environment
        self.frequency_penalty = float(os.getenv("LLM_FREQUENCY_PENALTY", "0.3"))
        self.presence_penalty = float(os.getenv("LLM_PRESENCE_PENALTY", "0.2"))
        self.top_p = float(os.getenv("LLM_TOP_P", "0.95"))
    
    def is_available(self) -> bool:
        """Check if OpenRouter is available"""
        return bool(self.api_key)
    
    def generate(self, prompt: str, model: Optional[str] = None, 
                 temperature: float = 0.7, max_tokens: int = 100) -> Optional[str]:
        """Generate text using OpenRouter API with enhanced parameters for human-like responses"""
        if not self.is_available():
            logger.warning("OpenRouter API key not set")
            return None
        
        try:
            # Lazy import to avoid dependency issues
            from openai import OpenAI
            
            if not self._client:
                self._client = OpenAI(
                    base_url=self.base_url,
                    api_key=self.api_key,
                )
            
            # Use default model if not specified
            model_to_use = model if model else self.default_model
            
            # Enhanced parameters for more human-like, varied responses
            response = self._client.chat.completions.create(
                model=model_to_use,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=self.top_p,  # Nucleus sampling for more diverse responses
                frequency_penalty=self.frequency_penalty,  # Reduce repetition of phrases
                presence_penalty=self.presence_penalty,  # Encourage topic diversity
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenRouter generation failed: {e}")
            return None


class GroqProvider(LLMProvider):
    """Groq LLM Provider - Fallback provider"""
    
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.default_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        self._client = None
        
        # Read LLM enhancement settings from environment
        self.frequency_penalty = float(os.getenv("LLM_FREQUENCY_PENALTY", "0.3"))
        self.presence_penalty = float(os.getenv("LLM_PRESENCE_PENALTY", "0.2"))
        self.top_p = float(os.getenv("LLM_TOP_P", "0.95"))
    
    def is_available(self) -> bool:
        """Check if Groq is available"""
        return bool(self.api_key)
    
    def generate(self, prompt: str, model: Optional[str] = None,
                 temperature: float = 0.7, max_tokens: int = 100) -> Optional[str]:
        """Generate text using Groq API with enhanced parameters for human-like responses"""
        if not self.is_available():
            logger.warning("Groq API key not set")
            return None
        
        try:
            from groq import Groq
            
            if not self._client:
                self._client = Groq(api_key=self.api_key)
            
            # Use default model if not specified
            model_to_use = model if model else self.default_model
            
            # Enhanced parameters for more human-like, varied responses
            response = self._client.chat.completions.create(
                model=model_to_use,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=self.top_p,  # Nucleus sampling for more diverse responses
                frequency_penalty=self.frequency_penalty,  # Reduce repetition of phrases
                presence_penalty=self.presence_penalty,  # Encourage topic diversity
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Groq generation failed: {e}")
            return None


class LLMManager:
    """
    PRIORITY 2: LLM Manager with automatic fallback
    
    Two-tier fallback strategy (OPTIMIZED FOR SPEED):
    1. OpenRouter Primary: meta-llama/llama-3.1-8b-instruct (fast, cheap, reliable)
    2. Groq Fallback: llama-3.3-70b-versatile (fast, reliable fallback)
    3. Template-based responses (final fallback in conversation_agent)
    """
    
    def __init__(self):
        # Create provider instances
        openrouter_primary = OpenRouterProvider()
        groq_fallback = GroqProvider()
        
        # Configure models - OpenRouter first, then Groq
        self.providers = [
            (openrouter_primary, "meta-llama/llama-3.1-8b-instruct"),     # Tier 1: Fast & cheap
            (groq_fallback, None),                                         # Tier 2: Fast fallback
        ]
        
        # Log available providers
        available = []
        for provider, model in self.providers:
            if provider.is_available():
                model_name = model if model else "default"
                available.append(f"{provider.__class__.__name__}({model_name})")
        
        if available:
            logger.info(f"✅ LLM providers available: {', '.join(available)}")
        else:
            logger.warning("⚠️  No LLM providers available - using fallback templates only")
    
    def generate(self, prompt: str, model: Optional[str] = None, 
                 temperature: float = 0.7, max_tokens: int = 100) -> Optional[str]:
        """
        Generate text with automatic provider fallback
        
        Returns None if all providers fail (caller should use template fallback)
        """
        for provider, default_model in self.providers:
            if not provider.is_available():
                continue
            
            try:
                # Use specified model, or provider's configured default, or provider's built-in default
                model_to_use = model if model else default_model
                provider_name = f"{provider.__class__.__name__}({model_to_use if model_to_use else 'default'})"
                
                logger.info(f"🤖 Attempting generation with {provider_name}")
                result = provider.generate(prompt, model_to_use, temperature, max_tokens)
                
                if result:
                    logger.info(f"✅ Generation successful with {provider_name}")
                    return result
                    
            except Exception as e:
                logger.warning(f"⚠️  {provider.__class__.__name__} failed: {e}")
                continue
        
        logger.warning("⚠️  All LLM providers failed - caller should use template fallback")
        return None
