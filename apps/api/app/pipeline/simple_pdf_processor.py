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

        # Extract raw text
        raw_text = self._extract_text(pdf_doc)
        logger.info(f"Extracted {len(raw_text)} characters of text")

        # Clean artifacts
        clean_text = self._clean_artifacts(raw_text)
        logger.info(f"After cleaning: {len(clean_text)} characters")

        # Convert to HTML spine documents
        spine_docs = self._to_simple_html(clean_text, metadata['title'])
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

    def _to_simple_html(self, text: str, title: str) -> List[Dict]:
        """
        Convert cleaned text to simple HTML spine documents.

        Creates:
        1. Title page (if title exists)
        2. Content document(s) with paragraphs

        Future: Will split into chapters based on page breaks and patterns.
        For now: Single content document.
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

        # 2. Create content document
        # Remove page break markers (replace with paragraph breaks)
        text = re.sub(r'___PAGE_BREAK_\d+___', '', text)

        # Split into paragraphs (double newline = paragraph break)
        paragraphs = self._split_paragraphs(text)

        # Build HTML content
        content_html = self._paragraphs_to_html(paragraphs, title)

        spine_docs.append({
            'id': 'content',
            'href': 'content.xhtml',
            'content': content_html,
            'title': 'Content'
        })

        return spine_docs

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
