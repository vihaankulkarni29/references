"""Investigate Asia fashion weeks and showrooms on modemonline.com"""
from scrapers.base_scraper import BaseScraper
import time


def check_asia_fashion_weeks():
    """Check if there are Asia fashion week pages"""
    print("="*80)
    print("Checking for Asia Fashion Weeks")
    print("="*80)
    
    scraper = BaseScraper(headless=False)
    scraper.start_browser()
    
    try:
        page = scraper.new_page()
        
        # Test various Asia city URLs
        asia_cities = [
            'tokyo', 'seoul', 'shanghai', 'hong-kong', 'singapore',
            'mumbai', 'delhi', 'bangkok', 'jakarta', 'manila'
        ]
        
        season = 'spring-summer-2026'
        
        for city in asia_cities:
            url = f"https://www.modemonline.com/fashion/fashion-weeks/{season}/{city}/women/multilabel-showrooms"
            print(f"\nTrying: {city}")
            print(f"  URL: {url}")
            
            try:
                page.goto(url, wait_until='networkidle', timeout=30000)
                scraper.handle_cookie_consent(page)
                time.sleep(1)
                
                # Check if page exists and has content
                title = page.title()
                body_text = page.inner_text('body')[:200] if page.query_selector('body') else ''
                
                # Check for "Mini Website" links
                mini_links = page.locator('a:has-text("Mini Website")').count()
                
                print(f"  Title: {title}")
                print(f"  Has Mini Website links: {mini_links > 0} ({mini_links} found)")
                
                if mini_links > 0:
                    print(f"  ✅ FOUND ASIA DATA! {mini_links} showrooms in {city}")
                elif '404' in title or 'not found' in title.lower():
                    print(f"  ❌ Page not found")
                else:
                    print(f"  ⚠️ Page exists but no showrooms")
                    
            except Exception as e:
                print(f"  ❌ Error: {e}")
        
        # Also check digital/extra pages for Asia
        print("\n" + "="*80)
        print("Checking digital/extra pages for Asia content")
        print("="*80)
        
        digital_url = f"https://www.modemonline.com/fashion/fashion-weeks/{season}/digital/extra/tradeshows"
        page.goto(digital_url, wait_until='networkidle', timeout=30000)
        scraper.handle_cookie_consent(page)
        
        # Search for Asia-related tradeshows
        body = page.inner_text('body')
        asia_keywords = ['Tokyo', 'Seoul', 'Shanghai', 'Hong Kong', 'Singapore', 'Asia', 'China', 'Japan', 'Korea']
        
        print(f"\nSearching for Asia keywords in tradeshows page...")
        found_keywords = [kw for kw in asia_keywords if kw in body]
        if found_keywords:
            print(f"  ✅ Found: {', '.join(found_keywords)}")
        else:
            print(f"  ❌ No Asia keywords found")
        
        input("\nPress Enter to close browser...")
        
    finally:
        scraper.stop_browser()


if __name__ == '__main__':
    check_asia_fashion_weeks()
