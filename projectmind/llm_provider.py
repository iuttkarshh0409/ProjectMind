import os
from abc import ABC, abstractmethod
from typing import Dict, Any
from google import genai
from google.genai import types

class BaseLLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, schema: Dict[str, Any]) -> str:
        """Generates a text/JSON completion for the given prompt with schema validation."""
        pass

class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: str = None):
        # Fallback to env variable if key is not passed
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured. Please set the environment variable.")
        self.client = genai.Client(api_key=self.api_key)

    def generate(self, prompt: str, schema: Dict[str, Any]) -> str:
        """Calls Gemini API using google-genai SDK with strict JSON schema response configuration."""
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema,
                    temperature=0.1,  # Low temperature for reproducibility and determinism
                ),
            )
            return response.text
        except Exception as e:
            # Propagate cleaner exceptions for integration issues
            raise RuntimeError(f"Gemini API request failed: {e}")
