"""
Extract brands.csv from existing data sources

Strategy:
1. Extract brand_name from designer_showrooms.csv (119 records)
2. Extract company_name from master_leads.csv where lead_type contains "Designer" (160 records)
3. Check fashion weeks for brand profile pages
4. Deduplicate and produce brands.csv

Target: 500+ unique brands across Asia + Europe
"""
import csv
from pathlib import Path
from datetime import datetime
import hashlib


class BrandExtractor:
    """Extract and deduplicate brands from multiple sources"""
    
    def __init__(self):
        self.brands = {}  # key: normalized_name, value: brand dict
        
    def normalize_name(self, name):
        """Normalize brand name for deduplication"""
        if not name or name == 'N/A':
            return None
        # Lowercase, remove extra spaces, strip common suffixes
        name = name.lower().strip()
        name = ' '.join(name.split())  # Normalize whitespace
        
        # Remove common noise
        noise_patterns = [
            ' showroom', ' sales department', ' sales office',
            ' - instagram', ' instagram', ' facebook',
            ' - sales contact', ' sales contact'
        ]
        for pattern in noise_patterns:
            if name.endswith(pattern):
                name = name[:-len(pattern)].strip()
        
        # Remove trailing punctuation
        name = name.rstrip('.,;:!?-')
        
        return name if name else None
    
    def load_from_designer_showrooms(self):
        """Extract brands from designer_showrooms.csv"""
        print("Loading brands from designer_showrooms.csv...")
        path = Path('data/processed/designer_showrooms.csv')
        
        if not path.exists():
            print(f"  ⚠️ File not found: {path}")
            return 0
        
        with open(path, encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                brand_name = self.normalize_name(row.get('brand_name', ''))
                if not brand_name:
                    continue
                
                if brand_name not in self.brands:
                    self.brands[brand_name] = {
                        'brand_name': row.get('brand_name', '').strip(),
                        'categories': row.get('categories', 'N/A'),
                        'city': row.get('primary_city', 'N/A'),
                        'country': row.get('country', 'N/A'),
                        'region': row.get('region', 'N/A'),
                        'phone': row.get('phone', 'N/A'),
                        'email': row.get('email', 'N/A'),
                        'instagram': row.get('instagram', 'N/A'),
                        'facebook': row.get('facebook', 'N/A'),
                        'website': 'N/A',
                        'source': 'designer_showrooms',
                        'source_url': row.get('source_url', 'N/A'),
                        'brand_id': hashlib.md5(brand_name.encode()).hexdigest()[:12],
                        'scraped_date': row.get('scraped_date', datetime.now().strftime('%Y-%m-%d'))
                    }
                    count += 1
        
        print(f"  ✓ Loaded {count} unique brands from designer showrooms")
        return count
    
    def load_from_master_leads(self):
        """Extract brands from master_leads.csv"""
        print("Loading brands from master_leads.csv...")
        path = Path('data/processed/master_leads.csv')
        
        if not path.exists():
            print(f"  ⚠️ File not found: {path}")
            return 0
        
        with open(path, encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                # Only extract from Designer showrooms, not multi-label
                lead_type = row.get('lead_type', '')
                if 'Designer' not in lead_type:
                    continue
                
                brand_name = self.normalize_name(row.get('company_name', ''))
                if not brand_name:
                    continue
                
                if brand_name not in self.brands:
                    self.brands[brand_name] = {
                        'brand_name': row.get('company_name', '').strip(),
                        'categories': 'N/A',
                        'city': row.get('city', 'N/A'),
                        'country': row.get('country', 'N/A'),
                        'region': row.get('region', 'N/A'),
                        'phone': row.get('phone', 'N/A'),
                        'email': row.get('email', 'N/A'),
                        'instagram': row.get('instagram', 'N/A'),
                        'facebook': row.get('facebook', 'N/A'),
                        'website': row.get('website', 'N/A'),
                        'source': 'master_leads',
                        'source_url': row.get('source_url', 'N/A'),
                        'brand_id': hashlib.md5(brand_name.encode()).hexdigest()[:12],
                        'scraped_date': row.get('scraped_date', datetime.now().strftime('%Y-%m-%d'))
                    }
                    count += 1
        
        print(f"  ✓ Loaded {count} unique brands from master leads")
        return count
    
    def save_brands_csv(self, output_path='data/processed/brands.csv'):
        """Save deduplicated brands to CSV"""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Sort by region, country, city, brand_name
        sorted_brands = sorted(
            self.brands.values(),
            key=lambda x: (
                x['region'],
                x['country'],
                x['city'],
                x['brand_name'].lower()
            )
        )
        
        fieldnames = [
            'brand_id', 'brand_name', 'categories', 'city', 'country', 'region',
            'phone', 'email', 'website', 'instagram', 'facebook',
            'source', 'source_url', 'scraped_date'
        ]
        
        with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(sorted_brands)
        
        print(f"\n[OK] Saved {len(sorted_brands)} brands to {output_path}")
        return len(sorted_brands)
    
    def run(self):
        """Main extraction workflow"""
        print("="*80)
        print("Brand Extractor - Consolidate brands from multiple sources")
        print("="*80)
        
        total = 0
        total += self.load_from_designer_showrooms()
        total += self.load_from_master_leads()
        
        print(f"\nTotal unique brands collected: {len(self.brands)}")
        
        # Breakdown by region
        from collections import Counter
        regions = Counter(b['region'] for b in self.brands.values())
        print("\nBreakdown by region:")
        for region, count in regions.items():
            print(f"  {region}: {count}")
        
        # Breakdown by country (top 10)
        countries = Counter(b['country'] for b in self.brands.values())
        print("\nTop 10 countries:")
        for country, count in countries.most_common(10):
            print(f"  {country}: {count}")
        
        # Save to CSV
        self.save_brands_csv()
        
        # Gap analysis
        print("\n" + "="*80)
        print("GAP ANALYSIS:")
        print("="*80)
        print(f"Target: 500 brands")
        print(f"Current: {len(self.brands)} brands")
        print(f"Gap: {max(0, 500 - len(self.brands))} brands needed")
        print(f"\n⚠️ CRITICAL: {regions.get('Asia', 0)} Asia brands found (target: ~250)")
        print(f"✓ Europe brands: {regions.get('Europe', 0)}")


if __name__ == '__main__':
    extractor = BrandExtractor()
    extractor.run()
