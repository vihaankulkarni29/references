import asyncio
import random
import urllib.parse
import re
import pandas as pd
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from duckduckgo_search import DDGS

# --- TARGETS ---
TARGETS = [
    "Kitopi", "Careem", "Tabby", "Swvl", "Huspy", "Bayut", "Property Finder", 
    "Chalhoub Group", "Al Tayer Group", "Majid Al Futtaim", "Landmark Group", 
    "GMG (Gulf Marketing Group)", "Apparel Group", "Seddiqi Holding", "Al Naboodah Group",
    "Emirates", "Emaar", "Etisalat (e&)", "DP World", "Jumeirah Group", 
    "Nakheel", "DAMAC", "DEWA",
    "Google MENA", "Amazon MENA", "Meta Middle East", "Microsoft UAE", 
    "Oracle Middle East", "Cisco Middle East", "IBM Middle East", "SAP MENA",
    "Unilever MENA", "Procter & Gamble (P&G)", "Nestlé Middle East", "PepsiCo MENA"
]

async def get_website_hybrid(page, company):
    # Strict Verification Logic
    def is_relevant(url, name):
        name_slug = name.lower().split(' ')[0]
        if len(name_slug) < 3 and len(name.split(' ')) > 1:
             name_slug = name.lower().split(' ')[1]
        if "GMG" in name: name_slug = "gmg"
        domain = urllib.parse.urlparse(url).netloc.lower()
        if name_slug in domain: return True
        return False
        
    print(f"  Finding website for {company}...")
    # 1. DDG
    try:
        results = DDGS().text(f"{company} official website Dubai", max_results=3)
        if results:
            for r in results:
                href = r.get('href', '')
                if href and "http" in href:
                    if not any(x in href.lower() for x in ["linkedin", "wikipedia", "facebook", "instagram"]):
                        if is_relevant(href, company):
                             print(f"    [DDG] Found: {href}")
                             return href
    except: pass

    # 2. Google Fallback
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
                if not any(x in href.lower() for x in ["google", "linkedin", "wikipedia"]):
                    if is_relevant(href, company):
                        print(f"    [Google] Found: {href}")
                        return href
        return "Not Found"
    except: return "Error"

async def deep_scan_contact(page, url):
    if not url or "http" not in url: return "", "", ""
    print(f"    Scanning: {url}")
    try:
        await page.goto(url, timeout=45000)
        await asyncio.sleep(2)
        content = await page.content()
        
        # Regex
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        phone_pattern = r'(?:\+971|00971|0)?\s?(?:50|51|52|55|56|58|2|3|4|6|7|9|800)\s?\d{3}\s?\d{4}'
        
        emails = list(set(re.findall(email_pattern, content)))
        phones = list(set(re.findall(phone_pattern, content)))
        
        # Socials
        socials = []
        if "instagram.com" in content: socials.append("IG")
        if "linkedin.com" in content: socials.append("LI")
        
        return ", ".join(emails[:3]), ", ".join(phones[:3]), ", ".join(socials)
    except: return "", "", ""

async def run_brand_hunter():
    results = []
    output_file = "dubai_brand_leads.csv"
    print(f"🚀 Starting Brand Hunter...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        for company in TARGETS:
            print(f"[{company}] Processing...")
            website = await get_website_hybrid(page, company)
            email, phone, social = await deep_scan_contact(page, website)
            
            # Smart Links
            encoded = urllib.parse.quote(company)
            cmo = f"https://www.linkedin.com/search/results/people/?keywords=CMO%20{encoded}%20Dubai"
            cto = f"https://www.linkedin.com/search/results/people/?keywords=CTO%20{encoded}%20Dubai"
            
            results.append({
                "Company": company,
                "Website": website,
                "Generic_Email": email,
                "Phone": phone,
                "Social_Links": social,
                "LinkedIn_CMO": cmo,
                "LinkedIn_CTO": cto
            })
            pd.DataFrame(results).to_csv(output_file, index=False)
            await asyncio.sleep(2)
            
        await browser.close()
    print("Done.")

if __name__ == "__main__":
    asyncio.run(run_brand_hunter())
