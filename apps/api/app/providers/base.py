from abc import ABC, abstractmethod
from typing import List, Optional, Dict


class TranslationProvider(ABC):
    """Abstract base class for translation providers."""
    
    name: str = "base"
    
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
    
    @abstractmethod
    async def translate_segments(
        self,
        segments: List[str],
        src_lang: Optional[str],
        tgt_lang: str,
        system_hint: Optional[str] = None,
        glossary: Optional[Dict[str, str]] = None,
    ) -> List[str]:
        """Translate a list of text segments.
        
        Args:
            segments: List of text segments to translate
            src_lang: Source language code (optional, auto-detect if None)
            tgt_lang: Target language code
            system_hint: Optional system prompt hint
            glossary: Optional translation glossary
            
        Returns:
            List of translated segments (1:1 mapping with input)
            
        Raises:
            Exception: If translation fails
        """
        raise NotImplementedError
    
    def get_default_system_hint(self, tgt_lang: str) -> str:
        """Get default system prompt hint."""

        # Language-specific quotation mark instructions
        quotation_marks = {
            'fr': 'Use proper French quotation marks (« guillemets ») for dialogue, not << >> or angle brackets.',
            'de': 'Use proper German quotation marks („ and ") for dialogue.',
            'es': 'Use proper Spanish quotation marks (« » or " ") for dialogue.',
            'it': 'Use proper Italian quotation marks (« ») for dialogue.',
            'pt': 'Use proper Portuguese quotation marks (" ") for dialogue.',
            'ru': 'Use proper Russian quotation marks (« ») for dialogue.',
            'pl': 'Use proper Polish quotation marks („ ") for dialogue.',
            'cs': 'Use proper Czech quotation marks („ ") for dialogue.',
            'nl': 'Use proper Dutch quotation marks (" " or ' ') for dialogue.',
            'sv': 'Use proper Swedish quotation marks (" " or » «) for dialogue.',
            'no': 'Use proper Norwegian quotation marks (« ») for dialogue.',
            'da': 'Use proper Danish quotation marks (» «) for dialogue.',
            'fi': 'Use proper Finnish quotation marks (" ") for dialogue.',
        }

        quote_instruction = quotation_marks.get(tgt_lang, '')

        base_instruction = (
            f"Translate to {tgt_lang}. Preserve placeholders {{TAG_n}}/{{NUM_n}}/{{URL_n}} exactly. "
            "Do not add or remove HTML tags."
        )

        if quote_instruction:
            return f"{base_instruction} {quote_instruction}"

        return base_instruction