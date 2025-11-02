"""
Database models for Russian and Uzbek documents.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class RussianDocument(Base):
    """Model for Russian documents"""
    __tablename__ = 'ru_documents'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    file_size = Column(Integer, nullable=True)  # Size in bytes

    # Composite index for efficient searching
    __table_args__ = (
        Index('idx_ru_title_created', 'title', 'created_at'),
    )


class UzbekDocument(Base):
    """Model for Uzbek documents"""
    __tablename__ = 'uz_documents'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    file_size = Column(Integer, nullable=True)  # Size in bytes

    # Composite index for efficient searching
    __table_args__ = (
        Index('idx_uz_title_created', 'title', 'created_at'),
    )
