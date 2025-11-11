# PDF Generation with WeasyPrint

## Overview

All PDFs (bilingual and regular translations) are generated using **WeasyPrint**, which provides vastly superior CSS rendering and typography compared to Calibre's EPUB-to-PDF conversion.

## Architecture

### Current Flow (WeasyPrint for ALL PDFs)

```
┌─────────────────────────────────────────────────────────────┐
│                     Translation Pipeline                     │
└─────────────────────────────────────────────────────────────┘
                              ↓
         ┌────────────────────┴────────────────────┐
         ↓                                          ↓
┌─────────────────────┐                  ┌──────────────────────┐
│  Regular Translation │                  │   Bilingual Output   │
└─────────────────────┘                  └──────────────────────┘
         ↓                                          ↓
    HTML Docs                                  HTML Docs
         ↓                                          ↓
    ┌────────┐                              ┌──────────────┐
    │  EPUB  │                              │ Bilingual    │
    └────────┘                              │ EPUB (CSS)   │
         ↓                                  └──────────────┘
    ┌─────────────────┐                          ↓
    │   WeasyPrint    │                    ┌─────────────────┐
    │  HTML → PDF     │←───────────────────│   WeasyPrint    │
    │  (Superior!)    │                    │  HTML → PDF     │
    └─────────────────┘                    │  (CSS Preserved)│
         ↓                                  └─────────────────┘
    ┌────────┐                                    ↓
    │  PDF   │                              ┌────────────┐
    │ ✅ High │                              │ PDF        │
    │ Quality│                              │ ✅ Subtitles│
    └────────┘                              │ Preserved  │
                                            └────────────┘
```

### Why WeasyPrint?

**Advantages over Calibre:**
- ✅ **Superior CSS Support**: Industry-standard HTML-to-PDF rendering
- ✅ **Better Typography**: Professional-quality text rendering
- ✅ **Accurate Margins**: Proper page layout (1.5cm/2cm)
- ✅ **Font Rendering**: Excellent font handling and ligatures
- ✅ **RTL Support**: Full support for Arabic, Hebrew, Farsi, Urdu
- ✅ **Image Embedding**: Base64 data URIs work flawlessly
- ✅ **Consistent Output**: Same quality for all PDF types

## Implementation

### Key Files

1. **`apps/api/app/html_to_pdf.py`**
   - `convert_bilingual_html_to_pdf()` - For bilingual PDFs with subtitle styling
   - `convert_html_to_pdf()` - For regular translation PDFs

2. **`apps/api/app/pipeline/worker.py`**
   - Lines 466-510: Bilingual PDF generation
   - Lines 534-563: Regular translation PDF generation

3. **`apps/api/nixpacks.toml`**
   - Railway deployment configuration
   - System dependencies for WeasyPrint

### CSS Features Preserved

#### Bilingual Subtitles
```css
.bilingual-subtitle {
    display: block;
    font-size: 0.85em;      /* Readable but distinct */
    font-style: italic;     /* Visual differentiation */
    color: #666;            /* Gray, not translucent */
    margin: 0.3em 0 0 0;
    line-height: 1.4;
    font-weight: normal;
}
```

#### Page Layout
```css
@page {
    size: A4;
    margin: 1.5cm 2cm;  /* Optimized for content */
    @bottom-center {
        content: counter(page);
        font-size: 10pt;
        color: #666;
    }
}
```

#### Typography
```css
body {
    font-family: 'Times New Roman', 'Georgia', 'Garamond', serif;
    line-height: 1.6;
    font-size: 11pt;
}

/* Page breaks */
h1, h2, h3 {
    page-break-after: avoid;
    page-break-inside: avoid;
}

p {
    orphans: 2;  /* Minimum lines at bottom of page */
    widows: 2;   /* Minimum lines at top of page */
}
```

## Deployment

### Railway Configuration

The `nixpacks.toml` file specifies all required system dependencies:

```toml
[phases.setup]
aptPkgs = [
    "libpango-1.0-0",      # Text layout and rendering
    "libpangocairo-1.0-0", # Cairo backend for Pango
    "libcairo2",           # 2D graphics library
    "libgdk-pixbuf2.0-0",  # Image loading library
    "shared-mime-info"      # MIME type database
]

[start]
cmd = "poetry run rq worker --with-scheduler bookTranslator-jobs"
```

### Python Dependencies

```toml
[tool.poetry.dependencies]
weasyprint = "^62.3"
```

### Local Development

For local testing on macOS:

```bash
# Install system dependencies
brew install pango cairo gdk-pixbuf

# Set library path for WeasyPrint
export DYLD_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_LIBRARY_PATH"

# Run tests
cd apps/api
./test_pdf_local.sh
```

## Monitoring

### Success Indicators

Look for these log messages:

**Bilingual PDF:**
```
📄 Converting bilingual HTML to PDF (preserves CSS styling)...
✅ Bilingual PDF generated: 2.05 MB
✅ Uploaded bilingual PDF with preserved CSS: outputs/{job_id}_bilingual.pdf
```

**Regular Translation PDF:**
```
📄 Converting translation HTML to PDF with WeasyPrint (superior quality)...
✅ Translation PDF generated with WeasyPrint: 1.95 MB
✅ Uploaded translation PDF (WeasyPrint): outputs/{job_id}.pdf
```

### Error Handling

If WeasyPrint fails, the system logs detailed errors:

```python
try:
    # WeasyPrint generation
    success = convert_html_to_pdf(...)
except Exception as e:
    logger.error(f"Failed to generate PDF with WeasyPrint: {e}", exc_info=True)
    # For bilingual PDFs, falls back to Calibre
```

## Quality Comparison

### WeasyPrint vs Calibre

| Feature | WeasyPrint | Calibre EPUB→PDF |
|---------|------------|------------------|
| CSS Support | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Typography | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Margins | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Images | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| RTL Support | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Bilingual CSS | ⭐⭐⭐⭐⭐ | ⭐ (Lost) |
| Speed | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| File Size | ~2MB | ~2MB |

## Testing

### Test Scripts

1. **Test Bilingual PDF:**
   ```bash
   cd apps/api
   export DYLD_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_LIBRARY_PATH"
   PYTHONPATH=. python app/html_to_pdf.py
   ```

2. **Test Regular Translation PDF:**
   ```bash
   cd apps/api
   export DYLD_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_LIBRARY_PATH"
   PYTHONPATH=. python test_regular_translation_weasyprint.py
   ```

3. **Compare Both Approaches:**
   - Opens both WeasyPrint and Calibre PDFs side-by-side
   - Visual comparison shows WeasyPrint superiority

### What to Check

**Bilingual PDFs:**
- ✅ Translated text is normal size and black
- ✅ Original text subtitles are smaller (0.85em)
- ✅ Subtitles are gray (#666) and italic
- ✅ Line spacing is correct (1.4)
- ✅ Margins are optimized (1.5cm/2cm)

**Regular Translation PDFs:**
- ✅ Clean typography throughout
- ✅ Proper page breaks (no orphans/widows)
- ✅ Images display correctly
- ✅ RTL text flows correctly (if applicable)
- ✅ Page numbers at bottom center

## Troubleshooting

### WeasyPrint Import Errors

**Symptom:**
```
ModuleNotFoundError: No module named 'app.html_to_pdf'
```

**Fix:**
- Ensure `html_to_pdf.py` is in `apps/api/app/` directory
- Check it's not in `apps/api/` (wrong location)

### Missing System Dependencies

**Symptom:**
```
OSError: cannot load library 'libpango-1.0-0'
```

**Fix:**
- Verify `nixpacks.toml` is in `apps/api/` directory
- Check Railway deployment logs show system packages installing
- Redeploy if necessary

### PDF Generation Failures

**Symptom:**
```
Failed to generate PDF with WeasyPrint: <error>
```

**Action:**
- Check full error traceback in logs
- For bilingual PDFs, system falls back to Calibre
- For regular PDFs, job fails (intentional - forces fix)

## Performance

### Generation Times

Typical PDF generation times (20-page book):

- **WeasyPrint**: ~3-4 seconds
- **Calibre**: ~3-4 seconds
- **No significant difference in speed**

### File Sizes

- **WeasyPrint**: ~1.9-2.1 MB
- **Calibre**: ~2.0-2.2 MB
- **Comparable file sizes**

## Future Enhancements

Potential improvements:

1. **Custom Fonts**: Allow users to select preferred font families
2. **Margin Control**: Let users customize margins for their needs
3. **Parallel Generation**: Generate EPUB and PDF simultaneously
4. **PDF Bookmarks**: Extract TOC from EPUB for PDF navigation
5. **Hyperlinks**: Preserve internal chapter links in PDFs
6. **Cover Pages**: Generate beautiful title pages
7. **Metadata**: Embed author, title, language in PDF metadata

## Summary

**Before (Calibre):**
- ❌ Lost bilingual CSS styling
- ❌ Inconsistent typography
- ❌ Less optimal margins

**After (WeasyPrint):**
- ✅ Perfect CSS preservation
- ✅ Professional typography
- ✅ Optimized page layout
- ✅ Consistent quality across all PDFs

WeasyPrint is now the standard for all PDF generation in the BookTranslator pipeline.
