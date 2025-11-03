# PayPal Live Setup Guide

**Date:** November 2, 2025
**Status:** ⚠️ Using sandbox credentials - needs live setup

---

## 📋 Prerequisites

- [ ] Business or Premier PayPal account (required for API access)
- [ ] Business details (ABN/ACN if in Australia)
- [ ] Bank account linked to PayPal
- [ ] Live website URL (https://polytext.site ✅ we have this)

---

## 🚀 Step-by-Step Setup

### **Step 1: Create PayPal Business Account (or Upgrade Existing)**

#### **Option A: Create New Business Account**

1. Go to: https://www.paypal.com/au/business
2. Click **"Sign Up"**
3. Choose **"Business Account"**
4. Fill in your business details:
   - Business name: **Polytext** (or your registered business name)
   - Business type: Sole proprietorship / Company
   - ABN/ACN (if registered in Australia)
   - Contact information
   - Business address: 230 Moreland Rd, Brunswick VIC 3052

5. **Verify your email** (check inbox)
6. **Link bank account** (for payouts)
7. **Complete identity verification** (may require ID upload)

**Timeline:**
- Account creation: Immediate
- Bank verification: 1-3 business days
- Identity verification: Minutes to 24 hours

---

#### **Option B: Upgrade Existing Personal Account**

1. Log in to your PayPal account
2. Go to: **Settings** → **Account Settings**
3. Click **"Upgrade to Business Account"**
4. Follow prompts to add business information
5. Link bank account if not already linked

---

### **Step 2: Get API Credentials**

Once your business account is approved and verified:

#### **2.1 Access Developer Dashboard**

1. Go to: https://developer.paypal.com/
2. Log in with your PayPal Business account
3. Click on **"Dashboard"** in top right

#### **2.2 Create REST API App**

1. Click **"Apps & Credentials"** in left sidebar
2. Make sure **"Live"** toggle is selected (NOT Sandbox)
3. Click **"Create App"**
4. Fill in:
   - **App Name:** `Polytext Translation Service`
   - **App Type:** `Merchant`
5. Click **"Create App"**

#### **2.3 Copy Credentials**

You'll now see your live credentials:

```
Client ID: AXXXXXXXXXxxxxxxxxxxxxxxxxxx
Secret: EXXXXXXXXXxxxxxxxxxxxxxxxxxx
```

⚠️ **IMPORTANT:** Keep these secret! Never commit to git.

---

### **Step 3: Create Webhook**

Webhooks notify your backend when payments complete.

#### **3.1 Create Webhook**

1. Still in PayPal Developer Dashboard
2. Click **"Webhooks"** in left sidebar (under "Apps & Credentials")
3. Click **"Add Webhook"**
4. Fill in:
   - **Webhook URL:** `https://api.polytext.site/webhook/paypal`
   - **Event types:** Click "Select all events" OR choose:
     - `PAYMENT.CAPTURE.COMPLETED`
     - `PAYMENT.CAPTURE.DENIED`
     - `PAYMENT.CAPTURE.REFUNDED`

5. Click **"Save"**

#### **3.2 Copy Webhook ID**

After saving, you'll see:
```
Webhook ID: 1AB2CD3EF4GHIJ5KLMNO6PQRS
```

Save this - you'll need it for Railway.

---

### **Step 4: Update Railway Environment Variables**

Now we'll update your production backend with live credentials.

#### **4.1 Via Railway Dashboard (Easiest)**

1. Go to: https://railway.app/project/a3dd86d2-5ce5-43f4-885e-ddc63fcb5d14/service/ee3c2e91-a6ff-4313-af92-2144591977c4

2. Click **"Variables"** tab

3. Update/Add these variables:
   - `PAYPAL_CLIENT_ID` = Your live Client ID
   - `PAYPAL_CLIENT_SECRET` = Your live Secret
   - `PAYPAL_WEBHOOK_ID` = Your Webhook ID
   - `PAYPAL_ENVIRONMENT` = `live` (change from "sandbox")

4. Click **"Save"**

5. Railway will automatically redeploy with new credentials

---

#### **4.2 Via Railway CLI (Alternative)**

```bash
railway variables --set "PAYPAL_CLIENT_ID=AXXXXXXXXXxxxxxxxxxxxxxxxxxx"
railway variables --set "PAYPAL_CLIENT_SECRET=EXXXXXXXXXxxxxxxxxxxxxxxxxxx"
railway variables --set "PAYPAL_WEBHOOK_ID=1AB2CD3EF4GHIJ5KLMNO6PQRS"
railway variables --set "PAYPAL_ENVIRONMENT=live"
```

---

### **Step 5: Verify Integration**

#### **5.1 Check Deployment Logs**

```bash
railway logs | grep -i paypal
```

Look for:
```
PayPal Provider initialized (mode: live)
```

#### **5.2 Test Payment Flow**

1. Go to https://polytext.site
2. Upload a small EPUB file
3. Select target language
4. Click **"Pay with PayPal"** (NOT "Skip Payment")
5. You'll be redirected to PayPal
6. Complete payment with your PayPal account
7. Verify you're redirected back to success page
8. Check that translation job starts

#### **5.3 Check PayPal Dashboard**

1. Go to: https://www.paypal.com/activity
2. You should see your test payment
3. Verify webhook was triggered:
   - Go to Developer Dashboard → Webhooks
   - Click on your webhook
   - Check "Recent Deliveries"
   - Should show successful delivery to your endpoint

---

### **Step 6: Verify Webhook is Working**

#### **6.1 Check Backend Logs**

```bash
railway logs | grep webhook
```

Look for:
```
PayPal webhook received: PAYMENT.CAPTURE.COMPLETED
Processing payment for job: <job_id>
Job <job_id> marked as paid
```

#### **6.2 Test Refund (Optional)**

1. In PayPal dashboard, find a test transaction
2. Issue refund
3. Check that your backend received `PAYMENT.CAPTURE.REFUNDED` webhook

---

## 🔒 Security Checklist

### **Before Going Live:**

- [ ] ✅ Never commit API credentials to git
- [ ] ✅ All credentials stored in Railway environment variables
- [ ] ✅ Webhook endpoint is HTTPS (https://api.polytext.site)
- [ ] ✅ Webhook signature verification enabled in code
- [ ] ✅ Test with small payment first ($0.50)
- [ ] ✅ Monitor PayPal dashboard for first few transactions

---

## 💰 PayPal Fee Structure

### **Australian PayPal Micropayments Fees**

For transactions **under $10 AUD** (our use case):
- **Fee:** 6.4% + $0.30 AUD

### **Examples:**

| Translation Price | PayPal Fee | You Receive |
|-------------------|------------|-------------|
| $0.50 | $0.33 (66%) | $0.17 |
| $0.99 | $0.36 (36%) | $0.63 |
| $1.49 | $0.40 (27%) | $1.09 |
| $2.99 | $0.49 (16%) | $2.50 |

**Note:** For small transactions like $0.50, PayPal takes a large percentage. Consider:
- Minimum price of $0.99 or $1.49
- Or use different payment processor for small amounts

---

## 🧪 Testing Checklist

### **Before Announcing to Public:**

- [ ] Test successful payment flow
- [ ] Test cancelled payment
- [ ] Test webhook delivery
- [ ] Test translation starts after payment
- [ ] Test email notification (once Resend is set up)
- [ ] Test download links work
- [ ] Test on mobile device
- [ ] Verify PayPal dashboard shows transactions
- [ ] Verify you can withdraw funds to bank account

---

## 🚨 Troubleshooting

### **"Client ID/Secret Invalid" Error**

**Problem:** Backend can't authenticate with PayPal

**Solutions:**
1. Verify you copied credentials correctly (no extra spaces)
2. Ensure you're using **Live** credentials, not Sandbox
3. Check `PAYPAL_ENVIRONMENT=live` in Railway
4. Restart Railway service

---

### **Webhook Not Being Called**

**Problem:** Payment succeeds but translation doesn't start

**Solutions:**
1. Check webhook URL is exactly: `https://api.polytext.site/webhook/paypal`
2. Verify webhook events include `PAYMENT.CAPTURE.COMPLETED`
3. Check Railway logs for webhook errors
4. Test webhook manually in PayPal Developer Dashboard

---

### **Payment Succeeds but Job Not Starting**

**Problem:** Webhook received but job doesn't process

**Solutions:**
1. Check Railway logs: `railway logs | grep webhook`
2. Verify database has job record
3. Check Redis queue: `redis-cli -h <railway-redis> LLEN rq:queue:translate`
4. Verify worker is running: `railway logs | grep "rq worker"`

---

### **PayPal Account Limitations**

**Problem:** Account limited or restricted

**Common reasons:**
- Unverified email
- Unlinked bank account
- Incomplete identity verification
- Sudden high volume (if you go viral)

**Solution:**
1. Complete all verification steps
2. Link bank account
3. Add credit card as backup
4. Contact PayPal support if needed

---

## 📞 Support Resources

### **PayPal Help**
- **Developer Support:** https://developer.paypal.com/support/
- **Business Support:** https://www.paypal.com/au/smarthelp/contact-us
- **Phone (AU):** 1800 073 263

### **Documentation**
- **REST API Docs:** https://developer.paypal.com/docs/api/overview/
- **Webhooks Guide:** https://developer.paypal.com/docs/api-basics/notifications/webhooks/
- **Testing Guide:** https://developer.paypal.com/tools/sandbox/

---

## ✅ Post-Setup Checklist

Once PayPal is live:

- [ ] Remove "Skip Payment (Test)" button from frontend
- [ ] Update frontend to show only PayPal button
- [ ] Add PayPal logo to payment page
- [ ] Update pricing page with PayPal fee disclosure
- [ ] Monitor first 10 transactions closely
- [ ] Set up bank account for automatic withdrawals
- [ ] Enable two-factor authentication on PayPal account

---

## 🎯 Quick Reference

### **Your PayPal URLs:**
- **Dashboard:** https://www.paypal.com/myaccount/summary
- **Developer Portal:** https://developer.paypal.com/dashboard
- **Webhook Management:** https://developer.paypal.com/dashboard/webhooks
- **Transactions:** https://www.paypal.com/activity

### **Your Backend Endpoints:**
- **Webhook:** https://api.polytext.site/webhook/paypal
- **Create Payment:** https://api.polytext.site/api/paypal/create-payment
- **Execute Payment:** https://api.polytext.site/api/paypal/execute-payment

### **Railway Variables to Set:**
```bash
PAYPAL_CLIENT_ID=<from_step_2>
PAYPAL_CLIENT_SECRET=<from_step_2>
PAYPAL_WEBHOOK_ID=<from_step_3>
PAYPAL_ENVIRONMENT=live
```

---

## 🚀 Timeline

**Day 1:** Create PayPal Business account (~30 minutes)
**Day 1-3:** Wait for verification (1-3 business days)
**Day 3:** Get API credentials (~10 minutes)
**Day 3:** Create webhook (~5 minutes)
**Day 3:** Update Railway variables (~5 minutes)
**Day 3:** Test payment flow (~30 minutes)

**Total active time:** ~1.5 hours
**Total calendar time:** 1-3 business days

---

## 💡 Pro Tips

1. **Start Small:** Test with $0.50 payment first
2. **Monitor Closely:** Watch first 10 transactions carefully
3. **Keep Records:** Export transaction history monthly for taxes
4. **Set Alerts:** Enable email notifications for all transactions
5. **Plan for Scale:** PayPal can handle high volume once verified
6. **Tax Compliance:** Consult accountant for GST/income tax on payments

---

**Questions?** Check [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) or PayPal's support resources above.
