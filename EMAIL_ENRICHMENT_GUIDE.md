# Email Enrichment Setup Guide

## Overview
The email enrichment module uses the Apollo.io API to find professional email addresses for companies in your `master_leads.csv` file.

## Prerequisites
- Python 3.13+ with virtual environment activated
- Apollo.io account (free tier: 50 credits/month)
- All dependencies installed from `requirements.txt`

## Step 1: Get Apollo.io API Key

1. **Sign up for Apollo.io**:
   - Visit: https://app.apollo.io/sign-up
   - Create a free account (no credit card required for free tier)

2. **Get your API key**:
   - Log in to Apollo.io
   - Navigate to: https://app.apollo.io/#/settings/integrations/api
   - Copy your API key

3. **Understand rate limits**:
   - Free tier: 50 credits/month
   - Each API call = 1 credit
   - Paid plans: 10,000+ credits/month
   - Rate limit: 1 request/second (built into script)

## Step 2: Configure Environment Variables

1. **Copy the example file**:
   ```powershell
   cp .env.example .env
   ```

2. **Edit `.env` file**:
   ```
   APOLLO_API_KEY=your_actual_api_key_here
   ```
   Replace `your_actual_api_key_here` with your Apollo.io API key

3. **Verify `.env` is in `.gitignore`**:
   - ✅ Already configured - your API key will NEVER be committed to Git

## Step 3: Run Email Enrichment

### Option A: Enrich All Leads (160 leads)
```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Run enrichment
python email_enricher.py
```

**Estimated time**: ~3 minutes (160 leads × 1 second each)  
**API credits used**: 160 credits (requires paid plan)

### Option B: Test with Sample (Recommended First)
Create a test file with first 10 leads:

```powershell
# Read first 10 leads into test file
python -c "import pandas as pd; df = pd.read_csv('data/processed/master_leads.csv', encoding='utf-8-sig').head(10); df.to_csv('data/processed/master_leads_test.csv', index=False, encoding='utf-8-sig')"

# Modify email_enricher.py to use test file
# Change line: input_file='data/processed/master_leads_test.csv'
python email_enricher.py
```

**Estimated time**: ~10 seconds  
**API credits used**: 10 credits (free tier compatible)

## Step 4: Check Results

### Output File
- **Location**: `data/enriched/master_leads_enriched.csv`
- **New column**: `email` (added to all existing columns)

### Expected Output
```
================================================================================
Email Enrichment Module v2.0
================================================================================

Loading data from data/processed/master_leads.csv...
Loaded 160 leads

Starting email enrichment via Apollo.io API...
Target: 160 companies
Rate limit: 1 request per second
Estimated time: ~2 minutes

✓ Found email for Antik Batik: contact@antikbatik.com
✓ Found email for EBIT™: info@ebitfashion.com
...

================================================================================
Enrichment Complete!
================================================================================
Total leads processed: 160
API calls made: 160
New emails found: 45
Success rate: 28.1%

Final email coverage: 45/160 (28.1%)
Output saved to: data/enriched/master_leads_enriched.csv
================================================================================
```

## Understanding Results

### Success Rate Expectations
- **Realistic rate**: 20-40% email discovery
- **Why not 100%?**:
  - Small fashion brands may not be in Apollo.io database
  - European companies less coverage than US
  - Boutique showrooms may lack online presence

### Email Quality
- ✅ **Verified emails**: Marked as `verified` by Apollo.io (deliverable)
- ⚠️ **Unverified emails**: Found but not verified (may bounce)
- ❌ **N/A**: No email found

## Troubleshooting

### Error: "APOLLO_API_KEY not found"
**Solution**: Make sure `.env` file exists and has correct format:
```
APOLLO_API_KEY=your_key_here
```
No spaces around `=`, no quotes needed.

### Error: "Rate limit exceeded" (429)
**Solution**: Script automatically waits 60 seconds and continues. If persistent:
- Check your Apollo.io dashboard for credit usage
- Upgrade to paid plan for higher limits
- Run enrichment in batches (10-50 leads at a time)

### Low Success Rate (<10%)
**Possible causes**:
1. **Free tier exhausted**: Check Apollo.io dashboard for remaining credits
2. **Network issues**: Check internet connection
3. **API key invalid**: Verify key in Apollo.io settings

**Solutions**:
- Wait for next month's credit refresh
- Upgrade to paid plan
- Try alternative enrichment sources (Hunter.io, Clearbit)

### Script Timeout
**Cause**: 160 leads × 1 second = ~3 minutes runtime  
**Solution**: Normal behavior, let it complete. Progress bar shows status.

## API Costs & Alternatives

### Apollo.io Pricing (as of Nov 2025)
| Plan | Credits/Month | Cost | Best For |
|------|---------------|------|----------|
| Free | 50 | $0 | Testing (10-50 leads) |
| Basic | 10,000 | $49/mo | Small datasets (100-500 leads) |
| Professional | 50,000 | $99/mo | Regular enrichment |

### Alternative APIs (Future)
1. **Hunter.io**: Email finder + verifier (100 searches/month free)
2. **Clearbit**: Company data enrichment ($99/mo)
3. **RocketReach**: Contact database (50 lookups/month free)

## Best Practices

### 1. Start Small
- Test with 10 leads first
- Verify output quality
- Then scale to full dataset

### 2. Monitor Credits
- Check Apollo.io dashboard regularly
- Track success rate
- Adjust strategy if rate is low

### 3. Batch Processing
If you have 500+ leads:
```python
# Modify email_enricher.py
df_batch1 = df.head(100)  # First 100
df_batch2 = df[100:200]   # Next 100
# etc.
```

### 4. Combine with Manual Lookup
For high-value leads without emails:
- Visit company website directly
- Check LinkedIn company page
- Use contact form to request PR email

## Next Steps After Enrichment

1. **Verify emails**: Use email verification service (ZeroBounce, NeverBounce)
2. **Update master_leads.csv**: Copy verified emails back
3. **Segment by email availability**:
   - Email leads → email campaigns
   - No email leads → phone/Instagram outreach

## Support

**Issues**: Check PROGRESS_REPORT.md troubleshooting section  
**API Docs**: https://apolloio.github.io/apollo-api-docs/  
**Questions**: Create issue on GitHub repository

---

*Last updated: November 13, 2025*
