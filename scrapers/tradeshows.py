"""
Tradeshows scraper for ModeMonline.com
Extracts tradeshow information from the digital/extra/tradeshows pages.
"""
import re
import time
from datetime import datetime
from scrapers.base_scraper import BaseScraper
from config.settings import REGION_MAPPING, TARGET_REGIONS
from utils.data_cleaner import clean_text


class TradeshowsScraper(BaseScraper):
    """Scraper for fashion tradeshows"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.modemonline.com/fashion/fashion-weeks"
        self.seasons = [
            "spring-summer-2026",
            "fall-winter-2025-2026"
        ]
        
    def get_urls_to_scrape(self):
        """Generate list of tradeshow URLs"""
        urls = []
        for season in self.seasons:
            url = f"{self.base_url}/{season}/digital/extra/tradeshows"
            urls.append(url)
        return urls
    
    def scrape_tradeshow_page(self, url):
        """Scrape a single tradeshow page using Playwright DOM selectors"""
        print(f"\n{'='*80}")
        print(f"Scraping: {url}")
        print('='*80)
        
        try:
            page = self.new_page()
            page.goto(url, wait_until='networkidle', timeout=60000)
            
            # Handle cookie consent if present
            self.handle_cookie_consent(page)
            
            # Wait for content to load
            import time
            time.sleep(5)
            
            # Find all "Mini Website" links and extract parent elements
            tradeshows = []
            
            # Use Playwright's locator API to find Mini Website links
            mini_website_links = page.locator('a:has-text("Mini Website")').all()
            print(f"Found {len(mini_website_links)} Mini Website links\n")
            
            for idx, link in enumerate(mini_website_links):
                try:
                    # Get the parent container (try div, tr, or td)
                    # Try to find a table row first, then any container
                    parent_element = None
                    
                    # Try finding parent tr (table row)
                    try:
                        parent_tr = link.locator('xpath=ancestor::tr[1]')
                        if parent_tr.count() > 0:
                            parent_element = parent_tr
                    except:
                        pass
                    
                    # If no tr, try div
                    if not parent_element:
                        try:
                            parent_div = link.locator('xpath=ancestor::div[contains(@class, "col") or contains(@class, "row")][1]')
                            if parent_div.count() > 0:
                                parent_element = parent_div
                        except:
                            pass
                    
                    # If still nothing, just get the immediate parent
                    if not parent_element:
                        parent_element = link.locator('xpath=..')
                    
                    text = parent_element.text_content()
                    href = None
                    try:
                        href = link.get_attribute('href')
                    except Exception:
                        href = None
                    # Build absolute mini website URL if possible
                    mini_url = None
                    if href:
                        mini_url = f"https://www.modemonline.com{href}" if href.startswith('/') else href
                    
                    if idx < 3:  # Show first 3 for debugging
                        print(f"=== Tradeshow #{idx+1} ===")
                        print(text[:500] if text else "(no text)")  # Show more text
                        print()
                    
                    # Extract tradeshow data from text
                    if text and len(text) > 50:
                        tradeshow_data = self.parse_tradeshow_text(text, url)
                        if tradeshow_data:
                            if mini_url:
                                tradeshow_data['mini_website_url'] = mini_url
                            tradeshows.append(tradeshow_data)
                        
                except Exception as e:
                    if idx < 5:  # Only show first 5 errors
                        print(f"Error processing link {idx}: {e}")
                    continue
            
            page.close()
            print(f"\n[OK] Successfully extracted {len(tradeshows)} tradeshows")
            return tradeshows
            
        except Exception as e:
            print(f"\n[ERROR] Error scraping {url}: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def parse_tradeshow_text(self, text, source_url):
        """Parse tradeshow details from text content"""
        import re
        
        if not text or len(text) < 10:
            return None
        
        # Clean up text - remove multiple whitespace, newlines
        text = ' '.join(text.split())
        
        # Extract name - it's usually before "* Mini Website" or at the beginning
        name = "Unknown"
        
        # Try to extract name before "* Mini Website"
        name_match = re.search(r'([A-Z][^*\[]+?)(?:\s*\*?\s*Mini Website|\s*\[)', text)
        if name_match:
            name = clean_text(name_match.group(1))
        else:
            # Otherwise take first substantial text before date pattern
            name_match2 = re.search(r'^([A-Z][^0-9]{10,80}?)(?:from|January|February|March|April|May|June|July|August|September|October|November|December)', text)
            if name_match2:
                name = clean_text(name_match2.group(1))
        
        # Remove trailing "Mini Website" and asterisks
        name = re.sub(r'\s*\*?\s*Mini\s+Website\s*$', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\s*[\*\[\]]\s*$', '', name).strip()
        
        # Extract dates
        date_match = re.search(r'from\s+(?:[A-Z][a-z]+\.?\s+)?([A-Z][a-z]+)\s+(\d{1,2})\s+(\d{4})\s+to\s+(?:[A-Z][a-z]+\.?\s+)?([A-Z][a-z]+)\s+(\d{1,2})\s+(\d{4})', text)
        start_date = "N/A"
        end_date = "N/A"
        if date_match:
            start_date = self.parse_date(f"{date_match.group(1)} {date_match.group(2)} {date_match.group(3)}")
            end_date = self.parse_date(f"{date_match.group(4)} {date_match.group(5)} {date_match.group(6)}")
        
        # Extract city
        city = "N/A"
        for known_city in ['Hong Kong', 'New York', 'Las Vegas', 'Paris', 'Milan', 'London', 'Tokyo', 'Shanghai', 'Istanbul', 'Seoul', 'Florence', 'Berlin', 'Munich', 'Sydney', 'Frankfurt', 'Düsseldorf', 'Moscow', 'Copenhagen']:
            if known_city in text:
                city = known_city
                break
        
        # Get country and region
        country = self.get_country_from_city(city)
        region = REGION_MAPPING.get(country, "Other")
        
        # Filter by region
        if region not in TARGET_REGIONS:
            return None
        
        # Skip if name is too short or still contains unwanted text
        if len(name) < 3 or 'Mini Website' in name:
            return None
        
        return {
            'event_name': name,
            'event_type': 'Tradeshow',
            'start_date': start_date,
            'end_date': end_date,
            'city': city,
            'country': country,
            'region': region,
            'source_url': source_url
        }
    
    def get_country_from_city(self, city):
        # Placeholder body; the actual implementation is defined later in the file.
        # This stub will be replaced by the proper mapping method below if needed.
        return 'Unknown'
    
    def parse_date(self, date_str):
        """Parse date string to YYYY-MM-DD format"""
        try:
            # Format: "Wed. September 03 2025" or "Tuesday September 04 2025"
            date_str = clean_text(date_str)
            # Remove day name if present
            date_str = re.sub(r'^[A-Z][a-z]+\.?\s+', '', date_str)
            
            # Parse
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
            'Las Vegas': 'USA',
            'Tokyo': 'Japan',
            'Shanghai': 'China',
            'Hong Kong': 'China',
            'Istanbul': 'Turkey',
            'Seoul': 'South Korea',
            'Offenbach': 'Germany',
            'Düsseldorf': 'Germany',
            'Munich': 'Germany',
            'Sidney': 'Australia',
            'Sydney': 'Australia',
            'Rho': 'Italy',
            'Villepinte': 'France',
        }
        return city_country_map.get(city, 'Unknown')
    
    def save_tradeshows(self, tradeshows):
        """Save tradeshows to CSV"""
        if not tradeshows:
            print("No tradeshows to save")
            return
        
        from pathlib import Path
        filename = str(Path('data/processed/tradeshows.csv'))
        
        # Add IDs and scraped date
        for i, ts in enumerate(tradeshows, 1):
            ts['event_id'] = f"TS{i:04d}"
            ts['scraped_date'] = datetime.now().strftime('%Y-%m-%d')
        
        self.save_to_csv(tradeshows, filename)
        print(f"Saved {len(tradeshows)} tradeshows to {filename}")
    
    def run(self):
        """Main scraping workflow"""
        print("Starting tradeshows scraper")
        
        self.start_browser()
        all_tradeshows = []
        
        urls = self.get_urls_to_scrape()
        
        for url in urls:
            tradeshows = self.scrape_tradeshow_page(url)
            all_tradeshows.extend(tradeshows)
            time.sleep(self.delay)
        
        # Save results
        self.save_tradeshows(all_tradeshows)
        
        print(f"Tradeshows scraping complete. Total: {len(all_tradeshows)}")
        
        self.stop_browser()


if __name__ == "__main__":
    scraper = TradeshowsScraper()
    scraper.run()
