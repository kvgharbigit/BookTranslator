import re
from typing import List, Dict, Tuple

from app.logger import get_logger

logger = get_logger(__name__)


class PlaceholderManager:
    """Manage placeholder protection for HTML tags, numbers, and URLs."""
    
    def __init__(self):
        # Patterns for content that needs protection
        self.patterns = {
            'tag': re.compile(r'<[^>]+>'),
            'num': re.compile(r'\b\d+(?:[.,]\d+)*\b'),
            'url': re.compile(r'https?://[^\s<>"]+|www\.[^\s<>"]+'),
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
        }
    
    def protect_segments(self, segments: List[str]) -> Tuple[List[str], Dict]:
        """Apply placeholder protection to all segments.
        
        Returns:
            tuple: (protected_segments, placeholder_map)
        """
        protected_segments = []
        placeholder_map = {}
        
        for i, segment in enumerate(segments):
            protected_segment, segment_map = self.protect_segment(segment, i)
            protected_segments.append(protected_segment)
            placeholder_map[i] = segment_map
        
        # Log placeholder statistics
        total_placeholders = sum(
            sum(len(type_map) for type_map in seg_map.values()) 
            for seg_map in placeholder_map.values()
        )
        
        logger.info(f"Protected {total_placeholders} placeholders across {len(segments)} segments")
        return protected_segments, placeholder_map
    
    def protect_segment(self, segment: str, segment_idx: int) -> Tuple[str, Dict]:
        """Apply placeholder protection to a single segment."""
        
        protected = segment
        segment_map = {}
        
        # Apply protection for each pattern type
        for pattern_type, pattern in self.patterns.items():
            protected, type_map = self._apply_pattern_protection(
                protected, pattern, pattern_type, segment_idx
            )
            if type_map:
                segment_map[pattern_type] = type_map
        
        return protected, segment_map
    
    def _apply_pattern_protection(
        self, 
        text: str, 
        pattern: re.Pattern, 
        pattern_type: str, 
        segment_idx: int
    ) -> Tuple[str, Dict]:
        """Apply protection for a specific pattern type."""
        
        matches = list(pattern.finditer(text))
        if not matches:
            return text, {}
        
        # Create placeholders and replacement map
        type_map = {}
        protected_text = text
        
        # Process matches in reverse order to maintain positions
        for i, match in enumerate(reversed(matches)):
            original = match.group()
            placeholder = f"{{{pattern_type.upper()}_{len(matches)-i-1}}}"
            
            type_map[placeholder] = original
            protected_text = (
                protected_text[:match.start()] + 
                placeholder + 
                protected_text[match.end():]
            )
        
        return protected_text, type_map
    
    def restore_segments(
        self, 
        translated_segments: List[str], 
        placeholder_map: Dict
    ) -> Tuple[List[str], bool]:
        """Restore placeholders in translated segments.
        
        Returns:
            tuple: (restored_segments, validation_passed)
        """
        restored_segments = []
        validation_passed = True
        
        for i, translated_segment in enumerate(translated_segments):
            if i in placeholder_map:
                restored_segment, segment_valid = self.restore_segment(
                    translated_segment, placeholder_map[i]
                )
                restored_segments.append(restored_segment)
                
                if not segment_valid:
                    validation_passed = False
                    logger.warning(f"Placeholder validation failed for segment {i}")
            else:
                restored_segments.append(translated_segment)
        
        logger.info(
            f"Restored placeholders in {len(translated_segments)} segments. "
            f"Validation: {'PASSED' if validation_passed else 'FAILED'}"
        )
        
        return restored_segments, validation_passed
    
    def restore_segment(self, translated_segment: str, segment_map: Dict) -> Tuple[str, bool]:
        """Restore placeholders in a single translated segment."""
        
        restored = translated_segment
        validation_passed = True
        
        # Restore each pattern type
        for pattern_type, type_map in segment_map.items():
            restored, type_valid = self._restore_pattern_type(
                restored, type_map, pattern_type
            )
            if not type_valid:
                validation_passed = False
        
        return restored, validation_passed
    
    def _restore_pattern_type(
        self, 
        text: str, 
        type_map: Dict, 
        pattern_type: str
    ) -> Tuple[str, bool]:
        """Restore placeholders for a specific pattern type."""
        
        restored_text = text
        validation_passed = True
        
        # Check placeholder parity
        expected_placeholders = set(type_map.keys())
        found_placeholders = set(re.findall(
            rf'{{{pattern_type.upper()}_\d+}}', 
            text
        ))
        
        if expected_placeholders != found_placeholders:
            logger.warning(
                f"Placeholder parity mismatch for {pattern_type}: "
                f"expected {expected_placeholders}, found {found_placeholders}"
            )
            validation_passed = False
        
        # Restore placeholders
        for placeholder, original in type_map.items():
            restored_text = restored_text.replace(placeholder, original)
        
        return restored_text, validation_passed
    
    def validate_translation_quality(
        self,
        original_segments: List[str],
        translated_segments: List[str],
        target_lang: str = "en"
    ) -> bool:
        """Validate translation quality with language-specific length ratio checks.

        Args:
            original_segments: Original text segments
            translated_segments: Translated text segments
            target_lang: Target language code for language-specific thresholds

        Returns:
            True if quality checks pass, False otherwise
        """

        if len(original_segments) != len(translated_segments):
            logger.error(
                f"Segment count mismatch: {len(original_segments)} -> {len(translated_segments)}"
            )
            return False

        # Language-specific thresholds
        # CJK and Thai languages naturally compress text (use fewer characters)
        cjk_languages = {'zh', 'ja', 'ko', 'th'}

        if target_lang.lower() in cjk_languages:
            min_ratio = 0.2  # Allow 20-250% for compact languages
            max_ratio = 2.5
            logger.debug(f"Using CJK thresholds for {target_lang}: {min_ratio}-{max_ratio}")
        else:
            min_ratio = 0.6  # Standard 60-180% for other languages
            max_ratio = 1.8

        failed_segments = 0

        for i, (original, translated) in enumerate(zip(original_segments, translated_segments)):
            # Skip empty segments
            if not original.strip() or not translated.strip():
                continue

            # Check length ratio with language-specific thresholds
            length_ratio = len(translated) / len(original)

            if length_ratio < min_ratio or length_ratio > max_ratio:
                logger.warning(
                    f"Suspicious length ratio for segment {i}: {length_ratio:.2f} "
                    f"(original: {len(original)}, translated: {len(translated)})"
                )
                failed_segments += 1
        
        # Allow up to 10% of segments to have suspicious ratios
        failure_rate = failed_segments / max(len(original_segments), 1)
        quality_passed = failure_rate <= 0.1
        
        logger.info(
            f"Translation quality check: {failed_segments}/{len(original_segments)} "
            f"suspicious segments ({failure_rate:.1%}). "
            f"Result: {'PASSED' if quality_passed else 'FAILED'}"
        )
        
        return quality_passed