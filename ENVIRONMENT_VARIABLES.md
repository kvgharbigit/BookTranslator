# Environment Variables Reference

**Last Updated:** November 3, 2025

This document lists all environment variables required by the BookTranslator application.

---

## 📋 Required Variables

### **Server Configuration**
| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `PORT` | API server port | `8000` | `8000` |
| `ENV` | Environment mode | `development` | `production` / `development` |
| `LOG_LEVEL` | Logging level | `info` | `info` / `debug` / `warning` |
| `DATABASE_URL` | PostgreSQL connection string | `sqlite:///./data/jobs.db` | `postgresql://user:pass@host:5432/db` |

### **Cloudflare R2 Storage** (Required)
| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `R2_ACCOUNT_ID` | Cloudflare account ID | ✅ Yes | `3537af84a0b983711ac3cfe7599a33f1` |
| `R2_ACCESS_KEY_ID` | R2 access key | ✅ Yes | `e055fe74e4ce9dafd50d8ed171c31c77` |
| `R2_SECRET_ACCESS_KEY` | R2 secret key | ✅ Yes | `XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX...` (see .env files) |
| `R2_BUCKET` | Bucket name | ✅ Yes | `epub-translator-production` |
| `R2_REGION` | R2 region | No | `auto` |
| `SIGNED_GET_TTL_SECONDS` | Download URL expiry (5 days) | No | `432000` |

### **Payment Processing (PayPal)**
| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `PAYPAL_CLIENT_ID` | PayPal API client ID | ✅ Yes | `AXXXXXXXXXxxxxxxxxxxxxxxxxxx` |
| `PAYPAL_CLIENT_SECRET` | PayPal API secret | ✅ Yes | `EXXXXXXXXXxxxxxxxxxxxxxxxxxx` |
| `PAYPAL_ENVIRONMENT` | PayPal mode | ✅ Yes | `live` / `sandbox` |
| `PAYPAL_WEBHOOK_ID` | PayPal webhook ID | ✅ Yes | `1AB2CD3EF4GHIJ5KLMNO6PQRS` |
| `MICROPAYMENTS_THRESHOLD_CENTS` | Price threshold for micropayments | No | `800` ($8.00) |

### **Pricing Configuration**
| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `MIN_PRICE_CENTS` | Minimum translation price | `50` | `50` ($0.50) |
| `TARGET_PROFIT_CENTS` | Target profit per job | `40` | `40` ($0.40) |
| `PRICE_CENTS_PER_MILLION_TOKENS` | Base pricing rate | `300` | `300` ($3.00/1M tokens) |

### **AI Translation Providers**
| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `PROVIDER` | Active provider | No | `groq` / `gemini` |
| `GEMINI_API_KEY` | Google Gemini API key | ✅ Yes | `AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXX` (see .env files) |
| `GEMINI_MODEL` | Gemini model name | No | `gemini-2.5-flash-lite` |
| `GROQ_API_KEY` | Groq API key | ✅ Yes | `gsk_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX...` (see .env files) |
| `GROQ_MODEL` | Groq model name | No | `llama-3.1-8b-instant` |
| `MAX_BATCH_TOKENS` | Max tokens per batch | `6000` | `6000` |
| `MAX_JOB_TOKENS` | Max tokens per job | `1000000` | `1000000` |
| `MAX_FILE_TOKENS` | Max tokens for file | `1000000` | `1000000` |
| `RETRY_LIMIT` | Translation retry attempts | `3` | `3` |

### **Queue & Processing**
| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `REDIS_URL` | Redis connection string | ✅ Yes | `redis://localhost:6379` |
| `RQ_QUEUES` | Queue names (comma-separated) | No | `translate` |
| `MAX_CONCURRENT_JOBS` | Max parallel jobs | `5` | `5` |
| `RETENTION_DAYS` | Job data retention | `5` | `5` |

### **Output Formats**
| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `GENERATE_PDF` | Enable PDF generation | `true` | `true` / `false` |
| `GENERATE_TXT` | Enable TXT generation | `true` | `true` / `false` |

### **Email Notifications (Resend)**
| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `EMAIL_PROVIDER` | Email service provider | No | `resend` |
| `RESEND_API_KEY` | Resend API key | ✅ Yes | `re_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX` (see .env files) |
| `EMAIL_FROM` | Sender email address | ✅ Yes | `noreply@polytext.site` |

### **Security & Rate Limiting**
| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `RATE_LIMIT_BURST` | Burst request limit | `10` | `10` |
| `RATE_LIMIT_PER_HOUR` | Hourly request limit | `60` | `60` |
| `MAX_FILE_MB` | Max upload size (MB) | `200` | `200` |
| `MAX_ZIP_ENTRIES` | Max files in ZIP | `5000` | `5000` |
| `MAX_COMPRESSION_RATIO` | Max compression ratio | `10` | `10` |

---

## 🚀 Railway Production Setup

### **Current Status**

✅ **Configured:**
- All core variables set
- Resend email integrated (`noreply@polytext.site`)
- R2 storage fully configured
- Translation providers (Groq + Gemini)
- Database and Redis connected

⚠️ **Pending:**
- PayPal live credentials (currently using sandbox/fake)

### **To Update Railway Variables:**

```bash
# Single variable
railway variables --set "VARIABLE_NAME=value"

# Multiple variables
railway variables --set "VAR1=value1" --set "VAR2=value2"

# View all variables
railway variables
```

---

## 💻 Local Development Setup

### **.env Files**

The project uses two local environment files:

1. **`.env`** - Basic local setup with SQLite
   - Location: `apps/api/.env`
   - Uses local SQLite database
   - Uses production R2 storage
   - Good for simple local testing

2. **`.env.local`** - Hybrid setup with Railway PostgreSQL
   - Location: `apps/api/.env.local`
   - Uses Railway PostgreSQL (external URL)
   - Uses local Redis
   - Uses production R2 storage
   - Best for testing production-like environment

### **Which file to use?**

```bash
# Default (uses .env)
python run_api.py

# Use .env.local instead
cp .env.local .env
python run_api.py
```

---

## 🔐 Secrets Management

### **Never Commit These:**
- ❌ `PAYPAL_CLIENT_SECRET`
- ❌ `RESEND_API_KEY`
- ❌ `GEMINI_API_KEY`
- ❌ `GROQ_API_KEY`
- ❌ `R2_SECRET_ACCESS_KEY`
- ❌ Any `DATABASE_URL` with credentials

### **Where to Find Secret Values:**
- 📁 **Local Development**: Check `apps/api/.env` or `apps/api/.env.local`
- ☁️ **Production**: Stored in Railway environment variables
- ⚠️ **This file**: Contains only placeholder examples with XXXXX

### **Safe to Commit:**
- ✅ Variable names and descriptions
- ✅ Default values
- ✅ Example formats with placeholders
- ✅ Public IDs (R2_ACCOUNT_ID, etc.)

---

## 📊 Service-Specific Variables

### **Cloudflare R2**
- Dashboard: https://dash.cloudflare.com/r2
- Get credentials: R2 Dashboard → Manage R2 API Tokens
- Bucket must exist before running app

### **Railway**
- Dashboard: https://railway.app/project/a3dd86d2-5ce5-43f4-885e-ddc63fcb5d14
- Variables auto-provided: `DATABASE_URL`, `REDIS_URL`, `RAILWAY_*`
- Custom domain: `api.polytext.site`

### **Resend**
- Dashboard: https://resend.com/domains
- API Keys: https://resend.com/api-keys
- Domain verified: `polytext.site` ✅
- Sender: `noreply@polytext.site`

### **PayPal**
- Developer Portal: https://developer.paypal.com/dashboard
- Webhooks: https://developer.paypal.com/dashboard/webhooks
- Environment: Currently `sandbox` → needs `live` setup
- See: `PAYPAL_SETUP_GUIDE.md`

### **Google Gemini**
- Get API Key: https://aistudio.google.com/app/apikey
- Model: `gemini-2.5-flash-lite`
- Cost: $0.34 per 1M tokens (input + output)

### **Groq**
- Dashboard: https://console.groq.com/
- Model: `llama-3.1-8b-instant`
- Cost: $0.074 per 1M tokens (much cheaper for testing)

---

## ✅ Validation Checklist

Before deploying, ensure:

- [ ] All required variables are set (marked with ✅ Yes above)
- [ ] Database connection works (`DATABASE_URL`)
- [ ] Redis connection works (`REDIS_URL`)
- [ ] R2 bucket exists and credentials valid
- [ ] At least one AI provider has valid API key
- [ ] Email domain verified in Resend
- [ ] PayPal credentials match environment (sandbox vs live)

### **Test Locally:**
```bash
# Start backend
cd apps/api
python run_api.py

# Start worker (in another terminal)
python run_worker.py

# Check health endpoint
curl http://localhost:8000/health
```

### **Test Production:**
```bash
# Check health
curl https://api.polytext.site/health

# View Railway logs
railway logs
```

---

## 🐛 Troubleshooting

### **"Missing required environment variable: XXX"**
- Add the variable to Railway or your local `.env` file
- See table above for required variables (✅ Yes)

### **"Database connection failed"**
- Local: Check PostgreSQL/SQLite is accessible
- Production: Railway provides `DATABASE_URL` automatically

### **"Redis connection refused"**
- Local: Start Redis with `redis-server`
- Production: Railway provides `REDIS_URL` automatically

### **"R2 access denied"**
- Verify `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`
- Check bucket exists and name matches `R2_BUCKET`

### **"Email sending failed"**
- Verify `RESEND_API_KEY` is valid
- Check domain is verified in Resend dashboard
- Ensure `EMAIL_FROM` matches verified domain

---

**For more help, see:**
- `README.md` - Setup guide
- `DEPLOYMENT_GUIDE.md` - Production deployment
- `TROUBLESHOOTING.md` - Common issues
- `PAYPAL_SETUP_GUIDE.md` - PayPal integration
