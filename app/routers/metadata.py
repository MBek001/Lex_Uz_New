"""
API endpoints for metadata management and Excel upload
"""
import os
import tempfile
from typing import List
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from app.config.database import get_db
from app.models.metadata import DocumentMetadata
from app.services.excel_processor import ExcelProcessor
from app.services.database_service import DatabaseService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/metadata", tags=["metadata"])


@router.post("/upload/excel")
async def upload_excel_metadata(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload Excel file with document metadata.

    Expected columns:
    - doc_type
    - registration_date
    - number
    - effective_date
    - link_rus
    - link_uz-latin
    - link_uz-cyrillic
    - status
    - title
    - category
    """
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are supported")

    temp_file_path = None

    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_file:
            temp_file_path = temp_file.name
            content = await file.read()
            temp_file.write(content)

        logger.info(f"Processing Excel file: {file.filename}")

        # Process Excel file
        excel_processor = ExcelProcessor()
        documents = excel_processor.process_excel(temp_file_path)

        if not documents:
            raise HTTPException(
                status_code=400,
                detail="No valid documents found in Excel file"
            )

        # Insert into database
        inserted = 0
        errors = 0
        error_details = []

        for doc in documents:
            try:
                metadata = DocumentMetadata(**doc)
                db.add(metadata)
                db.commit()
                inserted += 1
            except Exception as e:
                db.rollback()
                errors += 1
                error_details.append(f"{doc.get('title', 'Unknown')}: {str(e)}")
                logger.error(f"Error inserting document: {str(e)}")

        # Get total count
        total_count = db.query(DocumentMetadata).count()

        return {
            'status': 'success',
            'filename': file.filename,
            'processed': len(documents),
            'inserted': inserted,
            'errors': errors,
            'error_details': error_details[:20],  # First 20 errors
            'total_in_database': total_count
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing Excel upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing Excel file: {str(e)}")
    finally:
        # Cleanup
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)


@router.get("/stats")
async def get_metadata_stats(db: Session = Depends(get_db)):
    """Get statistics about document metadata"""
    try:
        total = db.query(DocumentMetadata).count()

        # Count by document type
        from sqlalchemy import func
        by_type = db.query(
            DocumentMetadata.doc_type,
            func.count(DocumentMetadata.id).label('count')
        ).group_by(DocumentMetadata.doc_type).all()

        # Count active vs inactive
        active_count = db.query(DocumentMetadata)\
            .filter(DocumentMetadata.status == "0")\
            .count()

        inactive_count = total - active_count

        # Latest documents
        latest = db.query(DocumentMetadata)\
            .order_by(DocumentMetadata.registration_date.desc())\
            .limit(10)\
            .all()

        return {
            'total_documents': total,
            'active_documents': active_count,
            'inactive_documents': inactive_count,
            'by_type': [{'type': t, 'count': c} for t, c in by_type],
            'latest_documents': [
                {
                    'id': doc.id,
                    'title': doc.title,
                    'doc_type': doc.doc_type,
                    'number': doc.number,
                    'registration_date': str(doc.registration_date) if doc.registration_date else None,
                    'status': doc.status
                }
                for doc in latest
            ]
        }

    except Exception as e:
        logger.error(f"Error getting metadata stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting statistics: {str(e)}")


@router.get("/search")
async def search_metadata(
    query: str,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Search document metadata by title, type, or category"""
    try:
        from sqlalchemy import or_

        results = db.query(DocumentMetadata)\
            .filter(
                or_(
                    DocumentMetadata.title.ilike(f'%{query}%'),
                    DocumentMetadata.doc_type.ilike(f'%{query}%'),
                    DocumentMetadata.category.ilike(f'%{query}%'),
                    DocumentMetadata.number.ilike(f'%{query}%')
                )
            )\
            .limit(limit)\
            .all()

        return {
            'query': query,
            'count': len(results),
            'results': [
                {
                    'id': doc.id,
                    'title': doc.title,
                    'doc_type': doc.doc_type,
                    'number': doc.number,
                    'registration_date': str(doc.registration_date) if doc.registration_date else None,
                    'effective_date': str(doc.effective_date) if doc.effective_date else None,
                    'status': doc.status,
                    'category': doc.category,
                    'link_rus': doc.link_rus,
                    'link_uz_cyrillic': doc.link_uz_cyrillic
                }
                for doc in results
            ]
        }

    except Exception as e:
        logger.error(f"Error searching metadata: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching: {str(e)}")
