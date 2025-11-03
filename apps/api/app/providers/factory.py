"""Provider factory for creating translation provider instances.

This module provides a centralized way to instantiate translation providers
with the correct configuration. It's separated from deps.py to avoid circular
dependencies and heavy imports like redis.
"""

from app.config import settings
from app.providers.base import TranslationProvider
from app.providers.gemini import GeminiFlashProvider
from app.providers.groq import GroqLlamaProvider


def get_provider(name: str) -> TranslationProvider:
    """Get translation provider instance with correct model configuration.

    This is the single source of truth for provider instantiation across
    the entire codebase. All code that needs a translation provider should
    use this function.

    Args:
        name: Provider name ("groq" or "gemini")

    Returns:
        Configured TranslationProvider instance

    Example:
        >>> groq_provider = get_provider("groq")
        >>> gemini_provider = get_provider("gemini")
    """
    if name == "groq":
        return GroqLlamaProvider(
            api_key=settings.groq_api_key,
            model=settings.groq_model
        )
    else:  # Default to Gemini
        return GeminiFlashProvider(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model
        )
