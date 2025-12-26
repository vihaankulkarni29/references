"""
Brands scraper for ModeMonline.com
Extracts fashion brand information using Mini Website pattern.
Priority 1B - Tier 1 Lead Generation
"""
import re
import time
from datetime import datetime
from scrapers.base_scraper import BaseScraper
from config.settings import REGION_MAPPING, TARGET_REGIONS
from utils.data_cleaner import clean_text


class BrandsScraper(BaseScraper):
    """Scraper for fashion brands using Mini Website pattern"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.modemonline.com/fashion/mini-web-sites/fashion-brands"
        
        # Countries to scrape (Asia + Europe based on TARGET_REGIONS)
        # For testing, start with a few key countries
        self.test_countries = ['italy', 'france', 'germany', 'japan', 'korea', 'hongkong']
        
        # All countries from the page
        self.all_countries = [
            'bahrain', 'france', 'germany', 'hongkong', 'italy', 'japan',
            'lebanon', 'newzealand', 'korea', 'switzerland', 'taiwan',
            'netherlands', 'turkey', 'greatbritain', 'usa'
        ]
        
        # Known cities for location extraction
        self.known_cities = {
            'Milan', 'Paris', 'London', 'New York', 'Tokyo', 'Shanghai', 
            'Hong Kong', 'Seoul', 'Singapore', 'Mumbai', 'Dubai', 'Bangkok',
            'Berlin', 'Madrid', 'Barcelona', 'Rome', 'Florence', 'Los Angeles',
            'Copenhagen', 'Stockholm', 'Amsterdam', 'Brussels', 'Zurich',
            'Vienna', 'Prague', 'Warsaw', 'Moscow', 'Istanbul', 'Tel Aviv',
            'Sydney', 'Melbourne', 'Toronto', 'Montreal', 'Beijing', 'Guangzhou'
        }
        
        # City to country mapping
        self.city_to_country = {
            'Milan': 'Italy', 'Florence': 'Italy', 'Rome': 'Italy',
            'Paris': 'France', 'London': 'United Kingdom', 'New York': 'United States',
            'Los Angeles': 'United States', 'Tokyo': 'Japan', 'Shanghai': 'China',
            'Hong Kong': 'Hong Kong', 'Seoul': 'South Korea', 'Singapore': 'Singapore',
            'Mumbai': 'India', 'Dubai': 'United Arab Emirates', 'Bangkok': 'Thailand',
            'Berlin': 'Germany', 'Madrid': 'Spain', 'Barcelona': 'Spain',
            'Copenhagen': 'Denmark', 'Stockholm': 'Sweden', 'Amsterdam': 'Netherlands',
            'Brussels': 'Belgium', 'Zurich': 'Switzerland', 'Vienna': 'Austria',
            'Prague': 'Czech Republic', 'Warsaw': 'Poland', 'Moscow': 'Russia',
            'Istanbul': 'Turkey', 'Tel Aviv': 'Israel', 'Sydney': 'Australia',
            'Melbourne': 'Australia', 'Toronto': 'Canada', 'Montreal': 'Canada',
            'Beijing': 'China', 'Guangzhou': 'China'
        }
    
    def get_urls(self):
        """Return URLs for each country (testing with subset first)"""
        # For testing, use test_countries. For full scrape, use all_countries
        countries = self.test_countries
        return [f"{self.base_url}/{country}" for country in countries]
    
    def scrape_brands_page(self, url):
        """Scrape brands from the mini-web-sites page"""
        print(f"\n{'='*80}")
        print(f"Scraping brands: {url}")
        print('='*80)
        
        try:
            page = self.new_page()
            page.goto(url, wait_until='networkidle', timeout=60000)
            time.sleep(3)
            
            brands = []
            
            # Find all "Mini Website" links (same pattern as tradeshows)
            mini_website_links = page.locator('a:has-text("Mini Website")').all()
            print(f"Found {len(mini_website_links)} Mini Website links")
            
            for i, link in enumerate(mini_website_links, 1):
                try:
                    # Get the parent element (usually tr or div)
                    parent = None
                    try:
                        parent = link.locator('xpath=ancestor::tr').first
                    except:
                        try:
                            parent = link.locator('xpath=ancestor::div[@class*="col" or @class*="row"]').first
                        except:
                            parent = link.locator('xpath=..').first
                    
                    if parent:
                        # Get all text content from parent
                        text = parent.text_content()
                        
                        # Get the link URL for source reference
                        href = link.get_attribute('href')
                        source_url = f"https://www.modemonline.com{href}" if href and href.startswith('/') else (href or "")
                        
                        # Parse the brand information
                        brand_data = self.parse_brand_text(text, source_url)
                        
                        if brand_data and brand_data.get('company_name'):
                            brands.append(brand_data)
                            if i % 10 == 0:
                                print(f"  Processed {i}/{len(mini_website_links)} brands...")
                
                except Exception as e:
                    print(f"  Warning: Error processing brand link {i}: {str(e)}")
                    continue
            
            print(f"[OK] Successfully extracted {len(brands)} brands")
            return brands
            
        except Exception as e:
            print(f"[ERROR] Failed to scrape brands: {str(e)}")
            return []
    
    def parse_brand_text(self, text, source_url=""):
        """Parse brand information from text content"""
        try:
            # Clean text
            text = ' '.join(text.split())
            
            # Remove "* Mini Website" suffix if present
            text = re.sub(r'\s*\*\s*Mini Website\s*$', '', text, flags=re.IGNORECASE)
            
            # Extract brand name (first part before city or contact info)
            name_match = re.match(r'^([^,\(]+?)(?:\s*[\(,]|$)', text)
            company_name = name_match.group(1).strip() if name_match else text.split()[0] if text.split() else ""
            
            # Extract city
            city = self.extract_city(text)
            
            # Get country from city
            country = self.city_to_country.get(city, "")
            
            # Get region
            region = REGION_MAPPING.get(country, "")
            
            # Extract contacts
            email = self.extract_email(text)
            phone = self.extract_phone(text)
            website = self.extract_website(text)
            instagram = self.extract_instagram(text)
            
            # Extract description (everything after name and before contacts)
            description = ""
            if company_name and len(text) > len(company_name) + 10:
                # Try to get text between name and contact info
                desc_start = text.find(company_name) + len(company_name)
                desc_text = text[desc_start:]
                # Remove contact info patterns
                desc_text = re.sub(r'\b[\w\.-]+@[\w\.-]+\.\w+\b', '', desc_text)
                desc_text = re.sub(r'\b(?:\+?[\d\s\(\)\-\.]{10,})\b', '', desc_text)
                desc_text = re.sub(r'www\.[\w\.-]+\.\w+', '', desc_text)
                desc_text = re.sub(r'@[\w\.]+', '', desc_text)
                description = desc_text.strip()[:500]  # Limit to 500 chars
            
            return {
                'lead_type': 'Brand',
                'company_name': company_name,
                'description': description,
                'email': email,
                'phone': phone,
                'website': website,
                'instagram': instagram,
                'facebook': '',
                'city': city,
                'country': country,
                'region': region,
                'source_url': source_url,
                'scraped_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"  Warning: Error parsing brand text: {str(e)}")
            return {}
    
    def extract_city(self, text):
        """Extract city from text"""
        for city in sorted(self.known_cities, key=len, reverse=True):
            if city in text:
                return city
        return ""
    
    def extract_email(self, text):
        """Extract email from text"""
        email_pattern = r'\b[\w\.-]+@[\w\.-]+\.\w+\b'
        match = re.search(email_pattern, text)
        return match.group(0) if match else ""
    
    def extract_phone(self, text):
        """Extract phone number from text"""
        phone_pattern = r'\b(?:\+?[\d\s\(\)\-\.]{10,})\b'
        match = re.search(phone_pattern, text)
        return match.group(0).strip() if match else ""
    
    def extract_website(self, text):
        """Extract website from text"""
        website_pattern = r'(?:www\.[\w\.-]+\.\w+|https?://[\w\.-]+\.\w+)'
        match = re.search(website_pattern, text, re.IGNORECASE)
        return match.group(0) if match else ""
    
    def extract_instagram(self, text):
        """Extract Instagram handle from text"""
        instagram_pattern = r'@([\w\.]+)'
        match = re.search(instagram_pattern, text)
        return match.group(1) if match else ""
    
    def run(self):
        """Main scraping process"""
        print(f"Starting brands scraper at {datetime.now()}")
        
        try:
            self.start_browser()
            
            all_brands = []
            urls = self.get_urls()
            
            for url in urls:
                brands = self.scrape_brands_page(url)
                all_brands.extend(brands)
                time.sleep(2)
            
            # Filter by region
            filtered_brands = []
            for brand in all_brands:
                if brand.get('region') in TARGET_REGIONS:
                    filtered_brands.append(brand)
                else:
                    print(f"  Skipping {brand.get('company_name')} - Region: {brand.get('region')} (not in target regions)")
            
            # Save to CSV
            if filtered_brands:
                self.save_to_csv(filtered_brands, 'brands.csv')
                print(f"\n[OK] Saved {len(filtered_brands)} brands (filtered from {len(all_brands)} total)")
            else:
                print("\nNo brands to save")
            
            print(f"\nBrands scraping complete. Total: {len(filtered_brands)}")
            
        except Exception as e:
            print(f"[ERROR] Scraping failed: {str(e)}")
            import traceback
            traceback.print_exc()
        
        finally:
            self.stop_browser()


def main():
    scraper = BrandsScraper()
    scraper.run()


if __name__ == "__main__":
    main()
