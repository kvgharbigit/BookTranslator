from fastapi import APIRouter, HTTPException, Request, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings
from app.deps import get_storage
from app.pricing import estimate_price_from_size, estimate_price_from_file
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
        
        # Validate file size (hard limit)
        max_bytes = settings.max_file_mb * 1024 * 1024
        if size_bytes > max_bytes:
            size_mb = size_bytes / (1024 * 1024)
            raise HTTPException(
                status_code=400,
                detail=f"File size limit exceeded: {size_mb:.1f}MB > {settings.max_file_mb}MB maximum. Please use a smaller file."
            )
        
        # For EPUB files, download and analyze text content
        if data.key.lower().endswith('.epub'):
            # Download file temporarily for text extraction
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(suffix='.epub', delete=False) as temp_file:
                temp_file_path = temp_file.name
            
            try:
                success = storage.download_file(data.key, temp_file_path)
                if success:
                    tokens_est, price_cents = estimate_price_from_file(temp_file_path)
                    logger.info(f"EPUB analysis successful: {tokens_est:,} tokens → ${price_cents/100:.2f}")
                else:
                    logger.warning("Failed to download EPUB file, using size fallback")
                    tokens_est, price_cents = estimate_price_from_size(size_bytes)
            except ValueError as e:
                # Content limit exceeded - return user-friendly 400 error
                raise HTTPException(
                    status_code=400,
                    detail=str(e)
                )
            except Exception as e:
                logger.warning(f"Failed to extract EPUB text, using size fallback: {e}")
                tokens_est, price_cents = estimate_price_from_size(size_bytes)
            finally:
                # Clean up temp file
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
        else:
            # For non-EPUB files, use size-based estimation
            try:
                tokens_est, price_cents = estimate_price_from_size(size_bytes)
            except ValueError as e:
                # Content limit exceeded - return user-friendly 400 error
                raise HTTPException(
                    status_code=400,
                    detail=str(e)
                )

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