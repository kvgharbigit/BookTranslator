# 📚 BookTranslator - AI-Powered EPUB Translation

> Transform EPUBs into any language with AI - **Live in Production**

[![Status](https://img.shields.io/badge/Status-Production-brightgreen)](https://polytext.site) [![License](https://img.shields.io/badge/License-MIT-blue)](.)

**🌐 Live at:** [https://polytext.site](https://polytext.site)
**🔌 API:** [https://api.polytext.site](https://api.polytext.site)

---

## ✨ What This Does

Translate any EPUB book into 50+ languages in under 5 minutes:

- **📚 Upload EPUB** → Get instant price estimate ($0.50-$3.00)
- **🎯 Free Preview** → See first 1000 words translated instantly
- **💳 Pay via PayPal** → Micropayments optimized for small amounts
- **⚡ AI Translation** → Gemini 2.5 Flash + Groq fallback
- **📱 Real-time Progress** → Smooth 0-100% progress tracking
- **📦 Multi-format Output** → Download EPUB + PDF + TXT
- **☁️ Cloudflare R2** → Zero egress fees, 5-day retention
- **📧 Email Delivery** → Automated notifications with download links

---

## 🚀 Quick Start

**Test locally with production infrastructure:**

```bash
# Terminal 1: Redis
redis-server

# Terminal 2: Backend
cd apps/api
poetry run uvicorn app.main:app --reload --port 8000

# Terminal 3: Worker (macOS)
cd apps/api
PYTHONPATH=/Users/kayvangharbi/PycharmProjects/BookTranslator \
OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES \
poetry run rq worker translate --url redis://localhost:6379

# Terminal 4: Frontend
cd apps/web
npm run dev
```

Visit **http://localhost:3000** → Upload EPUB → Click **"Skip Payment (Test)"**

---

## 💰 Pricing & Economics

| Category | Word Range | Price | AI Cost | Profit | Margin |
|----------|-----------|-------|---------|--------|--------|
| Short Book | 0-40K | $0.99 | $0.03 | $0.86 | 87% |
| Standard Novel | 40-120K | $1.49 | $0.08 | $1.29 | 87% |
| Long Novel | 120-200K | $2.19 | $0.14 | $1.89 | 86% |
| Epic Novel | 200-350K | $2.99 | $0.24 | $2.55 | 85% |

**Why This Works:**
- **5× cheaper** than competitors (O.Translator charges ~$5 for 100K words)
- **85-90% profit margins** with AI efficiency
- **PayPal Micropayments**: 5% + $0.05 (optimized for <$8 transactions)
- **Production-ready**: 100K words in under 5 minutes

---

## 🏗️ Architecture

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│  Frontend   │───▶│   Backend    │───▶│   Worker    │
│  (Next.js)  │    │  (FastAPI)   │    │ (RQ+Redis)  │
│  Vercel     │    │  Railway     │    │  Railway    │
└─────────────┘    └──────────────┘    └─────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   PayPal    │    │  PostgreSQL  │    │ Cloudflare  │
│  Payments   │    │   Database   │    │  R2 Storage │
└─────────────┘    └──────────────┘    └─────────────┘
```

---

## 🛠️ Tech Stack

**Frontend:** Next.js 14, Tailwind CSS, TypeScript
**Backend:** FastAPI, SQLAlchemy, PostgreSQL
**Queue:** Redis + RQ for async jobs
**AI:** Gemini 2.5 Flash + Groq Llama 3.1 fallback
**Storage:** Cloudflare R2 (5-day retention)
**Payments:** PayPal Micropayments
**Email:** Resend
**Hosting:** Railway (backend) + Vercel (frontend)

---

## 📋 Prerequisites

**For Local Development:**
- Python 3.12+ with Poetry
- Node.js 18+ with npm
- Redis (`brew install redis` on macOS)
- Git

**For Production Deployment:**
- Railway account (backend hosting)
- Vercel account (frontend hosting)
- Cloudflare account (R2 storage)
- Gemini API key
- Groq API key (optional)
- PayPal Business account
- Resend account (email)
- Custom domain (optional)

---

## 📖 Documentation

### Getting Started
- **[Quick Setup](#quick-start)** - Run locally in 5 minutes
- **[DEPLOYMENT.md](./DEPLOYMENT.md)** - Complete deployment guide

### Setup Guides
- **[R2_SETUP_GUIDE.md](./R2_SETUP_GUIDE.md)** - Cloudflare R2 storage setup
- **[PAYPAL_SETUP_GUIDE.md](./PAYPAL_SETUP_GUIDE.md)** - PayPal business account
- **[ENVIRONMENT_VARIABLES.md](./ENVIRONMENT_VARIABLES.md)** - All env vars reference

### Technical Docs
- **[POST_TRANSLATION_WORKFLOW.md](./POST_TRANSLATION_WORKFLOW.md)** - File generation & email flow
- **[PREVIEW_FEATURE.md](./PREVIEW_FEATURE.md)** - Preview translation feature
- **[TROUBLESHOOTING.md](./TROUBLESHOOTING.md)** - Common issues & fixes

### Navigation
- **[DOCUMENTATION_INDEX.md](./DOCUMENTATION_INDEX.md)** - Complete docs overview

---

## 🔧 Local Development Setup

### 1. Install Dependencies

```bash
# Backend
cd apps/api
poetry install

# Frontend
cd apps/web
npm install
echo "NEXT_PUBLIC_API_BASE=http://localhost:8000" > .env.local
```

### 2. Configure Environment

The `.env.local` file in `apps/api/` should include:
```bash
# AI Providers
GEMINI_API_KEY=your_gemini_key
GROQ_API_KEY=your_groq_key

# Database
DATABASE_URL=postgresql://user:pass@host/db  # Or use Railway PostgreSQL

# Queue
REDIS_URL=redis://localhost:6379

# R2 (optional for local, required for production)
R2_ACCOUNT_ID=your_account_id
R2_ACCESS_KEY_ID=your_access_key
R2_SECRET_ACCESS_KEY=your_secret_key
R2_BUCKET=epub-translator-production

# PayPal (use sandbox for testing)
PAYPAL_CLIENT_ID=sandbox_client_id
PAYPAL_CLIENT_SECRET=sandbox_secret
PAYPAL_ENVIRONMENT=sandbox

# Email (optional for local)
RESEND_API_KEY=your_resend_key
EMAIL_FROM=test@yourdomain.com
```

### 3. Test the System

1. Visit http://localhost:3000
2. Upload an EPUB file
3. Select target language
4. Click **"Skip Payment (Test)"** button
5. Watch translation progress
6. Download EPUB + PDF + TXT

---

## 🚀 Production Deployment

See **[DEPLOYMENT.md](./DEPLOYMENT.md)** for complete step-by-step guide.

**Quick Summary:**
1. Set up Cloudflare R2 storage (30 min)
2. Deploy backend to Railway (45 min)
3. Deploy frontend to Vercel (15 min)
4. Configure custom domain (30 min)
5. Set up PayPal payments (1-3 days)
6. Configure email notifications (15 min)

**Total Time:** 2-4 hours + PayPal approval time

---

## 💼 Business Model

### Revenue Streams
- **Per-translation fees**: $0.50-$3.00 per book
- **Target volume**: 100-1000+ translations/month
- **Pricing tiers**: Based on book length (word count)

### Cost Structure (1000 translations/month)
```
Monthly Costs:
- Railway Pro:      $20.00
- Cloudflare R2:     $4.50  (5-day retention)
- Vercel:            $0.00  (free tier)
- Gemini AI:       ~$34.00  (translation costs)
- Resend:            $0.00  (free tier: 3000/month)
- PayPal fees:     ~$2.00   (per-transaction)
Total:             ~$60.50/month

Revenue (@$1.50 avg): $1,500/month
Net Profit:           $1,440/month (96% margin)
```

### Market Position
- **Up to 5× cheaper** than competitors
- **Professional quality** in minutes, not hours
- **No accounts required** - pay-per-book simplicity
- **Format preservation** - maintains EPUB layout and images

---

## 📊 Performance

**Translation Speed:**
- Short novel (50K words): ~2-3 minutes
- Standard novel (80K words): ~3-5 minutes
- Long novel (150K words): ~5-8 minutes
- Epic novel (300K words): ~8-15 minutes

**Quality & Reliability:**
- Success rate: >95%
- Automatic AI fallback (Gemini → Groq)
- Format preservation with images
- Real-time progress tracking

---

## 🔒 Security

- Rate limiting: 60 requests/hour per IP
- File validation: EPUB-only, 50MB limit
- Input sanitization: HTML cleaning
- Payment security: PayPal integration
- Data retention: Auto-delete after 5 days
- CORS protection: Strict origin policies

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/new-feature`)
3. Make changes and test thoroughly
4. Submit pull request with description

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details

---

## 🆘 Support

- **Documentation**: [DOCUMENTATION_INDEX.md](./DOCUMENTATION_INDEX.md)
- **Deployment**: [DEPLOYMENT.md](./DEPLOYMENT.md)
- **Troubleshooting**: [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
- **Issues**: Use GitHub Issues

---

**Ready to launch?**
🚀 **[Start Deployment →](./DEPLOYMENT.md)**

**Current Status:** ✅ Production Live at [polytext.site](https://polytext.site)
