import uuid
from fastapi import APIRouter, HTTPException, Request, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.deps import get_storage, get_stripe
from app.pricing import estimate_price_from_size, validate_price_match
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
    storage = Depends(get_storage),
    stripe = Depends(get_stripe)
):
    """Create Stripe Checkout session for translation payment."""
    
    try:
        # Get file size for server-side price validation
        size_bytes = storage.get_object_size(data.key)
        
        if size_bytes is None:
            raise HTTPException(
                status_code=404,
                detail="File not found. Please upload file first."
            )
        
        # Server-side price recalculation (prevent tampering)
        tokens_est, server_price_cents = estimate_price_from_size(size_bytes)
        
        # Validate client price matches server calculation
        if not validate_price_match(size_bytes, data.price_cents):
            logger.warning(
                f"Price validation failed: client={data.price_cents}, server={server_price_cents}"
            )
            raise HTTPException(
                status_code=400,
                detail=f"Price mismatch. Expected: ${server_price_cents/100:.2f}"
            )
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Determine provider
        provider = data.provider or settings.provider
        if provider not in ["gemini", "groq"]:
            provider = settings.provider
        
        # Check if using fake Stripe keys - bypass payment for testing
        if settings.stripe_secret_key.startswith("sk_test_fake"):
            logger.info("Using fake Stripe keys - bypassing payment for testing")
            
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
                stripe_payment_id=f"fake_payment_{job_id}"
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
        
        # Create real Stripe Checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f"EPUB Translation to {data.target_lang.upper()}",
                        "description": f"Translate EPUB to {data.target_lang} (EPUB + PDF + TXT formats)",
                    },
                    "unit_amount": server_price_cents,
                },
                "quantity": 1,
            }],
            metadata={
                "job_id": job_id,
                "source_key": data.key,
                "target_lang": data.target_lang,
                "provider": provider,
                "email": data.email or "",
                "tokens_est": str(tokens_est),
                "size_bytes": str(size_bytes),
            },
            success_url=f"{request.url.scheme}://{request.url.netloc}/success?job_id={job_id}",
            cancel_url=f"{request.url.scheme}://{request.url.netloc}/cancel",
            customer_email=data.email,
        )
        
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
        )
        
        db.add(job)
        db.commit()
        
        logger.info(
            f"Created checkout session for job {job_id}: "
            f"${server_price_cents/100:.2f}, provider={provider}"
        )
        
        return CreateCheckoutResponse(
            checkout_url=checkout_session.url
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create checkout session: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create payment session"
        )