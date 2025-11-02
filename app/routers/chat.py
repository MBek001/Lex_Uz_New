"""
API endpoints for AI chat with RAG
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import logging

from app.config.database import get_db
from app.services.rag_service import RAGService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatMessage(BaseModel):
    """Chat message model"""
    role: str  # 'user' or 'assistant'
    content: str


class ChatRequest(BaseModel):
    """Chat request model"""
    message: str
    conversation_history: Optional[List[ChatMessage]] = None


class ChatResponse(BaseModel):
    """Chat response model"""
    response: str
    language: str
    documents_found: int
    metadata: List[dict]


@router.post("/message", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Send a message to AI assistant with RAG.

    The system will:
    1. Detect user language (Russian/Uzbek)
    2. Search for relevant documents
    3. Retrieve full document content
    4. Generate AI response with context

    Args:
        request: Chat request with message and optional history

    Returns:
        AI response with metadata
    """
    try:
        if not request.message or not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")

        # Initialize RAG service
        rag_service = RAGService()

        # Convert conversation history to dict format if provided
        history = None
        if request.conversation_history:
            history = [
                {"role": msg.role, "content": msg.content}
                for msg in request.conversation_history
            ]

        # Get AI response with RAG
        result = await rag_service.chat(
            db=db,
            user_message=request.message,
            conversation_history=history
        )

        if 'error' in result:
            raise HTTPException(status_code=500, detail=result['error'])

        return ChatResponse(
            response=result['response'],
            language=result.get('language', 'ru'),
            documents_found=result.get('documents_found', 0),
            metadata=result.get('metadata', [])
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")


@router.get("/health")
async def chat_health():
    """Check if chat service is available"""
    return {"status": "healthy", "service": "chat"}
