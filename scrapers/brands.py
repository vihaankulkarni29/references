"""
Brands scraper for ModeMonline.com
Extracts fashion brand information with descriptions.
Priority 1B - Tier 1 Lead Generation
"""
import re
import time
from datetime import datetime
from scrapers.base_scraper import BaseScraper
from config.settings import REGION_MAPPING, TARGET_REGIONS
from utils.data_cleaner import clean_text


class BrandsScraper(BaseScraper):
    """Scraper for fashion brands directory"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.modemonline.com/fashion/brands/letter"
        # Letters A-Z
        self.letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    
    def get_urls(self):
        """Generate URLs for each letter"""
        urls = []
        for letter in self.letters:
            urls.append(f"{self.base_url}/{letter.lower()}")
        return urls
    
    def scrape_brands_page(self, url, letter):
        """Scrape brands for a specific letter"""
        print(f"\n{'='*80}")
        print(f"Scraping brands starting with '{letter}': {url}")
        print('='*80)
        
        try:
            page = self.new_page()
            page.goto(url, wait_until='networkidle', timeout=60000)
            time.sleep(3)
            
            brands = []
            
            # Find all brand links - they usually have a specific pattern
            # Try to find links in a brands list or directory
            brand_links = page.locator('a[href*="/fashion/brands/"]').all()
            print(f"Found {len(brand_links)} potential brand links")
            
            # Get unique brand pages
            brand_urls = set()
            for link in brand_links[:100]:  # Limit to avoid timeout
                try:
                    href = link.get_attribute('href')
                    if href and '/brands/letter/' not in href and href.count('/') > 3:
                        brand_urls.add(href)
                except:
                    continue
            
            print(f"Extracted {len(brand_urls)} unique brand URLs")
            
            # Visit each brand page to get details
            for idx, brand_url in enumerate(list(brand_urls)[:20]):  # Limit to 20 per letter for now
                try:
                    if not brand_url.startswith('http'):
                        brand_url = 'https://www.modemonline.com' + brand_url
                    
                    brand_data = self.scrape_brand_detail(brand_url, page)
                    if brand_data:
                        brands.append(brand_data)
                        if idx < 3:
                            print(f"  [+] {brand_data['company_name']} - {brand_data['city']}, {brand_data['country']}")
                    
                    time.sleep(1)  # Rate limiting between brand pages
                except Exception as e:
                    print(f"  Error scraping brand {brand_url}: {e}")
                    continue
            
            page.close()
            print(f"\n[OK] Extracted {len(brands)} brands for letter '{letter}'")
            return brands
            
        except Exception as e:
            print(f"\n[ERROR] Error scraping {url}: {str(e)}")
            return []
    
    def scrape_brand_detail(self, url, page):
        """Scrape individual brand page for detailed information"""
        try:
            page.goto(url, wait_until='networkidle', timeout=30000)
            time.sleep(2)
            
            # Extract brand name
            brand_name = "Unknown"
            try:
                h1 = page.locator('h1').first
                if h1.count() > 0:
                    brand_name = clean_text(h1.text_content())
            except:
                pass
            
            # Extract description
            description = "N/A"
            try:
                # Look for description in various possible containers
                desc_selectors = [
                    'div.description',
                    'div.brand-description',
                    'div.about',
                    'p.description',
                    'div[class*="desc"]'
                ]
                for selector in desc_selectors:
                    desc_elem = page.locator(selector).first
                    if desc_elem.count() > 0:
                        desc_text = desc_elem.text_content()
                        if desc_text and len(desc_text) > 50:
                            description = clean_text(desc_text)[:500]
                            break
            except:
                pass
            
            # Get all text content to extract contact info
            page_text = page.text_content()
            
            # Extract city
            city = self.extract_city(page_text)
            
            # Extract email
            email = "N/A"
            email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', page_text)
            if email_match:
                email = clean_text(email_match.group(1))
            
            # Extract phone
            phone = "N/A"
            phone_match = re.search(r'(?:T|Tel|Phone|P)\s*:?\s*(\+?[\d\s\(\)\-\.]{10,})', page_text, re.IGNORECASE)
            if phone_match:
                phone = clean_text(phone_match.group(1))
            
            # Extract website
            website = "N/A"
            web_match = re.search(r'(?:www\.|https?://)([\w\-\.]+\.(?:com|net|org|it|fr|de|uk|cn|jp|au|kr)[^\s<"\)]*)', page_text, re.IGNORECASE)
            if web_match:
                website = clean_text(web_match.group(0))
                if not website.startswith('http'):
                    website = 'https://' + website
            
            # Extract social media
            instagram = "N/A"
            insta_match = re.search(r'instagram\.com/([a-zA-Z0-9_\.]+)', page_text.lower())
            if insta_match:
                instagram = f"@{insta_match.group(1)}"
            
            # Get country and region
            country = self.get_country_from_city(city)
            region = REGION_MAPPING.get(country, "Other")
            
            # Filter by region
            if region not in TARGET_REGIONS:
                return None
            
            return {
                'lead_type': 'Brand',
                'company_name': brand_name,
                'description': description,
                'email': email,
                'phone': phone,
                'website': website,
                'instagram': instagram,
                'city': city,
                'country': country,
                'region': region,
                'source_url': url
            }
            
        except Exception as e:
            return None
    
    def extract_city(self, text):
        """Extract city from text"""
        cities = ['Hong Kong', 'New York', 'Los Angeles', 'Paris', 'Milan', 'London', 'Tokyo',
                 'Shanghai', 'Istanbul', 'Seoul', 'Florence', 'Berlin', 'Munich', 'Sydney',
                 'Frankfurt', 'Düsseldorf', 'Moscow', 'Copenhagen', 'Madrid', 'Barcelona',
                 'Amsterdam', 'Brussels', 'Zurich', 'Vienna', 'Rome', 'Singapore', 'Bangkok',
                 'Antwerp', 'Stockholm', 'Oslo', 'Helsinki', 'Warsaw', 'Prague', 'Budapest']
        
        for city in cities:
            if city in text:
                return city
        return "N/A"
    
    def get_country_from_city(self, city):
        """Map city to country"""
        city_country_map = {
            'Paris': 'France', 'Milan': 'Italy', 'London': 'United Kingdom',
            'Florence': 'Italy', 'Rome': 'Italy', 'Berlin': 'Germany',
            'Munich': 'Germany', 'Frankfurt': 'Germany', 'Düsseldorf': 'Germany',
            'Copenhagen': 'Denmark', 'Madrid': 'Spain', 'Barcelona': 'Spain',
            'Amsterdam': 'Netherlands', 'Brussels': 'Belgium', 'Antwerp': 'Belgium',
            'Zurich': 'Switzerland', 'Vienna': 'Austria', 'Moscow': 'Russia',
            'Istanbul': 'Turkey', 'Hong Kong': 'China', 'Shanghai': 'China',
            'Tokyo': 'Japan', 'Seoul': 'South Korea', 'Singapore': 'Singapore',
            'Bangkok': 'Thailand', 'Sydney': 'Australia', 'New York': 'United States',
            'Los Angeles': 'United States', 'Stockholm': 'Sweden', 'Oslo': 'Norway',
            'Helsinki': 'Finland', 'Warsaw': 'Poland', 'Prague': 'Czech Republic',
            'Budapest': 'Hungary'
        }
        return city_country_map.get(city, 'Unknown')
    
    def save_to_csv(self, data):
        """Save brands to CSV"""
        if not data:
            print("No brands to save")
            return
        
        import csv
        from pathlib import Path
        
        output_dir = Path("data/processed")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filename = output_dir / "brands.csv"
        
        # Generate IDs and add scraped date
        for idx, brand in enumerate(data, 1):
            brand['lead_id'] = f"BR{idx:04d}"
            brand['scraped_date'] = datetime.now().strftime('%Y-%m-%d')
        
        fieldnames = ['lead_id', 'lead_type', 'company_name', 'description', 'email', 'phone',
                     'website', 'instagram', 'city', 'country', 'region', 'source_url', 'scraped_date']
        
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        
        print(f"Saved {len(data)} brands to {filename}")
    
    def run(self):
        """Main execution method"""
        all_brands = []
        
        # Test with just a few letters first
        test_letters = ['A', 'B', 'C']  # Start with A, B, C
        
        for letter in test_letters:
            url = f"{self.base_url}/{letter.lower()}"
            brands = self.scrape_brands_page(url, letter)
            all_brands.extend(brands)
            time.sleep(3)  # Rate limiting between letters
        
        self.save_to_csv(all_brands)
        print(f"\nBrands scraping complete. Total: {len(all_brands)}")


if __name__ == "__main__":
    scraper = BrandsScraper()
    scraper.run()
