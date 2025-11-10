# PDF Input Support - Simple Text Extraction Approach

**Strategy**: Text-only extraction with minimal structure detection
**Philosophy**: PDFs → Clean Text → Translate → Beautiful EPUB/PDF Output
**Timeline**: 4-6 days total

---

## Why This Approach?

### Previous Attempt - Complex Format Preservation
- ❌ Only 25% success rate on TOC extraction
- ❌ Only 25% success rate on chapter detection
- ❌ Fragile across diverse PDF formats
- ❌ Complex code with many edge cases

### New Approach - Simple Text Extraction
- ✅ Reliable text extraction (90%+ of text-based PDFs)
- ✅ Fast processing
- ✅ Minimal code complexity
- ✅ Consistent output quality
- ✅ Leverages existing excellent translation pipeline (90% code reuse)

### Key Insight
**Users care about translation quality, not PDF formatting preservation.**
Output quality matters more than input preservation.

---

## Architecture Overview

### Data Flow
```
PDF Upload
    ↓
Simple Text Extraction (NEW - PyMuPDF)
    ↓
Basic Cleanup (NEW - artifact removal)
    ↓
Convert to Simple HTML (NEW - paragraphs + basic chapters)
    ↓
[EXISTING PIPELINE - 100% REUSE]
    ↓
HTML Segmentation → Translation → Reconstruction
    ↓
EPUB/PDF/TXT Output Generation
```

### Code Reuse (90%)
```python
# NEW: Simple PDF text extractor (10% new code)
pdf_processor = SimplePDFProcessor()
html_docs = pdf_processor.process_pdf(pdf_path)

# REUSE: Existing segmenter (unchanged)
segmenter = HTMLSegmenter()
segments, maps = segmenter.segment_documents(html_docs)

# REUSE: Existing translator (unchanged)
orchestrator = TranslationOrchestrator()
translated, tokens, provider = orchestrator.translate_segments(segments)

# REUSE: Existing reconstructor (unchanged)
translated_docs = segmenter.reconstruct_documents(translated, maps, html_docs)

# REUSE: Existing output generator (unchanged)
output_generator.generate_all_outputs(translated_docs)
```

---

## Phase 1: Core Text Extraction (2 days)

### Goal
Extract clean, readable text from PDF files with minimal artifact pollution.

### Components to Build

#### 1.1 SimplePDFProcessor Class
**File**: `apps/api/app/pipeline/simple_pdf_processor.py`

**Responsibilities**:
- Extract text from PDF using PyMuPDF (fitz)
- Clean artifacts (page numbers, headers, footers)
- Detect basic structure (title, paragraphs)
- Convert to simple HTML format

**Key Methods**:
```python
class SimplePDFProcessor:
    def process_pdf(self, pdf_path: str) -> dict:
        """Main entry point - process PDF to HTML structure"""

    def _extract_text(self, pdf_path: str) -> str:
        """Extract raw text from PDF"""

    def _clean_artifacts(self, text: str) -> str:
        """Remove page numbers, headers, footers"""

    def _extract_title(self, pdf_doc) -> str:
        """Get title from metadata or first page"""

    def _to_simple_html(self, text: str, title: str) -> list[dict]:
        """Convert text to HTML documents (spine format)"""
```

#### 1.2 Artifact Removal
**Patterns to Remove**:
- Page numbers: `Page \d+`, `\d+ / \d+`, standalone numbers at line ends
- Headers/Footers: Repeated text across pages
- Extra whitespace: Multiple blank lines → single blank line

**What NOT to Remove**:
- Paragraph breaks (double newlines)
- Legitimate numbers in text
- Chapter markers

#### 1.3 Text to HTML Conversion
**Output Format** (compatible with existing HTMLSegmenter):
```python
[
    {
        'id': 'titlepage',
        'href': 'titlepage.xhtml',
        'content': '<html><body><h1>Book Title</h1></body></html>',
        'title': 'Title Page'
    },
    {
        'id': 'chapter_1',
        'href': 'chapter_1.xhtml',
        'content': '<html><body><p>Paragraph 1...</p><p>Paragraph 2...</p></body></html>',
        'title': 'Chapter 1'
    }
]
```

### Success Criteria
- ✅ Extract text from text-based PDFs
- ✅ Remove common artifacts (page numbers, headers)
- ✅ Preserve paragraph boundaries
- ✅ Extract title from metadata
- ✅ Output valid HTML structure compatible with HTMLSegmenter

### Testing
- Test with 3-4 diverse PDFs (fiction, non-fiction)
- Verify text quality (95%+ clean)
- Verify compatibility with existing pipeline

---

## Phase 2: Basic Chapter Detection (1-2 days)

### Goal
Detect chapter breaks to create multi-chapter HTML documents (not just one big file).

### Detection Heuristics

#### 2.1 Chapter Break Indicators
**Patterns** (in priority order):
1. **Page breaks at start of page** + significant whitespace
2. **"Chapter N" patterns**: "Chapter 1", "CHAPTER ONE", "1.", "I."
3. **All-caps text at page start** (potential chapter title)
4. **Large font size at page start** (if font data available)

#### 2.2 Implementation Strategy
```python
def detect_chapters(self, pdf_doc) -> list[dict]:
    """
    Returns: [
        {'page': 1, 'title': 'Chapter 1', 'text_start': 0},
        {'page': 15, 'title': 'Chapter 2', 'text_start': 1500},
        ...
    ]
    """
    chapters = []

    for page_num, page in enumerate(pdf_doc):
        text = page.get_text()

        # Check for chapter markers at page start
        if self._is_chapter_start(text, page_num):
            title = self._extract_chapter_title(text)
            chapters.append({
                'page': page_num,
                'title': title or f'Chapter {len(chapters) + 1}'
            })

    return chapters if len(chapters) > 1 else None
```

#### 2.3 Fallback Strategy
If chapter detection fails or finds 0-1 chapters:
- Create single HTML document with all content
- Still works perfectly with existing pipeline

### Success Criteria
- ✅ Detect chapters in well-structured PDFs (novels with clear breaks)
- ✅ Graceful fallback for PDFs without clear chapters
- ✅ No false positives (don't split mid-chapter)
- ✅ Generate separate HTML docs per chapter

### Testing
- Test with chapter-based books (novels)
- Test with non-chapter books (continuous text)
- Verify chapter titles extracted correctly

---

## Phase 3: Integration & Pricing (1 day)

### Goal
Integrate PDF upload into existing API endpoints and pricing logic.

### 3.1 File Upload Support
**File**: `apps/api/app/routes/upload.py` (or wherever EPUB upload happens)

**Changes Needed**:
```python
ALLOWED_EXTENSIONS = {'.epub', '.pdf'}

def validate_upload(file):
    if file.extension == '.pdf':
        # Validate it's text-based (not scanned)
        if not has_text_content(file):
            raise ValidationError("Scanned PDFs not supported. Please upload EPUB.")
```

### 3.2 Pricing Calculation
**File**: `apps/api/app/routes/checkout.py` (or pricing logic)

**PDF Text Extraction for Pricing**:
```python
if file_ext == '.pdf':
    processor = SimplePDFProcessor()
    text = processor.extract_text_for_pricing(pdf_path)
    char_count = len(text)
    estimated_tokens = char_count / 4
else:  # EPUB
    # existing EPUB pricing logic
```

### 3.3 Worker Integration
**File**: `apps/api/app/pipeline/worker.py`

**Update Translation Job**:
```python
def translate_document(job_id):
    job = get_job(job_id)

    # Download from R2
    local_path = download_from_r2(job.input_file_key)

    # Process based on file type
    if local_path.endswith('.pdf'):
        processor = SimplePDFProcessor()
        html_docs = processor.process_pdf(local_path)
        # Continue with existing pipeline

    else:  # EPUB
        processor = EPUBProcessor()
        book, html_docs = processor.read_epub(local_path)
        # existing EPUB flow

    # Common path from here (segmentation, translation, output generation)
    ...
```

### Success Criteria
- ✅ Accept PDF uploads alongside EPUB
- ✅ Validate PDF has text content
- ✅ Calculate accurate pricing for PDFs
- ✅ Process PDFs through worker pipeline
- ✅ Generate all outputs (EPUB, PDF, TXT)

---

## Phase 4: User Experience & Documentation (1 day)

### Goal
Set clear expectations and provide excellent UX for PDF uploads.

### 4.1 Upload UI Messaging
**Display on Upload Page**:
```
Supported formats: EPUB, PDF

Note on PDF uploads:
✓ Text-based PDFs only (scanned PDFs not supported)
✓ Text will be extracted and reformatted
✓ Original PDF formatting will not be preserved
✓ Output will have clean, professional formatting
```

### 4.2 Validation Feedback
**Error Messages**:
```python
VALIDATION_MESSAGES = {
    'scanned_pdf': "This appears to be a scanned PDF. Please upload a text-based PDF or EPUB file.",
    'encrypted_pdf': "This PDF is password-protected. Please upload an unprotected file.",
    'empty_pdf': "No text content found in this PDF. Please check the file.",
}
```

### 4.3 Documentation
**Add to User Guide**:
- PDF support overview
- What to expect (formatting not preserved)
- Best practices (EPUB preferred for complex formatting)
- Troubleshooting (scanned PDFs, encrypted PDFs)

### Success Criteria
- ✅ Clear messaging about PDF limitations
- ✅ Helpful error messages for common issues
- ✅ User guide documentation updated
- ✅ Expectation-setting prevents support issues

---

## Testing Strategy

### Unit Tests
```python
# tests/test_simple_pdf_processor.py

def test_extract_text_from_pdf():
    """Test basic text extraction"""

def test_clean_page_numbers():
    """Test artifact removal"""

def test_detect_chapters():
    """Test chapter detection"""

def test_to_html_format():
    """Test HTML conversion matches expected format"""
```

### Integration Tests
```python
# tests/test_pdf_pipeline.py

def test_pdf_to_epub_translation():
    """Full pipeline: PDF → Translation → EPUB output"""

def test_pdf_pricing_calculation():
    """Verify PDF pricing matches EPUB pricing logic"""
```

### Manual Testing
- Upload diverse PDFs (fiction, non-fiction, technical)
- Verify text extraction quality
- Check chapter detection accuracy
- Validate output quality (EPUB, PDF, TXT)
- Test in e-readers (Calibre, Apple Books)

---

## Success Metrics

### Technical Metrics
- ✅ 90%+ text extraction success rate (text-based PDFs)
- ✅ <5% artifact pollution in extracted text
- ✅ 70%+ chapter detection accuracy (for chapter-based books)
- ✅ 100% compatibility with existing translation pipeline

### User Experience Metrics
- ✅ Clear error messages for unsupported PDFs
- ✅ Accurate pricing (within 10% of actual tokens)
- ✅ Processing time comparable to EPUBs
- ✅ Output quality matches EPUB quality

### Code Quality Metrics
- ✅ 90%+ code reuse from existing pipeline
- ✅ <500 lines of new code
- ✅ Unit test coverage >80%
- ✅ No regressions in EPUB pipeline

---

## Risk Mitigation

### Risk 1: Scanned PDFs
**Impact**: Users upload scanned PDFs expecting them to work
**Mitigation**:
- Detect non-text PDFs early in validation
- Clear error message explaining limitation
- Suggest OCR tools or EPUB conversion

### Risk 2: Poor Text Extraction Quality
**Impact**: Garbage text breaks translation
**Mitigation**:
- Thorough artifact removal
- Quality validation before translation
- Allow user preview before payment (like current preview feature)

### Risk 3: No Chapter Detection
**Impact**: Entire book as single chapter (still works, but less ideal)
**Mitigation**:
- Fallback to single-document is acceptable
- Still produces valid, readable output
- Can improve detection in future iteration

### Risk 4: Unexpected PDF Formats
**Impact**: Some PDFs may not extract well
**Mitigation**:
- Comprehensive testing with diverse PDFs
- Clear expectations (EPUB preferred for best results)
- Graceful error handling with helpful messages

---

## Future Enhancements (Post-MVP)

### Phase 5: Enhanced Structure Detection (Optional)
- TOC extraction (if reliably detectable)
- Better heading hierarchy detection
- List and table structure preservation

### Phase 6: OCR Support (Optional)
- Integrate OCR for scanned PDFs
- Preprocessing pipeline for image-based PDFs
- May require significant additional work

### Phase 7: Advanced Formatting (Optional)
- Bold/italic preservation (if reliable)
- Better font size analysis for headings
- Quote detection and formatting

**Note**: These are OPTIONAL. The simple approach in Phases 1-4 provides 80% of value with 20% of complexity.

---

## Implementation Timeline

### Day 1-2: Phase 1 (Core Text Extraction)
- Build SimplePDFProcessor class
- Implement text extraction and cleanup
- Convert to HTML format
- Unit testing

### Day 3: Phase 2 (Chapter Detection)
- Implement chapter break detection
- Test with diverse PDFs
- Fallback strategy for no chapters

### Day 4: Phase 3 (Integration)
- Update upload endpoints
- Integrate pricing calculation
- Update worker pipeline
- Integration testing

### Day 5: Phase 4 (UX & Polish)
- Add UI messaging
- Write documentation
- Error message improvements
- Final testing

### Day 6: Buffer & Deployment
- Bug fixes
- Additional testing
- Deploy to production
- Monitor for issues

---

## Conclusion

This simple text-extraction approach provides:
- ✅ **Reliable PDF support** (90%+ success rate for text PDFs)
- ✅ **Minimal code complexity** (<500 lines new code)
- ✅ **Fast implementation** (4-6 days vs 6-8 weeks previous plan)
- ✅ **90% code reuse** (leverages existing excellent pipeline)
- ✅ **Clear user expectations** (no false promises about format preservation)
- ✅ **High-quality output** (same beautiful EPUB/PDF output as existing system)

**Bottom Line**: Users get translated PDFs as beautifully formatted EPUBs, which is what they actually want.
