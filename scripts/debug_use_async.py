from playwright_stealth import Stealth
import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        try:
            print("Calling Stealth().use_async(page)...")
            await Stealth().use_async(page)
            print("Success!")
        except Exception as e:
            print(f"Failed: {e}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
