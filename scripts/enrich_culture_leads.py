import asyncio
import re
import urllib.parse
import pandas as pd
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

INPUT_FILE = "output/Dubai_Culture_Leads.csv"
OUTPUT_FILE = "output/Dubai_Culture_Leads_Enriched.csv"

def clean_url(url):
    """Unwraps DDG redirects if present."""
    if not isinstance(url, str) or not url: return None
    if "duckduckgo.com" in url:
        try:
            parsed = urllib.parse.urlparse(url)
            query = urllib.parse.parse_qs(parsed.query)
            if 'uddg' in query:
                return query['uddg'][0]
        except: pass
    return url

async def extract_data(page, url):
    """Scrapes Email, Phone, and IG from the page."""
    data = {"Emails": set(), "Phones": set(), "Instagram": None}
    print(f"    Scanning: {url}")
    
    try:
        await page.goto(url, timeout=60000, wait_until="domcontentloaded")
        await asyncio.sleep(3)
        content = await page.content()
        
        # 1. Emails
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', content)
        for e in emails:
            if not any(x in e.lower() for x in ['.png', '.jpg', 'example.com', 'sentry.io']):
                data["Emails"].add(e.lower())

        # 2. Phones (UAE Focus)
        phones = re.findall(r'(?:\+971|00971|0)?\s?(?:50|51|52|55|56|58|2|3|4|6|7|9|800)\s?\d{3}\s?\d{4,5}', content)
        for p in phones:
            data["Phones"].add(p.strip())
            
        # 3. Instagram Link
        # Look for a tag with href containing instagram.com
        ig_links = page.locator("a[href*='instagram.com']")
        count = await ig_links.count()
        if count > 0:
            for i in range(count):
                href = await ig_links.nth(i).get_attribute("href")
                if href and "/p/" not in href and "/reel/" not in href:
                     data["Instagram"] = href
                     print(f"    -> Found IG: {href}")
                     break
        
    except Exception as e:
        print(f"    Scan Error: {e}")
        
    return data

async def run_enrichment():
    print(f"🚀 Starting Enrichment on {INPUT_FILE}...")
    try:
        df = pd.read_csv(INPUT_FILE)
    except FileNotFoundError:
        print("Input file not found!")
        return

    results = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=['--ignore-certificate-errors'])
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        for index, row in df.iterrows():
            company = row.get('Company', 'Unknown')
            website = clean_url(row.get('Website'))
            
            print(f"[{company}] Processing URL: {website}")
            
            email_str, phone_str, ig_str = "", "", ""
            
            if website and "http" in website:
                data = await extract_data(page, website)
                email_str = ", ".join(list(data["Emails"]))
                phone_str = ", ".join(list(data["Phones"]))
                ig_str = data["Instagram"] if data["Instagram"] else ""
            
            # Preserve existing data and add new
            new_row = row.to_dict()
            new_row['Website'] = website # Save cleaned URL
            new_row['Scraped_Emails'] = email_str
            new_row['Scraped_Phones'] = phone_str
            new_row['Scraped_Instagram'] = ig_str
            
            results.append(new_row)
            
            # Incremental Save
            pd.DataFrame(results).to_csv(OUTPUT_FILE, index=False)
            
        await browser.close()
        
    print(f"✅ Enriched data saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(run_enrichment())
