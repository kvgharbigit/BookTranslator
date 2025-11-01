import json
from fastapi import APIRouter, HTTPException, Request, Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.deps import get_stripe, get_queue
from app.models import Job
from app.pipeline.worker import translate_epub
from app.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("/webhook/stripe")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db),
    stripe = Depends(get_stripe),
    queue = Depends(get_queue)
):
    """Handle Stripe webhook events."""
    
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing signature header")
    
    try:
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
        
    except ValueError:
        logger.error("Invalid payload in Stripe webhook")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid signature in Stripe webhook")
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Handle checkout.session.completed event
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        
        # Extract job metadata
        metadata = session.get("metadata", {})
        job_id = metadata.get("job_id")
        source_key = metadata.get("source_key")
        target_lang = metadata.get("target_lang")
        provider = metadata.get("provider")
        email = metadata.get("email")
        
        if not all([job_id, source_key, target_lang, provider]):
            logger.error(f"Missing metadata in Stripe session: {metadata}")
            raise HTTPException(status_code=400, detail="Missing required metadata")
        
        # Check for idempotency (prevent duplicate processing)
        existing_job = db.query(Job).filter(
            Job.stripe_payment_id == session["id"]
        ).first()
        
        if existing_job:
            logger.info(f"Webhook already processed for session {session['id']}")
            return {"status": "already_processed"}
        
        # Find and update job
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found for Stripe session {session['id']}")
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Update job with payment info
        job.stripe_payment_id = session["id"]
        job.status = "queued"
        job.progress_step = "queued"
        
        # Auto-detect source language if not set
        if not job.source_lang:
            # Will be detected in worker
            pass
        
        db.commit()
        
        # Enqueue translation job
        queue.enqueue(
            translate_epub,
            job_id=job_id,
            source_key=source_key,
            target_lang=target_lang,
            provider_name=provider,
            email=email if email else None,
            timeout=3600,  # 1 hour timeout
        )
        
        logger.info(
            f"Enqueued translation job {job_id} after successful payment "
            f"(session: {session['id']})"
        )
        
        return {"status": "job_enqueued"}
    
    elif event["type"] == "checkout.session.expired":
        session = event["data"]["object"]
        metadata = session.get("metadata", {})
        job_id = metadata.get("job_id")
        
        if job_id:
            # Mark job as cancelled
            job = db.query(Job).filter(Job.id == job_id).first()
            if job and job.status == "pending_payment":
                job.status = "cancelled"
                job.error = "Payment session expired"
                db.commit()
                
                logger.info(f"Marked job {job_id} as cancelled due to expired payment")
        
        return {"status": "session_expired"}
    
    else:
        # Log other events but don't process them
        logger.info(f"Received unhandled Stripe webhook event: {event['type']}")
        return {"status": "event_ignored"}
    
    return {"status": "ok"}