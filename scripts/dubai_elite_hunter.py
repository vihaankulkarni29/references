import asyncio
import random
import urllib.parse
import pandas as pd
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from duckduckgo_search import DDGS

# --- TARGETS: THE ELITE 10 ---
TARGETS = [
    "Chalhoub Group", "Al Tayer Group", "Majid Al Futtaim", 
    "Landmark Group", "GMG (Gulf Marketing Group)", "Apparel Group", 
    "Kitopi", "Careem", "Tabby", "MBC Group"
]

async def get_website_hybrid(page, company):
    # Strict Verification
    def is_relevant(url, name):
        name_slug = name.lower().split(' ')[0]
        if len(name_slug) < 3 and len(name.split(' ')) > 1:
             name_slug = name.lower().split(' ')[1]
        if "GMG" in name: name_slug = "gmg"
        domain = urllib.parse.urlparse(url).netloc.lower()
        if name_slug in domain: return True
        return False

    print(f"  Finding website for {company}...")

    # 1. DDG API
    try:
        results = DDGS().text(f"{company} official website Dubai", max_results=3)
        if results:
            for r in results:
                href = r.get('href', '')
                if href and "http" in href:
                    if not any(x in href.lower() for x in ["linkedin", "wikipedia", "facebook", "instagram"]):
                        if is_relevant(href, company):
                             print(f"    [DDG API] Found: {href}")
                             return href
    except: pass

    # 2. DDG Browser Fallback
    print("    [DDG Browser] searching...")
    try:
        query = urllib.parse.quote(f"{company} official website Dubai")
        await page.goto(f"https://duckduckgo.com/?q={query}&t=h_&ia=web")
        await asyncio.sleep(2)
        links = page.locator("a[data-testid='result-title-a']")
        count = await links.count()
        for i in range(min(count, 3)):
             href = await links.nth(i).get_attribute("href")
             if href and "http" in href:
                 if not any(x in href.lower() for x in ["linkedin", "wikipedia", "facebook", "instagram"]):
                     if is_relevant(href, company):
                         print(f"    [DDG Browser] Found: {href}")
                         return href
    except: pass

    # 3. Google Fallback
    print("    [Google] Checking Browser...")
    try:
        query = f"{company} official website Dubai"
        await page.goto(f"https://www.google.com/search?q={query}")
        
        # CAPTCHA Detection
        title = await page.title()
        content = await page.content()
        if "robot" in title.lower() or "captcha-form" in content or "unusual traffic" in content.lower():
             print("\n🚨 CAPTCHA DETECTED! Waiting 60s... 🚨")
             try:
                 await page.wait_for_selector("div#search, div#rso, div.g", timeout=60000)
                 print("    ✅ CAPTCHA Solved!")
             except: return "Error"

        await asyncio.sleep(random.uniform(2, 4))
        links = page.locator("div#search a[href], div#rso a[href], div.g a[href]")
        count = await links.count()
        for i in range(count):
            href = await links.nth(i).get_attribute("href")
            if href and "http" in href:
                 if not any(x in href.lower() for x in ["linkedin", "wikipedia", "facebook", "instagram"]):
                     if is_relevant(href, company):
                         print(f"    [Google] Found: {href}")
                         return href
        return "Not Found"
    except: return "Error"

async def get_instagram_handle(page, company):
    print(f"  Hunting Instagram for {company}...")
    try:
        query = urllib.parse.quote(f"site:instagram.com {company} Dubai")
        await page.goto(f"https://duckduckgo.com/?q={query}&t=h_&ia=web")
        await asyncio.sleep(2)
        links = page.locator("a[data-testid='result-title-a']")
        count = await links.count()
        for i in range(min(count, 3)):
                href = await links.nth(i).get_attribute("href")
                if "instagram.com" in href:
                    print(f"    [DDG Browser] Found IG: {href}")
                    return href
        return "Low Digital Presence"
    except: return "Error"

async def run_elite_hunter():
    results = []
    output_file = "Dubai_Elite_10_Refined.csv"
    print(f"🚀 Starting Elite 10 Hunter...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        for company in TARGETS:
            print(f"Analyzing: {company}...")
            website = await get_website_hybrid(page, company)
            instagram = await get_instagram_handle(page, company)
            
            email_format = "Unknown"
            if website and "http" in website:
                domain = urllib.parse.urlparse(website).netloc.replace("www.", "")
                email_format = f"firstname.lastname@{domain} (Unverified)"
            
            encoded = urllib.parse.quote(company)
            cmo_link = f"https://www.linkedin.com/search/results/people/?keywords=Chief%20Marketing%20Officer%20{encoded}%20Dubai"
            brand_link = f"https://www.linkedin.com/search/results/people/?keywords=(Head%20of%20Brand%20OR%20Brand%20Director)%20{encoded}%20Dubai"
            digital_link = f"https://www.linkedin.com/search/results/people/?keywords=(VP%20Digital%20OR%20Head%20of%20Digital)%20{encoded}%20Dubai"
            
            results.append({
                "Company": company,
                "Website": website,
                "Instagram_Link": instagram,
                "LinkedIn_CMO_Search": cmo_link,
                "LinkedIn_Brand_Search": brand_link,
                "LinkedIn_Digital_Search": digital_link,
                "Probable_Email_Format": email_format
            })
            pd.DataFrame(results).to_csv(output_file, index=False)
            await asyncio.sleep(2)
            
        await browser.close()
    print("Done.")

if __name__ == "__main__":
    asyncio.run(run_elite_hunter())
