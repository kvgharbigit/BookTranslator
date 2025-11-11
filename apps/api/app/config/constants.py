"""Application constants that don't need to be secret.

These are configuration values that can safely live in source code.
Only actual secrets (API keys, passwords) should be in environment variables.
"""

# Server Configuration
DEFAULT_PORT = 8000
DEFAULT_LOG_LEVEL = "info"

# Storage Configuration
R2_BUCKET = "epub-translator-production"
R2_REGION = "auto"
SIGNED_GET_TTL_SECONDS = 432000  # 5 days

# Pricing Configuration
MIN_PRICE_CENTS = 50
TARGET_PROFIT_CENTS = 40
PRICE_CENTS_PER_MILLION_TOKENS = 300
MICROPAYMENTS_THRESHOLD_CENTS = 800

# Translation Configuration
DEFAULT_PROVIDER = "gemini"  # Best quality for production
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash-lite"
DEFAULT_GROQ_MODEL = "llama-3.1-8b-instant"
MAX_BATCH_TOKENS = 6000
MAX_JOB_TOKENS = 1_000_000
MAX_FILE_TOKENS = 1_000_000
RETRY_LIMIT = 3

# Queue Configuration
DEFAULT_RQ_QUEUES = "translate"
MAX_CONCURRENT_JOBS = 5
RETENTION_DAYS = 5

# Output Configuration
GENERATE_PDF = True
GENERATE_TXT = True

# Email Configuration
DEFAULT_EMAIL_PROVIDER = "resend"
EMAIL_FROM = "noreply@polytext.site"

# Security & Rate Limiting
RATE_LIMIT_BURST = 10
RATE_LIMIT_PER_HOUR = 60
MAX_FILE_MB = 200
MAX_ZIP_ENTRIES = 5000
MAX_COMPRESSION_RATIO = 10

# URL Configuration (environment-dependent)
# These are set based on ENV variable
def get_frontend_url(env: str) -> str:
    """Get frontend URL based on environment."""
    if env == "production":
        return "https://www.polytext.site"
    return "http://localhost:3000"
