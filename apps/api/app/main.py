import time
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.logger import setup_logging, get_logger, set_request_id
from app.db import create_tables
from app.routes import health, presign, estimate, checkout, webhook, jobs, paypal, skip_payment

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="BookTranslator API",
    description="AI-powered EPUB translation service with multi-format output (EPUB, PDF, TXT)",
    version="1.0.0"
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:8000",
    "https://polytext.site",
    "https://www.polytext.site",
    "https://api.polytext.site"
]

if settings.env == "development":
    allowed_origins.append("*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id_middleware(request: Request, call_next):
    """Add request ID to all requests for logging correlation."""
    request_id = set_request_id()
    request.state.request_id = request_id
    
    # Add X-Request-Id header to response
    response = await call_next(request)
    response.headers["X-Request-Id"] = request_id
    
    return response


@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    """Log all HTTP requests with clear formatting."""
    start_time = time.time()

    # Only log start for non-polling endpoints to reduce noise
    is_job_poll = request.url.path.startswith("/job/") and request.method == "GET"

    if not is_job_poll:
        logger.info(f"➤ {request.method} {request.url.path}")

    response = await call_next(request)

    process_time = time.time() - start_time

    # Status emoji for quick scanning
    if response.status_code < 300:
        status_emoji = "✓"
    elif response.status_code < 400:
        status_emoji = "↻"
    elif response.status_code < 500:
        status_emoji = "⚠"
    else:
        status_emoji = "✗"

    # Only log completion for important endpoints or slow requests
    if not is_job_poll or process_time > 0.5:
        logger.info(
            f"{status_emoji} {request.method} {request.url.path} → {response.status_code} ({process_time:.3f}s)"
        )

    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "request_id": getattr(request.state, "request_id", "unknown")
        }
    )


# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(presign.router, tags=["Upload"])
app.include_router(estimate.router, tags=["Pricing"])
app.include_router(checkout.router, tags=["Payment"])
app.include_router(webhook.router, tags=["Webhooks"])
app.include_router(paypal.router, prefix="/api/paypal", tags=["PayPal"])
app.include_router(jobs.router, tags=["Jobs"])
app.include_router(skip_payment.router, tags=["Testing"])


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("Starting BookTranslator API")

    # Create database tables
    create_tables()
    logger.info("Database tables created/verified")

    # Log configuration
    logger.info(f"Environment: {settings.env}")
    logger.info(f"Provider: {settings.provider}")
    logger.info(f"Storage: Cloudflare R2 ({settings.r2_bucket})")
    logger.info(f"Max file size: {settings.max_file_mb}MB")
    logger.info(f"Price per million tokens: ${settings.price_cents_per_million_tokens/100:.2f}")

    logger.info("BookTranslator API started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    logger.info("Shutting down BookTranslator API")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "BookTranslator API",
        "version": "1.0.0",
        "status": "running",
        "storage": "Cloudflare R2",
        "features": [
            "Multi-format output (EPUB + PDF + TXT)",
            "Groq Llama 3.1 (testing) + Gemini 2.5 Flash-Lite (production)",
            "Batch-level progress tracking (0-100%)",
            "PayPal micropayments",
            "$0.50 minimum pricing",
            "No accounts required",
            "5-day file retention"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    import time
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.port,
        log_level=settings.log_level.lower(),
        reload=settings.env == "development"
    )