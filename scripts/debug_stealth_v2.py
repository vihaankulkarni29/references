from playwright_stealth import stealth
import asyncio
from playwright.async_api import async_playwright

async def run():
    print(f"Type of stealth: {type(stealth)}")
    print(f"Stealth dir: {dir(stealth)}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        try:
            res = stealth(page)
            print(f"Call with stealth(page) returned: {res}")
        except Exception as e:
            print(f"Call failed: {e}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
