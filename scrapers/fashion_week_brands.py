"""
Scrape brand profiles from fashion weeks digital pages

Since modemonline.com has no Asia showroom data, we'll expand Europe coverage
by checking digital brand profiles/presentations
"""
from scrapers.base_scraper import BaseScraper
import time
import csv
from pathlib import Path
import hashlib
from datetime import datetime


class FashionWeekBrandsScraper(BaseScraper):
    """Extract brands from fashion week digital/presentations pages"""
    
    def scrape_fashion_week_brands(self):
        """Scrape brands from fashion week digital presentation pages"""
        print("="*80)
        print("Scraping brands from Fashion Week Digital Pages")
        print("="*80)
        
        # Major fashion weeks with digital presentations
        fashion_weeks = [
            'spring-summer-2026/paris/women',
            'spring-summer-2026/milan/women',
            'spring-summer-2026/london/women',
            'spring-summer-2026/new-york/women',
            'fall-winter-2025-2026/paris/women',
            'fall-winter-2025-2026/milan/women',
            'fall-winter-2025-2026/london/women',
            'fall-winter-2025-2026/new-york/women',
        ]
        
        all_brands = []
        
        for fw_path in fashion_weeks:
            # Try digital presentations page
            url = f"https://www.modemonline.com/fashion/fashion-weeks/{fw_path}/digital"
            brands = self.scrape_digital_page(url, fw_path)
            all_brands.extend(brands)
            time.sleep(3)  # Rate limit
        
        # Deduplicate
        unique_brands = self.deduplicate_brands(all_brands)
        
        # Save to CSV
        self.save_brands(unique_brands, 'data/processed/fashion_week_brands.csv')
        
        return unique_brands
    
    def scrape_digital_page(self, url, fw_path):
        """Scrape a single digital page for brand links"""
        print(f"\nScraping: {url}")
        brands = []
        
        try:
            page = self.new_page()
            page.goto(url, wait_until='networkidle', timeout=60000)
            self.handle_cookie_consent(page)
            time.sleep(3)
            
            # Look for brand/designer links
            # Pattern 1: Links to brand detail pages
            brand_links = page.locator('a[href*="/digital/designers/"]').all()
            print(f"  Found {len(brand_links)} designer links")
            
            for link in brand_links[:50]:  # Limit to first 50
                try:
                    href = link.get_attribute('href')
                    brand_name = link.inner_text().strip()
                    
                    if brand_name and len(brand_name) > 1:
                        # Extract city/country from fw_path
                        parts = fw_path.split('/')
                        city = parts[1] if len(parts) > 1 else 'N/A'
                        
                        # Map city to country
                        city_map = {
                            'paris': ('France', 'Europe'),
                            'milan': ('Italy', 'Europe'),
                            'london': ('United Kingdom', 'Europe'),
                            'new-york': ('United States', 'North America'),
                        }
                        country, region = city_map.get(city, ('N/A', 'Europe'))
                        
                        brands.append({
                            'brand_name': brand_name,
                            'city': city.title(),
                            'country': country,
                            'region': region,
                            'source_url': f"https://www.modemonline.com{href}" if href.startswith('/') else href,
                            'source': 'fashion_week_digital',
                            'season': parts[0] if parts else 'N/A'
                        })
                except Exception as e:
                    print(f"    Error extracting brand: {e}")
                    continue
            
            page.close()
            
        except Exception as e:
            print(f"  Error scraping {url}: {e}")
        
        print(f"  Extracted {len(brands)} brands")
        return brands
    
    def deduplicate_brands(self, brands):
        """Deduplicate brands by normalized name"""
        unique = {}
        for brand in brands:
            name = brand['brand_name'].lower().strip()
            if name not in unique:
                unique[name] = brand
        
        print(f"\nDeduplication: {len(brands)} → {len(unique)} unique brands")
        return list(unique.values())
    
    def save_brands(self, brands, output_path):
        """Save brands to CSV"""
        if not brands:
            print("[WARN] No brands to save")
            return
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Add brand_id and scraped_date
        for brand in brands:
            brand['brand_id'] = hashlib.md5(brand['brand_name'].lower().encode()).hexdigest()[:12]
            brand['scraped_date'] = datetime.now().strftime('%Y-%m-%d')
        
        fieldnames = ['brand_id', 'brand_name', 'city', 'country', 'region', 
                     'source', 'source_url', 'season', 'scraped_date']
        
        with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(brands)
        
        print(f"\n[OK] Saved {len(brands)} brands to {output_path}")
    
    def run(self):
        """Main execution"""
        self.start_browser()
        try:
            brands = self.scrape_fashion_week_brands()
            
            print("\n" + "="*80)
            print("SUMMARY")
            print("="*80)
            print(f"Total unique brands: {len(brands)}")
            
            # Breakdown by region
            from collections import Counter
            regions = Counter(b['region'] for b in brands)
            for region, count in regions.items():
                print(f"  {region}: {count}")
            
        finally:
            self.stop_browser()


if __name__ == '__main__':
    scraper = FashionWeekBrandsScraper()
    scraper.run()
