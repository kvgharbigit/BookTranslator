"""Preview service for generating sample translations of EPUB files.

This module provides functionality to translate the first N words of an EPUB
file for preview purposes, reusing the existing translation pipeline.
"""

import os
import tempfile
import asyncio
import base64
import re
from typing import Optional, Tuple, List, Dict
from bs4 import BeautifulSoup, NavigableString

from app.pipeline.epub_io import EPUBProcessor
from app.pipeline.html_segment import HTMLSegmenter
from app.pipeline.translate import TranslationOrchestrator
from app.storage import get_storage
from app.providers.factory import get_provider
from app.logger import get_logger
from app.config.models import get_default_model

logger = get_logger(__name__)


class PreviewService:
    """Service for generating preview translations of EPUB files.

    Reuses existing translation pipeline components (EPUBProcessor, HTMLSegmenter,
    TranslationOrchestrator) to translate a limited portion of an EPUB file.
    """

    def __init__(self):
        self.epub_processor = EPUBProcessor()
        self.segmenter = HTMLSegmenter()
        self.storage = get_storage()

    async def generate_preview(
        self,
        r2_key: str,
        target_lang: str,
        max_words: int = 1000,
        provider: str = "groq",
        model: Optional[str] = None,
        progress_callback: Optional[callable] = None
    ) -> Tuple[str, int, str]:
        """Generate a preview translation of the first N words of an EPUB.

        Args:
            r2_key: R2 storage key for the EPUB file
            target_lang: Target language code (e.g., 'es', 'fr', 'de')
            max_words: Maximum number of words to translate (default: 1000)
            provider: Translation provider to use (default: 'groq' for speed/cost)
            model: Optional specific model (default: llama-3.1-8b-instant for groq)

        Returns:
            Tuple of (preview_html, actual_word_count)

        Raises:
            Exception: If preview generation fails
        """
        logger.info(f"Generating preview for {r2_key}, lang={target_lang}, max_words={max_words}")

        # Use Gemini Flash as primary (fast and reliable), Groq as fallback
        # Default models for each provider - use centralized configuration
        if model is None:
            model = get_default_model(provider)

        # Download EPUB from R2 to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.epub') as tmp:
            epub_path = tmp.name

        try:
            # Download from R2
            logger.info(f"Downloading EPUB from R2: {r2_key}")
            await asyncio.to_thread(self.storage.download_file, r2_key, epub_path)

            # Read EPUB structure
            logger.info("Reading EPUB structure")
            book, spine_docs = self.epub_processor.read_epub(epub_path)

            # Extract original CSS and images from EPUB
            css_content = self._extract_css_from_epub(book)
            logger.info(f"Extracted {len(css_content)} chars of CSS from EPUB")

            image_map = self._extract_images_from_epub(book)
            logger.info(f"Extracted {len(set(image_map.values()))} unique images from EPUB")

            # Limit documents to first N words
            limited_docs, actual_words = self._limit_to_words(spine_docs, max_words)
            logger.info(f"Limited to {len(limited_docs)} documents, {actual_words} words")

            # Segment HTML (extracts translatable text while preserving structure)
            logger.info("Segmenting HTML content")
            segments, segment_maps = self.segmenter.segment_documents(limited_docs)
            logger.info(f"Extracted {len(segments)} segments")

            # Setup providers: Groq primary (cheap), Gemini fallback (reliable)
            # Same pattern as worker.py lines 108-131
            primary_provider = get_provider("groq")
            fallback_provider = get_provider("gemini")

            # Translate segments with fun progress messages
            logger.info(f"Translating {len(segments)} segments with Groq (primary) + Gemini (fallback)")

            # Create fun progress callback with language-specific emojis
            def batch_progress_callback(current_batch: int, total_batches: int):
                progress_message = self._get_fun_progress_message(current_batch, total_batches, target_lang)
                logger.info(progress_message)

                # If we have a progress callback from SSE, send it the message
                if progress_callback:
                    progress_callback(progress_message)

            orchestrator = TranslationOrchestrator()
            translated_segments, tokens_used, provider_used = await orchestrator.translate_segments(
                segments=segments,
                target_lang=target_lang,
                primary_provider=primary_provider,
                fallback_provider=fallback_provider,
                progress_callback=batch_progress_callback
            )

            # Calculate total cost for preview
            from app.config.models import estimate_cost
            # Rough split: 45% input, 55% output (based on typical translation patterns)
            input_tokens = int(tokens_used * 0.45)
            output_tokens = int(tokens_used * 0.55)
            total_cost = estimate_cost(provider_used, model, input_tokens, output_tokens)

            logger.info(f"✅ Translation completed using {provider_used}")
            logger.info(f"💰 Preview translation cost: ~${total_cost:.4f} USD ({tokens_used:,} tokens)")

            # Reconstruct HTML with translations
            logger.info("Reconstructing HTML with translations")
            translated_docs = self.segmenter.reconstruct_documents(
                translated_segments, segment_maps, limited_docs
            )

            # Format as single HTML document for preview display with images
            preview_html = self._format_preview_html(
                translated_docs, css_content, image_map, target_lang
            )

            logger.info(f"Preview generated successfully: {actual_words} words using {provider_used}")
            return preview_html, actual_words, provider_used

        except Exception as e:
            logger.error(f"Preview generation failed: {e}", exc_info=True)
            raise
        finally:
            # Cleanup temporary file
            if os.path.exists(epub_path):
                os.unlink(epub_path)

    def _limit_to_words(
        self,
        spine_docs: List[dict],
        max_words: int
    ) -> Tuple[List[dict], int]:
        """Limit spine documents to approximately max_words.

        Reads documents sequentially until word count reaches max_words.
        Truncates the last document mid-content if needed to hit the word limit.

        Args:
            spine_docs: List of spine document dicts with 'content' key
            max_words: Maximum words to include

        Returns:
            Tuple of (limited_docs, actual_word_count)
        """
        limited_docs = []
        total_words = 0

        for doc in spine_docs:
            # Extract text from HTML to count words
            soup = BeautifulSoup(doc['content'], 'html.parser')
            text = soup.get_text()
            word_count = len(text.split())

            if total_words + word_count > max_words:
                # This document would exceed limit - truncate it
                words_remaining = max_words - total_words
                if words_remaining > 0:
                    truncated_doc = self._truncate_document_to_words(doc, words_remaining)
                    limited_docs.append(truncated_doc)
                    total_words += words_remaining
                break

            # Include full document
            limited_docs.append(doc)
            total_words += word_count

            # Stop if we've hit the target exactly
            if total_words >= max_words:
                break

        return limited_docs, total_words

    def _truncate_document_to_words(self, doc: dict, max_words: int) -> dict:
        """Truncate a document's content to approximately max_words.

        Args:
            doc: Document dict with 'content' key
            max_words: Maximum words to include

        Returns:
            New document dict with truncated content
        """
        soup = BeautifulSoup(doc['content'], 'html.parser')

        # Find all text nodes and truncate at word boundary
        words_collected = 0

        for element in soup.find_all(string=True):
            if isinstance(element, NavigableString):
                text = str(element)
                words = text.split()

                if words_collected + len(words) > max_words:
                    # Truncate this text node
                    words_to_take = max_words - words_collected
                    truncated_text = ' '.join(words[:words_to_take]) + '...'
                    element.replace_with(truncated_text)
                    words_collected = max_words

                    # Remove all subsequent siblings and their content
                    parent = element.parent
                    if parent:
                        # Remove all following siblings
                        for sibling in list(element.next_siblings):
                            if hasattr(sibling, 'extract'):
                                sibling.extract()
                    break
                else:
                    words_collected += len(words)

        return {
            'id': doc['id'],
            'href': doc['href'],
            'title': doc['title'],
            'content': str(soup)
        }

    def _extract_css_from_epub(self, book) -> str:
        """Extract CSS stylesheets from EPUB for preview display.

        Args:
            book: EbookLib Book object

        Returns:
            Combined CSS content from all stylesheets
        """
        import ebooklib

        css_content = []
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_STYLE:
                try:
                    css = item.get_content().decode('utf-8')
                    css_content.append(css)
                except Exception as e:
                    logger.warning(f"Failed to extract CSS: {e}")

        return '\n\n'.join(css_content)

    def _extract_images_from_epub(self, book) -> Dict[str, str]:
        """Extract images from EPUB and encode as base64 data URIs.

        Args:
            book: EbookLib Book object

        Returns:
            Dictionary mapping image paths to base64 data URIs
        """
        import ebooklib

        image_map = {}
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_IMAGE:
                try:
                    img_path = item.get_name()
                    img_content = item.get_content()

                    # Determine MIME type from extension
                    ext = img_path.lower().split('.')[-1]
                    mime_types = {
                        'jpg': 'image/jpeg', 'jpeg': 'image/jpeg',
                        'png': 'image/png', 'gif': 'image/gif',
                        'svg': 'image/svg+xml', 'webp': 'image/webp'
                    }
                    mime_type = mime_types.get(ext, 'image/jpeg')

                    # Encode as base64 data URI
                    img_base64 = base64.b64encode(img_content).decode('utf-8')
                    data_uri = f"data:{mime_type};base64,{img_base64}"

                    # Store with multiple path variations for matching
                    image_map[img_path] = data_uri
                    image_map[img_path.lstrip('/')] = data_uri
                    image_map[img_path.lstrip('../')] = data_uri
                    image_map[os.path.basename(img_path)] = data_uri

                except Exception as e:
                    logger.warning(f"Failed to extract image {item.get_name()}: {e}")

        return image_map

    def _get_fun_progress_message(self, current_batch: int, total_batches: int, target_lang: str) -> str:
        """Generate fun progress messages with emojis during translation.

        Args:
            current_batch: Current batch number (1-indexed)
            total_batches: Total number of batches
            target_lang: Target language code

        Returns:
            Fun progress message with emojis
        """
        # Language-specific emojis and suffixes
        language_emojis = {
            'es': ('🇪🇸', 'Spanish-ifying'),
            'fr': ('🇫🇷', 'French-ifying'),
            'de': ('🇩🇪', 'German-ifying'),
            'it': ('🇮🇹', 'Italian-ifying'),
            'pt': ('🇵🇹', 'Portuguese-ifying'),
            'ru': ('🇷🇺', 'Russian-ifying'),
            'ja': ('🇯🇵', 'Japanese-ifying'),
            'zh': ('🇨🇳', 'Chinese-ifying'),
            'ko': ('🇰🇷', 'Korean-ifying'),
            'ar': ('🇸🇦', 'Arabic-ifying'),
            'hi': ('🇮🇳', 'Hindi-ifying'),
            'nl': ('🇳🇱', 'Dutch-ifying'),
            'pl': ('🇵🇱', 'Polish-ifying'),
            'tr': ('🇹🇷', 'Turkish-ifying'),
            'sv': ('🇸🇪', 'Swedish-ifying'),
            'da': ('🇩🇰', 'Danish-ifying'),
            'fi': ('🇫🇮', 'Finnish-ifying'),
            'no': ('🇳🇴', 'Norwegian-ifying'),
            'cs': ('🇨🇿', 'Czech-ifying'),
            'el': ('🇬🇷', 'Greek-ifying'),
            'he': ('🇮🇱', 'Hebrew-ifying'),
            'th': ('🇹🇭', 'Thai-ifying'),
            'vi': ('🇻🇳', 'Vietnamese-ifying'),
            'id': ('🇮🇩', 'Indonesian-ifying'),
            'uk': ('🇺🇦', 'Ukrainian-ifying'),
            'ro': ('🇷🇴', 'Romanian-ifying'),
            'hu': ('🇭🇺', 'Hungarian-ifying'),
            'bg': ('🇧🇬', 'Bulgarian-ifying'),
        }

        # Get language-specific emoji and suffix, or use default
        emoji, lang_suffix = language_emojis.get(target_lang.lower(), ('🌍', f'{target_lang.upper()}-ifying'))

        # Progress percentage
        progress_pct = int((current_batch / total_batches) * 100)

        # Fun messages based on progress
        if current_batch == 1:
            messages = [
                f"{emoji} ✨ Starting the magic...",
                f"{emoji} 🎨 Warming up the translation engines...",
                f"{emoji} 🚀 Beginning the {lang_suffix} journey...",
                f"{emoji} 📚 Opening the linguistic toolbox...",
            ]
        elif current_batch == total_batches:
            messages = [
                f"{emoji} 🎉 {lang_suffix} complete! Adding final touches...",
                f"{emoji} ✅ Making it beautiful... Done!",
                f"{emoji} 🌟 Polishing the masterpiece...",
                f"{emoji} 🎊 Finishing touches applied!",
            ]
        elif progress_pct < 33:
            messages = [
                f"{emoji} 🔄 {lang_suffix} in progress... ({progress_pct}%)",
                f"{emoji} 💫 Sprinkling linguistic magic... ({progress_pct}%)",
                f"{emoji} 🎯 Finding the perfect words... ({progress_pct}%)",
                f"{emoji} 📖 Turning pages... ({progress_pct}%)",
            ]
        elif progress_pct < 66:
            messages = [
                f"{emoji} 🎨 Making it beautiful... ({progress_pct}%)",
                f"{emoji} ⚡ Halfway through the {lang_suffix}! ({progress_pct}%)",
                f"{emoji} 🔥 On a roll now... ({progress_pct}%)",
                f"{emoji} 🌈 Words flowing beautifully... ({progress_pct}%)",
            ]
        else:
            messages = [
                f"{emoji} 🏁 Almost there... ({progress_pct}%)",
                f"{emoji} 💪 Final stretch of {lang_suffix}... ({progress_pct}%)",
                f"{emoji} ✨ Perfecting the translation... ({progress_pct}%)",
                f"{emoji} 🎯 Crossing the finish line... ({progress_pct}%)",
            ]

        # Rotate through messages based on batch number for variety
        return messages[current_batch % len(messages)]

    def _format_preview_html(
        self,
        translated_docs: List[dict],
        css_content: str = "",
        image_map: Optional[Dict[str, str]] = None,
        target_lang: str = "en"
    ) -> str:
        """Format translated documents into a single HTML preview.

        Uses the EXACT same HTML from reconstruct_documents() plus the original EPUB CSS
        to ensure the preview looks identical to the final EPUB.

        Args:
            translated_docs: List of translated spine document dicts (from reconstruct_documents)
            css_content: Original CSS from the EPUB
            image_map: Optional dictionary mapping image paths to base64 data URIs
            target_lang: Target language code for RTL detection

        Returns:
            Single HTML string suitable for iframe display
        """
        # Combine all document contents (using EXACT reconstructed HTML)
        combined_html = []

        for i, doc in enumerate(translated_docs):
            content = doc['content']

            # Add visual separator between documents (chapters)
            if i > 0:
                combined_html.append('<hr style="margin: 2em 0; border: 1px solid #e5e7eb; opacity: 0.5;" />')

            combined_html.append(content)

        # Join HTML and replace image src attributes with base64 data URIs
        combined_html_str = ''.join(combined_html)

        if image_map:
            # Replace all <img> tags with base64 data URIs
            def replace_img_src(match):
                img_tag = match.group(0)
                src_match = re.search(r'src=(?:"([^"]*)"|\'([^\']*)\')', img_tag, re.IGNORECASE)
                if not src_match:
                    return img_tag

                src = src_match.group(1) or src_match.group(2)

                # Try different path variations to find the image
                for variant in [src, src.lstrip('/'), src.lstrip('../'), os.path.basename(src)]:
                    if variant in image_map:
                        data_uri = image_map[variant]
                        # Replace src in the tag
                        return img_tag.replace(f'src="{src}"', f'src="{data_uri}"').replace(f"src='{src}'", f"src='{data_uri}'")

                logger.warning(f"Image not found in image_map: {src}")
                return img_tag

            combined_html_str = re.sub(
                r'<img[^>]*>',
                replace_img_src,
                combined_html_str,
                flags=re.IGNORECASE
            )

        # Determine if RTL language
        rtl_languages = {'ar', 'he', 'fa', 'ur'}  # Arabic, Hebrew, Farsi, Urdu
        is_rtl = target_lang.lower() in rtl_languages

        # Set HTML attributes for RTL support
        dir_attr = ' dir="rtl"' if is_rtl else ''
        lang_attr = f' lang="{target_lang}"'
        direction_css = 'rtl' if is_rtl else 'ltr'
        text_align = 'right' if is_rtl else 'left'

        # Wrap with original EPUB CSS plus minimal responsive wrapper
        preview_html = f"""<!DOCTYPE html>
<html{lang_attr}{dir_attr}>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        /* Original EPUB CSS */
        {css_content}

        /* Minimal responsive wrapper - don't override EPUB styles */
        body {{
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            direction: {direction_css};
            text-align: {text_align};
        }}

        /* Ensure images are responsive */
        img {{
            max-width: 100% !important;
            height: auto !important;
        }}

        /* Disable hover color changes on all elements */
        * {{
            pointer-events: auto !important;
        }}

        *:hover {{
            color: inherit !important;
        }}

        /* Preview banner */
        .preview-banner {{
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
            padding: 1em;
            margin-bottom: 2em;
            border-radius: 4px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }}
    </style>
</head>
<body>
    <div class="preview-banner">
        <strong>📖 Preview - First ~1500 Words</strong>
        <p style="margin: 0.5em 0 0 0; font-size: 0.9em; color: #92400e;">
            This shows exactly how your translated book will look with the same styling and formatting.
        </p>
    </div>
    {combined_html_str}
</body>
</html>"""

        return preview_html
