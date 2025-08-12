"""
LLM client for the AI-Powered Enterprise Workflow Agent.

This module provides a unified interface for interacting with different
LLM providers (OpenAI, Groq, Anthropic) for natural language processing tasks.
"""

import os
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
import json

from src.core.config import config
from src.core.exceptions import LLMError
from src.utils.logger import get_logger

logger = get_logger("llm_client")

class BaseLLMClient(ABC):
    """Base class for LLM clients."""
    
    def __init__(self, model_name: str, temperature: float = 0.1, max_tokens: int = 2000):
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
    
    @abstractmethod
    def generate_completion(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate a completion for the given prompt."""
        pass
    
    @abstractmethod
    def generate_structured_output(
        self,
        prompt: str,
        schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate structured output based on a schema."""
        pass

class OpenAIClient(BaseLLMClient):
    """OpenAI LLM client."""
    
    def __init__(self, model_name: str = "gpt-4", **kwargs):
        super().__init__(model_name, **kwargs)
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=config.llm.openai_api_key)
        except ImportError:
            raise LLMError("OpenAI library not installed")
        except Exception as e:
            raise LLMError(f"Failed to initialize OpenAI client: {e}")
    
    def generate_completion(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate a completion using OpenAI."""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                **kwargs
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI completion error: {e}")
            raise LLMError(f"OpenAI completion failed: {e}")
    
    def generate_structured_output(
        self,
        prompt: str,
        schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate structured output using OpenAI."""
        try:
            # Add JSON schema instruction to the prompt
            json_prompt = f"{prompt}\n\nPlease respond with a valid JSON object that matches this schema:\n{json.dumps(schema, indent=2)}"
            
            completion = self.generate_completion(json_prompt, system_prompt, **kwargs)
            
            # Parse JSON response
            try:
                return json.loads(completion)
            except json.JSONDecodeError:
                # Try to extract JSON from the response
                import re
                json_match = re.search(r'\{.*\}', completion, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    raise LLMError("Failed to parse JSON from LLM response")
                    
        except Exception as e:
            logger.error(f"OpenAI structured output error: {e}")
            raise LLMError(f"OpenAI structured output failed: {e}")

class GroqClient(BaseLLMClient):
    """Groq LLM client."""
    
    def __init__(self, model_name: str = "llama3-70b-8192", **kwargs):
        super().__init__(model_name, **kwargs)
        try:
            from groq import Groq
            self.client = Groq(api_key=config.llm.groq_api_key)
        except ImportError:
            raise LLMError("Groq library not installed")
        except Exception as e:
            raise LLMError(f"Failed to initialize Groq client: {e}")
    
    def generate_completion(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate a completion using Groq."""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                **kwargs
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq completion error: {e}")
            raise LLMError(f"Groq completion failed: {e}")
    
    def generate_structured_output(
        self,
        prompt: str,
        schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate structured output using Groq."""
        try:
            # Add JSON schema instruction to the prompt
            json_prompt = f"{prompt}\n\nPlease respond with a valid JSON object that matches this schema:\n{json.dumps(schema, indent=2)}"
            
            completion = self.generate_completion(json_prompt, system_prompt, **kwargs)
            
            # Parse JSON response
            try:
                return json.loads(completion)
            except json.JSONDecodeError:
                # Try to extract JSON from the response
                import re
                json_match = re.search(r'\{.*\}', completion, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    raise LLMError("Failed to parse JSON from LLM response")
                    
        except Exception as e:
            logger.error(f"Groq structured output error: {e}")
            raise LLMError(f"Groq structured output failed: {e}")

class LLMClientFactory:
    """Factory for creating LLM clients."""
    
    @staticmethod
    def create_client(
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        **kwargs
    ) -> BaseLLMClient:
        """Create an LLM client based on the provider."""
        provider = provider or config.llm.default_provider
        
        if provider == "openai":
            model_name = model_name or config.get_llm_model("default")
            return OpenAIClient(model_name=model_name, **kwargs)
        elif provider == "groq":
            model_name = model_name or config.get_llm_model("default")
            return GroqClient(model_name=model_name, **kwargs)
        else:
            raise LLMError(f"Unsupported LLM provider: {provider}")
    
    @staticmethod
    def create_classification_client() -> BaseLLMClient:
        """Create a client optimized for classification tasks."""
        provider = config.llm.default_provider
        model_name = config.get_llm_model("classification")
        return LLMClientFactory.create_client(
            provider=provider,
            model_name=model_name,
            temperature=0.1,
            max_tokens=1000
        )
    
    @staticmethod
    def create_assignment_client() -> BaseLLMClient:
        """Create a client optimized for assignment tasks."""
        provider = config.llm.default_provider
        model_name = config.get_llm_model("assignment")
        return LLMClientFactory.create_client(
            provider=provider,
            model_name=model_name,
            temperature=0.2,
            max_tokens=1500
        )
    
    @staticmethod
    def create_reporting_client() -> BaseLLMClient:
        """Create a client optimized for reporting tasks."""
        provider = config.llm.default_provider
        model_name = config.get_llm_model("reporting")
        return LLMClientFactory.create_client(
            provider=provider,
            model_name=model_name,
            temperature=0.3,
            max_tokens=2000
        )
