import asyncio
import random
import urllib.parse
import re
import pandas as pd
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

# --- TARGETS (10 Companies) ---
TARGETS = [
    # FMCG / VIRAL
    "Almarai", "Nando's UAE", "Dominos UAE", "Hunter Foods",
    # TECH
    "Samsung Gulf", "Virgin Mobile UAE", "Noon",
    # EVENTS
    "Dubai Design District (d3)", "Global Village", "Museum of the Future"
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
                # Filter out obvious non-official sites
                if not any(x in href.lower() for x in ["linkedin", "wikipedia", "facebook", "instagram", "twitter", "tiktok"]):
                    print(f"    found: {href}")
                    return href
        return None
    except Exception as e:
        print(f"    Error finding website: {e}")
        return None

async def extract_contacts(page, url):
    """Visits website, finds Contact page, scrapes Email/Phone."""
    contacts = {"Emails": set(), "Phones": set()}
    if not url: return contacts
    
    print(f"    Scanning: {url}")
    try:
        await page.goto(url, timeout=60000, wait_until="domcontentloaded")
        await asyncio.sleep(3)
        
        # 1. Scrape Homepage
        content = await page.content()
        extract_from_text(content, contacts)
        
        # 2. Find Contact Page
        contact_link = page.locator("a:text-is('Contact'), a:text-is('Contact Us'), a:has-text('Contact'), a:has-text('About')")
        count = await contact_link.count()
        if count > 0:
            # Try the first visible one
            for i in range(count):
                if await contact_link.nth(i).is_visible():
                    href = await contact_link.nth(i).get_attribute("href")
                    if href:
                        print(f"    Found Contact Page: {href}")
                        try:
                            # Handle relative URLs
                            if not href.startswith("http"):
                                href = urllib.parse.urljoin(url, href)
                            
                            await page.goto(href, timeout=45000, wait_until="domcontentloaded")
                            await asyncio.sleep(3)
                            content = await page.content()
                            extract_from_text(content, contacts)
                            break # Only scan one contact page
                        except: pass
    except Exception as e:
        print(f"    Scan Error: {e}")
        
    return contacts

def extract_from_text(html, contacts):
    # Email Regex
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html)
    # Filter junk emails
    for e in emails:
        e = e.lower()
        if not any(x in e for x in ['.png', '.jpg', '.jpeg', '.gif', 'sentry.io', 'email.com', 'example.com']):
            contacts["Emails"].add(e)
            
    # Phone Regex (Dubai + Generic)
    # Matches: +971 4 123 4567, 04 123 4567, 800 1234
    phones = re.findall(r'(?:\+971|00971|0)?\s?(?:50|51|52|55|56|58|2|3|4|6|7|9|800)\s?\d{3}\s?\d{4,5}', html)
    for p in phones:
        contacts["Phones"].add(p.strip())

async def run_media_contacts():
    results = []
    output_file = "Dubai_Media_Contacts.csv"
    print(f"🚀 Starting Contact Hunter on {len(TARGETS)} Companies...")
    
    async with async_playwright() as p:
        # Robust Browser Config
        browser = await p.chromium.launch(headless=False, args=['--ignore-certificate-errors'])
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        for company in TARGETS:
            print(f"[{company}] Processing...")
            
            # 1. Find Website
            website = await get_website_ddg(page, company)
            
            # 2. Extract Info
            data = await extract_contacts(page, website)
            
            row = {
                "Company": company,
                "Website": website if website else "Not Found",
                "Emails": ", ".join(list(data["Emails"])),
                "Phones": ", ".join(list(data["Phones"]))
            }
            results.append(row)
            print(f"    -> Found {len(data['Emails'])} Emails, {len(data['Phones'])} Phones")
            
            # Incremental Save
            pd.DataFrame(results).to_csv(output_file, index=False)
            await asyncio.sleep(random.uniform(1.5, 3))
            
        await browser.close()
    
    print(f"✅ Data saved to {output_file}")

if __name__ == "__main__":
    asyncio.run(run_media_contacts())
