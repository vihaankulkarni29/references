"""
Master leads merger and deduplicator.
Merges showrooms, designer_showrooms, and any other lead sources into master_leads.csv.
Normalizes company names, emails, websites for deduplication.
"""
import csv
import re
from pathlib import Path
from typing import List, Dict, Set, Tuple
from datetime import datetime


class LeadMerger:
    def __init__(self):
        self.data_dir = Path('data/processed')
        self.output_file = self.data_dir / 'master_leads.csv'
        
        # Source files
        self.sources = {
            'showrooms': self.data_dir / 'master_leads.csv',  # Original showrooms data
            'designer_showrooms': self.data_dir / 'designer_showrooms.csv',
        }
        
    def normalize_name(self, name: str) -> str:
        """Normalize company name for deduplication"""
        if not name:
            return ''
        # lowercase, remove extra spaces, remove common suffixes/prefixes
        n = name.lower().strip()
        n = re.sub(r'\s+', ' ', n)
        # Remove common business suffixes
        n = re.sub(r'\s+(showroom|sales department|sales contact|instagram|facebook|twitter)$', '', n, flags=re.IGNORECASE)
        # Remove trailing punctuation
        n = re.sub(r'[,\.\-\s]+$', '', n)
        return n.strip()
    
    def normalize_email(self, email: str) -> str:
        """Normalize email for deduplication"""
        if not email or email in ['N/A', '']:
            return ''
        return email.lower().strip()
    
    def normalize_website(self, website: str) -> str:
        """Normalize website for deduplication"""
        if not website or website in ['N/A', '']:
            return ''
        # Remove protocol, trailing slash, www
        w = website.lower().strip()
        w = re.sub(r'^https?://', '', w)
        w = re.sub(r'^www\.', '', w)
        w = re.sub(r'/$', '', w)
        return w
    
    def get_dedupe_key(self, record: Dict[str, str]) -> Tuple[str, str, str]:
        """Generate deduplication key from record"""
        name = self.normalize_name(record.get('company_name') or record.get('brand_name', ''))
        email = self.normalize_email(record.get('email', ''))
        website = self.normalize_website(record.get('website', ''))
        city = (record.get('city') or record.get('primary_city', '')).lower().strip()
        
        # Key is (normalized_name, city, email_or_website)
        # If both email and website are present, prefer website as it's more stable
        contact = website if website else email
        return (name, city, contact)
    
    def load_showrooms(self) -> List[Dict[str, str]]:
        """Load original showrooms (master_leads.csv)"""
        records = []
        file_path = self.sources['showrooms']
        if not file_path.exists():
            print(f"Showrooms file not found: {file_path}")
            return records
        
        with file_path.open('r', encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Map to standard schema
                records.append({
                    'lead_type': 'Multi-Label Showroom',
                    'company_name': row.get('company_name', ''),
                    'description': row.get('description', ''),
                    'email': row.get('email', ''),
                    'phone': row.get('phone', ''),
                    'website': row.get('website', ''),
                    'instagram': row.get('instagram', ''),
                    'facebook': row.get('facebook', ''),
                    'city': row.get('city', ''),
                    'country': row.get('country', ''),
                    'region': row.get('region', ''),
                    'source': 'showrooms',
                    'source_url': row.get('source_url', ''),
                    'scraped_date': row.get('scraped_date', '')
                })
        
        print(f"Loaded {len(records)} showrooms")
        return records
    
    def load_designer_showrooms(self) -> List[Dict[str, str]]:
        """Load designer showrooms"""
        records = []
        file_path = self.sources['designer_showrooms']
        if not file_path.exists():
            print(f"Designer showrooms file not found: {file_path}")
            return records
        
        with file_path.open('r', encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Map to standard schema
                records.append({
                    'lead_type': 'Designer Showroom',
                    'company_name': row.get('brand_name', ''),
                    'description': row.get('description', '') or row.get('categories', ''),
                    'email': row.get('email', ''),
                    'phone': row.get('phone', ''),
                    'website': '',  # Designer showrooms don't have website field
                    'instagram': row.get('instagram', ''),
                    'facebook': row.get('facebook', ''),
                    'city': row.get('primary_city', ''),
                    'country': row.get('country', ''),
                    'region': row.get('region', ''),
                    'source': 'designer_showrooms',
                    'source_url': row.get('source_url', ''),
                    'scraped_date': row.get('scraped_date', '')
                })
        
        print(f"Loaded {len(records)} designer showrooms")
        return records
    
    def merge_records(self, rec1: Dict[str, str], rec2: Dict[str, str]) -> Dict[str, str]:
        """Merge two duplicate records, preferring non-empty values"""
        merged = rec1.copy()
        
        # For each field, prefer non-empty value
        for key in rec2:
            val1 = (merged.get(key) or '').strip()
            val2 = (rec2.get(key) or '').strip()
            
            # Skip N/A values
            if val1 in ['N/A', '']:
                val1 = ''
            if val2 in ['N/A', '']:
                val2 = ''
            
            # Prefer longer/more complete value
            if not val1 and val2:
                merged[key] = val2
            elif val1 and val2 and len(val2) > len(val1):
                # For certain fields, prefer longer value (description, phone, etc)
                if key in ['description', 'phone', 'email', 'website', 'instagram', 'facebook']:
                    merged[key] = val2
        
        # Merge lead_type if different
        if rec1.get('lead_type') != rec2.get('lead_type'):
            types = [rec1.get('lead_type', ''), rec2.get('lead_type', '')]
            merged['lead_type'] = ' / '.join([t for t in types if t])
        
        # Merge sources
        sources = [rec1.get('source', ''), rec2.get('source', '')]
        merged['source'] = ' + '.join([s for s in sources if s and s not in merged.get('source', '')])
        
        return merged
    
    def deduplicate(self, records: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Deduplicate records based on normalized key"""
        seen: Dict[Tuple[str, str, str], Dict[str, str]] = {}
        duplicates = 0
        
        for rec in records:
            key = self.get_dedupe_key(rec)
            
            # Skip if key is too weak (no name or all empty)
            if not key[0] or all(not k for k in key):
                continue
            
            if key in seen:
                # Merge with existing record
                seen[key] = self.merge_records(seen[key], rec)
                duplicates += 1
            else:
                seen[key] = rec
        
        print(f"Removed {duplicates} duplicate records")
        return list(seen.values())
    
    def run(self):
        """Main merge and dedupe workflow"""
        print("=" * 80)
        print("Master Leads Merger & Deduplicator")
        print("=" * 80)
        
        all_records = []
        
        # Load all sources
        all_records.extend(self.load_showrooms())
        all_records.extend(self.load_designer_showrooms())
        
        print(f"\nTotal records before deduplication: {len(all_records)}")
        
        # Deduplicate
        deduped = self.deduplicate(all_records)
        
        print(f"Total records after deduplication: {len(deduped)}")
        
        # Sort by region, country, city, company name
        deduped.sort(key=lambda x: (
            x.get('region', ''),
            x.get('country', ''),
            x.get('city', ''),
            x.get('company_name', '')
        ))
        
        # Add merged_at timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for rec in deduped:
            rec['merged_at'] = timestamp
        
        # Save to CSV
        if deduped:
            fieldnames = [
                'lead_type', 'company_name', 'description', 'email', 'phone',
                'website', 'instagram', 'facebook', 'city', 'country', 'region',
                'source', 'source_url', 'scraped_date', 'merged_at'
            ]
            
            self.output_file.parent.mkdir(parents=True, exist_ok=True)
            with self.output_file.open('w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for rec in deduped:
                    writer.writerow(rec)
            
            print(f"\n[OK] Saved {len(deduped)} merged leads to {self.output_file}")
            
            # Print summary by source
            print("\nBreakdown by source:")
            source_counts = {}
            for rec in deduped:
                src = rec.get('source', 'unknown')
                source_counts[src] = source_counts.get(src, 0) + 1
            
            for src, count in sorted(source_counts.items()):
                print(f"  {src}: {count}")
            
            # Print summary by region
            print("\nBreakdown by region:")
            region_counts = {}
            for rec in deduped:
                rgn = rec.get('region', 'unknown')
                region_counts[rgn] = region_counts.get(rgn, 0) + 1
            
            for rgn, count in sorted(region_counts.items()):
                print(f"  {rgn}: {count}")
        else:
            print("\nNo records to save")


if __name__ == '__main__':
    merger = LeadMerger()
    merger.run()
