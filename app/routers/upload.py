"""
API endpoints for uploading and processing document archives.
"""
import os
import tempfile
import shutil
from typing import Dict
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
import logging

from app.config.database import get_db
from app.models.documents import RussianDocument, UzbekDocument
from app.services.document_processor import DocumentProcessor
from app.services.database_service import DatabaseService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["upload"])


async def process_upload_in_background(
    file_path: str,
    model_class,
    db: Session
) -> Dict:
    """
    Background task to process uploaded file.

    Args:
        file_path: Path to uploaded ZIP file
        model_class: Database model class
        db: Database session

    Returns:
        Processing results
    """
    temp_dir = None
    try:
        # Create temporary directory for extraction
        temp_dir = tempfile.mkdtemp()

        # Process documents
        processor = DocumentProcessor()
        documents = processor.process_zip_file(file_path, temp_dir)

        # Insert into database
        db_service = DatabaseService()
        db_result = db_service.batch_insert_documents(
            db=db,
            documents=documents,
            model_class=model_class
        )

        # Get processing stats
        proc_stats = processor.get_stats()

        result = {
            'status': 'completed',
            'processing': proc_stats,
            'database': db_result
        }

        logger.info(f"Upload processing completed: {result}")
        return result

    except Exception as e:
        logger.error(f"Error in background processing: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }
    finally:
        # Cleanup
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
        if os.path.exists(file_path):
            os.remove(file_path)


@router.post("/upload/russian")
async def upload_russian_documents(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload ZIP file containing Russian documents.

    The ZIP file should contain .doc or .docx files.
    Each file will be processed and stored in the ru_documents table.

    Args:
        file: ZIP file containing documents
        db: Database session

    Returns:
        Processing results and statistics
    """
    # Validate file
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Only ZIP files are supported")

    temp_file_path = None
    temp_dir = None

    try:
        # Create temporary file for upload
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
            temp_file_path = temp_file.name

            # Stream upload to temp file (memory efficient)
            chunk_size = 1024 * 1024  # 1MB chunks
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                temp_file.write(chunk)

        logger.info(f"File uploaded: {file.filename} ({os.path.getsize(temp_file_path)} bytes)")

        # Create temporary directory for extraction
        temp_dir = tempfile.mkdtemp()

        # Process documents
        processor = DocumentProcessor()
        documents = processor.process_zip_file(temp_file_path, temp_dir)

        if not documents:
            raise HTTPException(
                status_code=400,
                detail="No valid documents found in ZIP file"
            )

        # Insert into database
        db_service = DatabaseService()
        db_result = db_service.batch_insert_documents(
            db=db,
            documents=documents,
            model_class=RussianDocument
        )

        # Get processing stats
        proc_stats = processor.get_stats()

        result = {
            'status': 'success',
            'filename': file.filename,
            'processing': proc_stats,
            'database': db_result,
            'total_records_in_db': db_service.get_document_count(db, RussianDocument)
        }

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing upload: {str(e)}")
    finally:
        # Cleanup
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)


@router.post("/upload/uzbek")
async def upload_uzbek_documents(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload ZIP file containing Uzbek documents.

    The ZIP file should contain .doc or .docx files.
    Each file will be processed and stored in the uz_documents table.

    Args:
        file: ZIP file containing documents
        db: Database session

    Returns:
        Processing results and statistics
    """
    # Validate file
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Only ZIP files are supported")

    temp_file_path = None
    temp_dir = None

    try:
        # Create temporary file for upload
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
            temp_file_path = temp_file.name

            # Stream upload to temp file (memory efficient)
            chunk_size = 1024 * 1024  # 1MB chunks
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                temp_file.write(chunk)

        logger.info(f"File uploaded: {file.filename} ({os.path.getsize(temp_file_path)} bytes)")

        # Create temporary directory for extraction
        temp_dir = tempfile.mkdtemp()

        # Process documents
        processor = DocumentProcessor()
        documents = processor.process_zip_file(temp_file_path, temp_dir)

        if not documents:
            raise HTTPException(
                status_code=400,
                detail="No valid documents found in ZIP file"
            )

        # Insert into database
        db_service = DatabaseService()
        db_result = db_service.batch_insert_documents(
            db=db,
            documents=documents,
            model_class=UzbekDocument
        )

        # Get processing stats
        proc_stats = processor.get_stats()

        result = {
            'status': 'success',
            'filename': file.filename,
            'processing': proc_stats,
            'database': db_result,
            'total_records_in_db': db_service.get_document_count(db, UzbekDocument)
        }

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing upload: {str(e)}")
    finally:
        # Cleanup
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)


@router.get("/stats/russian")
async def get_russian_stats(db: Session = Depends(get_db)):
    """Get statistics for Russian documents"""
    db_service = DatabaseService()
    return {
        'total_documents': db_service.get_document_count(db, RussianDocument),
        'latest_documents': [
            {
                'id': doc.id,
                'title': doc.title,
                'created_at': doc.created_at.isoformat(),
                'file_size': doc.file_size
            }
            for doc in db_service.get_latest_documents(db, RussianDocument, limit=10)
        ]
    }


@router.get("/stats/uzbek")
async def get_uzbek_stats(db: Session = Depends(get_db)):
    """Get statistics for Uzbek documents"""
    db_service = DatabaseService()
    return {
        'total_documents': db_service.get_document_count(db, UzbekDocument),
        'latest_documents': [
            {
                'id': doc.id,
                'title': doc.title,
                'created_at': doc.created_at.isoformat(),
                'file_size': doc.file_size
            }
            for doc in db_service.get_latest_documents(db, UzbekDocument, limit=10)
        ]
    }
