"""
Database service for batch operations on documents.
"""
from typing import List, Dict, Type
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging

from app.models.documents import RussianDocument, UzbekDocument

logger = logging.getLogger(__name__)


class DatabaseService:
    """Service for efficient database operations"""

    BATCH_SIZE = 1000  # Insert 1000 records at a time

    @staticmethod
    def batch_insert_documents(
        db: Session,
        documents: List[Dict[str, any]],
        model_class: Type,
        batch_size: int = BATCH_SIZE
    ) -> Dict[str, any]:
        """
        Insert documents in batches for better performance.

        Args:
            db: Database session
            documents: List of document dictionaries
            model_class: Model class (RussianDocument or UzbekDocument)
            batch_size: Number of records per batch

        Returns:
            Dictionary with statistics
        """
        total = len(documents)
        inserted = 0
        errors = 0
        error_details = []

        logger.info(f"Starting batch insert of {total} documents")

        try:
            for i in range(0, total, batch_size):
                batch = documents[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (total + batch_size - 1) // batch_size

                try:
                    # Create model instances
                    instances = [
                        model_class(
                            title=doc['title'],
                            content=doc['content'],
                            file_size=doc.get('file_size')
                        )
                        for doc in batch
                    ]

                    # Bulk insert
                    db.bulk_save_objects(instances)
                    db.commit()

                    inserted += len(batch)
                    logger.info(f"Batch {batch_num}/{total_batches} inserted successfully ({len(batch)} records)")

                except SQLAlchemyError as e:
                    db.rollback()
                    errors += len(batch)
                    error_msg = f"Batch {batch_num} failed: {str(e)}"
                    logger.error(error_msg)
                    error_details.append(error_msg)

                    # Try inserting records one by one in this batch
                    logger.info(f"Attempting individual inserts for batch {batch_num}")
                    for doc in batch:
                        try:
                            instance = model_class(
                                title=doc['title'],
                                content=doc['content'],
                                file_size=doc.get('file_size')
                            )
                            db.add(instance)
                            db.commit()
                            inserted += 1
                            errors -= 1
                        except SQLAlchemyError as e:
                            db.rollback()
                            error_details.append(f"Failed to insert {doc['title']}: {str(e)}")
                            logger.error(f"Failed to insert {doc['title']}: {str(e)}")

        except Exception as e:
            logger.error(f"Unexpected error during batch insert: {str(e)}")
            error_details.append(f"Unexpected error: {str(e)}")

        result = {
            'total': total,
            'inserted': inserted,
            'errors': errors,
            'error_details': error_details[:50]  # Limit to first 50 errors
        }

        logger.info(f"Batch insert completed: {inserted}/{total} inserted, {errors} errors")
        return result

    @staticmethod
    def get_document_count(db: Session, model_class: Type) -> int:
        """Get total count of documents in table"""
        try:
            return db.query(model_class).count()
        except SQLAlchemyError as e:
            logger.error(f"Error counting documents: {str(e)}")
            return 0

    @staticmethod
    def get_latest_documents(
        db: Session,
        model_class: Type,
        limit: int = 10
    ) -> List:
        """Get latest documents"""
        try:
            return db.query(model_class)\
                .order_by(model_class.created_at.desc())\
                .limit(limit)\
                .all()
        except SQLAlchemyError as e:
            logger.error(f"Error fetching latest documents: {str(e)}")
            return []

    @staticmethod
    def search_documents(
        db: Session,
        model_class: Type,
        search_term: str,
        limit: int = 100
    ) -> List:
        """Search documents by title or content"""
        try:
            return db.query(model_class)\
                .filter(
                    (model_class.title.ilike(f'%{search_term}%')) |
                    (model_class.content.ilike(f'%{search_term}%'))
                )\
                .limit(limit)\
                .all()
        except SQLAlchemyError as e:
            logger.error(f"Error searching documents: {str(e)}")
            return []
