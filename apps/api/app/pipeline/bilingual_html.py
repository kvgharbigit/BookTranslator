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
        """Create HTML for one bilingual paragraph pair.

        Layout: TARGET (left/first) | SOURCE (right/second)
        Users read primarily in target language, reference source when needed.
        """

        return f'''<div class="bi-pair" epub:type="z3998:translation">
    <div class="bi-col bi-target" lang="{target_lang}" xml:lang="{target_lang}">
        {translation}
    </div>
    <div class="bi-col bi-source" lang="{source_lang}" xml:lang="{source_lang}">
        {original}
    </div>
</div>'''

    def _get_css(self) -> str:
        """Return CSS for bilingual subtitle styling.

        Subtitles appear inline in very small, subtle gray text.
        No extra spacing - just inherits parent element's natural spacing.
        """
        return '''/* Bilingual Subtitle Styles - Minimal and Unobtrusive */

.bilingual-subtitle {
    display: inline;
    font-size: 0.65em;
    font-style: italic;
    color: #bbb;
    margin: 0;
    padding: 0;
    line-height: 1.4;
    vertical-align: baseline;
    text-decoration: none;
    white-space: normal;
}

/* Ensure subtitles don't inherit bold from parent */
h1 .bilingual-subtitle,
h2 .bilingual-subtitle,
h3 .bilingual-subtitle,
h4 .bilingual-subtitle,
h5 .bilingual-subtitle,
h6 .bilingual-subtitle,
strong .bilingual-subtitle,
b .bilingual-subtitle {
    font-weight: normal !important;
}

/* Ensure block elements maintain block display and spacing */
p, h1, h2, h3, h4, h5, h6, div, blockquote, li {
    display: block !important;
}

/* Ensure proper spacing between block elements */
p {
    margin: 1em 0 !important;
}

h1, h2, h3, h4, h5, h6 {
    margin: 1em 0 0.5em 0 !important;
    display: block !important;
}

/* Line breaks should be visible */
br {
    display: block !important;
    content: "" !important;
    margin: 0.5em 0 !important;
}

/* Bilingual pair container - ensure block display with proper spacing */
.bi-pair {
    display: block;
    margin-bottom: 1em;
}

.bi-col {
    display: block;
    margin: 0;
}'''

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

    Preserves original HTML structure and formatting, inserting source text
    as subtitles below each translated element.

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
    from bs4 import BeautifulSoup, NavigableString

    bilingual_docs = []

    for doc_map in reconstruction_maps:
        # Extract segments for this document
        start = doc_map['segment_start']
        count = doc_map['segment_count']
        end = start + count

        orig_segs = original_segments[start:end]
        trans_segs = translated_segments[start:end]

        # Get original document
        doc_idx = doc_map['doc_idx']
        original_doc = spine_docs[doc_idx]
        original_content = original_doc['content']

        # Parse original document
        soup = BeautifulSoup(original_content, 'lxml-xml', from_encoding='utf-8')

        # Reconstruct with bilingual subtitles
        reconstructed_html = _reconstruct_bilingual_html(
            soup,
            orig_segs,
            trans_segs,
            source_lang,
            target_lang
        )

        bilingual_docs.append({
            'id': doc_map['doc_id'],
            'href': doc_map['doc_href'],
            'title': doc_map['doc_title'],
            'content': reconstructed_html
        })

        logger.info(
            f"Created bilingual document {doc_map['doc_idx']}: "
            f"{count} segment pairs"
        )

    logger.info(f"Created {len(bilingual_docs)} bilingual documents")
    return bilingual_docs


def _reconstruct_bilingual_html(
    soup,
    original_segments: List[str],
    translated_segments: List[str],
    source_lang: str,
    target_lang: str
) -> str:
    """
    Reconstruct HTML with bilingual content, preserving all original formatting.

    For each text node:
    1. Replace with translated text
    2. Insert subtitle span with original text right after parent element
    """
    from bs4 import NavigableString, Tag

    segment_idx = 0
    no_translate_tags = {'pre', 'code', 'script', 'style', 'svg', 'image', 'img'}

    # Track which elements we've processed to add subtitles
    elements_to_subtitle = []

    # First pass: Replace text with translations and mark elements for subtitles
    for element in soup.find_all(string=True):
        if isinstance(element, NavigableString) and element.strip():
            parent = element.parent

            # Skip non-translatable content
            if _should_skip_element(parent, no_translate_tags):
                continue

            text = element.strip()
            # Same criteria as segmentation
            if (len(text) >= 3 and
                not text.isdigit() and
                text.lower() not in ['html', 'head', 'body', 'div', 'span'] and
                segment_idx < len(translated_segments)):

                # Replace with translation
                element.replace_with(translated_segments[segment_idx])

                # Mark parent for subtitle insertion
                elements_to_subtitle.append({
                    'parent': parent,
                    'original': original_segments[segment_idx],
                    'translation': translated_segments[segment_idx]
                })

                segment_idx += 1

    # Second pass: Insert subtitle spans inside parent elements
    # Block-level elements that should have <br> before subtitle
    block_elements = {'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div', 'blockquote', 'li', 'td', 'th', 'dd', 'dt'}

    for item in elements_to_subtitle:
        try:
            parent = item['parent']
            original_text = item['original']

            # Create subtitle span
            subtitle = soup.new_tag('span', attrs={
                'class': 'bilingual-subtitle',
                'lang': source_lang,
                'xml:lang': source_lang
            })
            subtitle.string = original_text

            # Only add <br> if parent is a block-level element
            # For inline parents (like <em>, <strong>, <a>), just append subtitle
            if parent.name in block_elements:
                br = soup.new_tag('br')
                parent.append(br)
                parent.append(subtitle)
            else:
                # For inline elements, add a space before subtitle
                parent.append(' ')
                parent.append(subtitle)
        except Exception as e:
            logger.warning(f"Failed to add subtitle to element '{parent.name if hasattr(parent, 'name') else 'unknown'}': {e}")
            continue  # Skip this subtitle but continue with others

    return str(soup)


def _should_skip_element(element, no_translate_tags: set) -> bool:
    """Check if element content should be skipped for translation."""
    if not element:
        return True

    # Check if element or any parent is in no-translate tags
    current = element
    while current:
        if hasattr(current, 'name') and current.name in no_translate_tags:
            return True
        current = current.parent if hasattr(current, 'parent') else None

    return False
