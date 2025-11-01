from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from app.db import get_db
from app.deps import get_queue, get_redis_client
from app.models import Job
from app.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(
    db: Session = Depends(get_db),
    queue = Depends(get_queue),
    redis_client = Depends(get_redis_client)
):
    """Health check endpoint with queue and error metrics."""
    
    # Get queue depth
    queue_depth = len(queue)
    
    # Get jobs in flight (processing status)
    jobs_inflight = db.query(Job).filter(Job.status == "processing").count()
    
    # Calculate error rate in last 15 minutes
    fifteen_min_ago = datetime.utcnow() - timedelta(minutes=15)
    
    total_recent = db.query(Job).filter(
        Job.created_at >= fifteen_min_ago
    ).count()
    
    failed_recent = db.query(Job).filter(
        Job.created_at >= fifteen_min_ago,
        Job.status == "failed"
    ).count()
    
    err_rate_15m = failed_recent / max(total_recent, 1) * 100
    
    return HealthResponse(
        status="ok",
        queue_depth=queue_depth,
        jobs_inflight=jobs_inflight,
        err_rate_15m=round(err_rate_15m, 2)
    )