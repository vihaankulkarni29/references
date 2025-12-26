import asyncio
import random
import urllib.parse
import re
import pandas as pd
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

# --- TARGETS: THE AESTHETIC 10 ---
TARGETS = [
    "Ounass", "Atlantis The Royal", "Museum of the Future", 
    "Sole DXB", "Dubai Design District (d3)", "Matcha Club", 
    "Alserkal Avenue", "The Giving Movement", "Level Shoes", 
    "Huda Beauty"
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
                    print(f"    found: {href}")
                    return href
        return None
    except Exception as e:
        print(f"    Error finding website: {e}")
        return None

async def extract_contacts(page, url):
    """Deep scan of website for contact info."""
    contacts = {"Emails": set(), "Phones": set()}
    if not url: return contacts
    
    print(f"    Scanning: {url}")
    try:
        await page.goto(url, timeout=60000, wait_until="domcontentloaded")
        await asyncio.sleep(3)
        
        # 1. Scrape Homepage
        content = await page.content()
        extract_from_text(content, contacts)
        
        # 2. Find Contact/About Page
        # Look for typical keywords in links
        contact_link = page.locator("a:text-is('Contact'), a:text-is('Contact Us'), a:has-text('Contact'), a:has-text('About')")
        count = await contact_link.count()
        if count > 0:
            for i in range(count):
                if await contact_link.nth(i).is_visible():
                    href = await contact_link.nth(i).get_attribute("href")
                    if href:
                        print(f"    Found Sub-Page: {href}")
                        try:
                            if not href.startswith("http"):
                                href = urllib.parse.urljoin(url, href)
                            
                            await page.goto(href, timeout=45000, wait_until="domcontentloaded")
                            await asyncio.sleep(3)
                            content = await page.content()
                            extract_from_text(content, contacts)
                            break 
                        except: pass
    except Exception as e:
        print(f"    Scan Error: {e}")
        
    return contacts

def extract_from_text(html, contacts):
    # Regex for Emails
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html)
    for e in emails:
        e = e.lower()
        if not any(x in e for x in ['.png', '.jpg', 'example.com', 'sentry.io']):
            contacts["Emails"].add(e)
            
    # Regex for Phones (Dubai/UAE focus: +971, 04, 05x, 800)
    phones = re.findall(r'(?:\+971|00971|0)?\s?(?:50|51|52|55|56|58|2|3|4|6|7|9|800)\s?\d{3}\s?\d{4,5}', html)
    for p in phones:
        contacts["Phones"].add(p.strip())

async def run_creative_contacts():
    results = []
    output_file = "Dubai_Creative_Leads.csv"
    print(f"🚀 Starting Creative Contact Hunter...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=['--ignore-certificate-errors'])
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        for company in TARGETS:
            print(f"[{company}] Processing...")
            
            # 1. Official Website
            website = await get_website_ddg(page, company)
            
            # 2. Deep Contact Scan
            data = await extract_contacts(page, website)
            
            # 3. Creative Decision Maker Links
            encoded = urllib.parse.quote(company)
            link_creative = f"https://www.linkedin.com/search/results/people/?keywords=(Creative%20Director%20OR%20Art%20Director)%20{encoded}%20Dubai"
            link_visual = f"https://www.linkedin.com/search/results/people/?keywords=Head%20of%20Visual%20{encoded}%20Dubai"
            
            row = {
                "Company": company,
                "Website": website if website else "Not Found",
                "Emails": ", ".join(list(data["Emails"])),
                "Phones": ", ".join(list(data["Phones"])),
                "Link_Creative_Dir": link_creative,
                "Link_Visual_Head": link_visual
            }
            results.append(row)
            print(f"    -> Found {len(data['Emails'])} Emails, {len(data['Phones'])} Phones")
            
            pd.DataFrame(results).to_csv(output_file, index=False)
            await asyncio.sleep(random.uniform(1.5, 3))
            
        await browser.close()
    
    print(f"✅ Data saved to {output_file}")

if __name__ == "__main__":
    asyncio.run(run_creative_contacts())
