"""Quick investigation of PR contact availability on mini-sites"""
from scrapers.base_scraper import BaseScraper
import time


def investigate_pr_sections():
    """Check a few mini-sites to see if they have press/media sections"""
    scraper = BaseScraper(headless=False)
    scraper.start_browser()
    
    # Sample URLs from designer_showrooms.csv
    test_urls = [
        ('https://www.modemonline.com/fashion/mini-web-sites/multilabel-showrooms/references/mr60_showroom', 'MR60 Showroom'),
        ('https://www.modemonline.com/fashion/mini-web-sites/fashion-brands/references/antikbatik', 'Antik Batik'),
        ('https://www.modemonline.com/fashion/mini-web-sites/fashion-brands/references/ebit-tm_fashion_brand', 'EBIT'),
        ('https://www.modemonline.com/fashion/mini-web-sites/fashion-brands/references/ernestleoty_fashion_brand', 'Ernest Leoty'),
    ]
    
    try:
        page = scraper.new_page()
        
        for url, name in test_urls:
            print(f"\n{'='*80}")
            print(f"Checking: {name}")
            print(f"URL: {url}")
            print('='*80)
            
            try:
                page.goto(url, wait_until='networkidle', timeout=30000)
                scraper.handle_cookie_consent(page)
                time.sleep(2)
                
                # Get page text
                body_text = page.inner_text('body')
                
                # Check for press keywords
                pr_keywords = ['press', 'media', 'contact', 'email', '@', 'phone']
                found_keywords = [kw for kw in pr_keywords if kw in body_text.lower()]
                
                print(f"Page length: {len(body_text)} characters")
                print(f"Keywords found: {', '.join(found_keywords) if found_keywords else 'None'}")
                
                # Check for specific sections
                if 'press' in body_text.lower():
                    print("✓ Contains 'press' keyword")
                    # Show snippet around "press"
                    idx = body_text.lower().find('press')
                    snippet = body_text[max(0, idx-50):min(len(body_text), idx+150)]
                    print(f"  Snippet: ...{snippet}...")
                
                if '@' in body_text:
                    print("✓ Contains '@' (possible email)")
                    # Extract emails
                    import re
                    emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', body_text)
                    if emails:
                        print(f"  Emails found: {', '.join(emails[:3])}")
                
                # Check for links
                links = page.locator('a').all()
                link_texts = []
                for link in links[:20]:
                    try:
                        text = link.inner_text().strip().lower()
                        if text and ('press' in text or 'media' in text or 'contact' in text):
                            link_texts.append(text)
                    except Exception:
                        pass
                
                if link_texts:
                    print(f"✓ Relevant links: {', '.join(link_texts)}")
                
            except Exception as e:
                print(f"✗ Error loading page: {e}")
        
        input("\nPress Enter to close...")
        
    finally:
        scraper.stop_browser()


if __name__ == '__main__':
    investigate_pr_sections()
