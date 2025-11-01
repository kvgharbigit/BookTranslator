# 📚 EPUB Translator - Professional Translation Service

> **Production-Ready** translation service with smart payment routing and ultra-fast processing

## 🚀 Quick Start

```bash
git clone <your-repo>
cd BookTranslator
./scripts/start-backend.sh   # Terminal 1
./scripts/start-worker.sh    # Terminal 2  
./scripts/start-frontend.sh  # Terminal 3
```

Visit **http://localhost:3000** and start translating! 

👉 **Full setup guide:** [docs/quick-start.md](./docs/quick-start.md)

## ✨ Key Features

- **🌐 Enhanced multi-format output:** EPUB + high-quality PDF (Calibre) + TXT with full image preservation
- **💰 Smart payments:** PayPal (<$8) + Stripe (≥$8) auto-routing  
- **⚡ Ultra-fast:** Gemini Tier 1 (4K RPM) + Groq fallback
- **📱 Mobile-first:** Responsive UI with real-time progress
- **🔒 Secure:** Rate limiting, validation, auto-cleanup
- **💸 Profitable:** 83-99% margins with $0.50 minimum pricing

## Architecture
- **Frontend:** Next.js on Vercel (mobile-responsive)
- **Backend:** FastAPI + RQ worker (single process) on Railway  
- **Storage:** Cloudflare R2 (7-day auto-delete)
- **Payments:** PayPal Micropayments + Stripe (auto-routed for best rates)
- **Database:** SQLite → Postgres later
- **AI:** Gemini 2.5 Flash-Lite (Tier 1: 3.2K safe RPM) + Groq Llama (Developer: 800 safe RPM) fallback

## Economics (Updated with Tier 1 Performance)
- **Fixed:** ~$10/month (Railway + R2)
- **Variable Provider Costs (per 100K chars):**
  - Llama 3.1 8B Instant: $0.007400 (78.2% cheaper)
  - Gemini 2.5 Flash-Lite: $0.034000
- **Processing Speed (Tier 1):**
  - **3,200 safe RPM** (80% of 4,000 limit to avoid errors)
  - **3.2M safe TPM** (80% of 4M limit to avoid errors)
  - **~200x faster translation** processing vs Free tier
- **Profit Margins at $0.50 minimum:**
  - Llama: 98.5% margin  
  - Gemini: 93.2% margin
- **Payment Fees (auto-optimized):**
  - PayPal micropayments: 5% + $0.05 (better for < $8)
  - Stripe standard: 2.9% + $0.30 (better for ≥ $8)

## User Flow
1. Upload EPUB → instant price estimate  
2. Pay via PayPal/Stripe (auto-routed for best rates) → email notification  
3. **Fast translation processing** (Tier 1: 45x faster) → **3 formats ready**: EPUB + PDF + TXT
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
- [ ] Gemini adapter: `providers/gemini.py` (Tier 1: 10K token batches, 0.02s delays)
- [ ] Groq adapter: `providers/groq.py` (800 token batches, 0.1s delays)
- [ ] Fallback logic: Gemini fails 3x or 429 >60s → switch to Groq
- [ ] Force Gemini for low-resource languages: km,lo,eu,gl,ga,tg,uz,hy,ka

### Phase 4: EPUB Pipeline
- [ ] EPUB I/O: `pipeline/epub_io.py` (reject >5000 files, 10x compression)
- [ ] HTML segmentation: `pipeline/html_segment.py` (UTF-8, strip scripts)
- [ ] Placeholder protection: `{TAG_n}/{NUM_n}/{URL_n}` exact count parity
- [ ] No-translate blocks: `<pre>`, `<code>`, `<table>` content protected  
- [ ] Translation orchestration: fail job if validation fails 2x
- [ ] **Enhanced multi-format output**: EPUB + high-quality PDF (Calibre primary, WeasyPrint/ReportLab fallback) + TXT with full image preservation
- [ ] Worker function: `pipeline/worker.py` with progress steps

### Phase 5: Job Processing
- [ ] Redis + RQ setup
- [ ] Job status tracking with progress steps
- [ ] Email notifications via Resend/SendGrid
- [ ] Error handling + retries

### Phase 6: Payment Integration
- [ ] Dual payment providers: PayPal micropayments + Stripe
- [ ] Smart routing: PayPal for < $8, Stripe for ≥ $8
- [ ] Endpoints: `/estimate`, `/create-checkout`, `/webhook/stripe`, `/api/paypal/*`
- [ ] Webhook idempotency: reject duplicate payment IDs
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
MAX_BATCH_TOKENS=10000
MAX_JOB_TOKENS=1000000
RETRY_LIMIT=3

# Payments
STRIPE_SECRET_KEY=...
STRIPE_WEBHOOK_SECRET=...
MIN_PRICE_CENTS=50
PRICE_CENTS_PER_MILLION_TOKENS=300

# PayPal Micropayments
PAYPAL_CLIENT_ID=...
PAYPAL_CLIENT_SECRET=...
PAYPAL_ENVIRONMENT=sandbox  # or 'live'
PAYPAL_WEBHOOK_ID=...
MICROPAYMENTS_THRESHOLD_CENTS=800

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

## 📖 Documentation

| Guide | Description |
|-------|-------------|
| [🚀 Quick Start](./docs/quick-start.md) | Get running in 15 minutes |
| [🚢 Deployment](./docs/deployment.md) | Production setup guide |  
| [📊 API Reference](./docs/api-reference.md) | Complete API documentation |
| [🗺️ Roadmap](./docs/roadmap.md) | Future features & dual readers |
| [🔧 Configuration](./docs/configuration.md) | Environment setup |

## 💰 Business Model

**Revenue:** $0.50 minimum per translation  
**Costs:** ~$0.001-0.085 per translation (provider costs)  
**Margins:** 83-99% profit with smart payment routing

## 🛠️ Tech Stack

**Backend:** FastAPI + Redis/RQ + SQLite  
**Frontend:** Next.js + Tailwind CSS  
**AI:** Gemini 2.5 Flash-Lite + Groq Llama 3.1 8B  
**Payments:** Stripe + PayPal Micropayments  
**Storage:** Cloudflare R2  
**Deployment:** Railway + Vercel

## 🧪 Testing

```bash
# Run comprehensive provider comparison
cd tests
python test_dual_provider_comparison.py

# Test with different book sizes (with Tier 1 Gemini)
# - Short stories (10K words): ~30-60 seconds
# - Novels (80K words): ~3-5 minutes  
# - Epic books (200K+ words): ~8-12 minutes
```

## 📊 Performance Metrics

- **Processing Speed:** 3.2K safe RPM (Gemini) + 800 safe RPM (Groq)
- **Quality:** High accuracy with Gemini 2.5 Flash-Lite  
- **Reliability:** Automatic fallback when providers fail
- **Cost Efficiency:** 83-99% profit margins (depending on file size)
- **Enhanced Image Support:** Professional PDF generation with SVG, PNG, JPG preservation using Calibre (primary) + intelligent fallbacks

### ⏱️ Translation Time & Cost Examples

## 💰 Simple 5-Tier Pricing

| **Tier** | **Word Count** | **Price** | **Examples** |
|-----------|----------------|-----------|--------------|
| 📖 **Short Novel** | 0-56K words | **$0.50** | Novellas, short fiction |
| 📚 **Novel** | 56K-112K words | **$0.75** | Standard novels, memoirs |
| 📕 **Long Novel** | 112K-225K words | **$1.00** | Most bestsellers, non-fiction |
| 🏛️ **Epic Novel** | 225K-375K words | **$1.25** | Fantasy series, biographies |
| 📚📚 **Epic Series** | 375K-750K words | **$1.50** | Multi-book length, reference |
| ⚠️ **Over 750K words** | **Rejected** | Files over 750K words are too large for processing |

### ⏱️ Translation Time & Profit Examples

| Book Type | Example Title | Words | **Tier & Price** | **Gemini 2.5 Flash-Lite** | **Groq Llama 3.1 8B** |
|-----------|---------------|-------|------------------|---------------------------|----------------------|
| **Classic** | *The Great Gatsby* | 47K words | Short Novel • $0.50 | ⏱️ 2-3 min<br/>💸 Cost: $0.021<br/>📈 Profit: $0.40 (81% margin) | ⏱️ 4-5 min<br/>💸 Cost: $0.005<br/>📈 Profit: $0.42 (84% margin) |
| **Modern Classic** | *The Catcher in the Rye* | 80K words | Novel • $0.75 | ⏱️ 3-5 min<br/>💸 Cost: $0.036<br/>📈 Profit: $0.63 (84% margin) | ⏱️ 6-8 min<br/>💸 Cost: $0.008<br/>📈 Profit: $0.65 (87% margin) |
| **Bestseller** | *Harry Potter: Goblet of Fire* | 190K words | Long Novel • $1.00 | ⏱️ 8-12 min<br/>💸 Cost: $0.085<br/>📈 Profit: $0.82 (82% margin) | ⏱️ 15-25 min<br/>💸 Cost: $0.018<br/>📈 Profit: $0.88 (88% margin) |
| **Fantasy Epic** | *A Game of Thrones* | 298K words | Epic Novel • $1.25 | ⏱️ 12-18 min<br/>💸 Cost: $0.134<br/>📈 Profit: $1.00 (80% margin) | ⏱️ 25-35 min<br/>💸 Cost: $0.029<br/>📈 Profit: $1.11 (89% margin) |
| **Literary Epic** | *War and Peace* | 550K words | Epic Series • $1.50 | ⏱️ 25-35 min<br/>💸 Cost: $0.248<br/>📈 Profit: $1.13 (75% margin) | ⏱️ 45-60 min<br/>💸 Cost: $0.054<br/>📈 Profit: $1.32 (88% margin) |

*Customer-friendly 5-tier pricing: $0.50 minimum, $1.50 maximum, 750K word cap, with excellent 75-89% profit margins*

**💡 Smart Routing:** All tiers use PayPal (better fees) - Stripe only for enterprise  
**🔄 Auto-Fallback:** Gemini primary → Groq if rate limits hit or failures occur  
**📊 Value Proposition:** Translate *Game of Thrones* in 15 minutes for $1.25 vs human translator $30,000+ and 3+ months

## 🤝 Contributing

1. **Fork** the repository
2. **Create** feature branch (`git checkout -b feature/dual-readers`)
3. **Test** your changes thoroughly
4. **Submit** pull request with clear description

See [docs/contributing.md](./docs/contributing.md) for detailed guidelines.

---

**Ready to launch your translation service?** Start with the [Quick Start Guide](./docs/quick-start.md) 🚀