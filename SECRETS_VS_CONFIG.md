# Secrets vs Configuration

## Philosophy

**Secrets** (API keys, passwords, tokens) go in environment variables.
**Configuration** (numbers, booleans, constants) go in source code.

## What Are Secrets?

Secrets are values that:
- Must be kept private
- Would compromise security if exposed
- Are different per environment (dev vs prod)
- Should never be committed to Git

### Examples of Secrets:
- ✅ `GEMINI_API_KEY`
- ✅ `PAYPAL_CLIENT_SECRET`
- ✅ `DATABASE_URL`
- ✅ `R2_SECRET_ACCESS_KEY`
- ✅ `RESEND_API_KEY`

## What Are NOT Secrets?

Configuration constants that:
- Are safe to commit to Git
- Don't compromise security if public
- Rarely change
- Are the same across environments

### Examples of Non-Secrets:
- ❌ `MAX_FILE_MB=200`
- ❌ `RETRY_LIMIT=3`
- ❌ `MIN_PRICE_CENTS=50`
- ❌ `R2_BUCKET=epub-translator-production`
- ❌ `EMAIL_FROM=noreply@polytext.site`

---

## Our Implementation

### Secrets → Environment Variables
File: `.env.local` (local) or Railway Dashboard (production)

```bash
# SECRETS ONLY
ENV=production
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
GEMINI_API_KEY=AIzaSy...
GROQ_API_KEY=gsk_...
PAYPAL_CLIENT_ID=...
PAYPAL_CLIENT_SECRET=...
PAYPAL_WEBHOOK_ID=...
R2_ACCOUNT_ID=...
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
RESEND_API_KEY=re_...
```

### Configuration → Source Code
File: `apps/api/app/config/constants.py`

```python
# NON-SECRETS - Safe to commit
MIN_PRICE_CENTS = 50
TARGET_PROFIT_CENTS = 40
MAX_FILE_MB = 200
MAX_BATCH_TOKENS = 6000
RETRY_LIMIT = 3
R2_BUCKET = "epub-translator-production"
EMAIL_FROM = "noreply@polytext.site"

# Environment-dependent URLs (auto-detected)
def get_frontend_url(env: str) -> str:
    if env == "production":
        return "https://www.polytext.site"
    return "http://localhost:3000"
```

---

## Benefits

### ✅ Simpler Environment Setup
**Before:**
```bash
# 40+ environment variables to set
MIN_PRICE_CENTS=50
TARGET_PROFIT_CENTS=40
MAX_FILE_MB=200
RETRY_LIMIT=3
R2_BUCKET=epub-translator-production
# ... 35 more
```

**After:**
```bash
# ~10 secrets only
GEMINI_API_KEY=...
GROQ_API_KEY=...
DATABASE_URL=...
REDIS_URL=...
```

### ✅ Easier to Change Configuration
**Before:** Need to update Railway environment variables and redeploy

**After:** Just edit `constants.py`, commit, and push

### ✅ Version-Controlled Configuration
All non-secret config is in Git, so you have history and can review changes

### ✅ Clearer Separation
It's obvious what's a secret vs what's just configuration

---

## Railway Variables (Production)

You now only need these ~10 variables:

### Required Secrets:
```bash
ENV=production
DATABASE_URL=${​{Postgres.DATABASE_URL}}  # Railway auto-provides
REDIS_URL=${​{Redis.REDIS_URL}}  # Railway auto-provides
GEMINI_API_KEY=your_key
GROQ_API_KEY=your_key
PAYPAL_CLIENT_ID=your_id
PAYPAL_CLIENT_SECRET=your_secret
PAYPAL_WEBHOOK_ID=your_webhook
PAYPAL_ENVIRONMENT=live
R2_ACCOUNT_ID=your_account
R2_ACCESS_KEY_ID=your_key
R2_SECRET_ACCESS_KEY=your_secret
RESEND_API_KEY=your_key
```

### NOT Needed (Now in Code):
```bash
# Remove these from Railway:
MIN_PRICE_CENTS  ❌
TARGET_PROFIT_CENTS  ❌
PRICE_CENTS_PER_MILLION_TOKENS  ❌
MICROPAYMENTS_THRESHOLD_CENTS  ❌
GEMINI_MODEL  ❌
GROQ_MODEL  ❌
MAX_BATCH_TOKENS  ❌
MAX_JOB_TOKENS  ❌
MAX_FILE_TOKENS  ❌
RETRY_LIMIT  ❌
RQ_QUEUES  ❌
MAX_CONCURRENT_JOBS  ❌
RETENTION_DAYS  ❌
GENERATE_PDF  ❌
GENERATE_TXT  ❌
EMAIL_PROVIDER  ❌
EMAIL_FROM  ❌
RATE_LIMIT_BURST  ❌
RATE_LIMIT_PER_HOUR  ❌
MAX_FILE_MB  ❌
MAX_ZIP_ENTRIES  ❌
MAX_COMPRESSION_RATIO  ❌
R2_BUCKET  ❌
R2_REGION  ❌
SIGNED_GET_TTL_SECONDS  ❌
FRONTEND_URL  ❌  (Auto-detected from ENV)
PORT  ❌
LOG_LEVEL  ❌
```

---

## Migration Guide

### For Railway (Production):

1. Your current variables work fine (backward compatible)
2. You can safely remove non-secret variables over time
3. New deployments automatically use constants from code

### For Local Development:

Your `.env.local` now only needs secrets - much simpler!

---

## Example: Changing Pricing

**Before (Environment Variable):**
1. Go to Railway Dashboard
2. Find `MIN_PRICE_CENTS`
3. Change value
4. Wait for redeploy (~2 min)
5. Test

**After (Source Code):**
1. Edit `apps/api/app/config/constants.py`:
   ```python
   MIN_PRICE_CENTS = 100  # Changed from 50
   ```
2. Commit and push
3. Railway auto-deploys
4. Test

Same effort, but now it's version-controlled and reviewable!

---

## Security Note

`FRONTEND_URL` is NOT a secret, but it's auto-detected from `ENV`:
- `ENV=development` → `http://localhost:3000`
- `ENV=production` → `https://www.polytext.site`

You can still override it via environment variable if needed.
