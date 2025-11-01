import uuid
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.deps import get_storage
from app.pricing import estimate_price_from_file, estimate_price_from_size
from app.models import Job
from app.logger import get_logger
from pydantic import BaseModel

logger = get_logger(__name__)

router = APIRouter()


class SkipPaymentRequest(BaseModel):
    key: str
    target_lang: str
    email: str | None = None


class SkipPaymentResponse(BaseModel):
    job_id: str


@router.post("/skip-payment", response_model=SkipPaymentResponse)
async def skip_payment(
    data: SkipPaymentRequest,
    db: Session = Depends(get_db),
    storage = Depends(get_storage)
):
    """Skip payment and directly create translation job (for testing only)."""

    try:
        # Determine provider
        provider = settings.provider
        if provider not in ["gemini", "groq"]:
            provider = "gemini"

        # Get file size
        size_bytes = storage.get_object_size(data.key)

        if size_bytes is None:
            raise HTTPException(
                status_code=404,
                detail="File not found. Please upload file first."
            )

        # Estimate price (for record keeping)
        temp_file_path = None
        if data.key.lower().endswith('.epub'):
            import tempfile
            import os

            with tempfile.NamedTemporaryFile(suffix='.epub', delete=False) as temp_file:
                temp_file_path = temp_file.name

            try:
                success = storage.download_file(data.key, temp_file_path)
                if success:
                    tokens_est, price_cents = estimate_price_from_file(temp_file_path, provider)
                else:
                    logger.warning("Failed to download EPUB file, using size fallback")
                    tokens_est, price_cents = estimate_price_from_size(size_bytes, provider)
            except Exception as e:
                logger.warning(f"Failed to extract EPUB text, using size fallback: {e}")
                tokens_est, price_cents = estimate_price_from_size(size_bytes, provider)
            finally:
                if temp_file_path and os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
        else:
            tokens_est, price_cents = estimate_price_from_size(size_bytes, provider)

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
            stripe_payment_id=f"skip_payment_{job_id}"
        )
        db.add(job)
        db.commit()

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
