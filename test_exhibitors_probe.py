from playwright.sync_api import sync_playwright

url = 'https://www.modemonline.com/fashion/mini-web-sites/tradeshows/references/whosnext'

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    print('Navigating to', url)
    page.goto(url, wait_until='networkidle', timeout=60000)
    
    # Try to find 'Exhibitors' links or headings
    has_exhibitors_link = page.locator('a:has-text("Exhibitors")').count()
    has_brands_link = page.locator('a:has-text("Brands")').count()
    h_texts = [h.text_content().strip() for h in page.locator('h1, h2, h3, h4').all()[:20]]
    print('Exhibitors link count:', has_exhibitors_link)
    print('Brands link count:', has_brands_link)
    print('Headings sample:', h_texts)
    
    total_links = len(page.locator('a').all())
    print('Total links:', total_links)
    
    body_text = page.locator('body').text_content()[:1000]
    print('Body sample:', body_text.replace('\n',' ')[:400])
    
    browser.close()
