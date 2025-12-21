import logging
import asyncio
import random
import re
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def find_hiring_companies(keywords, max_pages=1):
    """
    Search Google X-Ray for Job Listings to identify companies using specific tools (e.g. Jira).
    X-Ray Query: site:linkedin.com/jobs "Jira" "Dubai"
    """
    logging.info(f"Starting Job Hunt for: {keywords}")
    hiring_companies = []
    seen_companies = set()
    
    async with async_playwright() as p:
        # Use headless=False for maximum stealth success as per previous learnings
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
             user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        for k in keywords:
            try:
                query = f'site:linkedin.com/jobs "{k}" "Dubai"'
                google_url = f"https://www.google.com/search?q={query}"
                
                logging.info(f"Searching Jobs: {google_url}")
                
                await page.goto(google_url)
                await asyncio.sleep(random.uniform(5, 10)) # Jitter
                
                # Parse Results
                # Google Title for Jobs usually: "Role at Company - Location" or "Company hiring Role in Location"
                # LinkedIn Title format: "Job Title at Company | LinkedIn" or "Company hiring Job Title in..."
                
                results = page.locator("div.g")
                count = await results.count()
                logging.info(f"Found {count} results for {k}")
                
                for i in range(count):
                    try:
                        div = results.nth(i)
                        title_tag = div.locator("h3").first
                        title_text = await title_tag.text_content()
                        
                        # Heuristics to extract Company Name
                        # 1. "at [Company]"
                        company = "Unknown"
                        if " at " in title_text:
                            # "Scrum Master at Emirates NBD"
                            parts = title_text.split(" at ")
                            if len(parts) > 1:
                                # Emirates NBD - Dubai...
                                suffix = parts[1]
                                company = suffix.split(" - ")[0].split(" | ")[0].strip()
                        elif " hiring " in title_text:
                            # "Emirates NBD hiring..."
                            parts = title_text.split(" hiring ")
                            company = parts[0].strip()
                            
                        # Clean up
                        company = re.sub(r'[^\w\s]', '', company).strip()
                        
                        if company and company not in seen_companies and company != "Unknown" and len(company) > 2:
                            seen_companies.add(company)
                            hiring_companies.append({
                                'name': company,
                                'hiring_signal': k,
                                'job_source': title_text
                            })
                            logging.info(f"Identified Hiring Company: {company}")
                            
                    except Exception as inner_e:
                        continue
                        
            except Exception as e:
                 logging.error(f"Error searching jobs for {k}: {e}")
                 try:
                    await page.screenshot(path=f"error_job_search_{k}.png")
                 except: pass
                 
        await browser.close()
        
    logging.info(f"Total Companies Found: {len(hiring_companies)}")
    return hiring_companies
