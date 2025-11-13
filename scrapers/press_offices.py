"""
Press Offices scraper for ModeMonline.com
Extracts press office contact information for lead generation.
Priority 1A - Tier 1 Lead Generation
"""
import re
import time
from datetime import datetime
from scrapers.base_scraper import BaseScraper
from config.settings import REGION_MAPPING, TARGET_REGIONS
from utils.data_cleaner import clean_text


class PressOfficesScraper(BaseScraper):
    """Scraper for press offices/PR agencies"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.modemonline.com/fashion/mini-web-sites/press-offices"
    
    def get_urls(self):
        """Get URLs to scrape"""
        return [self.base_url]
    
    def scrape_press_office_page(self, url):
        """Scrape press offices using Playwright DOM API"""
        print(f"\n{'='*80}")
        print(f"Scraping: {url}")
        print('='*80)
        
        try:
            page = self.new_page()
            page.goto(url, wait_until='networkidle', timeout=60000)
            
            # Wait for content to load
            time.sleep(5)
            
            # Find all "Mini Website" links
            press_offices = []
            mini_website_links = page.locator('a:has-text("Mini Website")').all()
            print(f"Found {len(mini_website_links)} Mini Website links\n")
            
            for idx, link in enumerate(mini_website_links):
                try:
                    # Get parent container
                    parent_element = None
                    
                    # Try table row first
                    try:
                        parent_tr = link.locator('xpath=ancestor::tr[1]')
                        if parent_tr.count() > 0:
                            parent_element = parent_tr
                    except:
                        pass
                    
                    # Try div container
                    if not parent_element:
                        try:
                            parent_div = link.locator('xpath=ancestor::div[contains(@class, "col") or contains(@class, "row")][1]')
                            if parent_div.count() > 0:
                                parent_element = parent_div
                        except:
                            pass
                    
                    # Fallback to immediate parent
                    if not parent_element:
                        parent_element = link.locator('xpath=..')
                    
                    text = parent_element.text_content()
                    
                    if idx < 3:  # Show first 3 for debugging
                        print(f"=== Press Office #{idx+1} ===")
                        print(text[:400] if text else "(no text)")
                        print()
                    
                    # Extract press office data
                    if text and len(text) > 20:
                        office_data = self.parse_press_office_text(text, url)
                        if office_data:
                            press_offices.append(office_data)
                        
                except Exception as e:
                    if idx < 5:
                        print(f"Error processing link {idx}: {e}")
                    continue
            
            page.close()
            print(f"\n[OK] Successfully extracted {len(press_offices)} press offices")
            return press_offices
            
        except Exception as e:
            print(f"\n[ERROR] Error scraping {url}: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def parse_press_office_text(self, text, source_url):
        """Parse press office details from text content"""
        if not text or len(text) < 10:
            return None
        
        # Clean up text
        text = ' '.join(text.split())
        
        # Extract company name (before "* Mini Website")
        company_name = "Unknown"
        name_match = re.search(r'^([A-Z][^*\[]+?)(?:\s*\*?\s*Mini Website|\s*\[)', text)
        if name_match:
            company_name = clean_text(name_match.group(1))
        else:
            # Try first substantial text
            name_match2 = re.search(r'^([A-Z][^0-9]{10,80}?)(?:\s|$)', text)
            if name_match2:
                company_name = clean_text(name_match2.group(1))
        
        # Remove trailing artifacts
        company_name = re.sub(r'\s*\*?\s*Mini\s+Website\s*$', '', company_name, flags=re.IGNORECASE)
        company_name = re.sub(r'\s*[\*\[\]]\s*$', '', company_name).strip()
        
        # Extract city
        city = "N/A"
        cities = ['Hong Kong', 'New York', 'Los Angeles', 'Paris', 'Milan', 'London', 'Tokyo', 
                 'Shanghai', 'Istanbul', 'Seoul', 'Florence', 'Berlin', 'Munich', 'Sydney',
                 'Frankfurt', 'Düsseldorf', 'Moscow', 'Copenhagen', 'Madrid', 'Barcelona',
                 'Amsterdam', 'Brussels', 'Zurich', 'Vienna', 'Rome', 'Singapore', 'Bangkok']
        
        for known_city in cities:
            if known_city in text:
                city = known_city
                break
        
        # Extract email
        email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        email_match = re.search(email_pattern, text)
        email = clean_text(email_match.group(1)) if email_match else "N/A"
        
        # Extract phone
        phone_pattern = r'(?:T|Tel|Phone|P)\s*:?\s*(\+?[\d\s\(\)\-\.]{10,})'
        phone_match = re.search(phone_pattern, text, re.IGNORECASE)
        phone = clean_text(phone_match.group(1)) if phone_match else "N/A"
        
        # Extract website
        web_pattern = r'(?:www\.|https?://)([\w\-\.]+\.(?:com|net|org|it|fr|de|uk|cn|jp|au|kr|nl|be|ch)[^\s<"\)]*)'
        web_match = re.search(web_pattern, text, re.IGNORECASE)
        website = "N/A"
        if web_match:
            website = clean_text(web_match.group(0))
            if not website.startswith('http'):
                website = 'https://' + website
        
        # Extract Instagram
        instagram_pattern = r'instagram\.com/([a-zA-Z0-9_\.]+)'
        insta_match = re.search(instagram_pattern, text.lower())
        instagram = f"@{insta_match.group(1)}" if insta_match else "N/A"
        
        # Extract Facebook  
        facebook_pattern = r'facebook\.com/([a-zA-Z0-9_\.]+)'
        fb_match = re.search(facebook_pattern, text.lower())
        facebook = f"facebook.com/{fb_match.group(1)}" if fb_match else "N/A"
        
        # Get country and region
        country = self.get_country_from_city(city)
        region = REGION_MAPPING.get(country, "Other")
        
        # Filter by region
        if region not in TARGET_REGIONS:
            return None
        
        # Skip if name is too short
        if len(company_name) < 3 or 'Mini Website' in company_name:
            return None
        
        return {
            'lead_type': 'Press Office',
            'company_name': company_name,
            'email': email,
            'phone': phone,
            'website': website,
            'instagram': instagram,
            'facebook': facebook,
            'city': city,
            'country': country,
            'region': region,
            'source_url': source_url
        }
    
    def get_country_from_city(self, city):
        """Map city to country"""
        city_country_map = {
            'Paris': 'France', 'Milan': 'Italy', 'London': 'United Kingdom',
            'Florence': 'Italy', 'Rome': 'Italy', 'Berlin': 'Germany',
            'Munich': 'Germany', 'Frankfurt': 'Germany', 'Düsseldorf': 'Germany',
            'Copenhagen': 'Denmark', 'Madrid': 'Spain', 'Barcelona': 'Spain',
            'Amsterdam': 'Netherlands', 'Brussels': 'Belgium', 'Zurich': 'Switzerland',
            'Vienna': 'Austria', 'Moscow': 'Russia', 'Istanbul': 'Turkey',
            'Hong Kong': 'China', 'Shanghai': 'China', 'Tokyo': 'Japan',
            'Seoul': 'South Korea', 'Singapore': 'Singapore', 'Bangkok': 'Thailand',
            'Sydney': 'Australia', 'New York': 'United States', 'Los Angeles': 'United States'
        }
        return city_country_map.get(city, 'Unknown')
    
    def save_to_csv(self, data):
        """Save press offices to CSV"""
        if not data:
            print("No press offices to save")
            return
        
        import csv
        from pathlib import Path
        
        # Ensure output directory exists
        output_dir = Path("data/processed")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filename = output_dir / "press_offices.csv"
        
        # Generate IDs and add scraped date
        for idx, office in enumerate(data, 1):
            office['lead_id'] = f"PO{idx:04d}"
            office['scraped_date'] = datetime.now().strftime('%Y-%m-%d')
        
        # Write to CSV
        fieldnames = ['lead_id', 'lead_type', 'company_name', 'email', 'phone', 'website',
                     'instagram', 'facebook', 'city', 'country', 'region', 'source_url', 'scraped_date']
        
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        
        print(f"Saved {len(data)} press offices to {filename}")
    
    def run(self):
        """Main execution method"""
        all_press_offices = []
        
        for url in self.get_urls():
            press_offices = self.scrape_press_office_page(url)
            all_press_offices.extend(press_offices)
            time.sleep(2)  # Rate limiting
        
        self.save_to_csv(all_press_offices)
        print(f"\nPress offices scraping complete. Total: {len(all_press_offices)}")


if __name__ == "__main__":
    scraper = PressOfficesScraper()
    scraper.run()
