"""
Designer Showrooms scraper for ModeMonline.com
Extracts individual brand showroom information from designer-showrooms pages.
"""
import re
import time
from datetime import datetime
from scrapers.base_scraper import BaseScraper
from config.settings import REGION_MAPPING, TARGET_REGIONS
from utils.data_cleaner import clean_text


class DesignerShowroomsScraper(BaseScraper):
    """Scraper for individual designer brand showrooms"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.modemonline.com/fashion/fashion-weeks"
        self.seasons = [
            "spring-summer-2026",
            "fall-winter-2025-2026",
            "spring-summer-2025",
            "fall-winter-2024-2025",
            "spring-summer-2024",
            "fall-winter-2023-2024"
        ]
        
    def get_urls_to_scrape(self):
        """Generate list of designer showroom URLs"""
        urls = []
        for season in self.seasons:
            url = f"{self.base_url}/{season}/digital/extra/designer-showrooms"
            urls.append(url)
        return urls
    
    def scrape_showroom_page(self, url):
        """Scrape a single designer showroom page using Playwright DOM selectors"""
        print(f"Scraping designer showroom page: {url}")
        try:
            page = self.new_page()
            page.goto(url, wait_until='networkidle', timeout=60000)

            # Handle cookie consent if present
            self.handle_cookie_consent(page)

            # Small wait to allow dynamic content to render
            time.sleep(5)

            showrooms = []

            # Find all "Mini Website" links (same pattern that worked for tradeshows)
            mini_links = page.locator('a:has-text("Mini Website")').all()
            print(f"Found {len(mini_links)} potential showroom entries")

            for idx, link in enumerate(mini_links, 1):
                try:
                    parent = None
                    # Try enclosing table row first
                    try:
                        tr = link.locator('xpath=ancestor::tr[1]')
                        if tr.count() > 0:
                            parent = tr
                    except Exception:
                        pass

                    # Fallback to a nearby div container
                    if not parent:
                        try:
                            div = link.locator('xpath=ancestor::div[contains(@class, "row") or contains(@class, "col")][1]')
                            if div.count() > 0:
                                parent = div
                        except Exception:
                            pass

                    # Last resort: direct parent
                    if not parent:
                        parent = link.locator('xpath=..')

                    text = parent.text_content() if parent else ''
                    href = link.get_attribute('href')
                    source_url = (
                        f"https://www.modemonline.com{href}" if href and href.startswith('/') else (href or url)
                    )

                    if text and len(text) > 30:
                        record = self.parse_showroom_text(text, source_url)
                        if record:
                            showrooms.append(record)
                            if idx <= 3:
                                # Print first few extracted for visibility
                                print(f"  Extracted: {record.get('brand_name')} – {record.get('primary_city')} ({record.get('categories')})")
                except Exception as e:
                    if idx <= 3:
                        print(f"  Warning: failed to parse entry #{idx}: {e}")
                    continue

            page.close()
            print(f"Found {len(showrooms)} designer showrooms on {url}")
            return showrooms

        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
            return []
    
    def parse_showroom_text(self, text: str, source_url: str):
        """Parse one showroom record from text content extracted from the DOM"""
        try:
            s = ' '.join(text.split())
            # Remove noisy leading sales campaign prefaces that can pollute name extraction
            s = re.sub(r'^Sales\s+campaign[^A-Z]{0,200}', '', s, flags=re.IGNORECASE)
            # Normalize common unicode apostrophes/quotes
            s = s.replace('’', "'").replace('“', '"').replace('”', '"')

            # Brand name: text before '* Mini Website' or before categories/date cues
            name = None
            m = re.search(r'^([^\*\[]+?)(?:\s*\*\s*Mini\s*Website|\s*\[|\s+Women\'s|\s+Men\'s|\s+M\'s/W\'s|\s+Sales\s+campaign|\s+from\s+[A-Z])', s)
            if m:
                name = clean_text(m.group(1))
            if not name:
                # Fallback: first capitalized chunk
                m2 = re.search(r'^([A-Z][A-Za-z0-9\s\&\'\-\.]{3,80})', s)
                name = clean_text(m2.group(1)) if m2 else ''

            # Guardrails and corrective fallback for brand name
            bad_prefix = name and name.lower().startswith('sales campaign')
            seasonish = name and re.match(r'^(ss|fw)\d{2}', name, re.IGNORECASE)
            dateish = name and re.search(r'\bfrom\s+[A-Z][a-z]+\s+\d{1,2}', name)
            if bad_prefix or seasonish or dateish:
                # Try extracting a trailing proper-case brand name from the end of the text
                tail = re.findall(r'([A-Z][A-Za-z0-9&\'\.\-]+(?:\s+[A-Z][A-Za-z0-9&\'\.\-]+){0,4})\s*$', s)
                if tail:
                    name = clean_text(tail[-1])
                    bad_prefix = seasonish = dateish = False
            # If still malformed, drop
            if (name and (name.lower().startswith('sales campaign') or re.match(r'^(ss|fw)\d{2}', name, re.IGNORECASE) or re.search(r'\bfrom\s+[A-Z][a-z]+\s+\d{1,2}', name))):
                return None
            if name and len(name) > 120:
                return None

            # Categories
            cats = re.findall(r'(Women\'s|Men\'s|M\'s/W\'s)\s+(RTW|Acc\.|Accessories)', s)
            categories = ', '.join([f"{c[0]} {c[1]}" for c in cats]) if cats else 'N/A'

            # Sales campaign dates
            sales_start = 'N/A'
            sales_end = 'N/A'
            dm = re.search(r'Sales\s+campaign\s+\w+\s+from\s+([A-Z][a-z]+\.?\s+\d{1,2}\s+\d{4})\s+to\s+([A-Z][a-z]+\.?\s+\d{1,2}\s+\d{4})', s)
            if dm:
                sales_start = self.parse_date(dm.group(1))
                sales_end = self.parse_date(dm.group(2))

            # City detection
            known_cities = ['Paris','Milan','Milano','London','New York','Florence','Firenze','Tokyo','Shanghai','Berlin','Düsseldorf','Munich','Seoul','Hong Kong','Copenhagen']
            primary_city = 'N/A'
            for c in known_cities:
                if c in s:
                    primary_city = c
                    break
            city_map = {'Milano': 'Milan', 'Firenze': 'Florence'}
            primary_city = city_map.get(primary_city, primary_city)

            # Contacts
            email_match = re.search(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', s)
            email = email_match.group(0) if email_match else 'N/A'
            phone_m = re.search(r'(?:P\s*:|Mobile:)?\s*(\+?[\d\s\(\)\-]{10,})', s)
            phone = clean_text(phone_m.group(1)) if phone_m else 'N/A'
            insta_m = re.search(r'instagram\.com/([A-Za-z0-9_\.]+)|@([A-Za-z0-9_\.]+)', s, re.IGNORECASE)
            instagram = f"@{insta_m.group(1) or insta_m.group(2)}" if insta_m else 'N/A'
            fb_m = re.search(r'facebook\.com/([A-Za-z0-9_\.]+)', s, re.IGNORECASE)
            facebook = f"facebook.com/{fb_m.group(1)}" if fb_m else 'N/A'

            # Address (best-effort)
            addr_m = re.search(r'((?:Via|Rue|Viale|Corso|Street|Avenue|Road)\s+[^\|]{5,120})', s)
            address = clean_text(addr_m.group(1))[:200] if addr_m else 'N/A'

            # Country / Region
            country = self.get_country_from_city(primary_city)
            region = REGION_MAPPING.get(country, 'Other')
            if region not in TARGET_REGIONS:
                return None

            return {
                'brand_name': name.strip(),
                'categories': categories,
                'sales_start': sales_start,
                'sales_end': sales_end,
                'primary_city': primary_city if primary_city else 'N/A',
                'all_cities': primary_city if primary_city else 'N/A',
                'country': country,
                'region': region,
                'address': address,
                'phone': phone,
                'email': email,
                'instagram': instagram,
                'facebook': facebook,
                'description': '',
                'source_url': source_url
            }
        except Exception as e:
            print(f"  Warning: parse error: {e}")
            return None
    
    def parse_date(self, date_str):
        """Parse date string to YYYY-MM-DD format"""
        try:
            date_str = clean_text(date_str)
            # Remove day name if present
            date_str = re.sub(r'^[A-Z][a-z]+\.?\s+', '', date_str)
            
            dt = datetime.strptime(date_str, '%B %d %Y')
            return dt.strftime('%Y-%m-%d')
        except Exception as e:
            print(f"Could not parse date '{date_str}': {str(e)}")
            return date_str
    
    def get_country_from_city(self, city):
        """Map city to country"""
        city_country_map = {
            'Paris': 'France',
            'Milan': 'Italy',
            'London': 'United Kingdom',
            'Florence': 'Italy',
            'New York': 'USA',
            'Tokyo': 'Japan',
            'Shanghai': 'China',
            'Berlin': 'Germany',
            'Düsseldorf': 'Germany',
            'Munich': 'Germany',
        }
        return city_country_map.get(city, 'Unknown')
    
    def save_showrooms(self, showrooms):
        """Save showrooms to CSV"""
        if not showrooms:
            print("No showrooms to save")
            return
        
        from pathlib import Path
        filename = str(Path('data/processed/designer_showrooms.csv'))
        
        # Add IDs and scraped date
        for i, sr in enumerate(showrooms, 1):
            sr['lead_id'] = f"DS{i:04d}"
            sr['scraped_date'] = datetime.now().strftime('%Y-%m-%d')
        
        self.save_to_csv(showrooms, filename)
        print(f"Saved {len(showrooms)} designer showrooms to {filename}")
    
    def run(self):
        """Main scraping workflow"""
        print("Starting designer showrooms scraper")
        
        self.start_browser()
        all_showrooms = []
        
        urls = self.get_urls_to_scrape()
        
        for url in urls:
            showrooms = self.scrape_showroom_page(url)
            all_showrooms.extend(showrooms)
            time.sleep(self.delay)
        
        # Dedupe by brand_name + source_url
        deduped = []
        seen = set()
        for r in all_showrooms:
            key = (r.get('brand_name','').strip().lower(), r.get('source_url','').strip().lower())
            if not r.get('brand_name') or key in seen:
                continue
            seen.add(key)
            deduped.append(r)

        # Save results
        self.save_showrooms(deduped)

        print(f"Designer showrooms scraping complete. Total: {len(deduped)}")

        self.stop_browser()


if __name__ == "__main__":
    scraper = DesignerShowroomsScraper()
    scraper.run()
