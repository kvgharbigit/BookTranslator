# Railway Production Setup Guide

## Current Status of Your Variables

### ✅ Already Correct
All these are set and correct:
- `FRONTEND_URL="https://www.polytext.site"` ← **Critical for redirects**
- All R2 Storage credentials
- Email (Resend) credentials
- All processing limits and configuration
- Database and Redis (auto-referenced)

### ⚠️ Missing Variables (Non-Critical)

Add these in Railway Dashboard:

1. **MICROPAYMENTS_THRESHOLD_CENTS**
   - Value: `800`
   - Purpose: Threshold for PayPal micropayments pricing

2. **LOG_LEVEL**
   - Value: `info`
   - Purpose: Logging verbosity

### 🔴 Critical Issue: PayPal Configuration

Your PayPal variables are currently set to **fake/test values**:
```
PAYPAL_CLIENT_ID="fake_paypal_client_id"
PAYPAL_CLIENT_SECRET="fake_paypal_secret"
PAYPAL_WEBHOOK_ID="fake_webhook_id"
PAYPAL_ENVIRONMENT="sandbox"
```

**This means your production app CANNOT process real payments!**

---

## How to Fix: Railway Dashboard Method

### Step 1: Add Missing Variables

1. Go to: https://railway.app/dashboard
2. Select your **BookTranslator** project
3. Click on your **API service** (the worker)
4. Click **Variables** tab
5. Click **+ New Variable**
6. Add these two:

   **Variable 1:**
   - Name: `MICROPAYMENTS_THRESHOLD_CENTS`
   - Value: `800`

   **Variable 2:**
   - Name: `LOG_LEVEL`
   - Value: `info`

7. Click **Save**

### Step 2: Change Provider to Gemini (Recommended)

Still in Variables tab:

1. Find `PROVIDER`
2. Change value from `groq` to `gemini`
3. Save

**Why?** Your code comments say "ALWAYS use Gemini for full book translations (best quality)". Groq is only for testing.

### Step 3: Get Real PayPal Credentials

**You need a PayPal Business Account to accept payments.**

#### Option A: Already Have PayPal Business Account

1. Go to: https://developer.paypal.com/dashboard/
2. Log in with your PayPal Business Account
3. Click **Apps & Credentials**
4. Select **Live** tab (NOT Sandbox)
5. Create a new app or use existing app
6. Copy:
   - **Client ID**
   - **Secret** (click "Show" to reveal)

7. Set up Webhook:
   - Go to **Webhooks** in left sidebar
   - Click **Add Webhook**
   - Webhook URL: `https://api.polytext.site/api/paypal/webhook`
   - Select events:
     - `PAYMENT.CAPTURE.COMPLETED`
     - `PAYMENT.CAPTURE.DENIED`
   - Save and copy the **Webhook ID**

#### Option B: Don't Have PayPal Business Account Yet

1. Sign up at: https://www.paypal.com/business
2. Complete business account setup
3. Verify your account
4. Then follow Option A steps

### Step 4: Update PayPal Variables in Railway

Back in Railway Variables tab:

1. Find `PAYPAL_CLIENT_ID` → Update to your real Client ID
2. Find `PAYPAL_CLIENT_SECRET` → Update to your real Secret
3. Find `PAYPAL_WEBHOOK_ID` → Update to your real Webhook ID
4. Find `PAYPAL_ENVIRONMENT` → Change from `sandbox` to `live`
5. Save

**Railway will automatically redeploy with new credentials.**

---

## Alternative: Keep Test Mode (Not Recommended for Production)

If you want to test without real PayPal for now:

**No changes needed** - but users won't be able to make real payments. The app will work for free translations only.

---

## Verification

After setting up PayPal:

1. Wait for Railway to redeploy (~2 minutes)
2. Go to https://www.polytext.site
3. Upload a book and try to pay
4. Payment should go through PayPal
5. Check PayPal dashboard for transaction

---

## Summary of Changes

### To Add:
```
MICROPAYMENTS_THRESHOLD_CENTS=800
LOG_LEVEL=info
```

### To Change:
```
PROVIDER=gemini  # Change from "groq"
PAYPAL_CLIENT_ID=<your_real_client_id>
PAYPAL_CLIENT_SECRET=<your_real_secret>
PAYPAL_WEBHOOK_ID=<your_real_webhook_id>
PAYPAL_ENVIRONMENT=live  # Change from "sandbox"
```

---

## Security Notes

- ✅ Never commit PayPal credentials to git
- ✅ Only set these in Railway dashboard
- ✅ Use LIVE credentials, not sandbox, for production
- ✅ Keep your PayPal Secret secure
- ✅ Webhook URL must be: `https://api.polytext.site/api/paypal/webhook`
