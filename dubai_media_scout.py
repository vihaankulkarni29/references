import asyncio
import random
import urllib.parse
import re
import pandas as pd
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

# --- SUBSET TARGETS (10 Companies) ---
TARGETS = [
    # FMCG / VIRAL
    "Almarai", "Nando's UAE", "Dominos UAE", "Hunter Foods",
    # TECH
    "Samsung Gulf", "Virgin Mobile UAE", "Noon",
    # EVENTS
    "Dubai Design District (d3)", "Global Village", "Museum of the Future"
]

async def get_instagram_ddg(page, company):
    """Finds Instagram handle using DuckDuckGo Browser Search."""
    print(f"  Hunting Instagram for {company} (via DDG)...")
    try:
        # Refined Query: Target profile pages explicitly
        query = urllib.parse.quote(f'site:instagram.com/ "{company}" Dubai -explore -popular -tags')
        await page.goto(f"https://duckduckgo.com/?q={query}&t=h_&ia=web", timeout=30000)
        await asyncio.sleep(random.uniform(2, 4))
        
        # Selectors for DDG results
        links = page.locator("a[data-testid='result-title-a']")
        count = await links.count()
        
        for i in range(min(count, 5)):
            href = await links.nth(i).get_attribute("href")
            if href and "instagram.com" in href:
                # Filter out posts, reels, tags
                if not any(x in href for x in ["/p/", "/reel/", "/explore/", "/tags/", "/popular/", "/stories/"]):
                     print(f"    found: {href}")
                     return href
        print("    [Alert] Not found on DDG. Converting to direct guess...")
        # Direct Guess Fallback
        slug = company.lower().replace(" ", "").replace("'", "")
        return f"https://www.instagram.com/{slug}/"
    except Exception as e:
        print(f"    Error finding IG: {e}")
        return None

async def analyze_instagram_followers(page, url):
    """Visits IG profile and scrapes follower count from Meta Tags."""
    if not url: return "N/A", False
    
    print(f"    Analyzing Social Power: {url}")
    try:
        await page.goto(url, timeout=45000)
        await asyncio.sleep(3)
        
        title = await page.title()
        if "Login" in title:
             print("    (Login Wall Hit)")
             return "Login Wall", "Unknown"

        # Extract Meta Description (contains stats)
        # Format: "1.2m Followers, 50 Following, 100 Posts..."
        try:
            # Use a faster selector strategy with short timeout
            element = page.locator("meta[property='og:description']")
            await element.wait_for(state="attached", timeout=5000)
            meta_desc = await element.get_attribute("content")
        except:
            print("    (Meta tag not found / Timeout)")
            return "Error", False
        
        if meta_desc:
            # Regex to find follower count part
            match = re.search(r'([0-9.,KkMm]+)\s+Followers', meta_desc)
            if match:
                count_str = match.group(1)
                print(f"    Stats: {count_str} Followers")
                
                # Parse to INT for Logic
                value = 0
                clean = count_str.lower().replace(',', '')
                if 'k' in clean:
                    value = float(clean.replace('k', '')) * 1000
                elif 'm' in clean:
                    value = float(clean.replace('m', '')) * 1000000
                else:
                    value = float(clean)
                
                is_high_volume = value > 50000
                return count_str, is_high_volume
                
        print("    (Could not parse stats)")
        return "Unknown", False
    except Exception as e:
        print(f"    Error analyzing IG: {e}")
        return "Error", False

async def run_media_scout():
    results = []
    output_file = "Dubai_Content_Survival_Leads.csv"
    print(f"🚀 Starting Media Scout on {len(TARGETS)} Companies...")
    
    async with async_playwright() as p:
        # Ignore SSL errors to fix net::ERR_CERT_AUTHORITY_INVALID
        browser = await p.chromium.launch(headless=False, args=['--ignore-certificate-errors'])
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        for company in TARGETS:
            print(f"[{company}] Processing...")
            
            # 1. Find Instagram
            ig_link = await get_instagram_ddg(page, company)
            
            # 2. Analyze Stats
            follower_count, is_high_vol = await analyze_instagram_followers(page, ig_link)
            
            # 3. Smart Links (Content Roles)
            encoded = urllib.parse.quote(company)
            link_brand = f"https://www.linkedin.com/search/results/people/?keywords=(Brand%20Manager%20OR%20Brand%20Director)%20{encoded}%20Dubai"
            link_content = f"https://www.linkedin.com/search/results/people/?keywords=(Head%20of%20Content%20OR%20Social%20Media%20Director)%20{encoded}%20Dubai"
            link_mktg = f"https://www.linkedin.com/search/results/people/?keywords=Marketing%20Director%20{encoded}%20Dubai"
            
            row = {
                "Company": company,
                "Instagram": ig_link if ig_link else "Not Found",
                "Followers": follower_count,
                "High_Volume_Lead": "YES" if is_high_vol else "No",
                "Link_Brand_Mgr": link_brand,
                "Link_Head_Content": link_content,
                "Link_Marketing_Dir": link_mktg
            }
            results.append(row)
            
            # Save
            pd.DataFrame(results).to_csv(output_file, index=False)
            await asyncio.sleep(random.uniform(1.5, 3))
            
        await browser.close()
    
    print(f"✅ Data saved to {output_file}")

if __name__ == "__main__":
    asyncio.run(run_media_scout())
