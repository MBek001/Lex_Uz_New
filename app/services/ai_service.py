"""
AI Service for embeddings and chat completions using Qwen
"""
import httpx
import logging
import os
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class AIService:
    """Service for interacting with Qwen AI"""

    def __init__(self):
        # Load from environment variables
        self.emb_url = os.getenv("EMB_URL", "").strip('"')
        self.llm_url = os.getenv("LLM_URL", "").strip('"')
        self.api_key = os.getenv("API_KEY", "").strip('"')
        self.model_name = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct").strip('"')  # Default model
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3").strip('"')
        self.timeout = 30.0

        if not self.api_key:
            logger.error("API_KEY not found in environment variables!")
        else:
            logger.info(f"AI Service initialized with API key: {self.api_key[:10]}...")
            logger.info(f"Using LLM model: {self.model_name}")
            logger.info(f"Using embedding model: {self.embedding_model}")

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
                        "model": self.embedding_model
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
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.llm_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model_name,
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

    async def extract_search_keywords(
        self,
        user_message: str,
        language: str
    ) -> Dict[str, any]:
        """
        FIRST STAGE AI: Extract search keywords and intent from user message.
        This AI only analyzes the query, does NOT generate final response.

        Args:
            user_message: User's question
            language: Detected language ('ru' or 'uz')

        Returns:
            Dict with keywords, document_numbers, categories, intent
        """
        try:
            system_prompt = """You are a search query analyzer for a legal document database.
Your task is to extract key information from the user's question to help search for relevant documents.

Extract and return ONLY these items in JSON format:
{
  "keywords": ["word1", "word2"],  // Main search terms
  "document_numbers": ["123", "456"],  // Any document/law numbers mentioned
  "categories": ["category1"],  // Document type/category if mentioned
  "intent": "brief description of what user wants"
}

Examples:
User: "prokratura tizimi haqida malumot ber"
Return: {"keywords": ["прокуратура", "система", "prokuratura"], "document_numbers": [], "categories": ["закон", "qonun"], "intent": "information about prosecutor system"}

User: "940 sonli qonun"
Return: {"keywords": ["закон", "qonun"], "document_numbers": ["940"], "categories": ["qonun", "закон"], "intent": "law number 940"}

IMPORTANT: Return ONLY the JSON, no other text."""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]

            response = await self.chat_completion(
                messages=messages,
                temperature=0.3,  # Lower temperature for more focused extraction
                max_tokens=300
            )

            if not response:
                # Fallback: simple extraction
                return {
                    "keywords": user_message.split()[:5],
                    "document_numbers": [],
                    "categories": [],
                    "intent": user_message
                }

            # Try to parse JSON response
            import json
            try:
                # Extract JSON from response (in case AI adds extra text)
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    result = json.loads(response[json_start:json_end])
                    logger.info(f"Extracted search keywords: {result}")
                    return result
                else:
                    raise ValueError("No JSON found in response")
            except:
                # Fallback
                return {
                    "keywords": user_message.split()[:5],
                    "document_numbers": [],
                    "categories": [],
                    "intent": user_message
                }

        except Exception as e:
            logger.error(f"Error extracting keywords: {str(e)}")
            return {
                "keywords": user_message.split()[:5],
                "document_numbers": [],
                "categories": [],
                "intent": user_message
            }

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
