from fastapi import APIRouter, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from pydantic import BaseModel

from app.config import settings
from app.pipeline.preview import PreviewService
from app.logger import get_logger

logger = get_logger(__name__)

# Rate limiter - more generous for previews
limiter = Limiter(key_func=get_remote_address)
router = APIRouter()


class PreviewRequest(BaseModel):
    """Request model for preview generation."""
    key: str  # R2 storage key for the EPUB file
    target_lang: str  # Target language code (e.g., 'es', 'fr', 'de')
    max_words: int = 1000  # Maximum words to translate


class PreviewResponse(BaseModel):
    """Response model for preview generation."""
    preview_html: str  # Formatted HTML preview
    word_count: int  # Actual number of words translated
    provider: str  # Provider used (e.g., 'groq')
    model: str  # Model used (e.g., 'llama-3.1-8b-instant')


@router.post("/preview", response_model=PreviewResponse)
@limiter.limit("5/hour")  # 5 previews per hour per IP
async def generate_preview(
    request: Request,
    data: PreviewRequest
):
    """Generate a preview translation of the first N words of an EPUB file.

    This endpoint:
    1. Downloads the EPUB from R2 storage
    2. Reads the first ~1000 words (configurable)
    3. Translates using Groq Llama 3.1 8B (fast and cheap)
    4. Returns formatted HTML suitable for iframe display

    Rate limited to 5 previews per hour per IP to prevent abuse.

    Args:
        request: FastAPI request object (for rate limiting)
        data: PreviewRequest with key, target_lang, and optional max_words

    Returns:
        PreviewResponse with preview_html and metadata

    Raises:
        HTTPException: If preview generation fails
    """

    try:
        logger.info(
            f"Preview request: key={data.key}, lang={data.target_lang}, "
            f"max_words={data.max_words}"
        )

        # Use Groq Llama 3.1 8B for fast, cheap previews
        provider = "groq"
        model = "llama-3.1-8b-instant"

        # Generate preview
        preview_service = PreviewService()
        preview_html, actual_words = await preview_service.generate_preview(
            r2_key=data.key,
            target_lang=data.target_lang,
            max_words=data.max_words,
            provider=provider,
            model=model
        )

        logger.info(
            f"Preview generated successfully: {actual_words} words, "
            f"provider={provider}, model={model}"
        )

        return PreviewResponse(
            preview_html=preview_html,
            word_count=actual_words,
            provider=provider,
            model=model
        )

    except Exception as e:
        logger.error(f"Preview generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate preview: {str(e)}"
        )
