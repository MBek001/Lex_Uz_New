"""
Main FastAPI application for bulk document import system.
"""
import logging
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import uvicorn

from app.routers import upload, metadata, chat
from app.config.database import init_db, get_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Lex Uz Bulk Document Import API",
    description="API for importing large batches of Russian and Uzbek documents into PostgreSQL",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router)
app.include_router(metadata.router)
app.include_router(chat.router)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        logger.info("Initializing database...")
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Lex Uz Bulk Document Import API",
        "version": "1.0.0",
        "endpoints": {
            "upload_russian": "/api/upload/russian",
            "upload_uzbek": "/api/upload/uzbek",
            "stats_russian": "/api/stats/russian",
            "stats_uzbek": "/api/stats/uzbek",
            "upload_metadata": "/api/metadata/upload/excel",
            "chat": "/api/chat/message",
            "search_metadata": "/api/metadata/search",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.post("/api/debug/search")
async def debug_search(request: dict, db: Session = Depends(get_db)):
    """
    Debug endpoint to see what keywords are extracted and what would be searched.
    Helps diagnose why searches aren't finding documents.

    POST /api/debug/search
    Body: {"message": "Menga 940-sonli qonun haqida ma'lumot ber"}
    """
    from app.services.rag_service import RAGService
    from app.services.ai_service import AIService
    from app.models.metadata import DocumentMetadata

    try:
        message = request.get('message', '')
        if not message:
            return {"error": "No message provided"}

        # Detect language
        ai_service = AIService()
        language = ai_service.detect_language(message)

        # Extract keywords
        rag_service = RAGService()
        keywords, numbers = rag_service._extract_keywords(message, language)

        # Get sample of what would be searched
        sample_docs = db.query(DocumentMetadata).limit(10).all()

        return {
            "input": {
                "message": message,
                "language": language
            },
            "extracted": {
                "keywords": keywords[:10],
                "numbers": numbers,
                "total_keywords": len(keywords)
            },
            "search_preview": {
                "will_search_for": {
                    "keywords_in_title": keywords[:5],
                    "keywords_in_doc_type": keywords[:5],
                    "numbers_in_number_field": numbers
                },
                "sql_example": f"WHERE (title ILIKE '%{keywords[0]}%' OR doc_type ILIKE '%{keywords[0]}%' OR number ILIKE '%{numbers[0] if numbers else 'N/A'}%' ...)"
            },
            "sample_documents_in_db": [
                {
                    "title": doc.title[:100],
                    "number": doc.number,
                    "doc_type": doc.doc_type,
                    "status": doc.status
                }
                for doc in sample_docs
            ],
            "debugging_tips": [
                f"✓ Extracted {len(keywords)} keywords (stopwords removed)",
                f"✓ Will search in: title, doc_type, category, number fields",
                f"✓ Check if any keywords match the sample documents above",
                "✗ If no matches, your documents may use different terminology",
                "→ Try searching by document number if you know it"
            ]
        }

    except Exception as e:
        logger.error(f"Debug search error: {str(e)}")
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }


@app.get("/api/diagnostics")
async def diagnostics():
    """
    Database diagnostics endpoint to check if data exists.
    Useful for debugging when searches return 0 results.
    """
    from app.config.database import get_db_context
    from app.models.metadata import DocumentMetadata
    from app.models.documents import RussianDocument, UzbekDocument

    try:
        with get_db_context() as db:
            # Count documents
            metadata_count = db.query(DocumentMetadata).count()
            ru_docs_count = db.query(RussianDocument).count()
            uz_docs_count = db.query(UzbekDocument).count()

            # Get sample metadata
            sample_metadata = db.query(DocumentMetadata).limit(3).all()
            sample_metadata_data = [
                {
                    'id': m.id,
                    'title': m.title[:100],
                    'doc_type': m.doc_type,
                    'number': m.number,
                    'status': m.status
                }
                for m in sample_metadata
            ]

            # Count by status
            active_count = db.query(DocumentMetadata)\
                .filter(DocumentMetadata.status == "0")\
                .count()

            return {
                "status": "ok",
                "database": {
                    "metadata_count": metadata_count,
                    "russian_documents": ru_docs_count,
                    "uzbek_documents": uz_docs_count,
                    "active_metadata": active_count,
                    "total_documents": metadata_count + ru_docs_count + uz_docs_count
                },
                "sample_metadata": sample_metadata_data,
                "diagnosis": {
                    "has_metadata": metadata_count > 0,
                    "has_documents": (ru_docs_count + uz_docs_count) > 0,
                    "ready_for_search": metadata_count > 0 and (ru_docs_count + uz_docs_count) > 0
                },
                "instructions": {
                    "upload_metadata": "POST /api/metadata/upload/excel with Excel file",
                    "upload_russian_docs": "POST /api/upload/russian with ZIP file",
                    "upload_uzbek_docs": "POST /api/upload/uzbek with ZIP file"
                }
            }
    except Exception as e:
        logger.error(f"Diagnostics error: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
