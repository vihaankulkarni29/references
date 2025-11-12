from typing import List, Dict, Any
import re
from .base_scraper import BaseScraper
from config import settings
from utils.incremental import IncrementalStore
from utils.logger import setup_logger
from utils.data_cleaner import clean_email, clean_text

logger = setup_logger('showrooms')


class ShowroomsScraper(BaseScraper):
    """Scraper for multi-label showrooms from fashion week pages.
    
    Extracts showroom names, locations, contact info, brands represented, and dates.
    """

    def __init__(self, headless=True):
        super().__init__(headless=headless)
        self.incremental = IncrementalStore('data/raw/scraped_showrooms_urls.txt')

    def get_list_page_urls(self) -> List[str]:
        """Return list of fashion week showroom pages to scrape."""
        # Start with Milan Men's showrooms as test, can expand to all cities
        base_weeks = [
            '/fashion/fashion-weeks/spring-summer-2026/milan/men/multilabel-showrooms',
            '/fashion/fashion-weeks/spring-summer-2026/milan/women/multilabel-showrooms',
            '/fashion/fashion-weeks/spring-summer-2026/paris/men/multilabel-showrooms',
            '/fashion/fashion-weeks/spring-summer-2026/paris/women/multilabel-showrooms',
            '/fashion/fashion-weeks/spring-summer-2026/london/women/multilabel-showrooms',
            '/fashion/fashion-weeks/spring-summer-2026/berlin/men-and-women/multilabel-showrooms',
        ]
        return [settings.BASE_URL + path for path in base_weeks]

    def scrape_list_page(self, page, url: str) -> List[Dict[str, Any]]:
        """Scrape showroom entries from a showrooms listing page."""
        logger.info(f'Visiting showrooms list page: {url}')
        page.goto(url, timeout=settings.TIMEOUT * 1000)
        page.wait_for_timeout(2000)
        
        # Extract city from URL for geographic context
        parts = url.split('/')
        city = parts[6] if len(parts) > 6 else 'N/A'
        
        # Strategy: Look for showroom entries in the page
        # Each showroom typically has a table with address, contact, brands
        showrooms = []
        
        # Find all tables (each showroom has a table with info)
        tables = page.query_selector_all('table')
        
        # Also look for showroom names (often in bold or heading before table)
        # Pattern: showroom name followed by table with details
        body_html = page.content()

        # Pattern: <span>ShowroomName</span> followed by Mini Website link, then collapsible div with <table>
        # Capture showroom name from span and table HTML
        pattern = re.compile(r"<span[^>]*>([A-Za-z0-9\s&'\-\.]+?)</span>\s*<a[^>]*>[\*\s]*Mini Website</a>.*?<table[^>]*>(.*?)</table>", re.IGNORECASE | re.DOTALL)
        matches = list(pattern.finditer(body_html))

        # Fallback: try without the span wrapper
        if not matches:
            pattern2 = re.compile(r"([A-Z][A-Za-z0-9 &'\-\.]{3,120})\s*<a[^>]*>[\*\s]*Mini Website</a>.*?<table[^>]*>(.*?)</table>", re.IGNORECASE | re.DOTALL)
            matches = list(pattern2.finditer(body_html))

        for idx, m in enumerate(matches):
            try:
                name_raw = m.group(1)
                table_html = m.group(2)
                # Convert HTML table to plain text for easier regex parsing
                table_text = re.sub(r'<[^>]+>', ' ', table_html)
                table_text = re.sub(r'\s+', ' ', table_text).strip()

                showroom_name = clean_text(name_raw)
                if not showroom_name:
                    showroom_name = f'Showroom {idx+1}'

                showrooms.append({
                    'showroom_name': showroom_name,
                    'city': city,
                    'table_text': table_text,
                    'table_html': table_html,
                    'source_url': url
                })
            except Exception as e:
                logger.debug(f'Error parsing showroom match {idx}: {e}')
                continue

        logger.info(f'Found {len(showrooms)} showrooms on page')
        return showrooms

    def scrape_detail_page(self, page, url: str) -> Dict[str, Any]:
        """Not used - showrooms are extracted from list pages directly."""
        return {}

    def parse_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and normalize showroom data from table text."""
        showroom_name = raw_data.get('showroom_name', 'N/A')
        table_text = raw_data.get('table_text', '')
        city = raw_data.get('city', 'N/A')
        source_url = raw_data.get('source_url', '')
        
        # Extract address (look for common Italian address prefixes + postal code)
        address_match = re.search(r'((?:via|corso|piazza|viale|vicolo|strada)\s+[^\n,]{5,120}?\d{5}\s*[A-Za-z]*)', table_text, re.IGNORECASE)
        address = address_match.group(0).strip() if address_match else 'N/A'

        # Extract phone (international formats, prefer +country)
        phone_match = re.search(r'(\+?\d{1,3}[\s\-\(\)\d]{6,})', table_text)
        phone = phone_match.group(1).strip() if phone_match else 'N/A'

        # Extract email (if present)
        email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', table_text)
        email = clean_email(email_match.group(1)) if email_match else 'N/A'

        # Extract Instagram handle from raw HTML if present
        instagram = 'N/A'
        table_html = raw_data.get('table_html', '')
        ig_match = re.search(r'instagram\.com/([A-Za-z0-9_\.]+)', table_html, re.IGNORECASE)
        if ig_match:
            instagram = ig_match.group(1).strip()

        # Extract brands represented (pattern: "Brands:" or similar)
        brands_match = re.search(r'(?:Brands|Brands\:|Coll\.|Coll\:|Coll)\s*[:\-]?\s*([^\n\|]{3,400})', table_text, re.IGNORECASE)
        brands = clean_text(brands_match.group(1)[:400]) if brands_match else 'N/A'

        # Extract sales campaign dates: try full 'Sales campaign ... from <date> to <date>' first
        dates = 'N/A'
        dates_full = re.search(r'Sales campaign[^\d\n]*from\s+(?:\w+\s+)?([A-Z][a-z]+\s+\d{1,2}\s+\d{4})\s+to\s+(?:\w+\s+)?([A-Z][a-z]+\s+\d{1,2}\s+\d{4})', table_text, re.IGNORECASE)
        if dates_full:
            dates = f"{dates_full.group(1)} to {dates_full.group(2)}"
        else:
            # fallback: look for Month DD - DD or Month DD, YYYY patterns
            d2 = re.search(r'([A-Z][a-z]+\s+\d{1,2}(?:\s*-\s*\d{1,2})?(?:,?\s*\d{4})?)', table_text)
            if d2:
                dates = d2.group(1)
        
        # Map city to country
        city_country_map = {
            'milan': 'Italy', 'paris': 'France', 'london': 'United Kingdom',
            'berlin': 'Germany', 'copenhagen': 'Denmark', 'lisbon': 'Portugal'
        }
        country = city_country_map.get(city.lower(), 'N/A')
        region = 'Europe' if country in ['Italy', 'France', 'United Kingdom', 'Germany', 'Denmark', 'Portugal'] else 'N/A'
        
        return {
            'lead_id': f'SR-{showroom_name[:20].replace(" ", "")}-{city}',
            'lead_type': 'Showroom',
            'company_name': showroom_name,
            'contact_person': 'N/A',  # Would need detail page scraping
            'email': email,
            'phone': phone,
            'website': 'N/A',
            'instagram': instagram,
            'linkedin': 'N/A',
            'facebook': 'N/A',
            'city': city.replace('-', ' ').title(),
            'country': country,
            'region': region,
            'category': 'Multi-Label Showroom',
            'brands_represented': brands,
            'description': f'Sales campaign: {dates}',
            'last_activity': dates,
            'notes': f'Address: {address}',
            'source_page': source_url,
            'scraped_date': self.timestamp()
        }

    def scrape(self):
        results = []
        try:
            self.start_browser()
            page = self.new_page()
            for list_url in self.get_list_page_urls():
                if self.incremental.has(list_url):
                    logger.debug(f'Skipping already scraped URL: {list_url}')
                    continue
                
                try:
                    showrooms = self.scrape_list_page(page, list_url)
                    for showroom_data in showrooms:
                        parsed = self.parse_data(showroom_data)
                        
                        # Apply geographic filtering
                        if parsed.get('region') in ['Asia', 'Europe']:
                            results.append(parsed)
                            logger.info(f"Added: {parsed.get('company_name')} ({parsed.get('city')}, {parsed.get('country')})")
                        else:
                            logger.info(f"Skipped (not Asia/Europe): {parsed.get('company_name')}")
                    
                    self.incremental.add(list_url)
                except Exception as e:
                    logger.error(f'Failed to scrape {list_url}: {e}')
            
            if results:
                self.save_to_csv(results, 'data/processed/master_leads.csv', mode='a')
                logger.info(f'Saved {len(results)} showrooms to CSV')
            else:
                logger.warning('No showrooms matched filters')
        finally:
            self.stop_browser()
