# Fashion Scraper (MVP)

Minimal scaffold for the ModeMonline fashion lead scraper.

Overview
- Python 3.9+
- Playwright for dynamic pages
- Outputs CSVs in `data/processed`

Runs
- The scraper will be scheduled to run every 2 days (cron/scheduler to be added later).

Quick start (local, development)
1. Create a virtualenv and activate it.
2. pip install -r requirements.txt
3. playwright install chromium
4. Run targeted scrapers via `main.py` (TBD)

Robots.txt
- Before running, the scaffold checks `https://www.modemonline.com/robots.txt` to confirm allowed scraping.

Notes
- Database storage deferred to later phases; CSV outputs are used for MVP.
- Social media handles (Instagram/LinkedIn/Facebook) are included as optional fields in `master_leads.csv`.
