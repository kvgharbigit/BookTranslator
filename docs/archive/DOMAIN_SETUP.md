# Domain Setup Guide: polytext.site

## Railway Deployment Steps

### 1. Deploy to Railway
```bash
# Connect Railway CLI
railway login

# Deploy from repository
railway deploy

# Set environment variables (add your API keys)
railway variables set GEMINI_API_KEY=your_actual_key
railway variables set GROQ_API_KEY=your_actual_key
```

### 2. Configure Custom Domain in Railway

1. Go to your Railway project dashboard
2. Navigate to Settings → Domains
3. Click "Custom Domain"
4. Add: `polytext.site`
5. Railway will provide DNS records

### 3. Update DNS in Namecheap

In your Namecheap domain management:

1. **Remove current redirect**: Go to Domain → Advanced DNS → Remove the redirect
2. **Add Railway DNS records** (Railway will provide exact values):
   - `A` record: `@` → Railway IP (e.g., `104.21.x.x`)
   - `CNAME` record: `www` → `polytext.site`
   - `CNAME` record: `api` → Railway domain (e.g., `your-app.railway.app`)

### 4. SSL Certificate
Railway automatically provisions SSL certificates for custom domains.

### 5. Environment Variables Already Configured

✅ **Safe variables** (already in repo):
- All configuration settings
- Database URLs
- Rate limits
- File size limits

🔑 **Only add these to Railway manually**:
- `GEMINI_API_KEY`
- `GROQ_API_KEY`

## Final URLs

- **Frontend**: https://polytext.site
- **API**: https://api.polytext.site (if using subdomain)
- **Admin**: Railway dashboard for monitoring

## Verification

Once deployed:
1. Visit https://polytext.site
2. Test file upload
3. Check API health: https://polytext.site/health
4. Monitor logs in Railway dashboard

## Rollback Plan

If issues occur:
1. Re-enable Namecheap redirect temporarily
2. Debug in Railway logs
3. Railway provides instant rollback to previous deployments