import asyncio
try:
    import _init_path
except ImportError:
    pass
from src.linkedin_pivot import find_decision_maker
from src.utils import setup_logging

async def test_pivot():
    setup_logging()
    print("Testing LinkedIn Pivot...")
    
    company = "Emaar Properties"
    result = await find_decision_maker(company)
    
    print("\nResult:")
    print(f"Company: {company}")
    print(f"Name: {result['dm_name']}")
    print(f"Title: {result['dm_title']}")
    print(f"LinkedIn: {result['dm_linkedin']}")

if __name__ == "__main__":
    asyncio.run(test_pivot())
