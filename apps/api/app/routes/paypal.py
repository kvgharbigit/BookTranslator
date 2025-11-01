from fastapi import APIRouter, HTTPException, Request, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.paypal import get_paypal_provider
from app.models import Job
from app.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/success")
async def paypal_success(
    request: Request,
    job_id: str = Query(...),
    paymentId: str = Query(...),
    PayerID: str = Query(...),
    db: Session = Depends(get_db)
):
    """Handle PayPal payment success callback."""
    
    try:
        # Get job from database
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Execute PayPal payment
        paypal = get_paypal_provider()
        result = paypal.execute_payment(paymentId, PayerID)
        
        if not result['success']:
            logger.error(f"PayPal payment execution failed: {result.get('error')}")
            raise HTTPException(
                status_code=400,
                detail=f"Payment execution failed: {result.get('error')}"
            )
        
        # Update job status to paid and queue for translation
        job.status = "queued"
        job.stripe_payment_id = paymentId  # Store PayPal payment ID
        db.commit()
        
        # Queue translation job
        from app.pipeline.worker import translate_epub
        from rq import Queue
        import redis
        from app.config import settings
        
        try:
            r = redis.Redis.from_url(settings.redis_url)
            queue = Queue(name="translate", connection=r)
            queue.enqueue(translate_epub, job_id)
            logger.info(f"Translation job queued after PayPal payment: {job_id}")
        except Exception as e:
            logger.error(f"Failed to queue translation after PayPal payment: {e}")
            # Job is still marked as paid, worker might pick it up later
        
        # Redirect to success page
        success_url = f"{request.url.scheme}://{request.url.netloc.replace(':8000', ':3000')}/success?job_id={job_id}"
        
        return {
            "message": "Payment successful",
            "job_id": job_id,
            "redirect_url": success_url,
            "payment_id": paymentId,
            "amount_paid": result.get('amount_paid')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PayPal success handling failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Payment processing failed"
        )


@router.get("/cancel")
async def paypal_cancel(
    request: Request,
    job_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """Handle PayPal payment cancellation."""
    
    try:
        # Update job status to cancelled
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = "cancelled"
            db.commit()
            logger.info(f"PayPal payment cancelled for job: {job_id}")
        
        # Redirect to cancel page
        cancel_url = f"{request.url.scheme}://{request.url.netloc.replace(':8000', ':3000')}/cancel"
        
        return {
            "message": "Payment cancelled",
            "job_id": job_id,
            "redirect_url": cancel_url
        }
        
    except Exception as e:
        logger.error(f"PayPal cancel handling failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Cancel processing failed"
        )


@router.post("/webhook")
async def paypal_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle PayPal webhook events."""
    
    try:
        payload = await request.body()
        
        # TODO: Verify webhook signature with PayPal
        # For now, we handle success via the redirect callback
        # In production, implement proper webhook verification
        
        logger.info("PayPal webhook received (not fully implemented)")
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"PayPal webhook processing failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Webhook processing failed"
        )