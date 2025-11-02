"""
Text formatting utilities for book output generation
Handles intelligent paragraph breaking, chapter extraction, and professional formatting
"""

import re
import logging
from datetime import datetime
from typing import List, Dict, Optional, Set
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class TextFormatter:
    """Handles text formatting for various output formats."""
    
    def __init__(self):
        # Title translations for consistent TOC handling
        self.title_translations = {
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
            "Table of Contents": "Tabla de contenidos"
        }
    
    def format_book_header(
        self, 
        title: str, 
        author: str, 
        original_title: str,
        target_lang: str = "Español",
        source_lang: str = "English"
    ) -> List[str]:
        """Generate formatted book header for professional output."""
        
        translation_date = datetime.now().strftime("%Y-%m-%d")
        
        return [
            "=" * 70,
            title.center(70),
            "=" * 70,
            "",
            f"Título original: {original_title}",
            f"Autor: {author}",
            f"Traducción: {target_lang}",
            f"Fecha de traducción: {translation_date}",
            "",
            "Esta es una traducción automática realizada por inteligencia artificial.",
            "Para uso personal y educativo.",
            "",
            "=" * 70,
            "",
            ""
        ]
    
    def extract_chapter_title(self, content: str) -> Optional[str]:
        """Extract chapter title from HTML content."""
        
        try:
            soup = BeautifulSoup(content, 'xml')
            for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                heading_text = heading.get_text(strip=True)
                if (heading_text and len(heading_text) > 3 and 
                    not any(skip in heading_text.lower() for skip in 
                           ['project gutenberg', 'ebook', 'contents', 'table'])):
                    return heading_text.strip()
        except Exception as e:
            logger.debug(f"Chapter title extraction failed: {e}")
        
        return None
    
    def format_chapter_header(
        self, 
        chapter_num: int,
        title: Optional[str] = None,
        doc_title: Optional[str] = None
    ) -> List[str]:
        """Format a chapter header with proper structure."""
        
        # Use extracted title, document title, or fallback to chapter number
        if title:
            header_text = title.upper()
        elif doc_title and doc_title != 'Untitled' and 'gutenberg' not in doc_title.lower():
            header_text = doc_title.strip().upper()
        else:
            header_text = f"CAPÍTULO {chapter_num}"
        
        return [
            f"\n{'='*60}",
            f"{header_text.center(60)}",
            f"{'='*60}\n"
        ]
    
    def format_toc_section(self, content: str) -> List[str]:
        """Format table of contents section with translations."""
        
        formatted_content = [
            f"\n{'='*60}",
            "TABLA DE CONTENIDOS".center(60),
            f"{'='*60}\n"
        ]
        
        try:
            soup = BeautifulSoup(content, 'xml')
            
            # Extract TOC entries and translate them
            toc_entries = []
            for element in soup.find_all(['p', 'div', 'li', 'a']):
                text = element.get_text(strip=True)
                if text and len(text) > 3:
                    # Check if this looks like a chapter title
                    if any(key.lower() in text.lower() for key in self.title_translations.keys()):
                        # Try to translate
                        for original, translation in self.title_translations.items():
                            if original.lower() in text.lower():
                                toc_entries.append(f"• {translation}")
                                break
                        else:
                            # If no translation found, add as-is but mark for review
                            if (len(text) < 100 and 
                                not any(skip in text.lower() for skip in ['project gutenberg', 'ebook'])):
                                toc_entries.append(f"• {text}")
            
            # Add translated TOC entries
            for entry in toc_entries[:10]:  # Limit to first 10 entries
                formatted_content.append(entry)
            
            formatted_content.append("")
            
        except Exception as e:
            logger.debug(f"TOC formatting failed: {e}")
            # Fallback: show basic message
            formatted_content.append("Contenido disponible en el documento principal")
            formatted_content.append("")
        
        return formatted_content
    
    def clean_and_wrap_text(self, text: str, max_length: int = 500) -> List[str]:
        """Clean HTML and wrap long paragraphs intelligently at sentence boundaries."""
        
        clean_text = ' '.join(text.split())
        
        if len(clean_text) <= 15:  # Skip very short text
            return []
        
        # Break very long paragraphs at sentence boundaries
        if len(clean_text) > max_length:
            sentences = []
            current_sentence = ""
            words = clean_text.split()
            
            for word in words:
                current_sentence += word + " "
                # Break at sentence endings
                if (word.endswith(('.', '!', '?', '."', '!"', '?"')) and 
                    len(current_sentence) > 100):
                    sentences.append(current_sentence.strip())
                    current_sentence = ""
            
            # Add remaining text
            if current_sentence.strip():
                sentences.append(current_sentence.strip())
            
            # Return sentences as separate paragraphs if needed
            result = []
            for sentence in sentences:
                if len(sentence) > 15:
                    result.append(sentence)
                    if len(sentence) > 200:  # Add break after long sentences
                        result.append("")
            
            return result
        else:
            return [clean_text]
    
    def extract_document_content(self, content: str, chapter_title: Optional[str] = None) -> List[str]:
        """Extract and format text from HTML content with proper structure."""
        
        formatted_content = []
        
        try:
            soup = BeautifulSoup(content, 'xml')
            
            # Track seen text to avoid duplicates
            seen_texts: Set[str] = set()
            first_heading_used = False  # Track if we've used the first heading as chapter title
            
            # Process elements in document order for proper flow
            for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'div', 'blockquote']):
                # Skip elements that are likely containers without direct text
                if element.name == 'div' and element.find(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                    continue
                    
                text = element.get_text(separator=' ', strip=True)
                if not text or len(text) < 3:
                    continue
                
                # Skip duplicates
                text_key = text.lower().replace(' ', '')[:100]  # Use first 100 chars as key
                if text_key in seen_texts:
                    continue
                seen_texts.add(text_key)
                
                # Skip Project Gutenberg metadata
                if any(keyword in text.lower() for keyword in 
                      ['project gutenberg', 'ebook #', 'gutenberg.org']):
                    continue
                
                # Format headings
                if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    # Skip the first heading if we already used it as the chapter title
                    if chapter_title and not first_heading_used and text.strip() == chapter_title:
                        first_heading_used = True
                        continue
                    
                    formatted_content.append(f"\n{text.upper()}")
                    formatted_content.append("-" * min(len(text), 40))
                    formatted_content.append("")
                
                # Format paragraphs with proper structure
                elif element.name in ['p', 'blockquote']:
                    paragraphs = self.clean_and_wrap_text(text)
                    formatted_content.extend(paragraphs)
                    if paragraphs:  # Add paragraph break only if content was added
                        formatted_content.append("")
                
                # Handle div elements that contain substantial direct text
                elif element.name == 'div':
                    # Only process divs with direct text content (not just child elements)
                    direct_text = element.get_text(separator=' ', strip=True)
                    if len(direct_text) > 15:
                        paragraphs = self.clean_and_wrap_text(direct_text)
                        formatted_content.extend(paragraphs)
                        if paragraphs:
                            formatted_content.append("")
            
            # Fallback: if no structured content found, use simple text extraction
            if len(formatted_content) <= 3:  # Very little content added
                text = soup.get_text(separator='\n', strip=True)
                # Split into paragraphs and clean up
                paragraphs = [p.strip() for p in text.split('\n') if p.strip() and len(p.strip()) > 15]
                for para in paragraphs:
                    if not any(keyword in para.lower() for keyword in 
                              ['project gutenberg', 'ebook #']):
                        formatted_content.append(para)
                        formatted_content.append("")
                    
        except Exception as e:
            logger.debug(f"Content extraction failed: {e}")
            # Fallback to raw content if HTML parsing fails
            if isinstance(content, str):
                # Remove HTML tags manually if BeautifulSoup fails
                clean_content = re.sub(r'<[^>]+>', '', content)
                clean_content = re.sub(r'\s+', ' ', clean_content).strip()
                formatted_content.append(clean_content)
            else:
                formatted_content.append(str(content))
        
        return formatted_content
    
    def is_metadata_document(self, content: str) -> bool:
        """Check if document is primarily metadata (short or contains Project Gutenberg info)."""
        
        return (len(content.strip()) < 500 or 
                'gutenberg' in content.lower() or 
                'ebook' in content.lower())
    
    def is_toc_document(self, content: str) -> bool:
        """Check if document is a table of contents."""
        
        return any(keyword in content.lower() for keyword in 
                  ['contents', 'índice', 'table'])
    
    def generate_formatted_book(
        self,
        docs: List[Dict],
        book_title: str,
        author: str,
        original_title: str,
        target_lang: str = "Español",
        provider_name: str = ""
    ) -> str:
        """Generate complete formatted book text with proper structure."""
        
        # Start with professional header (no provider metadata)
        formatted_content = self.format_book_header(
            title=book_title,
            author=author,
            original_title=original_title,
            target_lang=target_lang
        )
        
        actual_chapter_count = 0
        
        for i, doc in enumerate(docs):
            content = doc.get('content', '')
            
            # Handle metadata documents differently
            if self.is_metadata_document(content):
                if self.is_toc_document(content):
                    formatted_content.extend(self.format_toc_section(content))
                else:
                    continue  # Skip pure metadata documents
            else:
                # This is actual chapter content
                actual_chapter_count += 1
                
                # Extract chapter title
                chapter_title = self.extract_chapter_title(content)
                
                # Add chapter header
                formatted_content.extend(self.format_chapter_header(
                    chapter_num=actual_chapter_count,
                    title=chapter_title,
                    doc_title=doc.get('title')
                ))
                
                # Extract and format document content
                content_lines = self.extract_document_content(content, chapter_title)
                formatted_content.extend(content_lines)
            
            # Section separator
            formatted_content.append("\n" + "~" * 60 + "\n")
        
        # Join content and clean up excessive newlines
        final_content = '\n'.join(formatted_content)
        final_content = re.sub(r'\n\s*\n\s*\n+', '\n\n', final_content)  # Max 2 consecutive newlines
        
        return final_content