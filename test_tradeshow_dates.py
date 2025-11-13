"""Test tradeshow mini-site to see if dates are available"""
from scrapers.base_scraper import BaseScraper
import time


def test_tradeshow_dates():
    """Check a sample tradeshow mini-site for date information"""
    scraper = BaseScraper(headless=False)
    scraper.start_browser()
    
    try:
        page = scraper.new_page()
        
        # Test Centrestage (Hong Kong)
        url = "https://www.modemonline.com/fashion/mini-web-sites/tradeshows/references/centrestage"
        print("="*80)
        print(f"Testing: Centrestage")
        print(f"URL: {url}")
        print("="*80)
        
        page.goto(url, wait_until='networkidle', timeout=60000)
        scraper.handle_cookie_consent(page)
        time.sleep(3)
        
        # Check title
        title = page.title()
        print(f"\nPage title: {title}")
        
        # Get all text content
        body_text = page.inner_text('body')
        print(f"\nBody text length: {len(body_text)} characters")
        
        # Look for date patterns
        import re
        
        # Pattern 1: "from Month DD YYYY to Month DD YYYY"
        date_pattern1 = re.findall(r'from\s+([A-Z][a-z]+)\s+(\d{1,2}),?\s+(\d{4})\s+to\s+([A-Z][a-z]+)\s+(\d{1,2}),?\s+(\d{4})', body_text)
        if date_pattern1:
            print(f"\n✓ Found date pattern 1: {date_pattern1}")
        
        # Pattern 2: "DD-DD Month YYYY"
        date_pattern2 = re.findall(r'(\d{1,2})\s*-\s*(\d{1,2})\s+([A-Z][a-z]+)\s+(\d{4})', body_text)
        if date_pattern2:
            print(f"\n✓ Found date pattern 2: {date_pattern2}")
        
        # Pattern 3: "Month DD-DD, YYYY"
        date_pattern3 = re.findall(r'([A-Z][a-z]+)\s+(\d{1,2})\s*-\s*(\d{1,2}),?\s+(\d{4})', body_text)
        if date_pattern3:
            print(f"\n✓ Found date pattern 3: {date_pattern3}")
        
        # Pattern 4: Just look for months + years
        months_found = re.findall(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})[,\s]+(\d{4})', body_text)
        if months_found:
            print(f"\n✓ Found month patterns: {months_found[:5]}")  # First 5
        
        # Check for any headings that might contain dates
        print("\n" + "="*80)
        print("Checking headings...")
        headings = page.locator('h1, h2, h3, h4, h5').all()
        for h in headings:
            h_text = h.inner_text().strip()
            if h_text and (any(month in h_text for month in ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']) or re.search(r'\d{4}', h_text)):
                print(f"  - {h_text}")
        
        # Show first 1000 chars of body text
        print("\n" + "="*80)
        print("First 1000 characters of body text:")
        print("="*80)
        print(body_text[:1000])
        
        input("\n\nPress Enter to try another tradeshow...")
        
        # Test MICAM Milano
        url2 = "https://www.modemonline.com/fashion/mini-web-sites/tradeshows/references/micam_tradeshow"
        print("\n" + "="*80)
        print(f"Testing: MICAM Milano")
        print(f"URL: {url2}")
        print("="*80)
        
        page.goto(url2, wait_until='networkidle', timeout=60000)
        time.sleep(2)
        
        body_text2 = page.inner_text('body')
        print(f"\nBody text length: {len(body_text2)} characters")
        print(f"Title: {page.title()}")
        
        # Look for dates
        months_found2 = re.findall(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})[,\s]+(\d{4})', body_text2)
        if months_found2:
            print(f"\n✓ Found dates: {months_found2[:5]}")
        
        print("\nFirst 1000 characters:")
        print(body_text2[:1000])
        
        input("\nPress Enter to close...")
        
    finally:
        scraper.stop_browser()


if __name__ == '__main__':
    test_tradeshow_dates()
