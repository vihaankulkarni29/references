"""
Test script to validate cookie consent handler on modemonline.com
"""
from scrapers.base_scraper import BaseScraper


def test_cookie_consent():
    """Test cookie consent handler on the main modemonline.com page"""
    print("="*80)
    print("Testing Cookie Consent Handler")
    print("="*80)
    
    scraper = BaseScraper(headless=False)  # Run with visible browser
    scraper.start_browser()
    
    try:
        # Test on main page
        page = scraper.new_page()
        print("\n1. Navigating to https://www.modemonline.com...")
        page.goto("https://www.modemonline.com", wait_until='networkidle', timeout=30000)
        
        print("2. Checking for cookie consent dialog...")
        consent_handled = scraper.handle_cookie_consent(page)
        
        if consent_handled:
            print("   ✓ Cookie consent dialog found and accepted")
        else:
            print("   ✗ No cookie consent dialog detected (or already accepted)")
        
        # Verify page title is accessible
        title = page.title()
        print(f"3. Page title: {title}")
        
        if title and len(title) > 0:
            print("   ✓ Page title successfully retrieved")
        else:
            print("   ✗ Page title is empty")
        
        # Test on fashion weeks page
        print("\n4. Navigating to fashion weeks page...")
        page.goto("https://www.modemonline.com/fashion/fashion-weeks/", 
                  wait_until='networkidle', timeout=30000)
        
        consent_handled_2 = scraper.handle_cookie_consent(page)
        if consent_handled_2:
            print("   ✓ Cookie consent handled on second page")
        else:
            print("   ℹ No additional consent needed on second page")
        
        title_2 = page.title()
        print(f"5. Fashion weeks page title: {title_2}")
        
        if title_2 and len(title_2) > 0:
            print("   ✓ Fashion weeks page title successfully retrieved")
        else:
            print("   ✗ Fashion weeks page title is empty")
        
        print("\n" + "="*80)
        print("Test completed! Check the browser window for visual confirmation.")
        print("="*80)
        
        # Keep browser open for manual inspection
        input("\nPress Enter to close the browser and exit...")
        
    finally:
        scraper.stop_browser()


if __name__ == '__main__':
    test_cookie_consent()
