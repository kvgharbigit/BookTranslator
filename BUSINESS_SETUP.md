# 💼 BookTranslator - Business Setup Guide

**Last Updated:** November 3, 2025
**Status:** ⚠️ PayPal pending, Email complete, Domain complete

Quick reference for business operations and service setup.

---

## 🎯 Setup Status Overview

| Service | Status | Guide | Notes |
|---------|--------|-------|-------|
| **PayPal Payments** | ⚠️ Pending | [PAYPAL_SETUP_GUIDE.md](./PAYPAL_SETUP_GUIDE.md) | Awaiting live credentials |
| **Custom Domain** | ✅ Complete | [PRODUCTION_DEPLOYMENT.md](./PRODUCTION_DEPLOYMENT.md) | polytext.site |
| **Email Notifications** | ✅ Complete | [POST_TRANSLATION_WORKFLOW.md](./POST_TRANSLATION_WORKFLOW.md) | Resend configured |
| **Environment Variables** | ✅ Complete | [ENVIRONMENT_VARIABLES.md](./ENVIRONMENT_VARIABLES.md) | All documented |
| **Error Monitoring** | ❌ Not Started | - | Sentry recommended |
| **Usage Analytics** | ❌ Not Started | - | PostHog/Plausible |
| **Legal Pages** | ❌ Not Started | - | Terms, Privacy Policy |

---

## 💳 Payment Integration

### **PayPal (Primary Payment Processor)**

**Current Status:**
- ✅ Code implementation complete
- ✅ Sandbox credentials configured
- ✅ Webhook endpoints ready
- ✅ Micropayments support configured
- ⚠️ **Awaiting live business account setup**

**Complete Setup Guide:**
→ **[PAYPAL_SETUP_GUIDE.md](./PAYPAL_SETUP_GUIDE.md)**

**Quick Start:**
1. Create PayPal Business account (30 min)
2. Request Micropayments pricing: 5% + $0.05 (1-3 days)
3. Get live API credentials (10 min)
4. Create webhook (5 min)
5. Update Railway variables (5 min)
6. Test live payment (30 min)

**Required Environment Variables:**
```bash
PAYPAL_CLIENT_ID=<live_client_id>
PAYPAL_CLIENT_SECRET=<live_client_secret>
PAYPAL_WEBHOOK_ID=<webhook_id>
PAYPAL_ENVIRONMENT=live
```

**Timeline:** 1-3 business days (account verification)

---

## 📧 Email Notifications

### **Resend (Email Service Provider)**

**Current Status:** ✅ **Fully Configured**

**Setup Completed:**
- ✅ API Key: `re_gPd9MAH3_6pbxEa3Ag7x67MgB4ojW9WaL`
- ✅ Domain: `polytext.site` (DNS configured)
- ✅ Sender: `noreply@polytext.site`
- ✅ SPF Record: Configured
- ✅ DKIM Record: Configured
- ⏳ Domain Verification: Pending (DNS propagated)

**Email Types:**
1. **Completion Email** - Sent when translation done
   - Download links for EPUB, PDF, TXT
   - 5-day expiry notice
   - Professional HTML template

2. **Failure Email** - Sent when translation fails
   - Error details
   - "Try Again" call-to-action
   - No charge notice

**Documentation:**
→ **[POST_TRANSLATION_WORKFLOW.md](./POST_TRANSLATION_WORKFLOW.md)** - Complete email workflow

**Test Email:**
1. Verify domain at https://resend.com/domains
2. Run translation with your email
3. Check inbox for notification

---

## 🌐 Domain & DNS

### **Custom Domain Setup**

**Current Status:** ✅ **Complete**

**Configured:**
- Domain: `polytext.site` (Namecheap)
- Frontend: `https://polytext.site`
- API: `https://api.polytext.site`
- SSL: ✅ Let's Encrypt (auto-renewal)

**DNS Records:**
| Type | Host | Target | Purpose |
|------|------|--------|---------|
| A | @ | 76.76.21.21 | Frontend (Vercel) |
| CNAME | www | cname.vercel-dns.com | WWW redirect |
| CNAME | api | n1vq2u2a.up.railway.app | Backend API |
| TXT | @ | v=spf1 include:amazonses.com... | Email SPF |
| TXT | resend._domainkey | p=MIGfMA0GCS... | Email DKIM |

**Documentation:**
→ **[PRODUCTION_DEPLOYMENT.md](./PRODUCTION_DEPLOYMENT.md)** - Complete deployment status

---

## 📊 Analytics & Monitoring

### **Error Tracking** ❌ Not Started

**Recommended:** Sentry

**Setup Steps:**
1. Sign up at https://sentry.io (free tier)
2. Create Python project
3. Get DSN key
4. Add to Railway: `SENTRY_DSN=<dsn>`
5. Install SDK (already in requirements.txt)

**Cost:** Free tier: 5,000 errors/month

---

### **Usage Analytics** ❌ Not Started

**Options:**

**1. Plausible (Recommended)**
- Privacy-friendly
- GDPR compliant
- Cost: $9/month (10k page views)
- Setup: Add script tag to frontend

**2. PostHog**
- Open-source
- Self-hostable
- Free tier: 1M events/month
- Setup: Add JS snippet

**3. Google Analytics**
- Free
- Comprehensive
- Privacy concerns
- Setup: Add GA4 tag

---

## 📄 Legal & Compliance

### **Required Documents** ❌ Not Started

**1. Terms of Service**
- User agreement
- Service limitations
- Refund policy
- Usage restrictions

**2. Privacy Policy**
- Data collection disclosure
- Cookie usage
- Third-party services (PayPal, Resend, R2)
- GDPR compliance (if EU users)

**3. Refund Policy**
- Refund conditions
- Processing timeline
- Contact information

**Tools:**
- https://www.termsfeed.com/ (free generators)
- https://www.freeprivacypolicy.com/
- Or hire lawyer for custom policies

**Timeline:** 2-4 hours (using generators)

---

### **Business Registration** ⚠️ Pending

**For Australia:**
1. **ABN Registration** (if revenue > $75k/year)
   - Register at: https://abr.gov.au/
   - Free for sole traders
   - Takes 10-15 minutes

2. **GST Registration** (if revenue > $75k/year)
   - Included with ABN registration
   - Quarterly GST returns required

3. **Business Name** (optional)
   - Register if using name other than personal
   - Cost: ~$40 for 3 years

**Note:** Can operate without ABN initially, but PayPal Business may require it

---

## 💰 Pricing Strategy

### **Current Pricing Model**

**Cost Structure:**
```
Translation Price = Provider Cost + Profit Margin
Minimum Price: $0.50
Target Profit: $0.40 per translation
```

**Price Examples:**
| File Size | Tokens | Provider Cost | Price | Your Profit |
|-----------|--------|---------------|-------|-------------|
| Small (50k words) | ~100k | $0.10 | $0.50 | $0.40 |
| Medium (100k words) | ~200k | $0.20 | $0.70 | $0.50 |
| Large (200k words) | ~400k | $0.40 | $1.00 | $0.60 |

**PayPal Fees (Micropayments):**
- Fee: 5% + $0.05
- Example: $1.00 sale → $0.10 fee → $0.90 net

**Configuration:**
```bash
MIN_PRICE_CENTS=50  # $0.50 minimum
TARGET_PROFIT_CENTS=40  # $0.40 profit
MICROPAYMENTS_THRESHOLD_CENTS=800  # $8.00 threshold
```

---

## 🔐 Security Checklist

### **Before Going Live:**

**Credentials:**
- [ ] All API keys in Railway (not in code)
- [ ] PayPal webhook signature verification enabled
- [ ] Resend API key secured
- [ ] R2 access keys secured
- [ ] No secrets in git history

**Application:**
- [ ] HTTPS on all domains
- [ ] CORS configured correctly
- [ ] Rate limiting enabled (60/hour)
- [ ] File size limits enforced (200MB)
- [ ] Input validation on all endpoints
- [ ] SQL injection protection (SQLAlchemy ORM)

**Infrastructure:**
- [ ] Database backups configured
- [ ] Redis persistence enabled
- [ ] Error monitoring active (Sentry)
- [ ] Logging configured properly
- [ ] Railway environment = production

---

## 📞 Support Resources

### **Service Dashboards:**
- **PayPal:** https://developer.paypal.com/dashboard
- **Resend:** https://resend.com/domains
- **Cloudflare R2:** https://dash.cloudflare.com/r2
- **Railway:** https://railway.app/project/a3dd86d2-5ce5-43f4-885e-ddc63fcb5d14
- **Vercel:** https://vercel.com/dashboard
- **Namecheap:** https://ap.www.namecheap.com/

### **Documentation:**
- **PayPal Setup:** [PAYPAL_SETUP_GUIDE.md](./PAYPAL_SETUP_GUIDE.md)
- **Email Workflow:** [POST_TRANSLATION_WORKFLOW.md](./POST_TRANSLATION_WORKFLOW.md)
- **Environment Vars:** [ENVIRONMENT_VARIABLES.md](./ENVIRONMENT_VARIABLES.md)
- **Production Status:** [PRODUCTION_DEPLOYMENT.md](./PRODUCTION_DEPLOYMENT.md)
- **All Docs:** [DOCUMENTATION_INDEX.md](./DOCUMENTATION_INDEX.md)

---

## 🎯 Next Steps

### **Immediate (This Week):**
1. ⏳ Verify Resend domain (5 min)
2. ⏳ Test email notifications (15 min)
3. ⏳ Start PayPal Business account (30 min)

### **Short Term (Next Week):**
4. 🔄 Complete PayPal setup (1-3 business days)
5. 🔄 Test live payment ($0.50)
6. 🔄 Add Sentry error tracking (30 min)

### **Medium Term (2-4 Weeks):**
7. 📄 Create legal pages (2-4 hours)
8. 📊 Add analytics (1 hour)
9. 🧪 Load testing (2 hours)
10. 🚀 Remove "Skip Payment" button

---

**Status:** 🟢 **80% Complete** - Only PayPal and legal pages remaining!
