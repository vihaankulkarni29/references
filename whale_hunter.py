import asyncio
import random
import os
import urllib.parse
import pandas as pd
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from duckduckgo_search import DDGS 

# --- THE "WHALE" LIST ---
TARGET_COMPANIES = [
    # Construction / Real Estate
    "ALEC Engineering & Contracting", "ASGC Construction", "Arabian Construction Company",
    "Khansaheb Civil Engineering", "Wade Adams Contracting", "Dutco Balfour Beatty",
    "Emaar Development", "Damac Properties", "Nakheel", "Sobha Realty",
    "Azizi Developments", "Meraas", "Danube Properties", "Ellington Properties",
    "Omniyat", "Al Naboodah Construction", "Trojan Construction Group",
    
    # Logistics
    "DP World", "Aramex", "Emirates SkyCargo", "Tristar Group", "Gulftainer",
    "GAC Dubai", "Fetchr", "RSA Global", "Kuehne + Nagel UAE",
    
    # Retail
    "Majid Al Futtaim", "Landmark Group", "Apparel Group", "Al Tayer Group",
    "Chalhoub Group", "Gulf Marketing Group (GMG)", "Azadea Group",
    "Al-Futtaim Group", "Lulu Group International", "Jashanmal Group",
    
    # Tech/Service
    "Careem", "Talabat", "Kitopi", "Property Finder", "Bayut",
    "Tabby", "Tamara", "Starzplay", "BitOasis"
]

async def get_website_hybrid(page, company):
    """
    Tries DuckDuckGo API first (fast/safe). 
    Falls back to Google Playwright with CAPTCHA detection.
    """
    print(f"  Finding website for {company}...")
    
    # 1. Try DuckDuckGo (No Browser)
    try:
        results = DDGS().text(f"{company} official website Dubai", max_results=3)
        if results:
            for r in results:
                href = r.get('href', '')
                if href and "http" in href and not any(x in href for x in ["linkedin", "facebook", "instagram", "wikipedia"]):
                     print(f"    [DDG] Found: {href}")
                     return href
    except Exception as e:
        print(f"    [DDG] Failed: {e}")

    # 2. Fallback to Google (Browser)
    print("    [Google] Switching to Browser Search...")
    try:
        query = f"{company} official website Dubai"
        await page.goto(f"https://www.google.com/search?q={query}")
        
        # CAPTCHA CHECK
        title = await page.title()
        content = await page.content()
        if "robot" in title.lower() or "captcha" in content.lower().rsplit('</body>', 1)[-1]: # Check mostly visible content
             print("\n🚨 CAPTCHA DETECTED! 🚨")
             print("Please solve the CAPTCHA in the browser window.")
             input("Press ENTER in this terminal once you have solved it and results are visible...")
             
        await asyncio.sleep(random.uniform(2, 4))
        
        links = page.locator("div.g a")
        count = await links.count()
        
        for i in range(count):
            href = await links.nth(i).get_attribute("href")
            if href and "http" in href:
                if not any(x in href for x in ["linkedin", "facebook", "instagram", "wikipedia", "bloomberg", "zawya"]):
                    print(f"    [Google] Found: {href}")
                    return href
        return "Not Found"
    except Exception as e:
        print(f"    [Google] Error: {e}")
        return "Error"

async def analyze_company_site(page, url):
    """Visits the company site and extracts signals."""
    data = {
        "Website": url,
        "Social_Facebook": "", "Social_Insta": "", "Social_LinkedIn": "",
        "Legacy_Tech_Detected": "No", "Has_Careers_Page": "No"
    }
    
    if not url or "http" not in url:
        return data
        
    print(f"  Visiting: {url}")
    try:
        try:
            await page.goto(url, timeout=15000, wait_until="domcontentloaded")
        except:
             print("    (Timeout/Block on load, proceeding with partial content)")
             
        await asyncio.sleep(2) 
        
        # 1. Socials & Career
        hrefs = await page.eval_on_selector_all("a[href]", "elements => elements.map(e => e.href)")
        for href in hrefs:
            href_lower = href.lower()
            if "facebook.com" in href_lower: data["Social_Facebook"] = href
            if "instagram.com" in href_lower: data["Social_Insta"] = href
            if "linkedin.com" in href_lower: data["Social_LinkedIn"] = href
            if "career" in href_lower or "jobs" in href_lower: data["Has_Careers_Page"] = "Yes"
            
        # 2. Pain Point Scan
        content = await page.content()
        content_lower = content.lower()
        legacy_keywords = ["oracle", "sap", "primavera", "legacy", "portal", "intranet"]
        if any(kw in content_lower for kw in legacy_keywords):
             data["Legacy_Tech_Detected"] = "Yes (Pitch Modernization)"
             
    except Exception as e:
        print(f"  Analysis Error for {url}: {e}")
        
    return data

async def generate_whale_dataset():
    results = []
    output_file = "dubai_whales_analyzed.csv"
    
    print(f"🚀 Starting Playwright Deep Analysis (Smart Hybrid Mode) on {len(TARGET_COMPANIES)} Companies...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False) 
        context = await browser.new_context()
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        for i, company in enumerate(TARGET_COMPANIES):
            print(f"[{i+1}/{len(TARGET_COMPANIES)}] Analyzing: {company}...")
            
            # 1. Find Website (DDG -> Google w/ Pause)
            website = await get_website_hybrid(page, company)
            
            # 2. Analyze
            site_data = await analyze_company_site(page, website)
            
            # 3. Smart Links
            encoded_name = urllib.parse.quote(company)
            ceo_search = f"https://www.linkedin.com/search/results/people/?keywords=CEO%20{encoded_name}%20Dubai"
            cto_search = f"https://www.linkedin.com/search/results/people/?keywords=CTO%20{encoded_name}%20Dubai"
            
            # 4. Industry Tier
            industry = "Corporate"
            if company in TARGET_COMPANIES[:17]: industry = "Construction (High Priority)"
            elif company in TARGET_COMPANIES[17:26]: industry = "Logistics (High Priority)"
            elif company in TARGET_COMPANIES[26:36]: industry = "Retail (Med Priority)"
            
            row = {
                "Company_Name": company,
                "Industry_Tier": industry,
                "Website": website,
                "Research_CEO_Link": ceo_search,
                "Research_CTO_Link": cto_search,
                **site_data
            }
            results.append(row)
            
            # INCREMENTAL SAVE
            pd.DataFrame(results).to_csv(output_file, index=False)
            
            await asyncio.sleep(random.uniform(1, 2))
            
        await browser.close()
    
    print(f"✅ Done! Data saved to '{output_file}'")

if __name__ == "__main__":
    asyncio.run(generate_whale_dataset())
