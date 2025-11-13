# Fashion Scraper - ModeMonline Lead Generator

A comprehensive web scraper for extracting fashion industry leads (brands, showrooms, tradeshows, contacts) from modemonline.com.

## 📊 Project Status & Achievements

### ✅ Completed (Tier 1 - High Quality Leads)
- ✅ **244 unique leads** in `data/processed/master_leads.csv`
  - 110 designer brands/showrooms
  - 48 multi-label showrooms
  - 84 press office contacts (from showroom data)
  - 89% phone coverage, 41% Instagram coverage
- ✅ **24 tradeshows** in `data/processed/tradeshows.csv`
- ✅ **110 brands** in `data/processed/brands.csv`
- ✅ **84 PR contacts** in `data/processed/pr_contacts.csv`
- ✅ **Robust deduplication** (28% duplicate removal rate)
- ✅ **Cookie consent handler** (Cookiebot, OneTrust, generic patterns)
- ✅ **Git repository** at https://github.com/vihaankulkarni29/references

### ⚠️ Known Limitations
- **NO ASIA DATA**: modemonline.com has zero Asia showroom/brand content
  - Checked: Tokyo, Seoul, Shanghai, Hong Kong, Singapore, Mumbai, Delhi, Bangkok
  - All showroom pages return empty (0 results)
  - Asia tradeshows mentioned but no exhibitor/brand lists available
- **NO TRADESHOW DATES**: Mini-sites don't include event schedules (0/24 dates populated)
  - Date enrichment infrastructure built with 5 regex patterns
  - External link following implemented
  - Source limitation: Pages lack date information
- **NO DEDICATED PR SECTIONS**: Mini-sites don't have press office pages
  - Pragmatic solution: Repurposed showroom contacts (phone numbers) as potential PR leads
  - 84 PR contacts extracted (100% phone coverage, 0% email)
- **Geographic coverage**: 100% Europe (France: 101, Italy: 53, UK: 5, Germany: 1)
- **Brand target**: Delivered 110 brands vs. 500 target (external sources needed for gap)
- **Email coverage**: Very low (0.6%) - most leads have phone/Instagram only

---

## 🚀 Quick Start (Windows PowerShell)

### Prerequisites
- Python 3.13+ (tested with 3.13)
- Git
- Windows PowerShell

### 1. Clone & Setup
```powershell
cd C:\Users\<YourName>\Desktop\references
git clone https://github.com/vihaankulkarni29/references.git
cd references\fashion-scraper

# Create virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### 2. Run Scrapers

**All commands must be run from the `fashion-scraper` directory:**

```powershell
# Ensure you're in the correct directory
cd C:\Users\Vihaan\Desktop\references\fashion-scraper

# Run individual scrapers
.\.venv\Scripts\python.exe -m scrapers.tradeshows
.\.venv\Scripts\python.exe -m scrapers.showrooms
.\.venv\Scripts\python.exe -m scrapers.designer_showrooms
.\.venv\Scripts\python.exe -m scrapers.fashion_weeks

# Run merge utility to create master_leads.csv
.\.venv\Scripts\python.exe -m utils.merge_leads

# Extract brands from existing data
.\.venv\Scripts\python.exe -m utils.extract_brands
```

### 3. Email Enrichment (Optional - Requires Apollo.io API)

**Enrich leads with professional email addresses:**

```powershell
# 1. Get Apollo.io API key (free tier: 50 credits/month)
#    Sign up at: https://app.apollo.io/sign-up
#    Get API key: https://app.apollo.io/#/settings/integrations/api

# 2. Create .env file with your API key
cp .env.example .env
# Edit .env and add: APOLLO_API_KEY=your_key_here

# 3. Run email enrichment
python email_enricher.py

# Output: data/enriched/master_leads_enriched.csv
```

**💡 See [EMAIL_ENRICHMENT_GUIDE.md](EMAIL_ENRICHMENT_GUIDE.md) for detailed setup, troubleshooting, and best practices.**

```

---

## 📁 Data Schema

### `master_leads.csv` (160 records)
Primary consolidated dataset with deduplication.

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `lead_type` | string | Type of lead | "Designer Showroom", "Multi-Label Showroom" |
| `company_name` | string | Brand or showroom name | "Chanel", "Galeries Lafayette" |
| `description` | string | Categories or description | "Womenswear, Accessories" |
| `email` | string | Email contact | "info@brand.com" or "N/A" |
| `phone` | string | Phone number | "+33 1 23 45 67 89" |
| `website` | string | Website URL | "www.brand.com" or "N/A" |
| `instagram` | string | Instagram handle/URL | "@brandname" or "N/A" |
| `facebook` | string | Facebook page URL | "facebook.com/brand" or "N/A" |
| `city` | string | City location | "Paris", "Milan" |
| `country` | string | Country | "France", "Italy" |
| `region` | string | Geographic region | "Europe" (no Asia data) |
| `source` | string | Data source | "showrooms", "designer_showrooms" |
| `source_url` | string | Original page URL | Full modemonline.com URL |
| `scraped_date` | date | Date scraped | "2025-11-13" |
| `merged_at` | datetime | Merge timestamp | "2025-11-13 12:59:27" |

### `brands.csv` (110 records)
Deduplicated brand list extracted from showrooms.

| Field | Description |
|-------|-------------|
| `brand_id` | Unique hash ID (12 chars) |
| `brand_name` | Brand/designer name |
| `categories` | Product categories |
| `city`, `country`, `region` | Geographic data |
| `phone`, `email`, `website`, `instagram`, `facebook` | Contact info |
| `source`, `source_url` | Origin tracking |
| `scraped_date` | Extraction date |

### `tradeshows.csv` (24 records)
Fashion tradeshows and events.

| Field | Description |
|-------|-------------|
| `event_id` | Unique hash ID |
| `event_name` | Tradeshow name (e.g., "Centrestage", "Coterie") |
| `event_type` | Always "Tradeshow" |
| `start_date`, `end_date` | All "N/A" (mini-sites lack date info, source limitation) |
| `city`, `country`, `region` | Event location |
| `source_url` | Original listing page |
| `mini_website_url` | Event detail page (if available) |
| `scraped_date` | Extraction date |

**Note**: Date enrichment infrastructure complete (5 regex patterns, external link following), but modemonline.com mini-sites don't include event schedules.

### `pr_contacts.csv` (84 records)
Press office contacts extracted from showroom data.

| Field | Description |
|-------|-------------|
| `lead_type` | Always "Press Office" |
| `company_name` | Brand/showroom name |
| `description` | "Brand Contact (potential PR)" |
| `email` | Email address (N/A for all - not available on mini-sites) |
| `phone` | Phone number (100% coverage - +33, +39 international formats) |
| `website`, `instagram`, `facebook` | Web presence |
| `city`, `country`, `region` | Geographic data (France: 45, Italy: 38, Germany: 1) |
| `source` | "designer_showrooms_contacts" |
| `scraped_date` | Extraction date |

**Note**: Mini-sites don't have dedicated PR sections. Pragmatic approach: repurposed showroom contacts with email/phone as PR leads.

### `designer_showrooms.csv` (119 records - raw)
Unmerged designer showroom data (before deduplication).

---

## 🛠️ Architecture

### Base Classes
- **BaseScraper** (`scrapers/base_scraper.py`): 
  - Playwright browser lifecycle management
  - Cookie consent handler (`handle_cookie_consent()`)
  - Retry logic with exponential backoff
  - CSV save helpers (utf-8-sig encoding for Excel)

### Scrapers
1. **tradeshows.py**: Extracts tradeshows from `/fashion-weeks/*/digital/extra/tradeshows`
   - Date enrichment: 5 regex patterns (Month D1-D2 YYYY, ISO, etc.), external link following
   - Result: 24 tradeshows, 0 dates populated (source limitation)
2. **showrooms.py**: Multi-label showrooms from fashion week pages
3. **designer_showrooms.py**: Designer showrooms from 6 seasons
4. **brands.py**: Brand extraction with region filtering
5. **pr_contacts.py**: Press office contact extraction
   - Strategy: Repurpose showroom contacts (phone numbers) as PR leads
   - Result: 84 PR contacts with 100% phone coverage
4. **fashion_weeks.py**: Fashion week events metadata

### Utilities
1. **merge_leads.py**: Deduplicates and merges all lead sources
   - Normalization: lowercase, strip "Showroom"/"Sales Department", remove social suffixes
   - Dedupe key: `(normalized_name, city, email_or_website)`
   - Intelligent field merging (prefer non-empty, longer values)

2. **extract_brands.py**: Extracts unique brands from showrooms
   - Filters noisy names ("Instagram", "Sales Department")
   - Cross-references designer_showrooms + master_leads

---

## 🔧 Troubleshooting

### "Module not found" errors
**Cause**: Running from wrong directory or venv not activated.
```powershell
# Always run from repo root
cd C:\Users\Vihaan\Desktop\references\fashion-scraper

# Use full path to Python if needed
C:\Users\Vihaan\Desktop\references\fashion-scraper\.venv\Scripts\python.exe -m scrapers.tradeshows
```

### Empty results (0 records)
**Known issues**:
- Press offices page: Returns 57 bytes (empty)
- Multilabel stores page: Empty
- Fashion brands alphabet pages: No data
- Asia showroom pages: All return 0 results
- Exhibitor lists from tradeshows: Mini-sites have no exhibitor data

**Solution**: Focus on working sources (designer_showrooms, existing showrooms, tradeshows metadata).

### Playwright browser errors
```powershell
# Reinstall browsers
playwright install chromium

# If still fails, check headless mode
# In scraper code: BaseScraper(headless=False)  # Opens visible browser
```

### CSV encoding issues (Excel shows gibberish)
**Fixed**: All CSVs use `utf-8-sig` encoding (adds BOM for Excel compatibility).

---

## 📋 Development Workflow

### Adding a New Scraper
1. Create `scrapers/my_scraper.py` inheriting from `BaseScraper`
2. Implement required methods:
   - `get_list_page_urls()` - URLs to scrape
   - `scrape_list_page(page, url)` - Extract items from list
   - `run()` - Main orchestration
3. Add cookie consent call: `self.handle_cookie_consent(page)`
4. Save to CSV: `self.save_to_csv(data, 'data/processed/output.csv')`

### Git Workflow
```powershell
git add -A
git commit -m "Add feature X"
git push origin main
```

---

## 🎯 Future Work

### High Priority
1. **Todo 3**: Parse tradeshow dates (currently all "N/A")
2. **Todo 6**: Extract PR contacts from mini-sites
3. **External sources**: Find Asia brand databases (modemonline has none)
4. **Data quality**: Filter noisy company names, improve phone/email parsing

### Medium Priority
- Incremental scraping (avoid re-scraping existing data)
- Rate limiting improvements
- Error logging and monitoring
- Schedule automation (cron/Task Scheduler)

### Low Priority
- Database migration (currently CSV-based)
- API wrapper for querying leads
- Web dashboard for lead management

---

## 📊 Data Quality Notes

### Contact Coverage (master_leads.csv)
- ✅ Phone: 89% (143/160)
- ⚠️ Instagram: 41% (66/160)
- ❌ Email: 0.6% (1/160) - very low

### Known Data Issues
1. **Noisy company names**: Some records have "Instagram", "Facebook Instagram", "Sales Department" as names
   - Filtered in brand extractor but present in raw data
2. **Partial phone numbers**: Some phones like "01 2025", "26 2025" (missing country/area code)
3. **Missing emails**: Most showrooms don't provide email addresses publicly
4. **No Asia coverage**: Geographic limitation of modemonline.com

### Geographic Distribution
- Paris: 63% (101/160)
- Milan: 33% (53/160)
- London: 3% (5/160)
- Düsseldorf: 1% (1/160)
- **Asia: 0%** ⚠️

---

## 📞 Support

**Repository**: https://github.com/vihaankulkarni29/references  
**Branch**: main  
**Python Version**: 3.13  
**Playwright Version**: 1.55.0

For issues, check `COMPLETED_TODO_*.md` files for implementation details and lessons learned.

---

## 📄 License

This project is for educational/research purposes. Respect modemonline.com's robots.txt and terms of service.
