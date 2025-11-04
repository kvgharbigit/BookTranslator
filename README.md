# 📚 BookTranslator - AI-Powered EPUB Translation Service

> Transform EPUBs into any language with AI - **🎉 LIVE IN PRODUCTION**

[![Status](https://img.shields.io/badge/Status-Production%20Live-brightgreen)](https://polytext.site) [![R2](https://img.shields.io/badge/Storage-Cloudflare%20R2-orange)](.) [![License](https://img.shields.io/badge/License-MIT-blue)](.)

**🌐 Live at:** [https://polytext.site](https://polytext.site)
**🔌 API:** [https://api.polytext.site](https://api.polytext.site)

## 🚀 Quick Start

**Test locally with production infrastructure:**

```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Backend (uses Railway PostgreSQL + Cloudflare R2)
cd apps/api
poetry run python -m uvicorn app.main:app --reload --port 8000

# Terminal 3: Worker (macOS fix included)
cd apps/api
PYTHONPATH=/Users/kayvangharbi/PycharmProjects/BookTranslator OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES poetry run rq worker translate --url redis://localhost:6379

# Terminal 4: Frontend
cd apps/web
npm run dev
```

Visit **http://localhost:3000** → Upload EPUB → Click **"Skip Payment (Test)"** → Watch real-time progress!

**Current Setup:**
- ✅ **Cloudflare R2** - Production file storage (5-day retention)
- ✅ **Railway PostgreSQL** - Production database
- ✅ **Local Redis** - Job queue
- ✅ **Groq Llama 3.1** - AI translation ($0.074/1M tokens)
- ✅ **Batch Progress Tracking** - Smooth 0-100% progress bar

👉 **Current Status:** See [CURRENT_STATUS.md](./CURRENT_STATUS.md) for complete implementation details
👉 **R2 Setup:** See [R2_SETUP_GUIDE.md](./R2_SETUP_GUIDE.md) for Cloudflare R2 configuration
👉 **Deployment:** See [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) for production deployment

## ✨ What This Does

Transform any EPUB book into any language in **under 5 minutes** with professional quality:

- **📚 Upload EPUB** → Get instant price estimate ($0.50-$1.50)
- **🎯 Free Preview** → See first 1000 words translated instantly (NEW!)
- **💳 Pay via PayPal** → ⚠️ *Configured but needs live credentials*
- **⚡ AI Translation** → Groq Llama 3.1 (testing) + Gemini 2.5 Flash (production ready)
- **📱 Real-time Progress** → Smooth batch-level progress tracking (0-100%)
- **📦 Multi-format Output** → Download EPUB + PDF + TXT (UTF-8 verified)
- **☁️ Cloudflare R2 Storage** → Zero egress fees, 5-day retention
- **📧 Email Delivery** → ✅ *Fully working with Resend*

## 🎯 Key Features

### **💰 Smart Economics**
- **Fixed Pricing**: $0.50 (short) to $1.50 (epic) - transparent tiers
- **High Margins**: 85-95% profit with AI efficiency
- **PayPal Integration**: Optimized for micropayments (<$8)
- **Auto-scaling**: From prototype to thousands of users

### **🔧 Technical Excellence**
- **Multi-format Output**: Enhanced PDF generation with image preservation
- **Real-time Progress**: WebSocket-style polling with status updates
- **Dual AI Providers**: Gemini primary + Groq fallback for reliability
- **Production Architecture**: FastAPI + Next.js + Redis queue system
- **Security First**: Rate limiting, input validation, secure file handling

### **📱 User Experience**
- **Mobile-first**: Responsive design for all devices
- **No Account Required**: Upload, pay, download - that's it
- **Progress Tracking**: See exactly what's happening in real-time
- **Professional Quality**: Preserves formatting, images, and styling

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
│   PayPal    │    │  PostgreSQL  │    │ AI Provider │
│  Payments   │    │   Database   │    │ Gemini/Groq │
└─────────────┘    └──────────────┘    └─────────────┘
```

## 💰 Pricing Model

| **Category** | **Word Range** | **Price** | **Est. AI Cost** | **PayPal Fee** | **Net Profit ≈** | **Margin ≈** |
|--------------|----------------|-----------|------------------|----------------|------------------|--------------|
| 🧾 **Short Book** | 0-40K words | **$0.99** | ~$0.03-$0.05 | ~$0.10 | ~$0.84-$0.86 | ~85%-~87% |
| 📘 **Standard Novel** | 40K-120K words | **$1.49** | ~$0.05-$0.13 | ~$0.12 | ~$1.24-$1.32 | ~83%-~89% |
| 📕 **Long Novel** | 120K-200K words | **$2.19** | ~$0.13-$0.20 | ~$0.16 | ~$1.83-$1.90 | ~84%-~87% |
| 🏛️ **Epic Novel** | 200K-350K words | **$2.99** | ~$0.20-$0.32 | ~$0.20 | ~$2.47-$2.59 | ~83%-~87% |
| 📚 **Grand Epic** | 350K-750K words | **$3.99** | ~$0.33-$0.56 | ~$0.25 | ~$3.18-$3.41 | ~80%-~85% |

**Cost Components**:
- **AI Translation** (conservative Gemini-only estimates):
  - **Gemini 2.5 Flash-Lite** (Primary): $0.10/1M input, $0.40/1M output tokens
    - Blended rate: **$0.34/1M tokens** (assumes 20% input, 80% output)
    - Source: [Google AI Pricing](https://ai.google.dev/pricing) (verified Jan 2025)
  - **Groq Llama 3.1 8B Instant** (Fallback): $0.05/1M input, $0.08/1M output tokens
    - Blended rate: **$0.074/1M tokens** (78% cheaper than Gemini)
    - Source: [Groq Pricing](https://groq.com/) (verified Jan 2025)
  - Translation cost range: $0.03-$0.56 per book (using Gemini pricing)
- **PayPal fees**: $0.10-$0.25 per transaction (5% + $0.05 fixed fee)

**Processing Time**: 2-15 minutes depending on book size  
**Average Profit Margin**: 80-88% across all tiers (Groq reduces costs by ~78% when available)  
**Supported Languages**: 50+ languages including Spanish, French, German, Chinese, Japanese, Arabic

### 🛡️ **Rate Limit Safety**
- **95% Safety Barrier**: Operates at 95% of AI provider limits for reliability
- **Automatic Retry**: Exponential backoff handles temporary rate limits gracefully  
- **No Translation Failures**: Rate limits cause delays, not failures
- **Bulletproof Processing**: All requests are idempotent with progress tracking

### 🎯 Competitive Advantages

- **Up to 5× cheaper** than comparable AI EPUB translators (O.Translator charges ~$5 for 100K words)
- **Professional EPUB translation in minutes** — for less than $2 (40-120K word tier at $1.49)
- **Preserves formatting and images** — unlike free document translators that break EPUB layout
- **Fastest hosted EPUB translator** — 100K words in under 5 minutes with production-grade quality
- **No accounts, no subscriptions** — just pay-per-book simplicity with instant access

### 📚 Book Category Examples

**🧾 Short Book / Novella (0–40K words)**
Compact, fast reads that tell a full story in under 100 pages — like *The Metamorphosis* by Franz Kafka (22K words), *Animal Farm* by George Orwell (30K), or *Of Mice and Men* by John Steinbeck (29K).

**📘 Standard Novel (40K–120K words)**
Covers most mainstream single-volume novels: *The Great Gatsby* (47K), *Fahrenheit 451* (46K), and *Jane Eyre* (96K). This is your main "sweet spot" tier with the best value.

**📕 Long Novel (120K–200K words)**
Full-length works with complex plots and multiple sub-stories — such as *Pride and Prejudice* (122K), *Dune* (175K), and *Harry Potter and the Philosopher's Stone* (77K on lower edge).

**🏛️ Epic Novel (200K–350K words)**
Massive single-book adventures like *The Stand* (240K), *A Game of Thrones* (298K), or *Les Misérables* (195K, abridged). These books test AI throughput but still process in minutes.

**📚 Grand Epic (350K–750K words)**
Truly monumental single volumes such as *War and Peace* (587K), *Atlas Shrugged* (645K), or *The Count of Monte Cristo* (464K). Ideal for the "translate an entire classic" use case.

## 🛠️ Tech Stack

- **Frontend**: Next.js 14, Tailwind CSS, TypeScript
- **Backend**: FastAPI, SQLAlchemy, Pydantic
- **Queue**: Redis + RQ for async job processing
- **AI**: Google Gemini 2.5 Flash + Groq Llama 3.1 8B
- **Payments**: PayPal micropayments (optimized for small amounts)
- **Storage**: Local (development) → Cloudflare R2 (production)
- **Database**: SQLite (development) → PostgreSQL (production)
- **Deployment**: Railway (backend) + Vercel (frontend)

## 📊 Performance Metrics

### **Translation Speed**
- **Short Novel** (50K words): ~2-3 minutes
- **Standard Novel** (80K words): ~3-5 minutes  
- **Long Novel** (150K words): ~5-8 minutes
- **Epic Novel** (300K words): ~8-15 minutes

### **Quality & Reliability**
- **Success Rate**: >95% completion rate
- **AI Fallback**: Automatic Groq backup if Gemini fails
- **Error Recovery**: Comprehensive retry logic and validation
- **Format Preservation**: Maintains original styling and images

## 🚀 Deployment Options

### **Option 1: MVP Deployment (Recommended)**
Get live in 8 hours with minimal setup:
- See [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)
- Cost: ~$25-45/month
- Features: Full functionality with room to scale

### **Option 2: Business Setup**
PayPal payments, domain, and business operations:
- See [BUSINESS_SETUP.md](./BUSINESS_SETUP.md)  
- Timeline: 2-4 hours
- Revenue-ready with live payments

## 📁 Project Structure

```
BookTranslator/
├── apps/
│   ├── api/                 # FastAPI backend
│   │   ├── app/
│   │   │   ├── pipeline/    # Translation pipeline
│   │   │   ├── providers/   # AI provider integrations
│   │   │   ├── routes/      # API endpoints
│   │   │   └── main.py      # FastAPI application
│   │   └── pyproject.toml   # Python dependencies
│   └── web/                 # Next.js frontend
│       ├── src/
│       │   ├── app/         # Next.js app router
│       │   ├── components/  # React components
│       │   └── lib/         # Utility functions
│       └── package.json     # Node.js dependencies
├── scripts/                 # Development scripts
├── DEPLOYMENT_GUIDE.md      # Complete deployment guide
├── BUSINESS_SETUP.md        # PayPal, domain, business setup
├── TROUBLESHOOTING.md       # Technical problem solving
└── README.md               # This file
```

## 🧪 Local Development

### **Prerequisites**
- Python 3.12+ with Poetry
- Node.js 18+ with npm
- Redis (`brew install redis` on macOS)
- Git

### **Setup (One-time)**

1. **Install Dependencies**
```bash
# Backend
cd apps/api
poetry install

# Frontend
cd apps/web
npm install
echo "NEXT_PUBLIC_API_BASE=http://localhost:8000" > .env.local
```

2. **Configure Environment**

The `.env.local` file in `apps/api/` is already configured with:
- ✅ Railway PostgreSQL (public URL - works from your local machine)
- ✅ Local Redis (localhost:6379)
- ✅ AI API keys from Railway
- ✅ All necessary environment variables

No additional configuration needed!

### **Run Locally**

Open 4 terminals and run:

```bash
# Terminal 1: Redis
redis-server

# Terminal 2: Backend API
cd apps/api
poetry run python -m uvicorn app.main:app --reload --port 8000

# Terminal 3: Translation Worker (macOS fix for PDF generation)
cd apps/api
PYTHONPATH=/Users/kayvangharbi/PycharmProjects/BookTranslator OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES poetry run rq worker translate --url redis://localhost:6379

# Terminal 4: Frontend
cd apps/web
npm run dev
```

### **Test the System**
1. Visit http://localhost:3000
2. Upload an EPUB file
3. Select target language
4. Click **"Skip Payment (Test)"** button (yellow/orange button)
5. Watch translation progress in real-time
6. Download EPUB + PDF + TXT outputs

**Benefits of This Setup:**
- ✅ Test with Railway's production PostgreSQL
- ✅ See real job data from production
- ✅ Fast local Redis for queue
- ✅ Perfect for testing Skip Payment feature
- ✅ No need for Railway CLI or Docker

### **Fully Isolated Local Testing (Optional)**

If you want to test without any production dependencies:

1. Update `apps/api/.env.local`:
```bash
DATABASE_URL=sqlite:///./data/jobs.db  # Instead of Railway Postgres
REDIS_URL=redis://localhost:6379       # Same
```

2. Follow the same "Run Locally" steps above

This uses SQLite instead of PostgreSQL - perfect for fully offline testing.

## 📋 Environment Variables

### **Backend (.env)**
```bash
# AI Providers
GEMINI_API_KEY=your_gemini_key
GROQ_API_KEY=your_groq_key

# PayPal (sandbox for testing)
PAYPAL_CLIENT_ID=fake_paypal_client_id
PAYPAL_CLIENT_SECRET=fake_paypal_client_secret

# Email notifications
RESEND_API_KEY=fake_resend_key
EMAIL_FROM=test@yourdomain.com

# Database
DATABASE_URL=sqlite:///./data/jobs.db

# Queue
REDIS_URL=redis://localhost:6379
```

### **Frontend (.env.local)**
```bash
NEXT_PUBLIC_API_BASE=http://localhost:8000
```

## 🔒 Security Features

- **Rate Limiting**: 60 requests/hour per IP
- **File Validation**: EPUB-only uploads, size limits (50MB)
- **Input Sanitization**: HTML content cleaning and validation
- **Payment Security**: PayPal's secure payment processing
- **Data Protection**: Auto-delete files after 7 days
- **CORS Protection**: Strict cross-origin policies

## 🧪 Testing

```bash
# Test basic translation flow
cd apps/api
poetry run python -m pytest tests/

# Test with sample files
cd sample_books/
# Upload pg236_first20pages.epub via web interface

# Monitor logs
tail -f apps/api/logs/*.log
```

## 📈 Business Model

### **Revenue Streams**
- **Per-translation fees**: $0.50-$1.50 per book
- **Potential volume**: 100-1000+ translations/month
- **Subscription option**: Future enterprise tiers

### **Cost Structure**
- **AI Provider costs**: $0.005-$0.025 per translation
- **Payment processing**: PayPal 5% + $0.05
- **Infrastructure**: $5-20/month (Railway + Vercel)
- **Total margins**: 85-95% profit

### **Market Validation**
- **Target audience**: Multilingual readers, students, researchers
- **Competitive advantage**: AI speed + professional quality + fair pricing
- **Market size**: Global translation market worth $56B+

## 🛣️ Roadmap

### **Phase 1: MVP Launch** (Complete ✅)
- [x] Core translation pipeline with Groq Llama + Gemini fallback
- [x] Railway backend deployment with PostgreSQL + Redis
- [x] Vercel frontend deployment with production URLs
- [x] Multi-format output (EPUB/PDF/TXT) with enhanced PDF generation
- [x] Real-time progress tracking with WebSocket-style polling
- [x] Production-ready architecture with Docker containerization
- [x] Payment integration (PayPal sandbox mode)
- [x] End-to-end testing and validation completed
- [x] Complete troubleshooting documentation

### **Phase 2: Business Launch** (Ready when needed)
- [ ] PayPal live integration (Australian business account setup required)
- [ ] Custom domain setup (epubtranslator.com)
- [ ] Resend email notifications
- [ ] Analytics and monitoring
- [ ] SEO optimization

### **Phase 3: Growth Features** (Future)
- [ ] Stripe integration for larger payments
- [ ] Bulk translation discounts
- [ ] API access for developers
- [ ] Mobile app
- [ ] Enterprise features

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/new-feature`)
3. Make changes and test thoroughly
4. Submit pull request with clear description

## 📄 License

MIT License - see [LICENSE](LICENSE) for details

## 🆘 Support

- **Deployment Help**: [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)
- **Business Setup**: [BUSINESS_SETUP.md](./BUSINESS_SETUP.md)
- **Technical Issues**: [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
- **Bug Reports**: Use GitHub Issues

---

**Ready to launch your translation service?** 

🚀 **Quick Deployment**: [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) - Live in 8 hours  
💼 **Business Ready**: [BUSINESS_SETUP.md](./BUSINESS_SETUP.md) - Revenue in 2-4 hours  

**Current Status**: ✅ **LIVE MVP** - Fully functional translation service deployed and tested

🌐 **Live URLs:**
- **Frontend**: https://web-39ez6nx0h-kayvan-gharbis-projects.vercel.app
- **Backend**: https://booktranslator-production.up.railway.app
- **Health Check**: https://booktranslator-production.up.railway.app/health