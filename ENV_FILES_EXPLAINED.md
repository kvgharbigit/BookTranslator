# Environment Files Explained

## Simple Rule: One for Local, One for Production

### Local Development (Your Computer)
```
apps/api/.env.local          ← Your local API config with real keys
apps/web/.env.local          ← Your local frontend config
apps/api/.env.local.worker   ← Helper script to load .env.local for worker
```

### Production (Cloud)
```
Railway Dashboard → Variables  ← Set API variables here
Vercel Dashboard → Variables   ← Set frontend variables here
```

### Documentation (Committed to Git)
```
apps/api/.env.example        ← Template showing what API needs
apps/web/.env.example        ← Template showing what frontend needs
```

---

## What Each File Does

### `apps/api/.env.local` (LOCAL ONLY - NOT COMMITTED)
Your personal local development config. Contains:
- `FRONTEND_URL=http://localhost:3000`
- `REDIS_URL=redis://localhost:6379`
- Real API keys for Gemini, Groq, PayPal, etc.
- Railway PostgreSQL connection string

**How to use:**
```bash
cd apps/api
cp .env.example .env.local
# Edit .env.local with your real keys
```

### `apps/web/.env.local` (LOCAL ONLY - NOT COMMITTED)
Your local frontend config. Contains just one line:
```bash
NEXT_PUBLIC_API_BASE=http://localhost:8000
```

**How to use:**
```bash
cd apps/web
echo "NEXT_PUBLIC_API_BASE=http://localhost:8000" > .env.local
```

### `apps/api/.env.local.worker` (HELPER SCRIPT)
Loads `.env.local` for the RQ worker and fixes macOS issues.

**How to use:**
```bash
cd apps/api
source .env.local.worker
poetry run rq worker translate
```

### `.env.example` Files (COMMITTED TO GIT)
Templates showing what variables are needed. Safe to commit because they don't contain real keys.

---

## Production Setup

### Railway (API/Worker)
1. Go to Railway Dashboard
2. Select your project → API service
3. Click "Variables" tab
4. Add each variable:
   ```
   FRONTEND_URL=https://www.polytext.site
   DATABASE_URL=postgresql://...
   REDIS_URL=redis://...
   GEMINI_API_KEY=...
   etc.
   ```

### Vercel (Frontend)
1. Go to Vercel Dashboard
2. Select your project → Settings → Environment Variables
3. Add:
   ```
   NEXT_PUBLIC_API_BASE=https://api.polytext.site
   ```

---

## The Key Principle

**Environment behavior is SILOED by deployment:**

| Variable | Local Dev | Production |
|----------|-----------|------------|
| `FRONTEND_URL` | `http://localhost:3000` | `https://www.polytext.site` |
| `NEXT_PUBLIC_API_BASE` | `http://localhost:8000` | `https://api.polytext.site` |
| `REDIS_URL` | `redis://localhost:6379` | Railway Redis URL |

**NO FALLBACKS TO LOCALHOST IN CODE**

If production is missing a required variable, it will **fail immediately** with a clear error instead of silently falling back to localhost.

---

## Quick Start

### First Time Setup

**API:**
```bash
cd apps/api
cp .env.example .env.local
# Edit .env.local - add your real keys
```

**Frontend:**
```bash
cd apps/web
echo "NEXT_PUBLIC_API_BASE=http://localhost:8000" > .env.local
```

### Running Locally

**Terminal 1 - Redis:**
```bash
redis-server
```

**Terminal 2 - API:**
```bash
cd apps/api
uvicorn app.main:app --reload
```

**Terminal 3 - Worker:**
```bash
cd apps/api
source .env.local.worker
PYTHONPATH=/Users/.../BookTranslator poetry run rq worker translate
```

**Terminal 4 - Frontend:**
```bash
cd apps/web
npm run dev
```

---

## What's in .gitignore

These files are **never committed** to Git:
```
.env
.env.local
.env.*.local
apps/*/.env
apps/*/.env.local
```

These files **are committed** to Git:
```
.env.example
apps/*/.env.example
```

---

## Summary

✅ **DO:**
- Use `.env.local` for local development
- Set variables in Railway/Vercel dashboards for production
- Commit `.env.example` templates

❌ **DON'T:**
- Commit `.env` or `.env.local` files with real keys
- Use localhost fallbacks in code
- Have multiple redundant env files
