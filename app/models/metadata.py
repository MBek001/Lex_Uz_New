"""
Document metadata model for storing Excel data
"""
from sqlalchemy import Column, Integer, String, Text, Date, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import date

Base = declarative_base()


class DocumentMetadata(Base):
    """Model for document metadata from Excel"""
    __tablename__ = 'document_metadata'

    id = Column(Integer, primary_key=True, index=True)

    # Document information
    doc_type = Column(String(500), nullable=False, index=True)  # Указ, Закон, etc.
    registration_date = Column(Date, nullable=True)
    number = Column(String(200), nullable=True, index=True)
    effective_date = Column(Date, nullable=True)

    # Links
    link_rus = Column(String(500), nullable=True, index=True)
    link_uz_latin = Column(String(500), nullable=True)
    link_uz_cyrillic = Column(String(500), nullable=True, index=True)

    # Status and classification
    status = Column(String(500), nullable=True)  # "0", "Акт утратил силу", etc.
    title = Column(Text, nullable=False, index=True)
    category = Column(Text, nullable=True, index=True)

    # Indexes for faster search
    __table_args__ = (
        Index('idx_title_category', 'title', 'category'),
        Index('idx_doc_type_status', 'doc_type', 'status'),
    )

    def get_doc_id_from_link(self, language: str = 'ru') -> str:
        """
        Extract document ID from link based on language.

        Args:
            language: 'ru' or 'uz'

        Returns:
            Document ID (e.g., "7630588" or "-7630445")
        """
        if language == 'uz':
            # Try Cyrillic first, then Latin
            link = self.link_uz_cyrillic or self.link_uz_latin
        else:
            link = self.link_rus

        if not link:
            return None

        # Extract ID from URL: https://lex.uz/ru/docs/7630588 -> 7630588
        # Or: https://lex.uz/ru/docs/-7630445 -> -7630445
        parts = link.rstrip('/').split('/')
        if parts:
            return parts[-1]
        return None
