import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def debug_google():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await Stealth().apply_stealth_async(page)
        
        print("Googling 'Kitopi official website Dubai'...")
        await page.goto("https://www.google.com/search?q=Kitopi+official+website+Dubai")
        await asyncio.sleep(5)
        
        print("Taking screenshot...")
        await page.screenshot(path="debug_google_search.png", full_page=True)
        
        content = await page.content()
        with open("debug_google.html", "w", encoding="utf-8") as f:
            f.write(content)
            
        print("Done. Check 'debug_google_search.png' and 'debug_google.html'")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_google())
