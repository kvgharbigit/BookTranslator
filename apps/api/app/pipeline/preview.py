"""Preview service for generating sample translations of EPUB files.

This module provides functionality to translate the first N words of an EPUB
file for preview purposes, reusing the existing translation pipeline.
"""

import os
import tempfile
import asyncio
from typing import Optional, Tuple, List
from bs4 import BeautifulSoup

from app.pipeline.epub_io import EPUBProcessor
from app.pipeline.html_segment import HTMLSegmenter
from app.pipeline.translate import TranslationOrchestrator
from app.storage import get_storage
from app.providers.groq import GroqLlamaProvider
from app.config import settings
from app.logger import get_logger

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
        model: Optional[str] = None
    ) -> Tuple[str, int]:
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

        # Use Groq Llama 3.1 8B by default for fast, cheap previews
        if provider == "groq" and model is None:
            model = "llama-3.1-8b-instant"

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

            # Limit documents to first N words
            limited_docs, actual_words = self._limit_to_words(spine_docs, max_words)
            logger.info(f"Limited to {len(limited_docs)} documents, {actual_words} words")

            # Segment HTML (extracts translatable text while preserving structure)
            logger.info("Segmenting HTML content")
            segments, segment_maps = self.segmenter.segment_documents(limited_docs)
            logger.info(f"Extracted {len(segments)} segments")

            # Get translation provider (use Groq with specific model for preview)
            translation_provider = GroqLlamaProvider(
                api_key=settings.groq_api_key,
                model=model
            )

            # Translate segments
            logger.info(f"Translating {len(segments)} segments with {provider}/{model}")
            orchestrator = TranslationOrchestrator(translation_provider)
            translated_segments = await orchestrator.translate_segments(
                segments, target_lang
            )

            # Reconstruct HTML with translations
            logger.info("Reconstructing HTML with translations")
            translated_docs = self.segmenter.reconstruct_documents(
                translated_segments, segment_maps, limited_docs
            )

            # Format as single HTML document for preview display
            preview_html = self._format_preview_html(translated_docs)

            logger.info(f"Preview generated successfully: {actual_words} words")
            return preview_html, actual_words

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
                # This document would exceed limit
                if len(limited_docs) == 0:
                    # Include at least one document even if it exceeds limit
                    limited_docs.append(doc)
                    total_words += word_count
                break

            limited_docs.append(doc)
            total_words += word_count

            # Stop if we've hit the target
            if total_words >= max_words:
                break

        return limited_docs, total_words

    def _format_preview_html(self, translated_docs: List[dict]) -> str:
        """Format translated documents into a single HTML preview.

        Args:
            translated_docs: List of translated spine document dicts

        Returns:
            Single HTML string suitable for iframe display
        """
        # Combine all document contents
        combined_html = []

        for i, doc in enumerate(translated_docs):
            content = doc['content']

            # Add visual separator between documents (chapters)
            if i > 0:
                combined_html.append('<hr style="margin: 2em 0; border: 1px solid #e5e7eb;" />')

            combined_html.append(content)

        # Wrap in basic HTML structure with minimal styling
        preview_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            color: #1f2937;
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: #111827;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
        }}
        p {{
            margin-bottom: 1em;
        }}
        img {{
            max-width: 100%;
            height: auto;
        }}
    </style>
</head>
<body>
    <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 1em; margin-bottom: 2em; border-radius: 4px;">
        <strong>📖 Preview - First ~1000 Words</strong>
        <p style="margin: 0.5em 0 0 0; font-size: 0.9em; color: #92400e;">
            This is a sample showing translation quality. The full book will be translated with the same quality.
        </p>
    </div>
    {''.join(combined_html)}
</body>
</html>
"""

        return preview_html
