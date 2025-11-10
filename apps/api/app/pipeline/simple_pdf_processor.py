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

        # Try TOC-based chapter detection first (most reliable)
        chapters = self._detect_chapters_from_toc(pdf_doc)

        if not chapters:
            # Fallback: pattern-based detection with cleaned text
            raw_text = self._extract_text(pdf_doc)
            logger.info(f"Extracted {len(raw_text)} characters of text")
            chapters = self._detect_chapters(raw_text)

        if chapters:
            logger.info(f"Detected {len(chapters)} chapters")
        else:
            logger.info("No chapters detected, using single document")

        # Extract and clean text
        clean_text, page_offsets = self._extract_clean_text_with_offsets(pdf_doc)
        logger.info(f"Extracted {len(clean_text)} characters (clean)")

        # Convert to HTML spine documents (with or without chapters)
        spine_docs = self._to_simple_html(clean_text, metadata['title'], chapters, page_offsets)
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

    def _detect_chapters_from_toc(self, pdf_doc) -> Optional[List[Dict]]:
        """
        Detect chapters using PDF's built-in Table of Contents.
        This is the most reliable method when available.

        Returns:
            List of chapter dicts with 'title', 'start_pos', 'page_num', or None
        """
        try:
            # Get TOC (outline/bookmarks)
            # simple=False returns: [level, title, page, metadata_dict]
            toc = pdf_doc.get_toc(simple=False)

            if not toc or len(toc) < 2:
                logger.info("No TOC found or too few entries")
                return None

            # Skip keywords - entries to ignore
            SKIP_TOC_ENTRIES = [
                'CONTENTS', 'TABLE OF CONTENTS', 'INDEX',
                'ABOUT THE AUTHOR', 'ALSO BY', 'BACK ADS',
                'COPYRIGHT', 'ABOUT THE PUBLISHER',
                'ACKNOWLEDGMENTS', 'DEDICATION'
            ]

            # Filter to level 1 chapters only (top-level headings)
            chapters = []
            for entry in toc:
                level = entry[0]
                title = entry[1]
                page_num = entry[2]

                if level == 1:  # Top-level chapters only
                    # Skip metadata/back matter entries
                    if any(skip.lower() in title.lower() for skip in SKIP_TOC_ENTRIES):
                        continue

                    # PyMuPDF page numbers are 1-indexed in TOC
                    page_idx = max(0, page_num - 1)
                    chapters.append({
                        'title': title.strip(),
                        'page_num': page_idx,
                        'start_pos': None  # Will be calculated with offsets
                    })

            if len(chapters) >= 2:
                logger.info(f"Found {len(chapters)} chapters from TOC: {[c['title'] for c in chapters]}")
                return chapters

            logger.info("TOC has < 2 chapters after filtering, not using")
            return None

        except Exception as e:
            logger.warning(f"Failed to extract TOC: {e}")
            return None

    def _extract_clean_text_with_offsets(self, pdf_doc) -> tuple[str, Dict[int, int]]:
        """
        Extract text from PDF with:
        1. Header/footer removal (frequency analysis)
        2. Page-to-offset mapping for reliable chapter splitting
        3. Improved paragraph shaping

        Returns:
            (clean_text, page_offsets) where page_offsets maps page_num -> char position
        """
        # Step 1: Extract all pages
        pages_text = []
        for page_num in range(len(pdf_doc)):
            page = pdf_doc[page_num]
            text = page.get_text()
            pages_text.append(text)

        # Step 2: Detect and remove repeated headers/footers
        headers, footers = self._detect_headers_footers(pages_text)

        # Step 3: Build clean text with offset map
        page_offsets = {}
        clean_pages = []
        current_offset = 0

        for page_num, text in enumerate(pages_text):
            # Store offset for this page
            page_offsets[page_num] = current_offset

            # Remove headers/footers
            lines = text.split('\n')
            clean_lines = []

            for line in lines:
                line_stripped = line.strip()
                # Skip headers, footers, and page numbers
                if line_stripped in headers or line_stripped in footers:
                    continue
                if re.match(r'^\s*\d+\s*$', line_stripped):  # Lone page numbers
                    continue
                clean_lines.append(line)

            page_text = '\n'.join(clean_lines)

            # Improve paragraph shaping
            page_text = self._shape_paragraphs(page_text)

            clean_pages.append(page_text)
            current_offset += len(page_text) + 2  # +2 for \n\n between pages

        # Join all pages
        clean_text = '\n\n'.join(clean_pages)

        return clean_text, page_offsets

    def _detect_headers_footers(self, pages_text: List[str]) -> tuple[set, set]:
        """
        Detect repeated headers and footers using frequency analysis.

        Returns:
            (headers_set, footers_set) - sets of repeated text to remove
        """
        if len(pages_text) < 3:
            return set(), set()

        # Count frequency of first/last lines
        first_lines = {}
        last_lines = {}

        for text in pages_text:
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            if not lines:
                continue

            # First 1-2 lines
            for line in lines[:2]:
                first_lines[line] = first_lines.get(line, 0) + 1

            # Last 1-2 lines
            for line in lines[-2:]:
                last_lines[line] = last_lines.get(line, 0) + 1

        # Find lines that appear on >= 50% of pages
        threshold = len(pages_text) * 0.5

        headers = {line for line, count in first_lines.items() if count >= threshold}
        footers = {line for line, count in last_lines.items() if count >= threshold}

        if headers:
            logger.info(f"Detected {len(headers)} repeated headers")
        if footers:
            logger.info(f"Detected {len(footers)} repeated footers")

        return headers, footers

    def _shape_paragraphs(self, text: str) -> str:
        """
        Improve paragraph formatting:
        - Fix end-of-line hyphenation
        - Normalize line endings
        - Collapse multiple blank lines
        """
        # De-hyphenate end-of-line breaks
        # "near-\nest" → "nearest"
        text = re.sub(r'(\w)-\s*\n\s*(\w)', r'\1\2', text)

        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # Collapse 3+ blank lines to 2 (paragraph break)
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text

    def _detect_chapters(self, text: str) -> Optional[List[Dict]]:
        """
        Detect chapter breaks in text.

        Uses multiple heuristics:
        1. "Part One", "Part Two" patterns
        2. "Prologue", "Epilogue", "Foreword" patterns
        3. "Chapter N" patterns
        4. Roman numerals (I., II., III., etc.)
        5. All-caps titles at page start
        6. Numbered patterns (1., 2., etc.)

        Returns:
            List of chapter dicts with 'title' and 'start_pos', or None if no chapters
        """
        chapters = []

        # Skip patterns - pages to ignore for chapter detection
        SKIP_KEYWORDS = [
            'CONTENTS', 'TABLE OF CONTENTS', 'INDEX',
            'COPYRIGHT', 'PUBLISHER', 'ISBN', 'PAGE',
            'ACKNOWLEDGMENTS', 'DEDICATION',
            'ALSO BY', 'ABOUT THE AUTHOR', 'BACK ADS'
        ]

        # Split text into pages using page break markers
        page_pattern = r'___PAGE_BREAK_(\d+)___'
        pages = re.split(page_pattern, text)

        # pages will be: [text_before_page0, page_num, text_of_page, page_num, text_of_page, ...]
        current_pos = 0

        for i in range(0, len(pages), 2):
            page_text = pages[i]
            page_num = int(pages[i-1]) if i > 0 else 0

            # Get first few lines of page (potential chapter title)
            lines = [l.strip() for l in page_text.strip().split('\n')[:10] if l.strip()]
            if not lines:
                current_pos += len(page_text)
                continue

            first_line = lines[0]

            # Skip metadata/TOC pages
            if any(skip in first_line.upper() for skip in SKIP_KEYWORDS):
                current_pos += len(page_text)
                continue

            # Check for chapter patterns
            chapter_title = None

            # Pattern 1: "Part One", "Part Two", etc.
            # Examples: "Part One", "Part Two", "PART ONE"
            if re.match(r'^(?:PART|Part)\s+(?:One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten|I+|V|1|2|3|4|5|6|7|8|9|10)$', first_line, re.IGNORECASE):
                chapter_title = first_line

            # Pattern 2: "Prologue", "Epilogue", "Foreword", "Preface", "Introduction"
            elif re.match(r'^(?:Prologue|Epilogue|Foreword|Preface|Introduction|Afterword)$', first_line, re.IGNORECASE):
                chapter_title = first_line

            # Pattern 3: "Chapter" followed by number or word
            # Examples: "Chapter 1", "Chapter One", "CHAPTER ONE"
            elif re.match(r'^(?:CHAPTER|Chapter)\s+([IVXLCDM\d]+|[A-Za-z]+)(?:\s*[:\-]?\s*(.*))?$', first_line):
                chapter_title = first_line

            # Pattern 4: Roman numerals (standalone or with text)
            # Examples: "I.", "II.", "III. CORALINE", "IV. THE BEGINNING"
            elif re.match(r'^[IVXLCDM]+\.$', first_line):
                # Standalone Roman numeral (common chapter marker)
                chapter_title = first_line
            elif re.match(r'^[IVXLCDM]+\.?\s+[A-Z]{2,}', first_line):
                # Roman numeral with following text
                chapter_title = first_line

            # Pattern 5: Numbered patterns
            # Examples: "1. The Story Begins", "2 The Adventure"
            elif re.match(r'^\d+\.?\s+[A-Z]', first_line):
                chapter_title = first_line

            # Pattern 6: All-caps title (at least 2 words or 10+ chars)
            # Examples: "LITTLE RED RIDING HOOD", "THE BEGINNING"
            # But skip if it looks like metadata
            elif first_line.isupper() and (len(first_line.split()) >= 2 or len(first_line) >= 10):
                if not any(skip in first_line.upper() for skip in SKIP_KEYWORDS):
                    # Additional check: make sure it's not a repeated header across multiple pages
                    chapter_title = first_line

            # Pattern 7: Title Case with sufficient length
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

    def _to_simple_html(self, text: str, title: str, chapters: Optional[List[Dict]] = None, page_offsets: Optional[Dict[int, int]] = None) -> List[Dict]:
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

        # 2. Create content documents (with or without chapters)
        if chapters and page_offsets:
            # Calculate start_pos from page_num using offsets
            for chapter in chapters:
                if chapter.get('start_pos') is None and 'page_num' in chapter:
                    chapter['start_pos'] = page_offsets.get(chapter['page_num'], 0)

            # Sort chapters by start_pos
            chapters.sort(key=lambda c: c.get('start_pos', 0))

            # Split into chapters using reliable offsets
            for i, chapter in enumerate(chapters):
                start_pos = chapter.get('start_pos', 0)
                end_pos = chapters[i + 1].get('start_pos', len(text)) if i + 1 < len(chapters) else len(text)

                # Extract chapter text by slicing
                chapter_text = text[start_pos:end_pos]

                if not chapter_text or len(chapter_text) < 10:
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

            # Check first several pages for text (some PDFs have blank cover pages)
            pages_to_check = min(10, len(pdf_doc))
            total_text = ""

            for i in range(pages_to_check):
                page_text = pdf_doc[i].get_text().strip()
                total_text += page_text

                # Early exit if we found enough text
                if len(total_text) > 500:
                    break

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
