"""Quick analysis of potential brand sources"""
import csv
from collections import Counter

# Load master leads
with open('data/processed/master_leads.csv', encoding='utf-8-sig') as f:
    leads = list(csv.DictReader(f))

print(f"Total leads in master_leads.csv: {len(leads)}")
print(f"\nLead type breakdown:")
type_counts = Counter(r['lead_type'] for r in leads)
for lead_type, count in type_counts.items():
    print(f"  {lead_type}: {count}")

print(f"\nRegion breakdown:")
region_counts = Counter(r['region'] for r in leads)
for region, count in region_counts.items():
    print(f"  {region}: {count}")

print(f"\nCountry breakdown:")
country_counts = Counter(r['country'] for r in leads)
for country, count in sorted(country_counts.items(), key=lambda x: -x[1])[:10]:
    print(f"  {country}: {count}")

# Check designer_showrooms.csv
print("\n" + "="*80)
with open('data/processed/designer_showrooms.csv', encoding='utf-8-sig') as f:
    designer_showrooms = list(csv.DictReader(f))

print(f"Total designer_showrooms.csv records: {len(designer_showrooms)}")
print(f"\nRegion breakdown:")
region_counts = Counter(r['region'] for r in designer_showrooms)
for region, count in region_counts.items():
    print(f"  {region}: {count}")

# Check for Asia records
asia_records = [r for r in designer_showrooms if r['region'] == 'Asia']
print(f"\nAsia records: {len(asia_records)}")
if asia_records:
    print("Sample Asia records:")
    for r in asia_records[:3]:
        print(f"  - {r['brand_name']} | {r['primary_city']}, {r['country']}")

# Strategy recommendation
print("\n" + "="*80)
print("BRAND EXTRACTION STRATEGY:")
print("="*80)
print(f"1. Current leads (showrooms): {len(leads)} - many are already brands")
print(f"2. Designer showrooms not in merge: {len(designer_showrooms) - len([r for r in leads if 'designer_showrooms' in r.get('source', '')])}")
print(f"3. Need to find: ~{500 - len(leads)} more unique brands")
print("\nRecommended approach:")
print("  A. Extract brand_name from designer_showrooms → brands.csv")
print("  B. Check fashion weeks 'digital' pages for brand profiles")
print("  C. Check for Asia-specific fashion weeks/showrooms")
