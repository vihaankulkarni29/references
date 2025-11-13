from playwright.sync_api import sync_playwright
import time

p = sync_playwright().start()
browser = p.chromium.launch(headless=True)
page = browser.new_page()

page.goto('https://www.modemonline.com/fashion/mini-web-sites/press-offices', wait_until='networkidle')
time.sleep(5)

html = page.content()
print('Page length:', len(html))
print('Mini Website mentions:', html.count('Mini Website'))
print('mini-web-sites mentions:', html.count('mini-web-sites'))

# Check for links
links = page.locator('a').all()
print(f'\nTotal links on page: {len(links)}')

# Sample some link text
print('\nSample link texts:')
for i in range(min(15, len(links))):
    text = page.locator('a').nth(i).text_content()
    if text and text.strip():
        print(f'  {i}: {text.strip()[:60]}')

browser.close()
p.stop()
