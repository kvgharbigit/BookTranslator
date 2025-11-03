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

### 2. Run Database Migration on Railway ✅ **COMPLETED**
- [x] Run migration command via `railway connect postgres`
- [x] Verify column exists in Railway database
- [x] Test progress tracking on production
- **Result:** Migration completed Nov 2, 2025 - `progress_percent` column active

### 3. Deploy to Railway ✅ **COMPLETED**
- [x] Configure railway.json to use Dockerfile builder
- [x] Verify all R2 variables are set
- [x] Auto-deploy configured on git push
- [x] Check Railway logs for R2 connection
- [x] Test upload/download on production URL
- **Result:** Live at https://api.polytext.site with R2 storage

### 4. Custom Domain Setup ✅ **COMPLETED**
- [x] Add custom domain to Railway: api.polytext.site
- [x] Configure DNS records in Namecheap
- [x] Add custom domain to Vercel: polytext.site, www.polytext.site
- [x] Update R2 CORS policy for custom domain
- [x] Update backend CORS allowed origins
- [x] Wait for SSL certificate provisioning
- **Result:** Live at https://polytext.site and https://api.polytext.site

---

## 🎯 **HIGH PRIORITY (Next Week)**

### 5. PayPal Live Integration
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

### 5. Email Notifications (Resend) ✅ **COMPLETED**
- [x] Sign up at https://resend.com (free: 100 emails/day)
- [x] Get API key: `re_gPd9MAH3_6pbxEa3Ag7x67MgB4ojW9WaL`
- [x] Update Railway variables:
  ```bash
  RESEND_API_KEY=re_gPd9MAH3_6pbxEa3Ag7x67MgB4ojW9WaL
  EMAIL_FROM=noreply@polytext.site
  ```
- [x] Configure DNS records (SPF, DKIM, MX)
- [x] Verify domain: polytext.site (Nov 3, 2025)
- [x] Test completion email (working)
- [x] Test failure notification email (working)
- [x] Verify download links in email work (confirmed)

### 6. Email Retrieval System ✅ **COMPLETED - Nov 3, 2025**
- [x] Create backend API endpoint `/jobs-by-email/{email}`
- [x] Add rate limiting (10/minute) to prevent abuse
- [x] Filter jobs to last 5 days only
- [x] Generate presigned download URLs for each job
- [x] Create frontend `/retrieve` page
- [x] Add search form with email validation
- [x] Display job list with status indicators
- [x] Show download buttons for completed jobs
- [x] Add link to retrieve page from homepage
- [x] Test end-to-end functionality

### 7. Download Experience Improvements ✅ **COMPLETED - Nov 3, 2025**
- [x] Make download links open in new tabs
- [x] Add `rel="noopener noreferrer"` for security
- [x] Update all three download buttons (EPUB, PDF, TXT)
- [x] Test on production

### 8. R2 Upload Verification ✅ **COMPLETED - Nov 3, 2025**
- [x] Add file size checking after uploads
- [x] Compare local and remote file sizes
- [x] Add detailed logging with emoji indicators
- [x] Test verification logic

---

## 📦 **MEDIUM PRIORITY (2-4 Weeks)**

### 9. Custom Domain Setup ✅ **COMPLETED - Nov 3, 2025**
- [x] Purchase domain: polytext.site (Namecheap)
- [x] Configure DNS:
  - Frontend: Point to Vercel (polytext.site, www.polytext.site)
  - Backend: Point to Railway (api.polytext.site)
- [x] Update R2 CORS policy to use real domain
- [x] Update `EMAIL_FROM` to use custom domain
- [x] Test everything with new domain
- [x] SSL certificates active on all domains

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
- [x] ~~Database migration not run on Railway~~ **FIXED**: Migration completed Nov 2, 2025
- [x] ~~Email notifications not working~~ **FIXED**: Resend configured & tested Nov 3, 2025
- [x] ~~Users losing download links~~ **FIXED**: Email retrieval system Nov 3, 2025
- [x] ~~Downloads don't open in new tab~~ **FIXED**: Added target="_blank" Nov 3, 2025
- [x] ~~No upload verification~~ **FIXED**: File size checking added Nov 3, 2025
- [ ] PayPal payments not tested with real account (pending live setup)

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

**Last Updated:** November 3, 2025
