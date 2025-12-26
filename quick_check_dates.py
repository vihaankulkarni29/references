"""Quick check of tradeshow mini-sites for date patterns (headless)"""
from scrapers.base_scraper import BaseScraper
import time
import re


def quick_check_dates():
    """Check sample tradeshows for date availability"""
    scraper = BaseScraper(headless=True)
    scraper.start_browser()
    
    # Sample tradeshows from CSV
    tradeshows = [
        ("Centrestage", "https://www.modemonline.com/fashion/mini-web-sites/tradeshows/references/centrestage"),
        ("MICAM Milano", "https://www.modemonline.com/fashion/mini-web-sites/tradeshows/references/micam_tradeshow"),
        ("Pitti Immagine", "https://www.modemonline.com/fashion/mini-web-sites/tradeshows/references/pitti_immagine"),
    ]
    
    print("="*80)
    print("Checking Tradeshow Mini-Sites for Date Information")
    print("="*80)
    
    for name, url in tradeshows:
        print(f"\n{name}:")
        print(f"  URL: {url}")
        
        try:
            page = scraper.new_page()
            page.goto(url, wait_until='networkidle', timeout=30000)
            scraper.handle_cookie_consent(page)
            time.sleep(2)
            
            body_text = page.inner_text('body')
            
            # Look for date patterns
            patterns_found = []
            
            # Pattern 1: "from Month DD YYYY to Month DD YYYY"
            p1 = re.findall(r'from\s+([A-Z][a-z]+)\s+(\d{1,2}),?\s+(\d{4})\s+to\s+([A-Z][a-z]+)\s+(\d{1,2}),?\s+(\d{4})', body_text)
            if p1:
                patterns_found.append(f"Pattern1: {p1[0]}")
            
            # Pattern 2: "Month DD-DD, YYYY"
            p2 = re.findall(r'([A-Z][a-z]+)\s+(\d{1,2})\s*-\s*(\d{1,2}),?\s+(\d{4})', body_text)
            if p2:
                patterns_found.append(f"Pattern2: {p2[0]}")
            
            # Pattern 3: Any month + year combo
            p3 = re.findall(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})[,\s-]+(\d{4})', body_text)
            if p3:
                patterns_found.append(f"Months: {p3[:3]}")  # First 3
            
            if patterns_found:
                print(f"  ✓ Dates found: {', '.join(patterns_found)}")
            else:
                print(f"  ✗ No dates found")
                # Show first 500 chars to debug
                print(f"  Sample text: {body_text[:500]}")
            
            page.close()
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    scraper.stop_browser()
    
    print("\n" + "="*80)
    print("Recommendation:")
    print("="*80)
    if any("✓" in str(ts) for ts in tradeshows):
        print("✓ Dates ARE available on mini-sites - implement date extraction")
    else:
        print("✗ Dates NOT available - may need to check main listing page or external sources")


if __name__ == '__main__':
    quick_check_dates()
