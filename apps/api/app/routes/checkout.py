import uuid
from fastapi import APIRouter, HTTPException, Request, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.deps import get_storage
from app.pricing import estimate_price_from_size, estimate_price_from_file, validate_price_match, validate_price_match_from_file, get_optimal_payment_provider
from app.paypal import get_paypal_provider
from app.schemas import CreateCheckoutRequest, CreateCheckoutResponse
from app.models import Job
from app.logger import get_logger

logger = get_logger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)
router = APIRouter()


@router.post("/create-checkout", response_model=CreateCheckoutResponse)
@limiter.limit(f"{settings.rate_limit_per_hour}/hour")
async def create_checkout(
    request: Request,
    data: CreateCheckoutRequest,
    db: Session = Depends(get_db),
    storage = Depends(get_storage)
):
    """Create PayPal payment session for EPUB translation."""
    
    try:
        # Determine provider first
        provider = data.provider or settings.provider
        if provider not in ["gemini", "groq"]:
            provider = settings.provider
            
        # Get file size for server-side price validation
        size_bytes = storage.get_object_size(data.key)
        
        if size_bytes is None:
            raise HTTPException(
                status_code=404,
                detail="File not found. Please upload file first."
            )
        
        # Server-side price recalculation (prevent tampering)
        # For EPUB files, download and analyze text content for accurate token estimation
        temp_file_path = None
        epub_download_success = False
        
        if data.key.lower().endswith('.epub'):
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(suffix='.epub', delete=False) as temp_file:
                temp_file_path = temp_file.name
            
            try:
                success = storage.download_file(data.key, temp_file_path)
                if success:
                    tokens_est, server_price_cents = estimate_price_from_file(temp_file_path, provider)
                    epub_download_success = True
                else:
                    logger.warning("Failed to download EPUB file for checkout, using size fallback")
                    tokens_est, server_price_cents = estimate_price_from_size(size_bytes, provider)
            except Exception as e:
                logger.warning(f"Failed to extract EPUB text for checkout, using size fallback: {e}")
                tokens_est, server_price_cents = estimate_price_from_size(size_bytes, provider)
        else:
            tokens_est, server_price_cents = estimate_price_from_size(size_bytes, provider)
        
        # Validate client price matches server calculation
        # Use file-based validation for EPUB files if we downloaded it successfully
        if epub_download_success and temp_file_path and os.path.exists(temp_file_path):
            price_validation_passed = validate_price_match_from_file(temp_file_path, data.price_cents, provider)
        else:
            price_validation_passed = validate_price_match(size_bytes, data.price_cents, provider)
            
        # Clean up temp file after validation
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            
        if not price_validation_passed:
            logger.warning(
                f"Price validation failed: client={data.price_cents}, server={server_price_cents}"
            )
            raise HTTPException(
                status_code=400,
                detail=f"Price mismatch. Expected: ${server_price_cents/100:.2f}"
            )
        
        # Always use PayPal for payments
        logger.info(f"Using PayPal for ${server_price_cents/100:.2f} payment")
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Check if using fake PayPal keys - bypass payment for testing
        if settings.paypal_client_id.startswith("fake_"):
            logger.info("Using fake PayPal keys - bypassing payment for testing")
            
            # Create job directly and trigger translation
            job = Job(
                id=job_id,
                source_key=data.key,
                target_lang=data.target_lang,
                provider=provider,
                status="queued",  # Start as queued, worker will process
                price_charged_cents=server_price_cents,
                tokens_est=tokens_est,
                size_bytes=size_bytes,
                email=data.email,
                stripe_payment_id=f"fake_paypal_payment_{job_id}"
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
                logger.info(f"Translation job queued: {job_id}")
            except Exception as e:
                logger.error(f"Failed to queue translation: {e}")
            
            return CreateCheckoutResponse(
                checkout_url=f"http://localhost:3000/processing?job_id={job_id}",
                job_id=job_id
            )
        
        # Create PayPal payment
        paypal = get_paypal_provider()
        
        success_url = f"{request.url.scheme}://{request.url.netloc}/api/paypal/success?job_id={job_id}"
        cancel_url = f"{request.url.scheme}://{request.url.netloc}/cancel"
        
        payment_result = paypal.create_payment(
            amount_cents=server_price_cents,
            job_id=job_id,
            description=f"EPUB Translation to {data.target_lang.upper()}",
            success_url=success_url,
            cancel_url=cancel_url,
            customer_email=data.email
        )
        
        if not payment_result['success']:
            raise HTTPException(
                status_code=500,
                detail=f"PayPal payment creation failed: {payment_result.get('error')}"
            )
        
        checkout_url = payment_result['approval_url']
        payment_id = payment_result['payment_id']
        
        # Pre-create job record (will be updated by webhook)
        job = Job(
            id=job_id,
            email=data.email,
            source_key=data.key,
            target_lang=data.target_lang,
            provider=provider,
            status="pending_payment",
            size_bytes=size_bytes,
            tokens_est=tokens_est,
            price_charged_cents=server_price_cents,
            stripe_payment_id=payment_id,  # Store payment ID for both providers
        )
        
        db.add(job)
        db.commit()
        
        logger.info(
            f"Created PayPal checkout for job {job_id}: "
            f"${server_price_cents/100:.2f}, provider={provider}"
        )
        
        return CreateCheckoutResponse(
            checkout_url=checkout_url,
            job_id=job_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create checkout session: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create payment session"
        )