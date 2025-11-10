"""
Simple PDF text extraction processor.

Philosophy: Extract clean text, minimal structure detection.
No format preservation - focus on reliable text extraction.
"""
import re
from typing import List, Dict, Optional
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

from app.logger import get_logger

logger = get_logger(__name__)


class SimplePDFProcessor:
    """
    Simple PDF text extractor with minimal structure detection.

    Extracts clean text from PDFs and converts to simple HTML format
    compatible with existing HTMLSegmenter pipeline.
    """

    def __init__(self):
        if fitz is None:
            raise ImportError("PyMuPDF (fitz) not installed. Run: pip install PyMuPDF")

    def process_pdf(self, pdf_path: str) -> tuple[Dict, List[Dict]]:
        """
        Main entry point - process PDF to EPUB-compatible structure.

        Returns:
            Tuple of (book_metadata, spine_docs) where:
            - book_metadata: dict with title, author, language
            - spine_docs: list of dicts with id, href, content, title
        """
        logger.info(f"Processing PDF: {pdf_path}")

        # Open PDF
        pdf_doc = fitz.open(pdf_path)

        # Extract metadata
        metadata = self._extract_metadata(pdf_doc)
        logger.info(f"Extracted metadata: {metadata}")

        # Extract raw text with page markers (for chapter detection)
        raw_text = self._extract_text(pdf_doc)
        logger.info(f"Extracted {len(raw_text)} characters of text")

        # Detect chapters (before cleaning, to use page break markers)
        chapters = self._detect_chapters(raw_text)
        if chapters:
            logger.info(f"Detected {len(chapters)} chapters")
        else:
            logger.info("No chapters detected, using single document")

        # Clean artifacts
        clean_text = self._clean_artifacts(raw_text)
        logger.info(f"After cleaning: {len(clean_text)} characters")

        # Convert to HTML spine documents (with or without chapters)
        spine_docs = self._to_simple_html(clean_text, metadata['title'], chapters)
        logger.info(f"Created {len(spine_docs)} HTML documents")

        pdf_doc.close()

        return metadata, spine_docs

    def extract_text_for_pricing(self, pdf_path: str) -> str:
        """
        Quick text extraction for pricing calculation.
        No structure detection, just raw text.
        """
        logger.info(f"Extracting text for pricing: {pdf_path}")
        pdf_doc = fitz.open(pdf_path)
        text = self._extract_text(pdf_doc)
        pdf_doc.close()
        return text

    def _extract_metadata(self, pdf_doc) -> Dict:
        """Extract title, author from PDF metadata."""
        metadata = pdf_doc.metadata or {}

        title = metadata.get('title', '').strip()
        author = metadata.get('author', '').strip()

        # Fallback: try to extract title from first page
        if not title:
            first_page = pdf_doc[0] if len(pdf_doc) > 0 else None
            if first_page:
                title = self._extract_title_from_first_page(first_page)

        return {
            'title': title or 'Untitled',
            'author': author or 'Unknown Author',
            'language': 'en',  # Default, will be detected during translation
        }

    def _extract_title_from_first_page(self, page) -> Optional[str]:
        """
        Try to extract title from first page.
        Look for largest text block near top of page.
        """
        try:
            blocks = page.get_text("dict")["blocks"]

            # Find text blocks in top 30% of page
            page_height = page.rect.height
            top_blocks = []

            for block in blocks:
                if block.get("type") == 0:  # Text block
                    y0 = block.get("bbox", [0, 0, 0, 0])[1]
                    if y0 < page_height * 0.3:
                        # Get largest font size in block
                        max_size = 0
                        text = ""
                        for line in block.get("lines", []):
                            for span in line.get("spans", []):
                                size = span.get("size", 0)
                                if size > max_size:
                                    max_size = size
                                    text = span.get("text", "").strip()

                        if text and max_size > 0:
                            top_blocks.append((max_size, text))

            # Return text with largest font
            if top_blocks:
                top_blocks.sort(reverse=True)
                return top_blocks[0][1]

        except Exception as e:
            logger.warning(f"Failed to extract title from first page: {e}")

        return None

    def _extract_text(self, pdf_doc) -> str:
        """
        Extract raw text from all pages.
        Uses simple text extraction (no layout analysis).
        """
        text_parts = []

        for page_num, page in enumerate(pdf_doc):
            try:
                # Extract text (simple mode)
                page_text = page.get_text()

                if page_text.strip():
                    # Add page break marker (will help with chapter detection later)
                    text_parts.append(f"\n___PAGE_BREAK_{page_num}___\n")
                    text_parts.append(page_text)

            except Exception as e:
                logger.warning(f"Failed to extract text from page {page_num}: {e}")
                continue

        return ''.join(text_parts)

    def _clean_artifacts(self, text: str) -> str:
        """
        Remove common PDF artifacts:
        - Page numbers
        - Headers/footers
        - Extra whitespace
        """
        # Remove page break markers for now (we'll use them later for chapter detection)
        # Keep them for now, remove in final processing

        # Normalize line breaks
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # Remove page numbers at line ends/starts
        # Patterns: "Page 12", "12", "- 12 -", etc.
        text = re.sub(r'^\s*Page\s+\d+\s*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
        text = re.sub(r'^\s*-?\s*\d+\s*-?\s*$', '', text, flags=re.MULTILINE)

        # Remove common header/footer patterns
        # Simple heuristic: single line repeated across pages
        # TODO: Implement repeated text detection (future enhancement)

        # Collapse multiple blank lines into max 2 (paragraph break)
        text = re.sub(r'\n{4,}', '\n\n\n', text)

        # Remove trailing/leading whitespace from lines
        lines = [line.rstrip() for line in text.split('\n')]
        text = '\n'.join(lines)

        return text.strip()

    def _detect_chapters(self, text: str) -> Optional[List[Dict]]:
        """
        Detect chapter breaks in text.

        Uses multiple heuristics:
        1. Page breaks followed by chapter markers
        2. "Chapter N" patterns
        3. Roman numerals (I., II., III., etc.)
        4. All-caps titles at page start
        5. Numbered patterns (1., 2., etc.)

        Returns:
            List of chapter dicts with 'title' and 'start_pos', or None if no chapters
        """
        chapters = []

        # Split text into pages using page break markers
        page_pattern = r'___PAGE_BREAK_(\d+)___'
        pages = re.split(page_pattern, text)

        # pages will be: [text_before_page0, page_num, text_of_page, page_num, text_of_page, ...]
        current_pos = 0

        for i in range(0, len(pages), 2):
            page_text = pages[i]
            page_num = int(pages[i-1]) if i > 0 else 0

            # Get first few lines of page (potential chapter title)
            lines = page_text.strip().split('\n')[:5]
            first_line = lines[0].strip() if lines else ""

            if not first_line:
                current_pos += len(page_text)
                continue

            # Check for chapter patterns
            chapter_title = None

            # Pattern 1: "Chapter" followed by number or word
            # Examples: "Chapter 1", "Chapter One", "CHAPTER ONE"
            chapter_match = re.match(r'^(?:CHAPTER|Chapter)\s+([IVXLCDM\d]+|[A-Za-z]+)(?:\s*[:\-]?\s*(.*))?$', first_line)
            if chapter_match:
                chapter_title = first_line

            # Pattern 2: Roman numerals at start
            # Examples: "I.", "II.", "III. CORALINE"
            elif re.match(r'^[IVXLCDM]+\.?\s+[A-Z]', first_line):
                chapter_title = first_line

            # Pattern 3: Numbered patterns
            # Examples: "1.", "2. The Story Begins"
            elif re.match(r'^\d+\.?\s+[A-Z]', first_line):
                chapter_title = first_line

            # Pattern 4: All-caps title (at least 3 words or 10+ chars)
            # Examples: "LITTLE RED RIDING HOOD", "THE BEGINNING"
            elif first_line.isupper() and (len(first_line.split()) >= 2 or len(first_line) >= 10):
                # Make sure it's not just metadata or headers
                if not any(skip in first_line for skip in ['PAGE', 'ISBN', 'COPYRIGHT', 'PUBLISHER']):
                    chapter_title = first_line

            # Pattern 5: Title Case with sufficient length
            # Examples: "Little Red Riding Hood", "Snow White and the Seven Dwarfs"
            elif first_line.istitle() and len(first_line) >= 10 and not first_line.endswith('.'):
                chapter_title = first_line

            if chapter_title:
                chapters.append({
                    'title': chapter_title,
                    'start_pos': current_pos,
                    'page_num': page_num
                })

            current_pos += len(page_text)

        # Only return chapters if we found at least 2
        # (1 chapter = just continuous text, not worth splitting)
        if len(chapters) >= 2:
            return chapters

        return None

    def _to_simple_html(self, text: str, title: str, chapters: Optional[List[Dict]] = None) -> List[Dict]:
        """
        Convert cleaned text to simple HTML spine documents.

        Creates:
        1. Title page (if title exists)
        2. Content document(s) - either single or split by chapters
        """
        spine_docs = []

        # 1. Create title page
        if title and title != 'Untitled':
            title_html = f"""<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>{self._escape_html(title)}</title>
    <meta charset="utf-8"/>
</head>
<body>
    <h1>{self._escape_html(title)}</h1>
</body>
</html>"""

            spine_docs.append({
                'id': 'titlepage',
                'href': 'titlepage.xhtml',
                'content': title_html,
                'title': 'Title Page'
            })

        # 2. Remove page break markers (replace with paragraph breaks)
        text = re.sub(r'___PAGE_BREAK_\d+___', '', text)

        # 3. Create content documents (with or without chapters)
        if chapters:
            # Split into chapters
            for i, chapter in enumerate(chapters):
                # Get text for this chapter
                start_pos = chapter['start_pos']
                end_pos = chapters[i + 1]['start_pos'] if i + 1 < len(chapters) else len(text)

                # Adjust positions after page marker removal
                # (page markers were removed, so we need to search for chapter title)
                chapter_text = self._extract_chapter_text(text, chapter['title'],
                                                          chapters[i + 1]['title'] if i + 1 < len(chapters) else None)

                if not chapter_text:
                    continue

                # Split into paragraphs
                paragraphs = self._split_paragraphs(chapter_text)

                if not paragraphs:
                    continue

                # Build HTML with chapter heading
                chapter_html = self._chapter_to_html(chapter['title'], paragraphs, title)

                chapter_id = f"chapter_{i + 1}"
                spine_docs.append({
                    'id': chapter_id,
                    'href': f'{chapter_id}.xhtml',
                    'content': chapter_html,
                    'title': chapter['title']
                })

        else:
            # Single content document (no chapters detected)
            paragraphs = self._split_paragraphs(text)
            content_html = self._paragraphs_to_html(paragraphs, title)

            spine_docs.append({
                'id': 'content',
                'href': 'content.xhtml',
                'content': content_html,
                'title': 'Content'
            })

        return spine_docs

    def _extract_chapter_text(self, text: str, chapter_title: str, next_chapter_title: Optional[str]) -> str:
        """
        Extract text for a specific chapter.

        Finds the chapter title in text and extracts everything until the next chapter.
        """
        # Find chapter start
        chapter_start = text.find(chapter_title)
        if chapter_start == -1:
            logger.warning(f"Could not find chapter title in text: {chapter_title}")
            return ""

        # Find chapter end (next chapter or end of text)
        if next_chapter_title:
            chapter_end = text.find(next_chapter_title, chapter_start + len(chapter_title))
            if chapter_end == -1:
                chapter_end = len(text)
        else:
            chapter_end = len(text)

        return text[chapter_start:chapter_end]

    def _chapter_to_html(self, chapter_title: str, paragraphs: List[str], book_title: str) -> str:
        """Convert chapter title and paragraphs to HTML document."""
        html_parts = [
            '<!DOCTYPE html>',
            '<html xmlns="http://www.w3.org/1999/xhtml">',
            '<head>',
            f'    <title>{self._escape_html(chapter_title)}</title>',
            '    <meta charset="utf-8"/>',
            '</head>',
            '<body>',
            f'    <h2>{self._escape_html(chapter_title)}</h2>',
        ]

        # Add each paragraph (skip first if it's the chapter title)
        for para in paragraphs:
            # Skip if paragraph is just the chapter title
            if para.strip() == chapter_title.strip():
                continue

            escaped_para = self._escape_html(para)
            html_parts.append(f'    <p>{escaped_para}</p>')

        html_parts.extend([
            '</body>',
            '</html>'
        ])

        return '\n'.join(html_parts)

    def _split_paragraphs(self, text: str) -> List[str]:
        """
        Split text into paragraphs.
        Paragraph = separated by blank lines (2+ newlines).
        """
        # Split on 2+ newlines
        raw_paragraphs = re.split(r'\n\s*\n+', text)

        # Clean up each paragraph
        paragraphs = []
        for para in raw_paragraphs:
            # Join lines within paragraph (remove single newlines)
            para = ' '.join(line.strip() for line in para.split('\n') if line.strip())

            # Only keep non-empty paragraphs with meaningful content
            if para and len(para) > 3:
                paragraphs.append(para)

        return paragraphs

    def _paragraphs_to_html(self, paragraphs: List[str], title: str) -> str:
        """Convert paragraphs to HTML document."""
        html_parts = [
            '<!DOCTYPE html>',
            '<html xmlns="http://www.w3.org/1999/xhtml">',
            '<head>',
            f'    <title>{self._escape_html(title)}</title>',
            '    <meta charset="utf-8"/>',
            '</head>',
            '<body>',
        ]

        # Add each paragraph
        for para in paragraphs:
            escaped_para = self._escape_html(para)
            html_parts.append(f'    <p>{escaped_para}</p>')

        html_parts.extend([
            '</body>',
            '</html>'
        ])

        return '\n'.join(html_parts)

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))

    def has_text_content(self, pdf_path: str) -> bool:
        """
        Check if PDF has extractable text (not a scanned image).

        Returns True if PDF has text content, False if scanned/empty.
        """
        try:
            pdf_doc = fitz.open(pdf_path)

            # Check first few pages for text
            pages_to_check = min(3, len(pdf_doc))
            total_text = ""

            for i in range(pages_to_check):
                page_text = pdf_doc[i].get_text().strip()
                total_text += page_text

            pdf_doc.close()

            # If we got substantial text, it's a text-based PDF
            has_text = len(total_text) > 100

            if not has_text:
                logger.warning(f"PDF appears to be scanned (no text found): {pdf_path}")

            return has_text

        except Exception as e:
            logger.error(f"Failed to check PDF text content: {e}")
            return False


# Validation function for upload endpoints
def validate_pdf_for_translation(pdf_path: str) -> tuple[bool, Optional[str]]:
    """
    Validate PDF is suitable for translation.

    Returns:
        (is_valid, error_message)
    """
    try:
        processor = SimplePDFProcessor()

        # Check if text-based
        if not processor.has_text_content(pdf_path):
            return False, "This appears to be a scanned PDF with no extractable text. Please upload a text-based PDF or EPUB."

        # Check if encrypted
        pdf_doc = fitz.open(pdf_path)
        if pdf_doc.is_encrypted:
            pdf_doc.close()
            return False, "This PDF is password-protected. Please upload an unprotected file."

        pdf_doc.close()
        return True, None

    except Exception as e:
        logger.error(f"PDF validation failed: {e}")
        return False, f"Failed to process PDF: {str(e)}"
