# 💼 EPUB Translator - Business Setup Guide

Complete guide for setting up PayPal payments, domain, email, and business operations.

## 🎯 Business Setup Checklist

- [ ] PayPal business account and live API credentials
- [ ] Custom domain with SSL 
- [ ] Email service for notifications
- [ ] Analytics and monitoring
- [ ] Legal and compliance setup

---

## 💰 PayPal Integration Setup

### **Step 1: PayPal Business Account (30 minutes)**

**1.1: Create Business Account**
1. Go to [PayPal Business](https://www.paypal.com/au/business)
2. Select "Business Account" 
3. Complete business registration:
   - Business type: Individual/Sole Proprietor (easiest)
   - Business category: Computer/Data Processing Services
   - Business description: "Online document translation services"

**1.2: Verify Account**
- Link bank account (required for live payments)
- Complete identity verification
- Enable PayPal micropayments (call PayPal support)

### **Step 2: PayPal Developer Setup (15 minutes)**

**2.1: Create Developer App**
1. Go to [PayPal Developer](https://developer.paypal.com/)
2. Log in with your business account
3. Create new app:
   - App name: "EPUB Translator"
   - Merchant: Your business account
   - Features: Accept payments, Express Checkout

**2.2: Get API Credentials**
```bash
# Live credentials (for production)
PAYPAL_CLIENT_ID=your_live_client_id
PAYPAL_CLIENT_SECRET=your_live_client_secret
PAYPAL_ENVIRONMENT=live

# Keep sandbox credentials for testing
PAYPAL_CLIENT_ID_SANDBOX=your_sandbox_client_id
PAYPAL_CLIENT_SECRET_SANDBOX=your_sandbox_client_secret
```

### **Step 3: Micropayments Optimization**

**3.1: Enable Micropayments Pricing**
- Call PayPal business support: 1800 073 263 (Australia)
- Request micropayments pricing: 5% + $0.05 AUD
- Explain business model: small digital transactions ($0.99-$3.99)
- Wait 1-2 business days for approval

**3.2: Configure Webhooks**
1. In PayPal Developer dashboard
2. Create webhook endpoint: `https://yourdomain.com/api/paypal/webhook`
3. Select events:
   - Payment capture completed
   - Payment capture denied
   - Payment capture refunded

### **Step 4: Testing and Validation**

**4.1: Test Sandbox Payments**
```bash
# Use sandbox credentials in Railway
PAYPAL_CLIENT_ID=your_sandbox_client_id
PAYPAL_CLIENT_SECRET=your_sandbox_client_secret  
PAYPAL_ENVIRONMENT=sandbox

# Test with PayPal sandbox personal account
# Use test cards: 4032032577059114 (Visa)
```

**4.2: Test Live Payments** 
```bash
# Switch to live credentials
PAYPAL_CLIENT_ID=your_live_client_id
PAYPAL_CLIENT_SECRET=your_live_client_secret
PAYPAL_ENVIRONMENT=live

# Test with real $0.99 payment (smallest tier)
# Verify funds appear in PayPal business account
```

---

## 🌐 Domain and SSL Setup

### **Step 1: Domain Purchase (15 minutes)**

**Recommended Domain Registrars:**
- **Cloudflare**: $8-12/year, best DNS management
- **Namecheap**: $10-15/year, good support
- **Google Domains**: $12-15/year, simple setup

**Domain Suggestions:**
- `epubtranslator.com` (primary choice)
- `booktranslator.com` 
- `translatebooks.com`
- `aiepubtranslator.com`

### **Step 2: DNS Configuration (30 minutes)**

**2.1: Vercel Domain Setup**
1. In Vercel dashboard → Project → Settings → Domains
2. Add your domain: `yourdomain.com`
3. Add www subdomain: `www.yourdomain.com` (optional)
4. Copy DNS records provided by Vercel

**2.2: Configure DNS Records**
```bash
# In your domain registrar's DNS settings:

# For apex domain (yourdomain.com)
Type: A
Name: @
Value: 76.76.21.21 (Vercel's IP)

# For www subdomain  
Type: CNAME
Name: www
Value: cname.vercel-dns.com

# For backend subdomain (optional)
Type: CNAME  
Name: api
Value: your-app.up.railway.app
```

**2.3: SSL Certificate**
- Vercel automatically provides SSL certificates
- Verify HTTPS works: `https://yourdomain.com`
- Check SSL rating: [SSL Labs Test](https://www.ssllabs.com/ssltest/)

### **Step 3: Update Application URLs**

**3.1: Update Frontend Environment**
```bash
# In Vercel → Environment Variables
NEXT_PUBLIC_API_BASE=https://your-railway-app.up.railway.app

# Or if using api subdomain:
NEXT_PUBLIC_API_BASE=https://api.yourdomain.com
```

**3.2: Update CORS Settings**
```bash
# In Railway → API service → Environment Variables
FRONTEND_URL=https://yourdomain.com

# Update CORS configuration in your FastAPI app
# Allow origins: yourdomain.com, www.yourdomain.com
```

---

## 📧 Email Service Setup

### **Step 1: Resend Account Setup (15 minutes)**

**1.1: Create Account**
1. Go to [Resend](https://resend.com/)
2. Sign up with business email
3. Choose free plan (3,000 emails/month)

**1.2: Domain Verification**
1. Add your domain in Resend dashboard
2. Configure DNS records:
```bash
# SPF Record
Type: TXT
Name: @
Value: v=spf1 include:_spf.resend.com ~all

# DKIM Record
Type: TXT  
Name: resend._domainkey
Value: [provided by Resend]

# DMARC Record (optional but recommended)
Type: TXT
Name: _dmarc
Value: v=DMARC1; p=quarantine; rua=mailto:admin@yourdomain.com
```

### **Step 2: Email Templates (30 minutes)**

**2.1: Configure Environment Variables**
```bash
# In Railway → Environment Variables
RESEND_API_KEY=your_resend_api_key
EMAIL_FROM=noreply@yourdomain.com

# Optional: Custom reply-to
EMAIL_REPLY_TO=support@yourdomain.com
```

**2.2: Test Email Delivery**
```bash
# Send test email through Resend dashboard
# Verify delivery to various email providers:
# - Gmail
# - Outlook  
# - Yahoo
# - Apple Mail
```

### **Step 3: Email Content Optimization**

**3.1: Professional Email Templates**
- Welcome/confirmation emails
- Translation completion notifications
- Error/failure notifications
- Marketing emails (optional)

**3.2: Deliverability Best Practices**
- Use proper SPF/DKIM records
- Maintain good sender reputation
- Include unsubscribe links
- Monitor bounce rates

---

## 📊 Analytics and Monitoring

### **Step 1: Google Analytics (30 minutes)**

**1.1: Create Analytics Account**
1. Go to [Google Analytics](https://analytics.google.com/)
2. Create new property for your domain
3. Get tracking ID (G-XXXXXXXXXX)

**1.2: Install Tracking**
```bash
# In Vercel → Environment Variables
NEXT_PUBLIC_GA_ID=G-XXXXXXXXXX

# Add Google Analytics to your Next.js app
# (assuming you have GA setup in your frontend)
```

**1.3: Configure Goals**
- File uploads (engagement)
- Payment completions (conversions)
- Download completions (success)

### **Step 2: Business Monitoring (45 minutes)**

**2.1: Revenue Tracking**
```bash
# Track key metrics:
- Daily/monthly revenue
- Translation volume
- Average order value
- Customer acquisition cost
- Profit margins
```

**2.2: System Health Monitoring**
```bash
# Use Railway built-in monitoring
- API response times
- Error rates
- Queue processing times
- Database performance

# Optional: External monitoring
- UptimeRobot (free)
- Pingdom (paid)
- DataDog (enterprise)
```

### **Step 3: Customer Support Setup**

**2.1: Support Channels**
```bash
# Minimum viable support:
- Email: support@yourdomain.com
- FAQ page on website
- GitHub issues for technical problems

# Enhanced support (future):
- Live chat widget
- Knowledge base
- Video tutorials
```

---

## ⚖️ Legal and Compliance

### **Step 1: Terms of Service and Privacy Policy**

**1.1: Required Legal Pages**
- Terms of Service
- Privacy Policy  
- Refund Policy
- Copyright/DMCA Policy

**1.2: Content Guidelines**
```bash
# Key points to include:
- User warranties about content ownership
- DRM-free content requirement
- File retention/deletion policy (7 days)
- Payment terms and refund conditions
- Limitation of liability
```

### **Step 2: Business Registration (Australia)**

**2.1: ABN Registration (if applicable)**
- Register for Australian Business Number
- Consider GST registration if revenue >$75k
- Business insurance (professional indemnity)

**2.2: International Considerations**
- GDPR compliance (EU users)
- Data residency requirements
- Tax obligations for international sales

---

## 🚀 Marketing and Launch Setup

### **Step 1: Pre-Launch Preparation**

**1.1: Content Marketing**
- Blog posts about translation
- Social media presence
- SEO optimization
- Google Business listing

**1.2: Launch Strategy**
```bash
# Soft launch (Week 1):
- Friends and family testing
- Social media announcement
- Product Hunt submission

# Public launch (Week 2):
- Press release
- Industry blog outreach
- Paid advertising (Google Ads)
- Influencer partnerships
```

### **Step 2: Growth Optimization**

**2.1: Conversion Optimization**
- A/B testing landing pages
- Pricing optimization
- User experience improvements
- Customer feedback integration

**2.2: Scaling Preparation**
- Customer service processes
- Technical scaling plans
- International expansion
- Enterprise feature development

---

## 📋 Business Launch Checklist

### **Pre-Launch (All Required)**
- [ ] PayPal live payments working
- [ ] Custom domain with SSL active
- [ ] Email notifications functioning
- [ ] Analytics tracking implemented
- [ ] Legal pages published
- [ ] Terms of service accepted by users
- [ ] Backup and monitoring systems active

### **Launch Day**
- [ ] All systems tested and verified
- [ ] Customer support channels ready
- [ ] Social media accounts active
- [ ] Launch announcement prepared
- [ ] Emergency procedures documented

### **Post-Launch (First Week)**
- [ ] Monitor system performance daily
- [ ] Respond to customer inquiries promptly
- [ ] Track key business metrics
- [ ] Gather user feedback actively
- [ ] Plan feature improvements
- [ ] Scale infrastructure as needed

---

## 💡 Business Tips

### **Revenue Optimization**
- Monitor which book types are most popular
- Adjust pricing based on demand
- Offer bulk discounts for repeat customers
- Consider subscription models for heavy users

### **Customer Acquisition**
- Target students and researchers (high demand)
- Partner with language learning platforms
- Reach out to small publishers
- Build referral programs

### **Operational Excellence**
- Automate as much as possible
- Monitor profit margins closely
- Plan for seasonal demand variations
- Build customer loyalty programs

---

**Questions?** Create an issue on GitHub or email support@yourdomain.com