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
            "fall-winter-2025-2026"
        ]
        
    def get_urls_to_scrape(self):
        """Generate list of designer showroom URLs"""
        urls = []
        for season in self.seasons:
            url = f"{self.base_url}/{season}/digital/extra/designer-showrooms"
            urls.append(url)
        return urls
    
    def scrape_showroom_page(self, url):
        """Scrape a single designer showroom page"""
        print(f"Scraping designer showroom page: {url}")
        
        try:
            page = self.new_page()
            page.goto(url, timeout=30000)
            
            # Wait for content
            page.wait_for_selector('body', timeout=30000)
            
            # Get HTML content
            html = page.content()
            
            # Extract showrooms
            showrooms = self.extract_showrooms(html, url)
            
            print(f"Found {len(showrooms)} designer showrooms on {url}")
            
            page.close()
            return showrooms
            
        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
            return []
    
    def extract_showrooms(self, html, source_url):
        """Extract showroom data from HTML"""
        showrooms = []
        
        # Pattern for brand name with Mini Website
        name_pattern = r'\*\s*([A-Za-z0-9\s\[\]\'\-\&\.\/\(\)]+?)(?:M\'s|W\'s|M\'s/W\'s|\[)'
        
        # Split into blocks by list items
        blocks = re.split(r'<li[^>]*>|</li>', html)
        
        for block in blocks:
            if len(block) < 100:
                continue
                
            try:
                # Extract brand name
                name_match = re.search(name_pattern, block)
                if not name_match:
                    # Try alternative pattern
                    name_match = re.search(r'\*\s*([A-Z][A-Za-z0-9\s\&\'\-\.]+?)\s*(?:<table|Sales\s+campaign)', block)
                
                if not name_match:
                    continue
                
                brand_name = clean_text(name_match.group(1))
                
                # Extract categories (Men's RTW, Women's RTW, etc.)
                category_pattern = r'((?:Women\'s|Men\'s|M\'s/W\'s|M\'s|W\'s)\s+(?:RTW|Acc\.|Accessories)[^<\|]*)'
                category_matches = re.findall(category_pattern, block)
                categories = ', '.join([clean_text(cat) for cat in category_matches]) if category_matches else "N/A"
                
                # Extract sales campaign dates
                sales_pattern = r'Sales\s+campaign\s+\w+\s+from\s+([A-Z][a-z]+\.?\s+[A-Z][a-z]+\s+\d{1,2}\s+\d{4})\s+to\s+([A-Z][a-z]+\.?\s+[A-Z][a-z]+\s+\d{1,2}\s+\d{4})'
                sales_match = re.search(sales_pattern, block)
                
                sales_start = "N/A"
                sales_end = "N/A"
                
                if sales_match:
                    sales_start = self.parse_date(sales_match.group(1))
                    sales_end = self.parse_date(sales_match.group(2))
                
                # Extract showroom locations (multiple possible)
                # Pattern: CITY name Date - Date Address
                location_pattern = r'([A-Z]{2,}(?:\s+[A-Z]+)?)\s+(?:[A-Z][a-z]+\s+\d{1,2}|from)'
                location_matches = re.findall(location_pattern, block)
                
                # Get primary city
                cities = []
                for loc in location_matches:
                    if loc in ['PARIS', 'MILAN', 'MILANO', 'NEW YORK', 'LONDON', 'FLORENCE', 
                              'FIRENZE', 'TOKYO', 'SHANGHAI', 'BERLIN', 'DÜSSELDORF', 'MUNICH']:
                        cities.append(loc.title())
                
                # Normalize city names
                city_map = {'Milano': 'Milan', 'Firenze': 'Florence'}
                cities = [city_map.get(c, c) for c in cities]
                
                primary_city = cities[0] if cities else "N/A"
                all_cities = ', '.join(list(set([c for c in cities if c]))) if cities else "N/A"
                
                # Extract address
                address_patterns = [
                    r'((?:via|Via|Rue|rue|Viale|Corso)\s+[A-Za-z\s\.\,]{5,80}?\d+[^\|<\n]{0,50}?(?:\d{5}|Milan|Paris|Florence))',
                    r'(\d+\s+[A-Z][a-z]+\s+(?:Street|Avenue|Road|St|Ave)[^\|<\n]{0,50})',
                ]
                
                address = "N/A"
                for pattern in address_patterns:
                    addr_match = re.search(pattern, block)
                    if addr_match:
                        address = clean_text(addr_match.group(1))[:200]
                        break
                
                # Extract phone
                phone_pattern = r'(?:P\s*:|Mobile:)\s*(\+?[\d\s\(\)\-]{10,})'
                phone_match = re.search(phone_pattern, block)
                phone = clean_text(phone_match.group(1)) if phone_match else "N/A"
                
                # Extract email
                email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
                email_match = re.search(email_pattern, block)
                email = clean_text(email_match.group(1)) if email_match else "N/A"
                
                # Extract Instagram
                instagram_pattern = r'instagram\.com/([a-zA-Z0-9_\.]+)'
                insta_match = re.search(instagram_pattern, block.lower())
                instagram = f"@{insta_match.group(1)}" if insta_match else "N/A"
                
                # Extract Facebook
                facebook_pattern = r'facebook\.com/([a-zA-Z0-9_\.]+)'
                fb_match = re.search(facebook_pattern, block.lower())
                facebook = f"facebook.com/{fb_match.group(1)}" if fb_match else "N/A"
                
                # Extract description (brand description text)
                desc_pattern = r'</table>\s*([A-Z][^<]{100,800}?)\s*(?:\||<)'
                desc_match = re.search(desc_pattern, block)
                description = clean_text(desc_match.group(1))[:500] if desc_match else "N/A"
                
                # Determine country and region
                country = self.get_country_from_city(primary_city)
                region = REGION_MAPPING.get(country, "Other")
                
                # Filter by region
                if region not in TARGET_REGIONS:
                    print(f"Skipping {brand_name} - Region {region} not in targets")
                    continue
                
                showroom = {
                    'brand_name': brand_name,
                    'categories': categories,
                    'sales_start': sales_start,
                    'sales_end': sales_end,
                    'primary_city': primary_city,
                    'all_cities': all_cities,
                    'country': country,
                    'region': region,
                    'address': address,
                    'phone': phone,
                    'email': email,
                    'instagram': instagram,
                    'facebook': facebook,
                    'description': description,
                    'source_url': source_url
                }
                
                showrooms.append(showroom)
                print(f"Extracted: {brand_name} ({categories}) in {primary_city}")
                
            except Exception as e:
                print(f"Error parsing showroom block: {str(e)}")
                continue
        
        return showrooms
    
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
        
        # Save results
        self.save_showrooms(all_showrooms)
        
        print(f"Designer showrooms scraping complete. Total: {len(all_showrooms)}")
        
        self.stop_browser()


if __name__ == "__main__":
    scraper = DesignerShowroomsScraper()
    scraper.run()
