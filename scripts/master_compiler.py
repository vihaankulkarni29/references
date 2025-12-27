import asyncio
import re
import pandas as pd
import urllib.parse
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

# Files
FILE_MEDIA = "output/Dubai_Media_Contacts.csv"
FILE_CREATIVE = "output/Dubai_Creative_Leads.csv"
FILE_CULTURE = "output/Dubai_Culture_Leads_Enriched.csv"
OUTPUT_FILE = "output/Dubai_Master_Leads.csv"

# Global Set for deduplication
SEEN_COMPANIES = set()

def clean_phone_strict(text):
    """Applies strict UAE phone validation."""
    if not isinstance(text, str): return ""
    
    valid_numbers = set()
    # Split by comma if multiple numbers exist
    parts = text.split(',')
    
    for p in parts:
        # Remove non-digits
        clean = re.sub(r'\D', '', p)
        
        # Normalize
        if clean.startswith('971'): clean = '0' + clean[3:]
        if clean.startswith('00971'): clean = '0' + clean[5:]
        
        # Validate
        formatted = None
        if len(clean) == 10 and clean.startswith(('050', '052', '054', '055', '056', '058')):
            formatted = f"+971 {clean[1:3]} {clean[3:6]} {clean[6:]}"
        elif len(clean) == 9 and clean.startswith(('02', '03', '04', '06', '07', '09')):
            formatted = f"+971 {clean[1]} {clean[2:5]} {clean[5:]}"
        elif clean.startswith('800') and len(clean) >= 7:
            formatted = clean
            
        if formatted:
            valid_numbers.add(formatted)
            
    return ", ".join(list(valid_numbers))

async def get_dubai_hq(page, company):
    """Finds Dubai HQ Location snippet using DDG."""
    print(f"  📍 Locating HQ for {company}...")
    try:
        query = urllib.parse.quote(f"{company} Dubai office address location")
        await page.goto(f"https://duckduckgo.com/?q={query}&t=h_&ia=web", timeout=30000)
        await asyncio.sleep(2)
        print(f"    (Debug) Title: {await page.title()}")
        # content = await page.content()
        # print(f"    (Debug) HTML: {content[:1000]}") # Only enable if desperate
        
        # New Attempt: Generic 'article' or 'li' for results
        # DDG usually uses list items for results
        # .result__snippet = organic result text
        # .module__text = knowledge panel text
        # Try ID-based selector (r1-0 is usually the first result)
        element = page.locator("#r1-0, article, .result").first
        if await element.count() > 0:
            snippet = await element.text_content()
            return snippet.strip().replace('\n', ' ')[:150] + "..."
        
        return "Not Found"
    except Exception as e:
        return "Not Found"

async def run_master_compiler():
    print("🚀 Starting Master Compiler & HQ Locator...")
    
    master_data = []
    
    # 1. Load Data
    try:
        df_media = pd.read_csv(FILE_MEDIA)
        df_media['Sector'] = "Media/FMCG"
        df_media['Source'] = "Media"
    except: df_media = pd.DataFrame()

    try:
        df_creative = pd.read_csv(FILE_CREATIVE)
        df_creative['Sector'] = "Luxury/Design"
        df_creative['Source'] = "Creative"
    except: df_creative = pd.DataFrame()

    try:
        df_culture = pd.read_csv(FILE_CULTURE)
        # Culture already has Sector
        df_culture['Source'] = "Culture"
    except: df_culture = pd.DataFrame()
    
    # Normalize columns for merging
    # Map 'Scraped_Emails' -> 'Emails', 'Scraped_Phones' -> 'Phones'
    if 'Scraped_Emails' in df_culture.columns:
        df_culture['Emails'] = df_culture['Scraped_Emails']
        df_culture['Phones'] = df_culture['Scraped_Phones']
        
    # Combine frames
    all_dfs = [df_media, df_creative, df_culture]
    combined = pd.concat(all_dfs, ignore_index=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        for index, row in combined.iterrows():
            company = row.get('Company', 'Unknown')
            if company in SEEN_COMPANIES: continue
            SEEN_COMPANIES.add(company)
            
            print(f"[{company}] Processing...")
            
            # 1. Clean Phone
            raw_phone = str(row.get('Phones', ''))
            clean_phone = clean_phone_strict(raw_phone)
            
            # 2. Get HQ
            hq = await get_dubai_hq(page, company)
            print(f"    -> HQ: {hq}")
            
            # 3. Consolidate Row
            new_row = {
                "Company": company,
                "Sector": row.get('Sector', 'Unknown'),
                "Dubai_HQ": hq,
                "Website": row.get('Website', ''),
                "Clean_Phones": clean_phone,
                "Emails": row.get('Emails', ''),
                "Instagram": row.get('Scraped_Instagram', row.get('Instagram', '')),
                # Preserve various link columns if they exist, else empty
                "Link_Creative": row.get('Link_Creative_Dir', row.get('LinkedIn_Creative_Search', '')),
                "Link_Brand": row.get('Link_Visual_Head', row.get('LinkedIn_Brand_Search', '')),
                "Link_Marketing": row.get('LinkedIn_Marketing_Search', '')
            }
            master_data.append(new_row)
            
            # Incremental Save
            pd.DataFrame(master_data).to_csv(OUTPUT_FILE, index=False)
            
        await browser.close()
        
    print(f"✅ Master Leads saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(run_master_compiler())
