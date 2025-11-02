"""
Main FastAPI application for bulk document import system.
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.routers import upload
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
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
