import pandas as pd
import sys

# Force UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Load the CSV
df = pd.read_csv('output/Sole_DXB_Leads_Expanded.csv')

print("=" * 60)
print("SOLE DXB LEADS - DATA QUALITY REPORT")
print("=" * 60)

# 1. Basic Stats
print(f"\nTOTAL RECORDS: {len(df)}")
print(f"Expected: 113 companies\n")

# 2. Completeness Analysis
web_found = (df['Website Link'] != 'Not Found').sum()
ig_found = (df['Social Media Link'] != 'Not Found').sum()
phone_found = (df['Phone Number'].fillna('').str.strip() != '').sum()
loc_found = (df['Location'] != 'Online / Remote').sum()

print("DATA COMPLETENESS:")
print(f"  Website Found:    {web_found:3d} / {len(df)} ({web_found/len(df)*100:5.1f}%)")
print(f"  Instagram Found:  {ig_found:3d} / {len(df)} ({ig_found/len(df)*100:5.1f}%)")
print(f"  Phone Found:      {phone_found:3d} / {len(df)} ({phone_found/len(df)*100:5.1f}%)")
print(f"  Location Found:   {loc_found:3d} / {len(df)} ({loc_found/len(df)*100:5.1f}%)\n")

# 3. Phone Number Quality
phones_with_data = df[df['Phone Number'].fillna('').str.strip() != '']
print("PHONE NUMBER QUALITY:")
print(f"  Total with Phones: {len(phones_with_data)}")
if len(phones_with_data) > 0:
    valid_971 = phones_with_data['Phone Number'].str.contains(r'\+971', na=False).sum()
    print(f"  Valid +971 Format: {valid_971}")
    print("\n  Sample Phones:")
    for idx, row in phones_with_data.head(5).iterrows():
        print(f"    - {row['Company Name']}: {row['Phone Number']}")

# 4. Location Insights
physical_locations = df[df['Location'] != 'Online / Remote']
print(f"\nLOCATION INSIGHTS:")
print(f"  Physical Locations: {len(physical_locations)}")
print(f"  Online/Remote:      {(df['Location'] == 'Online / Remote').sum()}")

if len(physical_locations) > 0:
    print("\n  Sample Locations:")
    for idx, row in physical_locations.head(3).iterrows():
        loc = str(row['Location'])[:70] + "..." if len(str(row['Location'])) > 70 else str(row['Location'])
        print(f"    - {row['Company Name']}: {loc}")

# 5. Missing Data Report
print("\nMISSING DATA:")
missing_all = df[(df['Website Link'] == 'Not Found') & 
                 (df['Social Media Link'] == 'Not Found') & 
                 (df['Phone Number'].fillna('').str.strip() == '')]

if len(missing_all) > 0:
    print(f"  Companies with NO contact info: {len(missing_all)}")
    for company in missing_all['Company Name'].tolist()[:5]:
        print(f"    - {company}")
else:
    print("  SUCCESS: All companies have at least one contact method!")

# 6. Complete Profiles
print("\nCOMPLETE PROFILES (All 4 fields):")
complete = df[(df['Website Link'] != 'Not Found') & 
              (df['Social Media Link'] != 'Not Found') & 
              (df['Phone Number'].fillna('').str.strip() != '') &
              (df['Location'] != 'Online / Remote')]

print(f"  Total: {len(complete)} companies")
if len(complete) > 0:
    for company in complete['Company Name'].head(5).tolist():
        print(f"    - {company}")

print("\n" + "=" * 60)
print("VALIDATION COMPLETE")
print("=" * 60)
