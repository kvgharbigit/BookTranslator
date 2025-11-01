# 🚀 Quick Start Guide

Get your EPUB Translator running in 15 minutes!

## ✅ Prerequisites

- **Python 3.11+** with Poetry installed
- **Node.js 18+** with npm
- **Redis** server running
- **Calibre** and **WeasyPrint dependencies** for enhanced PDF generation
- **API Keys** (see [Configuration Guide](./configuration.md) for details)

### System Dependencies

#### macOS
```bash
# Install PDF generation tools
brew install calibre pango gtk+3 gdk-pixbuf libffi

# Set environment for WeasyPrint
export DYLD_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_LIBRARY_PATH"
```

#### Linux/Ubuntu
```bash
sudo apt-get update && sudo apt-get install -y \
    calibre \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info
```

## 🎯 Local Development (3 Steps)

### Step 1: Clone and Install
```bash
git clone <your-repo-url>
cd BookTranslator

# Install Python dependencies
cd apps/api
poetry install

# Install Node.js dependencies  
cd ../web
npm install
```

### Step 2: Configure Environment
```bash
# Copy environment template
cp env.example .env

# Edit .env with your API keys
# See configuration.md for all required variables
```

### Step 3: Start Services
```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start Backend
cd apps/api
poetry run uvicorn app.main:app --reload

# Terminal 3: Start Worker
cd apps/api
poetry run rq worker translate --url redis://localhost:6379

# Terminal 4: Start Frontend
cd apps/web
npm run dev
```

## 🌐 Test Your Setup

1. **Open browser:** http://localhost:3000
2. **Test API:** http://localhost:8000/health
3. **Upload test file:** Use any small EPUB from Project Gutenberg
4. **Check payment routing:** See which provider is selected based on price

## 🧪 Run Tests

```bash
# Run provider comparison test
cd tests
python test_dual_provider_comparison.py

# Test individual components
cd apps/api
poetry run pytest tests/
```

## 📱 Production Deployment

Quick deploy to Railway + Vercel:

```bash
# 1. Push to GitHub
git add . && git commit -m "Ready for production"
git push origin main

# 2. Deploy backend on Railway
# - Connect GitHub repo
# - Point to apps/api directory
# - Add Redis add-on
# - Set environment variables

# 3. Deploy frontend on Vercel
# - Connect GitHub repo  
# - Point to apps/web directory
# - Set NEXT_PUBLIC_API_BASE to your Railway URL
```

## 🔧 Key Features to Test

### Translation Pipeline
- Upload EPUB → See token estimation
- Multi-format output (EPUB + PDF + TXT)
- Image preservation in all formats
- Provider fallback (Gemini → Groq)

### Payment System  
- Smart routing: PayPal for <$8, Stripe for ≥$8
- Test with Stripe card: `4242 4242 4242 4242`
- Email notifications via Resend

### Performance
- **Gemini Tier 1:** 4K RPM, 4M TPM (ultra-fast)
- **Groq Developer:** 30 RPM, 600K TPM (reliable fallback)
- **Processing Speed:** 2-5 minutes for average book

## 🐛 Troubleshooting

### Common Issues

**Redis connection error:**
```bash
# Install and start Redis
brew install redis
brew services start redis
```

**Poetry not found:**
```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -
```

**WeasyPrint PDF generation fails:**
```bash
# macOS: Install system dependencies
brew install cairo pango gdk-pixbuf libffi
```

**API keys not working:**
- Check .env file is in project root
- Verify API keys are valid and have correct permissions
- Restart all services after changing .env

### Health Checks

- **Backend health:** `curl http://localhost:8000/health`
- **Redis status:** `redis-cli ping` (should return "PONG")
- **Queue status:** Check RQ worker terminal for activity
- **Frontend status:** Should show upload form at localhost:3000

## 📊 Expected Performance

### Cost per Translation (5-Tier Word-Based Pricing)
- **Short Novel (47K words):** $0.021 provider cost → $0.50 user price = 81% margin
- **Long Novel (190K words):** $0.085 provider cost → $1.00 user price = 82% margin
- **Epic Series (550K words):** $0.248 provider cost → $1.50 user price = 75% margin

### Speed Benchmarks
- **Short story (10K words):** 1-2 minutes
- **Novel (80K words):** 8-15 minutes  
- **Epic (200K words):** 20-30 minutes

### Quality Metrics
- **Gemini 2.5 Flash-Lite:** High quality, fast processing
- **Groq Llama 3.1 8B:** Good quality, reliable fallback
- **Image preservation:** 100% success rate with SVG and standard formats

## 🎉 Next Steps

- ✅ **Working locally?** → Try [Production Deployment](./deployment.md)
- 📚 **Need API docs?** → See [API Reference](./api-reference.md)  
- 🚀 **Planning features?** → Check the [Roadmap](./roadmap.md)
- 🔧 **Advanced setup?** → Review [Configuration Guide](./configuration.md)

---

*Having issues? Check the troubleshooting section above or review the complete [Installation Guide](./installation.md).*