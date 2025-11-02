"""
RAG (Retrieval-Augmented Generation) Service
Handles document search and AI chat with context
"""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
import logging
import re

from app.models.metadata import DocumentMetadata
from app.models.documents import RussianDocument, UzbekDocument
from app.services.ai_service import AIService

logger = logging.getLogger(__name__)


class RAGService:
    """RAG service for intelligent document search and chat"""

    def __init__(self):
        self.ai_service = AIService()

    async def extract_search_keywords(self, user_message: str, language: str) -> List[str]:
        """
        Use AI to extract key search terms from user's natural language question.

        Args:
            user_message: User's question in natural language
            language: Detected language ('ru' or 'uz')

        Returns:
            List of search keywords
        """
        try:
            if language == 'ru':
                prompt = f"""Извлеките ключевые слова для поиска в базе данных юридических документов из вопроса пользователя.
Верните только ключевые слова через запятую, без объяснений.

Вопрос: {user_message}

Ключевые слова:"""
            else:
                prompt = f"""Foydalanuvchi savolidan qonuniy hujjatlar bazasidan qidirish uchun asosiy kalit so'zlarni ajratib oling.
Faqat kalit so'zlarni vergul bilan qaytaring, tushuntirmasdan.

Savol: {user_message}

Kalit so'zlar:"""

            messages = [{"role": "user", "content": prompt}]
            response = await self.ai_service.chat_completion(
                messages=messages,
                temperature=0.3,
                max_tokens=50
            )

            # Extract keywords from response
            keywords = [kw.strip() for kw in response.split(',') if kw.strip()]

            # Also extract words from original message (fallback)
            # Remove common words
            common_words = {
                'ru': ['о', 'в', 'на', 'с', 'по', 'для', 'от', 'до', 'из', 'к', 'у', 'и', 'а', 'но', 'что', 'как', 'это', 'мне', 'расскажите', 'покажите', 'дайте', 'информацию', 'данные'],
                'uz': ['haqida', 'haqidagi', 'bo\'yicha', 'uchun', 'bilan', 'dan', 'ga', 'ning', 'va', 'yoki', 'lekin', 'nima', 'qanday', 'bu', 'menga', 'aytib', 'bering', 'malumot', 'ma\'lumot']
            }

            words = re.findall(r'\b\w+\b', user_message.lower())
            filtered_words = [w for w in words if w not in common_words.get(language, []) and len(w) > 2]

            # Combine AI keywords with filtered words
            all_keywords = list(set(keywords + filtered_words))

            logger.info(f"Extracted keywords: {all_keywords}")
            return all_keywords[:10]  # Limit to top 10

        except Exception as e:
            logger.error(f"Error extracting keywords: {str(e)}")
            # Fallback: return words from message
            return [w for w in re.findall(r'\b\w+\b', user_message.lower()) if len(w) > 3][:5]

    async def search_metadata(
        self,
        db: Session,
        keywords: List[str],
        limit: int = 5
    ) -> List[DocumentMetadata]:
        """
        Search document metadata using extracted keywords.

        Args:
            db: Database session
            keywords: List of search keywords
            limit: Maximum number of results

        Returns:
            List of matching DocumentMetadata objects
        """
        try:
            if not keywords:
                return []

            # Build OR conditions for each keyword
            conditions = []
            for keyword in keywords:
                keyword_pattern = f'%{keyword}%'
                conditions.append(
                    or_(
                        DocumentMetadata.title.ilike(keyword_pattern),
                        DocumentMetadata.doc_type.ilike(keyword_pattern),
                        DocumentMetadata.category.ilike(keyword_pattern),
                        DocumentMetadata.number.ilike(keyword_pattern)
                    )
                )

            # Combine all conditions with OR
            combined_condition = or_(*conditions)

            # Execute search
            results = db.query(DocumentMetadata)\
                .filter(combined_condition)\
                .filter(
                    # Prefer active documents (status = "0")
                    or_(
                        DocumentMetadata.status == "0",
                        DocumentMetadata.status == "",
                        DocumentMetadata.status == None
                    )
                )\
                .limit(limit * 3)\
                .all()

            if not results:
                logger.warning(f"No results found for keywords: {keywords}")
                return []

            # Score results based on keyword matches
            scored_results = []
            for doc in results:
                score = 0
                doc_text = f"{doc.title} {doc.doc_type} {doc.category or ''} {doc.number or ''}".lower()

                for keyword in keywords:
                    keyword_lower = keyword.lower()
                    if keyword_lower in doc_text:
                        # Title match is most important
                        if keyword_lower in doc.title.lower():
                            score += 10
                        # Doc type match
                        if keyword_lower in doc.doc_type.lower():
                            score += 7
                        # Category match
                        if doc.category and keyword_lower in doc.category.lower():
                            score += 5
                        # Number match
                        if doc.number and keyword_lower in doc.number.lower():
                            score += 8

                if score > 0:
                    scored_results.append((score, doc))

            # Sort by score and return top results
            scored_results.sort(reverse=True, key=lambda x: x[0])
            top_results = [doc for score, doc in scored_results[:limit]]

            logger.info(f"Found {len(top_results)} documents with scores")
            return top_results

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
                logger.info(f"Found document with ID {doc_id} in {language} documents")
                return doc.content

            # Try without extension
            doc = db.query(model_class)\
                .filter(model_class.title.ilike(f'%{doc_id}%'))\
                .first()

            if doc:
                logger.info(f"Found document with ID {doc_id} (without extension)")
                return doc.content

            logger.warning(f"Document with ID {doc_id} not found in {language} documents")
            return None

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

        Flow:
        1. Detect language
        2. Extract keywords from user message using AI
        3. Search metadata using keywords
        4. Get document IDs from metadata links
        5. Fetch full content from documents tables
        6. Build context with metadata + content
        7. Send to AI with context
        8. Return response with links

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

            # 2. Extract search keywords from user message
            keywords = await self.extract_search_keywords(user_message, language)
            logger.info(f"Extracted keywords: {keywords}")

            # 3. Search for relevant metadata using keywords
            metadata_results = await self.search_metadata(db, keywords, limit=5)
            logger.info(f"Found {len(metadata_results)} metadata results")

            # 4. Retrieve full document contents
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
                                'category': metadata.category,
                                'link_rus': metadata.link_rus,
                                'link_uz_latin': metadata.link_uz_latin,
                                'link_uz_cyrillic': metadata.link_uz_cyrillic
                            },
                            'content': content[:3000]  # Increased to 3000 chars for more context
                        })
                        logger.info(f"Added document: {metadata.title} (ID: {doc_id})")

            # 5. Build context for AI
            context_text = self._build_context(documents_context, language)

            # 6. Prepare messages for AI
            system_message = self._get_system_message(language)

            messages = [
                {"role": "system", "content": system_message}
            ]

            # Add conversation history if provided
            if conversation_history:
                # Filter out empty content
                valid_history = [msg for msg in conversation_history if msg.get('content', '').strip()]
                messages.extend(valid_history[-4:])  # Last 4 messages for context

            # Add context and user message
            if context_text:
                if language == 'ru':
                    messages.append({
                        "role": "user",
                        "content": f"Контекст из базы данных:\n{context_text}\n\nВопрос пользователя: {user_message}\n\nВажно: Используйте только информацию из предоставленного контекста. Обязательно укажите ссылки на документы."
                    })
                else:
                    messages.append({
                        "role": "user",
                        "content": f"Ma'lumotlar bazasidan kontekst:\n{context_text}\n\nFoydalanuvchi savoli: {user_message}\n\nMuhim: Faqat taqdim etilgan kontekstdan foydalaning. Hujjatlarga havolalarni ko'rsating."
                    })
            else:
                messages.append({
                    "role": "user",
                    "content": user_message
                })
                logger.warning("No documents found, AI will use general knowledge")

            # 7. Get AI response
            response = await self.ai_service.chat_completion(
                messages=messages,
                temperature=0.7,
                max_tokens=2000
            )

            # Determine source of response
            source = "dataset" if len(documents_context) > 0 else "ai_knowledge"

            return {
                'response': response,
                'language': language,
                'source': source,
                'keywords_used': keywords,  # Show which keywords were used for search
                'documents_found': len(documents_context),
                'metadata': [doc['metadata'] for doc in documents_context]
            }

        except Exception as e:
            logger.error(f"Error in chat: {str(e)}", exc_info=True)
            return {
                'response': "Извините, произошла ошибка при обработке вашего запроса." if language == 'ru'
                           else "Kechirasiz, so'rovingizni qayta ishlashda xatolik yuz berdi.",
                'source': 'error',
                'documents_found': 0,
                'metadata': [],
                'error': str(e)
            }

    def _build_context(self, documents: List[Dict], language: str) -> str:
        """Build context text from documents"""
        if not documents:
            return ""

        context_parts = []
        for idx, doc in enumerate(documents, 1):
            meta = doc['metadata']
            # Choose appropriate link based on language
            link = meta.get('link_rus') if language == 'ru' else meta.get('link_uz_latin')

            if language == 'ru':
                context_parts.append(
                    f"Документ {idx}:\n"
                    f"Название: {meta['title']}\n"
                    f"Тип: {meta['doc_type']}\n"
                    f"Номер: {meta['number']}\n"
                    f"Дата: {meta['date']}\n"
                    f"Ссылка: {link}\n"
                    f"Содержание: {doc['content'][:2000]}...\n"
                )
            else:
                context_parts.append(
                    f"Hujjat {idx}:\n"
                    f"Nomi: {meta['title']}\n"
                    f"Turi: {meta['doc_type']}\n"
                    f"Raqami: {meta['number']}\n"
                    f"Sana: {meta['date']}\n"
                    f"Havola: {link}\n"
                    f"Mazmuni: {doc['content'][:2000]}...\n"
                )

        return "\n---\n".join(context_parts)

    def _get_system_message(self, language: str) -> str:
        """Get system message for AI based on language"""
        if language == 'ru':
            return """Вы - помощник по правовым вопросам Узбекистана.
Ваша задача - отвечать на вопросы пользователей о законах и нормативных актах на основе предоставленных документов.

ВАЖНО:
- Используйте ТОЛЬКО информацию из предоставленного контекста документов
- ВСЕГДА указывайте ссылки на документы, откуда взята информация
- Если в контексте нет нужной информации, честно скажите об этом
- Отвечайте четко и структурированно"""
        else:
            return """Siz O'zbekiston huquqiy masalalari bo'yicha yordamchisiz.
Sizning vazifangiz - taqdim etilgan hujjatlar asosida foydalanuvchilarning qonunlar va me'yoriy hujjatlar haqidagi savollariga javob berish.

MUHIM:
- FAQAT taqdim etilgan hujjatlar kontekstidan foydalaning
- HAR DOIM ma'lumot olingan hujjatlarga havolalarni ko'rsating
- Agar kontekstda kerakli ma'lumot bo'lmasa, halol aytib bering
- Aniq va tuzilgan javob bering"""
