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
        return (
            f"Translate to {tgt_lang}. Preserve placeholders {{TAG_n}}/{{NUM_n}}/{{URL_n}} exactly. "
            "Do not add or remove HTML tags."
        )