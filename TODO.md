# BookTranslator - TODO List

## 🔥 **IMMEDIATE (This Week)**

### 1. Test R2 Integration End-to-End ✅ **COMPLETED**
- [x] Restart local backend/worker with new `.env.local`
- [x] Upload test EPUB via frontend
- [x] Verify file appears in R2 dashboard: https://dash.cloudflare.com/r2
- [x] Check batch progress updates work (0-100%)
- [x] Download all formats (EPUB, PDF, TXT)
- [x] Verify 5-day expiry notice shows
- **Result:** 7/7 tests passed, R2 fully functional with public download URLs

### 2. Run Database Migration on Railway
```bash
# Add progress_percent column to production database
railway run --service booktranslator-api psql $DATABASE_URL -f apps/api/add_progress_percent.sql
```
- [ ] Run migration command
- [ ] Verify column exists in Railway database
- [ ] Test progress tracking on production

### 3. Deploy to Railway
- [ ] Remove `STORAGE_TYPE=local` from Railway variables (if exists)
- [ ] Verify all R2 variables are set
- [ ] Trigger new deployment: `railway up` or via dashboard
- [ ] Check Railway logs for R2 connection
- [ ] Test upload/download on production URL

---

## 🎯 **HIGH PRIORITY (Next Week)**

### 4. PayPal Live Integration
- [ ] Create Australian PayPal business account
- [ ] Generate live API credentials (Client ID, Secret)
- [ ] Get PayPal Webhook ID
- [ ] Update Railway variables:
  ```bash
  PAYPAL_CLIENT_ID=<live_id>
  PAYPAL_CLIENT_SECRET=<live_secret>
  PAYPAL_WEBHOOK_ID=<webhook_id>
  PAYPAL_ENVIRONMENT=live
  ```
- [ ] Test real payment ($0.50 minimum)
- [ ] Verify webhook receives payment
- [ ] Test end-to-end: Upload → Pay → Translate → Download

### 5. Email Notifications (Resend)
- [ ] Sign up at https://resend.com (free: 100 emails/day)
- [ ] Get API key
- [ ] Update Railway variables:
  ```bash
  RESEND_API_KEY=<real_key>
  EMAIL_FROM=noreply@yourdomain.com  # or resend-provided email
  ```
- [ ] Test completion email
- [ ] Test failure notification email
- [ ] Verify download links in email work

---

## 📦 **MEDIUM PRIORITY (2-4 Weeks)**

### 6. Custom Domain Setup
- [ ] Purchase domain (Namecheap/Cloudflare)
- [ ] Configure DNS:
  - Frontend: Point to Vercel
  - Backend: Point to Railway
- [ ] Update R2 CORS policy to use real domain
- [ ] Update `EMAIL_FROM` to use custom domain
- [ ] Test everything with new domain

### 7. Production Hardening
- [ ] Add Sentry for error tracking
- [ ] Set up usage analytics (PostHog/Plausible)
- [ ] Test rate limiting (60/hour)
- [ ] Load test with 10 concurrent uploads
- [ ] Create backup strategy for database
- [ ] Document recovery procedures

### 8. Legal & Compliance
- [ ] Create Terms of Service
- [ ] Create Privacy Policy
- [ ] Add cookie consent (if needed)
- [ ] Add refund policy
- [ ] Add contact/support page

---

## 🌟 **NICE TO HAVE (Future)**

### 9. Feature Enhancements
- [ ] Show detected source language in UI
- [ ] Add email validation
- [ ] Add file size validation UI feedback
- [ ] Support more input formats (PDF, MOBI)
- [ ] Add user accounts (optional)
- [ ] Add translation history (optional)
- [ ] Support custom glossaries
- [ ] Add language auto-detection display

### 10. Optimization
- [ ] Cache price estimates
- [ ] Optimize PDF generation speed
- [ ] Add compression for large files
- [ ] Implement request deduplication
- [ ] Add batch job processing

### 11. Marketing & Growth
- [ ] Create landing page copy
- [ ] Add testimonials section
- [ ] Create demo video
- [ ] Set up Google Analytics
- [ ] Create blog for SEO
- [ ] Submit to product directories

---

## 🐛 **KNOWN BUGS**

- [x] ~~macOS PDF generation crash~~ **FIXED**: `OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES`
- [x] ~~Progress jumps 30% → 60%~~ **FIXED**: Batch-level progress tracking
- [ ] Database migration not run on Railway (progress_percent column missing)
- [ ] Email notifications not working (fake API key)
- [ ] PayPal payments not tested with real account

---

## 📊 **METRICS TO TRACK**

Once live, monitor:
- [ ] R2 storage usage (should cap at ~300GB with 1,000 jobs/month)
- [ ] R2 monthly cost (should be ~$4.50 at 1,000 jobs/month)
- [ ] Translation success rate (target: >95%)
- [ ] Average translation time (target: <5 minutes)
- [ ] Payment success rate (target: >90%)
- [ ] Email delivery rate (target: >95%)
- [ ] User satisfaction (add feedback form)

---

## 🔗 **HELPFUL LINKS**

- **Cloudflare R2:** https://dash.cloudflare.com/r2
- **Railway Dashboard:** https://railway.app/dashboard
- **Vercel Dashboard:** https://vercel.com/dashboard
- **Resend Dashboard:** https://resend.com/emails
- **PayPal Developer:** https://developer.paypal.com/dashboard

---

**Last Updated:** November 2, 2025
