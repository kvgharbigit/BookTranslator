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

            # Setup providers for PREVIEW translations:
            # - Groq Llama 3.1 8B (primary) - Fast & cheap for previews
            # - Gemini 2.5 Flash Lite (fallback) - For Tier 4 languages (auto-switched by TranslationOrchestrator)
            # Note: Full book translations ALWAYS use Gemini for best quality
            primary_provider = get_provider("groq")
            fallback_provider = get_provider("gemini")

            # Translate segments with fun progress messages
            logger.info(f"Translating preview with Groq (Llama) primary + Gemini fallback (auto for Tier 4 langs)")

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
        # Language-specific configurations with cultural references
        language_config = {
            'es': {
                'emoji': '🇪🇸',
                'start': ['¡Hola! Starting Spanish magic...', '🌮 Sprinkling some español...', '💃 ¡Vámonos! Let\'s translate...'],
                'progress': ['Making it muy bonito...', '🎸 Getting that Spanish rhythm...', 'Adding some sabor...'],
                'finish': ['¡Perfecto! Spanish translation complete!', '🎉 ¡Olé! All done!', '✨ ¡Excelente! Finished!']
            },
            'fr': {
                'emoji': '🇫🇷',
                'start': ['Bonjour! Starting French elegance...', '🥐 Baking some beautiful français...', '🗼 Channeling Parisian charm...'],
                'progress': ['Making it très magnifique...', '🎨 Painting with French flair...', 'Adding that je ne sais quoi...'],
                'finish': ['Voilà! French perfection achieved!', '🎊 C\'est fini! All done!', '✨ Magnifique! Complete!']
            },
            'de': {
                'emoji': '🇩🇪',
                'start': ['Guten Tag! Beginning German precision...', '🍺 Starting the Deutsch journey...', '⚙️ German engineering engaged...'],
                'progress': ['Making it wunderbar...', '🏰 Building with German precision...', 'Adding some gemütlichkeit...'],
                'finish': ['Ausgezeichnet! German translation done!', '🎉 Perfekt! All finished!', '✨ Wunderbar! Complete!']
            },
            'it': {
                'emoji': '🇮🇹',
                'start': ['Ciao! Starting Italian artistry...', '🍝 Cooking up some italiano...', '🎭 Italian opera of words begins...'],
                'progress': ['Making it bellissimo...', '🎨 Painting with Italian passion...', 'Adding that dolce vita touch...'],
                'finish': ['Perfetto! Italian masterpiece done!', '🎉 Bravo! All finished!', '✨ Fantastico! Complete!']
            },
            'pt': {
                'emoji': '🇵🇹',
                'start': ['Olá! Starting Portuguese soul...', '⚽ Kicking off português...', '🎵 Portuguese saudade begins...'],
                'progress': ['Making it muito bonito...', '🌊 Flowing like Portuguese waves...', 'Adding some alegria...'],
                'finish': ['Perfeito! Portuguese beauty complete!', '🎉 Ótimo! All done!', '✨ Maravilhoso! Finished!']
            },
            'ja': {
                'emoji': '🇯🇵',
                'start': ['こんにちは! Starting Japanese harmony...', '🍜 Preparing 日本語 magic...', '🏯 Japanese precision activated...'],
                'progress': ['Making it 美しい (beautiful)...', '🎌 Weaving Japanese elegance...', 'Adding that 和 (harmony)...'],
                'finish': ['完璧! (Perfect!) Japanese done!', '🎉 素晴らしい! All complete!', '✨ できた! Finished!']
            },
            'zh': {
                'emoji': '🇨🇳',
                'start': ['你好! Starting Chinese wisdom...', '🏮 Beginning 中文 journey...', '🐉 Chinese dragon awakening...'],
                'progress': ['Making it 美丽 (beautiful)...', '🎎 Crafting with Chinese art...', 'Adding that 和谐 (harmony)...'],
                'finish': ['完美! (Perfect!) Chinese complete!', '🎉 好极了! All done!', '✨ 成功! Success!']
            },
            'ko': {
                'emoji': '🇰🇷',
                'start': ['안녕! Starting Korean flow...', '🎤 Beginning 한글 K-magic...', '🌸 Korean cherry blossoms blooming...'],
                'progress': ['Making it 아름다운 (beautiful)...', '💜 Adding K-style charm...', 'Channeling 정 (heart)...'],
                'finish': ['완벽! (Perfect!) Korean complete!', '🎉 대박! Amazing work!', '✨ 성공! Success!']
            },
            'ru': {
                'emoji': '🇷🇺',
                'start': ['Привет! Starting Russian grandeur...', '❄️ Beginning русский magic...', '🪆 Russian matryoshka unfolding...'],
                'progress': ['Making it прекрасно (beautiful)...', '🎭 Adding Russian soul...', 'Channeling that широта...'],
                'finish': ['Отлично! (Excellent!) Russian done!', '🎉 Замечательно! Wonderful!', '✨ Готово! Complete!']
            },
            'ar': {
                'emoji': '🇸🇦',
                'start': ['السلام عليكم! Arabic beauty begins...', '🕌 Starting عربي elegance...', '🌙 Arabic magic awakening...'],
                'progress': ['Making it جميل (beautiful)...', '✨ Weaving Arabic poetry...', 'Adding that روح (soul)...'],
                'finish': ['ممتاز! (Excellent!) Arabic complete!', '🎉 رائع! Wonderful!', '✨ تم! Done!']
            },
            'hi': {
                'emoji': '🇮🇳',
                'start': ['नमस्ते! Starting Hindi magic...', '🪔 Beginning हिंदी journey...', '🕉️ Hindi harmony begins...'],
                'progress': ['Making it सुंदर (beautiful)...', '🎨 Adding Indian colors...', 'Channeling that रस (essence)...'],
                'finish': ['बहुत बढ़िया! (Excellent!) Hindi done!', '🎉 शानदार! Wonderful!', '✨ पूरा! Complete!']
            },
            'nl': {
                'emoji': '🇳🇱',
                'start': ['Hallo! Starting Dutch directness...', '🌷 Beginning Nederlands charm...', '🚴 Dutch cycling through words...'],
                'progress': ['Making it mooi (beautiful)...', '🧀 Adding Dutch flavor...', 'Gezellig vibes flowing...'],
                'finish': ['Perfect! Dutch translation klaar!', '🎉 Geweldig! All done!', '✨ Fantastisch! Complete!']
            },
            'pl': {
                'emoji': '🇵🇱',
                'start': ['Cześć! Starting Polish spirit...', '🥟 Beginning polski journey...', '🦅 Polish eagle soaring...'],
                'progress': ['Making it piękny (beautiful)...', '🎨 Polish artistry flowing...', 'Adding that dusza (soul)...'],
                'finish': ['Doskonale! Polish perfection done!', '🎉 Wspaniale! Wonderful!', '✨ Gotowe! Complete!']
            },
            'tr': {
                'emoji': '🇹🇷',
                'start': ['Merhaba! Starting Turkish delight...', '☕ Beginning Türkçe magic...', '🌉 Bridging East and West...'],
                'progress': ['Making it güzel (beautiful)...', '🎭 Turkish elegance flowing...', 'Adding that keyif (pleasure)...'],
                'finish': ['Mükemmel! Turkish perfection done!', '🎉 Harika! Wonderful!', '✨ Tamam! Complete!']
            },
            'el': {
                'emoji': '🇬🇷',
                'start': ['Γεια σου! Starting Greek wisdom...', '🏛️ Beginning Ελληνικά magic...', '⚡ Zeus-level translation power...'],
                'progress': ['Making it όμορφος (beautiful)...', '🎨 Greek artistry flowing...', 'Channeling ancient wisdom...'],
                'finish': ['Τέλειο! (Perfect!) Greek complete!', '🎉 Υπέροχο! Wonderful!', '✨ Έτοιμο! Done!']
            },
            'he': {
                'emoji': '🇮🇱',
                'start': ['שלום! Starting Hebrew beauty...', '✡️ Beginning עברית journey...', '📜 Ancient meets modern...'],
                'progress': ['Making it יפה (beautiful)...', '🎨 Hebrew artistry flowing...', 'Adding that נשמה (soul)...'],
                'finish': ['מושלם! (Perfect!) Hebrew complete!', '🎉 נהדר! Wonderful!', '✨ גמור! Done!']
            },
            'th': {
                'emoji': '🇹🇭',
                'start': ['สวัสดี! Starting Thai grace...', '🙏 Beginning ไทย journey...', '🐘 Thai elegance awakening...'],
                'progress': ['Making it สวย (beautiful)...', '🌺 Thai artistry blooming...', 'Adding that สนุก (joy)...'],
                'finish': ['สมบูรณ์แบบ! (Perfect!) Thai done!', '🎉 ยอดเยี่ยม! Excellent!', '✨ เสร็จ! Complete!']
            },
            'vi': {
                'emoji': '🇻🇳',
                'start': ['Xin chào! Starting Vietnamese flow...', '🍜 Beginning Tiếng Việt magic...', '🏮 Vietnamese beauty begins...'],
                'progress': ['Making it đẹp (beautiful)...', '🎨 Vietnamese grace flowing...', 'Adding that tình (love)...'],
                'finish': ['Hoàn hảo! Vietnamese perfection!', '🎉 Tuyệt vời! Wonderful!', '✨ Xong! Done!']
            },
            'sv': {
                'emoji': '🇸🇪',
                'start': ['Hej! Starting Swedish hygge...', '☕ Beginning Svenska journey...', '🌲 Nordic magic awakening...'],
                'progress': ['Making it vacker (beautiful)...', '🎨 Swedish style flowing...', 'Adding that lagom balance...'],
                'finish': ['Perfekt! Swedish translation klar!', '🎉 Underbart! Wonderful!', '✨ Färdig! Complete!']
            },
            'da': {
                'emoji': '🇩🇰',
                'start': ['Hej! Starting Danish hygge...', '🧁 Beginning Dansk delight...', '🏰 Danish fairytale begins...'],
                'progress': ['Making it smuk (beautiful)...', '🎨 Danish charm flowing...', 'Adding that hygge warmth...'],
                'finish': ['Perfekt! Danish translation færdig!', '🎉 Fantastisk! Wonderful!', '✨ Klar! Complete!']
            },
            'fi': {
                'emoji': '🇫🇮',
                'start': ['Hei! Starting Finnish sisu...', '🧖 Beginning Suomi journey...', '🌲 Forest magic awakening...'],
                'progress': ['Making it kaunis (beautiful)...', '❄️ Finnish precision flowing...', 'Channeling that sisu...'],
                'finish': ['Täydellinen! Finnish perfection!', '🎉 Mahtava! Wonderful!', '✨ Valmis! Complete!']
            },
            'no': {
                'emoji': '🇳🇴',
                'start': ['Hei! Starting Norwegian charm...', '⛷️ Beginning Norsk adventure...', '🏔️ Norwegian fjords guiding...'],
                'progress': ['Making it vakker (beautiful)...', '❄️ Norwegian elegance flowing...', 'Adding that koselig warmth...'],
                'finish': ['Perfekt! Norwegian translation ferdig!', '🎉 Fantastisk! Wonderful!', '✨ Klar! Complete!']
            },
            'cs': {
                'emoji': '🇨🇿',
                'start': ['Ahoj! Starting Czech magic...', '🍺 Beginning Čeština journey...', '🏰 Prague castle awakening...'],
                'progress': ['Making it krásný (beautiful)...', '🎨 Czech artistry flowing...', 'Adding that pohoda vibes...'],
                'finish': ['Výborně! Czech perfection done!', '🎉 Skvělé! Wonderful!', '✨ Hotovo! Complete!']
            },
            'uk': {
                'emoji': '🇺🇦',
                'start': ['Привіт! Starting Ukrainian soul...', '🌻 Beginning українська magic...', '🎨 Ukrainian beauty blooming...'],
                'progress': ['Making it гарний (beautiful)...', '💛💙 Ukrainian spirit flowing...', 'Adding that душа (soul)...'],
                'finish': ['Чудово! Ukrainian perfection!', '🎉 Прекрасно! Wonderful!', '✨ Готово! Complete!']
            },
            'ro': {
                'emoji': '🇷🇴',
                'start': ['Salut! Starting Romanian charm...', '🎻 Beginning Română melody...', '🏔️ Carpathian magic awakening...'],
                'progress': ['Making it frumos (beautiful)...', '🎨 Romanian grace flowing...', 'Adding that dor feeling...'],
                'finish': ['Perfect! Romanian beauty complete!', '🎉 Minunat! Wonderful!', '✨ Gata! Done!']
            },
            'hu': {
                'emoji': '🇭🇺',
                'start': ['Szia! Starting Hungarian magic...', '🎻 Beginning Magyar journey...', '🏛️ Budapest elegance begins...'],
                'progress': ['Making it szép (beautiful)...', '🎨 Hungarian artistry flowing...', 'Adding that csodás touch...'],
                'finish': ['Tökéletes! Hungarian perfection!', '🎉 Nagyszerű! Wonderful!', '✨ Kész! Complete!']
            },
            'bg': {
                'emoji': '🇧🇬',
                'start': ['Здравей! Starting Bulgarian soul...', '🌹 Beginning Български magic...', '⛰️ Balkan beauty awakening...'],
                'progress': ['Making it красив (beautiful)...', '🎨 Bulgarian grace flowing...', 'Adding that топлина warmth...'],
                'finish': ['Отлично! Bulgarian perfection!', '🎉 Страхотно! Wonderful!', '✨ Готово! Complete!']
            },
            'id': {
                'emoji': '🇮🇩',
                'start': ['Halo! Starting Indonesian flow...', '🏝️ Beginning Bahasa journey...', '🌺 Indonesian warmth begins...'],
                'progress': ['Making it indah (beautiful)...', '🎨 Indonesian grace flowing...', 'Adding that ramah spirit...'],
                'finish': ['Sempurna! Indonesian perfection!', '🎉 Luar biasa! Wonderful!', '✨ Selesai! Complete!']
            },
            'ms': {
                'emoji': '🇲🇾',
                'start': ['Apa khabar! Starting Malay magic...', '🌴 Beginning Bahasa Melayu...', '🏝️ Malaysian harmony begins...'],
                'progress': ['Making it cantik (beautiful)...', '🎨 Malay elegance flowing...', 'Adding that mesra warmth...'],
                'finish': ['Sempurna! Malay perfection!', '🎉 Hebat! Wonderful!', '✨ Siap! Complete!']
            },
            'bn': {
                'emoji': '🇧🇩',
                'start': ['নমস্কার! Starting Bengali beauty...', '🌸 Beginning বাংলা journey...', '🎨 Bengali poetry awakening...'],
                'progress': ['Making it সুন্দর (beautiful)...', '🎭 Bengali artistry flowing...', 'Adding that ভাব (emotion)...'],
                'finish': ['নিখুঁত! Bengali perfection!', '🎉 চমৎকার! Wonderful!', '✨ সম্পূর্ণ! Complete!']
            },
            'ta': {
                'emoji': '🇮🇳',
                'start': ['வணக்கம்! Starting Tamil heritage...', '🎭 Beginning தமிழ் journey...', '🏛️ Ancient Tamil wisdom flows...'],
                'progress': ['Making it அழகான (beautiful)...', '🎨 Tamil artistry flowing...', 'Adding that இனிமை sweetness...'],
                'finish': ['சிறப்பு! Tamil perfection!', '🎉 அருமை! Wonderful!', '✨ முடிந்தது! Complete!']
            },
            'te': {
                'emoji': '🇮🇳',
                'start': ['నమస్కారం! Starting Telugu elegance...', '🎭 Beginning తెలుగు magic...', '🌺 Telugu beauty blooms...'],
                'progress': ['Making it అందమైన (beautiful)...', '🎨 Telugu grace flowing...', 'Adding that మధురం sweetness...'],
                'finish': ['పరిపూర్ణం! Telugu perfection!', '🎉 అద్భుతం! Wonderful!', '✨ పూర్తయింది! Complete!']
            },
            'ur': {
                'emoji': '🇵🇰',
                'start': ['السلام علیکم! Starting Urdu poetry...', '🌙 Beginning اردو elegance...', '📜 Urdu beauty awakening...'],
                'progress': ['Making it خوبصورت (beautiful)...', '✨ Urdu artistry flowing...', 'Adding that شان (grace)...'],
                'finish': ['بہترین! Urdu perfection!', '🎉 شاندار! Wonderful!', '✨ مکمل! Complete!']
            },
            'fa': {
                'emoji': '🇮🇷',
                'start': ['سلام! Starting Persian poetry...', '🌹 Beginning فارسی elegance...', '📖 Persian wisdom flows...'],
                'progress': ['Making it زیبا (beautiful)...', '✨ Persian artistry flowing...', 'Adding that عشق (love)...'],
                'finish': ['عالی! Persian perfection!', '🎉 فوق‌العاده! Wonderful!', '✨ تمام! Complete!']
            },
            'sk': {
                'emoji': '🇸🇰',
                'start': ['Ahoj! Starting Slovak charm...', '⛰️ Beginning Slovenčina journey...', '🏔️ Tatra mountains guiding...'],
                'progress': ['Making it krásny (beautiful)...', '🎨 Slovak artistry flowing...', 'Adding that pohoda vibes...'],
                'finish': ['Výborne! Slovak perfection!', '🎉 Skvelé! Wonderful!', '✨ Hotovo! Complete!']
            },
            'hr': {
                'emoji': '🇭🇷',
                'start': ['Bok! Starting Croatian beauty...', '🌊 Beginning Hrvatski journey...', '⚓ Adriatic magic flows...'],
                'progress': ['Making it lijep (beautiful)...', '🎨 Croatian grace flowing...', 'Adding that živahan energy...'],
                'finish': ['Savršeno! Croatian perfection!', '🎉 Odlično! Wonderful!', '✨ Gotovo! Complete!']
            },
            'sr': {
                'emoji': '🇷🇸',
                'start': ['Здраво! Starting Serbian soul...', '🎭 Beginning Српски journey...', '🏛️ Serbian spirit awakening...'],
                'progress': ['Making it леп (beautiful)...', '🎨 Serbian artistry flowing...', 'Adding that душа (soul)...'],
                'finish': ['Савршено! Serbian perfection!', '🎉 Одлично! Wonderful!', '✨ Готово! Complete!']
            },
            'lt': {
                'emoji': '🇱🇹',
                'start': ['Labas! Starting Lithuanian charm...', '🌲 Beginning Lietuvių journey...', '🏰 Baltic magic awakening...'],
                'progress': ['Making it gražus (beautiful)...', '🎨 Lithuanian grace flowing...', 'Adding that šiluma warmth...'],
                'finish': ['Tobula! Lithuanian perfection!', '🎉 Puiku! Wonderful!', '✨ Baigta! Complete!']
            },
            'lv': {
                'emoji': '🇱🇻',
                'start': ['Sveiki! Starting Latvian beauty...', '🌲 Beginning Latviešu magic...', '⚓ Baltic charm flows...'],
                'progress': ['Making it skaists (beautiful)...', '🎨 Latvian artistry flowing...', 'Adding that dvēsele soul...'],
                'finish': ['Lieliski! Latvian perfection!', '🎉 Brīnišķīgi! Wonderful!', '✨ Pabeigts! Complete!']
            },
            'et': {
                'emoji': '🇪🇪',
                'start': ['Tere! Starting Estonian magic...', '🌲 Beginning Eesti journey...', '💻 Digital nation wizardry...'],
                'progress': ['Making it ilus (beautiful)...', '🎨 Estonian precision flowing...', 'Adding that hing (spirit)...'],
                'finish': ['Suurepärane! Estonian perfection!', '🎉 Fantastiline! Wonderful!', '✨ Valmis! Complete!']
            },
            'sl': {
                'emoji': '🇸🇮',
                'start': ['Živjo! Starting Slovenian charm...', '⛰️ Beginning Slovenski journey...', '🏔️ Alpine magic awakening...'],
                'progress': ['Making it lep (beautiful)...', '🎨 Slovenian grace flowing...', 'Adding that ljubezen love...'],
                'finish': ['Odlično! Slovenian perfection!', '🎉 Čudovito! Wonderful!', '✨ Končano! Complete!']
            },
            'ca': {
                'emoji': '🏴',
                'start': ['Hola! Starting Catalan pride...', '🎨 Beginning Català journey...', '🏛️ Barcelona magic flows...'],
                'progress': ['Making it bonic (beautiful)...', '🎭 Catalan artistry flowing...', 'Adding that seny wisdom...'],
                'finish': ['Perfecte! Catalan perfection!', '🎉 Fantàstic! Wonderful!', '✨ Acabat! Complete!']
            }
        }

        # Get language config or use default
        config = language_config.get(target_lang.lower(), {
            'emoji': '🌍',
            'start': [f'✨ Starting {target_lang.upper()} translation...'],
            'progress': [f'🎨 {target_lang.upper()} magic in progress...'],
            'finish': [f'🎉 {target_lang.upper()} translation complete!']
        })

        emoji = config['emoji']
        progress_pct = int((current_batch / total_batches) * 100)

        # Select message based on progress stage
        if current_batch == 1:
            message = config['start'][current_batch % len(config['start'])]
        elif current_batch == total_batches:
            message = config['finish'][current_batch % len(config['finish'])]
        else:
            base_msg = config['progress'][current_batch % len(config['progress'])]
            message = f"{base_msg} ({progress_pct}%)"

        return f"{emoji} {message}"

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
