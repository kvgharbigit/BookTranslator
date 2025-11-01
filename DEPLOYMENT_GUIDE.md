# 🚀 Polytext - Complete Deployment Guide

Deploy your translation service from zero to production in 8 hours to 2 weeks depending on your needs.

## 🎯 Choose Your Deployment Path

| **Option** | **Timeline** | **Cost** | **Best For** |
|------------|--------------|----------|--------------|
| [**MVP Deployment**](#mvp-deployment) | 8 hours | $5-15/month | Testing, validation, early users |
| [**Production Deployment**](#production-deployment) | 2 weeks | $50-100/month | Enterprise, high volume, full features |

---

## 🚀 MVP Deployment (8 Hours)

**Goal**: Get a working translation service live with real payments

### **Prerequisites (30 minutes)**
- GitHub account
- Railway account (free tier)
- Vercel account (free tier)
- Python 3.12+ and Node.js 18+ locally

### **Step 1: Repository Setup (15 minutes)**

```bash
# Clone your repository
git clone <your-repo-url>
cd BookTranslator

# Verify project structure
ls -la  # Should see apps/, docs/, scripts/, README.md
```

### **Step 2: Local Testing (45 minutes)**

```bash
# Backend setup
cd apps/api
poetry install
cp .env.example .env

# Add your AI provider keys to .env
GEMINI_API_KEY=your_actual_gemini_key
GROQ_API_KEY=your_actual_groq_key

# Frontend setup  
cd ../web
npm install
echo "NEXT_PUBLIC_API_BASE=http://localhost:8000" > .env.local

# Test locally (3 terminals)
./scripts/start-backend.sh   # Terminal 1
./scripts/start-worker.sh    # Terminal 2  
./scripts/start-frontend.sh  # Terminal 3

# Verify: Visit http://localhost:3000 and upload test EPUB
```

### **Step 3: Backend Deployment - Railway (2 hours)**

**3.1: Create Railway Project**
1. Go to [Railway](https://railway.app)
2. Connect GitHub account
3. Deploy from GitHub → Select your repository
4. Choose `apps/api` as the root directory

**3.2: Add Services**
```bash
# In Railway dashboard, add these services:
1. PostgreSQL (from templates)
2. Redis (from templates)  
3. Your API service (from GitHub)
```

**3.3: Configure Environment Variables**
In Railway → Your API Service → Variables:

```bash
# Database (auto-filled by Railway)
DATABASE_URL=${PostgreSQL.DATABASE_URL}

# Queue  
REDIS_URL=${Redis.REDIS_URL}

# AI Providers
GEMINI_API_KEY=your_actual_gemini_key
GROQ_API_KEY=your_actual_groq_key
PROVIDER=gemini

# PayPal (sandbox for testing)
PAYPAL_CLIENT_ID=fake_paypal_client_id
PAYPAL_CLIENT_SECRET=fake_paypal_client_secret
PAYPAL_ENVIRONMENT=sandbox

# Email (fake for testing)
RESEND_API_KEY=fake_resend_key
EMAIL_FROM=test@yourdomain.com

# Rate Limit Safety (optional - defaults provided)
MAX_AI_REQUESTS_PER_HOUR=100000  # Global safety limit
RATE_LIMIT_PER_HOUR=60           # Job status polling limit

# Security
RATE_LIMIT_PER_HOUR=60
MAX_FILE_MB=200

# Pricing
MIN_PRICE_CENTS=50
TARGET_PROFIT_CENTS=40
MAX_FILE_TOKENS=1000000
```

**3.4: Deploy**
- Railway will auto-deploy on git push
- Monitor logs for successful startup
- Test health check: `https://your-app.up.railway.app/health`

### **Step 4: Frontend Deployment - Vercel (1 hour)**

**4.1: Connect Vercel**
1. Go to [Vercel](https://vercel.com)
2. Import from GitHub → Select your repository
3. Set root directory: `apps/web`
4. Framework preset: Next.js

**4.2: Environment Variables**
In Vercel → Project → Settings → Environment Variables:

```bash
NEXT_PUBLIC_API_BASE=https://your-railway-app.up.railway.app
```

**4.3: Deploy**
- Vercel deploys automatically
- Verify: Visit your Vercel URL
- Test full upload flow

### **Step 5: End-to-End Testing (30 minutes)**

```bash
# Test complete flow
1. Upload EPUB file
2. See price estimate ($0.99-$3.99)
3. Mock payment (with fake PayPal keys)
4. Watch translation progress
5. Download EPUB + PDF + TXT outputs
6. Check Railway logs for success
```

### **Step 6: Domain Setup (Optional - 1 hour)**

```bash
# Purchase domain (e.g., epubtranslator.com)
1. Buy domain from Namecheap/Cloudflare
2. In Vercel: Settings → Domains → Add your domain  
3. Configure DNS records as instructed
4. Update CORS in Railway if needed
```

**🎉 MVP Complete! You now have a working translation service.**

---

## 🏢 Production Deployment (2 Weeks)

**Goal**: Enterprise-ready service with monitoring, backups, and scale

### **Phase 1: Enhanced Infrastructure (Week 1)**

**1.1: Advanced Railway Configuration**
```bash
# Upgrade Railway plan for better performance
- Professional plan ($20/month)
- Increased memory and CPU
- Priority support

# Environment optimizations
REDIS_URL=redis://redis:6379  # Internal Redis
DATABASE_URL=postgresql://...  # Production PostgreSQL
MAX_CONCURRENT_JOBS=10
```

**1.2: Storage Migration to Cloudflare R2**
```bash
# Add R2 environment variables
R2_ACCOUNT_ID=your_cloudflare_account_id
R2_ACCESS_KEY_ID=your_r2_access_key  
R2_SECRET_ACCESS_KEY=your_r2_secret_key
R2_BUCKET=epub-translator-production
R2_REGION=auto
SIGNED_GET_TTL_SECONDS=172800

# Configure R2 CORS
[
  {
    "AllowedOrigins": ["https://yourdomain.com"],
    "AllowedMethods": ["GET", "PUT", "POST"],
    "AllowedHeaders": ["*"],
    "MaxAgeSeconds": 300
  }
]
```

**1.3: Advanced Monitoring**
```bash
# Add Sentry for error tracking
SENTRY_DSN=your_sentry_dsn

# Add logging service (optional)
LOGSTASH_URL=your_logging_service_url
```

### **Phase 2: Business Integration (Week 2)**

**2.1: Live Payment Integration**
- Set up Australian PayPal business account
- Generate live API credentials
- Enable PayPal micropayments pricing
- Configure webhooks for production domain

**2.2: Email Service Activation**
```bash
# Resend production setup
RESEND_API_KEY=your_live_resend_key
EMAIL_FROM=noreply@yourdomain.com

# Configure DNS records for email domain
# SPF: v=spf1 include:_spf.resend.com ~all
# DKIM: Configure as per Resend instructions
```

**2.3: Analytics and SEO**
```bash
# Google Analytics
NEXT_PUBLIC_GA_ID=your_google_analytics_id

# SEO optimization
- Meta tags and Open Graph
- Sitemap generation
- Structured data markup
```

### **Phase 3: Scaling and Optimization**

**3.1: Performance Optimization**
- CDN configuration through Vercel
- Image optimization
- Database query optimization
- Caching layer implementation

**3.2: Advanced Features**
- User authentication (optional)
- API rate limiting tiers
- Bulk translation discounts
- Admin dashboard

**3.3: Backup and Disaster Recovery**
- Automated database backups
- Configuration backup
- Disaster recovery procedures
- Uptime monitoring

---

## 🔧 Platform-Specific Notes

### **Railway Deployment Tips**

**Common Issues:**
```bash
# Build fails - missing dependencies
# Solution: Ensure pyproject.toml includes all dependencies

# Memory issues
# Solution: Upgrade to Professional plan or optimize memory usage

# Port binding issues  
# Solution: Railway automatically sets PORT, don't override
```

**Optimization:**
```bash
# Use Railway's internal networking
REDIS_URL=redis://redis:6379  # Not external URL
DATABASE_URL=postgresql://postgres:5432/...  # Internal connection

# Health check endpoint
railway logs --follow  # Monitor startup
curl https://your-app.up.railway.app/health  # Test health
```

### **Vercel Deployment Tips**

**Common Issues:**
```bash
# Build fails - wrong directory
# Solution: Set root directory to apps/web

# Environment variables not updating
# Solution: Redeploy after environment changes

# CORS issues  
# Solution: Ensure API_BASE points to Railway domain
```

**Optimization:**
```bash
# Use Vercel Analytics
NEXT_PUBLIC_VERCEL_ANALYTICS=true

# Enable compression
# Vercel handles this automatically

# Custom domains
# Add in Project Settings → Domains
```

---

## 🔒 Security Checklist

### **MVP Security (Required)**
- [x] Rate limiting enabled (60 req/hour per IP)
- [x] File type validation (EPUB only)
- [x] File size limits (200MB max)
- [x] Input sanitization
- [x] CORS configuration

### **Production Security (Additional)**
- [ ] DDoS protection via Cloudflare
- [ ] Advanced rate limiting by user
- [ ] Security headers (HSTS, CSP)
- [ ] Regular security audits
- [ ] Encrypted environment variables

---

## 📊 Cost Breakdown

### **MVP Costs**
- Railway Professional: $20/month
- Vercel Pro (optional): $20/month  
- Domain: $15/year
- **Total: $25-45/month**

### **Production Costs**
- Railway Professional: $20/month
- Vercel Pro: $20/month
- Cloudflare R2: $5-15/month
- Monitoring tools: $10-20/month
- **Total: $55-75/month**

---

## 🆘 Common Deployment Issues

### **"Railway build fails"**
```bash
# Check pyproject.toml has all dependencies
poetry lock --check
poetry install --only=main

# Check Python version
python --version  # Should be 3.12+
```

### **"Frontend can't connect to backend"**
```bash
# Verify environment variable
echo $NEXT_PUBLIC_API_BASE  # Should be Railway URL

# Check CORS in Railway logs
railway logs --follow | grep -i cors

# Test API directly
curl https://your-railway-app.up.railway.app/health
```

### **"Database connection fails"**
```bash
# Check Railway PostgreSQL is running
railway status

# Verify DATABASE_URL format
# Should be: postgresql://user:pass@host:port/db

# Test connection
railway run python -c "from app.db import engine; print(engine.execute('SELECT 1'))"
```

### **"Translation jobs not processing"**
```bash
# Check Redis connection
railway run redis-cli ping  # Should return PONG

# Verify worker is running
railway logs --service worker

# Check queue status
railway run python -c "from rq import Queue; import redis; r = redis.from_url('$REDIS_URL'); q = Queue(connection=r); print(f'Jobs: {len(q)}')"
```

---

## 🎯 Deployment Success Criteria

### **MVP Success**
- [ ] Backend health check returns 200
- [ ] Frontend loads without errors
- [ ] Can upload EPUB file
- [ ] Price estimation works
- [ ] Mock payment completes
- [ ] Translation processes successfully
- [ ] Can download all 3 output formats

### **Production Success**
- [ ] All MVP criteria met
- [ ] Real PayPal payments work
- [ ] Email notifications sent
- [ ] Custom domain active
- [ ] Monitoring and logs working
- [ ] Security measures active
- [ ] Performance meets targets

---

**Need help?** Check [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) or create an issue on GitHub.