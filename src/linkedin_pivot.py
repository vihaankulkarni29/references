import logging
import asyncio
import random
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def find_decision_maker(company_name):
    """
    Uses Google X-Ray search (Stealth Mode) to find a LinkedIn profile for a CTO/Innovation head.
    Returns: {'dm_name': '...', 'dm_linkedin': '...', 'dm_title': '...'}
    """
    logging.info(f"Looking for Decision Maker at {company_name} (Stealth X-Ray)")
    
    result = {'dm_name': 'Not Found', 'dm_linkedin': '', 'dm_title': '', 'xray_snippet': ''}
    
    async with async_playwright() as p:
        # User tip: Try headless=False if blocked. Starting with True as per code, but can be toggled.
        browser = await p.chromium.launch(headless=False)
        try:
            # Create a realistic browser context
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            # Apply Stealth to bypass 'AutomationControlled' detection
            await Stealth().apply_stealth_async(page)

            # Queries to try in order of specificity
            queries = [
                f'site:linkedin.com/in/ "CTO" OR "Head of Digital" "{company_name}" "Dubai"',
                f'site:linkedin.com/in/ CTO "{company_name}" Dubai',
                f'site:linkedin.com/in/ "Head of IT" "{company_name}" Dubai'
            ]
            
            found = False
            for query in queries:
                logging.info(f"Navigating to: https://www.google.com/search?q={query}")
                await page.goto(f"https://www.google.com/search?q={query}")
                
                # Random sleep to mimic human behavior
                await asyncio.sleep(random.uniform(2, 5))
                
                # Selector for Google Search result links (usually within an <a> tag inside a 'g' class div)
                results = page.locator("div.g")
                count = await results.count()
                
                if count > 0:
                    found = True
                    first_result = results.first
                    link_tag = first_result.locator("a").first
                    title_tag = first_result.locator("h3").first
                    
                    href = await link_tag.get_attribute("href")
                    title_text = await title_tag.text_content()
                    snippet = await first_result.text_content()
                    
                    logging.info(f"[SUCCESS] Found for {company_name}: {href}")
                    
                    # Parse title for Name/Role
                    parts = title_text.split(' - ')
                    name = parts[0].strip() if parts else "Unknown"
                    job_title = parts[1].strip() if len(parts) > 1 else "Unknown"
                    
                    result = {
                        'dm_name': name, 
                        'dm_linkedin': href, 
                        'dm_title': job_title,
                        'xray_snippet': snippet
                    }
                    break # Stop if found
                else:
                    logging.info("Query returned no results, trying next...")
            
            if not found:
                logging.info(f"[INFO] No profile found for {company_name} after all attempts")
                await page.screenshot(path=f"debug_pivot_{company_name}.png")

        except Exception as e:
            logging.error(f"[ERROR] Scraping {company_name}: {e}")
            await page.screenshot(path=f"error_pivot_{company_name}.png")
        finally:
            await browser.close()
            
    return result
