# Cloudflare R2 Setup Guide (5-Day Retention)

✅ **STATUS: COMPLETED AND TESTED (November 2, 2025)**
- All steps completed successfully
- End-to-end integration test passed (7/7 tests)
- Public download URLs confirmed working
- See `R2_INTEGRATION_TEST_RESULTS.md` for test results

## Step 1: Create Cloudflare R2 Account

### 1.1 Sign up for Cloudflare
1. Go to https://dash.cloudflare.com/sign-up
2. Create a free account (no credit card required initially)
3. Verify your email

### 1.2 Enable R2
1. In Cloudflare Dashboard, go to **R2** in the left sidebar
2. Click **"Enable R2"**
3. Add payment method (required for R2, but you'll stay well under free tier limits)
   - They won't charge unless you exceed $0 threshold

## Step 2: Create R2 Bucket

### 2.1 Create Bucket
1. Click **"Create bucket"**
2. Bucket name: `epub-translator-production`
3. Location: Choose closest to your users (e.g., `APAC` for Australia, `WNAM` for US)
4. Click **"Create bucket"**

### 2.2 Configure CORS (Important!)
1. Go to your bucket → **Settings** → **CORS Policy**
2. Click **"Add CORS Policy"**
3. Paste this configuration:

```json
[
  {
    "AllowedOrigins": ["*"],
    "AllowedMethods": ["GET", "PUT", "POST"],
    "AllowedHeaders": ["*"],
    "ExposeHeaders": ["ETag"],
    "MaxAgeSeconds": 3600
  }
]
```

**Note:** After you set up your custom domain, replace `"*"` with your actual domain:
```json
"AllowedOrigins": ["https://yourdomain.com"]
```

### 2.3 Set Up 5-Day Lifecycle Policy
1. In your bucket, go to **Settings** → **Object lifecycle rules**
2. Click **"Create lifecycle rule"**
3. Configure:
   - **Rule name:** `delete-after-5-days`
   - **Scope:** Apply to all objects in bucket
   - **Action:** Delete objects
   - **Days after object creation:** `5`
4. Click **"Create rule"**

This will automatically delete files 5 days after upload.

## Step 3: Generate API Credentials

### 3.1 Create API Token
1. Go to **R2** → **Manage R2 API Tokens**
2. Click **"Create API token"**
3. Configure:
   - **Token name:** `epub-translator-api`
   - **Permissions:**
     - ✅ Object Read & Write
     - ✅ Admin Read & Write (for lifecycle management)
   - **Bucket scope:** Select `epub-translator-production`
   - **TTL:** No expiration
4. Click **"Create API token"**

### 3.2 Save Credentials
⚠️ **IMPORTANT:** Copy these immediately - they won't be shown again!

You'll get:
- **Access Key ID:** `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
- **Secret Access Key:** `yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy`
- **Endpoint:** `https://<ACCOUNT_ID>.r2.cloudflarestorage.com`

Save these in a secure location (password manager).

### 3.3 Find Your Account ID
1. Go to **R2** → **Overview**
2. Copy your **Account ID** (shown in the right panel)
   - Format: `1234567890abcdef1234567890abcdef`

## Step 4: Configure Railway Environment Variables

### 4.1 Update Railway Variables
Run these commands (replace with your actual values):

```bash
# Navigate to your project
cd /Users/kayvangharbi/PycharmProjects/BookTranslator/apps/api

# Set R2 credentials (replace with actual values)
railway variables set R2_ACCOUNT_ID=your_account_id_here
railway variables set R2_ACCESS_KEY_ID=your_access_key_here
railway variables set R2_SECRET_ACCESS_KEY=your_secret_key_here
railway variables set R2_BUCKET=epub-translator-production
railway variables set R2_REGION=auto
railway variables set SIGNED_GET_TTL_SECONDS=432000
```

**Note:** `SIGNED_GET_TTL_SECONDS=432000` = 5 days in seconds (5 × 24 × 60 × 60)

### 4.2 Verify Variables Set
```bash
railway variables | grep R2
```

You should see all 5 variables listed.

## Step 5: Update Local Environment (Optional)

If you want to test R2 locally:

### 5.1 Update `.env.local`
```bash
# R2 Production Storage
R2_ACCOUNT_ID=your_account_id_here
R2_ACCESS_KEY_ID=your_access_key_here
R2_SECRET_ACCESS_KEY=your_secret_key_here
R2_BUCKET=epub-translator-production
R2_REGION=auto
SIGNED_GET_TTL_SECONDS=432000
```

### 5.2 Keep Fake for Local Testing
Alternatively, keep fake credentials to use local storage for development:
```bash
# This uses local filesystem storage
R2_ACCOUNT_ID=fake_account_id
```

## Step 6: Test R2 Integration

### 6.1 Deploy to Railway
```bash
# Trigger redeployment with new env vars
railway up
```

### 6.2 Test File Upload
1. Go to your Railway URL
2. Upload a test EPUB
3. Check Cloudflare R2 dashboard → Your bucket → **Objects**
4. Verify file appears in `uploads/` folder

### 6.3 Test Translation & Download
1. Run a translation (skip payment for testing)
2. Check R2 for output files in `outputs/` folder
3. Try downloading the files
4. Verify download URLs work

### 6.4 Verify Lifecycle Policy (Wait 5 Days)
After 5 days, check that old files are automatically deleted.

## Step 7: Cost Monitoring

### 7.1 Set Up Billing Alerts
1. Cloudflare Dashboard → **Billing** → **R2**
2. Enable email alerts for:
   - Storage exceeds 1GB
   - Monthly costs exceed $1

### 7.2 Monitor Usage
Check regularly:
- **Storage:** Cloudflare Dashboard → R2 → Overview
- **Requests:** Check operations count
- **Cost:** Should be ~$0.01-0.05/month with 5-day retention

## Troubleshooting

### Files Not Uploading
- Check CORS configuration
- Verify API credentials are correct
- Check Railway logs: `railway logs`

### Downloads Not Working
- Ensure presigned URLs are enabled
- Check `SIGNED_GET_TTL_SECONDS` is set
- Verify bucket is not set to private-only

### Lifecycle Not Deleting Files
- Wait full 5 days (deletions happen once per day)
- Check lifecycle rule is active
- Verify rule applies to all objects

## Security Best Practices

### 8.1 Restrict API Token (After Testing)
1. Once working, create a new token with minimal permissions
2. Remove **Admin** access, keep only **Object Read & Write**
3. Rotate credentials every 90 days

### 8.2 Domain-Specific CORS
After setting up custom domain, update CORS:
```json
"AllowedOrigins": ["https://yourdomain.com"]
```

### 8.3 Never Commit Credentials
Ensure `.env` and `.env.local` are in `.gitignore`:
```bash
# Check they're ignored
git status
```

## Expected Costs (5-Day Retention)

### Low Volume (100 translations/month)
- Storage: ~30GB max (5 days × 6GB/day)
- Cost: **$0.45/month**

### Medium Volume (1,000 translations/month)
- Storage: ~300GB max (5 days × 60GB/day)
- Cost: **$4.50/month**

### High Volume (10,000 translations/month)
- Storage: ~3TB max (5 days × 600GB/day)
- Cost: **$45/month**

**Bandwidth:** Always FREE! 🎉

## Next Steps

After R2 is working:
1. ✅ Test with real EPUBs
2. ✅ Monitor costs for first week
3. ✅ Set up custom domain (optional)
4. ✅ Configure email notifications for expiring downloads
5. ✅ Add "Downloads expire in 5 days" notice to UI

---

**Need Help?**
- Cloudflare R2 Docs: https://developers.cloudflare.com/r2/
- Cloudflare Support: https://dash.cloudflare.com/?to=/:account/support
