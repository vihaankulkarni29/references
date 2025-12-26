import asyncio
import random
import urllib.parse
import pandas as pd
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

# --- TARGETS WITH SECTORS ---
TARGETS = [
    ("The Giving Movement", "Streetwear"),
    ("Amongst Few", "Streetwear"),
    ("Les Benjamins Dubai", "Streetwear"),
    ("Concepts Dubai", "Streetwear"),
    ("Ounass", "Luxury Fashion"),
    ("Level Shoes", "Luxury Retail"),
    ("Sole DXB", "Street Culture"),
    ("Break The Block", "Street Culture"),
    
    ("Soho Garden DXB", "Nightlife"),
    ("Bla Bla Dubai", "Nightlife"),
    ("FIVE Hotels and Resorts", "Hospitality"),
    ("Cove Beach Dubai", "Nightlife"),
    ("White Dubai", "Nightlife"),
    ("Coca-Cola Arena", "Events"),
    ("Dubai Design District (d3)", "Design Hub"),
    
    ("Virgin Mobile UAE", "Gen-Z Tech"),
    ("Swapp Car Subscription", "Gen-Z Tech"),
    ("CAFU", "Gen-Z Tech"),
    ("Tabby", "Fintech"),
    ("Noon", "E-commerce"),
    ("Deliveroo UAE", "Tech/Food"),
    ("Talabat", "Tech/Food"),
    
    ("Ellington Properties", "Design Real Estate"),
    ("Omniyat", "Design Real Estate"),
    ("Al Barari", "Design Real Estate"),
    ("Kerzner International", "Hospitality")
]

async def get_website_ddg(page, company):
    """Finds Official Website using DuckDuckGo Browser Search."""
    print(f"  Finding website for {company}...")
    try:
        query = urllib.parse.quote(f"{company} official website Dubai")
        await page.goto(f"https://duckduckgo.com/?q={query}&t=h_&ia=web", timeout=60000)
        await asyncio.sleep(2)
        
        links = page.locator("a[data-testid='result-title-a']")
        count = await links.count()
        
        for i in range(min(count, 3)):
            href = await links.nth(i).get_attribute("href")
            if href and "http" in href:
                if not any(x in href.lower() for x in ["linkedin", "wikipedia", "facebook", "instagram", "twitter", "tiktok"]):
                    print(f"    [Web] Found: {href}")
                    return href
        return "Not Found"
    except Exception as e:
        print(f"    [Web] Error: {e}")
        return "Error"

async def get_instagram_ddg(page, company):
    """Finds Instagram using DuckDuckGo Browser Search."""
    print(f"  Hunting Instagram for {company}...")
    try:
        # Targeted site search
        query = urllib.parse.quote(f"site:instagram.com {company} Dubai")
        await page.goto(f"https://duckduckgo.com/?q={query}&t=h_&ia=web", timeout=60000)
        await asyncio.sleep(2)
        
        links = page.locator("a[data-testid='result-title-a']")
        count = await links.count()
        
        for i in range(min(count, 3)):
            href = await links.nth(i).get_attribute("href")
            # Filter for pure profile links (avoiding tags/explore if possible, though DDG is usually good)
            if href and "instagram.com" in href:
                if not any(x in href for x in ["/p/", "/reel/", "/explore/", "/tags/", "/location/"]):
                     print(f"    [IG] Found: {href}")
                     return href
        return "Not Found"
    except Exception as e:
        print(f"    [IG] Error: {e}")
        return "Error"

async def run_culture_hunter():
    results = []
    output_file = "output/Dubai_Culture_Leads.csv"
    print(f"🚀 Starting Culture Hunter on {len(TARGETS)} Brands...")
    
    async with async_playwright() as p:
        # Launch with ignore_https_errors for resilience
        browser = await p.chromium.launch(headless=False, args=['--ignore-certificate-errors'])
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        for company, sector in TARGETS:
            print(f"[{company}] ({sector}) Processing...")
            
            # 1. Discovery
            website = await get_website_ddg(page, company)
            await asyncio.sleep(random.uniform(2, 4))
            
            instagram = await get_instagram_ddg(page, company)
            await asyncio.sleep(random.uniform(2, 4))
            
            # 2. Smart Links
            encoded = urllib.parse.quote(company)
            link_creative = f"https://www.linkedin.com/search/results/people/?keywords=(Creative%20Director%20OR%20Art%20Director)%20{encoded}%20Dubai"
            link_brand = f"https://www.linkedin.com/search/results/people/?keywords=(Head%20of%20Brand%20OR%20Brand%20Director)%20{encoded}%20Dubai"
            link_marketing = f"https://www.linkedin.com/search/results/people/?keywords=Marketing%20Director%20{encoded}%20Dubai"
            
            results.append({
                "Company": company,
                "Sector": sector,
                "Website": website,
                "Instagram_Link": instagram,
                "LinkedIn_Creative_Search": link_creative,
                "LinkedIn_Brand_Search": link_brand,
                "LinkedIn_Marketing_Search": link_marketing
            })
            
            # Incremental Save
            pd.DataFrame(results).to_csv(output_file, index=False)
            
        await browser.close()
    
    print(f"✅ Data saved to {output_file}")

if __name__ == "__main__":
    asyncio.run(run_culture_hunter())
