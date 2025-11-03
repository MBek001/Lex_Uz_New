"""
IMPROVED RAG (Retrieval-Augmented Generation) Service
Features:
- Two-stage AI process (search extraction + response generation)
- Full-text search with PostgreSQL for speed
- Better document matching from ru_documents and uz_documents tables
- Detailed logging showing which tables are used
"""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, text, func
import logging

from app.models.metadata import DocumentMetadata
from app.models.documents import RussianDocument, UzbekDocument
from app.services.ai_service import AIService

logger = logging.getLogger(__name__)


class RAGService:
    """Improved RAG service with two-stage AI and fast full-text search"""

    def __init__(self):
        self.ai_service = AIService()

    async def search_documents_fulltext(
        self,
        db: Session,
        keywords: List[str],
        language: str,
        limit: int = 10
    ) -> List[Dict]:
        """
        Search directly in ru_documents/uz_documents using full-text search.
        This is MUCH faster than ILIKE and searches actual document content.

        Args:
            db: Database session
            keywords: List of search keywords
            language: 'ru' or 'uz'
            limit: Maximum number of results

        Returns:
            List of documents with content
        """
        try:
            model_class = RussianDocument if language == 'ru' else UzbekDocument
            table_name = 'ru_documents' if language == 'ru' else 'uz_documents'

            logger.info(f"🔍 [SEARCH] Searching in {table_name} table with keywords: {keywords}")

            # Build search query
            search_terms = ' | '.join(keywords)  # OR search

            # Use full-text search with ranking
            query = text(f"""
                SELECT id, title, content,
                       ts_rank(search_vector, to_tsquery('russian', :search_terms)) as rank
                FROM {table_name}
                WHERE search_vector @@ to_tsquery('russian', :search_terms)
                ORDER BY rank DESC
                LIMIT :limit
            """)

            result = db.execute(query, {
                'search_terms': search_terms,
                'limit': limit
            })

            documents = []
            for row in result:
                documents.append({
                    'id': row[0],
                    'title': row[1],
                    'content': row[2][:3000],  # First 3000 chars
                    'rank': row[3],
                    'source_table': table_name
                })

            logger.info(f"✅ [SEARCH] Found {len(documents)} documents in {table_name}")
            for doc in documents[:3]:  # Log top 3
                logger.info(f"  📄 {doc['title']} (rank: {doc['rank']:.4f})")

            return documents

        except Exception as e:
            logger.error(f"❌ [SEARCH ERROR] Full-text search in {table_name} failed: {str(e)}")
            # Fallback to LIKE search if full-text search fails (indexes not created yet)
            return await self._fallback_search_documents(db, keywords, language, limit)

    async def _fallback_search_documents(
        self,
        db: Session,
        keywords: List[str],
        language: str,
        limit: int
    ) -> List[Dict]:
        """
        Fallback search using LIKE when full-text indexes don't exist yet.
        """
        try:
            model_class = RussianDocument if language == 'ru' else UzbekDocument
            table_name = 'ru_documents' if language == 'ru' else 'uz_documents'

            logger.warning(f"⚠️ [FALLBACK] Using LIKE search in {table_name} (slower)")

            # Build LIKE conditions
            conditions = []
            for keyword in keywords[:5]:  # Limit to 5 keywords
                conditions.append(model_class.title.ilike(f'%{keyword}%'))
                conditions.append(model_class.content.ilike(f'%{keyword}%'))

            query = db.query(model_class).filter(or_(*conditions)).limit(limit)

            documents = []
            for doc in query:
                documents.append({
                    'id': doc.id,
                    'title': doc.title,
                    'content': doc.content[:3000],
                    'rank': 0.5,
                    'source_table': table_name
                })

            logger.info(f"✅ [FALLBACK] Found {len(documents)} documents")
            return documents

        except Exception as e:
            logger.error(f"❌ [FALLBACK ERROR]: {str(e)}")
            return []

    async def search_metadata_fulltext(
        self,
        db: Session,
        keywords: List[str],
        document_numbers: List[str],
        limit: int = 5
    ) -> List[DocumentMetadata]:
        """
        Search metadata using full-text search.
        Faster than ILIKE for large datasets.

        Args:
            db: Database session
            keywords: Search keywords
            document_numbers: Specific document numbers if mentioned
            limit: Maximum results

        Returns:
            List of DocumentMetadata objects
        """
        try:
            logger.info(f"🔍 [METADATA SEARCH] Keywords: {keywords}, Numbers: {document_numbers}")

            # If specific document numbers mentioned, search by number first
            if document_numbers:
                number_results = db.query(DocumentMetadata).filter(
                    or_(*[DocumentMetadata.number.ilike(f'%{num}%') for num in document_numbers])
                ).limit(limit).all()

                if number_results:
                    logger.info(f"✅ [METADATA] Found {len(number_results)} documents by number")
                    return number_results

            # Use full-text search
            search_terms = ' | '.join(keywords[:10])  # Limit keywords

            query = text("""
                SELECT *, ts_rank(search_vector, to_tsquery('russian', :search_terms)) as rank
                FROM document_metadata
                WHERE search_vector @@ to_tsquery('russian', :search_terms)
                  AND (status = '0' OR status = '')
                ORDER BY rank DESC
                LIMIT :limit
            """)

            result = db.execute(query, {
                'search_terms': search_terms,
                'limit': limit
            })

            metadata_list = []
            for row in result:
                metadata = db.query(DocumentMetadata).filter(DocumentMetadata.id == row[0]).first()
                if metadata:
                    metadata_list.append(metadata)

            logger.info(f"✅ [METADATA] Found {len(metadata_list)} metadata records")
            return metadata_list

        except Exception as e:
            logger.error(f"❌ [METADATA SEARCH ERROR]: {str(e)}")
            # Fallback to LIKE search
            return await self._fallback_search_metadata(db, keywords, limit)

    async def _fallback_search_metadata(
        self,
        db: Session,
        keywords: List[str],
        limit: int
    ) -> List[DocumentMetadata]:
        """Fallback metadata search using LIKE"""
        try:
            logger.warning("⚠️ [FALLBACK] Using LIKE search for metadata")

            conditions = []
            for keyword in keywords[:5]:
                conditions.extend([
                    DocumentMetadata.title.ilike(f'%{keyword}%'),
                    DocumentMetadata.doc_type.ilike(f'%{keyword}%'),
                    DocumentMetadata.category.ilike(f'%{keyword}%')
                ])

            results = db.query(DocumentMetadata)\
                .filter(or_(*conditions))\
                .filter(or_(
                    DocumentMetadata.status == "0",
                    DocumentMetadata.status == ""
                ))\
                .limit(limit * 2)\
                .all()

            logger.info(f"✅ [FALLBACK] Found {len(results)} metadata records")
            return results[:limit]

        except Exception as e:
            logger.error(f"❌ [FALLBACK METADATA ERROR]: {str(e)}")
            return []

    async def get_documents_by_metadata(
        self,
        db: Session,
        metadata_list: List[DocumentMetadata],
        language: str
    ) -> List[Dict]:
        """
        Get full documents matching metadata links.
        Tries multiple matching strategies.

        Args:
            db: Database session
            metadata_list: List of metadata objects
            language: 'ru' or 'uz'

        Returns:
            List of documents with metadata and content
        """
        try:
            model_class = RussianDocument if language == 'ru' else UzbekDocument
            table_name = 'ru_documents' if language == 'ru' else 'uz_documents'

            logger.info(f"🔗 [MATCHING] Trying to match {len(metadata_list)} metadata with {table_name}")

            documents = []
            for meta in metadata_list:
                # Extract doc ID from link
                doc_id = meta.get_doc_id_from_link(language)

                if not doc_id:
                    logger.warning(f"⚠️ [MATCHING] No doc_id found for: {meta.title}")
                    continue

                # Strategy 1: Match by doc_id in title (e.g., "-7630588.doc")
                doc = db.query(model_class)\
                    .filter(model_class.title.ilike(f'%{doc_id}%'))\
                    .first()

                if doc:
                    logger.info(f"✅ [MATCH] Found document in {table_name}: {doc.title}")
                    documents.append({
                        'metadata': {
                            'title': meta.title,
                            'doc_type': meta.doc_type,
                            'number': meta.number,
                            'date': str(meta.registration_date) if meta.registration_date else None,
                            'status': meta.status,
                            'category': meta.category,
                            'link_rus': meta.link_rus,
                            'link_uz_latin': meta.link_uz_latin,
                            'link_uz_cyrillic': meta.link_uz_cyrillic
                        },
                        'content': doc.content[:3000],
                        'source_table': table_name,
                        'document_id': doc.id
                    })
                else:
                    logger.warning(f"⚠️ [NO MATCH] No document found in {table_name} for doc_id: {doc_id}")

            logger.info(f"✅ [MATCHING] Successfully matched {len(documents)}/{len(metadata_list)} documents")
            return documents

        except Exception as e:
            logger.error(f"❌ [MATCHING ERROR]: {str(e)}")
            return []

    async def chat(
        self,
        db: Session,
        user_message: str,
        conversation_history: List[Dict[str, str]] = None
    ) -> Dict:
        """
        TWO-STAGE AI PROCESS:
        Stage 1: AI extracts search keywords (no user response)
        Stage 2: Search documents + AI generates response with context

        Args:
            db: Database session
            user_message: User's message
            conversation_history: Previous conversation (optional)

        Returns:
            Dict with response and metadata
        """
        try:
            # Detect language
            language = self.ai_service.detect_language(user_message)
            logger.info(f"🌍 [LANGUAGE] Detected: {language}")

            # STAGE 1: AI extracts search keywords (FIRST AI CALL)
            logger.info("🤖 [STAGE 1] AI extracting search keywords...")
            search_data = await self.ai_service.extract_search_keywords(user_message, language)

            keywords = search_data.get('keywords', [])
            document_numbers = search_data.get('document_numbers', [])
            categories = search_data.get('categories', [])
            intent = search_data.get('intent', '')

            logger.info(f"📊 [STAGE 1 RESULT] Intent: {intent}")
            logger.info(f"  Keywords: {keywords}")
            logger.info(f"  Doc numbers: {document_numbers}")

            # SEARCH PHASE: Use extracted keywords to search
            all_documents = []

            # Search 1: Search in document content directly (ru_documents/uz_documents)
            logger.info("📚 [SEARCH PHASE] Searching document content...")
            content_docs = await self.search_documents_fulltext(
                db, keywords + document_numbers, language, limit=5
            )
            all_documents.extend(content_docs)

            # Search 2: Search metadata and match with documents
            logger.info("📋 [SEARCH PHASE] Searching metadata...")
            metadata_results = await self.search_metadata_fulltext(
                db, keywords, document_numbers, limit=3
            )

            if metadata_results:
                matched_docs = await self.get_documents_by_metadata(db, metadata_results, language)
                all_documents.extend(matched_docs)

            # Remove duplicates by document_id
            seen_ids = set()
            unique_docs = []
            for doc in all_documents:
                doc_id = doc.get('document_id') or doc.get('id')
                if doc_id not in seen_ids:
                    seen_ids.add(doc_id)
                    unique_docs.append(doc)

            logger.info(f"📑 [SEARCH RESULT] Total unique documents found: {len(unique_docs)}")

            # STAGE 2: AI generates response with context (SECOND AI CALL)
            logger.info("🤖 [STAGE 2] AI generating response with context...")

            context_text = self._build_context(unique_docs, language)
            system_message = self._get_system_message(language)

            messages = [
                {"role": "system", "content": system_message}
            ]

            # Add conversation history if provided
            if conversation_history:
                messages.extend(conversation_history[-4:])

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

            # Get AI response
            response = await self.ai_service.chat_completion(
                messages=messages,
                temperature=0.7,
                max_tokens=1500
            )

            # Determine source
            source = "dataset" if len(unique_docs) > 0 else "ai_knowledge"
            logger.info(f"✅ [COMPLETE] Response source: {source}")

            # Extract metadata for response
            metadata_for_response = []
            for doc in unique_docs[:5]:  # Top 5 documents
                if 'metadata' in doc:
                    metadata_for_response.append(doc['metadata'])
                else:
                    # Document from content search
                    metadata_for_response.append({
                        'title': doc.get('title', ''),
                        'source_table': doc.get('source_table', ''),
                        'document_id': doc.get('id')
                    })

            return {
                'response': response,
                'language': language,
                'source': source,
                'documents_found': len(unique_docs),
                'metadata': metadata_for_response,
                'search_info': {
                    'keywords': keywords,
                    'document_numbers': document_numbers,
                    'intent': intent
                }
            }

        except Exception as e:
            logger.error(f"❌ [CHAT ERROR]: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())

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
        for idx, doc in enumerate(documents[:5], 1):  # Top 5 documents
            if 'metadata' in doc:
                # Document with metadata
                meta = doc['metadata']
                link = meta.get('link_rus') if language == 'ru' else meta.get('link_uz_latin')

                context_parts.append(
                    f"Документ {idx} (из таблицы metadata):\n"
                    f"Название: {meta['title']}\n"
                    f"Тип: {meta['doc_type']}\n"
                    f"Номер: {meta['number']}\n"
                    f"Дата: {meta['date']}\n"
                    f"Ссылка: {link}\n"
                    f"Содержание: {doc['content'][:1500]}...\n"
                )
            else:
                # Document from direct content search
                context_parts.append(
                    f"Документ {idx} (из таблицы {doc.get('source_table', 'unknown')}):\n"
                    f"Файл: {doc.get('title', 'unknown')}\n"
                    f"Содержание: {doc.get('content', '')[:1500]}...\n"
                )

        return "\n---\n".join(context_parts)

    def _get_system_message(self, language: str) -> str:
        """Get system message for AI based on language"""
        if language == 'ru':
            return """Вы - помощник по правовым вопросам Узбекистана.
Ваша задача - отвечать на вопросы пользователей о законах и нормативных актах.
Используйте предоставленный контекст документов для точных ответов.
Отвечайте кратко, но полно. Если информации недостаточно, так и скажите.
Всегда указывайте источник информации (название документа, ссылку если есть)."""
        else:
            return """Siz O'zbekiston huquqiy masalalari bo'yicha yordamchisiz.
Sizning vazifangiz - foydalanuvchilarning qonunlar va me'yoriy hujjatlar haqidagi savollariga javob berish.
Aniq javoblar uchun taqdim etilgan hujjatlar kontekstidan foydalaning.
Qisqa, lekin to'liq javob bering. Agar ma'lumot yetarli bo'lmasa, shunday ayting.
Har doim ma'lumot manbasini (hujjat nomi, havola) ko'rsating."""
