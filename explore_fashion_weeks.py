"""Check what's actually on the fashion week pages to find brand data"""
from scrapers.base_scraper import BaseScraper
import time


def explore_fashion_week_structure():
    """Explore fashion week pages to find where brand data lives"""
    scraper = BaseScraper(headless=False)
    scraper.start_browser()
    
    try:
        page = scraper.new_page()
        
        # Test Paris SS26 main page
        url = "https://www.modemonline.com/fashion/fashion-weeks/spring-summer-2026/paris/women"
        print(f"Exploring: {url}")
        page.goto(url, wait_until='networkidle', timeout=60000)
        scraper.handle_cookie_consent(page)
        time.sleep(3)
        
        # Check title
        print(f"\nPage title: {page.title()}")
        
        # Look for any links that might contain brand/designer info
        all_links = page.locator('a').all()
        print(f"\nTotal links on page: {len(all_links)}")
        
        # Check for common patterns
        patterns = [
            ('designers/', 'Designer detail pages'),
            ('brands/', 'Brand pages'),
            ('collections/', 'Collection pages'),
            ('shows/', 'Show pages'),
            ('digital/', 'Digital pages'),
            ('presentations/', 'Presentation pages'),
            ('schedule', 'Schedule pages'),
        ]
        
        print("\nLink patterns found:")
        for pattern, desc in patterns:
            matching = [l for l in all_links if pattern in (l.get_attribute('href') or '')]
            if matching:
                print(f"  ✓ {desc}: {len(matching)} links")
                # Show first 3 examples
                for link in matching[:3]:
                    href = link.get_attribute('href')
                    text = link.inner_text()[:50]
                    print(f"      - {text} → {href}")
            else:
                print(f"  ✗ {desc}: 0 links")
        
        # Check the page HTML structure
        print("\nChecking for section headings...")
        headings = page.locator('h1, h2, h3, h4').all()
        print(f"Found {len(headings)} headings:")
        for h in headings[:10]:
            print(f"  - {h.inner_text()}")
        
        # Check if there's a schedule or list
        print("\nLooking for lists/tables...")
        lists = page.locator('ul, ol, table').all()
        print(f"Found {len(lists)} lists/tables")
        
        input("\nPress Enter to continue to digital page...")
        
        # Now check digital page
        digital_url = url + "/digital"
        print(f"\n{'='*80}")
        print(f"Exploring: {digital_url}")
        page.goto(digital_url, wait_until='networkidle', timeout=60000)
        time.sleep(2)
        
        print(f"Digital page title: {page.title()}")
        digital_links = page.locator('a').all()
        print(f"Total links: {len(digital_links)}")
        
        # Sample some link texts
        print("\nSample link texts:")
        for link in digital_links[:20]:
            text = link.inner_text().strip()
            href = link.get_attribute('href')
            if text and len(text) > 2:
                print(f"  - '{text}' → {href}")
        
        input("\nPress Enter to close...")
        
    finally:
        scraper.stop_browser()


if __name__ == '__main__':
    explore_fashion_week_structure()
