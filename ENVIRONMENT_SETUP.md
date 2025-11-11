# Environment Variable Setup

This document explains all environment variables and how to configure them for different deployment types.

## Deployment Types

### 1. Local Development
- API runs on `localhost:8000`
- Frontend runs on `localhost:3000`
- Uses local Redis
- Connects to Railway PostgreSQL (external URL)

### 2. Production (Railway + Vercel)
- API deployed on Railway
- Frontend deployed on Vercel
- **NO localhost fallbacks** - all URLs must be explicitly configured

---

## API Environment Variables

### Required for ALL Deployments

These variables **MUST** be set in production. No fallbacks exist.

```bash
# Server
PORT=8000
ENV=production  # "development" for local
LOG_LEVEL=info
DATABASE_URL=postgresql://...
FRONTEND_URL=https://www.polytext.site  # REQUIRED - no localhost fallback

# Cloudflare R2 Storage
R2_ACCOUNT_ID=your_account_id
R2_ACCESS_KEY_ID=your_access_key
R2_SECRET_ACCESS_KEY=your_secret_key
R2_BUCKET=epub-translator-production
R2_REGION=auto
SIGNED_GET_TTL_SECONDS=432000  # 5 days

# PayPal
PAYPAL_CLIENT_ID=your_client_id
PAYPAL_CLIENT_SECRET=your_secret
PAYPAL_ENVIRONMENT=live  # "sandbox" for testing
PAYPAL_WEBHOOK_ID=your_webhook_id

# LLM Providers
PROVIDER=gemini
GEMINI_API_KEY=your_key
GEMINI_MODEL=gemini-2.5-flash-lite
GROQ_API_KEY=your_key
GROQ_MODEL=llama-3.1-8b-instant

# Redis Queue
REDIS_URL=redis://...

# Email (Resend)
EMAIL_PROVIDER=resend
RESEND_API_KEY=your_key
EMAIL_FROM=noreply@polytext.site
```

### File Locations

**Local Development:**
- `apps/api/.env` - Basic local config (not used by default)
- `apps/api/.env.local` - Active local config with real keys
- `apps/api/.env.local.worker` - Worker-specific env loader
- `.env` - Root level (legacy, not actively used)

**Production (Railway):**
- Set via Railway dashboard under "Variables" tab
- Or via CLI: `railway variables --set KEY=VALUE`

---

## Frontend Environment Variables

### Required for ALL Deployments

```bash
NEXT_PUBLIC_API_BASE=https://api.polytext.site  # REQUIRED - no localhost fallback
```

### File Locations

**Local Development:**
- `apps/web/.env.local`:
  ```bash
  NEXT_PUBLIC_API_BASE=http://localhost:8000
  ```

**Production (Vercel):**
- Set via Vercel dashboard under "Settings → Environment Variables"
- Or via CLI: `vercel env add NEXT_PUBLIC_API_BASE`
- Value: `https://api.polytext.site`

---

## Setting Up Environments

### Local Development Setup

1. **API Setup:**
   ```bash
   cd apps/api
   cp .env.example .env.local
   # Edit .env.local with your actual keys
   # Make sure FRONTEND_URL=http://localhost:3000
   ```

2. **Frontend Setup:**
   ```bash
   cd apps/web
   echo "NEXT_PUBLIC_API_BASE=http://localhost:8000" > .env.local
   ```

3. **Start Services:**
   ```bash
   # Terminal 1: Start Redis
   redis-server

   # Terminal 2: Start API
   cd apps/api
   uvicorn app.main:app --reload --port 8000

   # Terminal 3: Start Worker
   cd apps/api
   source .env.local.worker
   PYTHONPATH=/path/to/BookTranslator poetry run rq worker translate

   # Terminal 4: Start Frontend
   cd apps/web
   npm run dev
   ```

### Production Setup (Railway API)

1. Go to Railway dashboard → Your project → API service
2. Click **Variables** tab
3. Add each required variable manually or via CLI:
   ```bash
   railway variables --set ENV=production
   railway variables --set FRONTEND_URL=https://www.polytext.site
   railway variables --set DATABASE_URL=postgresql://...
   # ... etc for all required vars
   ```
4. Railway will automatically redeploy after adding variables

**Critical Production Variables:**
- `FRONTEND_URL=https://www.polytext.site` ← **MUST BE SET**
- `ENV=production`
- All payment, storage, and email credentials

### Production Setup (Vercel Frontend)

1. Go to Vercel dashboard → Your project → Settings → Environment Variables
2. Add:
   ```
   Name: NEXT_PUBLIC_API_BASE
   Value: https://api.polytext.site
   ```
3. Or via CLI:
   ```bash
   vercel env add NEXT_PUBLIC_API_BASE production
   # Enter value: https://api.polytext.site
   ```
4. Redeploy for changes to take effect

---

## Important Notes

### No Localhost Fallbacks

**Before (BAD):**
```typescript
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
```

**After (GOOD):**
```typescript
const API_BASE = process.env.NEXT_PUBLIC_API_BASE;
if (!API_BASE) {
  throw new Error('NEXT_PUBLIC_API_BASE environment variable is not set');
}
```

This ensures:
- ✅ Production deployments fail fast if misconfigured
- ✅ No silent fallback to localhost in production
- ✅ Clear error messages when env vars are missing
- ✅ Explicit configuration for each deployment type

### Environment-Specific Behavior

The system behavior is **siloed by deployment**:

| Variable | Local Dev | Production |
|----------|-----------|------------|
| `FRONTEND_URL` | `http://localhost:3000` | `https://www.polytext.site` |
| `NEXT_PUBLIC_API_BASE` | `http://localhost:8000` | `https://api.polytext.site` |
| `ENV` | `development` | `production` |
| `REDIS_URL` | `redis://localhost:6379` | Railway Redis URL |

### Security

- ❌ Never commit `.env`, `.env.local`, or files with real keys
- ✅ Only commit `.env.example` files
- ✅ Use different keys for dev vs production
- ✅ Rotate keys regularly

---

## Troubleshooting

### "NEXT_PUBLIC_API_BASE environment variable is not set"
**Problem:** Frontend trying to run without API URL configured

**Fix:**
- Local: Create `apps/web/.env.local` with `NEXT_PUBLIC_API_BASE=http://localhost:8000`
- Production: Add variable in Vercel dashboard

### "Redirecting to localhost after payment"
**Problem:** `FRONTEND_URL` not set on Railway

**Fix:**
```bash
railway variables --set FRONTEND_URL=https://www.polytext.site
```

### "Connection refused to localhost:8000"
**Problem:** Frontend trying to connect to local API in production

**Fix:** Verify `NEXT_PUBLIC_API_BASE` is set correctly in Vercel

---

## Quick Reference

### Check Current Variables

**Railway:**
```bash
railway variables
```

**Vercel:**
```bash
vercel env ls
```

**Local:**
```bash
# API
cat apps/api/.env.local | grep -v "^#" | grep -v "^$"

# Frontend
cat apps/web/.env.local
```

### Test Configuration

**Local API:**
```bash
cd apps/api
python -c "from app.config import settings; print(f'FRONTEND_URL: {settings.frontend_url}')"
```

**Local Frontend:**
```bash
cd apps/web
npm run dev
# Check console for API_BASE errors
```
