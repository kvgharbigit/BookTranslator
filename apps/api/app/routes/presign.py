import uuid
from fastapi import APIRouter, HTTPException, Request, Depends
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

from app.config import settings
from app.deps import get_storage
from app.schemas import PresignUploadRequest, PresignUploadResponse
from app.logger import get_logger

logger = get_logger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)
router = APIRouter()


@router.post("/presign-upload", response_model=PresignUploadResponse)
@limiter.limit(f"{settings.rate_limit_per_hour}/hour")
async def presign_upload(
    request: Request,
    data: PresignUploadRequest,
    storage = Depends(get_storage)
):
    """Generate presigned URL for EPUB upload."""
    
    # Validate file type
    if not data.filename.lower().endswith('.epub'):
        raise HTTPException(
            status_code=400,
            detail="Only EPUB files are supported"
        )
    
    if data.content_type != "application/epub+zip":
        raise HTTPException(
            status_code=400,
            detail="Invalid content type. Must be application/epub+zip"
        )
    
    # Generate unique key for upload
    job_id = str(uuid.uuid4())
    key = f"uploads/{job_id}/{data.filename}"
    
    try:
        # Generate presigned upload URL
        upload_url = storage.generate_presigned_upload_url(
            key=key,
            content_type=data.content_type,
            expires_in=3600  # 1 hour
        )
        
        max_bytes = settings.max_file_mb * 1024 * 1024  # Convert MB to bytes
        
        logger.info(f"Generated presigned upload for {data.filename}, key: {key}")
        
        return PresignUploadResponse(
            key=key,
            upload_url=upload_url,
            max_bytes=max_bytes
        )
        
    except Exception as e:
        logger.error(f"Failed to generate presigned upload URL: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate upload URL"
        )