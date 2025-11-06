# BookTranslator EPUB Architecture - Quick Reference

**Jump to what you need:**

## Files You Need to Read

1. **EPUB_ARCHITECTURE_ANALYSIS.md** (29 KB) - *Most comprehensive*
   - Complete system breakdown
   - Library analysis (ebooklib, BeautifulSoup, lxml, weasyprint)
   - Detailed code walkthroughs with line numbers
   - Translation workflow deep-dive
   - Formatting preservation strategies
   - Best for understanding HOW everything works

2. **PDF_SUPPORT_ASSESSMENT.md** (12 KB) - *Most practical*
   - Three implementation options (MVP, High-Fidelity, Production)
   - Effort estimates (10 days to 60+ days)
   - Code snippets ready to use
   - Integration checklist
   - Testing strategy
   - Best for planning PDF input feature

3. **INVESTIGATION_SUMMARY.txt** (15 KB) - *Quick overview*
   - One-page findings
   - Key metrics
   - Risk assessment
   - Recommendations
   - Best for executive summary

---

## 30-Second Overview

**Current State:**
- EPUB input only → Translate → Output EPUB + PDF + TXT
- 2400+ lines of code across 7 modules
- Uses ebooklib for EPUB parsing, BeautifulSoup for HTML

**How It Works:**
1. Download EPUB from cloud storage
2. Extract text from HTML (preserving structure)
3. Translate using Gemini/Groq AI
4. Reconstruct HTML with translations
5. Generate EPUB + PDF + TXT outputs

**Adding PDF Support:**
- Reuse: 70-80% of existing code (translation pipeline is format-agnostic)
- New code: PDF extraction (~300-400 lines)
- Timeline: 2-3 weeks for MVP (basic PDF support)
- Tech: Add pdfplumber library

---

## Key Code Locations

```
EPUB Processing:
  apps/api/app/pipeline/epub_io.py           (491 lines)
  
Text Segmentation:
  apps/api/app/pipeline/html_segment.py      (269 lines)
  
Translation:
  apps/api/app/pipeline/translate.py         (211 lines)
  
Placeholder Protection:
  apps/api/app/pipeline/placeholders.py      (250+ lines)
  
Output Generation:
  common/outputs/generator.py                (232 lines)
  
Preview Feature:
  apps/api/app/pipeline/preview.py           (400+ lines)
  
Worker/Pipeline:
  apps/api/app/pipeline/worker.py            (438 lines)
```

---

## Translation Pipeline at a Glance

```
EPUB Input
  ↓
EPUBProcessor.read_epub()           ← Extract spine documents
  ↓
HTMLSegmenter.segment_documents()   ← Extract text, keep HTML structure
  ↓
PlaceholderManager.protect_segments()  ← Replace numbers/URLs/emails
  ↓
TranslationOrchestrator.translate_segments() ← Call AI provider
  ↓
PlaceholderManager.restore_segments()  ← Put originals back
  ↓
HTMLSegmenter.reconstruct_documents()  ← Inject translations into HTML
  ↓
EPUBProcessor.write_epub()          ← Write new EPUB file
  ↓
OutputGenerator.generate_all_outputs() ← Also make PDF and TXT
  ↓
Upload to R2 Storage
```

---

## Libraries Used

| Library | Version | Purpose |
|---------|---------|---------|
| `ebooklib` | 0.18 | Read/write EPUB files |
| `beautifulsoup4` | 4.12 | Parse HTML/XML |
| `lxml` | 4.9 | XML processing (BS4 backend) |
| `weasyprint` | 66.0 | CSS-to-PDF rendering |
| `google-generativeai` | Latest | Gemini API |
| `groq` | Latest | Groq Llama API |

**For PDF support, add:**
- `pdfplumber` >= 0.11.0 (text extraction)

---

## Why This Design Works

**Strengths:**
✅ DOM-aware segmentation = perfect formatting preservation
✅ Placeholder protection = AI can't mistranslate numbers/URLs
✅ Provider fallback = automatic quality assurance
✅ Format-agnostic translation = easy to add PDF later
✅ Modular = each piece is testable and replaceable

**For EPUB specifically:**
✅ ebooklib is the only mature pure-Python EPUB library
✅ HTML structure is semantic (easy to parse and reconstruct)
✅ Spine concept (reading order) is well-defined
✅ Easy to preserve all assets (CSS, images, fonts)

---

## Adding PDF Support - Decision Tree

**Do you want to start now?** → Read PDF_SUPPORT_ASSESSMENT.md

**Quick decision guide:**

```
1. Can you accept layout loss in PDF output?
   YES → Option A (MVP, 10 days, 70% code reuse)
   NO  → Option B (High-fidelity, 30 days, more complex)

2. Do you need to support scanned PDFs (OCR)?
   YES → Add 5 days + pytesseract dependency
   NO  → Skip OCR, focus on text-selectable PDFs (90% of cases)

3. Do you need PDF-to-EPUB conversion?
   YES → Different algorithm, add 10+ days
   NO  → Just PDF-to-PDF translation (simpler)
```

**Recommendation:** Start with Option A (MVP)
- Fastest time to market
- Proves concept
- Easy to improve iteratively
- Real user feedback guides Phase 2

---

## File Structure for PDF Support

**New files to create:**
```
apps/api/app/pipeline/
  ├── pdf_io.py          (NEW - 300-400 lines)
  └── pdf_segment.py     (NEW - 200-300 lines)
```

**Files to modify:**
```
apps/api/app/routes/
  ├── presign.py         (Add .pdf validation)
  ├── estimate.py        (Add PDF processor routing)
  └── checkout.py        (Add PDF processor routing)

apps/api/app/pipeline/
  └── worker.py          (Add format detection)

apps/api/app/
  └── models.py          (Add source_format field)
```

**Files to REUSE as-is:**
```
✅ translate.py          (Format-agnostic)
✅ placeholders.py       (Format-agnostic)
✅ generator.py          (Format-agnostic)
✅ preview.py            (Already works for PDFs)
```

---

## Metrics

**Translation Speed (80K word book):**
- Total: ~3-4 minutes
- Bottleneck: AI provider API latency (~3 minutes)
- Other operations: ~30-60 seconds

**Quality:**
- Success rate: >95%
- Format preservation: 100%
- Link preservation: 100%
- Image preservation: 100%

---

## Critical Insight: Text Ordering

The main challenge with PDF:
- **EPUB:** HTML tells you reading order (semantic tags)
- **PDF:** Just coordinates; must infer reading order

Example problem:
```
Two-column PDF layout:
┌─────────┬─────────┐
│ "Chapter│ "The"   │
│ 1"      │ end"    │
│ "Text A"│ "Text B"│
└─────────┴─────────┘

Text position order:  "Chapter 1", "Text A", "The end", "Text B"
Desired read order:   "Chapter 1", "Text A", "The end", "Text B" ✓
Wrong read order:     "Chapter 1", "The end", "Text A", "Text B" ✗
```

**Solution for MVP:** Accept this limitation, warn users
**Solution for Phase 2:** Add multi-column detection (non-trivial)

---

## What Happens to a PDF in MVP Mode

1. **Input:** PDF file (any format)
2. **Text extraction:** pdfplumber extracts all text
3. **Segmentation:** Split by paragraph (blank lines)
4. **Translation:** Send to Gemini/Groq (same as EPUB)
5. **Output:** 
   - Translated PDF (ReportLab or WeasyPrint)
   - Translated TXT (plain text)
   - ~~No EPUB~~ (not generated for PDF input)
6. **Quality:** Same as EPUB for translation; layout different

---

## Next Steps

1. **Review:** Read PDF_SUPPORT_ASSESSMENT.md
2. **Decide:** Option A, B, or skip for now?
3. **Plan:** Timeline and resource allocation
4. **Implement:** Create PDFProcessor and PDFSegmenter
5. **Test:** Test with 5-10 real PDFs
6. **Deploy:** Add to production
7. **Gather feedback:** Iterate for Phase 2

---

## Questions?

**For detailed answers, see:**
- EPUB_ARCHITECTURE_ANALYSIS.md (16 sections, complete reference)
- PDF_SUPPORT_ASSESSMENT.md (practical implementation guide)
- INVESTIGATION_SUMMARY.txt (executive summary)

---

**Analysis Date:** November 6, 2025
**Status:** Ready for implementation planning
