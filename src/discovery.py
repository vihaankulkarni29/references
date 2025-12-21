import asyncio
import logging
from duckduckgo_search import DDGS
from playwright.async_api import async_playwright
from .utils import clean_text

async def search_ddg(query, max_results=5):
    logging.info(f"Searching DDG for: {query}")
    results = []
    try:
        with DDGS() as ddgs:
            search_gen = ddgs.text(query, region='ae-en', max_results=max_results)
            for r in search_gen:
                results.append(r)
    except Exception as e:
        logging.error(f"Error searching DDG: {e}")
    return results

async def scrape_yellowpages_category_playwright(url):
    """
    Scrapes a YellowPages UAE category page using Playwright.
    """
    logging.info(f"Scraping YP URL (Playwright): {url}")
    companies = []
    
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Go to URL
            await page.goto(url, timeout=30000, wait_until='domcontentloaded')
            
            # Log title
            title = await page.title()
            logging.info(f"Page Title: {title}")
            
            # Save Debug HTML
            content = await page.content()
            with open("debug_page.html", "w", encoding="utf-8") as f:
                f.write(content)
                
            # Wait for content (generic)
            # YP structure: looking for result cards.
            # We'll try to find 'h2' or similar containers.
            # Using a generic wait could be safer
            try:
                await page.wait_for_selector('h2', timeout=5000)
            except:
                logging.warning("Timeout waiting for h2 selector")

            # Extract content
            # We evaluate JS to get data cleaner
            links = await page.evaluate('''() => {
                const items = [];
                const anchors = document.querySelectorAll('a');
                anchors.forEach(a => {
                    const h2 = a.querySelector('h2'); 
                    // Or if a is inside h2
                    // Let's grab all links that have an h2 parent or are h2
                    // Heuristic: check specific YP classes if known, or generic text length
                    const text = a.innerText.trim();
                    const href = a.href;
                    if (text.length > 3 && href.includes('yellowpages-uae.com')) {
                        items.append({name: text, profile_url: href});
                    }
                });
                return items;
            }''')
            
            # Attempt 2: Refined logic if JS returns garbage. 
            # Actually, standard YP card text is usually prominent. 
            # Let's rely on Python parsing of the PAGE CONTENT for flexibility
            content = await page.content()
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')
            
            candidates = soup.find_all(['h2', 'h3'])
            for tag in candidates:
                link = tag.find('a')
                if link:
                    name = clean_text(link.get_text())
                    href = link.get('href')
                    if name and len(name) > 3:
                        companies.append({
                            'name': name,
                            'source_url': url,
                            'profile_url': href if 'http' in str(href) else f"https://www.yellowpages-uae.com{href}"
                        })

            await browser.close()
            
        except Exception as e:
            logging.error(f"Error in Playwright: {e}")
            
    return companies

async def find_companies(seed_keywords):
    """
    Finds companies by searching for YellowPages directories matching the keywords.
    """
    all_companies = []
    seen_names = set()
    
    for keyword in seed_keywords:
        # Step 1: Find the directory page
        query = f"site:yellowpages-uae.com {keyword} dubai"
        search_results = await search_ddg(query, max_results=3)
        
        if not search_results:
            logging.warning(f"No YP results found for {keyword}")
            continue
            
        # Step 2: Scrape the top result
        category_url = search_results[0]['href']
        logging.info(f"Found YP Category: {category_url}")
        
        extracted = await scrape_yellowpages_category_playwright(category_url)
        
        for comp in extracted:
            if comp['name'] not in seen_names:
                seen_names.add(comp['name'])
                comp['industry'] = keyword
                comp['website'] = "" 
                all_companies.append(comp)
                
    if not all_companies:
        logging.warning("No companies found via scraping. Using Fallback Whales.")
        fallback = ['Emaar Properties', 'Damac Properties', 'Al-Futtaim Group', 'Emirates NBD', 'Chalhoub Group']
        for name in fallback:
            all_companies.append({'name': name, 'industry': 'Fallback', 'website': '', 'source_url': 'Fallback'})
            
    logging.info(f"Total unique companies found: {len(all_companies)}")
    return all_companies
