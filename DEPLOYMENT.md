# 🚀 BookTranslator Deployment Guide

**Last Updated:** November 6, 2025
**Status:** ✅ Production System Live

Deploy your translation service from development to production.

---

## 🌐 Current Production Status

**Live URLs:**
- Frontend: https://polytext.site
- API: https://api.polytext.site
- Health: https://api.polytext.site/health

**Infrastructure:**
- Backend: Railway (FastAPI + PostgreSQL + Redis)
- Frontend: Vercel (Next.js)
- Storage: Cloudflare R2 (5-day retention)
- Domain: polytext.site (Namecheap DNS)

---

## 🎯 Deployment Options

### Option 1: Quick Local Testing (15 minutes)
Perfect for development and testing.

```bash
# Terminal 1: Redis
redis-server

# Terminal 2: Backend API
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

Visit http://localhost:3000 and use "Skip Payment (Test)" to test translations.

### Option 2: Production Deployment (2-4 hours)
Deploy to Railway + Vercel with production infrastructure.

---

## 📋 Production Deployment Steps

### 1. Prerequisites (15 minutes)

**Accounts Needed:**
- [x] GitHub account
- [x] Railway account (https://railway.app)
- [x] Vercel account (https://vercel.com)
- [x] Cloudflare account (for R2 storage)
- [ ] Domain registrar (optional, for custom domain)

**API Keys Needed:**
- [x] Gemini API key (https://aistudio.google.com/app/apikey)
- [x] Groq API key (https://console.groq.com)
- [ ] PayPal credentials (see PAYPAL_SETUP_GUIDE.md)
- [x] Resend API key (https://resend.com)

---

### 2. Cloudflare R2 Setup (30 minutes)

Follow the complete guide: **[R2_SETUP_GUIDE.md](./R2_SETUP_GUIDE.md)**

Quick summary:
1. Create R2 bucket: `epub-translator-production`
2. Configure 5-day lifecycle policy
3. Set up CORS policy
4. Generate API credentials
5. Save Account ID, Access Key, Secret Key

---

### 3. Railway Backend Deployment (45 minutes)

#### 3.1 Create Railway Project

1. Go to [Railway](https://railway.app)
2. Connect GitHub account
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your BookTranslator repository
5. Choose `apps/api` as the root directory

#### 3.2 Add Required Services

In Railway dashboard, add these services:
```
1. PostgreSQL (from templates)
2. Redis (from templates)
3. Your API service (from GitHub repo)
```

#### 3.3 Configure Environment Variables

In Railway → API Service → Variables, add:

**Required Variables:**
```bash
# Database (auto-configured by Railway)
DATABASE_URL=${PostgreSQL.DATABASE_URL}
REDIS_URL=${Redis.REDIS_URL}

# Environment
ENV=production
PORT=8000

# Cloudflare R2 (from Step 2)
R2_ACCOUNT_ID=your_account_id
R2_ACCESS_KEY_ID=your_access_key
R2_SECRET_ACCESS_KEY=your_secret_key
R2_BUCKET=epub-translator-production
R2_REGION=auto
SIGNED_GET_TTL_SECONDS=432000

# AI Providers
GEMINI_API_KEY=your_gemini_key
GROQ_API_KEY=your_groq_key
PROVIDER=gemini

# Email (Resend)
RESEND_API_KEY=your_resend_key
EMAIL_FROM=noreply@yourdomain.com

# PayPal (use sandbox initially)
PAYPAL_CLIENT_ID=sandbox_client_id
PAYPAL_CLIENT_SECRET=sandbox_secret
PAYPAL_ENVIRONMENT=sandbox
PAYPAL_WEBHOOK_ID=webhook_id
```

See [ENVIRONMENT_VARIABLES.md](./ENVIRONMENT_VARIABLES.md) for complete reference.

#### 3.4 Deploy

Railway will auto-deploy when you push to main branch:
```bash
git add .
git commit -m "Deploy to production"
git push origin main
```

Monitor deployment in Railway dashboard → Deployments tab.

#### 3.5 Run Database Migration

```bash
# Connect to Railway PostgreSQL
railway connect postgres

# Run migration
\i /path/to/apps/api/add_progress_percent.sql
```

---

### 4. Vercel Frontend Deployment (15 minutes)

#### 4.1 Connect to Vercel

1. Go to [Vercel](https://vercel.com)
2. Click "Add New" → "Project"
3. Import your GitHub repository
4. Configure:
   - Framework Preset: Next.js
   - Root Directory: `apps/web`

#### 4.2 Configure Environment Variables

In Vercel → Project Settings → Environment Variables:

```bash
NEXT_PUBLIC_API_BASE=https://your-railway-app.up.railway.app
```

After custom domain setup, update to:
```bash
NEXT_PUBLIC_API_BASE=https://api.yourdomain.com
```

#### 4.3 Deploy

Vercel auto-deploys on git push. Monitor in Vercel dashboard.

---

### 5. Custom Domain Setup (30 minutes, optional)

#### 5.1 Purchase Domain

1. Register domain at Namecheap, Google Domains, or similar
2. Example: polytext.site

#### 5.2 Configure DNS Records

**For Backend (Railway):**
1. Railway → Settings → Domains → Add Custom Domain
2. Enter: `api.yourdomain.com`
3. Add DNS records in your registrar:
   ```
   Type: CNAME
   Name: api
   Value: your-service.up.railway.app
   ```

**For Frontend (Vercel):**
1. Vercel → Project → Settings → Domains → Add Domain
2. Enter: `yourdomain.com` and `www.yourdomain.com`
3. Add DNS records in your registrar:
   ```
   Type: A
   Name: @
   Value: 76.76.21.21 (Vercel IP)

   Type: CNAME
   Name: www
   Value: cname.vercel-dns.com
   ```

#### 5.3 Update Configuration

1. Update Railway `CORS_ORIGINS` to include your domain
2. Update Vercel `NEXT_PUBLIC_API_BASE` to use `https://api.yourdomain.com`
3. Update R2 CORS policy to allow your domain
4. Update `EMAIL_FROM` to use your domain

SSL certificates are automatically provisioned by Railway and Vercel.

---

### 6. Email Setup (15 minutes)

See [POST_TRANSLATION_WORKFLOW.md](./POST_TRANSLATION_WORKFLOW.md) for complete workflow.

**Quick Setup:**
1. Sign up at https://resend.com (free tier: 3000 emails/month)
2. Add and verify your domain
3. Configure DNS records (SPF, DKIM)
4. Get API key and add to Railway variables
5. Test email delivery

---

### 7. Payment Setup (PayPal)

See [PAYPAL_SETUP_GUIDE.md](./PAYPAL_SETUP_GUIDE.md) for complete guide.

**Quick Steps:**
1. Create PayPal Business account (30 min)
2. Request Micropayments pricing: 5% + $0.05 (1-3 days approval)
3. Generate API credentials (10 min)
4. Create webhook (5 min)
5. Update Railway environment variables
6. Test live payment

**Important:** Use Micropayments pricing for transactions under $8.

---

## 🧪 Testing Your Deployment

### 1. Health Check
```bash
curl https://api.yourdomain.com/health
```

Should return: `{"status":"ok"}`

### 2. Upload Test
1. Visit https://yourdomain.com
2. Upload test EPUB (use `sample_books/pg236_first20pages.epub`)
3. Click "Skip Payment (Test)" button
4. Monitor progress bar (should go 0% → 100%)
5. Check Railway logs for any errors
6. Download all three formats (EPUB, PDF, TXT)
7. Verify files in R2 dashboard

### 3. Email Test
1. Upload EPUB with your email address
2. Complete translation
3. Check inbox for notification email
4. Verify download links work
5. Check /retrieve page functionality

---

## 💰 Cost Breakdown

### Current Production Costs (Nov 2025)

**Monthly Infrastructure:**
- Railway (Pro): $20/month - Backend + PostgreSQL + Redis
- Vercel (Hobby): $0/month - Frontend hosting
- Cloudflare R2: ~$0.45-4.50/month - Storage (5-day retention)
- Domain: ~$1/month - Registration fee
- Resend: $0/month - Email (free tier: 3000/month)
- **Total**: ~$21-26/month

**Per-Translation Costs (1000 words average):**
- AI (Gemini): ~$0.034 per translation
- PayPal fees: 5% + $0.05 (with Micropayments)
  - On $0.99 sale: $0.10 fee
  - On $1.49 sale: $0.12 fee
  - On $2.99 sale: $0.20 fee

**Example Revenue (100 translations/month @ $1.49 avg):**
- Revenue: $149
- AI costs: $3.40
- PayPal fees: $12
- Infrastructure: $25
- **Net Profit**: ~$108.60 (~73% margin)

---

## 🔒 Security Checklist

Before going live:
- [ ] All API keys stored in Railway/Vercel (never in code)
- [ ] CORS configured for specific domains (not `*`)
- [ ] Rate limiting enabled (60 requests/hour per IP)
- [ ] File size limits enforced (50MB max)
- [ ] HTTPS enabled on all domains
- [ ] Database backups configured
- [ ] Error monitoring setup (Sentry recommended)
- [ ] Usage analytics configured (optional)

---

## 🐛 Troubleshooting

See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for common issues.

**Quick fixes:**

**Railway build fails:**
- Check Railway logs for specific error
- Verify all environment variables are set
- Ensure Dockerfile packages are correct

**Frontend can't connect to backend:**
- Verify `NEXT_PUBLIC_API_BASE` is set correctly
- Check CORS configuration in backend
- Test API health endpoint directly

**Translations fail:**
- Check Railway logs for worker errors
- Verify AI API keys are valid
- Ensure Redis is running
- Check R2 credentials

**Emails not sending:**
- Verify Resend API key
- Check domain verification in Resend dashboard
- Verify DNS records are propagated

---

## 📊 Monitoring & Maintenance

**Daily Checks:**
- Railway health status
- Vercel deployment status
- R2 storage usage (should stay under 300GB with 5-day retention)

**Weekly Checks:**
- Error logs in Railway
- AI API usage/costs
- Email delivery rates
- Payment success rates

**Monthly Checks:**
- Total costs vs revenue
- Storage cleanup (verify 5-day deletion working)
- Database size and performance
- Update dependencies

---

## 🔄 Updating Your Deployment

**Code Updates:**
```bash
git add .
git commit -m "Update: description"
git push origin main
```

Railway and Vercel automatically redeploy on push to main.

**Environment Variables:**
- Railway: Dashboard → Variables → Add/Update
- Vercel: Dashboard → Settings → Environment Variables

**Database Migrations:**
```bash
railway connect postgres
\i /path/to/migration.sql
```

---

## 📞 Support Resources

**Dashboards:**
- Railway: https://railway.app/dashboard
- Vercel: https://vercel.com/dashboard
- Cloudflare R2: https://dash.cloudflare.com/r2
- Resend: https://resend.com/emails
- PayPal Developer: https://developer.paypal.com/dashboard

**Documentation:**
- [Environment Variables](./ENVIRONMENT_VARIABLES.md)
- [R2 Setup](./R2_SETUP_GUIDE.md)
- [PayPal Setup](./PAYPAL_SETUP_GUIDE.md)
- [Email Workflow](./POST_TRANSLATION_WORKFLOW.md)
- [Troubleshooting](./TROUBLESHOOTING.md)

---

**Ready to deploy?** Start with local testing, then follow the production steps above. The entire process takes 2-4 hours from start to finish.
