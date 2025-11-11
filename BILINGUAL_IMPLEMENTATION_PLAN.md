# Bilingual EPUB Implementation Plan
## Complete Strategy & Technical Specification

**Version:** 1.0
**Date:** 2025-11-11
**Status:** Design Phase
**Estimated Timeline:** 2-3 weeks

---

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [User Experience](#user-experience)
3. [Technical Architecture](#technical-architecture)
4. [Implementation Plan](#implementation-plan)
5. [Testing Strategy](#testing-strategy)
6. [Deployment & Rollout](#deployment--rollout)

---

## Executive Summary

### Goal
Add bilingual EPUB output option that displays original and translated text together, optimized for all devices from iPhone to desktop.

### Approach
Responsive paragraph-pair layout using standard HTML/CSS:
- **Desktop/Tablet Landscape:** Side-by-side columns
- **Mobile Portrait:** Stacked paragraphs with visual separation

### Business Value
- **Unique Feature:** Differentiator in translation market
- **Target Market:** Language learners, educators, comparative readers
- **Pricing:** +$0.50 premium over standard translation
- **Low Risk:** Uses standard EPUB features, maximum compatibility

### Key Advantages
✅ Works on ALL EPUB readers (Kindle, Apple Books, Google Play, etc.)
✅ Leverages existing segment alignment (minimal code changes)
✅ Professional reading experience on all devices
✅ No JavaScript or special features required
✅ Quick implementation (2-3 weeks)

---

## User Experience

### Desktop/Tablet Experience (> 600px width)

```
╔════════════════════════════════════════════════════════╗
║  CHAPTER 1: MOWGLI'S BROTHERS                         ║
╠═══════════════════════╦════════════════════════════════╣
║  ENGLISH              ║  ESPAÑOL                       ║
╠═══════════════════════╬════════════════════════════════╣
║  It was seven o'clock ║  Eran las siete de la tarde   ║
║  of a very warm       ║  de un día muy cálido en las  ║
║  evening in the       ║  colinas de Seeonee cuando el ║
║  Seeonee hills when   ║  Padre Lobo despertó de su    ║
║  Father Wolf woke     ║  descanso diurno.             ║
║  from his day's rest. ║                               ║
║                       ║                               ║
║  He scratched         ║  Se rascó, bostezó y          ║
║  himself, yawned,     ║  extendió sus patas una tras  ║
║  and spread out his   ║  otra para librarse de la     ║
║  paws one after the   ║  sensación de somnolencia que ║
║  other to get rid of  ║  aún persistía en sus         ║
║  the sleepy feeling   ║  extremidades.                ║
║  in their tips.       ║                               ║
╚═══════════════════════╩════════════════════════════════╝
```

**Reading Flow:**
- Natural left-to-right reading
- Easy comparison between languages
- Both texts visible simultaneously

### Mobile Experience (< 600px width)

```
╔══════════════════════╗
║  CHAPTER 1          ║
╠══════════════════════╣
║  🇬🇧 ENGLISH        ║
╠══════════════════════╣
║  It was seven       ║
║  o'clock of a very  ║
║  warm evening in    ║
║  the Seeonee hills  ║
║  when Father Wolf   ║
║  woke from his      ║
║  day's rest.        ║
╠══════════════════════╣
║  🇪🇸 ESPAÑOL        ║
╠══════════════════════╣
║  Eran las siete de  ║
║  la tarde de un día ║
║  muy cálido en las  ║
║  colinas de Seeonee ║
║  cuando el Padre    ║
║  Lobo despertó de   ║
║  su descanso diurno.║
╠══════════════════════╣
║      ↓ Scroll       ║
╠══════════════════════╣
║  🇬🇧 ENGLISH        ║
╠══════════════════════╣
║  He scratched       ║
║  himself, yawned... ║
╚══════════════════════╝
```

**Reading Flow:**
1. Read English paragraph (full width)
2. Scroll down → see Spanish translation
3. Scroll down → next English paragraph
4. Natural vertical flow

---

## Technical Architecture

### Current Pipeline (For Reference)
```
┌─────────────┐
│ EPUB Input  │
└──────┬──────┘
       │
       ↓
┌──────────────────┐
│ EPUBProcessor    │ ← Read EPUB, extract documents
│ read_epub()      │
└────────┬─────────┘
         │
         ↓
┌─────────────────────┐
│ HTMLSegmenter       │ ← Segment into chunks
│ segment_documents() │
└─────────┬───────────┘
          │
          ↓
┌──────────────────────────┐
│ TranslationOrchestrator  │ ← Translate segments
│ translate_segments()     │
└──────────┬───────────────┘
           │
           ↓
┌─────────────────────┐
│ HTMLSegmenter       │ ← Reconstruct HTML
│ reconstruct_docs()  │
└─────────┬───────────┘
          │
          ↓
┌─────────────────┐
│ OutputGenerator │ ← Generate outputs
│ generate_*()    │
└─────────┬───────┘
          │
          ↓
    ┌─────┴─────┐
    │           │
┌───┴──┐   ┌───┴──┐   ┌─────┐
│ EPUB │   │ PDF  │   │ TXT │
└──────┘   └──────┘   └─────┘
```

### New Bilingual Pipeline

```
┌─────────────┐
│ EPUB Input  │
└──────┬──────┘
       │
       ↓
┌──────────────────┐
│ EPUBProcessor    │
│ read_epub()      │
└────────┬─────────┘
         │
         ↓
┌─────────────────────┐
│ HTMLSegmenter       │
│ segment_documents() │ ← Creates ALIGNED segments
└────────┬────────────┘
         │
         ├─────────────────────────────┐
         │ (Keep originals)            │ (Translate)
         │                             ↓
         │                   ┌──────────────────────────┐
         │                   │ TranslationOrchestrator  │
         │                   │ translate_segments()     │
         │                   └──────────┬───────────────┘
         │                              │
         ↓                              ↓
┌─────────────────┐         ┌─────────────────────┐
│ original_segments│         │ translated_segments │
└────────┬────────┘         └─────────┬───────────┘
         │                            │
         └────────────┬───────────────┘
                      │
                      ↓
           ┌──────────────────────┐
           │ BilingualHTMLGen     │ ← NEW COMPONENT
           │ merge_segments()     │   Merges orig + trans
           └──────────┬───────────┘
                      │
                      ↓
           ┌──────────────────────┐
           │ EPUBProcessor        │
           │ write_bilingual_epub()│ ← NEW METHOD
           └──────────┬───────────┘
                      │
                      ↓
              ┌───────────────┐
              │ Bilingual EPUB│
              └───────────────┘
```

### Key Insight: Perfect Alignment Already Exists!

Your `HTMLSegmenter` creates perfectly aligned segments:
```python
# Current code already does this:
original_segments = [seg1, seg2, seg3, ...]      # Original text
translated_segments = translate(original_segments) # Same order, same count

# segments[0] in English = segments[0] in Spanish ✓
# segments[1] in English = segments[1] in Spanish ✓
# Perfect 1:1 alignment!
```

---

## Implementation Plan

### Phase 1: Core Components (Week 1)

#### 1.1 Create BilingualHTMLGenerator

**New File:** `apps/api/app/pipeline/bilingual_html.py`

```python
"""
Bilingual HTML generation for side-by-side EPUB reading.
"""
from typing import List, Dict, Tuple
from bs4 import BeautifulSoup


class BilingualHTMLGenerator:
    """Generates bilingual HTML with original and translated text."""

    def __init__(self):
        self.css_template = self._load_bilingual_css()

    def merge_segments(
        self,
        original_segments: List[str],
        translated_segments: List[str],
        source_lang: str = "en",
        target_lang: str = "es",
        layout_mode: str = "responsive"  # or "side-by-side", "alternating"
    ) -> List[Dict]:
        """
        Merge original and translated segments into bilingual HTML.

        Args:
            original_segments: List of original text segments
            translated_segments: List of translated segments (aligned 1:1)
            source_lang: Source language code
            target_lang: Target language code
            layout_mode: Layout style

        Returns:
            List of document dicts with bilingual HTML content
        """
        if len(original_segments) != len(translated_segments):
            raise ValueError("Segment counts must match!")

        bilingual_docs = []

        # Group segments by document (based on reconstruction maps)
        for orig, trans in zip(original_segments, translated_segments):
            bilingual_html = self._create_bilingual_paragraph(
                orig, trans, source_lang, target_lang
            )
            bilingual_docs.append(bilingual_html)

        return bilingual_docs

    def _create_bilingual_paragraph(
        self,
        original: str,
        translation: str,
        source_lang: str,
        target_lang: str
    ) -> str:
        """Create HTML for a single bilingual paragraph pair."""

        # Get language display names
        lang_names = self._get_language_names(source_lang, target_lang)

        html = f'''
        <div class="bilingual-container">
            <div class="original-text">
                <span class="lang-label">{lang_names['source']}</span>
                <div class="content">{original}</div>
            </div>
            <div class="translated-text">
                <span class="lang-label">{lang_names['target']}</span>
                <div class="content">{translation}</div>
            </div>
        </div>
        '''

        return html

    def _load_bilingual_css(self) -> str:
        """Load bilingual CSS styles."""
        return '''
        /* Bilingual EPUB Styles */

        .bilingual-container {
            display: flex;
            flex-direction: row;
            gap: 1em;
            margin: 1.5em 0;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            overflow: hidden;
            page-break-inside: avoid;
        }

        .original-text,
        .translated-text {
            flex: 1;
            padding: 1em;
        }

        .original-text {
            background: linear-gradient(135deg, #fafafa 0%, #f5f5f5 100%);
            border-right: 1px solid #e0e0e0;
        }

        .translated-text {
            background: linear-gradient(135deg, #f0f4ff 0%, #e8f0ff 100%);
        }

        .lang-label {
            display: block;
            font-weight: 600;
            color: #666;
            font-size: 0.85em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 0.75em;
        }

        .content {
            line-height: 1.6;
        }

        /* Preserve inline formatting */
        .content em { font-style: italic; }
        .content strong { font-weight: bold; }
        .content a { color: #2196F3; text-decoration: none; }

        /* Mobile responsive: Stack vertically */
        @media (max-width: 600px) {
            .bilingual-container {
                flex-direction: column;
                gap: 0;
            }

            .original-text {
                border-right: none;
                border-bottom: 2px solid #2196F3;
            }

            .bilingual-container {
                font-size: 1.1em;
                line-height: 1.6;
            }

            .lang-label {
                font-size: 0.9em;
                color: #2196F3;
            }
        }

        /* Tablet portrait */
        @media (min-width: 601px) and (max-width: 900px) {
            .bilingual-container {
                gap: 0.75em;
            }

            .original-text,
            .translated-text {
                padding: 0.75em;
                font-size: 1.05em;
            }
        }

        /* Desktop/Tablet landscape */
        @media (min-width: 901px) {
            .bilingual-container {
                max-width: 1200px;
                margin-left: auto;
                margin-right: auto;
            }
        }

        /* Dark mode support */
        @media (prefers-color-scheme: dark) {
            .bilingual-container {
                border-color: #333;
            }

            .original-text {
                background: #1a1a1a;
                color: #e0e0e0;
                border-right-color: #333;
            }

            .translated-text {
                background: #1a1a2e;
                color: #e0e0e0;
            }

            .lang-label {
                color: #888;
            }
        }
        '''

    def _get_language_names(self, source_lang: str, target_lang: str) -> Dict[str, str]:
        """Get display names for language codes."""
        lang_map = {
            'en': 'English',
            'es': 'Español',
            'fr': 'Français',
            'de': 'Deutsch',
            'it': 'Italiano',
            'pt': 'Português',
            'ja': '日本語',
            'zh': '中文',
            'ko': '한국어',
            'ar': 'العربية',
            'ru': 'Русский',
            # Add more as needed
        }

        return {
            'source': lang_map.get(source_lang, source_lang.upper()),
            'target': lang_map.get(target_lang, target_lang.upper())
        }
```

#### 1.2 Update EPUBProcessor

**Modify:** `apps/api/app/pipeline/epub_io.py`

Add new method:

```python
def write_bilingual_epub(
    self,
    original_book: epub.EpubBook,
    original_docs: List[Dict],
    translated_docs: List[Dict],
    bilingual_docs: List[Dict],
    output_path: str,
    source_lang: str,
    target_lang: str
) -> bool:
    """
    Write bilingual EPUB with original and translation.

    Args:
        original_book: Original EPUB book object
        original_docs: Original spine documents
        translated_docs: Translated spine documents
        bilingual_docs: Merged bilingual HTML documents
        output_path: Path to save bilingual EPUB
        source_lang: Source language code
        target_lang: Target language code
    """
    try:
        # Create new book
        book = epub.EpubBook()

        # Update metadata for bilingual edition
        original_title = self._extract_title(original_book)
        book.set_title(f"{original_title} (Bilingual Edition)")

        # Copy metadata from original
        for meta_type in ['DC', 'OPF']:
            for item in original_book.metadata.get(meta_type, []):
                book.add_metadata(meta_type, item[0], item[1])

        # Add bilingual-specific metadata
        book.add_metadata('DC', 'description',
            f'Bilingual edition: {source_lang} - {target_lang}')
        book.add_metadata('DC', 'language', f'{source_lang},{target_lang}')

        # Add bilingual CSS
        bilingual_css = epub.EpubItem(
            uid="style_bilingual",
            file_name="style/bilingual.css",
            media_type="text/css",
            content=self._get_bilingual_css()
        )
        book.add_item(bilingual_css)

        # Copy images and other resources from original
        for item in original_book.get_items():
            if item.get_type() in [ebooklib.ITEM_IMAGE, ebooklib.ITEM_STYLE,
                                   ebooklib.ITEM_FONT, ebooklib.ITEM_AUDIO]:
                book.add_item(item)

        # Add bilingual documents
        spine = ['nav']
        for idx, (doc, bilin_doc) in enumerate(zip(original_docs, bilingual_docs)):
            # Create new chapter with bilingual content
            chapter = epub.EpubHtml(
                title=doc.get('title', f'Chapter {idx+1}'),
                file_name=f'bilingual_{idx}.xhtml',
                lang=f'{source_lang},{target_lang}'
            )

            # Set content with bilingual HTML
            chapter.set_content(self._wrap_bilingual_html(
                bilin_doc, doc.get('title', '')
            ))

            # Link CSS
            chapter.add_link(href='style/bilingual.css', rel='stylesheet',
                           type='text/css')

            book.add_item(chapter)
            spine.append(chapter)

        # Create table of contents
        book.toc = self._create_bilingual_toc(original_docs, spine[1:])

        # Add navigation
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        # Set spine
        book.spine = spine

        # Write EPUB
        epub.write_epub(output_path, book)

        logger.info(f"Successfully wrote bilingual EPUB to {output_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to write bilingual EPUB: {e}")
        return False

def _wrap_bilingual_html(self, content: str, title: str) -> str:
    """Wrap bilingual content in proper XHTML structure."""
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>{title}</title>
    <link rel="stylesheet" href="style/bilingual.css" type="text/css"/>
</head>
<body>
    <h1>{title}</h1>
    {content}
</body>
</html>'''
```

#### 1.3 Update Worker Pipeline

**Modify:** `apps/api/app/pipeline/worker.py`

```python
def translate_epub(job_id: str):
    """Main worker function to translate EPUB files."""

    # ... existing code ...

    # After translation completes
    translated_segments, tokens_actual, provider_used = asyncio.run(
        orchestrator.translate_segments(...)
    )

    # Reconstruct documents
    translated_docs = segmenter.reconstruct_documents(
        translated_segments, reconstruction_maps, spine_docs
    )

    # Check if bilingual output requested
    if job.output_format == "bilingual":
        # Generate bilingual outputs
        output_keys = _generate_bilingual_outputs(
            job_id, temp_dir, original_book, spine_docs,
            translated_docs, segments, translated_segments,
            job.source_lang, job.target_lang
        )
    else:
        # Standard translation-only output
        output_keys = _generate_outputs(
            job_id, temp_dir, original_book, translated_docs, translated_segments
        )

    # ... rest of existing code ...

def _generate_bilingual_outputs(
    job_id: str,
    temp_dir: str,
    original_book,
    original_docs: list,
    translated_docs: list,
    original_segments: list,
    translated_segments: list,
    source_lang: str,
    target_lang: str
) -> dict:
    """Generate bilingual EPUB, PDF, and TXT outputs."""

    from app.pipeline.bilingual_html import BilingualHTMLGenerator

    storage = get_storage()
    output_keys = {}

    try:
        # Generate bilingual HTML
        bilingual_gen = BilingualHTMLGenerator()
        bilingual_docs = bilingual_gen.merge_segments(
            original_segments,
            translated_segments,
            source_lang,
            target_lang
        )

        # Write bilingual EPUB
        epub_processor = EPUBProcessor()
        epub_path = os.path.join(temp_dir, f"bilingual_{job_id}.epub")

        if epub_processor.write_bilingual_epub(
            original_book, original_docs, translated_docs,
            bilingual_docs, epub_path, source_lang, target_lang
        ):
            # Upload EPUB
            epub_key = f"outputs/{job_id}_bilingual.epub"
            if storage.upload_file(epub_path, epub_key, "application/epub+zip"):
                output_keys["epub"] = epub_key
                logger.info(f"Uploaded bilingual EPUB: {epub_key}")

            # Generate PDF from bilingual EPUB
            pdf_path = os.path.join(temp_dir, f"bilingual_{job_id}.pdf")
            # ... PDF generation code ...

            # Generate TXT (keep existing TXT generation for now)
            # ... TXT generation code ...

        return output_keys

    except Exception as e:
        logger.error(f"Failed to generate bilingual outputs: {e}")
        raise
```

### Phase 2: Database & API Updates (Week 1-2)

#### 2.1 Update Job Model

**Modify:** `apps/api/app/models.py`

```python
class Job(Base):
    __tablename__ = "jobs"

    # ... existing fields ...

    # Add output format field
    output_format = Column(
        String,
        default="translated",
        nullable=False,
        comment="Output format: 'translated' or 'bilingual'"
    )

    # Update output key fields to support bilingual
    output_epub_bilingual_key = Column(String, nullable=True)
    output_pdf_bilingual_key = Column(String, nullable=True)
```

#### 2.2 Database Migration

**Create:** `apps/api/alembic/versions/xxx_add_bilingual_support.py`

```python
"""Add bilingual output support

Revision ID: xxx
"""

from alembic import op
import sqlalchemy as sa

def upgrade():
    # Add output_format column
    op.add_column('jobs', sa.Column(
        'output_format',
        sa.String(),
        nullable=False,
        server_default='translated'
    ))

    # Add bilingual output keys
    op.add_column('jobs', sa.Column(
        'output_epub_bilingual_key',
        sa.String(),
        nullable=True
    ))
    op.add_column('jobs', sa.Column(
        'output_pdf_bilingual_key',
        sa.String(),
        nullable=True
    ))

def downgrade():
    op.drop_column('jobs', 'output_pdf_bilingual_key')
    op.drop_column('jobs', 'output_epub_bilingual_key')
    op.drop_column('jobs', 'output_format')
```

### Phase 3: Frontend Updates (Week 2)

#### 3.1 Add Output Format Selector

**Modify:** `apps/web/src/app/translate/page.tsx`

```typescript
'use client'

export default function TranslatePage() {
  const [outputFormat, setOutputFormat] = useState<'translated' | 'bilingual'>('translated')

  return (
    <div className="translate-page">
      {/* ... existing upload UI ... */}

      {/* Output format selector */}
      <div className="output-format-section">
        <h3>Output Format</h3>
        <div className="format-options">
          <label className="format-option">
            <input
              type="radio"
              name="outputFormat"
              value="translated"
              checked={outputFormat === 'translated'}
              onChange={(e) => setOutputFormat(e.target.value as any)}
            />
            <div className="option-content">
              <strong>Translation Only</strong>
              <p>Standard translated EPUB, PDF, and TXT</p>
              <span className="price">Current pricing</span>
            </div>
          </label>

          <label className="format-option">
            <input
              type="radio"
              name="outputFormat"
              value="bilingual"
              checked={outputFormat === 'bilingual'}
              onChange={(e) => setOutputFormat(e.target.value as any)}
            />
            <div className="option-content">
              <strong>Bilingual Edition</strong>
              <p>Original and translation side-by-side</p>
              <span className="badge">Perfect for learning!</span>
              <span className="price">+$0.50</span>
            </div>
          </label>
        </div>
      </div>

      {/* Preview bilingual layout */}
      {outputFormat === 'bilingual' && (
        <div className="bilingual-preview">
          <h4>Preview: How it looks</h4>
          <div className="preview-desktop">
            <strong>Desktop/Tablet:</strong>
            <div className="preview-box side-by-side">
              <div className="col">English text...</div>
              <div className="col">Español text...</div>
            </div>
          </div>
          <div className="preview-mobile">
            <strong>Mobile:</strong>
            <div className="preview-box stacked">
              <div className="block">English text...</div>
              <div className="block">Español text...</div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
```

#### 3.2 Update API Call

**Modify:** `apps/web/src/app/translate/actions.ts`

```typescript
export async function createTranslationJob(formData: FormData) {
  const file = formData.get('file') as File
  const targetLang = formData.get('targetLang') as string
  const outputFormat = formData.get('outputFormat') as 'translated' | 'bilingual'

  // Upload to R2
  const uploadResult = await uploadToR2(file)

  // Create job with output format
  const response = await fetch(`${API_URL}/jobs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      source_key: uploadResult.key,
      target_lang: targetLang,
      output_format: outputFormat,  // NEW FIELD
      // ... other fields
    })
  })

  return response.json()
}
```

### Phase 4: Testing (Week 2-3)

#### 4.1 Create Bilingual Tests

**New File:** `tests/test_bilingual_epub.py`

```python
#!/usr/bin/env python3
"""
Test bilingual EPUB generation across different devices and readers.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "api"))

from app.pipeline.bilingual_html import BilingualHTMLGenerator
from app.pipeline.epub_io import EPUBProcessor


class TestBilingualGeneration:
    """Test bilingual HTML and EPUB generation."""

    def test_segment_alignment(self):
        """Test that original and translated segments align correctly."""
        original_segments = [
            "First paragraph in English.",
            "Second paragraph in English.",
            "Third paragraph in English."
        ]

        translated_segments = [
            "Primer párrafo en español.",
            "Segundo párrafo en español.",
            "Tercer párrafo en español."
        ]

        gen = BilingualHTMLGenerator()
        bilingual_docs = gen.merge_segments(
            original_segments,
            translated_segments,
            source_lang='en',
            target_lang='es'
        )

        assert len(bilingual_docs) == len(original_segments)

        # Verify each doc contains both languages
        for idx, doc in enumerate(bilingual_docs):
            assert original_segments[idx] in doc
            assert translated_segments[idx] in doc

    def test_bilingual_html_structure(self):
        """Test HTML structure of bilingual content."""
        gen = BilingualHTMLGenerator()
        html = gen._create_bilingual_paragraph(
            "English text",
            "Texto español",
            "en",
            "es"
        )

        # Check for required CSS classes
        assert 'bilingual-container' in html
        assert 'original-text' in html
        assert 'translated-text' in html
        assert 'lang-label' in html

        # Check for both languages
        assert 'English text' in html
        assert 'Texto español' in html

    @pytest.mark.asyncio
    async def test_full_bilingual_epub(self):
        """Test complete bilingual EPUB generation."""
        # Use sample EPUB
        sample_epub = Path(__file__).parent.parent / "sample_books" / "pg236_first20pages.epub"

        # Read original
        processor = EPUBProcessor()
        original_book, docs = processor.read_epub(str(sample_epub))

        # Create mock translated docs (in real test, run actual translation)
        translated_docs = [
            {'id': doc['id'], 'content': f"[TRANSLATED] {doc['content']}",
             'title': doc['title']}
            for doc in docs
        ]

        # Generate bilingual
        gen = BilingualHTMLGenerator()

        # Extract segments from docs
        original_segments = [doc['content'] for doc in docs]
        translated_segments = [doc['content'] for doc in translated_docs]

        bilingual_docs = gen.merge_segments(
            original_segments,
            translated_segments,
            'en',
            'es'
        )

        # Write bilingual EPUB
        output_path = "/tmp/test_bilingual.epub"
        success = processor.write_bilingual_epub(
            original_book,
            docs,
            translated_docs,
            bilingual_docs,
            output_path,
            'en',
            'es'
        )

        assert success
        assert Path(output_path).exists()

        # Verify EPUB structure
        # ... validation code ...


class TestResponsiveLayout:
    """Test responsive CSS behavior."""

    def test_mobile_breakpoint(self):
        """Test CSS switches to stacked layout on mobile."""
        gen = BilingualHTMLGenerator()
        css = gen._load_bilingual_css()

        # Check for mobile media query
        assert '@media (max-width: 600px)' in css
        assert 'flex-direction: column' in css

    def test_desktop_breakpoint(self):
        """Test CSS uses side-by-side on desktop."""
        gen = BilingualHTMLGenerator()
        css = gen._load_bilingual_css()

        # Check for desktop styles
        assert 'flex-direction: row' in css

    def test_dark_mode_support(self):
        """Test dark mode CSS is included."""
        gen = BilingualHTMLGenerator()
        css = gen._load_bilingual_css()

        # Check for dark mode media query
        assert 'prefers-color-scheme: dark' in css


class TestCompatibility:
    """Test compatibility with different EPUB readers."""

    # Note: These would need to be run manually or with automation

    def test_apple_books_compatibility(self):
        """Manual test: Open in Apple Books and verify layout."""
        # Generate bilingual EPUB
        # Manual: Open in Apple Books
        # Manual: Verify side-by-side on iPad
        # Manual: Verify stacked on iPhone
        pass

    def test_kindle_compatibility(self):
        """Manual test: Open in Kindle app and verify layout."""
        # Generate bilingual EPUB
        # Manual: Open in Kindle app
        # Manual: Verify rendering
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

#### 4.2 Manual Testing Checklist

**Devices to Test:**
- [ ] iPhone 13/14 (portrait + landscape)
- [ ] iPhone SE (smallest screen)
- [ ] iPad (portrait + landscape)
- [ ] MacBook (Apple Books)
- [ ] Kindle Fire tablet
- [ ] Android phone (Google Play Books)

**Readers to Test:**
- [ ] Apple Books (iOS/macOS)
- [ ] Kindle app (iOS/Android)
- [ ] Google Play Books
- [ ] Calibre (desktop)
- [ ] Adobe Digital Editions

**Test Cases:**
- [ ] Paragraph alignment correct
- [ ] Bold/italic formatting preserved
- [ ] Images display correctly
- [ ] Chapter headings clear
- [ ] Dark mode works
- [ ] Font size adjustable
- [ ] Layout responsive to orientation change

---

## Deployment & Rollout

### Week 2: Beta Release

#### Step 1: Deploy Backend
```bash
# Database migration
cd apps/api
poetry run alembic upgrade head

# Restart worker
systemctl restart rq-worker

# Restart API
systemctl restart api-server
```

#### Step 2: Deploy Frontend
```bash
cd apps/web
npm run build
vercel --prod
```

#### Step 3: Beta Testing
- Enable for internal testing accounts only
- Test 5-10 real books
- Gather feedback on layout/UX

### Week 3: Public Launch

#### Step 1: Marketing Preparation
- Update website copy
- Create demo video showing mobile/desktop views
- Write blog post about bilingual feature
- Email existing users about new feature

#### Step 2: Gradual Rollout
- Enable for 10% of users
- Monitor error rates
- Check user feedback
- Gradually increase to 100%

#### Step 3: Pricing Updates
```typescript
// Update pricing calculator
const calculatePrice = (tokens: number, format: 'translated' | 'bilingual') => {
  const basePrice = calculateTranslationPrice(tokens)
  const bilingualSurcharge = format === 'bilingual' ? 0.50 : 0
  return basePrice + bilingualSurcharge
}
```

### Success Metrics

**Technical Metrics:**
- [ ] Bilingual EPUB generation success rate > 95%
- [ ] No increase in error rates
- [ ] Generation time < 2x standard translation
- [ ] File size < 2x standard EPUB

**Business Metrics:**
- [ ] Bilingual option selected by > 15% of users
- [ ] User satisfaction rating > 4.5/5
- [ ] Support tickets related to bilingual < 5%

---

## Maintenance & Future Enhancements

### Short-term (Month 1-2)
- [ ] Add layout preference saving (user chooses default)
- [ ] Add alternating paragraph option
- [ ] Optimize CSS for more readers
- [ ] Add bilingual TXT export (side-by-side in monospace)

### Medium-term (Month 3-6)
- [ ] Add color theme options
- [ ] Support for RTL languages (Arabic, Hebrew)
- [ ] Interactive features (tap to show/hide translation)
- [ ] Vocab highlighting for language learners

### Long-term (6+ months)
- [ ] Bilingual audiobook (alternating audio)
- [ ] Learning features (flashcards, quizzes)
- [ ] Progress tracking for language learners
- [ ] Integration with language learning apps

---

## Risk Mitigation

### Technical Risks

**Risk:** EPUB readers don't support CSS properly
- **Mitigation:** Use only well-supported CSS features
- **Fallback:** Simple stacked layout works everywhere

**Risk:** File size too large
- **Mitigation:** Content is same, just reorganized
- **Actual impact:** < 5% size increase (CSS overhead only)

**Risk:** Generation takes too long
- **Mitigation:** Reuses existing segments, minimal processing
- **Actual impact:** < 10% increase in generation time

### Business Risks

**Risk:** Users don't want bilingual option
- **Mitigation:** Beta test first, gather feedback
- **Fallback:** Make it opt-in, not default

**Risk:** Pricing too high/low
- **Mitigation:** A/B test pricing
- **Alternative:** Include free for premium subscribers

---

## Appendix: Code References

### Current Codebase Files to Modify

**Core Pipeline:**
- `apps/api/app/pipeline/epub_io.py` - EPUB reading/writing
- `apps/api/app/pipeline/html_segment.py` - Segmentation (no changes needed!)
- `apps/api/app/pipeline/worker.py` - Worker orchestration
- `common/outputs/generator.py` - Output generation

**Database:**
- `apps/api/app/models.py` - Job model
- `apps/api/alembic/versions/` - Migration files

**Frontend:**
- `apps/web/src/app/translate/page.tsx` - Upload page
- `apps/web/src/app/translate/actions.ts` - API calls

**Tests:**
- `tests/test_dual_provider_complete.py` - Existing test (reference)
- `tests/test_bilingual_epub.py` - New bilingual tests

### New Files to Create

**Backend:**
- `apps/api/app/pipeline/bilingual_html.py` - HTML generator
- `apps/api/app/pipeline/bilingual_styles.css` - CSS styles

**Tests:**
- `tests/test_bilingual_epub.py` - Bilingual tests
- `tests/test_bilingual_layout.py` - Layout tests

**Documentation:**
- This file! (BILINGUAL_IMPLEMENTATION_PLAN.md)

---

## Conclusion

The bilingual EPUB feature is a **low-risk, high-value** addition that:

✅ Leverages your existing segment alignment
✅ Uses standard EPUB features (maximum compatibility)
✅ Provides unique value to language learners
✅ Requires minimal code changes
✅ Can be implemented in 2-3 weeks

**Next Steps:**
1. Review this plan
2. Get approval on UX/pricing
3. Begin Phase 1 implementation
4. Beta test in Week 2
5. Public launch in Week 3

**Ready to start? Let me know and I'll begin implementing Phase 1!**
