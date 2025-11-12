"""API Discovery Script - Capture network traffic to find hidden API endpoints"""
from playwright.sync_api import sync_playwright
import json

def discover_api_endpoints():
    """Capture API calls made by the brands page"""
    p = sync_playwright().start()
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    
    api_calls = []
    
    def capture_response(response):
        url = response.url
        if 'wp-json' in url or 'api' in url or '/mode/' in url:
            try:
                api_calls.append({
                    'url': url,
                    'status': response.status,
                    'content_type': response.headers.get('content-type', '')
                })
            except:
                pass
    
    page.on('response', capture_response)
    
    print("Loading brands page...")
    page.goto('https://www.modemonline.com/fashion/brands/', timeout=30000)
    page.wait_for_timeout(5000)
    
    print(f"\n=== API Calls Captured: {len(api_calls)} ===")
    for call in api_calls:
        print(f"Status {call['status']}: {call['url']}")
        print(f"  Type: {call['content_type']}\n")
    
    browser.close()
    p.stop()

if __name__ == '__main__':
    discover_api_endpoints()
