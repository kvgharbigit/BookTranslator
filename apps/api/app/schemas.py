from datetime import datetime
from typing import Optional, Dict

from pydantic import BaseModel, Field


class PresignUploadRequest(BaseModel):
    filename: str = Field(..., description="Original filename")
    content_type: str = Field(default="application/epub+zip", description="MIME type")


class PresignUploadResponse(BaseModel):
    key: str = Field(..., description="R2 object key")
    upload_url: str = Field(..., description="Presigned PUT URL")
    max_bytes: int = Field(..., description="Maximum file size")


class EstimateRequest(BaseModel):
    key: str = Field(..., description="R2 object key")
    target_lang: str = Field(..., description="Target language code")


class EstimateResponse(BaseModel):
    tokens_est: int = Field(..., description="Estimated tokens")
    price_cents: int = Field(..., description="Price in cents")
    currency: str = Field(default="usd", description="Currency code")


class CreateCheckoutRequest(BaseModel):
    key: str = Field(..., description="R2 object key")
    target_lang: str = Field(..., description="Target language code")
    email: Optional[str] = Field(None, description="Email for delivery")
    price_cents: int = Field(..., description="Expected price in cents")
    provider: Optional[str] = Field(None, description="Preferred provider")


class CreateCheckoutResponse(BaseModel):
    checkout_url: str = Field(..., description="Stripe Checkout URL")


class JobStatusResponse(BaseModel):
    id: str = Field(..., description="Job ID")
    status: str = Field(..., description="Job status")
    progress_step: str = Field(..., description="Current progress step")
    created_at: datetime = Field(..., description="Creation timestamp")
    download_urls: Optional[Dict[str, str]] = Field(None, description="Download URLs by format")
    expires_at: Optional[datetime] = Field(None, description="Download link expiration")
    error: Optional[str] = Field(None, description="Error message if failed")


class HealthResponse(BaseModel):
    status: str = Field(default="ok", description="Health status")
    queue_depth: int = Field(..., description="Number of queued jobs")
    jobs_inflight: int = Field(..., description="Number of processing jobs")
    err_rate_15m: float = Field(..., description="Error rate in last 15 minutes")