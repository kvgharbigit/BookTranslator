from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings using environment variables."""
    
    # Server
    port: int = Field(default=8000, alias="PORT")
    env: str = Field(default="development", alias="ENV")
    log_level: str = Field(default="info", alias="LOG_LEVEL")
    database_url: str = Field(default="sqlite:///./data/jobs.db", alias="DATABASE_URL")
    
    # Cloudflare R2 Storage (Required - No Local Fallback)
    r2_account_id: str = Field(alias="R2_ACCOUNT_ID")
    r2_access_key_id: str = Field(alias="R2_ACCESS_KEY_ID")
    r2_secret_access_key: str = Field(alias="R2_SECRET_ACCESS_KEY")
    r2_bucket: str = Field(default="epub-translator-production", alias="R2_BUCKET")
    r2_region: str = Field(default="auto", alias="R2_REGION")
    signed_get_ttl_seconds: int = Field(default=432000, alias="SIGNED_GET_TTL_SECONDS")  # 5 days (5 * 24 * 60 * 60)
    
    # Payment Processing (PayPal only)
    min_price_cents: int = Field(default=50, alias="MIN_PRICE_CENTS")
    target_profit_cents: int = Field(default=40, alias="TARGET_PROFIT_CENTS")
    price_cents_per_million_tokens: int = Field(default=300, alias="PRICE_CENTS_PER_MILLION_TOKENS")
    
    # PayPal Micropayments
    paypal_client_id: str = Field(alias="PAYPAL_CLIENT_ID")
    paypal_client_secret: str = Field(alias="PAYPAL_CLIENT_SECRET")
    paypal_environment: str = Field(default="sandbox", alias="PAYPAL_ENVIRONMENT")  # "sandbox" or "live"
    paypal_webhook_id: str = Field(alias="PAYPAL_WEBHOOK_ID")
    micropayments_threshold_cents: int = Field(default=800, alias="MICROPAYMENTS_THRESHOLD_CENTS")
    
    # Translation Providers
    # NOTE: Default models are defined in app.config.models (single source of truth)
    # These defaults should match DEFAULT_GEMINI_MODEL and DEFAULT_GROQ_MODEL
    provider: str = Field(default="gemini", alias="PROVIDER")
    gemini_api_key: str = Field(alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.5-flash-lite", alias="GEMINI_MODEL")  # Should match app.config.models.DEFAULT_GEMINI_MODEL
    groq_api_key: str = Field(alias="GROQ_API_KEY")
    groq_model: str = Field(default="llama-3.1-8b-instant", alias="GROQ_MODEL")  # Should match app.config.models.DEFAULT_GROQ_MODEL
    max_batch_tokens: int = Field(default=6000, alias="MAX_BATCH_TOKENS")
    max_job_tokens: int = Field(default=1000000, alias="MAX_JOB_TOKENS")
    max_file_tokens: int = Field(default=1000000, alias="MAX_FILE_TOKENS")  # 1M token limit for pricing tiers
    retry_limit: int = Field(default=3, alias="RETRY_LIMIT")
    
    # Queue & Processing
    redis_url: str = Field(alias="REDIS_URL")
    rq_queues: str = Field(default="translate", alias="RQ_QUEUES")
    max_concurrent_jobs: int = Field(default=5, alias="MAX_CONCURRENT_JOBS")
    retention_days: int = Field(default=7, alias="RETENTION_DAYS")
    
    # Multi-Format Output
    generate_pdf: bool = Field(default=True, alias="GENERATE_PDF")
    generate_txt: bool = Field(default=True, alias="GENERATE_TXT")
    
    # Email
    email_provider: str = Field(default="resend", alias="EMAIL_PROVIDER")
    resend_api_key: str = Field(alias="RESEND_API_KEY")
    email_from: str = Field(alias="EMAIL_FROM")
    
    # Security & Rate Limiting
    rate_limit_burst: int = Field(default=10, alias="RATE_LIMIT_BURST")
    rate_limit_per_hour: int = Field(default=60, alias="RATE_LIMIT_PER_HOUR")
    max_file_mb: int = Field(default=200, alias="MAX_FILE_MB")
    max_zip_entries: int = Field(default=5000, alias="MAX_ZIP_ENTRIES")
    max_compression_ratio: int = Field(default=10, alias="MAX_COMPRESSION_RATIO")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra environment variables


# Global settings instance
settings = Settings()