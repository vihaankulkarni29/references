import asyncio
import re
import urllib.parse
import pandas as pd
import random
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

TARGETS = [
    # Previously Existed
    "The Giving Movement", "Concepts Dubai", "Les Benjamins Dubai",
    "ASICS Middle East", "Fred Perry Middle East", "G-Shock Middle East",
    "New Balance Middle East", "Puma Middle East",
    "Kayali Fragrances", "Humantra", "DJI Middle East", "Faure Le Page Dubai",
    "25hours Hotel Dubai", "Mamafri", "The Maine Oyster Bar", "Bonbird",
    "Pickl Dubai", "Mattar Farm", "Sole DXB Team",
    "Ziina", "Talabat", "Power Horse Energy Drink", "Fujifilm Middle East",
    
    # New Batch (Fashion/Brands)
    "BLTNM", "Bootleg", "Maison QR", "Samurai Farai", "Tasado", "5ivepillars",
    "A.P.C.", "Adaye", "Amongst Few", "AOTA", "Ashri Skin", "Atlal From Galbi",
    "Badibanga", "BLANK", "Champion", "Congo Clothing Company", "F5", "Finchitua",
    "Hoka", "Jokes Aside", "Leaf Apparel", "Midnight Sports", "Mqaaar", "No Borders",
    "Precious Trust", "Prince Politique", "Qasimi", "Retropia", "SN3 Studio",
    "SWEY Collective", "Umbro", "02 Marketplace", "Koromandel BY DARSHAN PAL",
    "Maisha", "THOU Gallery", "Babwê", "Basliq", "Dastaangoi", "Eiido",
    "International Baddies Worldwide", "Ncapped", "Saint Ayun", "Shooters Shoot",
    "Viewpoint Color Magazine",
    
    # Brand Pavilion
    "OFA", "28Natelier", "Absent Findings", "Datecrete Studio & Lab", "FIGURES",
    "FullMetal", "Marsy", "NearTwins", "Peace Venue", "Safran World", "Suez", "VANDART",
    
    # Food & Beverage
    "Alokozay", "Club Ocha", "Drink IQ", "Matter Matcha", "Soul Sante", "My Govindas",
    "OT Cookies", "PDL Coffee Co", "Pop Culture", "Soil", "Al Mallah", "Slice 45",
    "Barrad", "Bigface", "Carnie Store", "Rudy’s Diner", "Eleven Green", "Fadie Cakes",
    "Kokum & Kari", "Mama Fri", "Mashawi", "Mirzam", "Miss Lily’s",
    "Neighbourhood Food Hall", "Neo Temaki", "Noon", "One Life", "PIEHAUS",
    "Sandwich Nerds", "Shake Shack", "TACOS CAMINO", "TONTON", "Varak", "Yava"
]

OUTPUT_FILE = "output/Sole_DXB_Leads_Expanded.csv"

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
    
    # Simple search for distinct assets
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
    """Finds Dubai HQ snippet using Multi-Query + Keyword validation."""
    queries = [
        f"{company} Dubai office address",
        f"{company} store location Dubai",
        f"{company} HQ address Dubai"
    ]
    
    keywords = ["Building", "Street", "Road", "Box", "Floor", "Unit", "Al Quoz", "d3", "Design District", "Mall", "Tower"]
    
    for q in queries:
        try:
            encoded = urllib.parse.quote(q)
            await page.goto(f"https://duckduckgo.com/?q={encoded}&t=h_&ia=web", timeout=15000)
            await asyncio.sleep(1.5)
            
            # Use robust selector for snippet (First result snippet)
            element = page.locator("#r1-0, article, .result").first
            if await element.count() > 0:
                txt = await element.text_content()
                clean_txt = txt.strip().replace('\n', ' ')
                
                # Keyword Check
                if any(k.lower() in clean_txt.lower() for k in keywords):
                    return clean_txt[:150] + "..."
                    
        except: continue
        
    return "Online / Remote"

async def run_sole_hunter():
    # Remove duplicates
    unique_targets = list(set(TARGETS))
    print(f"🚀 Starting Sole DXB Hunter on {len(unique_targets)} targets...")
    results = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=['--ignore-certificate-errors'])
        context = await browser.new_context(ignore_https_errors=True)
        
        # Block heavy resources
        await context.route("**/*", lambda route: route.abort() 
            if route.request.resource_type in ["image", "media", "font", "stylesheet"] 
            else route.continue_())
            
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        for company in unique_targets:
            print(f"[{company}] Processing...")
            
            # 1. Discovery
            web, ig = await find_website_instagram(page, company)
            print(f"    -> Web: {web} | IG: {ig}")
            
            # 2. Phone Scan
            phone = ""
            if web != "Not Found":
                phone = await scrape_phone(page, web)
                print(f"    -> Phone: {phone}")
            
            # 3. Location (Smart)
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
            await asyncio.sleep(random.uniform(1, 2))
            
        await browser.close()
    
    print(f"✅ Data saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(run_sole_hunter())
