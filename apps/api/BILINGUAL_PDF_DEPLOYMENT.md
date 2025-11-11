# Bilingual PDF with Preserved Formatting - Deployment Guide

## Problem Statement

**Before**: Bilingual PDFs generated via Calibre (EPUB→PDF conversion) lost CSS styling:
- ❌ Bilingual subtitles appeared same size/color as main text
- ❌ Italic and gray color styles were not preserved
- ❌ Made bilingual PDFs less readable

**After**: Bilingual PDFs generated via HTML→PDF (WeasyPrint) preserve all CSS:
- ✅ Bilingual subtitles are smaller (0.65em)
- ✅ Subtitles are gray (#bbb) and italic
- ✅ Perfect match with EPUB and preview formatting

## Solution Overview

### Architecture Change

**Old Flow:**
```
Bilingual HTML Docs → Bilingual EPUB → [Calibre] → PDF (CSS lost ❌)
```

**New Flow:**
```
Bilingual HTML Docs → [WeasyPrint] → PDF (CSS preserved ✅)
                    ↘ Bilingual EPUB (CSS preserved ✅)
```

### Key Files

1. **`apps/api/html_to_pdf.py`** - New HTML-to-PDF converter using WeasyPrint
2. **`apps/api/app/pipeline/worker.py`** (lines 466-509) - Updated to use HTML-to-PDF
3. **Fallback mechanism** - Falls back to EPUB→PDF if HTML-to-PDF fails

## Railway Deployment Requirements

### System Dependencies

WeasyPrint requires the following system libraries on Railway:

#### Option 1: Using `nixpacks.toml` (Recommended)

Create `apps/api/nixpacks.toml`:

```toml
[phases.setup]
aptPkgs = [
    "libpango-1.0-0",
    "libpangocairo-1.0-0",
    "libcairo2",
    "libgdk-pixbuf2.0-0",
    "shared-mime-info"
]

[start]
cmd = "poetry run rq worker --with-scheduler bookTranslator-jobs"
```

#### Option 2: Using Dockerfile

If using a custom Dockerfile, add before `RUN pip install`:

```dockerfile
RUN apt-get update && apt-get install -y \\
    libpango-1.0-0 \\
    libpangocairo-1.0-0 \\
    libcairo2 \\
    libgdk-pixbuf2.0-0 \\
    shared-mime-info \\
    && rm -rf /var/lib/apt/lists/*
```

### Python Dependencies

Ensure `pyproject.toml` includes WeasyPrint:

```toml
[tool.poetry.dependencies]
weasyprint = "^62.3"  # Excellent CSS support for PDF generation
```

Run after adding:
```bash
poetry lock
poetry install
```

## Deployment Steps

### 1. Commit Changes

```bash
git add apps/api/html_to_pdf.py \\
        apps/api/app/pipeline/worker.py \\
        apps/api/nixpacks.toml \\
        apps/api/pyproject.toml

git commit -m "feat: Preserve bilingual CSS formatting in PDFs via HTML-to-PDF

- Add html_to_pdf.py for HTML-to-PDF conversion with WeasyPrint
- Update worker.py to use HTML-to-PDF for bilingual PDFs
- Preserve bilingual subtitle styling (smaller, gray, italic)
- Add fallback to EPUB-based PDF if HTML-to-PDF fails
- Add Railway deployment config for WeasyPrint dependencies

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
"

git push
```

### 2. Deploy to Railway

Railway will automatically:
1. Detect `nixpacks.toml` configuration
2. Install system dependencies (Pango, Cairo, etc.)
3. Install Python dependencies including WeasyPrint
4. Restart the worker with new code

### 3. Verify Deployment

Check Railway logs for:

```
✅ WeasyPrint available for PDF generation
📄 Converting bilingual HTML to PDF (preserves CSS styling)...
✅ Bilingual PDF generated: X.XX MB
   Bilingual subtitle styling preserved in PDF
```

If you see fallback messages:
```
⚠️  Failed to generate bilingual PDF: cannot load library 'libpango-1.0-0'
⚠️  Falling back to EPUB-to-PDF conversion...
```

This means system dependencies weren't installed correctly. Check nixpacks.toml is in the right location.

## Testing

### Test Production Bilingual PDF

1. **Submit a translation job** with bilingual output
2. **Download the bilingual PDF**
3. **Visual inspection**:
   - Spanish/translated text should be normal size, black
   - English/original text should be smaller, gray, italic below
   - Same formatting as bilingual EPUB and preview

### Test Script (Local Development)

```bash
cd apps/api
PYTHONPATH=. python html_to_pdf.py
```

This will:
- Load sample EPUB
- Create bilingual documents
- Generate PDF with CSS preserved
- Open PDF for inspection

**Note**: Local testing requires WeasyPrint dependencies. On macOS:

```bash
brew install pango cairo gdk-pixbuf
```

## Rollback Plan

If HTML-to-PDF fails in production, the worker automatically falls back to EPUB-based PDF:

```python
except Exception as e:
    logger.error(f"Failed to generate bilingual PDF: {e}", exc_info=True)
    # Fallback to EPUB-based PDF
    logger.info("Falling back to EPUB-to-PDF conversion...")
    bilingual_pdf_path = convert_epub_to_pdf(bilingual_epub_path, temp_dir)
```

This ensures users always get a bilingual PDF, even if CSS styling is lost.

## Monitoring

Watch for these metrics after deployment:

- **Success rate**: `Uploaded bilingual PDF with preserved CSS` vs fallback usage
- **File sizes**: HTML-to-PDF typically produces slightly larger files than Calibre
- **Generation time**: WeasyPrint is comparable to Calibre in speed
- **Error rate**: Should see zero errors if dependencies are installed correctly

## Benefits

1. **User Experience**: Bilingual PDFs now match preview and EPUB formatting exactly
2. **Consistency**: All 3 formats (EPUB, PDF, TXT) generated from same HTML source
3. **Quality**: Professional typography and CSS rendering in PDFs
4. **Reliability**: Automatic fallback ensures service continuity

## Technical Details

### Why WeasyPrint?

- ✅ **Excellent CSS support**: Industry-standard for HTML→PDF with CSS
- ✅ **Print media**: Designed specifically for generating print-quality PDFs
- ✅ **Typography**: Supports advanced typography features (orphans, widows, page breaks)
- ✅ **Performance**: Fast enough for production use
- ✅ **Open source**: Well-maintained, widely used

### CSS Features Preserved

```css
.bilingual-subtitle {
    display: block;
    font-size: 0.65em;      /* ✅ Preserved */
    font-style: italic;     /* ✅ Preserved */
    color: #bbb;            /* ✅ Preserved */
    margin: 0.3em 0 0 0;    /* ✅ Preserved */
    line-height: 1.4;       /* ✅ Preserved */
    font-weight: normal;    /* ✅ Preserved */
}
```

Plus:
- Page breaks and margins
- Orphans and widows control
- Font families and sizes
- Text alignment and direction (RTL support)
- All original EPUB CSS

## Support

If issues arise after deployment:

1. **Check Railway logs** for WeasyPrint import errors
2. **Verify nixpacks.toml** is in `apps/api/` directory
3. **Check system dependencies** are installed (libpango, libcairo)
4. **Monitor fallback usage** - if all jobs use fallback, dependencies are missing
5. **Test locally** first if possible

## Future Enhancements

Potential improvements for future versions:

1. **Parallel generation**: Generate EPUB and PDF simultaneously
2. **Custom fonts**: Allow users to specify font preferences
3. **Page numbers**: Add custom page numbering styles
4. **Watermarks**: Optional watermarks for preview PDFs
5. **Bookmarks**: Generate PDF bookmarks from EPUB TOC
