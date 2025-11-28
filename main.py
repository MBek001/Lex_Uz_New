"""
Main FastAPI application for bulk document import system.
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.routers import upload, metadata, chat
from app.config.database import init_db

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
