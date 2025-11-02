"""
Excel file processor for document metadata
"""
import pandas as pd
from typing import List, Dict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ExcelProcessor:
    """Process Excel files containing document metadata"""

    @staticmethod
    def parse_date(date_str) -> datetime.date:
        """Parse date string in various formats"""
        if pd.isna(date_str):
            return None

        if isinstance(date_str, datetime):
            return date_str.date()

        # Try different date formats
        date_formats = [
            '%d.%m.%Y',
            '%Y-%m-%d',
            '%d/%m/%Y',
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(str(date_str), fmt).date()
            except:
                continue

        return None

    @staticmethod
    def process_excel(file_path: str) -> List[Dict]:
        """
        Process Excel file and return list of document metadata.

        Args:
            file_path: Path to Excel file

        Returns:
            List of dictionaries with document metadata
        """
        try:
            # Read Excel file
            df = pd.read_excel(file_path)

            logger.info(f"Processing Excel file with {len(df)} rows")

            documents = []
            for idx, row in df.iterrows():
                try:
                    doc = {
                        'doc_type': str(row.get('doc_type', '')).strip() if pd.notna(row.get('doc_type')) else '',
                        'registration_date': ExcelProcessor.parse_date(row.get('registration_date')),
                        'number': str(row.get('number', '')).strip() if pd.notna(row.get('number')) else '',
                        'effective_date': ExcelProcessor.parse_date(row.get('effective_date')),
                        'link_rus': str(row.get('link_rus', '')).strip() if pd.notna(row.get('link_rus')) else '',
                        'link_uz_latin': str(row.get('link_uz-latin', '')).strip() if pd.notna(row.get('link_uz-latin')) else '',
                        'link_uz_cyrillic': str(row.get('link_uz-cyrillic', '')).strip() if pd.notna(row.get('link_uz-cyrillic')) else '',
                        'status': str(row.get('status', '')).strip() if pd.notna(row.get('status')) else '',
                        'title': str(row.get('title', '')).strip() if pd.notna(row.get('title')) else '',
                        'category': str(row.get('category', '')).strip() if pd.notna(row.get('category')) else '',
                    }

                    # Only add if title is not empty
                    if doc['title']:
                        documents.append(doc)

                except Exception as e:
                    logger.error(f"Error processing row {idx}: {str(e)}")
                    continue

            logger.info(f"Successfully processed {len(documents)} documents")
            return documents

        except Exception as e:
            logger.error(f"Error processing Excel file: {str(e)}")
            raise
