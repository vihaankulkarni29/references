import argparse
import sys
from config.settings import BASE_URL, SCHEDULE_EVERY_DAYS
from scrapers.fashion_weeks import FashionWeeksScraper
from scrapers.showrooms import ShowroomsScraper
from utils.logger import setup_logger

# A mapping of section names to scraper classes
SCRAPER_CLASSES = {
    'fashion_weeks': FashionWeeksScraper,
    'showrooms': ShowroomsScraper,
    # Add other scrapers here as they are implemented
    # 'brands': BrandsScraper,
    # 'stores': StoresScraper,
}

def main():
    parser = argparse.ArgumentParser(description='Fashion scraper orchestration')
    parser.add_argument(
        '--sections', 
        type=str, 
        default='fashion_weeks', 
        help=f'Comma-separated list of sections to scrape. Available: {", ".join(SCRAPER_CLASSES.keys())}'
    )
    parser.add_argument('--headless', action='store_true', help='Run browser in headless mode')
    parser.set_defaults(headless=True) # Headless by default
    args = parser.parse_args()

    main_logger = setup_logger('main')
    main_logger.info('--- Starting scraper run ---')

    sections_to_run = [s.strip() for s in args.sections.split(',') if s.strip()]

    for section in sections_to_run:
        if section not in SCRAPER_CLASSES:
            main_logger.warning(f'Unknown section: "{section}". Skipping.')
            continue

        main_logger.info(f'Running scraper for section: "{section}"')
        ScraperClass = SCRAPER_CLASSES[section]
        
        try:
            scraper = ScraperClass(headless=args.headless)
            scraper.scrape()
            main_logger.info(f'Successfully finished scraping section: "{section}"')
        except Exception as e:
            main_logger.error(f'An error occurred during scraping of section "{section}": {e}', exc_info=True)
            # Depending on desired behavior, you might want to exit or continue
            # sys.exit(1) 
    
    main_logger.info('--- Scraper run finished ---')


if __name__ == '__main__':
    main()
