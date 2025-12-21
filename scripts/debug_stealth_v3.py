from playwright_stealth import stealth as stealth_module
import asyncio
from playwright.async_api import async_playwright

async def run():
    print(f"Module: {stealth_module}")
    if hasattr(stealth_module, 'stealth'):
        print("Module has 'stealth' attribute.")
        print(f"Type: {type(stealth_module.stealth)}")
    else:
        print("Module does NOT have 'stealth' attribute.")
        
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        try:
            # Try calling stealth_module.stealth(page)
            if hasattr(stealth_module, 'stealth'):
                # It seems stealth function is sync
                stealth_module.stealth(page)
                print("Called stealth_module.stealth(page) successfully.")
        except Exception as e:
            print(f"Call failed: {e}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
