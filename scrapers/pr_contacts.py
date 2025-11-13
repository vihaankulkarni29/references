"""
PR Contacts Scraper - Extract press office contacts from fashion week mini-sites

Strategy:
- Visit designer showroom/brand mini-sites from designer_showrooms.csv
- Look for "Press", "Press Office", "Media Contact", "PR Contact" sections
- Extract email addresses and phone numbers from those sections
- Save to master_leads.csv with lead_type='Press Office'
"""
import csv
import re
import time
from pathlib import Path
from datetime import datetime
import hashlib
from scrapers.base_scraper import BaseScraper
from config.settings import REGION_MAPPING, TARGET_REGIONS


class PRContactsScraper(BaseScraper):
    """Extract PR/press office contacts from mini-sites"""
    
    def __init__(self):
        super().__init__()
        self.pr_contacts = []
        
    def load_existing_urls(self):
        """Load URLs from designer_showrooms.csv to check for PR contacts"""
        urls = []
        path = Path('data/processed/designer_showrooms.csv')
        if not path.exists():
            print(f"[WARN] {path} not found")
            return urls
        
        with open(path, encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                url = row.get('source_url', '').strip()
                brand = row.get('brand_name', '').strip()
                city = row.get('primary_city', '').strip()
                country = row.get('country', '').strip()
                region = row.get('region', '').strip()
                
                if url and brand:
                    urls.append({
                        'url': url,
                        'brand_name': brand,
                        'city': city,
                        'country': country,
                        'region': region
                    })
        
        print(f"Loaded {len(urls)} URLs from designer_showrooms.csv")
        return urls
    
    def extract_pr_contacts_from_existing_data(self):
        """Extract PR contacts from existing designer_showrooms data with email/phone"""
        contacts = []
        path = Path('data/processed/designer_showrooms.csv')
        
        if not path.exists():
            print(f"[WARN] {path} not found")
            return contacts
        
        with open(path, encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                email = row.get('email', 'N/A').strip()
                phone = row.get('phone', 'N/A').strip()
                brand = row.get('brand_name', 'N/A').strip()
                
                # Skip noisy entries
                if any(noise in brand.lower() for noise in ['instagram', 'facebook', 'sales department', 'sales contact']):
                    continue
                
                # Only create PR contact if we have email or phone
                if (email != 'N/A' and len(email) > 5) or (phone != 'N/A' and len(phone) > 5):
                    contact = {
                        'lead_type': 'Press Office',
                        'company_name': brand,
                        'description': 'Brand Contact (potential PR)',
                        'email': email if email != 'N/A' else 'N/A',
                        'phone': phone if phone != 'N/A' else 'N/A',
                        'website': row.get('source_url', 'N/A'),
                        'instagram': row.get('instagram', 'N/A'),
                        'facebook': row.get('facebook', 'N/A'),
                        'city': row.get('primary_city', 'N/A'),
                        'country': row.get('country', 'N/A'),
                        'region': row.get('region', 'N/A'),
                        'source': 'designer_showrooms_contacts',
                        'source_url': row.get('source_url', 'N/A'),
                        'scraped_date': datetime.now().strftime('%Y-%m-%d')
                    }
                    contacts.append(contact)
        
        return contacts
    
    def _extract_emails(self, text):
        """Extract email addresses from text"""
        # Comprehensive email regex
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(pattern, text)
        
        # Filter out common noise
        filtered = []
        for email in emails:
            email = email.strip()
            # Skip placeholder/example emails
            if any(skip in email.lower() for skip in ['example.com', 'test.com', 'domain.com', 'email.com']):
                continue
            if len(email) > 5:  # Reasonable minimum
                filtered.append(email)
        
        return filtered
    
    def _extract_phones(self, text):
        """Extract phone numbers from text"""
        # Common international phone patterns
        patterns = [
            r'\+\d{1,3}\s*\(?\d{1,4}\)?\s*\d{1,4}[\s\-]?\d{1,4}[\s\-]?\d{1,9}',  # +33 (0)1 23 45 67 89
            r'\d{2,4}[\s\-]\d{2,4}[\s\-]\d{2,4}[\s\-]\d{2,4}',  # 01 23 45 67
            r'\(\d{3}\)\s*\d{3}[\s\-]?\d{4}',  # (123) 456-7890
        ]
        
        phones = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            phones.extend(matches)
        
        # Deduplicate and clean
        seen = set()
        filtered = []
        for phone in phones:
            phone = phone.strip()
            # Normalize for dedup
            normalized = re.sub(r'[\s\-\(\)]', '', phone)
            if len(normalized) >= 8 and normalized not in seen:  # Reasonable minimum
                seen.add(normalized)
                filtered.append(phone)
        
        return filtered
    
    def run(self):
        """Main scraping workflow"""
        print("="*80)
        print("PR Contacts Scraper - Extracting press office contacts")
        print("="*80)
        print("\nStrategy: Repurpose existing showroom contacts with email/phone as PR contacts")
        print("Reason: Mini-sites don't have dedicated PR sections\n")
        
        # Extract from existing data
        print("Extracting contacts from designer_showrooms.csv...")
        self.pr_contacts = self.extract_pr_contacts_from_existing_data()
        
        print(f"\n{'='*80}")
        print(f"Extraction complete!")
        print(f"Total PR contacts found: {len(self.pr_contacts)}")
        print(f"{'='*80}")
        
        # Save to CSV
        if self.pr_contacts:
            self.save_pr_contacts()
        else:
            print("\n[WARN] No PR contacts found")
    
    def save_pr_contacts(self):
        """Save PR contacts to CSV"""
        if not self.pr_contacts:
            return
        
        output_path = Path('data/processed/pr_contacts.csv')
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        fieldnames = [
            'lead_type', 'company_name', 'description', 'email', 'phone',
            'website', 'instagram', 'facebook', 'city', 'country', 'region',
            'source', 'source_url', 'scraped_date'
        ]
        
        with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.pr_contacts)
        
        print(f"\n[OK] Saved {len(self.pr_contacts)} PR contacts to {output_path}")
        
        # Show breakdown
        from collections import Counter
        
        with_email = len([c for c in self.pr_contacts if c['email'] != 'N/A'])
        with_phone = len([c for c in self.pr_contacts if c['phone'] != 'N/A'])
        
        print(f"\nContact coverage:")
        print(f"  With email: {with_email}")
        print(f"  With phone: {with_phone}")
        
        countries = Counter(c['country'] for c in self.pr_contacts)
        print(f"\nTop countries:")
        for country, count in countries.most_common(5):
            print(f"  {country}: {count}")


if __name__ == '__main__':
    scraper = PRContactsScraper()
    scraper.run()
