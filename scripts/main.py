import asyncio
import pandas as pd
import time
import random
from src.job_discovery import find_hiring_companies
from src.linkedin_pivot import find_decision_maker
from src.tech_checker import analyze_site
from src.utils import setup_logging

async def main():
    setup_logging()
    print("Starting Dubai Whale Hunter (Pain Point Edition)...")
    
    # Phase 1: Job Board X-Ray (The Pain Point Finder)
    # Finding companies hiring for Jira/Agile
    job_keywords = ["Jira", "Scrum Master", "Project Coordinator"]
    companies = await find_hiring_companies(job_keywords)
    
    # Fallback if stealth fails
    if not companies:
        print("No hiring companies found (likely Stealth block). Using Fallback.")
        companies = [
            {'name': 'Landmark Group', 'hiring_signal': 'Mock-Jira', 'website': 'https://www.landmarkgroup.com'},
            {'name': 'Aramex', 'hiring_signal': 'Mock-Logistics', 'website': 'https://www.aramex.com'}
        ]
        
    print(f"Found {len(companies)} companies with hiring signals.")
    
    # Phase 2 & 3: Enrichment
    results = []
    for i, company in enumerate(companies):
        print(f"[{i+1}/{len(companies)}] Processing {company['name']}...")
        
        # Tech Check (Phase 3) - Do first as URL is usually available or we can guess
        # If website is missing, we might skip or try to find it?
        # For now, rely on what Discovery gave us.
        tech_info = {}
        if company.get('website'):
            tech_info = analyze_site(company['website'])
        else:
            # Fallback for known companies
            if company['name'] == 'Emaar Properties':
                 tech_info = analyze_site('https://www.emaar.com')
            elif company['name'] == 'Damac Properties':
                 tech_info = analyze_site('https://www.damacproperties.com')
        
        # LinkedIn Pivot (Phase 2)
        dm_info = await find_decision_maker(company['name'])
        
        # Merge Data
        record = {**company, **dm_info, **tech_info}
        results.append(record)
        
        # Rate Limit with Jitter (User Enhancement)
        # "Add time.sleep(random.uniform(10, 20)) between company searches"
        delay = random.uniform(10, 20)
        print(f"Sleeping for {delay:.2f} seconds...")
        time.sleep(delay)
        
    # Export
    if results:
        df = pd.DataFrame(results)
        # Reorder columns for readability
        cols = ['name', 'industry', 'hiring_signal', 'dm_name', 'dm_linkedin', 'website', 'tech_stack', 'cms', 'localization', 'tech_debt_signal']
        # Filter strictly for existing columns
        existing_cols = [c for c in cols if c in df.columns]
        # detailed columns at the end
        extra_cols = [c for c in df.columns if c not in existing_cols]
        df = df[existing_cols + extra_cols]
        
        df.to_csv("leads.csv", index=False)
        print("Done! Leads saved to leads.csv")
        print(df.head())
    else:
        print("No leads generated.")

if __name__ == "__main__":
    asyncio.run(main())
