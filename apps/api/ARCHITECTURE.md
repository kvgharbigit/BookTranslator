# BookTranslator API Architecture

## Overview

BookTranslator API is a background worker service that translates EPUB books and generates outputs in multiple formats. The system supports two output modes:

1. **Regular Translation** - Translated text only (EPUB, PDF, TXT)
2. **Bilingual Output** - Translation with original text as subtitles (EPUB, PDF, TXT)

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       User Request                           │
│                     (Web Interface)                          │
└──────────────────────┬───────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                           │
│              (Job Creation & Management)                     │
└──────────────────────┬───────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                    Redis Queue (RQ)                          │
│              (Job Queue & Scheduling)                        │
└──────────────────────┬───────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                   RQ Worker Process                          │
│              (apps/api/app/pipeline/worker.py)               │
│                                                              │
│  ┌────────────────────────────────────────────────┐         │
│  │  1. Read EPUB from R2 Storage                  │         │
│  │  2. Segment HTML into translatable chunks      │         │
│  │  3. Translate via LLM Provider                 │         │
│  │  4. Reconstruct HTML with translations         │         │
│  │  5. Generate Outputs (based on output_format)  │         │
│  │  6. Upload to R2 Storage                       │         │
│  │  7. Send Email with Download Links             │         │
│  └────────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

## Pipeline Flow

### Phase 1: Job Creation & Queuing

```
User Upload → FastAPI → Database → Redis Queue
                ↓
         Job Status: 'queued'
```

**Files:**
- `app/main.py` - FastAPI endpoints
- `app/models.py` - Job database model
- `app/pipeline/worker.py` - `translate_epub()` function

### Phase 2: EPUB Processing

```
Worker Picks Job → Download from R2 → Parse EPUB
                                           ↓
                                    Segment HTML
                                           ↓
                            Extract translatable text chunks
```

**Files:**
- `app/pipeline/epub_io.py` - EPUB reading/writing
- `app/pipeline/html_segment.py` - HTML segmentation

**Key Functions:**
- `EPUBProcessor.read_epub()` - Parse EPUB structure
- `HTMLSegmenter.segment_documents()` - Extract text segments

### Phase 3: Translation

```
Text Segments → LLM Provider → Translated Segments
                    ↓
        (Gemini / Groq / etc.)
```

**Files:**
- `app/pipeline/translate.py` - Translation orchestration
- `app/providers/` - LLM provider implementations
  - `gemini.py` - Google Gemini
  - `groq.py` - Groq
  - `base.py` - Provider interface

**Key Functions:**
- `translate_segments()` - Main translation function
- Provider-specific batch translation

### Phase 4: Output Generation

This is where the pipeline splits based on `output_format`:

#### Option 1: Translation Only (`output_format='translation'`)

```
Translated Segments
        ↓
Reconstruct HTML
        ↓
┌───────┴────────┬────────────┐
↓                ↓             ↓
EPUB            PDF           TXT
(Calibre)    (WeasyPrint)  (Plain Text)
```

#### Option 2: Bilingual Only (`output_format='bilingual'`)

```
Original + Translated Segments
        ↓
Create Bilingual HTML (subtitle format)
        ↓
┌───────┴────────┬────────────┐
↓                ↓             ↓
EPUB            PDF           TXT
(External CSS) (WeasyPrint)  (Formatted)
```

#### Option 3: Both (`output_format='both'`)

```
Generates ALL 6 files:
├── {job_id}.epub              (Translation only)
├── {job_id}.pdf               (Translation only - WeasyPrint)
├── {job_id}.txt               (Translation only)
├── {job_id}_bilingual.epub    (Bilingual with subtitles)
├── {job_id}_bilingual.pdf     (Bilingual with subtitles - WeasyPrint)
└── {job_id}_bilingual.txt     (Bilingual formatted)
```

## Detailed Pathway Breakdown

### Regular Translation Pathway

**Step-by-step:**

1. **Segment & Translate** (`worker.py:140-179`)
   - Segment HTML documents
   - Translate text via LLM
   - Reconstruct HTML with translations

2. **Generate EPUB** (`common/outputs/generator.py`)
   - Use original EPUB structure
   - Replace content with translations
   - Preserve all assets (images, CSS, metadata)

3. **Generate PDF** (`worker.py:555-563`)
   - ✨ **NEW: WeasyPrint approach**
   - Extract CSS from original EPUB
   - Convert HTML → PDF with WeasyPrint
   - Preserves typography and layout
   - **Fallback:** Uses Calibre if WeasyPrint fails

4. **Generate TXT** (`common/formatting/text.py`)
   - Extract plain text from HTML
   - Format with proper spacing
   - Clean, readable output

**Output Files:**
- `{job_id}.epub` - Standard EPUB format
- `{job_id}.pdf` - High-quality PDF via WeasyPrint
- `{job_id}.txt` - Plain text format

### Bilingual Pathway

**Step-by-step:**

1. **Create Bilingual HTML** (`worker.py:440-458`)
   - Take translated + original segments
   - Use `create_bilingual_documents()` function
   - Format: Translation with original as subtitle

   **Bilingual Format:**
   ```html
   <p>
       Translated text here
       <span class="bilingual-subtitle">Original text here</span>
   </p>
   ```

2. **Generate Bilingual EPUB** (`epub_io.py:write_bilingual_epub()`)
   - Create EPUB with bilingual HTML
   - **External CSS file** (EPUB standard)
   - CSS includes subtitle styling:
     ```css
     .bilingual-subtitle {
         font-size: 0.85em;
         color: #666;
         font-style: italic;
     }
     ```

3. **Generate Bilingual PDF** (`worker.py:466-512`)
   - ✨ **WeasyPrint HTML → PDF**
   - Preserves all CSS styling
   - Subtitles render correctly (small, gray, italic)
   - **Fallback:** EPUB → PDF via Calibre (loses CSS)

4. **Generate Bilingual TXT** (`worker.py:514-553`)
   - Parse bilingual HTML
   - Format as:
     ```
     Translated text
         (Original text)

     Next translated text
         (Next original text)
     ```

**Output Files:**
- `{job_id}_bilingual.epub` - Bilingual EPUB with subtitles
- `{job_id}_bilingual.pdf` - Bilingual PDF (CSS preserved)
- `{job_id}_bilingual.txt` - Formatted bilingual text

### Both Pathway

When `output_format='both'`, the worker generates **all 6 files**:

**Execution Flow** (`worker.py:_generate_both_outputs()`):

1. Generate **regular translation outputs** (3 files)
2. Generate **bilingual outputs** (3 files)
3. Upload all files to R2
4. Send email with 6 download links

**Important:** This is the most resource-intensive option but provides maximum flexibility for users.

## Key Technologies

### PDF Generation (WeasyPrint)

**Why WeasyPrint?**
- ✅ Superior CSS rendering vs Calibre
- ✅ Preserves bilingual subtitle styling
- ✅ Better typography and margins
- ✅ RTL language support
- ✅ Professional-quality output

**System Requirements:**
```toml
# nixpacks.toml (Railway deployment)
[phases.setup]
aptPkgs = [
    "libpango-1.0-0",
    "libpangocairo-1.0-0",
    "libcairo2",
    "libgdk-pixbuf2.0-0",
    "shared-mime-info"
]
```

**Local Development:**
```bash
brew install pango cairo gdk-pixbuf
export DYLD_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_LIBRARY_PATH"
```

### LLM Providers

**Supported:**
- Google Gemini (gemini-2.5-flash-lite)
- Groq (llama-3.3-70b-versatile)

**Provider Selection:**
- User chooses provider at job creation
- Cost tracked per provider
- Automatic retry on failures

### Storage (R2)

**Bucket Structure:**
```
epub-translator-production/
├── uploads/{uuid}/{filename}.epub     # User uploads
└── outputs/
    ├── {job_id}.epub                  # Translation outputs
    ├── {job_id}.pdf
    ├── {job_id}.txt
    ├── {job_id}_bilingual.epub        # Bilingual outputs
    ├── {job_id}_bilingual.pdf
    └── {job_id}_bilingual.txt
```

## File Organization

### Core Pipeline Files

```
apps/api/app/pipeline/
├── worker.py              # Main translation worker
├── epub_io.py             # EPUB read/write operations
├── html_segment.py        # HTML segmentation
├── bilingual_html.py      # Bilingual HTML generation
├── translate.py           # Translation orchestration
├── placeholders.py        # Protect HTML entities
└── preview.py             # Preview generation
```

### Output Generation

```
apps/api/app/
├── html_to_pdf.py         # WeasyPrint PDF generation
│   ├── convert_bilingual_html_to_pdf()  # For bilingual PDFs
│   └── convert_html_to_pdf()            # For regular PDFs
└── common/outputs/
    └── generator.py       # EPUB & TXT generation
```

### Provider Implementations

```
apps/api/app/providers/
├── base.py               # Provider interface
├── factory.py            # Provider factory
├── gemini.py             # Google Gemini
└── groq.py               # Groq
```

## Database Schema

### Job Model (`app/models.py`)

```python
class Job:
    id: str                    # UUID
    email: str                 # User email
    source_key: str            # R2 path to input EPUB
    output_format: str         # 'translation' | 'bilingual' | 'both'
    target_lang: str           # ISO language code (es, fr, de, etc.)
    source_lang: str           # Auto-detected or user-specified
    provider: str              # LLM provider (gemini, groq)
    status: str                # queued, processing, done, failed
    progress_step: str         # Current step (segmenting, translating, etc.)
    progress_percent: int      # 0-100

    # Output keys
    output_epub_key: str       # R2 path to translation EPUB
    output_pdf_key: str        # R2 path to translation PDF
    output_txt_key: str        # R2 path to translation TXT
    bilingual_epub_key: str    # R2 path to bilingual EPUB (if applicable)
    bilingual_pdf_key: str     # R2 path to bilingual PDF (if applicable)
    bilingual_txt_key: str     # R2 path to bilingual TXT (if applicable)
```

## Error Handling & Fallbacks

### PDF Generation Fallback

```python
try:
    # Primary: WeasyPrint
    convert_html_to_pdf(...)
except Exception:
    # Fallback: Calibre EPUB→PDF
    convert_epub_to_pdf(...)
```

**Why Fallback?**
- WeasyPrint requires system libraries
- If deployment fails, Calibre ensures PDFs still generate
- Calibre widely available (included in base image)

### Translation Retry

```python
# Automatic retry on LLM failures
try:
    provider.translate_batch(...)
except Exception:
    # Retry with exponential backoff
    # Max 3 retries
```

## Monitoring & Logging

### Log Levels

```python
logger.info()    # Normal operations
logger.warning() # Fallbacks, non-critical issues
logger.error()   # Failures that need attention
```

### Key Metrics to Monitor

1. **Job Success Rate** - `status='done'` vs `status='failed'`
2. **WeasyPrint Usage** - Should be >99% (fallback = bad)
3. **Processing Time** - Average time per job
4. **LLM Costs** - Token usage per provider
5. **Storage Usage** - R2 bucket size

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql://...

# R2 Storage
R2_ACCOUNT_ID=...
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET_NAME=epub-translator-production

# Redis Queue
REDIS_URL=redis://localhost:6379

# LLM Providers
GEMINI_API_KEY=...
GROQ_API_KEY=...

# Email (Resend)
RESEND_API_KEY=...
```

## Development Workflow

### Running Locally

```bash
# 1. Start Redis
redis-server

# 2. Start worker
cd apps/api
PYTHONPATH=/Users/.../BookTranslator \\
OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES \\
poetry run rq worker translate --url redis://localhost:6379

# 3. Submit test job via API or web interface
```

### Testing

```bash
# Test bilingual PDF generation
cd apps/api
./test_pdf_local.sh

# Run full pipeline test
PYTHONPATH=. python tests/test_dual_provider_complete.py
```

## Deployment (Railway)

### Configuration Files

**`nixpacks.toml`:**
```toml
[phases.setup]
aptPkgs = ["libpango-1.0-0", "libpangocairo-1.0-0", "libcairo2", ...]

[start]
cmd = "poetry run rq worker --with-scheduler bookTranslator-jobs"
```

**`pyproject.toml`:**
```toml
[tool.poetry.dependencies]
python = "^3.12"
weasyprint = "^62.3"
...
```

### Deployment Process

1. **Push to GitHub** - `git push origin main`
2. **Railway Auto-Deploy** - Detects changes
3. **Build Phase** - Installs dependencies
4. **Deploy Phase** - Restarts worker
5. **Verify** - Check logs for WeasyPrint availability

## Future Enhancements

### Planned Features

1. **Parallel PDF Generation** - Generate EPUB + PDF simultaneously
2. **Custom Fonts** - Allow users to select font preferences
3. **PDF Bookmarks** - Extract TOC from EPUB for PDF navigation
4. **Streaming Progress** - Real-time progress updates via WebSocket
5. **Batch Jobs** - Process multiple books in one request
6. **PDF Hyperlinks** - Preserve internal chapter links

### Performance Optimizations

1. **Worker Scaling** - Auto-scale based on queue depth
2. **Caching** - Cache translated segments for similar books
3. **Async I/O** - Parallel file operations
4. **Compression** - Compress output files before upload

## Troubleshooting

### Common Issues

**1. WeasyPrint Import Error**
```
ModuleNotFoundError: No module named 'app.html_to_pdf'
```
**Fix:** Ensure `html_to_pdf.py` is in `apps/api/app/` directory

**2. Missing System Dependencies**
```
OSError: cannot load library 'libpango-1.0-0'
```
**Fix:** Verify `nixpacks.toml` is present and has correct packages

**3. PDF CSS Not Preserved**
```
WARNING: Used fallback PDF (CSS styling may be lost)
```
**Fix:** Check WeasyPrint logs for errors, verify system deps

**4. Job Stuck in Processing**
```
status='processing' for >10 minutes
```
**Fix:** Check worker logs, restart worker if hung

## Summary

The BookTranslator pipeline is a robust, production-ready system that:

✅ **Handles 3 output modes** (translation, bilingual, both)
✅ **Generates 6 file types** (EPUB, PDF, TXT × 2)
✅ **Uses WeasyPrint** for superior PDF quality
✅ **Supports multiple LLM providers** with automatic retry
✅ **Scales with Railway** auto-deployment
✅ **Has robust fallbacks** for all critical operations

The architecture is clean, well-documented, and maintainable.
