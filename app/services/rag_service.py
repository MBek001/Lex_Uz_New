"""
Fixed RAG system to use dataset instead of AI knowledge
Workflow: User message → Search metadata → Get documents → AI response with links
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
    """Simple, reliable RAG service focused on using metadata + documents"""

    def __init__(self):
        self.ai_service = AIService()

    async def search_metadata(
        self,
        db: Session,
        user_message: str,
        language: str,
        limit: int = 5
    ) -> List[DocumentMetadata]:
        """
        Search metadata table based on user message.
        Extract keywords and search in title, doc_type, category, number.

        Args:
            db: Database session
            user_message: User's question
            language: 'ru' or 'uz'
            limit: Max results

        Returns:
            List of DocumentMetadata objects
        """
        try:
            # Extract simple keywords (words longer than 2 chars)
            words = re.findall(r'\w+', user_message.lower())
            keywords = [w for w in words if len(w) > 2][:10]  # Top 10 keywords

            # Extract numbers (potential document numbers)
            numbers = re.findall(r'\b\d+\b', user_message)

            logger.info(f"🔍 [METADATA SEARCH] Keywords: {keywords[:5]}, Numbers: {numbers}")

            # Build search conditions
            conditions = []

            # Search by keywords in title, doc_type, category
            for keyword in keywords[:5]:  # Limit to 5 keywords
                conditions.append(DocumentMetadata.title.ilike(f'%{keyword}%'))
                conditions.append(DocumentMetadata.doc_type.ilike(f'%{keyword}%'))
                if DocumentMetadata.category:
                    conditions.append(DocumentMetadata.category.ilike(f'%{keyword}%'))

            # Search by document numbers
            for num in numbers[:3]:  # Limit to 3 numbers
                conditions.append(DocumentMetadata.number.ilike(f'%{num}%'))

            if not conditions:
                logger.warning("⚠️ [METADATA SEARCH] No search conditions, returning empty")
                return []

            # Execute search
            results = db.query(DocumentMetadata)\
                .filter(or_(*conditions))\
                .filter(or_(
                    DocumentMetadata.status == "0",
                    DocumentMetadata.status == ""
                ))\
                .limit(limit * 2)\
                .all()

            # Score and rank results with improved prioritization
            scored_results = []
            for doc in results:
                score = 0
                doc_number = (doc.number or '').lower()
                doc_title = doc.title.lower()
                doc_type = doc.doc_type.lower()
                doc_category = (doc.category or '').lower()

                # PRIORITY 1: Exact number matches (HIGHEST PRIORITY)
                for num in numbers:
                    # Exact match in number field
                    if doc_number == num.lower():
                        score += 100
                        logger.info(f"   🎯 EXACT NUMBER MATCH: {doc.number} = {num}")
                    # Number field contains the searched number
                    elif num in doc_number:
                        score += 50
                        logger.info(f"   ✓ Number contains: {num} in {doc.number}")
                    # Number appears in title
                    elif num in doc_title:
                        score += 10

                # PRIORITY 2: Keyword matches in different fields
                for keyword in keywords:
                    # Title match (important)
                    if keyword in doc_title:
                        score += 5
                    # Doc type match
                    if keyword in doc_type:
                        score += 3
                    # Category match
                    if keyword in doc_category:
                        score += 2

                if score > 0:
                    scored_results.append((score, doc))
                    logger.debug(f"   Document scored {score}: {doc.title[:50]}... (Number: {doc.number})")

            # Sort by score (highest first) and return top results
            scored_results.sort(reverse=True, key=lambda x: x[0])
            final_results = [doc for score, doc in scored_results[:limit]]

            # Log top results with scores
            logger.info(f"✅ [METADATA] Found {len(final_results)} documents")
            for idx, (score, doc) in enumerate(scored_results[:limit], 1):
                logger.info(f"   #{idx} Score={score}: {doc.title[:60]}... (№{doc.number})")

            return final_results

        except Exception as e:
            logger.error(f"❌ [METADATA ERROR]: {str(e)}")
            db.rollback()  # IMPORTANT: Rollback transaction on error
            return []

    async def get_documents_from_metadata(
        self,
        db: Session,
        metadata_list: List[DocumentMetadata],
        language: str
    ) -> List[Dict]:
        """
        Get full document content from ru_documents/uz_documents tables
        by matching document IDs from metadata links.

        Args:
            db: Database session
            metadata_list: List of metadata objects
            language: 'ru' or 'uz'

        Returns:
            List of dicts with metadata + content
        """
        try:
            model_class = RussianDocument if language == 'ru' else UzbekDocument
            table_name = 'ru_documents' if language == 'ru' else 'uz_documents'

            logger.info(f"🔗 [DOCUMENT MATCHING] Matching {len(metadata_list)} metadata with {table_name}")

            documents = []
            for meta in metadata_list:
                # Extract document ID from link
                doc_id = meta.get_doc_id_from_link(language)

                if not doc_id:
                    logger.warning(f"⚠️ [NO DOC_ID] Could not extract doc_id from: {meta.link_rus or meta.link_uz_latin}")
                    continue

                # Search for document with this ID in title
                # Document titles are like "-7630588.doc" or "7630588.doc"
                doc = db.query(model_class)\
                    .filter(model_class.title.ilike(f'%{doc_id}%'))\
                    .first()

                if doc:
                    logger.info(f"✅ [MATCHED] {meta.title} → {doc.title}")

                    # Choose appropriate link based on language
                    link = meta.link_rus if language == 'ru' else (meta.link_uz_latin or meta.link_uz_cyrillic)

                    documents.append({
                        'title': meta.title,
                        'doc_type': meta.doc_type,
                        'number': meta.number,
                        'date': str(meta.registration_date) if meta.registration_date else None,
                        'category': meta.category,
                        'link': link,
                        'content': doc.content[:2000],  # First 2000 chars
                        'doc_filename': doc.title
                    })
                else:
                    logger.warning(f"⚠️ [NOT FOUND] No document in {table_name} for doc_id: {doc_id}")

            logger.info(f"✅ [DOCUMENT MATCHING] Matched {len(documents)}/{len(metadata_list)} documents")
            return documents

        except Exception as e:
            logger.error(f"❌ [DOCUMENT MATCHING ERROR]: {str(e)}")
            db.rollback()  # IMPORTANT: Rollback transaction on error
            return []

    async def chat(
        self,
        db: Session,
        user_message: str,
        conversation_history: List[Dict[str, str]] = None
    ) -> Dict:
        """
        Main chat function with RAG.

        Workflow:
        1. Detect language
        2. Search metadata table
        3. Get full documents from ru_documents/uz_documents
        4. Build context with ALL information (metadata + content + links)
        5. AI generates response with MANDATORY links
        6. Return response with source indicator

        Args:
            db: Database session
            user_message: User's question
            conversation_history: Previous messages (optional)

        Returns:
            Dict with response, source, documents, links
        """
        try:
            # Step 1: Detect language
            language = self.ai_service.detect_language(user_message)
            logger.info(f"🌍 [LANGUAGE] Detected: {language}")

            # Step 2: Search metadata
            logger.info("📋 [STEP 2] Searching metadata table...")
            metadata_results = await self.search_metadata(db, user_message, language, limit=5)

            # Step 3: Get full documents
            logger.info("📄 [STEP 3] Getting full documents from ru/uz tables...")
            documents = await self.get_documents_from_metadata(db, metadata_results, language)

            # Step 4: Build context
            logger.info(f"📝 [STEP 4] Building context with {len(documents)} documents...")
            context_text = self._build_context_with_links(documents, language)

            # Step 5: Prepare messages for AI
            system_message = self._get_system_message_with_mandatory_links(language, len(documents) > 0)

            messages = [
                {"role": "system", "content": system_message}
            ]

            # Add conversation history
            if conversation_history:
                messages.extend(conversation_history[-4:])

            # Add context and user question
            if context_text:
                if language == 'ru':
                    messages.append({
                        "role": "user",
                        "content": f"ДОКУМЕНТЫ ИЗ БАЗЫ ДАННЫХ:\n{context_text}\n\nВОПРОС ПОЛЬЗОВАТЕЛЯ: {user_message}"
                    })
                else:
                    messages.append({
                        "role": "user",
                        "content": f"MA'LUMOTLAR BAZASIDAGI HUJJATLAR:\n{context_text}\n\nFOYDALANUVCHI SAVOLI: {user_message}"
                    })
            else:
                messages.append({
                    "role": "user",
                    "content": user_message
                })

            # Step 6: Get AI response
            logger.info("🤖 [STEP 6] Getting AI response...")
            response = await self.ai_service.chat_completion(
                messages=messages,
                temperature=0.7,
                max_tokens=2000
            )

            # Determine source
            source = "dataset" if len(documents) > 0 else "ai_knowledge"

            # Extract metadata for response
            metadata_list = []
            for doc in documents:
                metadata_list.append({
                    'title': doc['title'],
                    'doc_type': doc['doc_type'],
                    'number': doc['number'],
                    'date': doc['date'],
                    'category': doc['category'],
                    'link': doc['link'],
                    'filename': doc['doc_filename']
                })

            logger.info(f"✅ [COMPLETE] Source: {source}, Documents: {len(documents)}")

            return {
                'response': response,
                'language': language,
                'source': source,
                'documents_found': len(documents),
                'metadata': metadata_list
            }

        except Exception as e:
            logger.error(f"❌ [CHAT ERROR]: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            db.rollback()  # IMPORTANT: Rollback transaction on error

            return {
                'response': "Извините, произошла ошибка при обработке вашего запроса." if language == 'ru'
                           else "Kechirasiz, so'rovingizni qayta ishlashda xatolik yuz berdi.",
                'source': 'error',
                'documents_found': 0,
                'metadata': [],
                'error': str(e)
            }

    def _build_context_with_links(self, documents: List[Dict], language: str) -> str:
        """
        Build context text with ALL information for AI.
        Include metadata, content, and LINKS.
        """
        if not documents:
            return ""

        context_parts = []
        for idx, doc in enumerate(documents, 1):
            if language == 'ru':
                context_parts.append(
                    f"═══ ДОКУМЕНТ {idx} ═══\n"
                    f"Название: {doc['title']}\n"
                    f"Тип: {doc['doc_type']}\n"
                    f"Номер: {doc['number']}\n"
                    f"Дата: {doc['date']}\n"
                    f"Категория: {doc['category']}\n"
                    f"ССЫЛКА: {doc['link']}\n"
                    f"Файл: {doc['doc_filename']}\n"
                    f"\nТЕКСТ ДОКУМЕНТА:\n{doc['content']}\n"
                )
            else:
                context_parts.append(
                    f"═══ HUJJAT {idx} ═══\n"
                    f"Nomi: {doc['title']}\n"
                    f"Turi: {doc['doc_type']}\n"
                    f"Raqami: {doc['number']}\n"
                    f"Sanasi: {doc['date']}\n"
                    f"Kategoriya: {doc['category']}\n"
                    f"HAVOLA: {doc['link']}\n"
                    f"Fayl: {doc['doc_filename']}\n"
                    f"\nHUJJAT MATNI:\n{doc['content']}\n"
                )

        return "\n\n".join(context_parts)

    def _get_system_message_with_mandatory_links(self, language: str, has_documents: bool) -> str:
        """
        Get system message that FORCES AI to include links when documents are found.
        """
        if language == 'ru':
            if has_documents:
                return """Вы - помощник по правовым вопросам Узбекистана, работающий с базой данных документов.

КРИТИЧЕСКИ ВАЖНО:
1. Вам предоставлены РЕАЛЬНЫЕ ДОКУМЕНТЫ из базы данных с их ССЫЛКАМИ
2. Вы ОБЯЗАНЫ использовать ТОЛЬКО информацию из этих документов
3. Вы ОБЯЗАНЫ включить в ответ ССЫЛКИ на все использованные документы
4. Формат ссылки: "Источник: [Название документа](https://lex.uz/...)" или "Подробнее: https://lex.uz/..."

ИНСТРУКЦИЯ:
- Отвечайте на основе предоставленных документов
- В конце ответа ОБЯЗАТЕЛЬНО добавьте раздел "📎 Источники:" со ссылками
- Если документ упоминается в ответе, ОБЯЗАТЕЛЬНО укажите его ссылку
- Будьте точны и используйте только факты из документов"""
            else:
                return """Вы - помощник по правовым вопросам Узбекистана.

К сожалению, в базе данных не найдены документы по этому запросу.
Вы можете дать общий ответ на основе ваших знаний, но ОБЯЗАТЕЛЬНО сообщите пользователю,
что это общая информация и нет конкретных документов в базе данных."""
        else:  # Uzbek
            if has_documents:
                return """Siz O'zbekiston huquqiy masalalari bo'yicha yordamchisiz va hujjatlar bazasi bilan ishlaysiz.

JUDA MUHIM:
1. Sizga ma'lumotlar bazasidan HAQIQIY HUJJATLAR va ularning HAVOLALARI berilgan
2. Siz FAQAT shu hujjatlardan foydalanishingiz SHART
3. Javobga ishlatilgan barcha hujjatlarning HAVOLARINI kiritishingiz MAJBURIY
4. Havola formati: "Manba: [Hujjat nomi](https://lex.uz/...)" yoki "Batafsil: https://lex.uz/..."

KO'RSATMA:
- Berilgan hujjatlarga asoslangan javob bering
- Javob oxirida ALBATTA "📎 Manbalar:" bo'limini qo'shing va havolalarni ko'rsating
- Agar javobda hujjat tilga olinsa, uning havolasini ALBATTA ko'rsating
- Aniq bo'ling va faqat hujjatlardagi faktlardan foydalaning"""
            else:
                return """Siz O'zbekiston huquqiy masalalari bo'yicha yordamchisiz.

Afsuski, ma'lumotlar bazasida ushbu so'rov bo'yicha hujjatlar topilmadi.
Siz o'z bilimlaringizga asoslangan umumiy javob berishingiz mumkin, lekin foydalanuvchiga
bu umumiy ma'lumot ekanligini va ma'lumotlar bazasida aniq hujjatlar yo'qligini ALBATTA ayting."""
