from typing import List, Optional, Dict, Callable
from langdetect import detect

from app.providers.base import TranslationProvider
from app.pipeline.placeholders import PlaceholderManager
from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)


class TranslationOrchestrator:
    """Orchestrate translation with validation and quality checks."""
    
    def __init__(self):
        self.placeholder_manager = PlaceholderManager()
        self.max_validation_failures = 2
        
        # Low-resource languages that should use Gemini only
        self.gemini_only_languages = {
            'km', 'lo', 'eu', 'gl', 'ga', 'tg', 'uz', 'hy', 'ka'
        }
    
    async def translate_segments(
        self,
        segments: List[str],
        target_lang: str,
        primary_provider: TranslationProvider,
        fallback_provider: Optional[TranslationProvider] = None,
        source_lang: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> tuple[List[str], int, str]:
        """Translate segments with validation and fallback.
        
        Returns:
            tuple: (translated_segments, tokens_actual, provider_used)
        """
        
        if not segments:
            return [], 0, primary_provider.name
        
        # Auto-detect source language if not provided
        if source_lang is None:
            source_lang = self._detect_source_language(segments[:5])  # Sample first 5
        
        # Check if we should force Gemini for low-resource languages
        provider_to_use = self._select_provider(
            target_lang, primary_provider, fallback_provider
        )
        
        validation_failures = 0
        
        while validation_failures < self.max_validation_failures:
            try:
                # Step 1: Apply placeholder protection
                protected_segments, placeholder_map = self.placeholder_manager.protect_segments(segments)
                
                # Step 2: Translate protected segments
                translated_protected = await provider_to_use.translate_segments(
                    protected_segments,
                    source_lang,
                    target_lang,
                    progress_callback=progress_callback
                )
                
                # Step 3: Restore placeholders
                translated_segments, placeholder_valid = self.placeholder_manager.restore_segments(
                    translated_protected, placeholder_map
                )

                # Step 4: Validate translation quality (with language-specific thresholds)
                quality_valid = self.placeholder_manager.validate_translation_quality(
                    segments, translated_segments, target_lang
                )
                
                # Check if validation passed
                if placeholder_valid and quality_valid:
                    tokens_actual = self._estimate_tokens_used(segments, translated_segments)
                    logger.info(
                        f"Translation successful: {len(segments)} segments, "
                        f"{tokens_actual} tokens, provider: {provider_to_use.name}"
                    )
                    return translated_segments, tokens_actual, provider_to_use.name
                
                # Validation failed
                validation_failures += 1
                logger.warning(
                    f"Translation validation failed (attempt {validation_failures}). "
                    f"Placeholder valid: {placeholder_valid}, Quality valid: {quality_valid}"
                )
                
                # Try fallback provider if available and we haven't tried it yet
                if (validation_failures == 1 and 
                    fallback_provider and 
                    provider_to_use.name != fallback_provider.name):
                    
                    logger.info(f"Switching to fallback provider: {fallback_provider.name}")
                    provider_to_use = fallback_provider
                
            except Exception as e:
                validation_failures += 1
                logger.error(
                    f"Translation attempt {validation_failures} failed: {e}"
                )
                
                # Try fallback provider on error
                if (validation_failures == 1 and 
                    fallback_provider and 
                    provider_to_use.name != fallback_provider.name):
                    
                    logger.info(f"Switching to fallback provider due to error: {fallback_provider.name}")
                    provider_to_use = fallback_provider
        
        # All attempts failed
        raise Exception(
            f"Translation failed after {self.max_validation_failures} attempts"
        )
    
    def _detect_source_language(self, sample_segments: List[str]) -> str:
        """Auto-detect source language from sample text."""
        try:
            # Combine sample segments
            sample_text = " ".join(sample_segments)
            
            # Use langdetect library
            detected_lang = detect(sample_text)
            logger.info(f"Detected source language: {detected_lang}")
            return detected_lang
            
        except Exception as e:
            logger.warning(f"Language detection failed: {e}. Defaulting to 'en'")
            return "en"
    
    def _select_provider(
        self,
        target_lang: str,
        primary_provider: TranslationProvider,
        fallback_provider: Optional[TranslationProvider]
    ) -> TranslationProvider:
        """Select appropriate provider based on target language."""
        
        # Force Gemini for low-resource languages
        if target_lang.lower() in self.gemini_only_languages:
            if primary_provider.name == "gemini":
                logger.info(f"Using Gemini for low-resource language: {target_lang}")
                return primary_provider
            elif fallback_provider and fallback_provider.name == "gemini":
                logger.info(f"Switching to Gemini for low-resource language: {target_lang}")
                return fallback_provider
        
        # Default to primary provider
        return primary_provider
    
    def _estimate_tokens_used(
        self, 
        original_segments: List[str], 
        translated_segments: List[str]
    ) -> int:
        """Estimate actual tokens used in translation."""
        
        # Combine all text
        input_text = " ".join(original_segments)
        output_text = " ".join(translated_segments)
        
        # Rough estimation: input + output tokens
        input_tokens = len(input_text) // 4
        output_tokens = len(output_text) // 4
        
        total_tokens = input_tokens + output_tokens
        
        logger.info(
            f"Token estimation: input={input_tokens}, output={output_tokens}, total={total_tokens}"
        )
        
        return total_tokens
    
    def should_use_rtl_layout(self, target_lang: str) -> bool:
        """Check if target language requires RTL layout."""
        rtl_languages = {'ar', 'he', 'fa', 'ur'}
        return target_lang.lower() in rtl_languages