# EPUB Translator - Pay-Per-File Translation Service

## Overview
Minimal, cost-effective EPUB translator using Gemini 2.5 Flash-Lite (default) and Groq Llama-3.x (fallback).

**Business Model:** $0.30 per 100k characters, $1 minimum  
**No accounts required** - upload, pay, translate, download via email

## Architecture
- **Frontend:** Next.js on Vercel (mobile-responsive)
- **Backend:** FastAPI + RQ worker (single process) on Railway  
- **Storage:** Cloudflare R2 (7-day auto-delete)
- **Payments:** Stripe Checkout (one-time)
- **Database:** SQLite → Postgres later
- **AI:** Gemini Flash-Lite + Groq Llama fallback

## Economics
- **Fixed:** ~$10/month (Railway + R2)
- **Variable:** $0.05-0.20 per book (API costs)
- **Profit Margin:** 51-73% per translation

## User Flow
1. Upload EPUB → instant price estimate
2. Pay via Stripe → email notification  
3. Translation processed → **3 formats ready**: EPUB + PDF + TXT
4. Download links emailed → files auto-delete after 7 days

## Implementation Checklist

### Phase 1: Backend Foundation
- [ ] Project structure: `apps/{api,web}` + `env.example`
- [ ] FastAPI app: `main.py`, `config.py`, `logger.py`, `db.py`
- [ ] Models: Job table with SQLite
- [ ] Health endpoint: `GET /health`

### Phase 2: Storage & Pricing  
- [ ] R2 client: presigned upload/download URLs
- [ ] Pricing logic: server-side token estimation
- [ ] CORS configuration for R2 bucket

### Phase 3: Translation Providers
- [ ] Provider interface: `providers/base.py`
- [ ] Gemini adapter: `providers/gemini.py` (batch 6k tokens, retry 1s/2s/4s)
- [ ] Groq adapter: `providers/groq.py` (same batching/retry)
- [ ] Fallback logic: Gemini fails 3x or 429 >60s → switch to Groq
- [ ] Force Gemini for low-resource languages: km,lo,eu,gl,ga,tg,uz,hy,ka

### Phase 4: EPUB Pipeline
- [ ] EPUB I/O: `pipeline/epub_io.py` (reject >5000 files, 10x compression)
- [ ] HTML segmentation: `pipeline/html_segment.py` (UTF-8, strip scripts)
- [ ] Placeholder protection: `{TAG_n}/{NUM_n}/{URL_n}` exact count parity
- [ ] No-translate blocks: `<pre>`, `<code>`, `<table>` content protected  
- [ ] Translation orchestration: fail job if validation fails 2x
- [ ] **Multi-format output**: EPUB + PDF (WeasyPrint) + TXT (BeautifulSoup)
- [ ] Worker function: `pipeline/worker.py` with progress steps

### Phase 5: Job Processing
- [ ] Redis + RQ setup
- [ ] Job status tracking with progress steps
- [ ] Email notifications via Resend/SendGrid
- [ ] Error handling + retries

### Phase 6: Payment Integration
- [ ] Stripe client setup
- [ ] Endpoints: `/estimate`, `/create-checkout`, `/webhook/stripe`
- [ ] Webhook idempotency: reject duplicate `checkout.session.id`
- [ ] Checkout metadata: `{jobId, key, targetLang, provider, email}`
- [ ] Refund policy: manual within 24h for malformed EPUBs

### Phase 7: API Routes
- [ ] Upload: `POST /presign-upload` (60 req/IP/hour, burst 10)
- [ ] Status: `GET /job/{id}` (1 req/5s, max 10min after success)
- [ ] All endpoints: X-Request-Id logging, MIME validation
- [ ] Health: `queue_depth`, `jobs_inflight`, `err_rate_15m`

### Phase 8: Frontend (Next.js)
- [ ] File upload: drag-and-drop + fallback file input for mobile
- [ ] Legal checkbox: "I own the rights to translate this file"
- [ ] Price display + Stripe Checkout integration  
- [ ] Progress tracking with RTL toggle for ar/he/fa/ur languages
- [ ] Mobile: 44px touch targets, responsive layout

### Phase 9: Deployment
- [ ] Dockerfile + supervisord (API + worker)
- [ ] Railway backend deployment
- [ ] Vercel frontend deployment
- [ ] Environment variables configuration

### Phase 10: Security & Launch
- [ ] R2 CORS: PUT/GET from frontend domain, 300s MaxAge
- [ ] R2 multipart upload for files >50MB  
- [ ] Email setup: Resend + SPF/DKIM DNS records
- [ ] Security: reject non-EPUB MIME, sanitize XHTML
- [ ] Golden test suite (Project Gutenberg EPUBs)
- [ ] Legal copy: privacy (7-day deletion), refund policy

## Environment Setup

```bash
# Backend (Railway)
PORT=8000
DATABASE_URL=sqlite:///./data/jobs.db

# Translation Providers
PROVIDER=gemini  # 'gemini' | 'groq'
GEMINI_API_KEY=...
GROQ_API_KEY=...
MAX_BATCH_TOKENS=6000
MAX_JOB_TOKENS=1000000
RETRY_LIMIT=3

# Payments
STRIPE_SECRET_KEY=...
STRIPE_WEBHOOK_SECRET=...
MIN_PRICE_CENTS=100
PRICE_CENTS_PER_MILLION_TOKENS=300

# Storage  
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET=epub-translator
SIGNED_GET_TTL_SECONDS=172800  # 48h

# Queue
REDIS_URL=...

# Email
EMAIL_PROVIDER=resend
RESEND_API_KEY=...
EMAIL_FROM=noreply@yourdomain.com

# Security & Rate Limiting
RATE_LIMIT_BURST=10
RATE_LIMIT_PER_HOUR=60
MAX_FILE_MB=200
MAX_ZIP_ENTRIES=5000
MAX_COMPRESSION_RATIO=10

# Frontend (Vercel)  
NEXT_PUBLIC_API_BASE=https://api.domain.com
```

## Quick Start

```bash
# Project setup
mkdir -p apps/{web,api}/app/{routes,pipeline,providers}

# Backend
cd apps/api && poetry init && poetry add fastapi uvicorn

# Frontend  
cd apps/web && npx create-next-app@latest . --typescript --tailwind

# Development
uvicorn app.main:app --reload  # Backend
npm run dev                    # Frontend
rq worker translate           # Worker
```

## Multi-Format Output Implementation

### Cost Analysis: EPUB + PDF + TXT
| Format | Incremental Cost | File Size | Implementation |
|--------|------------------|-----------|----------------|
| EPUB | (existing) | ~2MB | Already built |
| PDF | <$0.01/job | ~1-3MB | WeasyPrint (3 lines) |
| TXT | ~$0.00/job | ~0.5MB | BeautifulSoup (2 lines) |

**Total additional cost: <$0.01 per translation**

### Worker Pipeline Addition
```python
# In pipeline/worker.py after EPUB rebuild
async def generate_additional_formats(job_id: str, translated_html: str):
    # 1. Generate PDF using WeasyPrint
    from weasyprint import HTML
    pdf_path = f"/tmp/{job_id}.pdf"
    HTML(string=translated_html).write_pdf(pdf_path)
    pdf_key = f"outputs/{job_id}.pdf"
    await upload_to_r2(pdf_path, pdf_key)
    
    # 2. Generate TXT using BeautifulSoup  
    from bs4 import BeautifulSoup
    txt_path = f"/tmp/{job_id}.txt"
    soup = BeautifulSoup(translated_html, "lxml")
    plain_text = soup.get_text(separator="\n", strip=True)
    
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(plain_text)
    
    txt_key = f"outputs/{job_id}.txt"
    await upload_to_r2(txt_path, txt_key)
    
    return pdf_key, txt_key
```

### Database Schema Updates
```python
# Add to models.py Job table
output_epub_key = Column(String, nullable=True)  # existing
output_pdf_key = Column(String, nullable=True)   # new
output_txt_key = Column(String, nullable=True)   # new
```

### API Response Updates
```python
# GET /job/{id} response when status="done"
{
    "status": "done",
    "downloadUrls": {
        "epub": "https://r2.../job123.epub?signed...",
        "pdf": "https://r2.../job123.pdf?signed...", 
        "txt": "https://r2.../job123.txt?signed..."
    },
    "expiresAt": "2024-01-15T12:00:00Z"  # 48h TTL
}
```

### Email Template
```html
<h2>Your translated book is ready!</h2>
<p>Choose your preferred format:</p>
<div style="margin: 20px 0;">
  <a href="{{epub_url}}" style="display: block; margin: 10px 0; padding: 12px; background: #e3f2fd;">
    📚 <strong>EPUB</strong> - For e-readers (Kindle, Apple Books)
  </a>
  <a href="{{pdf_url}}" style="display: block; margin: 10px 0; padding: 12px; background: #f3e5f5;">
    📄 <strong>PDF</strong> - For printing or mobile reading  
  </a>
  <a href="{{txt_url}}" style="display: block; margin: 10px 0; padding: 12px; background: #e8f5e8;">
    📝 <strong>TXT</strong> - Plain text for any device
  </a>
</div>
<p><small>Links expire in 48 hours. Files auto-delete after 7 days.</small></p>
```

## Key Features
✅ No accounts (email-only)  ✅ Live pricing  ✅ Mobile-responsive  
✅ **3 output formats** (EPUB + PDF + TXT)  ✅ Dual AI providers  
✅ Auto file cleanup  ✅ Single deployment  ✅ 7-day retention  
✅ Webhook-driven  ✅ $10/month fixed cost