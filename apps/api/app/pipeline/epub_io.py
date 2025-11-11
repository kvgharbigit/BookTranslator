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

            # Extract and combine all CSS for embedding (like preview does)
            css_content = self.extract_all_css_from_book(original_book)
            logger.info(f"Extracted {len(css_content)} chars of CSS for embedding")

            # Copy all non-document items (CSS, images, fonts, etc.)
            for item in original_book.get_items():
                if item.get_type() != ebooklib.ITEM_DOCUMENT:
                    new_book.add_item(item)
            
            # Add translated documents and build href mapping
            spine = []
            href_mapping = {}
            
            for doc in translated_docs:
                # Use EpubItem instead of EpubHtml to preserve embedded CSS
                # EpubHtml has built-in sanitization that strips <style> tags
                chapter = epub.EpubItem(
                    uid=doc['id'],
                    file_name=doc['href'],
                    media_type='application/xhtml+xml',
                    content=b''  # Will be set below
                )
                # Set title as property
                chapter.title = doc['title'] or f"Chapter {len(spine)+1}"
                
                # Build proper href mapping BEFORE updating content
                href_mapping[doc['href']] = chapter.get_name()
                logger.debug(f"Href mapping: '{doc['href']}' -> '{chapter.get_name()}'")

                # Update internal links in content with correct mapping
                updated_content = self._update_internal_links(doc['content'], href_mapping)

                # Embed CSS in the HTML document (like preview does)
                updated_content = self._embed_css_in_html(updated_content, css_content)

                # Set content as bytes (EpubItem preserves raw content without sanitization)
                if isinstance(updated_content, str):
                    chapter.set_content(updated_content.encode('utf-8'))
                elif isinstance(updated_content, bytes):
                    chapter.set_content(updated_content)
                else:
                    chapter.set_content(str(updated_content).encode('utf-8'))

                new_book.add_item(chapter)
                spine.append(chapter)
            
            # Set spine - ebooklib expects a list of (item, linear) tuples or just items
            new_book.spine = [item for item in spine]
            
            # Update navigation and table of contents
            self._update_navigation(original_book, new_book, spine, translated_docs, href_mapping)
            
            # Write EPUB
            epub.write_epub(output_path, new_book)
            
            logger.info(f"Successfully wrote translated EPUB to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write EPUB: {e}")
            return False

    def write_bilingual_epub(
        self,
        original_book: epub.EpubBook,
        bilingual_docs: List[Dict],
        source_lang: str,
        target_lang: str,
        output_path: str
    ) -> bool:
        """Write bilingual EPUB with side-by-side original and translation."""

        try:
            # Create new book with bilingual metadata
            new_book = epub.EpubBook()

            # Copy metadata
            new_book.set_identifier(original_book.get_metadata('DC', 'identifier')[0][0])

            # Update title to indicate bilingual edition
            original_title = original_book.get_metadata('DC', 'title')[0][0]
            new_book.set_title(f"{original_title} (Bilingual Edition)")

            # Add TWO separate language declarations (critical for compatibility)
            new_book.add_metadata('DC', 'language', source_lang)
            new_book.add_metadata('DC', 'language', target_lang)

            # Add description
            from ..pipeline.bilingual_html import BilingualHTMLGenerator
            gen = BilingualHTMLGenerator()
            source_name = gen._get_language_name(source_lang)
            target_name = gen._get_language_name(target_lang)
            new_book.add_metadata('DC', 'description',
                f'Bilingual edition: {source_name} and {target_name}')

            # Copy authors
            for author in original_book.get_metadata('DC', 'creator'):
                new_book.add_author(author[0])

            # Extract original CSS
            original_css = self.extract_all_css_from_book(original_book)

            # Get bilingual CSS from generator (use public property for consistency with preview)
            bilingual_css = gen.css

            # Combine CSS: original + bilingual
            combined_css = f"{original_css}\n\n/* Bilingual Layout */\n{bilingual_css}"
            logger.info(f"Combined CSS: {len(combined_css)} chars")

            # Create external CSS file (EPUB standard - better e-reader compatibility)
            css_file = epub.EpubItem(
                uid="bilingual_style",
                file_name="styles/bilingual.css",
                media_type="text/css",
                content=combined_css.encode('utf-8')
            )
            new_book.add_item(css_file)
            logger.info("Created external bilingual CSS file: styles/bilingual.css")

            # Copy all non-document items (images, fonts, etc.)
            for item in original_book.get_items():
                if item.get_type() != ebooklib.ITEM_DOCUMENT:
                    new_book.add_item(item)

            # Add bilingual documents
            spine = []
            href_mapping = {}

            for doc in bilingual_docs:
                chapter = epub.EpubItem(
                    uid=doc['id'],
                    file_name=doc['href'],
                    media_type='application/xhtml+xml',
                    content=b''
                )
                chapter.title = doc['title'] or f"Chapter {len(spine)+1}"

                href_mapping[doc['href']] = chapter.get_name()

                # Update links and ADD CSS LINK instead of embedding
                updated_content = self._update_internal_links(doc['content'], href_mapping)
                updated_content = self._add_css_link(updated_content, "../styles/bilingual.css")

                # Set content
                if isinstance(updated_content, str):
                    chapter.set_content(updated_content.encode('utf-8'))
                elif isinstance(updated_content, bytes):
                    chapter.set_content(updated_content)
                else:
                    chapter.set_content(str(updated_content).encode('utf-8'))

                new_book.add_item(chapter)
                spine.append(chapter)

            # Set spine
            new_book.spine = [item for item in spine]

            # Update navigation
            self._update_navigation(original_book, new_book, spine, bilingual_docs, href_mapping)

            # Add NCX and Nav only if they don't already exist
            has_ncx = any(item.file_name.endswith('.ncx') for item in new_book.get_items())
            has_nav = any(item.get_type() == ebooklib.ITEM_NAVIGATION for item in new_book.get_items())

            if not has_ncx:
                new_book.add_item(epub.EpubNcx())

            if not has_nav:
                new_book.add_item(epub.EpubNav())

            # Write EPUB
            epub.write_epub(output_path, new_book)

            logger.info(f"Successfully wrote bilingual EPUB to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to write bilingual EPUB: {e}")
            return False

    def _update_navigation(self, original_book: epub.EpubBook, new_book: epub.EpubBook, spine: List, translated_docs: List[Dict], href_mapping: Dict[str, str]):
        """Update navigation elements including TOC and NCX files."""
        try:
            # Use the provided href_mapping from document creation
            
            # Update table of contents if present
            if hasattr(original_book, 'toc') and original_book.toc:
                updated_toc = self._update_toc_links(original_book.toc, href_mapping)
                new_book.toc = updated_toc
            else:
                # Create a basic TOC from spine documents if none exists
                basic_toc = self._create_basic_toc(spine)
                new_book.toc = basic_toc
            
            # Update NCX file if present
            for item in original_book.get_items():
                if item.file_name.endswith('.ncx'):
                    updated_ncx = self._update_ncx_content(item, href_mapping)
                    new_book.add_item(updated_ncx)
                    break
            
            # Update navigation document if present
            for item in original_book.get_items():
                if item.get_type() == ebooklib.ITEM_NAVIGATION:
                    updated_nav = self._update_nav_document(item, href_mapping)
                    new_book.add_item(updated_nav)
                    break
            
            logger.info("Navigation elements updated successfully")
            
        except Exception as e:
            logger.warning(f"Failed to update navigation: {e}")
            # Fallback: copy original TOC as-is
            if hasattr(original_book, 'toc'):
                new_book.toc = original_book.toc
    
    def _update_toc_links(self, toc_items, href_mapping):
        """Recursively update TOC links and translate titles."""
        updated_toc = []
        
        
        # Simple title translations for common chapters
        title_translations = {
            "Mowgli's Brothers": "Los hermanos de Mowgli",
            "Hunting-Song of the Seeonee Pack": "Canción de caza de la manada Seeonee",
            "Kaa's Hunting": "La caza de Kaa", 
            "Road-Song of the Bandar-Log": "Canción del camino de los Bandar-Log",
            "Tiger! Tiger!": "¡Tigre! ¡Tigre!",
            "Mowgli's Song": "La canción de Mowgli",
            "The White Seal": "La foca blanca",
            "Lukannon": "Lukannon",
            "Rikki-Tikki-Tavi": "Rikki-Tikki-Tavi",
            "Darzee's Chant": "El canto de Darzee",
            "Toomai of the Elephants": "Toomai de los elefantes",
            "Shiv and the Grasshopper": "Shiv y el saltamontes",
            "Her Majesty's Servants": "Los servidores de Su Majestad",
            "Parade Song of the Camp Animals": "Canción de desfile de los animales del campamento",
            "Contents": "Contenidos",
            "Table of Contents": "Tabla de contenidos"
        }
        
        # Add debug logging for title translation
        logger.debug(f"Available title translations: {list(title_translations.keys())}")
        logger.debug(f"Processing {len(toc_items)} TOC items")
        logger.debug(f"Href mapping keys: {list(href_mapping.keys())}")
        
        for item in toc_items:
            logger.debug(f"Processing TOC item: {type(item)}, {item}")
            if isinstance(item, tuple) and len(item) >= 2:
                # Handle tuple format (section, subsections)
                section, subsections = item[0], item[1] if len(item) > 1 else []
                
                # Check if the section href exists in our translated documents
                section_href = getattr(section, 'href', '').split('#')[0]  # Remove anchor
                if section_href and section_href in href_mapping:
                    # Update the href
                    section.href = href_mapping[section_href] + (section.href[len(section_href):] if '#' in getattr(section, 'href', '') else '')
                    
                    # Translate title if available
                    if hasattr(section, 'title'):
                        logger.debug(f"Section title: '{section.title}'")
                        if section.title in title_translations:
                            old_title = section.title
                            section.title = title_translations[section.title]
                            logger.info(f"Translated TOC title: '{old_title}' -> '{section.title}'")
                        else:
                            logger.debug(f"No translation found for: '{section.title}'")
                    
                    # Recursively update subsections
                    if subsections:
                        updated_subsections = self._update_toc_links(subsections, href_mapping)
                        if updated_subsections:  # Only add if subsections exist
                            updated_toc.append((section, updated_subsections))
                        else:
                            updated_toc.append(section)
                    else:
                        updated_toc.append(section)
                # Skip items that point to non-existent documents
                    
            else:
                # Handle direct items
                logger.debug(f"Direct TOC item - type: {type(item)}, title: {getattr(item, 'title', 'NO_TITLE')}, href: {getattr(item, 'href', 'NO_HREF')}")
                item_href = getattr(item, 'href', '').split('#')[0]  # Remove anchor
                if item_href and item_href in href_mapping:
                    # Update the href (preserve anchor if present)
                    anchor = item.href[len(item_href):] if '#' in getattr(item, 'href', '') else ''
                    item.href = href_mapping[item_href] + anchor
                    
                    # Translate title if available
                    if hasattr(item, 'title'):
                        logger.debug(f"Item title: '{item.title}'")
                        if item.title in title_translations:
                            old_title = item.title
                            item.title = title_translations[item.title]
                            logger.info(f"Translated TOC title: '{old_title}' -> '{item.title}'")
                        else:
                            logger.debug(f"No translation found for: '{item.title}'")
                        
                    updated_toc.append(item)
                # Skip items that point to non-existent documents
        
        return updated_toc
    
    def _create_basic_toc(self, spine):
        """Create a basic table of contents from spine documents."""
        toc = []
        for i, chapter in enumerate(spine):
            # Get title from chapter - try different attributes
            title = None
            if hasattr(chapter, 'title'):
                title = chapter.title
            elif hasattr(chapter, 'get_name'):
                # Use filename as fallback
                name = chapter.get_name()
                title = name.replace('.xhtml', '').replace('.html', '').replace('_', ' ').title()
            else:
                title = f"Chapter {i+1}"

            toc_item = epub.Link(
                href=chapter.get_name() if hasattr(chapter, 'get_name') else f"chapter{i+1}.xhtml",
                title=title,
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
            
            # Title translations for NCX
            title_translations = {
                "Mowgli's Brothers": "Los hermanos de Mowgli",
                "Hunting-Song of the Seeonee Pack": "Canción de caza de la manada Seeonee",
                "Kaa's Hunting": "La caza de Kaa", 
                "Road-Song of the Bandar-Log": "Canción del camino de los Bandar-Log",
                "Tiger! Tiger!": "¡Tigre! ¡Tigre!",
                "\"Tiger! Tiger!\"": "\"¡Tigre! ¡Tigre!\"",
                "Mowgli's Song": "La canción de Mowgli",
                "The White Seal": "La foca blanca",
                "Lukannon": "Lukannon",
                "Rikki-Tikki-Tavi": "Rikki-Tikki-Tavi",
                "\"Rikki-Tikki-Tavi\"": "\"Rikki-Tikki-Tavi\"",
                "Darzee's Chant": "El canto de Darzee",
                "Toomai of the Elephants": "Toomai de los elefantes",
                "Shiv and the Grasshopper": "Shiv y el saltamontes",
                "Her Majesty's Servants": "Los servidores de Su Majestad",
                "Parade Song of the Camp Animals": "Canción de desfile de los animales del campamento",
                "Contents": "Contenidos",
                "Table of Contents": "Tabla de contenidos",
                "THE JUNGLE BOOK": "EL LIBRO DE LA SELVA",
                "The Jungle Book": "El Libro de la Selva"
            }
            
            # Update all navPoint src attributes and translate text labels
            for nav_point in soup.find_all('navPoint'):
                content_tag = nav_point.find('content')
                if content_tag and content_tag.get('src'):
                    src = content_tag['src']
                    # Extract filename without anchor
                    base_href = src.split('#')[0]
                    anchor = '#' + src.split('#')[1] if '#' in src else ''
                    
                    if base_href in href_mapping:
                        content_tag['src'] = href_mapping[base_href] + anchor
                
                # Translate the text label
                nav_label = nav_point.find('navLabel')
                if nav_label:
                    text_element = nav_label.find('text')
                    if text_element and text_element.string:
                        original_text = text_element.string.strip()
                        if original_text in title_translations:
                            text_element.string = title_translations[original_text]
                            logger.info(f"Translated NCX title: '{original_text}' -> '{title_translations[original_text]}'")
            
            # Also update the document title
            doc_title = soup.find('docTitle')
            if doc_title:
                text_element = doc_title.find('text')
                if text_element and text_element.string:
                    original_text = text_element.string.strip()
                    if original_text in title_translations:
                        text_element.string = title_translations[original_text]
                        logger.info(f"Translated NCX document title: '{original_text}' -> '{title_translations[original_text]}'")
            
            # Create new NCX item
            new_ncx = epub.EpubItem(
                uid=ncx_item.get_id(),
                file_name=ncx_item.get_name(),
                media_type='application/x-dtbncx+xml',  # Use explicit media type
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
            
            # Title translations for EPUB3 navigation
            title_translations = {
                "Mowgli's Brothers": "Los hermanos de Mowgli",
                "Hunting-Song of the Seeonee Pack": "Canción de caza de la manada Seeonee",
                "Kaa's Hunting": "La caza de Kaa", 
                "Road-Song of the Bandar-Log": "Canción del camino de los Bandar-Log",
                "Tiger! Tiger!": "¡Tigre! ¡Tigre!",
                "\"Tiger! Tiger!\"": "\"¡Tigre! ¡Tigre!\"",
                "Mowgli's Song": "La canción de Mowgli",
                "The White Seal": "La foca blanca",
                "Lukannon": "Lukannon",
                "Rikki-Tikki-Tavi": "Rikki-Tikki-Tavi",
                "\"Rikki-Tikki-Tavi\"": "\"Rikki-Tikki-Tavi\"",
                "Darzee's Chant": "El canto de Darzee",
                "Toomai of the Elephants": "Toomai de los elefantes",
                "Shiv and the Grasshopper": "Shiv y el saltamontes",
                "Her Majesty's Servants": "Los servidores de Su Majestad",
                "Parade Song of the Camp Animals": "Canción de desfile de los animales del campamento",
                "Contents": "Contenidos",
                "Table of Contents": "Tabla de contenidos",
                "THE JUNGLE BOOK": "EL LIBRO DE LA SELVA",
                "The Jungle Book": "El Libro de la Selva"
            }
            
            # Update all anchor hrefs in navigation and translate text
            for link in soup.find_all('a', href=True):
                href = link['href']
                base_href = href.split('#')[0]
                anchor = '#' + href.split('#')[1] if '#' in href else ''
                
                if base_href in href_mapping:
                    link['href'] = href_mapping[base_href] + anchor
                
                # Translate the link text
                if link.string:
                    original_text = link.string.strip()
                    if original_text in title_translations:
                        link.string = title_translations[original_text]
                        logger.info(f"Translated nav text: '{original_text}' -> '{title_translations[original_text]}'")
            
            # Create new navigation item
            new_nav = epub.EpubNav()
            new_nav.content = str(soup).encode('utf-8')
            
            return new_nav
            
        except Exception as e:
            logger.warning(f"Failed to update navigation document: {e}")
            return nav_item
    
    def extract_all_css_from_book(self, book: epub.EpubBook) -> str:
        """Extract and combine all CSS stylesheets from EPUB.

        Args:
            book: EbookLib Book object

        Returns:
            Combined CSS content from all stylesheets
        """
        css_content = []
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_STYLE:
                try:
                    css = item.get_content().decode('utf-8')
                    css_content.append(css)
                except Exception as e:
                    logger.warning(f"Failed to extract CSS from {item.get_name()}: {e}")

        return '\n\n'.join(css_content)

    def _embed_css_in_html(self, html_content: str, css_content: str) -> str:
        """Embed CSS directly in HTML document's <head> section.

        Uses EXACT same approach as preview.py for consistency.

        Args:
            html_content: HTML document content
            css_content: CSS to embed

        Returns:
            HTML with embedded CSS
        """
        try:
            if not css_content:
                return html_content

            soup = BeautifulSoup(html_content, 'xml')

            # Find or create head element
            head = soup.find('head')
            if not head:
                # Create head if it doesn't exist
                html_tag = soup.find('html')
                if html_tag:
                    head = soup.new_tag('head')
                    html_tag.insert(0, head)
                else:
                    logger.warning("No <html> or <head> tag found, cannot embed CSS")
                    return html_content

            # Use EXACT same CSS embedding as preview.py (lines 968-1008)
            # Just inject raw CSS text inside <style> tags - no BeautifulSoup manipulation
            enhanced_css = f"""{css_content}

/* Minimal responsive wrapper - don't override EPUB styles */
body {{
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
}}

/* Ensure images are responsive */
img {{
    max-width: 100% !important;
    height: auto !important;
}}
"""

            # Insert the style tag as raw HTML (same as preview does)
            style_html = f'<style type="text/css">\n{enhanced_css}\n</style>'

            # Convert to string and inject style tag at start of head
            html_str = str(soup)

            # Find </head> closing tag and insert before it
            head_close_pos = html_str.find('</head>')
            if head_close_pos != -1:
                html_str = html_str[:head_close_pos] + style_html + html_str[head_close_pos:]
            else:
                # Fallback: try to find <head> and insert after it
                head_open_pos = html_str.find('<head>')
                if head_open_pos != -1:
                    insert_pos = html_str.find('>', head_open_pos) + 1
                    html_str = html_str[:insert_pos] + style_html + html_str[insert_pos:]

            return html_str

        except Exception as e:
            logger.error(f"Failed to embed CSS in HTML: {e}", exc_info=True)
            return html_content

    def _add_css_link(self, html_content: str, css_href: str) -> str:
        """Add CSS link to HTML document's <head> section.

        Args:
            html_content: HTML document content
            css_href: Relative path to CSS file (e.g., "../styles/bilingual.css")

        Returns:
            HTML with CSS link added
        """
        try:
            soup = BeautifulSoup(html_content, 'xml')

            # Find or create head element
            head = soup.find('head')
            if not head:
                html_tag = soup.find('html')
                if html_tag:
                    head = soup.new_tag('head')
                    html_tag.insert(0, head)
                else:
                    logger.warning("No <html> or <head> tag found, cannot add CSS link")
                    return html_content

            # Create link tag (EPUB standard format)
            link_tag = soup.new_tag('link', rel='stylesheet', type='text/css', href=css_href)
            head.insert(0, link_tag)

            logger.info(f"Added CSS link: {css_href}")
            return str(soup)

        except Exception as e:
            logger.error(f"Failed to add CSS link: {e}", exc_info=True)
            return html_content

    def _update_internal_links(self, content: str, href_mapping: Dict[str, str]) -> str:
        """Update internal hyperlinks within document content."""
        try:
            if not content or not isinstance(content, str):
                return content

            soup = BeautifulSoup(content, 'xml')

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