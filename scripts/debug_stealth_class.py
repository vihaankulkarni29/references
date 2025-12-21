from playwright_stealth import Stealth
import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        try:
            print("Instantiating Stealth(page)...")
            s = Stealth(page)
            print(f"Instance: {s}")
            # Is it awaitable?
            if hasattr(s, '__await__'):
                print("It is awaitable!")
                await s
                print("Awaited successfully.")
            else:
                print("Not awaitable.")
                
            # Does it have apply?
            if hasattr(s, 'apply'):
                print("Has apply method.")
                res = s.apply()
                if hasattr(res, '__await__'):
                    await res
                    print("Applied (async).")
                else:
                    print("Applied (sync).")
                    
        except Exception as e:
            print(f"Failed: {e}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
