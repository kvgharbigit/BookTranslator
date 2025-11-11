"""
Bilingual HTML generation - Production ready version.
Maximum compatibility, minimal complexity.

Generates side-by-side bilingual content for EPUB readers with
battle-tested CSS that works across all major readers.
"""
from typing import List, Dict

from app.logger import get_logger

logger = get_logger(__name__)


class BilingualHTMLGenerator:
    """Generates bilingual HTML with table-based responsive layout."""

    def __init__(self):
        self.css = self._get_css()

    def merge_segments(
        self,
        original_segments: List[str],
        translated_segments: List[str],
        source_lang: str = "en",
        target_lang: str = "es"
    ) -> str:
        """
        Merge aligned segments into bilingual HTML.

        Args:
            original_segments: Original text segments
            translated_segments: Translated segments (1:1 aligned)
            source_lang: Source language code (e.g., 'en')
            target_lang: Target language code (e.g., 'es')

        Returns:
            Complete HTML with all bilingual pairs

        Raises:
            ValueError: If segment counts don't match
        """
        if len(original_segments) != len(translated_segments):
            raise ValueError(
                f"Segment mismatch: {len(original_segments)} original "
                f"vs {len(translated_segments)} translated"
            )

        # Get language display names
        source_name = self._get_language_name(source_lang)
        target_name = self._get_language_name(target_lang)

        # Build HTML
        html_parts = []

        for orig, trans in zip(original_segments, translated_segments):
            html_parts.append(self._create_pair(
                orig, trans,
                source_lang, target_lang,
                source_name, target_name
            ))

        return '\n'.join(html_parts)

    def _create_pair(
        self,
        original: str,
        translation: str,
        source_lang: str,
        target_lang: str,
        source_name: str,
        target_name: str
    ) -> str:
        """Create HTML for one bilingual paragraph pair."""

        return f'''<div class="bi-pair" epub:type="z3998:translation">
    <div class="bi-col bi-source" lang="{source_lang}" xml:lang="{source_lang}">
        <div class="bi-label">{source_name}</div>
        <div class="bi-content">
            {original}
        </div>
    </div>
    <div class="bi-col bi-target" lang="{target_lang}" xml:lang="{target_lang}">
        <div class="bi-label">{target_name}</div>
        <div class="bi-content">
            {translation}
        </div>
    </div>
</div>'''

    def _get_css(self) -> str:
        """Return production-ready CSS."""
        return '''/* Bilingual EPUB Styles - Production Ready */

/* Baseline: stacked (universal) */
.bi-pair {
    margin: 1em 0;
    page-break-inside: avoid;
}

.bi-col {
    padding: 0.75em;
    border: 1px solid #ddd;
}

.bi-source {
    background-color: #fafafa;
    border-bottom: 0;
}

.bi-target {
    background-color: #f5f5f5;
}

.bi-label {
    display: block;
    font-size: 0.85em;
    font-weight: 600;
    color: #555;
    margin-bottom: 0.5em;
}

.bi-content {
    line-height: 1.5;
}

/* Enhancement: side-by-side using table layout (widely supported) */
@media (min-width: 48em) {
    .bi-pair {
        display: table;
        width: 100%;
        border-collapse: collapse;
    }

    .bi-col {
        display: table-cell;
        width: 50%;
        vertical-align: top;
        border: 1px solid #ddd;
    }

    .bi-source {
        border-right: 0;
        border-bottom: 1px solid #ddd;
    }
}

.bi-col em { font-style: italic; }
.bi-col strong { font-weight: bold; }'''

    def _get_language_name(self, lang_code: str) -> str:
        """Get display name for language code."""
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
            'hi': 'हिन्दी',
            'nl': 'Nederlands',
            'pl': 'Polski',
            'tr': 'Türkçe',
            'sv': 'Svenska',
            'no': 'Norsk',
            'da': 'Dansk',
            'fi': 'Suomi',
            'cs': 'Čeština',
            'hu': 'Magyar',
            'ro': 'Română',
            'uk': 'Українська',
            'el': 'Ελληνικά',
            'he': 'עברית',
            'id': 'Indonesia',
            'ms': 'Melayu',
            'th': 'ไทย',
            'vi': 'Tiếng Việt',
        }
        return lang_map.get(lang_code, lang_code.upper())


def create_bilingual_documents(
    original_segments: List[str],
    translated_segments: List[str],
    reconstruction_maps: List[Dict],
    spine_docs: List[Dict],
    source_lang: str,
    target_lang: str
) -> List[Dict]:
    """
    Create bilingual documents from aligned segments.

    Args:
        original_segments: All original text segments
        translated_segments: All translated segments (1:1 aligned)
        reconstruction_maps: Document reconstruction metadata
        spine_docs: Original spine documents (for HTML structure)
        source_lang: Source language code (e.g., 'en')
        target_lang: Target language code (e.g., 'es')

    Returns:
        List of bilingual documents, one per original document
    """
    from bs4 import BeautifulSoup

    bilingual_gen = BilingualHTMLGenerator()
    bilingual_docs = []

    for doc_map in reconstruction_maps:
        # Extract segments for this document
        start = doc_map['segment_start']
        count = doc_map['segment_count']
        end = start + count

        orig_segs = original_segments[start:end]
        trans_segs = translated_segments[start:end]

        # Generate bilingual HTML for this document
        bilingual_html = bilingual_gen.merge_segments(
            orig_segs,
            trans_segs,
            source_lang,
            target_lang
        )

        # Get original document structure
        doc_idx = doc_map['doc_idx']
        original_doc = spine_docs[doc_idx]
        original_content = original_doc['content']

        # Parse original document and replace body content with bilingual HTML
        soup = BeautifulSoup(original_content, 'lxml-xml', from_encoding='utf-8')

        # Find body or create one if it doesn't exist
        body = soup.find('body')
        if body:
            # Clear existing content and insert bilingual HTML
            body.clear()
            body.append(BeautifulSoup(bilingual_html, 'html.parser'))
        else:
            # If no body, try to find the root and replace all content
            logger.warning(f"No body tag found in document {doc_idx}, using full replacement")
            # Wrap bilingual HTML in proper XHTML structure
            full_html = f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>{doc_map['doc_title']}</title>
</head>
<body>
{bilingual_html}
</body>
</html>'''
            soup = BeautifulSoup(full_html, 'lxml-xml', from_encoding='utf-8')

        bilingual_docs.append({
            'id': doc_map['doc_id'],
            'href': doc_map['doc_href'],
            'title': doc_map['doc_title'],
            'content': str(soup)
        })

        logger.info(
            f"Created bilingual document {doc_map['doc_idx']}: "
            f"{count} segment pairs"
        )

    logger.info(f"Created {len(bilingual_docs)} bilingual documents")
    return bilingual_docs
