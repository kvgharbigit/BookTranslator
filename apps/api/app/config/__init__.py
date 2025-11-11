"""Application configuration using Pydantic settings.

Only secrets (API keys, passwords, tokens) are loaded from environment variables.
Non-secret configuration constants are in app.config.constants.
"""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

from .constants import (
    DEFAULT_PORT,
    DEFAULT_LOG_LEVEL,
    R2_BUCKET,
    R2_REGION,
    SIGNED_GET_TTL_SECONDS,
    MIN_PRICE_CENTS,
    TARGET_PROFIT_CENTS,
    PRICE_CENTS_PER_MILLION_TOKENS,
    MICROPAYMENTS_THRESHOLD_CENTS,
    DEFAULT_PROVIDER,
    DEFAULT_GEMINI_MODEL,
    DEFAULT_GROQ_MODEL,
    MAX_BATCH_TOKENS,
    MAX_JOB_TOKENS,
    MAX_FILE_TOKENS,
    RETRY_LIMIT,
    DEFAULT_RQ_QUEUES,
    MAX_CONCURRENT_JOBS,
    RETENTION_DAYS,
    GENERATE_PDF,
    GENERATE_TXT,
    DEFAULT_EMAIL_PROVIDER,
    EMAIL_FROM,
    RATE_LIMIT_BURST,
    RATE_LIMIT_PER_HOUR,
    MAX_FILE_MB,
    MAX_ZIP_ENTRIES,
    MAX_COMPRESSION_RATIO,
    get_frontend_url,
)


class Settings(BaseSettings):
    """Application settings - only secrets from environment variables."""

    # Server Configuration
    port: int = Field(default=DEFAULT_PORT, alias="PORT")
    env: str = Field(default="development", alias="ENV")
    log_level: str = Field(default=DEFAULT_LOG_LEVEL, alias="LOG_LEVEL")

    # SECRETS - Must be in environment
    database_url: str = Field(alias="DATABASE_URL")
    redis_url: str = Field(alias="REDIS_URL")

    # Frontend URL (auto-determined from env, but can override)
    frontend_url: str | None = Field(default=None, alias="FRONTEND_URL")

    # R2 Storage SECRETS
    r2_account_id: str = Field(alias="R2_ACCOUNT_ID")
    r2_access_key_id: str = Field(alias="R2_ACCESS_KEY_ID")
    r2_secret_access_key: str = Field(alias="R2_SECRET_ACCESS_KEY")

    # R2 non-secrets (constants)
    r2_bucket: str = R2_BUCKET
    r2_region: str = R2_REGION
    signed_get_ttl_seconds: int = SIGNED_GET_TTL_SECONDS

    # PayPal SECRETS
    paypal_client_id: str = Field(alias="PAYPAL_CLIENT_ID")
    paypal_client_secret: str = Field(alias="PAYPAL_CLIENT_SECRET")
    paypal_webhook_id: str = Field(alias="PAYPAL_WEBHOOK_ID")
    paypal_environment: str = Field(default="sandbox", alias="PAYPAL_ENVIRONMENT")

    # Pricing (constants)
    min_price_cents: int = MIN_PRICE_CENTS
    target_profit_cents: int = TARGET_PROFIT_CENTS
    price_cents_per_million_tokens: int = PRICE_CENTS_PER_MILLION_TOKENS
    micropayments_threshold_cents: int = MICROPAYMENTS_THRESHOLD_CENTS

    # Translation Provider SECRETS
    gemini_api_key: str = Field(alias="GEMINI_API_KEY")
    groq_api_key: str = Field(alias="GROQ_API_KEY")

    # Translation non-secrets (constants)
    provider: str = DEFAULT_PROVIDER
    gemini_model: str = DEFAULT_GEMINI_MODEL
    groq_model: str = DEFAULT_GROQ_MODEL
    max_batch_tokens: int = MAX_BATCH_TOKENS
    max_job_tokens: int = MAX_JOB_TOKENS
    max_file_tokens: int = MAX_FILE_TOKENS
    retry_limit: int = RETRY_LIMIT

    # Queue (constants)
    rq_queues: str = DEFAULT_RQ_QUEUES
    max_concurrent_jobs: int = MAX_CONCURRENT_JOBS
    retention_days: int = RETENTION_DAYS

    # Output (constants)
    generate_pdf: bool = GENERATE_PDF
    generate_txt: bool = GENERATE_TXT

    # Email SECRETS
    resend_api_key: str = Field(alias="RESEND_API_KEY")

    # Email non-secrets (constants)
    email_provider: str = DEFAULT_EMAIL_PROVIDER
    email_from: str = EMAIL_FROM

    # Security (constants)
    rate_limit_burst: int = RATE_LIMIT_BURST
    rate_limit_per_hour: int = RATE_LIMIT_PER_HOUR
    max_file_mb: int = MAX_FILE_MB
    max_zip_entries: int = MAX_ZIP_ENTRIES
    max_compression_ratio: int = MAX_COMPRESSION_RATIO

    @field_validator("frontend_url", mode="before")
    @classmethod
    def set_frontend_url(cls, v, info):
        """Auto-set frontend URL based on environment if not provided."""
        if v is not None:
            return v
        env = info.data.get("env", "development")
        return get_frontend_url(env)

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


# Global settings instance
settings = Settings()

__all__ = ["settings", "Settings"]
