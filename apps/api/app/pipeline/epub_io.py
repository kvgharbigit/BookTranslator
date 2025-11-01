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
            
            # Create href mapping for internal link updates
            href_mapping = {}
            for doc in translated_docs:
                href_mapping[doc['href']] = doc['href']  # Keep same hrefs for now
            
            # Add translated documents
            spine = []
            for doc in translated_docs:
                # Update internal links in content
                updated_content = self._update_internal_links(doc['content'], href_mapping)
                
                # Create new EPUB item
                chapter = epub.EpubHtml(
                    title=doc['title'] or f"Chapter {len(spine)+1}",
                    file_name=doc['href'],
                    lang='es'  # Set to target language
                )
                
                # Ensure content is properly encoded
                if isinstance(updated_content, str):
                    chapter.content = updated_content.encode('utf-8')
                else:
                    chapter.content = updated_content
                
                new_book.add_item(chapter)
                spine.append(chapter)
            
            # Set spine and NCX
            new_book.spine = spine
            
            # Update navigation and table of contents
            self._update_navigation(original_book, new_book, spine, translated_docs)
            
            # Write EPUB
            epub.write_epub(output_path, new_book)
            
            logger.info(f"Successfully wrote translated EPUB to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write EPUB: {e}")
            return False
    
    def _update_navigation(self, original_book: epub.EpubBook, new_book: epub.EpubBook, spine: List, translated_docs: List[Dict]):
        """Update navigation elements including TOC and NCX files."""
        try:
            # Create href mapping for documents
            href_mapping = {}
            for i, doc in enumerate(translated_docs):
                if i < len(spine):
                    href_mapping[doc['href']] = spine[i].get_name()
            
            # Update table of contents if present
            if hasattr(original_book, 'toc') and original_book.toc:
                new_book.toc = self._update_toc_links(original_book.toc, href_mapping)
            else:
                # Create a basic TOC from spine documents if none exists
                new_book.toc = self._create_basic_toc(spine)
            
            # Find and update NCX file if present
            for item in original_book.get_items():
                if item.get_type() == ebooklib.ITEM_NCX:
                    updated_ncx = self._update_ncx_content(item, href_mapping)
                    if updated_ncx:
                        new_book.add_item(updated_ncx)
                        new_book.add_item(epub.EpubNcx())
                    break
            else:
                # Add default NCX if none exists
                new_book.add_item(epub.EpubNcx())
            
            # Handle EPUB3 navigation document
            nav_item = None
            for item in original_book.get_items():
                if item.get_type() == ebooklib.ITEM_NAV:
                    nav_item = item
                    break
            
            if nav_item:
                updated_nav = self._update_nav_document(nav_item, href_mapping)
                if updated_nav:
                    new_book.add_item(updated_nav)
            
            logger.info("Navigation elements updated successfully")
            
        except Exception as e:
            logger.warning(f"Failed to update navigation: {e}")
            # Fallback: copy original TOC as-is
            if hasattr(original_book, 'toc'):
                new_book.toc = original_book.toc
    
    def _update_toc_links(self, toc_items, href_mapping):
        """Recursively update TOC links."""
        updated_toc = []
        
        for item in toc_items:
            if isinstance(item, tuple) and len(item) >= 2:
                # Handle tuple format (section, subsections)
                section, subsections = item[0], item[1] if len(item) > 1 else []
                
                if hasattr(section, 'href') and section.href in href_mapping:
                    # Update the href
                    section.href = href_mapping[section.href]
                
                # Recursively update subsections
                if subsections:
                    updated_subsections = self._update_toc_links(subsections, href_mapping)
                    updated_toc.append((section, updated_subsections))
                else:
                    updated_toc.append(section)
            else:
                # Handle direct items
                if hasattr(item, 'href') and item.href in href_mapping:
                    item.href = href_mapping[item.href]
                updated_toc.append(item)
        
        return updated_toc
    
    def _create_basic_toc(self, spine):
        """Create a basic table of contents from spine documents."""
        toc = []
        for i, chapter in enumerate(spine):
            toc_item = epub.Link(
                href=chapter.get_name(),
                title=chapter.get_title() or f"Chapter {i+1}",
                uid=f"toc_{i}"
            )
            toc.append(toc_item)
        return toc
    
    def _update_ncx_content(self, ncx_item, href_mapping):
        """Update NCX navigation content."""
        try:
            ncx_content = ncx_item.get_content().decode('utf-8', errors='ignore')
            
            # Parse NCX XML and update hrefs
            soup = BeautifulSoup(ncx_content, 'xml')
            
            # Update all navPoint src attributes
            for nav_point in soup.find_all('navPoint'):
                content_tag = nav_point.find('content')
                if content_tag and content_tag.get('src'):
                    src = content_tag['src']
                    # Extract filename without anchor
                    base_href = src.split('#')[0]
                    anchor = '#' + src.split('#')[1] if '#' in src else ''
                    
                    if base_href in href_mapping:
                        content_tag['src'] = href_mapping[base_href] + anchor
            
            # Create new NCX item
            new_ncx = epub.EpubItem(
                uid=ncx_item.get_id(),
                file_name=ncx_item.get_name(),
                media_type=ncx_item.get_type(),
                content=str(soup).encode('utf-8')
            )
            
            return new_ncx
            
        except Exception as e:
            logger.warning(f"Failed to update NCX content: {e}")
            return ncx_item
    
    def _update_nav_document(self, nav_item, href_mapping):
        """Update EPUB3 navigation document."""
        try:
            nav_content = nav_item.get_content().decode('utf-8', errors='ignore')
            soup = BeautifulSoup(nav_content, 'html.parser')
            
            # Update all anchor hrefs in navigation
            for link in soup.find_all('a', href=True):
                href = link['href']
                base_href = href.split('#')[0]
                anchor = '#' + href.split('#')[1] if '#' in href else ''
                
                if base_href in href_mapping:
                    link['href'] = href_mapping[base_href] + anchor
            
            # Create new navigation item
            new_nav = epub.EpubNav()
            new_nav.content = str(soup).encode('utf-8')
            
            return new_nav
            
        except Exception as e:
            logger.warning(f"Failed to update navigation document: {e}")
            return nav_item
    
    def _update_internal_links(self, content: str, href_mapping: Dict[str, str]) -> str:
        """Update internal hyperlinks within document content."""
        try:
            if not content or not isinstance(content, str):
                return content
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Update all anchor links
            for link in soup.find_all('a', href=True):
                href = link['href']
                
                # Skip external links (http/https)
                if href.startswith(('http://', 'https://', 'mailto:', 'ftp://')):
                    continue
                
                # Handle relative links to other chapters
                if '/' not in href or href.startswith('./'):
                    # Clean up the href
                    base_href = href.replace('./', '')
                    base_file = base_href.split('#')[0]
                    anchor = '#' + base_href.split('#')[1] if '#' in base_href else ''
                    
                    # Update if we have a mapping for this file
                    if base_file in href_mapping:
                        link['href'] = href_mapping[base_file] + anchor
                        logger.debug(f"Updated internal link: {href} -> {link['href']}")
            
            return str(soup)
            
        except Exception as e:
            logger.warning(f"Failed to update internal links: {e}")
            return content