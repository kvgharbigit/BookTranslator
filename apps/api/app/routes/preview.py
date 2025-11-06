from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from pydantic import BaseModel
import json
import asyncio

from app.config import settings
from app.pipeline.preview import PreviewService
from app.logger import get_logger
from app.config.models import get_default_model

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
# No rate limit - previews are free and should be unlimited
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

        # Generate preview (Groq primary, Gemini fallback)
        preview_service = PreviewService()
        preview_html, actual_words, provider_used = await preview_service.generate_preview(
            r2_key=data.key,
            target_lang=data.target_lang,
            max_words=data.max_words
        )

        # Parse provider name and model from provider_used string (e.g., "groq" or "gemini")
        # Use centralized model configuration
        provider_name = provider_used.lower()
        if "groq" in provider_name:
            model_name = get_default_model("groq")
        elif "gemini" in provider_name:
            model_name = get_default_model("gemini")
        else:
            model_name = "unknown"

        logger.info(
            f"✅ Preview generated successfully: {actual_words} words using {provider_used}"
        )

        return PreviewResponse(
            preview_html=preview_html,
            word_count=actual_words,
            provider=provider_name,
            model=model_name
        )

    except Exception as e:
        logger.error(f"Preview generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate preview: {str(e)}"
        )


@router.get("/preview/stream")
# No rate limit - previews are free and should be unlimited
async def stream_preview(
    request: Request,
    key: str,
    target_lang: str,
    max_words: int = 300
):
    """Stream preview generation with real-time progress updates via SSE.

    This endpoint:
    1. Streams progress messages as Server-Sent Events
    2. Shows fun, emoji-filled progress updates during translation
    3. Returns final preview HTML when complete

    Rate limited to 5 previews per hour per IP to prevent abuse.

    Args:
        request: FastAPI request object (for rate limiting)
        key: R2 storage key for the EPUB file
        target_lang: Target language code (e.g., 'es', 'fr', 'de')
        max_words: Maximum words to translate (default: 300)

    Returns:
        StreamingResponse with SSE events

    Raises:
        HTTPException: If preview generation fails
    """

    async def event_generator():
        """Generate SSE events for preview progress."""
        try:
            logger.info(
                f"SSE Preview request: key={key}, lang={target_lang}, "
                f"max_words={max_words}"
            )

            # Create a queue for progress messages
            progress_queue = asyncio.Queue()

            # Define progress callback that puts messages in the queue
            def progress_callback(message: str):
                asyncio.create_task(progress_queue.put(message))

            # Start preview generation in background
            preview_service = PreviewService()

            # Create task for preview generation
            async def generate():
                try:
                    result = await preview_service.generate_preview(
                        r2_key=key,
                        target_lang=target_lang,
                        max_words=max_words,
                        progress_callback=progress_callback
                    )
                    await progress_queue.put(("done", result))
                except Exception as e:
                    await progress_queue.put(("error", str(e)))

            generation_task = asyncio.create_task(generate())

            # Stream progress messages
            while True:
                try:
                    # Wait for next message with timeout
                    message = await asyncio.wait_for(progress_queue.get(), timeout=0.5)

                    if isinstance(message, tuple):
                        event_type, data = message

                        if event_type == "done":
                            # Preview generation complete
                            preview_html, actual_words, provider_used = data

                            # Parse provider name and model
                            provider_name = provider_used.lower()
                            if "groq" in provider_name:
                                model_name = get_default_model("groq")
                            elif "gemini" in provider_name:
                                model_name = get_default_model("gemini")
                            else:
                                model_name = "unknown"

                            # Send completion event
                            yield f"event: complete\n"
                            yield f"data: {json.dumps({'preview_html': preview_html, 'word_count': actual_words, 'provider': provider_name, 'model': model_name})}\n\n"
                            break

                        elif event_type == "error":
                            # Error occurred
                            yield f"event: error\n"
                            yield f"data: {json.dumps({'error': data})}\n\n"
                            break
                    else:
                        # Progress message
                        yield f"event: progress\n"
                        yield f"data: {json.dumps({'message': message})}\n\n"

                except asyncio.TimeoutError:
                    # Send heartbeat to keep connection alive
                    yield f": heartbeat\n\n"
                    continue

            # Ensure generation task is complete
            await generation_task

        except Exception as e:
            logger.error(f"SSE Preview generation failed: {e}", exc_info=True)
            yield f"event: error\n"
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )
