import asyncio
import re
import urllib.parse
import pandas as pd
import random
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

TARGETS = [
    "Amongst Few", "5ivepillars", "Qasimi", "Precious Trust", 
    "Midnight Sports", "SWEY Collective", "Finchitua", "The Giving Movement",
    "Concepts Dubai", "Les Benjamins Dubai",
    "ASICS Middle East", "Fred Perry Middle East", "G-Shock Middle East", 
    "New Balance Middle East", "Puma Middle East",
    "Kayali Fragrances", "Humantra", "DJI Middle East", "Faure Le Page Dubai",
    "25hours Hotel Dubai", "Mamafri", "The Maine Oyster Bar", "Bonbird", 
    "Pickl Dubai", "Mattar Farm", "Sole DXB Team",
    "Ziina", "Talabat", "Power Horse Energy Drink", "Fujifilm Middle East"
]

OUTPUT_FILE = "output/Sole_DXB_Leads.csv"

async def get_search_results(page, query):
    """Generic DDG Search."""
    try:
        encoded = urllib.parse.quote(query)
        await page.goto(f"https://duckduckgo.com/?q={encoded}&t=h_&ia=web", timeout=30000)
        await asyncio.sleep(2)
        return page.locator("a[data-testid='result-title-a']")
    except: return None

async def find_website_instagram(page, company):
    """Finds Website and IG Link."""
    website = "Not Found"
    instagram = "Not Found"
    
    # 1. Search for Official Site & Instagram
    links = await get_search_results(page, f"{company} official site instagram Dubai")
    if links:
        count = await links.count()
        for i in range(min(count, 5)):
            href = await links.nth(i).get_attribute("href")
            if not href: continue
            
            if "instagram.com" in href and instagram == "Not Found":
                if "/p/" not in href and "/reel/" not in href: # Avoid posts
                    instagram = href
            elif "http" in href and website == "Not Found":
                # Filter out social/wiki
                if not any(x in href.lower() for x in ["linkedin", "facebook", "twitter", "wikipedia", "tiktok", "instagram"]):
                    website = href
                    
    return website, instagram

async def scrape_phone(page, url):
    """Visits site and scrapes UAE phone."""
    if not url or "http" not in url: return ""
    print(f"    -> Scanning {url} for phone...")
    try:
        await page.goto(url, timeout=45000, wait_until="domcontentloaded")
        await asyncio.sleep(2)
        content = await page.content()
        
        # Strict UAE Validation
        valid_phones = set()
        raw = re.findall(r'(?:\+?971|00971|0)?[- .]?\d{2,3}[- .]?\d{3}[- .]?\d{4,}', content)
        for p in raw:
            clean = re.sub(r'\D', '', p)
            if clean.startswith('971'): clean = '0' + clean[3:]
            if clean.startswith('00971'): clean = '0' + clean[5:]
            
            fmt = None
            if len(clean) == 10 and clean.startswith(('050', '052', '054', '055', '056', '058')):
                fmt = f"+971 {clean[1:3]} {clean[3:6]} {clean[6:]}"
            elif len(clean) == 9 and clean.startswith(('02', '03', '04', '06', '07', '09')):
                fmt = f"+971 {clean[1]} {clean[2:5]} {clean[5:]}"
            elif clean.startswith('800') and len(clean) >= 7:
                fmt = clean
            
            if fmt: valid_phones.add(fmt)
            
        return ", ".join(list(valid_phones))
    except Exception as e:
        print(f"    -> Scan Error: {e}")
        return ""

async def find_location(page, company):
    """Finds Dubai Location snippet."""
    try:
        links = await get_search_results(page, f"{company} Dubai office address location")
        # Try to find snippet text from ID #r1-0 or article
        element = page.locator("#r1-0, article, .result").first
        if await element.count() > 0:
            txt = await element.text_content()
            return txt.strip().replace('\n', ' ')[:150] + "..."
        return "Not Found"
    except: return "Not Found"

async def run_sole_hunter():
    print(f"🚀 Starting Sole DXB Hunter on {len(TARGETS)} targets...")
    results = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=['--ignore-certificate-errors'])
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        for company in TARGETS:
            print(f"[{company}] Processing...")
            
            # 1. Discovery
            web, ig = await find_website_instagram(page, company)
            print(f"    -> Web: {web} | IG: {ig}")
            
            # 2. Phone Scan
            phone = ""
            if web != "Not Found":
                phone = await scrape_phone(page, web)
                print(f"    -> Phone: {phone}")
            
            # 3. Location
            loc = await find_location(page, company)
            print(f"    -> Loc: {loc}")
            
            results.append({
                "Company Name": company,
                "Website Link": web,
                "Social Media Link": ig,
                "Location": loc,
                "Phone Number": phone
            })
            
            # Incremental Save
            pd.DataFrame(results).to_csv(OUTPUT_FILE, index=False)
            await asyncio.sleep(random.uniform(1, 3))
            
        await browser.close()
    
    print(f"✅ Data saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(run_sole_hunter())
