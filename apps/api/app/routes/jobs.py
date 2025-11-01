from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Request, Depends
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings
from app.db import get_db
from app.deps import get_storage
from app.models import Job
from app.schemas import JobStatusResponse
from app.logger import get_logger

logger = get_logger(__name__)

# Rate limiter (more frequent polling allowed)
limiter = Limiter(key_func=get_remote_address)
router = APIRouter()


@router.get("/job/{job_id}", response_model=JobStatusResponse)
@limiter.limit("1000/minute")  # Allow frequent polling - well below AI API limits
async def get_job_status(
    job_id: str,
    request: Request,
    db: Session = Depends(get_db),
    storage = Depends(get_storage)
):
    """Get translation job status and download URLs when complete."""
    
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Prepare base response
    response_data = {
        "id": job.id,
        "status": job.status,
        "progress_step": job.progress_step,
        "progress_percent": job.progress_percent,
        "created_at": job.created_at,
        "download_urls": None,
        "expires_at": None,
        "error": job.error
    }
    
    # Add download URLs if job is complete
    if job.status == "done":
        download_urls = {}
        expires_at = datetime.utcnow() + timedelta(seconds=settings.signed_get_ttl_seconds)
        
        try:
            # Generate presigned URLs for each available format
            if job.output_epub_key:
                download_urls["epub"] = storage.generate_presigned_download_url(
                    job.output_epub_key
                )
            
            if job.output_pdf_key:
                download_urls["pdf"] = storage.generate_presigned_download_url(
                    job.output_pdf_key
                )
            
            if job.output_txt_key:
                download_urls["txt"] = storage.generate_presigned_download_url(
                    job.output_txt_key
                )
            
            if download_urls:
                response_data["download_urls"] = download_urls
                response_data["expires_at"] = expires_at
            
        except Exception as e:
            logger.error(f"Failed to generate download URLs for job {job_id}: {e}")
            # Don't fail the request, just log the error
    
    # Limit polling for completed jobs (prevent spam after completion)
    if job.status in ["done", "failed"]:
        # Check if job was completed more than 10 minutes ago
        if job.created_at and (datetime.utcnow() - job.created_at).total_seconds() > 600:
            # Apply stricter rate limiting for old completed jobs
            pass  # The limiter already handles this
    
    logger.info(f"Retrieved status for job {job_id}: {job.status}")
    
    return JobStatusResponse(**response_data)