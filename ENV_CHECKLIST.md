# Environment Variables Checklist

## ✅ Current Status

### Local Development Files (NOT in Git)

**`apps/api/.env.local`**
- ✅ `FRONTEND_URL=http://localhost:3000`
- ✅ `DATABASE_URL=postgresql://...` (Railway external URL)
- ✅ `REDIS_URL=redis://localhost:6379`
- ✅ All required API keys present
- ✅ R2 Storage configured
- ✅ Email (Resend) configured

**`apps/web/.env.local`**
- ✅ `NEXT_PUBLIC_API_BASE=http://localhost:8000`

### Example Files (IN Git - Safe Templates)

**`apps/api/.env.example`**
- ✅ `FRONTEND_URL=https://www.polytext.site` (production example)
- ✅ All required variables documented
- ✅ No real credentials

**`apps/web/.env.example`**
- ✅ `NEXT_PUBLIC_API_BASE=https://api.polytext.site` (production example)
- ✅ Local dev example commented

---

## 🚀 Production Setup Required

### Railway (API/Worker Service)

You need to set these in Railway Dashboard → Variables:

```bash
# CRITICAL - Must be set for redirect to work
FRONTEND_URL=https://www.polytext.site

# Server
ENV=production
PORT=8000
LOG_LEVEL=info
DATABASE_URL=postgresql://...  # Railway provides this automatically

# Redis
REDIS_URL=redis://...  # Railway provides this automatically

# R2 Storage
R2_ACCOUNT_ID=your_r2_account_id
R2_ACCESS_KEY_ID=your_r2_access_key
R2_SECRET_ACCESS_KEY=your_r2_secret_key
R2_BUCKET=epub-translator-production
R2_REGION=auto
SIGNED_GET_TTL_SECONDS=432000

# PayPal (Production)
PAYPAL_CLIENT_ID=your_production_client_id
PAYPAL_CLIENT_SECRET=your_production_secret
PAYPAL_ENVIRONMENT=live
PAYPAL_WEBHOOK_ID=your_production_webhook_id
MICROPAYMENTS_THRESHOLD_CENTS=800

# Pricing
MIN_PRICE_CENTS=50
TARGET_PROFIT_CENTS=40
PRICE_CENTS_PER_MILLION_TOKENS=300

# LLM Providers
PROVIDER=gemini
GEMINI_API_KEY=your_production_gemini_key
GEMINI_MODEL=gemini-2.5-flash-lite
GROQ_API_KEY=your_production_groq_key
GROQ_MODEL=llama-3.1-8b-instant
MAX_BATCH_TOKENS=6000
MAX_JOB_TOKENS=1000000
MAX_FILE_TOKENS=1000000
RETRY_LIMIT=3

# Queue & Processing
RQ_QUEUES=translate
MAX_CONCURRENT_JOBS=5
RETENTION_DAYS=5

# Output Formats
GENERATE_PDF=true
GENERATE_TXT=true

# Email (Resend)
EMAIL_PROVIDER=resend
RESEND_API_KEY=your_production_resend_key
EMAIL_FROM=noreply@polytext.site

# Security & Rate Limiting
RATE_LIMIT_BURST=10
RATE_LIMIT_PER_HOUR=60
MAX_FILE_MB=200
MAX_ZIP_ENTRIES=5000
MAX_COMPRESSION_RATIO=10
```

### Vercel (Frontend)

You need to set these in Vercel Dashboard → Settings → Environment Variables:

```bash
NEXT_PUBLIC_API_BASE=https://api.polytext.site
```

---

## 🎯 URL Summary

### Local Development
| Component | URL |
|-----------|-----|
| Frontend | `http://localhost:3000` |
| API | `http://localhost:8000` |
| Redis | `redis://localhost:6379` |
| Database | Railway external URL |

### Production
| Component | URL |
|-----------|-----|
| Frontend | `https://www.polytext.site` |
| API | `https://api.polytext.site` |
| Redis | Railway internal URL |
| Database | Railway internal URL |

---

## 🔍 How to Verify

### Local Setup is Correct:
```bash
# Check API config
cd apps/api
python -c "from app.config import settings; print(f'FRONTEND_URL: {settings.frontend_url}')"
# Should output: FRONTEND_URL: http://localhost:3000

# Check Frontend can start
cd apps/web
npm run dev
# Should NOT see any errors about missing NEXT_PUBLIC_API_BASE
```

### Production Setup is Correct:

**Railway:**
```bash
railway variables | grep FRONTEND_URL
# Should show: FRONTEND_URL=https://www.polytext.site
```

**Vercel:**
```bash
vercel env ls
# Should show NEXT_PUBLIC_API_BASE for production
```

---

## ⚠️ Common Issues

### Issue: "Redirecting to localhost after payment"
**Cause:** `FRONTEND_URL` not set in Railway
**Fix:** `railway variables --set FRONTEND_URL=https://www.polytext.site`

### Issue: "NEXT_PUBLIC_API_BASE environment variable is not set"
**Cause:** Missing env var in Vercel or local `.env.local`
**Fix (Local):** Create `apps/web/.env.local` with `NEXT_PUBLIC_API_BASE=http://localhost:8000`
**Fix (Production):** Add to Vercel dashboard

### Issue: "Connection refused to localhost:8000"
**Cause:** Frontend trying to connect to local API in production
**Fix:** Verify `NEXT_PUBLIC_API_BASE=https://api.polytext.site` in Vercel

---

## 📝 Quick Commands

### Set Railway Variables (if not using dashboard):
```bash
railway variables --set FRONTEND_URL=https://www.polytext.site
railway variables --set GEMINI_API_KEY=your_key
railway variables --set GROQ_API_KEY=your_key
# ... etc for all variables
```

### Set Vercel Variables (if not using dashboard):
```bash
vercel env add NEXT_PUBLIC_API_BASE production
# Enter: https://api.polytext.site
```

### View Current Variables:
```bash
# Railway
railway variables

# Vercel
vercel env ls
```
