"""
Exhibitors scraper for ModeMonline.com
Collect exhibitor brands from each tradeshow's Mini Website.
"""
import csv
import re
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict

from scrapers.base_scraper import BaseScraper
from config.settings import REGION_MAPPING, TARGET_REGIONS
from utils.data_cleaner import clean_text


class ExhibitorsScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.tradeshows_csv = Path('data/processed/tradeshows.csv')

    def load_tradeshow_sites(self) -> List[Dict[str, str]]:
        sites = []
        if not self.tradeshows_csv.exists():
            print(f"Tradeshows file not found: {self.tradeshows_csv}")
            return sites
        with self.tradeshows_csv.open('r', encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                mini = row.get('mini_website_url', '').strip()
                src = row.get('source_url', '').strip()
                sites.append({
                    'event_name': row.get('event_name',''),
                    'mini_url': mini,
                    'source_url': src,
                    'city': row.get('city',''),
                    'country': row.get('country',''),
                    'region': row.get('region','')
                })
        print(f"Loaded {len(sites)} tradeshow mini sites")
        return sites

    def scrape_exhibitors_for_site(self, site: Dict[str, str]) -> List[Dict[str, str]]:
        """Try mini site first, then fallback to source_url. Returns list of exhibitor records."""
        event_name = site.get('event_name', '')
        urls_to_try = []
        if site.get('mini_url'):
            urls_to_try.append(site.get('mini_url'))
        if site.get('source_url') and site.get('source_url') not in urls_to_try:
            urls_to_try.append(site.get('source_url'))

        records: List[Dict[str,str]] = []

        for url in urls_to_try:
            if not url:
                continue
            print(f"\nScraping exhibitors for: {event_name} -> {url}")
            page = self.new_page()
            try:
                page.goto(url, wait_until='networkidle', timeout=60000)
                
                # Handle cookie consent if present
                self.handle_cookie_consent(page)
                
                time.sleep(3)

                # If there is a link to 'Exhibitors' page internally, click or navigate to it
                try:
                    link = page.locator('a:has-text("Exhibitors")').first
                    if link and link.count() > 0 and link.is_visible():
                        href = link.get_attribute('href')
                        if href and not href.startswith('http'):
                            href = (url.rstrip('/') + '/' + href.lstrip('/'))
                        if href:
                            page.goto(href, wait_until='networkidle', timeout=60000)
                            time.sleep(2)
                        else:
                            link.click()
                            time.sleep(2)
                except Exception:
                    pass

                links = page.locator('a:has-text("Mini Website")').all()
                print(f"Found {len(links)} potential exhibitor entries on {url}")

                for i, lnk in enumerate(links, 1):
                    try:
                        parent = None
                        try:
                            tr = lnk.locator('xpath=ancestor::tr[1]')
                            if tr.count() > 0:
                                parent = tr
                        except Exception:
                            pass
                        if not parent:
                            try:
                                div = lnk.locator('xpath=ancestor::div[contains(@class, "row") or contains(@class, "col")][1]')
                                if div.count() > 0:
                                    parent = div
                            except Exception:
                                pass
                        if not parent:
                            parent = lnk.locator('xpath=..')

                        text = parent.text_content() if parent else ''
                        href = lnk.get_attribute('href')
                        exhibitor_url = f"https://www.modemonline.com{href}" if href and href.startswith('/') else (href or url)

                        rec = self.parse_exhibitor_text(text)
                        if not rec:
                            continue
                        # enrich
                        rec.update({
                            'lead_type': 'Exhibitor',
                            'source_tradeshow': event_name,
                            'tradeshow_url': url,
                            'exhibitor_source_url': exhibitor_url,
                            'scraped_at': datetime.now().isoformat()
                        })
                        # region filter
                        if rec.get('region') in TARGET_REGIONS:
                            records.append(rec)
                    except Exception as e:
                        if i <= 3:
                            print(f"  Warn: failed entry #{i}: {e}")
                        continue

                page.close()
                if records:
                    print(f"Extracted {len(records)} exhibitors for {event_name} from {url}")
                    return records
            except Exception as e:
                print(f"  ERROR scraping tradeshow page {url}: {e}")
                try:
                    page.close()
                except Exception:
                    pass
                continue

        # No exhibitors found on mini or source pages
        print(f"No exhibitors found on mini or source pages for {event_name}")
        return []

    def parse_exhibitor_text(self, text: str) -> Dict[str, str]:
        try:
            s = ' '.join(text.split())
            s = s.replace('’', "'")
            # name: before '* Mini Website' or fallback to trailing capitalized chunk
            name = None
            m = re.search(r'^([^\*\[]+?)(?:\s*\*\s*Mini\s*Website|\s*\[|\s+Women\'s|\s+Men\'s|\s+M\'s/W\'s|\s+from\s+[A-Z])', s)
            if m:
                name = clean_text(m.group(1))
            if not name or name.lower().startswith('sales campaign') or len(name) < 2:
                tail = re.findall(r'([A-Z][A-Za-z0-9&\'\.\-]+(?:\s+[A-Z][A-Za-z0-9&\'\.\-]+){0,4})\s*$', s)
                if tail:
                    name = clean_text(tail[-1])
            if not name:
                return {}

            # city
            primary_city = 'N/A'
            for c in ['Paris','Milan','London','New York','Tokyo','Shanghai','Berlin','Düsseldorf','Munich','Florence','Seoul','Hong Kong','Copenhagen','Istanbul']:
                if c in s:
                    primary_city = c
                    break
            city_map = {'Milano':'Milan','Firenze':'Florence'}
            primary_city = city_map.get(primary_city, primary_city)

            # contacts
            email_m = re.search(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', s)
            email = email_m.group(0) if email_m else ''
            phone_m = re.search(r'(?:P\s*:|Mobile:)?\s*(\+?[\d\s\(\)\-]{10,})', s)
            phone = clean_text(phone_m.group(1)) if phone_m else ''
            web_m = re.search(r'(?:https?://|www\.)[\w\.-]+\.[a-z]{2,}(?:/[^\s<"]*)?', s, re.IGNORECASE)
            website = web_m.group(0) if web_m else ''
            insta_m = re.search(r'instagram\.com/([A-Za-z0-9_\.]+)|@([A-Za-z0-9_\.]+)', s, re.IGNORECASE)
            instagram = f"@{insta_m.group(1) or insta_m.group(2)}" if insta_m else ''

            # country/region
            country = self.get_country_from_city(primary_city) if primary_city and primary_city != 'N/A' else ''
            region = REGION_MAPPING.get(country, 'Other') if country else 'Other'

            return {
                'company_name': name,
                'city': primary_city if primary_city else '',
                'country': country,
                'region': region,
                'email': email,
                'phone': phone,
                'website': website,
                'instagram': instagram
            }
        except Exception:
            return {}

    def save_exhibitors(self, recs: List[Dict[str,str]]):
        out = Path('data/processed/exhibitors.csv')
        self.save_to_csv(recs, str(out))
        print(f"Saved {len(recs)} exhibitors to {out}")

    def get_country_from_city(self, city: str) -> str:
        map_ = {
            'Paris': 'France', 'Milan': 'Italy', 'London': 'United Kingdom', 'Florence': 'Italy',
            'New York': 'United States', 'Tokyo': 'Japan', 'Shanghai': 'China', 'Berlin': 'Germany',
            'Düsseldorf': 'Germany', 'Munich': 'Germany', 'Seoul': 'South Korea', 'Hong Kong': 'Hong Kong',
            'Istanbul': 'Turkey', 'Copenhagen': 'Denmark'
        }
        return map_.get(city, '')

    def run(self):
        print("Starting exhibitors scraper")
        self.start_browser()
        all_recs: List[Dict[str,str]] = []
        sites = self.load_tradeshow_sites()
        # Process only first N sites to avoid long runs during iteration; can be increased later
        max_sites = 10
        for site in sites[:max_sites]:
            recs = self.scrape_exhibitors_for_site(site)
            all_recs.extend(recs)
            time.sleep(self.delay)

        # Dedupe by (company_name, website or email)
        seen = set()
        deduped = []
        for r in all_recs:
            key = (r.get('company_name','').strip().lower(), (r.get('website') or '').strip().lower(), (r.get('email') or '').strip().lower())
            if not r.get('company_name') or key in seen:
                continue
            seen.add(key)
            deduped.append(r)

        self.save_exhibitors(deduped)
        print(f"Exhibitors scraping complete. Total: {len(deduped)}")
        self.stop_browser()


if __name__ == "__main__":
    ExhibitorsScraper().run()
