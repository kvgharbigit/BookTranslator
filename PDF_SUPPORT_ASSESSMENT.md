# PDF Input Support - High-Quality Implementation Plan

**Decision: Implementing high-quality PDF translation with PyMuPDF from the start**

---

## Executive Summary

**Chosen Approach:** High-Quality PDF Support with Layout Preservation (6-8 weeks)

**Key Points:**
- ✅ **70% code reuse** - Core translation pipeline unchanged
- ✅ **PyMuPDF (fitz)** - Position-aware text extraction and PDF rendering
- ✅ **Layout preservation** - Fonts, images, colors, structure (80%+ target)
- ✅ **Same quality** - Translation quality equals EPUB workflow
- ✅ **Multi-format output** - PDF, EPUB, TXT from PDF input
- ✅ **Smart features** - Multi-column detection, font fitting, image preservation
- ⏱️ **Timeline** - 6-8 weeks (40 working days)
- 📝 **New code** - ~900-1000 lines (PDFProcessor + PDFSegmenter)

**Why High-Quality Over MVP:**
- Users expect professional output quality
- Layout preservation differentiates from competitors
- PyMuPDF is proven and well-documented
- Foundation for future enhancements (OCR, advanced tables)
- 70% code reuse makes it feasible in reasonable timeline

---

## Current State

BookTranslator currently:
- **Input:** EPUB files only
- **Output:** EPUB, PDF, TXT
- **Core:** 2400+ lines of pipeline code across 7 key modules

---

## Code Reusability Assessment

### Can Directly Reuse (80-90%)

```
✅ TranslationOrchestrator    (~200 lines) - Format-agnostic translation
✅ PlaceholderManager         (~250 lines) - Placeholder protection
✅ OutputGenerator            (~230 lines) - Multi-format output
✅ Worker pipeline structure  (~400 lines) - Job management
✅ Provider integration       (~150 lines) - AI provider handling
```

**These components work with ANY source material that's been converted to structured text.**

### Must Adapt/Create (10-20%)

```
❌ EPUBProcessor              → Create PDFProcessor (new, ~300-400 lines)
❌ HTMLSegmenter            → Create PDFSegmenter (new, ~200-300 lines)
❌ Preview generation       → Create PDFPreviewService (new, ~150 lines)
```

---

## High-Quality Implementation Architecture

### Technology Stack

```python
PyMuPDF (fitz) >= 1.23.0    # Native text extraction & PDF rendering (primary)
arabic-reshaper >= 3.0.0    # RTL text shaping (Arabic, Hebrew)
python-bidi >= 0.4.2        # BiDi algorithm for RTL languages
pikepdf >= 8.0.0            # PDF sanitization & security validation
Noto fonts (subset)         # Embedded font family (Serif/Sans/CJK/Arabic/Hebrew)
pdfplumber >= 0.11.0        # Optional: sanity checks behind feature flag
```

**Key Decision: Use PyMuPDF end-to-end**
- Single engine for extraction + rendering = no drift
- Native `page.get_text("rawdict")` gives blocks/lines/spans with complete metadata
- Native `page.insert_textbox()` handles overflow/wrapping automatically
- Real redaction via `page.add_redact_annot()` removes source text cleanly

### Component Overview

**New Components (900-1000 lines total):**
1. **PDFProcessor** (~400-500 lines) - Extract/write PDFs with formatting
2. **PDFSegmenter** (~300-400 lines) - Reading order detection & segmentation
3. **Worker Integration** (~100 lines) - Format detection & routing
4. **Validation** (~100 lines) - Scan detection & security checks

**Reused Components (1800+ lines):**
- ✅ TranslationOrchestrator - Core translation logic
- ✅ PlaceholderManager - Protect numbers, URLs, emails
- ✅ Provider system - Gemini/Groq fallback
- ✅ OutputGenerator - Multi-format output creation
- ✅ Worker infrastructure - Queue, progress, email
- ✅ Storage, DB, API routes - Minimal changes

---

## Architecture Comparison: EPUB vs PDF

### EPUB Processing (Existing)
```
┌─────────────┐
│ EPUB File   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────┐
│ EPUBProcessor           │  Extract HTML documents
│ - Read spine documents  │  with semantic structure
│ - Parse HTML/CSS        │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ HTMLSegmenter           │  Extract text from
│ - DOM-aware extraction  │  HTML nodes
│ - Preserve structure    │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ TranslationOrchestrator │  ⭐ FORMAT-AGNOSTIC
│ - Translate segments    │  ⭐ 100% REUSABLE
│ - Placeholder protection│
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ HTMLSegmenter           │  Reconstruct HTML
│ - Reconstruct documents │  with translated text
│ - Preserve DOM tree     │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ EPUBProcessor           │  Generate outputs
│ - Write EPUB            │  (EPUB, PDF, TXT)
│ - Generate PDF/TXT      │
└─────────────────────────┘
```

### PDF Processing (New)
```
┌─────────────┐
│ PDF File    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────┐
│ PDFProcessor            │  Extract text blocks
│ - Extract text blocks   │  with positions & styles
│ - Capture positions     │
│ - Get font metadata     │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ PDFSegmenter            │  Order text by reading
│ - Detect columns        │  logic (top→bottom,
│ - Sort reading order    │  left→right per column)
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ TranslationOrchestrator │  ⭐ SAME AS EPUB
│ - Translate segments    │  ⭐ ZERO CHANGES
│ - Placeholder protection│
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ PDFSegmenter            │  Map translated text
│ - Reconstruct blocks    │  back to positions
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ PDFProcessor            │  Render translated PDF
│ - Write PDF             │  + generate EPUB/TXT
│ - Fit text in bounds    │
│ - Preserve images       │
└─────────────────────────┘
```

### Key Insight
**The core translation logic is identical** - both pipelines convert input to `List[str]`, translate, then reconstruct. The difference is only in **extraction** (structured HTML vs positioned text) and **reconstruction** (DOM tree vs positioned rendering).

---

## Detailed Architecture

### 1. PDFProcessor (`apps/api/app/pipeline/pdf_io.py`)

**Responsibilities:**
- Extract text blocks with position, font, color metadata
- Validate PDFs (detect scans, security issues)
- Reconstruct PDFs with translated text at original positions
- Handle font sizing/fitting when text length changes

**Key Methods:**

```python
class PDFProcessor:
    def __init__(self):
        self.max_file_size_mb = 100
        self.font_policy = FontPolicy()  # Manages Noto font embedding

    def validate_pdf_safety(self, pdf_path: str) -> Dict[str, Any]:
        """
        Comprehensive validation with actionable feedback.

        Returns: {
            'ok': bool,
            'reason': str,
            'is_scanned': bool,      # <100 words in sample
            'has_js': bool,          # Embedded JavaScript
            'has_forms': bool,       # XFA/AcroForms
            'page_count': int,
            'needs_flatten': bool    # Interactive elements to flatten
        }
        """
        # Use pikepdf for security validation
        # Sample 5 pages to detect scans quickly
        # Reject/flatten interactive PDFs

    def read_pdf(self, pdf_path: str) -> Tuple[fitz.Document, List[Dict]]:
        """
        Extract text blocks with complete styling metadata.
        Uses page.get_text("rawdict") for native PyMuPDF extraction.

        Returns: (pdf_doc, blocks)

        blocks = [
            {
                'page': 0,
                'bbox': (100.0, 50.0, 300.0, 80.0),  # Normalized coords
                'font': 'Helvetica-Bold',
                'size': 24.0,
                'color': (0.0, 0.0, 0.0),           # RGB 0..1
                'text': 'Chapter One\n',            # Preserves \n
                'flags': {
                    'bold': True,
                    'italic': False,
                    'superscript': False
                },
                'role': 'heading',  # body|heading|list|caption|header|footer
                'rotation': 0,      # Page rotation applied
                'block_id': 'p0_b0_l0_s0'
            },
            ...
        ]
        """
        doc = fitz.open(pdf_path)
        blocks = []

        for page_num in range(len(doc)):
            page = doc[page_num]

            # Normalize rotation to upright
            normalized_blocks = self._extract_normalized_blocks(page, page_num)
            blocks.extend(normalized_blocks)

        return doc, blocks

    def _extract_normalized_blocks(self, page: fitz.Page, page_num: int) -> List[Dict]:
        """
        Extract with rotation normalization.
        Handle page.rotation and per-object transforms.
        """
        raw = page.get_text("rawdict", flags=11)  # Preserve whitespace & structure
        rotation = page.rotation

        # Extract blocks/lines/spans and normalize bboxes
        # Apply rotation matrix to get upright coordinates
        # Tag role (heading vs body) using font size z-score

    def write_pdf(
        self,
        original_doc: fitz.Document,
        translated_blocks: List[Dict],
        output_path: str
    ) -> bool:
        """
        Reconstruct PDF with translated text.

        Process:
        1. Copy original pages (preserves images, vectors, links)
        2. Apply real redaction (not white rectangles) to text areas
        3. Insert translated text with native overflow handling
        4. Embed Noto fonts (subsetted per document)
        """
        new_doc = fitz.open()

        for page_num in range(len(original_doc)):
            original_page = original_doc[page_num]
            new_page = new_doc.new_page(
                width=original_page.rect.width,
                height=original_page.rect.height
            )

            # Copy page as base (keeps images, vectors)
            new_page.show_pdf_page(new_page.rect, original_doc, page_num)

            # Get blocks for this page
            page_blocks = [b for b in translated_blocks if b['page'] == page_num]

            # Redact original text (removes selectable source text)
            for block in page_blocks:
                new_page.add_redact_annot(block['bbox'], fill=(1, 1, 1))
            new_page.apply_redactions()

            # Insert translated text
            for block in page_blocks:
                self._insert_text_with_fitting(new_page, block)

        new_doc.save(output_path, garbage=4, deflate=True)
        return True

    def _insert_text_with_fitting(self, page: fitz.Page, block: Dict):
        """
        Smart text rendering with PyMuPDF native overflow handling.

        - Use page.insert_textbox() which returns overflow text
        - Max 15-20% font shrink, then stack multiple textboxes
        - Handle RTL with arabic_reshaper + python-bidi
        - Respect role for spacing (extra margin before headings)
        """
        text = block['text']
        bbox = fitz.Rect(block['bbox'])
        font = self.font_policy.get_font(block['font'])
        size = block['size']
        color = block['color']
        role = block.get('role', 'body')

        # Apply RTL shaping if needed
        if self._is_rtl(text):
            from arabic_reshaper import reshape
            from bidi.algorithm import get_display
            text = get_display(reshape(text))

        # Try original size first
        overflow = page.insert_textbox(
            bbox,
            text,
            fontname=font,
            fontsize=size,
            color=color,
            align=fitz.TEXT_ALIGN_LEFT,
            rotate=0
        )

        # If overflow, shrink font (max 20%)
        if overflow > -1 and overflow < len(text):
            size *= 0.85
            overflow = page.insert_textbox(bbox, text, fontname=font, fontsize=size, color=color)

            # Still overflowing? Stack multiple textboxes
            if overflow > -1:
                self._insert_multiline_overflow(page, bbox, text, font, size, color)

    def _is_rtl(self, text: str) -> bool:
        """Detect RTL languages (Arabic, Hebrew, Farsi)."""
        import unicodedata
        rtl_scripts = {'ARABIC', 'HEBREW'}
        for char in text[:100]:  # Sample
            script = unicodedata.name(char, '').split()[0] if char.strip() else ''
            if script in rtl_scripts:
                return True
        return False
```

**Estimated: 500-600 lines**

---

### 2. PDFSegmenter (`apps/api/app/pipeline/pdf_segment.py`)

**Responsibilities:**
- Sort text blocks by reading order
- Detect multi-column layouts
- Handle tables, sidebars, footnotes
- Create reconstruction map for translated text

**Key Methods:**

```python
class PDFSegmenter:
    def __init__(self):
        self.header_footer_cache = {}  # Detect repeated header/footer patterns
        self.font_stats_cache = {}     # Per-page font size statistics

    def segment_documents(
        self,
        blocks: List[Dict]
    ) -> Tuple[List[str], List[Dict]]:
        """
        Convert PDF blocks to ordered, role-tagged segments.

        Process:
        1. Detect headers/footers (repeated on 60%+ pages)
        2. Tag roles (heading, list, body) using heuristics
        3. Sort by reading order (banding + XY-cut)
        4. Merge lines with consistent spacing
        5. Build reconstruction map

        Returns: (segments, reconstruction_map)

        segments = ["Chapter One", "Once upon a time...", ...]
        reconstruction_map = [
            {
                'segment_idx': 0,
                'page': 0,
                'bbox': (100, 50, 300, 80),
                'font': 'Arial-Bold',
                'size': 24.0,
                'color': (0, 0, 0),
                'flags': {'bold': True, 'italic': False},
                'role': 'heading'
            },
            ...
        ]
        """
        # 1. Detect headers/footers
        self._detect_headers_footers(blocks)

        # 2. Tag roles (heading, list, body)
        self._tag_roles(blocks)

        # 3. Sort by reading order
        sorted_blocks = self._sort_by_reading_order(blocks)

        # 4. Merge lines into segments
        segments = []
        reconstruction_map = []

        for block in sorted_blocks:
            # Skip headers/footers
            if block.get('role') in ['header', 'footer']:
                continue

            segments.append(block['text'])
            reconstruction_map.append({
                'segment_idx': len(segments) - 1,
                'page': block['page'],
                'bbox': block['bbox'],
                'font': block['font'],
                'size': block['size'],
                'color': block['color'],
                'flags': block['flags'],
                'role': block['role']
            })

        return segments, reconstruction_map

    def _detect_headers_footers(self, blocks: List[Dict]):
        """
        Detect repeated header/footer patterns.
        Tag blocks with role='header' or role='footer' if repeated on 60%+ pages.
        """
        # Group by page
        pages = {}
        for block in blocks:
            page_num = block['page']
            if page_num not in pages:
                pages[page_num] = []
            pages[page_num].append(block)

        total_pages = len(pages)

        # Find candidate patterns (top/bottom 10% of each page)
        candidates = {'top': {}, 'bottom': {}}

        for page_num, page_blocks in pages.items():
            if not page_blocks:
                continue

            # Sort by Y position
            sorted_blocks = sorted(page_blocks, key=lambda b: b['bbox'][1])

            # Top 10%
            page_height = max(b['bbox'][3] for b in page_blocks)
            top_blocks = [b for b in sorted_blocks if b['bbox'][1] < page_height * 0.1]
            bottom_blocks = [b for b in sorted_blocks if b['bbox'][3] > page_height * 0.9]

            # Normalize text (lowercase, strip digits/dates)
            for block in top_blocks:
                normalized = self._normalize_text(block['text'])
                if normalized not in candidates['top']:
                    candidates['top'][normalized] = 0
                candidates['top'][normalized] += 1

            for block in bottom_blocks:
                normalized = self._normalize_text(block['text'])
                if normalized not in candidates['bottom']:
                    candidates['bottom'][normalized] = 0
                candidates['bottom'][normalized] += 1

        # Tag blocks that appear on 60%+ pages
        threshold = total_pages * 0.6

        for block in blocks:
            normalized = self._normalize_text(block['text'])
            if candidates['top'].get(normalized, 0) >= threshold:
                block['role'] = 'header'
            elif candidates['bottom'].get(normalized, 0) >= threshold:
                block['role'] = 'footer'

    def _normalize_text(self, text: str) -> str:
        """Normalize for header/footer matching (remove page numbers, dates)."""
        import re
        # Lowercase
        text = text.lower().strip()
        # Remove digits
        text = re.sub(r'\d+', '', text)
        # Remove common date patterns
        text = re.sub(r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b', '', text)
        return text

    def _tag_roles(self, blocks: List[Dict]):
        """
        Tag blocks with role using heuristics.
        - heading: font size z-score > 1.5, or bold + centered
        - list: starts with ^\s*(\d+[\.\)]|[-•●])\s+
        - caption: small font (z-score < -1) + italic
        - body: default
        """
        # Calculate font size stats per page
        pages = {}
        for block in blocks:
            page = block['page']
            if page not in pages:
                pages[page] = []
            pages[page].append(block['size'])

        # Compute z-scores
        import statistics
        for block in blocks:
            if block.get('role'):  # Already tagged (header/footer)
                continue

            page = block['page']
            sizes = pages[page]
            mean_size = statistics.mean(sizes)
            stdev_size = statistics.stdev(sizes) if len(sizes) > 1 else 1

            z_score = (block['size'] - mean_size) / stdev_size if stdev_size > 0 else 0

            # Heading detection
            if z_score > 1.5 or (block['flags'].get('bold') and self._is_centered(block)):
                block['role'] = 'heading'
            # List detection
            elif self._is_list_item(block['text']):
                block['role'] = 'list'
            # Caption detection
            elif z_score < -1 and block['flags'].get('italic'):
                block['role'] = 'caption'
            else:
                block['role'] = 'body'

    def _is_centered(self, block: Dict) -> bool:
        """Check if block is horizontally centered on page."""
        bbox = block['bbox']
        # Assume page width ~600pt (typical)
        page_center = 300
        block_center = (bbox[0] + bbox[2]) / 2
        return abs(block_center - page_center) < 50

    def _is_list_item(self, text: str) -> bool:
        """Detect list items by pattern."""
        import re
        return bool(re.match(r'^\s*(\d+[\.\)]|[-•●])\s+', text))

    def _sort_by_reading_order(self, blocks: List[Dict]) -> List[Dict]:
        """
        Advanced reading order detection using banding + XY-cut.

        Process:
        1. Group by page
        2. Detect columns via x-centroid clustering
        3. Sort columns left-to-right
        4. Within columns: sort top-to-bottom
        5. Merge lines with consistent spacing
        """
        sorted_blocks = []

        # Group by page
        pages = {}
        for block in blocks:
            page = block['page']
            if page not in pages:
                pages[page] = []
            pages[page].append(block)

        for page_num in sorted(pages.keys()):
            page_blocks = pages[page_num]

            # Detect columns via banding (x-centroid gaps)
            columns = self._detect_columns_banding(page_blocks)

            # Sort columns left-to-right
            columns.sort(key=lambda col: min(b['bbox'][0] for b in col))

            # Sort within each column top-to-bottom
            for column in columns:
                column.sort(key=lambda b: (b['bbox'][1], b['bbox'][0]))
                sorted_blocks.extend(column)

        return sorted_blocks

    def _detect_columns_banding(self, blocks: List[Dict]) -> List[List[Dict]]:
        """
        Detect columns using x-centroid clustering.
        Find gaps > 80pt between centroids = column boundary.
        """
        if not blocks:
            return []

        # Compute x-centroids
        centroids = [(b, (b['bbox'][0] + b['bbox'][2]) / 2) for b in blocks]
        centroids.sort(key=lambda x: x[1])

        # Detect gaps
        columns = []
        current_column = [centroids[0][0]]

        for i in range(1, len(centroids)):
            prev_centroid = centroids[i-1][1]
            curr_centroid = centroids[i][1]

            if curr_centroid - prev_centroid > 80:  # Column gap
                columns.append(current_column)
                current_column = [centroids[i][0]]
            else:
                current_column.append(centroids[i][0])

        if current_column:
            columns.append(current_column)

        return columns

    def reconstruct_documents(
        self,
        translated_segments: List[str],
        reconstruction_map: List[Dict],
        original_blocks: List[Dict]
    ) -> List[Dict]:
        """
        Map translated segments back to styled blocks.

        Returns: translated_blocks with same structure as original
        """
        translated_blocks = []

        for i, segment in enumerate(translated_segments):
            if i >= len(reconstruction_map):
                break

            map_entry = reconstruction_map[i]

            translated_blocks.append({
                'text': segment,
                'page': map_entry['page'],
                'bbox': map_entry['bbox'],
                'font': map_entry['font'],
                'size': map_entry['size'],
                'color': map_entry['color'],
                'flags': map_entry['flags'],
                'role': map_entry['role']
            })

        return translated_blocks
```

**Estimated: 400-500 lines**

---

### 3. Worker Integration (`apps/api/app/pipeline/worker.py`)

**Changes to existing `translate_epub()` → `translate_document()`:**

```python
def translate_document(job_id: str):
    """Universal worker for EPUB or PDF translation."""

    # ... existing job setup ...

    # DETECT FILE TYPE
    file_type = 'pdf' if source_key.endswith('.pdf') else 'epub'

    with tempfile.TemporaryDirectory() as temp_dir:
        input_path = os.path.join(temp_dir, f"input.{file_type}")

        # Download file
        storage.download_file(source_key, input_path)

        # BRANCH BY FORMAT
        if file_type == "epub":
            # Existing EPUB pipeline (unchanged)
            processor = EPUBProcessor()
            segmenter = HTMLSegmenter()
            original_book, spine_docs = processor.read_epub(input_path)
            segments, reconstruction_maps = segmenter.segment_documents(spine_docs)

        elif file_type == "pdf":
            # New PDF pipeline
            from app.pipeline.pdf_io import PDFProcessor
            from app.pipeline.pdf_segment import PDFSegmenter

            processor = PDFProcessor()
            segmenter = PDFSegmenter()

            # Validate PDF
            validation = processor.validate_pdf_safety(input_path)
            if not validation['ok']:
                raise Exception(f"PDF validation failed: {validation['reason']}")

            # Extract PDF blocks with complete styling
            original_doc, blocks = processor.read_pdf(input_path)

            # Segment with role tagging and reading order
            segments, reconstruction_map = segmenter.segment_documents(blocks)

        # SAME TRANSLATION PIPELINE (no changes!)
        orchestrator = TranslationOrchestrator()
        translated_segments, tokens, provider = await orchestrator.translate_segments(
            segments=segments,
            target_lang=target_lang,
            primary_provider=primary_provider,
            fallback_provider=fallback_provider,
            progress_callback=update_translation_progress
        )

        # RECONSTRUCT BY FORMAT
        if file_type == "epub":
            translated_docs = segmenter.reconstruct_documents(
                translated_segments, reconstruction_maps, spine_docs
            )
            # Generate EPUB + PDF + TXT outputs
            _generate_outputs_from_epub(...)

        elif file_type == "pdf":
            translated_blocks = segmenter.reconstruct_documents(
                translated_segments, reconstruction_map, text_blocks
            )
            # Write translated PDF
            output_pdf = os.path.join(temp_dir, f"{job_id}.pdf")
            processor.write_pdf(original_doc, translated_blocks, output_pdf)

            # Generate additional formats (EPUB, TXT)
            _generate_outputs_from_pdf(...)
```

**Estimated: 100 lines of changes**

---

## Key Technical Challenges

### 1. Text Ordering Problem
**Complexity:** Hard

PDF doesn't store reading order. You must infer it from:
- Visual coordinates (top-to-bottom, left-to-right)
- Text clustering
- Column detection
- Multi-column handling

```
Real world example - two-column layout:

Page PDF coordinates:
┌─────────┬─────────┐
│ Col A1  │ Col B1  │
│ Col A2  │ Col B2  │
└─────────┴─────────┘

Correct reading order: A1, A2, B1, B2
Wrong reading order:   A1, B1, A2, B2 (line-by-line)
```

### 2. Formatting Preservation
**Complexity:** Hard

EPUB = semantic markup (easy)
```html
<h1>Chapter 1</h1>    <!-- Clearly a heading -->
<p>Text here</p>      <!-- Clearly a paragraph -->
<em>Emphasized</em>   <!-- Clearly emphasized -->
```

PDF = visual rendering (hard)
```
"Chapter 1"           /* Just text at position (100, 200) */
                      /* Must infer: is it a heading? */
Font size: 24pt       /* Infer from coordinates + font info */
Bold: yes             /* Infer from font metrics */
```

### 3. Image Handling
**Complexity:** Medium

EPUB images:
- Referenced separately
- Extractable with one command
- Paths known
- Easy to include in output

PDF images:
- Embedded in content stream
- Complex extraction (graphics state needed)
- Positioning relative (not absolute)
- Quality loss on extraction

### 4. Scanned PDFs (OCR)
**Complexity:** Medium+

- Require pytesseract + tesseract binary
- Additional dependency complexity
- Slower processing
- Lower accuracy than native PDFs
- Consider: should this be supported?

---

## Implementation Timeline (6-8 Weeks)

### Week 1-2: Core PDF Processing
**Goal:** Extract and validate PDFs with formatting metadata

Tasks:
- [ ] Install and configure PyMuPDF
- [ ] Implement `PDFProcessor.validate_pdf_safety()`
  - File size checks
  - Scan detection (reject image-only PDFs)
  - JavaScript/form security validation
- [ ] Implement `PDFProcessor.read_pdf()`
  - Extract text blocks with bounding boxes
  - Capture font names, sizes, colors
  - Handle multi-page documents
- [ ] Unit tests for PDF extraction
- [ ] Test with 10-15 sample PDFs (various layouts)

**Deliverable:** PDFProcessor that extracts positioned text blocks

---

### Week 3-4: Segmentation & Reading Order
**Goal:** Smart text ordering and segmentation

Tasks:
- [ ] Implement `PDFSegmenter.segment_documents()`
- [ ] Implement `_sort_by_reading_order()`
  - Page-level grouping
  - Column detection algorithm
  - Top-to-bottom, left-to-right sorting
- [ ] Implement `_detect_columns()`
  - X-coordinate clustering
  - Handle 1, 2, 3+ column layouts
  - Identify headers, footers, sidebars
- [ ] Handle edge cases
  - Tables embedded in text
  - Footnotes
  - Marginal notes
- [ ] Integration tests for segmentation
- [ ] Test reading order with multi-column PDFs

**Deliverable:** PDFSegmenter that produces correctly ordered segments

---

### Week 5-6: Text Fitting & PDF Rendering
**Goal:** Reconstruct PDFs with translated text

Tasks:
- [ ] Implement `PDFProcessor.write_pdf()`
  - Copy original pages (preserve images/graphics)
  - Redact original text areas
  - Insert translated text
- [ ] Implement `_insert_text_with_fitting()`
  - Measure text width in target font
  - Shrink font size if text doesn't fit (max 20% reduction)
  - Split to multiple lines for severe overflow
  - Preserve font family and color
- [ ] Image preservation validation
  - Verify images remain in correct positions
  - Test with image-heavy PDFs
- [ ] Handle special cases
  - Very long translations (German, Finnish)
  - RTL languages (Arabic, Hebrew)
  - Special characters and diacritics
- [ ] Integration tests for full pipeline

**Deliverable:** Working PDF translation with layout preservation

---

### Week 7-8: Testing, Polish & API Integration
**Goal:** Production-ready PDF support

Tasks:
- [ ] API route updates
  - Update `presign.py` to accept .pdf files
  - Update `estimate.py` for PDF token estimation
  - Update `checkout.py` for PDF processing
- [ ] Worker integration
  - Rename `translate_epub()` → `translate_document()`
  - Add format detection
  - Branch EPUB vs PDF pipelines
- [ ] Output generation
  - PDF → PDF (translated)
  - PDF → EPUB (convert structure)
  - PDF → TXT (extract plain text)
- [ ] Database schema updates
  - Add `source_format` column to Job model
  - Migration script
- [ ] Comprehensive testing
  - Test 50+ real-world PDFs
  - Various layouts: single-column, multi-column, mixed
  - Different languages (with varying text expansion)
  - Large files (100+ pages)
  - Edge cases (rotated text, embedded fonts)
- [ ] Performance optimization
  - Profile slow operations
  - Optimize column detection algorithm
  - Cache font metrics
- [ ] Documentation
  - Update README with PDF support
  - Add PDF-specific troubleshooting guide
  - Update API documentation

**Deliverable:** Production-ready PDF translation feature

---

## Phased Rollout Strategy

### Phase 1: Internal Testing (Week 7)
- Deploy to staging environment
- Test with internal team
- Gather feedback on edge cases
- Fix critical bugs

### Phase 2: Limited Beta (Week 8)
- Release to subset of users (10-20)
- Monitor error rates and user feedback
- Collect sample problematic PDFs
- Iterate on reading order algorithm

### Phase 3: Public Launch (Week 9+)
- Full deployment to production
- Marketing announcement
- Monitor performance and quality
- Plan iterative improvements

---

## Integration Points

### File Structure
```
apps/api/app/pipeline/
├── epub_io.py          (existing - EPUB)
├── pdf_io.py           (new - PDF extraction)
├── html_segment.py     (existing - HTML → segments)
├── pdf_segment.py      (new - PDF text → segments)
├── translate.py        (existing - REUSE)
├── placeholders.py     (existing - REUSE)
├── worker.py           (existing - MINIMAL CHANGES)
└── preview.py          (existing - REUSE for PDF preview)
```

### Worker Changes
```python
# In worker.py translate_epub() - rename to translate_document()

if source_key.endswith('.epub'):
    processor = EPUBProcessor()
    original_book, spine_docs = processor.read_epub(epub_path)
    segmenter = HTMLSegmenter()
elif source_key.endswith('.pdf'):
    processor = PDFProcessor()
    text, metadata = processor.read_pdf(pdf_path)
    # Create spine_docs structure from text + metadata
    segmenter = PDFSegmenter()

# Rest of pipeline stays the same
segments, reconstruction_maps = segmenter.segment_documents(...)
```

### Database Changes
```python
# In models.py Job class
source_format: str = Column(String, default="epub")  # "epub" or "pdf"

# For PDF inputs:
# - output_epub_key might be null (if user wanted just translated PDF)
# - output_pdf_key still populated
# - output_txt_key still populated
```

### API Changes
```python
# In presign.py
- Remove ".epub" file type check
- Accept both .epub and .pdf
- Validate MIME types: application/epub+zip, application/pdf

# In estimate.py / checkout.py
- Detect format from extension
- Use appropriate processor for token estimation
- Same pricing logic (word/token-based)

# In preview.py
- Already works! Just extract text and translate
- No changes needed (format-agnostic)
```

---

## Testing Strategy

### Unit Tests
```python
# tests/test_pdf_processor.py
def test_pdf_extraction():
    processor = PDFProcessor()
    text, metadata = processor.read_pdf('sample.pdf')
    assert len(text) > 0
    assert metadata['page_count'] > 0

def test_pdf_segmentation():
    segmenter = PDFSegmenter()
    segments = segmenter.segment_pdf_text(sample_text)
    assert all(len(s) > 3 for s in segments)
```

### Integration Tests
```python
# Full workflow test
def test_pdf_translation_workflow():
    # Upload PDF → Estimate → Checkout → Process → Download
    # Verify translated PDF is valid
    # Check format of text extraction
```

### Real-world Tests
- Test with various PDF types:
  - Native PDFs (text selectable)
  - Scanned PDFs (image-based, might skip initially)
  - Complex layouts (multi-column, tables)
  - Different encodings
  - Large files (100+ pages)

---

## Effort Breakdown (40 Working Days)

### Core Development (30 days)
```
Week 1-2:    Core PDF Processing (10 days)
             - PDFProcessor implementation
             - Validation and security checks
             - Text extraction with metadata

Week 3-4:    Segmentation & Reading Order (10 days)
             - PDFSegmenter implementation
             - Multi-column detection
             - Smart text ordering

Week 5-6:    Text Fitting & Rendering (10 days)
             - PDF reconstruction
             - Font sizing algorithms
             - Image preservation
```

### Integration & Testing (10 days)
```
Week 7-8:    API Integration & Testing (10 days)
             - Worker integration
             - API route updates
             - Comprehensive testing
             - Performance optimization
             - Documentation
```

### Total: 6-8 weeks (40 working days)

---

## Risk Assessment

### High Confidence ✅
- **PyMuPDF is mature and well-documented** - Used by thousands of production apps
- **70% code reuse** - Core translation pipeline completely unchanged
- **Similar architecture to EPUB** - Same pattern (extract → translate → reconstruct)
- **Team expertise** - Already mastered complex EPUB processing

### Medium Confidence ⚠️
- **Text ordering algorithms** - Well-documented, but edge cases exist
  - Mitigation: Start with simple heuristics, iterate based on real PDFs
- **Font fitting** - Text expansion varies by language
  - Mitigation: Conservative font shrinking (max 20%), multi-line fallback
- **Complex layouts** - Tables, sidebars, footnotes require smart detection
  - Mitigation: Test with diverse PDF samples early, iterate algorithm

### Low Risk (Out of Scope) 🚫
- **OCR for scanned PDFs** - Not supporting initially (reject with clear message)
- **Perfect pixel-perfect layout** - Accepting minor layout shifts
- **Form fields and interactive PDFs** - Reject these edge cases

### Known Limitations
1. **Text expansion overflow** - If translated text is >40% longer, may require font shrinking or line breaks
2. **Complex tables** - May not preserve perfect cell alignment
3. **Rotated text** - Initial version handles horizontal text only
4. **Embedded fonts** - May fallback to system fonts if embedding fails

---

## Success Criteria

### Week 2 Milestone
- ✅ PDFProcessor extracts text blocks with positions
- ✅ Validation rejects scanned PDFs
- ✅ Unit tests pass for 15+ sample PDFs

### Week 4 Milestone
- ✅ PDFSegmenter correctly orders text (1, 2, 3 column layouts)
- ✅ Reading order tests pass (95%+ accuracy)
- ✅ Edge cases handled: headers, footers, sidebars

### Week 6 Milestone
- ✅ PDF reconstruction works with layout preservation
- ✅ Images remain in correct positions
- ✅ Font fitting handles text expansion up to 40%
- ✅ Integration tests pass end-to-end

### Week 8 Milestone (Production Launch)
- ✅ PDF translation feature live in production
- ✅ API accepts .pdf files
- ✅ Translation quality equals EPUB quality
- ✅ 95%+ success rate on real-world PDFs
- ✅ Output preserves 80%+ of original layout
- ✅ Users can download PDF, EPUB, TXT outputs
- ✅ Performance: <5min for 100-page PDF
- ✅ Documentation complete

---

## Key Decisions Made

### 1. Scanned PDFs: NOT SUPPORTED (Initial Release)
**Decision:** Reject scanned/image-based PDFs with clear error message

**Rationale:**
- OCR adds complexity and dependencies (tesseract)
- Lower accuracy than native PDFs
- 90% of user PDFs are text-based
- Can add OCR in future iteration if demand exists

**Error Message:**
```
"This PDF appears to be scanned (image-based).
Please upload a PDF with selectable text, or use OCR
software to convert it first."
```

### 2. Output Formats: PDF + EPUB-Lite + TXT
**Decision:** Generate PDF (high-quality), EPUB-Lite, and TXT

**Rationale:**
- **PDF**: High-quality with layout preservation (primary output)
- **EPUB-Lite**: Simplified EPUB with headings, paragraphs, lists, images
  - ⚠️ **Not CSS parity** - No precise floats or complex layouts
  - Basic structure only: chapters, paragraphs, basic formatting
  - Set user expectations: "EPUB-Lite" not "EPUB with full fidelity"
- **TXT**: Plain text export (trivial, already have segments)

**EPUB-Lite Generation Strategy:**
```python
def generate_epub_lite_from_pdf(blocks: List[Dict], metadata: Dict) -> epub.EpubBook:
    """
    Generate simplified EPUB from PDF blocks.
    Structure: Headings → Chapters, Body → Paragraphs, Lists → <ul>/<ol>
    No CSS layout preservation - basic semantic HTML only.
    """
    book = epub.EpubBook()
    # Group by 'heading' role to create chapters
    # Convert role='list' → <li> elements
    # Embed images by page
    # No floats, no precise positioning
```

**User Communication:**
- Label as "EPUB-Lite (simplified structure)" in download
- FAQ: "EPUB from PDF won't match the layout precision of EPUB input"

### 3. Layout Preservation: 80%+ Target
**Decision:** Preserve most layout, accept minor shifts

**Rationale:**
- Perfect layout preservation not achievable (text length changes)
- 80% preservation provides professional output
- Users prioritize translation quality over pixel-perfect layout
- Can improve iteratively based on feedback

### 4. Reading Order: Smart Detection
**Decision:** Implement column detection and smart ordering

**Rationale:**
- Multi-column PDFs are common (books, academic papers)
- Poor reading order = incomprehensible translation
- Algorithm is well-documented and testable
- Critical for quality user experience

---

## Testing Strategy

### The 12 Golden PDFs Test Suite

Create a comprehensive test suite with diverse PDF layouts:

1. **Single-column novel** - Simple linear text (baseline)
2. **2-column academic journal** - Standard multi-column
3. **3-column magazine** - Complex column layout
4. **Mixed column layout** - Varying columns per page
5. **Heavy footnotes** - Bottom-of-page annotations
6. **CJK document** (Chinese/Japanese/Korean) - Non-Latin characters
7. **RTL document** (Arabic/Hebrew) - Right-to-left text
8. **Heavy headers/footers** - Repeated page elements
9. **Rotated pages** - Landscape orientation, mixed rotation
10. **Image-heavy brochure** - Text + image positioning
11. **Vector-heavy technical PDF** - Diagrams, charts, tables
12. **Long document** (300+ pages) - Performance test

### Reading Order Validation

**Metric: Kendall Tau (τ)**

Measure pairwise inversions to quantify reading order quality:

```python
def test_reading_order_accuracy():
    """
    Manual ground truth: Mark expected order in 3-4 pages per fixture.
    Compute Kendall-τ correlation between expected and actual.
    Target: τ > 0.95 (95% correct pairwise orderings)
    """
    for pdf in golden_pdfs:
        expected_order = load_ground_truth(pdf)
        actual_order = segmenter.segment_documents(processor.read_pdf(pdf))

        tau = kendalltau(expected_order, actual_order)
        assert tau > 0.95, f"Reading order failed for {pdf}: τ={tau}"
```

### Round-Trip Invariants

**Ensure translation pipeline integrity:**

```python
def test_round_trip_invariants():
    """Validate no content loss or duplication."""

    # 1. Token count preservation (±2%)
    original_tokens = count_tokens(cleaned_original_text)
    segment_tokens = count_tokens(' '.join(segments))
    assert abs(segment_tokens - original_tokens) / original_tokens < 0.02

    # 2. P95 block overflow rate < 3%
    overflow_count = sum(1 for b in blocks if b['overflow'] > 0)
    assert (overflow_count / len(blocks)) < 0.03

    # 3. No ghost text (redaction successful)
    output_text = output_pdf.get_text()
    assert original_language_words not in output_text

    # 4. Image preservation
    assert count_images(output_pdf) == count_images(original_pdf)
```

### International Text Validation

**RTL and CJK rendering must be visually correct:**

```python
def test_rtl_rendering():
    """Arabic/Hebrew must render correctly (not reversed)."""
    arabic_pdf = translate_pdf("test_arabic.pdf", target="en")

    # Extract first 100 chars
    rendered_text = arabic_pdf.pages[0].extract_text()

    # Verify RTL markers present (BiDi algorithm applied)
    assert has_rtl_markers(rendered_text)

    # Visual regression: compare to ground truth screenshot
    screenshot = render_page_to_image(arabic_pdf.pages[0])
    assert image_similarity(screenshot, "ground_truth_arabic.png") > 0.95

def test_cjk_rendering():
    """Chinese/Japanese must render as glyphs, not tofu (□□□)."""
    chinese_pdf = translate_pdf("test_chinese.pdf", target="en")

    # Check for tofu characters
    rendered_text = chinese_pdf.pages[0].extract_text()
    assert '□' not in rendered_text
    assert '\ufffd' not in rendered_text  # Replacement character

    # Verify Noto CJK font embedded
    fonts = chinese_pdf.get_fonts()
    assert any('Noto' in f and 'CJK' in f for f in fonts)
```

### Performance Benchmarks

**Target: <5 min for 100-page PDF**

```python
def test_performance_100_pages():
    """Measure per-page processing time."""
    start = time.time()

    pdf_doc, blocks = processor.read_pdf("100_page_test.pdf")
    extraction_time = time.time() - start

    segments, _ = segmenter.segment_documents(blocks)
    segmentation_time = time.time() - start - extraction_time

    # Translation time depends on provider (not tested here)

    # Reconstruction
    recon_start = time.time()
    processor.write_pdf(pdf_doc, translated_blocks, "output.pdf")
    reconstruction_time = time.time() - recon_start

    total_time = extraction_time + segmentation_time + reconstruction_time

    # Targets (excluding translation API time)
    assert extraction_time < 30  # <0.3s/page
    assert segmentation_time < 20  # <0.2s/page
    assert reconstruction_time < 50  # <0.5s/page
```

---

## UX Enhancements

### 1. 2-Page Preview Before Charging

**Reduce refunds by showing extraction quality upfront:**

```python
# In preview.py
def generate_pdf_preview(pdf_path: str, target_lang: str) -> Dict:
    """
    Generate 2-page preview showing source vs extracted reading order.
    User can verify quality before paying.
    """
    processor = PDFProcessor()
    segmenter = PDFSegmenter()

    doc, blocks = processor.read_pdf(pdf_path)

    # Extract first 2 pages
    page_0_blocks = [b for b in blocks if b['page'] == 0]
    page_1_blocks = [b for b in blocks if b['page'] == 1]

    # Show reading order
    ordered_0 = segmenter._sort_by_reading_order(page_0_blocks)
    ordered_1 = segmenter._sort_by_reading_order(page_1_blocks)

    # Translate first 300 words
    preview_segments = [b['text'] for b in (ordered_0 + ordered_1)[:20]]
    preview_text = ' '.join(preview_segments)[:1500]  # ~300 words

    translated_preview = translate_preview(preview_text, target_lang)

    return {
        'source_pages': [
            {'page': 0, 'text': [b['text'] for b in ordered_0]},
            {'page': 1, 'text': [b['text'] for b in ordered_1]}
        ],
        'translated_preview': translated_preview,
        'layout_confidence': calculate_layout_confidence(blocks)
    }

def calculate_layout_confidence(blocks: List[Dict]) -> str:
    """
    Estimate layout preservation quality.
    Returns: "high", "medium", "low"
    """
    # Heuristics:
    # - Single column, standard fonts → "high"
    # - 2-3 columns, no tables → "medium"
    # - Complex tables, rotated text → "low"

    num_columns = detect_max_columns(blocks)
    has_tables = any(b.get('is_table') for b in blocks)
    has_rotation = any(b.get('rotation', 0) != 0 for b in blocks)

    if num_columns == 1 and not has_tables:
        return "high"
    elif num_columns <= 3 and not has_tables and not has_rotation:
        return "medium"
    else:
        return "low"
```

**UI Flow:**
1. User uploads PDF
2. Show 2-page preview + layout confidence ("High quality preservation expected")
3. User clicks "Proceed" or "Cancel" before checkout
4. Reduces complaints about unexpected layout changes

### 2. Quick Scan Detection

**Reject scanned PDFs early with helpful guidance:**

```python
def quick_scan_detection(pdf_path: str) -> bool:
    """
    Sample 5 random pages, extract text.
    If <100 words total → likely scanned.
    """
    doc = fitz.open(pdf_path)
    total_pages = len(doc)

    # Sample 5 pages (or all if <5 pages)
    import random
    sample_indices = random.sample(range(total_pages), min(5, total_pages))

    total_words = 0
    for idx in sample_indices:
        page = doc[idx]
        text = page.get_text()
        total_words += len(text.split())

    return total_words < 100  # Threshold
```

**Error Message:**
```
"⚠️ This PDF appears to be scanned (image-based).

We detected very little text, indicating the PDF may be a scanned document.

Recommendations:
• Use Adobe Acrobat's OCR feature
• Try online tools: ocrmypdf.com, pdfescape.com
• Re-export from the original document if available

Once you have a text-based PDF, upload it again!"
```

### 3. Page Range Translation (Future Enhancement)

**Allow users to translate specific page ranges for long documents:**

```python
# In checkout.py
class TranslationRequest(BaseModel):
    file_key: str
    target_lang: str
    page_range: Optional[Tuple[int, int]] = None  # (start, end) inclusive

def estimate_cost_with_page_range(file_key: str, page_range: Optional[Tuple[int, int]]):
    """Calculate cost for specific page range."""
    if page_range:
        start, end = page_range
        # Extract only specified pages
        # Estimate tokens for that subset
```

**Benefits:**
- Reduce cost for users who only need specific chapters
- Faster processing for long documents
- Test feature before translating entire book

---

## Determinism & Caching

### Stable Segment IDs

**Enable cache hits for re-uploads:**

```python
def generate_segment_id(block: Dict) -> str:
    """
    Deterministic segment ID based on content + position.
    Format: p{page}_c{col}_b{block}_hash{content_hash}
    """
    import hashlib

    content_hash = hashlib.md5(
        block['text'].strip().encode('utf-8')
    ).hexdigest()[:8]

    return f"p{block['page']}_c{block.get('column', 0)}_b{block.get('block_num', 0)}_{content_hash}"

def cache_translation(segment_id: str, translation: str, provider: str):
    """Cache translated segments in Redis/DB."""
    cache_key = f"trans:{segment_id}:{provider}"
    redis.setex(cache_key, ttl=86400*30, value=translation)  # 30 days

def get_cached_translation(segment_id: str, provider: str) -> Optional[str]:
    """Retrieve cached translation if available."""
    cache_key = f"trans:{segment_id}:{provider}"
    return redis.get(cache_key)
```

**Benefits:**
- Re-uploading same PDF = instant delivery (cache hit)
- Partial cache hits for similar documents
- Reduce translation API costs

---

## Performance Optimizations

### 1. Page-by-Page Processing

**Don't load all pages into RAM simultaneously:**

```python
def read_pdf_streaming(pdf_path: str) -> Generator[List[Dict], None, None]:
    """
    Yield blocks page-by-page to avoid memory bloat.
    """
    doc = fitz.open(pdf_path)

    for page_num in range(len(doc)):
        page = doc[page_num]
        page_blocks = extract_normalized_blocks(page, page_num)

        yield page_blocks

        # Clear page from memory
        page = None
```

### 2. Font Width Caching

**Cache font metrics to avoid repeated calculations:**

```python
class FontWidthCache:
    def __init__(self):
        self.cache = {}  # (font, size, text_prefix) → width

    def get_text_width(self, text: str, font: str, size: float) -> float:
        """
        Cache width computations by (font, size, hash(text[:128]))
        """
        cache_key = (font, size, hash(text[:128]))

        if cache_key in self.cache:
            return self.cache[cache_key]

        # Compute width using PyMuPDF
        width = fitz.get_text_length(text, fontname=font, fontsize=size)

        self.cache[cache_key] = width
        return width
```

### 3. Parallel Page Extraction

**Parallelize extraction across CPU cores:**

```python
from concurrent.futures import ProcessPoolExecutor

def read_pdf_parallel(pdf_path: str) -> List[Dict]:
    """
    Extract pages in parallel up to CPU cores.
    Translation stays serialized (provider rate limits).
    """
    doc = fitz.open(pdf_path)
    total_pages = len(doc)

    with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
        futures = []

        for page_num in range(total_pages):
            future = executor.submit(extract_page_blocks, pdf_path, page_num)
            futures.append(future)

        all_blocks = []
        for future in futures:
            page_blocks = future.result()
            all_blocks.extend(page_blocks)

    return all_blocks

def extract_page_blocks(pdf_path: str, page_num: int) -> List[Dict]:
    """Process single page (called in subprocess)."""
    doc = fitz.open(pdf_path)
    page = doc[page_num]
    return extract_normalized_blocks(page, page_num)
```

**Performance Target:**
- Extraction: <0.3s/page (parallelized)
- Segmentation: <0.2s/page
- Translation: Variable (API-bound)
- Reconstruction: <0.5s/page
- **Total (100 pages, excluding translation)**: <60 seconds
- **Total (100 pages, including translation)**: <5 minutes

---

## Next Steps

### Immediate (This Week)
1. ✅ **Plan approved** - Document updated with high-quality approach
2. **Setup environment** - Install PyMuPDF, create branch
3. **Start implementation** - Begin Week 1 tasks (PDFProcessor)

### Week 1-2
- Implement core PDF extraction
- Build validation and security checks
- Test with sample PDFs

### Week 3-4
- Implement segmentation and reading order
- Build column detection algorithm
- Integration testing

### Week 5-6
- PDF reconstruction with text fitting
- Image preservation
- End-to-end testing

### Week 7-8
- API integration
- Performance optimization
- Documentation and launch

---

**Analysis Date:** November 6, 2025
**Decision:** High-quality PDF support with PyMuPDF
**Timeline:** 6-8 weeks (40 working days)
**Code Reuse:** 70% of existing pipeline
**Risk Level:** Medium (manageable with phased approach)

