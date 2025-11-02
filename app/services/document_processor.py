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
    import docx2txt
    DOCX2TXT_AVAILABLE = True
except ImportError:
    DOCX2TXT_AVAILABLE = False

try:
    import olefile
    OLEFILE_AVAILABLE = True
except ImportError:
    OLEFILE_AVAILABLE = False

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Processes document files and extracts text content"""

    SUPPORTED_EXTENSIONS = {'.doc', '.docx'}
    BATCH_SIZE = 1000  # Number of records to insert at once

    def __init__(self):
        self.processed_count = 0
        self.error_count = 0
        self.errors = []
        self.antiword_checked = False
        self.antiword_available = False

    def extract_text_from_docx(self, file_path: str) -> Optional[str]:
        """
        Extract text from DOCX file using python-docx or docx2txt.

        Args:
            file_path: Path to the DOCX file

        Returns:
            Extracted text or None if extraction fails
        """
        # Try python-docx first (more reliable)
        if DocxDocument is not None:
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
                logger.warning(f"python-docx failed, trying docx2txt: {str(e)}")

        # Fallback to docx2txt
        if DOCX2TXT_AVAILABLE:
            try:
                text = docx2txt.process(file_path)
                if text and text.strip():
                    return text.strip()
            except Exception as e:
                logger.error(f"Error extracting text with docx2txt from {file_path}: {str(e)}")

        logger.error("No DOCX extraction library available")
        return None

    def extract_text_from_doc(self, file_path: str) -> Optional[str]:
        """
        Extract text from DOC file using antiword or olefile (fast methods only).
        AGGRESSIVE MODE: Extract ANY text, even partial.

        Args:
            file_path: Path to the DOC file

        Returns:
            Extracted text or None if extraction fails
        """
        import subprocess

        # Check antiword availability once
        if not self.antiword_checked:
            try:
                subprocess.run(['antiword', '--version'], capture_output=True, timeout=1)
                self.antiword_available = True
                logger.info("✅ antiword detected - DOC files will be processed faster!")
            except:
                self.antiword_available = False
                logger.warning("⚠️  antiword not installed - DOC processing will be limited. Install with: sudo apt-get install antiword")
            self.antiword_checked = True

        # Method 1: Try antiword with UTF-8 encoding (for Cyrillic/Uzbek text)
        if self.antiword_available:
            try:
                # Try with UTF-8 encoding first
                result = subprocess.run(
                    ['antiword', '-m', 'UTF-8.txt', file_path],
                    capture_output=True,
                    timeout=5,
                    check=False
                )
                if result.returncode == 0 and result.stdout.strip():
                    text = result.stdout.decode('utf-8', errors='ignore') if isinstance(result.stdout, bytes) else result.stdout
                    if text.strip():
                        return text

                # Try without encoding specification
                result = subprocess.run(
                    ['antiword', file_path],
                    capture_output=True,
                    timeout=5,
                    check=False
                )
                if result.stdout:
                    text = result.stdout.decode('utf-8', errors='ignore') if isinstance(result.stdout, bytes) else result.stdout
                    if text.strip():
                        return text

            except Exception as e:
                logger.debug(f"antiword failed: {str(e)}")

        # Method 2: Try olefile for AGGRESSIVE text extraction
        if OLEFILE_AVAILABLE:
            try:
                import olefile
                if olefile.isOleFile(file_path):
                    ole = olefile.OleFileIO(file_path)
                    extracted_text = []

                    # Try multiple streams
                    for stream_name in ['WordDocument', '1Table', '0Table', 'Data']:
                        try:
                            if ole.exists(stream_name):
                                stream = ole.openstream(stream_name)
                                data = stream.read()

                                # Try UTF-8 decoding
                                try:
                                    text = data.decode('utf-8', errors='ignore')
                                    extracted_text.append(text)
                                except:
                                    pass

                                # Try extracting printable characters (ASCII + extended)
                                text = ''.join(chr(b) if 32 <= b < 256 and b != 127 else ' ' for b in data)
                                extracted_text.append(text)
                        except:
                            pass

                    ole.close()

                    # Combine all extracted text
                    combined = ' '.join(extracted_text)
                    combined = ' '.join(combined.split())  # Clean whitespace

                    # VERY AGGRESSIVE: Accept ANY text > 10 characters
                    if len(combined) > 10:
                        return combined

            except Exception as e:
                logger.debug(f"olefile extraction failed: {str(e)}")

        # Method 3: LAST RESORT - Raw bytes extraction
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
                # Try UTF-8 decoding
                try:
                    text = data.decode('utf-8', errors='ignore')
                    # Clean and check
                    text = ' '.join(text.split())
                    if len(text) > 20:
                        return text
                except:
                    pass

                # Try Windows-1251 (Cyrillic)
                try:
                    text = data.decode('windows-1251', errors='ignore')
                    text = ' '.join(text.split())
                    if len(text) > 20:
                        return text
                except:
                    pass
        except:
            pass

        # If all methods fail, return None
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
                            # Count error but don't spam logs
                            self.error_count += 1
                            if self.error_count <= 10:  # Only log first 10 errors
                                logger.warning(f"No content extracted from: {file_name}")
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
