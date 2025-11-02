"""
AI Service for embeddings and chat completions using Qwen
"""
import httpx
import logging
from typing import List, Dict, Optional
import asyncio

logger = logging.getLogger(__name__)


class AIService:
    """Service for interacting with Qwen AI"""

    def __init__(self):
        self.emb_url = "https://p950-w002-runai-r01-p950.runai-inference.dc.uz/v1/embeddings"
        self.llm_url = "https://p950-w003-runai-r01-p950.runai-inference.dc.uz/v1/chat/completions"
        self.api_key = "5df1454b1e95b2648fd89d"
        self.timeout = 30.0

    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """
        Get embedding vector for text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector or None if failed
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.emb_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "input": text,
                        "model": "text-embedding-ada-002"  # Adjust model if needed
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    return data['data'][0]['embedding']
                else:
                    logger.error(f"Embedding API error: {response.status_code} - {response.text}")
                    return None

        except Exception as e:
            logger.error(f"Error getting embedding: {str(e)}")
            return None

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Optional[str]:
        """
        Get chat completion from Qwen AI.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response

        Returns:
            AI response text or None if failed
        """
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.llm_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "qwen",  # Adjust model name if needed
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    return data['choices'][0]['message']['content']
                else:
                    logger.error(f"Chat API error: {response.status_code} - {response.text}")
                    return None

        except Exception as e:
            logger.error(f"Error getting chat completion: {str(e)}")
            return None

    def detect_language(self, text: str) -> str:
        """
        Detect language from text (Russian or Uzbek).

        Args:
            text: Text to analyze

        Returns:
            'ru' for Russian, 'uz' for Uzbek
        """
        # Simple detection based on Cyrillic characters
        cyrillic_chars = sum(1 for c in text if '\u0400' <= c <= '\u04FF')
        latin_chars = sum(1 for c in text if c.isalpha() and c.isascii())

        # Uzbek-specific characters
        uzbek_chars = sum(1 for c in text if c in "oʻgʻ'Oʻ'Gʻ")

        total_chars = cyrillic_chars + latin_chars + uzbek_chars

        if total_chars == 0:
            return 'ru'  # Default to Russian

        # If mostly Cyrillic, it's Russian
        if cyrillic_chars / total_chars > 0.5:
            return 'ru'

        # If has Uzbek-specific chars or mostly Latin, it's Uzbek
        return 'uz'
