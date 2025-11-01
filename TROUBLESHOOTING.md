# 🛠️ Polytext Troubleshooting Guide

## Common Railway Deployment Issues

### 1. Docker Build Failures

#### **Package Not Found: `libgdk-pixbuf2.0-0`**
```
ERROR: Package 'libgdk-pixbuf2.0-0' has no installation candidate
```
**Fix:** Update Dockerfile package name:
```dockerfile
# ❌ Old (fails)
libgdk-pixbuf2.0-0 \

# ✅ New (works)
libgdk-pixbuf-xlib-2.0-0 \
```

#### **Poetry `--no-dev` Flag Error**
```
ERROR: The option "--no-dev" does not exist
```
**Fix:** Update Poetry command in Dockerfile:
```dockerfile
# ❌ Old (fails)
RUN poetry install --no-dev --no-interaction --no-ansi

# ✅ New (works)
RUN poetry install --only=main --no-root --no-interaction --no-ansi
```

### 2. Runtime Errors

#### **Missing Environment Variables**
```
ValidationError: 4 validation errors for Settings
R2_ACCOUNT_ID: Field required
R2_ACCESS_KEY_ID: Field required
R2_SECRET_ACCESS_KEY: Field required
PAYPAL_WEBHOOK_ID: Field required
```
**Fix:** Add missing environment variables in Railway shared variables:
```
R2_ACCOUNT_ID=fake_account_id
R2_ACCESS_KEY_ID=fake_access_key
R2_SECRET_ACCESS_KEY=fake_secret_key
PAYPAL_WEBHOOK_ID=fake_webhook_id
```

#### **PostgreSQL Driver Missing**
```
ModuleNotFoundError: No module named 'psycopg2'
```
**Fix:** Add PostgreSQL driver to `pyproject.toml`:
```toml
[tool.poetry.dependencies]
sqlalchemy = "^2.0.0"
psycopg2-binary = "^2.9.0"  # Add this line
```
Then run: `poetry lock && railway up --service BookTranslator`

### 3. Service Connection Issues

#### **502 Bad Gateway Errors**
Common causes and fixes:

1. **App Still Starting:**
   - Wait 2-3 minutes after deployment
   - Check Railway logs for startup progress

2. **Missing Dependencies:**
   - Check build logs for failed installations
   - Verify all dependencies in pyproject.toml

3. **Environment Variables:**
   - Ensure all required variables are set
   - Check variable names match exactly

4. **Port Configuration:**
   - Verify `PORT=8000` in environment variables
   - Ensure app binds to `0.0.0.0:$PORT`

#### **Database Connection Failures**
```
sqlalchemy.exc.OperationalError: connection to server failed
```
**Fix:** Verify database environment variables:
```
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
```

## Vercel Frontend Issues

### 1. Environment Variables

#### **API Connection Errors**
**Symptoms:** Frontend loads but can't reach backend
**Fix:** Set correct API base URL:
```bash
# In Vercel dashboard or .env.local
NEXT_PUBLIC_API_BASE=https://booktranslator-production.up.railway.app
```

#### **Build Failures**
**Symptoms:** Vercel build fails during deployment
**Common causes:**
- TypeScript errors
- Missing dependencies
- Environment variable references

**Fix:** Check build logs and fix errors before redeploying

## End-to-End Flow Issues

### 1. File Upload Problems

#### **CORS Errors**
```
Access to fetch at 'api-url' from origin 'frontend-url' has been blocked by CORS
```
**Fix:** Update backend CORS settings:
```python
# In main.py
origins = [
    "https://your-vercel-app.vercel.app",
    "https://your-custom-domain.com"
]
```

#### **File Size Limits**
**Error:** "File too large"
**Fix:** Check environment variables:
```
MAX_FILE_MB=50  # Adjust as needed
```

### 2. Payment Processing

#### **PayPal Sandbox vs Live**
**Issue:** Real payments not working
**Fix:** Ensure live credentials:
```
PAYPAL_ENVIRONMENT=live  # Not sandbox
PAYPAL_CLIENT_ID=your_live_client_id
PAYPAL_CLIENT_SECRET=your_live_secret
```

## AI API Rate Limits & Safety

### 1. Rate Limit Protection

#### **95% Safety Barrier**
Polytext operates at 95% of AI provider limits for safety:

**Gemini 2.5 Flash-Lite:**
- Limit: 4,000 RPM, 4M TPM
- Polytext uses: 3,800 RPM, 3.8M TPM (95%)
- Effective rate: 3,750 RPM with 16ms delays

**Groq Llama 3.1-8B:**
- Limit: 1,000 RPM, 250K TPM  
- Polytext uses: 950 RPM, 237.5K TPM (95%)
- Effective rate: 924 RPM with 65ms delays

#### **What Happens During Rate Limits**
✅ **Translation continues** - automatic retry with exponential backoff
✅ **No data loss** - all requests are idempotent
✅ **Progress preserved** - job resumes from last successful batch
❌ **Slight delays** - processing takes longer but always completes

### 2. Job Status Polling

#### **Rate Limit Errors (429)**
**Error:** "Rate limit exceeded at endpoint: /job/{id}"

**Old Issue:** Limited to 12 requests/minute
**Fixed:** Now allows 1,000 requests/minute

**Why it's safe:**
- Job status is just a database read (lightweight)
- No AI API calls involved in status checking
- Well below actual AI provider limits (1K-4K RPM)

#### **Frontend Polling Behavior**
- Polls every 5 seconds during translation
- Automatically slows down if rate limited (adaptive polling)
- Never crashes or stops - always gets final result

### 3. Global Safety Limits

#### **100K Request/Hour Safety**
- Prevents runaway request loops
- Well above normal usage patterns
- Gemini theoretical max: 228K/hour (4K RPM × 60)
- Groq theoretical max: 57K/hour (1K RPM × 60)

**What triggers this:**
- Multiple concurrent large book translations
- System bugs causing request loops
- Abnormal usage patterns

**Result:** Graceful degradation, not system failure

### 3. Translation Failures

#### **AI Provider Errors**
**Common issues:**
- Invalid API keys
- Rate limits exceeded
- Token limits exceeded

**Debug steps:**
1. Check provider API key validity
2. Verify token estimation accuracy
3. Check provider status pages

#### **Queue Processing Issues**
**Symptoms:** Jobs stuck in "processing"
**Debug:**
1. Check Redis connection
2. Verify RQ worker is running
3. Check worker logs in Railway

## Debugging Commands

### Railway Debugging
```bash
# Check service status
railway status

# View logs
railway logs

# Check environment variables
railway variables

# Force redeploy
railway up --service BookTranslator
```

### Vercel Debugging
```bash
# Check deployment status
vercel inspect your-deployment-url --logs

# Redeploy
vercel --prod --yes

# Check environment variables
vercel env ls
```

### Health Checks
```bash
# Backend health
curl https://booktranslator-production.up.railway.app/health

# Expected response: {"status": "healthy"}

# Frontend availability
curl -I https://your-vercel-app.vercel.app

# Expected: HTTP 200
```

## Performance Monitoring

### Backend Performance
- **Response time**: < 2 seconds for API calls
- **Translation time**: 2-15 minutes depending on book size
- **Memory usage**: Monitor in Railway metrics

### Frontend Performance
- **Load time**: < 3 seconds initial load
- **Bundle size**: Monitor in Vercel analytics
- **Core Web Vitals**: Use Vercel speed insights

## Production Checklist

### Before Going Live
- [ ] All environment variables set correctly
- [ ] Health checks passing
- [ ] Test file upload and translation
- [ ] Payment flow tested (sandbox first)
- [ ] Email notifications working
- [ ] Custom domain configured
- [ ] SSL certificates active
- [ ] Monitoring and alerts set up

### Launch Day
- [ ] Monitor error rates
- [ ] Check payment processing
- [ ] Verify email delivery
- [ ] Watch server resources
- [ ] Test with real users

## Emergency Procedures

### Service Down
1. Check Railway/Vercel status pages
2. Review recent deployments
3. Check environment variables
4. Roll back if necessary
5. Monitor error logs

### Payment Issues
1. Verify PayPal service status
2. Check webhook delivery
3. Review transaction logs
4. Contact PayPal support if needed

### High Error Rates
1. Check application logs
2. Monitor database connections
3. Verify AI provider status
4. Scale resources if needed

## Getting Help

### Railway Support
- Railway Discord: https://discord.gg/railway
- Railway Docs: https://docs.railway.app

### Vercel Support
- Vercel Discord: https://discord.gg/vercel
- Vercel Docs: https://vercel.com/docs

### AI Provider Support
- Google AI Studio: https://aistudio.google.com
- Groq Support: https://console.groq.com

Remember: Most issues are environment configuration problems. Always check environment variables first!