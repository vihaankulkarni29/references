import asyncio
import logging
try:
    import _init_path
except ImportError:
    pass
from src.discovery import find_companies
from src.utils import setup_logging

async def test_discovery():
    setup_logging()
    print("Testing Discovery Module...")
    
    # Use a specific keyword
    keywords = ["Top Construction Companies Dubai"]
    
    companies = await find_companies(keywords)
    
    print("\nFound Companies:")
    for c in companies:
        print(f"Name: {c['name']}")
        print(f"URL: {c['website']}")
        print(f"Source: {c['source_title']}")
        print("-" * 30)

if __name__ == "__main__":
    asyncio.run(test_discovery())
