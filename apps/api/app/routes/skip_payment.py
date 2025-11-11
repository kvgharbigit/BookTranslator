import uuid
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.deps import get_storage
from app.pricing import estimate_tokens_from_size, estimate_tokens_from_epub, calculate_price_with_format
from app.models import Job
from app.logger import get_logger
from pydantic import BaseModel

logger = get_logger(__name__)

router = APIRouter()


class SkipPaymentRequest(BaseModel):
    key: str
    target_lang: str
    email: str | None = None
    output_format: str | None = "translation"


class SkipPaymentResponse(BaseModel):
    job_id: str


@router.post("/skip-payment", response_model=SkipPaymentResponse)
async def skip_payment(
    data: SkipPaymentRequest,
    db: Session = Depends(get_db),
    storage = Depends(get_storage)
):
    """Skip payment and directly create translation job (for testing only).

    This endpoint bypasses payment processing for testing purposes.
    """

    try:
        # ALWAYS use Gemini for full book translations (best quality)
        # Previews use Llama for speed/cost, but full books deserve the best
        provider = "gemini"

        # Get file size
        size_bytes = storage.get_object_size(data.key)

        if size_bytes is None:
            raise HTTPException(
                status_code=404,
                detail="File not found. Please upload file first."
            )

        # Estimate tokens and price (for record keeping)
        temp_file_path = None

        # Step 1: Estimate tokens
        if data.key.lower().endswith('.epub'):
            import tempfile
            import os

            with tempfile.NamedTemporaryFile(suffix='.epub', delete=False) as temp_file:
                temp_file_path = temp_file.name

            try:
                success = storage.download_file(data.key, temp_file_path)
                if success:
                    tokens_est = estimate_tokens_from_epub(temp_file_path)
                else:
                    logger.warning("Failed to download EPUB file, using size fallback")
                    tokens_est = estimate_tokens_from_size(size_bytes)
            except ValueError as e:
                # Content limit exceeded - return user-friendly error
                raise HTTPException(
                    status_code=400,
                    detail=str(e)
                )
            except Exception as e:
                logger.warning(f"Failed to extract EPUB text, using size fallback: {e}")
                tokens_est = estimate_tokens_from_size(size_bytes)
            finally:
                if temp_file_path and os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
        else:
            try:
                tokens_est = estimate_tokens_from_size(size_bytes)
            except ValueError as e:
                # Content limit exceeded - return user-friendly error
                raise HTTPException(
                    status_code=400,
                    detail=str(e)
                )

        # Step 2: Calculate price including format surcharge
        output_format = data.output_format or "translation"
        logger.info(f"🔍 API RECEIVED: output_format={repr(output_format)}, type={type(output_format).__name__}")
        try:
            price_cents = calculate_price_with_format(
                tokens_est,
                output_format=output_format,
                provider=provider
            )
        except ValueError as e:
            # Content limit exceeded - return user-friendly error
            raise HTTPException(
                status_code=400,
                detail=str(e)
            )

        # Generate job ID
        job_id = str(uuid.uuid4())

        logger.info(f"Skip payment requested for job {job_id}, price would be: ${price_cents/100:.2f}")

        # Create job directly and trigger translation
        job = Job(
            id=job_id,
            source_key=data.key,
            target_lang=data.target_lang,
            provider=provider,
            status="queued",  # Start as queued, worker will process
            price_charged_cents=0,  # No charge for skip payment
            tokens_est=tokens_est,
            size_bytes=size_bytes,
            email=data.email,
            output_format=output_format,
            stripe_payment_id=f"skip_payment_{job_id}"
        )
        db.add(job)
        db.commit()
        logger.info(f"✅ SAVED TO DB: job_id={job_id}, output_format={repr(job.output_format)}")

        # Start translation job immediately
        from app.pipeline.worker import translate_epub
        from rq import Queue
        import redis

        try:
            r = redis.Redis.from_url(settings.redis_url)
            queue = Queue(name="translate", connection=r)
            queue.enqueue(translate_epub, job_id)
            logger.info(f"Translation job queued (skip payment): {job_id}")
        except Exception as e:
            logger.error(f"Failed to queue translation: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to queue translation job"
            )

        return SkipPaymentResponse(job_id=job_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create skip payment job: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create translation job"
        )
