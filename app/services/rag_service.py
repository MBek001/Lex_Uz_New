"""
RAG (Retrieval-Augmented Generation) Service
Handles document search and AI chat with context
"""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
import logging

from app.models.metadata import DocumentMetadata
from app.models.documents import RussianDocument, UzbekDocument
from app.services.ai_service import AIService

logger = logging.getLogger(__name__)


class RAGService:
    """RAG service for intelligent document search and chat"""

    def __init__(self):
        self.ai_service = AIService()

    async def search_metadata(
        self,
        db: Session,
        query: str,
        limit: int = 5
    ) -> List[DocumentMetadata]:
        """
        Search document metadata based on user query.

        Args:
            db: Database session
            query: User query text
            limit: Maximum number of results

        Returns:
            List of matching DocumentMetadata objects
        """
        try:
            # Search by title, doc_type, or category
            results = db.query(DocumentMetadata)\
                .filter(
                    or_(
                        DocumentMetadata.title.ilike(f'%{query}%'),
                        DocumentMetadata.doc_type.ilike(f'%{query}%'),
                        DocumentMetadata.category.ilike(f'%{query}%'),
                        DocumentMetadata.number.ilike(f'%{query}%')
                    )
                )\
                .filter(
                    # Prefer active documents (status = "0")
                    or_(
                        DocumentMetadata.status == "0",
                        DocumentMetadata.status == ""
                    )
                )\
                .limit(limit * 2)\
                .all()

            # Sort by relevance (simple scoring)
            scored_results = []
            query_lower = query.lower()

            for doc in results:
                score = 0
                # Title match is most important
                if query_lower in doc.title.lower():
                    score += 10
                # Doc type match
                if query_lower in doc.doc_type.lower():
                    score += 5
                # Category match
                if doc.category and query_lower in doc.category.lower():
                    score += 3
                # Number match
                if doc.number and query_lower in doc.number.lower():
                    score += 7

                scored_results.append((score, doc))

            # Sort by score and return top results
            scored_results.sort(reverse=True, key=lambda x: x[0])
            return [doc for score, doc in scored_results[:limit]]

        except Exception as e:
            logger.error(f"Error searching metadata: {str(e)}")
            return []

    def get_document_content(
        self,
        db: Session,
        doc_id: str,
        language: str
    ) -> Optional[str]:
        """
        Get full document content by ID and language.

        Args:
            db: Database session
            doc_id: Document ID (e.g., "7630588" or "-7630445")
            language: 'ru' or 'uz'

        Returns:
            Document content or None
        """
        try:
            # The document title in database is like "-7630588.doc"
            title_pattern = f"{doc_id}.doc"

            # Choose table based on language
            model_class = RussianDocument if language == 'ru' else UzbekDocument

            # Search by title
            doc = db.query(model_class)\
                .filter(model_class.title.ilike(f'%{title_pattern}%'))\
                .first()

            if doc:
                return doc.content

            # Try without extension
            doc = db.query(model_class)\
                .filter(model_class.title.ilike(f'%{doc_id}%'))\
                .first()

            return doc.content if doc else None

        except Exception as e:
            logger.error(f"Error getting document content: {str(e)}")
            return None

    async def chat(
        self,
        db: Session,
        user_message: str,
        conversation_history: List[Dict[str, str]] = None
    ) -> Dict:
        """
        Main chat function with RAG.

        Args:
            db: Database session
            user_message: User's message
            conversation_history: Previous conversation (optional)

        Returns:
            Dict with response and metadata
        """
        try:
            # 1. Detect language
            language = self.ai_service.detect_language(user_message)
            logger.info(f"Detected language: {language}")

            # 2. Search for relevant metadata
            metadata_results = await self.search_metadata(db, user_message, limit=3)
            logger.info(f"Found {len(metadata_results)} metadata results")

            # 3. Retrieve full document contents
            documents_context = []
            for metadata in metadata_results:
                doc_id = metadata.get_doc_id_from_link(language)
                if doc_id:
                    content = self.get_document_content(db, doc_id, language)
                    if content:
                        documents_context.append({
                            'metadata': {
                                'title': metadata.title,
                                'doc_type': metadata.doc_type,
                                'number': metadata.number,
                                'date': str(metadata.registration_date) if metadata.registration_date else None,
                                'status': metadata.status,
                                'category': metadata.category
                            },
                            'content': content[:2000]  # Limit content length
                        })

            # 4. Build context for AI
            context_text = self._build_context(documents_context, language)

            # 5. Prepare messages for AI
            system_message = self._get_system_message(language)

            messages = [
                {"role": "system", "content": system_message}
            ]

            # Add conversation history if provided
            if conversation_history:
                messages.extend(conversation_history[-4:])  # Last 4 messages for context

            # Add context and user message
            if context_text:
                messages.append({
                    "role": "user",
                    "content": f"Контекст:\n{context_text}\n\nВопрос: {user_message}"
                })
            else:
                messages.append({
                    "role": "user",
                    "content": user_message
                })

            # 6. Get AI response
            response = await self.ai_service.chat_completion(
                messages=messages,
                temperature=0.7,
                max_tokens=1500
            )

            return {
                'response': response,
                'language': language,
                'documents_found': len(documents_context),
                'metadata': [doc['metadata'] for doc in documents_context]
            }

        except Exception as e:
            logger.error(f"Error in chat: {str(e)}")
            return {
                'response': "Извините, произошла ошибка при обработке вашего запроса." if language == 'ru'
                           else "Kechirasiz, so'rovingizni qayta ishlashda xatolik yuz berdi.",
                'error': str(e)
            }

    def _build_context(self, documents: List[Dict], language: str) -> str:
        """Build context text from documents"""
        if not documents:
            return ""

        context_parts = []
        for idx, doc in enumerate(documents, 1):
            meta = doc['metadata']
            context_parts.append(
                f"Документ {idx}:\n"
                f"Название: {meta['title']}\n"
                f"Тип: {meta['doc_type']}\n"
                f"Номер: {meta['number']}\n"
                f"Дата: {meta['date']}\n"
                f"Статус: {meta['status']}\n"
                f"Категория: {meta['category']}\n"
                f"Содержание: {doc['content'][:1500]}...\n"
            )

        return "\n---\n".join(context_parts)

    def _get_system_message(self, language: str) -> str:
        """Get system message for AI based on language"""
        if language == 'ru':
            return """Вы - помощник по правовым вопросам Узбекистана.
Ваша задача - отвечать на вопросы пользователей о законах и нормативных актах.
Используйте предоставленный контекст документов для точных ответов.
Отвечайте кратко, но полно. Если информации недостаточно, так и скажите.
Всегда указывайте источник информации (название документа)."""
        else:
            return """Siz O'zbekiston huquqiy masalalari bo'yicha yordamchisiz.
Sizning vazifangiz - foydalanuvchilarning qonunlar va me'yoriy hujjatlar haqidagi savollariga javob berish.
Aniq javoblar uchun taqdim etilgan hujjatlar kontekstidan foydalaning.
Qisqa, lekin to'liq javob bering. Agar ma'lumot yetarli bo'lmasa, shunday ayting.
Har doim ma'lumot manbasini (hujjat nomi) ko'rsating."""
