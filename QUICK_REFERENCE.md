# BookTranslator - Quick Reference

**Last Updated:** November 2, 2025

---

## ✅ **WHAT'S WORKING**

### **Core Features**
- ✅ EPUB upload and translation
- ✅ Multi-format output (EPUB, PDF, TXT)
- ✅ Real-time batch progress tracking (0-100%)
- ✅ Cloudflare R2 storage (5-day retention)
- ✅ AI translation (Groq Llama + Gemini)
- ✅ Price estimation
- ✅ Skip payment (testing mode)

### **Infrastructure**
- ✅ Railway PostgreSQL (production database)
- ✅ Local Redis (job queue)
- ✅ FastAPI backend
- ✅ Next.js frontend
- ✅ Cloudflare R2 (file storage)

---

## ⚠️ **WHAT'S CONFIGURED BUT NOT TESTED**

- ⚠️ PayPal payments (sandbox credentials)
- ⚠️ Email notifications (fake Resend key)
- ⚠️ Railway deployment with R2

---

## ❌ **WHAT'S NOT WORKING**

- ❌ Database migration on Railway (progress_percent column)
- ❌ Live PayPal payments (no business account)
- ❌ Email delivery (no Resend API key)
- ❌ Custom domain (none purchased)

---

## 🚀 **HOW TO TEST LOCALLY**

```bash
# 1. Start Redis
redis-server

# 2. Start Backend (Terminal 2)
cd apps/api
poetry run uvicorn app.main:app --reload --port 8000

# 3. Start Worker (Terminal 3 - macOS)
cd apps/api
PYTHONPATH=/Users/kayvangharbi/PycharmProjects/BookTranslator OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES poetry run rq worker translate --url redis://localhost:6379

# 4. Start Frontend (Terminal 4)
cd apps/web
npm run dev

# 5. Open browser
open http://localhost:3000
```

**Test Flow:**
1. Upload an EPUB file
2. Click "Skip Payment (Test)"
3. Watch progress bar (should show 0% → 100% smoothly)
4. Download EPUB, PDF, TXT when complete
5. Check Cloudflare R2 dashboard for uploaded files

---

## 📦 **STORAGE LOCATIONS**

### **Local Development:**
- Files stored in: `/Users/kayvangharbi/PycharmProjects/BookTranslator/apps/api/local_storage/`
- Uploads: `local_storage/uploads/{uuid}/{filename}.epub`
- Outputs: `local_storage/outputs/{job-id}.{format}`

### **Production (Cloudflare R2):**
- Bucket: `epub-translator-production`
- Region: Eastern North America (ENAM)
- Dashboard: https://dash.cloudflare.com/r2
- Uploads: `uploads/{uuid}/{filename}.epub`
- Outputs: `outputs/{job-id}.{format}`
- **Auto-delete:** After 5 days

---

## 🔑 **CREDENTIALS LOCATIONS**

### **Development:**
- File: `apps/api/.env.local`
- Database: Railway PostgreSQL (external URL)
- Redis: localhost:6379
- R2: Production credentials (Cloudflare)

### **Production (Railway):**
- Dashboard: https://railway.app/dashboard
- Service: `booktranslator-api`
- Variables: See Railway Variables tab
- **R2 Credentials:** Stored in `.r2-credentials.txt` (not committed)

---

## 💰 **PRICING**

### **Development (Current):**
```
Groq Llama 3.1: $0.074 per 1M tokens
Average book: ~100k tokens = $0.0074
Target price: $0.50 (minimum)
Profit: $0.49 per translation
```

### **Production (Recommended):**
```
Gemini 2.5 Flash-Lite: $0.34 per 1M tokens
Average book: ~100k tokens = $0.034
Target price: $0.50-1.50
Profit: $0.47-1.47 per translation
```

### **Monthly Costs (1,000 translations):**
```
Cloudflare R2:    $4.50  (5-day retention)
Railway:         $20.00  (Pro plan)
Gemini AI:       $34.00  (translation costs)
Resend Email:     $0.00  (free tier)
Total:           ~$58.50/month
Revenue @ $1/ea:  $1,000/month
Net Profit:       $941.50/month
```

---

## 🐛 **TROUBLESHOOTING**

### **Worker crashes on macOS or "no module named common" error:**
```bash
cd apps/api
PYTHONPATH=/Users/kayvangharbi/PycharmProjects/BookTranslator OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES poetry run rq worker translate --url redis://localhost:6379
```

### **Can't connect to PostgreSQL:**
Check Railway database is running and external URL is correct in `.env.local`

### **Files not appearing in R2:**
1. Check credentials in `.env.local`
2. Restart backend/worker
3. Check Cloudflare R2 dashboard for errors

### **Progress stuck at 0%:**
Database migration not run - `progress_percent` column missing

---

## 📚 **DOCUMENTATION**

- **Current Status:** `CURRENT_STATUS.md` - Complete implementation details
- **Todo List:** `TODO.md` - What needs to be done
- **R2 Setup:** `R2_SETUP_GUIDE.md` - Cloudflare R2 configuration
- **Deployment:** `DEPLOYMENT_GUIDE.md` - Production deployment
- **Main README:** `README.md` - Getting started

---

## 🔗 **DASHBOARDS**

| Service | URL | Purpose |
|---------|-----|---------|
| Cloudflare R2 | https://dash.cloudflare.com/r2 | File storage |
| Railway | https://railway.app/dashboard | Database + Backend |
| Vercel | https://vercel.com/dashboard | Frontend |
| Groq | https://console.groq.com/ | AI API (testing) |
| Gemini | https://aistudio.google.com/app/apikey | AI API (production) |

---

## 🎯 **NEXT STEPS**

1. **Test R2 locally** - Verify files upload/download
2. **Run DB migration** - Add progress_percent column on Railway
3. **Deploy to Railway** - Test production environment
4. **Set up PayPal** - Get live credentials
5. **Set up Resend** - Enable email notifications

See `TODO.md` for complete checklist.
