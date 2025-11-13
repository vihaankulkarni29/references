from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    
    url = 'https://www.modemonline.com/fashion/mini-web-sites/fashion-brands/italy'
    print(f"Navigating to {url}")
    page.goto(url, wait_until='networkidle')
    time.sleep(3)
    
    print(f"\nPage length: {len(page.content())}")
    print(f"Page title: {page.title()}")
    
    # Check for Mini Website links
    mini_website_links = page.locator('a:has-text("Mini Website")').all()
    print(f"Mini Website links: {len(mini_website_links)}")
    
    # Check all links
    all_links = page.locator('a').all()
    print(f"Total links: {len(all_links)}")
    
    # Show potential brand links (not navigation)
    print("\nPotential brand links:")
    count = 0
    for link in all_links:
        href = link.get_attribute('href') or ''
        text = (link.text_content() or '').strip()
        # Filter out navigation and empty links
        if (text and len(text) > 3 and 
            href and not href.startswith('#') and 
            'cookie' not in href.lower() and 
            'google' not in href.lower() and
            '/fashion/mini-web-sites' not in href and
            '/fashion/fashion-weeks' not in href and
            '/fashion/tradeshows' not in href):
            print(f"  {text[:60]} -> {href}")
            count += 1
            if count >= 20:
                break
    
    # Check for any specific brand patterns in HTML
    html = page.content()
    import re
    
    # Look for common brand-related patterns
    company_mentions = len(re.findall(r'class="company|id="company', html, re.IGNORECASE))
    brand_class = len(re.findall(r'class="brand', html, re.IGNORECASE))
    item_class = len(re.findall(r'class="item|class="listing', html, re.IGNORECASE))
    
    print(f"\nPattern analysis:")
    print(f"  'company' class/id: {company_mentions}")
    print(f"  'brand' class: {brand_class}")
    print(f"  'item/listing' class: {item_class}")
    
    browser.close()
