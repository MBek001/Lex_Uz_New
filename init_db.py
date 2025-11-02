#!/usr/bin/env python3
"""
Database initialization script.
Run this to create tables if needed.
"""
from app.config.database import init_db, engine
from app.models.documents import Base
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Initialize database tables"""
    try:
        logger.info("Creating database tables...")
        init_db()

        # Verify tables were created
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        logger.info(f"Tables created: {tables}")

        if 'ru_documents' in tables and 'uz_documents' in tables:
            logger.info("✅ Database initialized successfully!")
        else:
            logger.warning("⚠️ Some tables may be missing")

    except Exception as e:
        logger.error(f"❌ Error initializing database: {str(e)}")
        raise


if __name__ == "__main__":
    main()
