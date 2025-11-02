"""
Service for processing document files and extracting content.
Handles DOC and DOCX files efficiently.
"""
import os
import tempfile
import zipfile
import gc
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import logging

try:
    from docx import Document as DocxDocument
except ImportError:
    DocxDocument = None

try:
    import win32com.client
    WORD_AVAILABLE = True
except ImportError:
    WORD_AVAILABLE = False

# Alternative: use textract or antiword for .doc files
try:
    import textract
    TEXTRACT_AVAILABLE = True
except ImportError:
    TEXTRACT_AVAILABLE = False

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Processes document files and extracts text content"""

    SUPPORTED_EXTENSIONS = {'.doc', '.docx'}
    BATCH_SIZE = 1000  # Number of records to insert at once

    def __init__(self):
        self.processed_count = 0
        self.error_count = 0
        self.errors = []

    def extract_text_from_docx(self, file_path: str) -> Optional[str]:
        """
        Extract text from DOCX file using python-docx.

        Args:
            file_path: Path to the DOCX file

        Returns:
            Extracted text or None if extraction fails
        """
        if DocxDocument is None:
            logger.error("python-docx not installed")
            return None

        try:
            doc = DocxDocument(file_path)
            full_text = []

            # Extract text from paragraphs
            for para in doc.paragraphs:
                if para.text.strip():
                    full_text.append(para.text)

            # Extract text from tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text.strip():
                            full_text.append(cell.text)

            return '\n'.join(full_text)
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {str(e)}")
            return None

    def extract_text_from_doc(self, file_path: str) -> Optional[str]:
        """
        Extract text from DOC file using textract or antiword.

        Args:
            file_path: Path to the DOC file

        Returns:
            Extracted text or None if extraction fails
        """
        if TEXTRACT_AVAILABLE:
            try:
                text = textract.process(file_path).decode('utf-8', errors='ignore')
                return text
            except Exception as e:
                logger.error(f"Error extracting text with textract from {file_path}: {str(e)}")

        # Fallback: try antiword command if available
        try:
            import subprocess
            result = subprocess.run(
                ['antiword', file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                return result.stdout
        except Exception as e:
            logger.error(f"Error extracting text with antiword from {file_path}: {str(e)}")

        logger.warning(f"Could not extract text from DOC file: {file_path}")
        return None

    def extract_text(self, file_path: str) -> Optional[str]:
        """
        Extract text from document file based on extension.

        Args:
            file_path: Path to the document file

        Returns:
            Extracted text or None if extraction fails
        """
        ext = Path(file_path).suffix.lower()

        if ext == '.docx':
            return self.extract_text_from_docx(file_path)
        elif ext == '.doc':
            return self.extract_text_from_doc(file_path)
        else:
            logger.warning(f"Unsupported file extension: {ext}")
            return None

    def process_zip_file(self, zip_path: str, temp_dir: str) -> List[Dict[str, any]]:
        """
        Process a ZIP file containing documents.
        Extracts files in streaming fashion to handle large archives.

        Args:
            zip_path: Path to the ZIP file
            temp_dir: Temporary directory for extraction

        Returns:
            List of dictionaries with 'title', 'content', and 'file_size'
        """
        documents = []

        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                total_files = len(file_list)

                logger.info(f"Processing {total_files} files from ZIP archive")

                for idx, file_name in enumerate(file_list, 1):
                    # Skip directories and hidden files
                    if file_name.endswith('/') or file_name.startswith('.'):
                        continue

                    # Check file extension
                    ext = Path(file_name).suffix.lower()
                    if ext not in self.SUPPORTED_EXTENSIONS:
                        continue

                    try:
                        # Extract single file to temp location
                        file_info = zip_ref.getinfo(file_name)
                        file_size = file_info.file_size

                        # Create a unique temp file path
                        temp_file_path = os.path.join(temp_dir, f"temp_{idx}{ext}")

                        # Extract the file
                        with zip_ref.open(file_name) as source:
                            with open(temp_file_path, 'wb') as target:
                                target.write(source.read())

                        # Extract text content
                        content = self.extract_text(temp_file_path)

                        if content and content.strip():
                            # Get clean filename without path
                            title = Path(file_name).name

                            documents.append({
                                'title': title,
                                'content': content.strip(),
                                'file_size': file_size
                            })
                            self.processed_count += 1
                        else:
                            logger.warning(f"No content extracted from: {file_name}")
                            self.error_count += 1
                            self.errors.append(f"No content: {file_name}")

                        # Clean up temp file immediately
                        try:
                            os.remove(temp_file_path)
                        except:
                            pass

                        # Progress logging
                        if idx % 100 == 0:
                            logger.info(f"Processed {idx}/{total_files} files ({self.processed_count} successful)")

                        # Force garbage collection every 500 files
                        if idx % 500 == 0:
                            gc.collect()

                    except Exception as e:
                        logger.error(f"Error processing file {file_name}: {str(e)}")
                        self.error_count += 1
                        self.errors.append(f"{file_name}: {str(e)}")
                        continue

                logger.info(f"Completed processing: {self.processed_count} successful, {self.error_count} errors")

        except Exception as e:
            logger.error(f"Error processing ZIP file: {str(e)}")
            raise

        return documents

    def get_stats(self) -> Dict[str, any]:
        """Get processing statistics"""
        return {
            'processed': self.processed_count,
            'errors': self.error_count,
            'error_list': self.errors[:100]  # Return first 100 errors
        }
