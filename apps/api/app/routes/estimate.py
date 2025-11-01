from fastapi import APIRouter, HTTPException, Request, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings
from app.deps import get_storage
from app.pricing import estimate_price_from_size
from app.schemas import EstimateRequest, EstimateResponse
from app.logger import get_logger

logger = get_logger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)
router = APIRouter()


@router.post("/estimate", response_model=EstimateResponse)
@limiter.limit(f"{settings.rate_limit_per_hour}/hour")
async def estimate_price(
    request: Request,
    data: EstimateRequest,
    storage = Depends(get_storage)
):
    """Estimate translation price from uploaded file size."""
    
    try:
        # Get file size from R2
        size_bytes = storage.get_object_size(data.key)
        
        if size_bytes is None:
            raise HTTPException(
                status_code=404,
                detail="File not found or not yet uploaded"
            )
        
        # Validate file size
        max_bytes = settings.max_file_mb * 1024 * 1024
        if size_bytes > max_bytes:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {settings.max_file_mb}MB"
            )
        
        # Calculate price estimation
        tokens_est, price_cents = estimate_price_from_size(size_bytes)
        
        logger.info(
            f"Price estimate for {data.key}: {size_bytes} bytes -> "
            f"{tokens_est} tokens -> ${price_cents/100:.2f}"
        )
        
        return EstimateResponse(
            tokens_est=tokens_est,
            price_cents=price_cents,
            currency="usd"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to estimate price: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to estimate price"
        )