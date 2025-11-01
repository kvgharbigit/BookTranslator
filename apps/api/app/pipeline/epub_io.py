import zipfile
import tempfile
import os
from typing import List, Dict, Tuple
from pathlib import Path

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)


class EPUBProcessor:
    """EPUB reader/writer with validation and security checks."""
    
    def __init__(self):
        self.max_zip_entries = settings.max_zip_entries
        self.max_compression_ratio = settings.max_compression_ratio
    
    def validate_epub_safety(self, epub_path: str) -> bool:
        """Validate EPUB file for security issues."""
        try:
            with zipfile.ZipFile(epub_path, 'r') as zip_file:
                # Check number of entries
                if len(zip_file.infolist()) > self.max_zip_entries:
                    logger.error(f"EPUB has too many entries: {len(zip_file.infolist())}")
                    return False
                
                # Check compression ratio (zip bomb detection)
                total_compressed = 0
                total_uncompressed = 0
                
                for info in zip_file.infolist():
                    total_compressed += info.compress_size
                    total_uncompressed += info.file_size
                
                if total_uncompressed > 0:
                    compression_ratio = total_uncompressed / max(total_compressed, 1)
                    if compression_ratio > self.max_compression_ratio:
                        logger.error(f"Suspicious compression ratio: {compression_ratio}")
                        return False
                
                logger.info(f"EPUB validation passed: {len(zip_file.infolist())} entries")
                return True
                
        except Exception as e:
            logger.error(f"EPUB validation failed: {e}")
            return False
    
    def read_epub(self, epub_path: str) -> Tuple[epub.EpubBook, List[Dict]]:
        """Read EPUB and extract spine documents."""
        
        # Validate safety first
        if not self.validate_epub_safety(epub_path):
            raise ValueError("EPUB failed security validation")
        
        try:
            book = epub.read_epub(epub_path)
            spine_docs = []
            
            # Extract spine documents in order
            for item_id, linear in book.spine:
                if isinstance(item_id, tuple):
                    item_id = item_id[0]
                
                item = book.get_item_with_id(item_id)
                if item and item.get_type() == ebooklib.ITEM_DOCUMENT:
                    content = item.get_content().decode('utf-8', errors='ignore')
                    
                    # Sanitize content
                    content = self._sanitize_xhtml(content)
                    
                    spine_docs.append({
                        'id': item_id,
                        'href': item.get_name(),
                        'content': content,
                        'title': getattr(item, 'title', item_id)
                    })
            
            logger.info(f"Read EPUB with {len(spine_docs)} spine documents")
            return book, spine_docs
            
        except Exception as e:
            logger.error(f"Failed to read EPUB: {e}")
            raise
    
    def _sanitize_xhtml(self, content: str) -> str:
        """Sanitize XHTML content for security."""
        try:
            # Parse with BeautifulSoup
            soup = BeautifulSoup(content, 'xml')
            
            # Remove script tags and event handlers
            for script in soup.find_all('script'):
                script.decompose()
            
            # Remove event attributes (onclick, onload, etc.)
            for tag in soup.find_all():
                attrs_to_remove = [attr for attr in tag.attrs if attr.startswith('on')]
                for attr in attrs_to_remove:
                    del tag[attr]
            
            # Ensure UTF-8 encoding
            return str(soup)
            
        except Exception as e:
            logger.warning(f"Failed to sanitize XHTML, using original: {e}")
            return content
    
    def write_epub(
        self, 
        original_book: epub.EpubBook, 
        translated_docs: List[Dict], 
        output_path: str
    ) -> bool:
        """Write translated EPUB preserving structure and assets."""
        
        try:
            # Create new book with same metadata
            new_book = epub.EpubBook()
            
            # Copy metadata
            new_book.set_identifier(original_book.get_metadata('DC', 'identifier')[0][0])
            new_book.set_title(original_book.get_metadata('DC', 'title')[0][0])
            new_book.set_language(original_book.get_metadata('DC', 'language')[0][0])
            
            # Copy authors
            for author in original_book.get_metadata('DC', 'creator'):
                new_book.add_author(author[0])
            
            # Copy all non-document items (CSS, images, fonts, etc.)
            for item in original_book.get_items():
                if item.get_type() != ebooklib.ITEM_DOCUMENT:
                    new_book.add_item(item)
            
            # Add translated documents
            spine = []
            for doc in translated_docs:
                # Create new EPUB item
                chapter = epub.EpubHtml(
                    title=doc['title'] or f"Chapter {len(spine)+1}",
                    file_name=doc['href'],
                    lang='es'  # Set to target language
                )
                
                # Ensure content is properly encoded
                content = doc['content']
                if isinstance(content, str):
                    chapter.content = content.encode('utf-8')
                else:
                    chapter.content = content
                
                new_book.add_item(chapter)
                spine.append(chapter)
            
            # Set spine and NCX
            new_book.spine = spine
            
            # Copy navigation
            if hasattr(original_book, 'toc'):
                new_book.toc = original_book.toc
            
            # Write EPUB
            epub.write_epub(output_path, new_book)
            
            logger.info(f"Successfully wrote translated EPUB to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write EPUB: {e}")
            return False