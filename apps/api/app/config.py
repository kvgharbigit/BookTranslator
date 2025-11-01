from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings using environment variables."""
    
    # Server
    port: int = Field(default=8000, alias="PORT")
    env: str = Field(default="development", alias="ENV")
    log_level: str = Field(default="info", alias="LOG_LEVEL")
    database_url: str = Field(default="sqlite:///./data/jobs.db", alias="DATABASE_URL")
    
    # Cloudflare R2 Storage
    r2_account_id: str = Field(alias="R2_ACCOUNT_ID")
    r2_access_key_id: str = Field(alias="R2_ACCESS_KEY_ID")
    r2_secret_access_key: str = Field(alias="R2_SECRET_ACCESS_KEY")
    r2_bucket: str = Field(default="epub-translator", alias="R2_BUCKET")
    r2_region: str = Field(default="auto", alias="R2_REGION")
    signed_get_ttl_seconds: int = Field(default=172800, alias="SIGNED_GET_TTL_SECONDS")  # 48h
    
    # Stripe Payments
    stripe_secret_key: str = Field(alias="STRIPE_SECRET_KEY")
    stripe_webhook_secret: str = Field(alias="STRIPE_WEBHOOK_SECRET")
    min_price_cents: int = Field(default=100, alias="MIN_PRICE_CENTS")
    price_cents_per_million_tokens: int = Field(default=300, alias="PRICE_CENTS_PER_MILLION_TOKENS")
    
    # Translation Providers
    provider: str = Field(default="gemini", alias="PROVIDER")
    gemini_api_key: str = Field(alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="text-multilingual-2.5-flash-lite", alias="GEMINI_MODEL")
    groq_api_key: str = Field(alias="GROQ_API_KEY")
    groq_model: str = Field(default="llama-3.1-8b-instant", alias="GROQ_MODEL")
    max_batch_tokens: int = Field(default=6000, alias="MAX_BATCH_TOKENS")
    max_job_tokens: int = Field(default=1000000, alias="MAX_JOB_TOKENS")
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


# Global settings instance
settings = Settings()