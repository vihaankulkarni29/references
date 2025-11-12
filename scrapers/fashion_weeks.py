from typing import List, Dict, Any
import re
from datetime import datetime
from .base_scraper import BaseScraper
from config import settings
from utils.incremental import IncrementalStore
from utils.logger import setup_logger

logger = setup_logger('fashion_weeks')


class FashionWeeksScraper(BaseScraper):
    """Starter scraper for fashion weeks listing.

    This is a scaffold that navigates to the fashion weeks index and extracts event links.
    Concrete selectors should be refined after inspecting ModeMonline pages.
    """

    def __init__(self, headless=True):
        super().__init__(headless=headless)
        self.base_path = '/fashion/fashion-weeks/'
        self.incremental = IncrementalStore('data/raw/scraped_urls.txt')

    def get_list_page_urls(self) -> List[str]:
        return [settings.BASE_URL + self.base_path]

    def scrape_list_page(self, page, url: str) -> List[Dict[str, Any]]:
        logger.info(f'Visiting list page: {url}')
        page.goto(url, timeout=settings.TIMEOUT * 1000)
        page.wait_for_timeout(2000)
        
        # Extract event links with date context from the index page using DOM traversal
        # Dates appear as text nodes before the anchor: "June 20-24[Event Link]"
        anchors = page.query_selector_all('a[href*="/fashion/fashion-weeks/spring-summer-"]')
        links = []
        seen = set()
        
        for a in anchors:
            try:
                href = a.get_attribute('href')
                if not href or '/spring-summer-' not in href:
                    continue
                
                # Build full URL
                if href.startswith('/'):
                    full = settings.BASE_URL + href
                elif href.startswith('http'):
                    full = href
                else:
                    continue
                
                # Filter: skip already seen URLs
                if full in seen:
                    continue
                
                # Only include links that look like detail pages (have city after season)
                parts = href.split('/')
                if len(parts) >= 6:  # e.g., /fashion/fashion-weeks/spring-summer-2026/milan/men
                    event_name = a.inner_text().strip() if a else ''
                    
                    # Extract date from preceding text using JavaScript to get parent's text content
                    # The pattern is: parent contains "Date [Anchor]", we want the date part
                    date_hint = ''
                    try:
                        parent_text = a.evaluate('(el) => { let p = el.parentElement; return p ? p.innerText : ""; }')
                        # Look for date pattern: "Month DD-DD" before the event name
                        date_match = re.search(r'([A-Z][a-z]{2,8})\s+(\d{1,2})-(\d{1,2})', parent_text)
                        if date_match:
                            date_hint = f"{date_match.group(1)} {date_match.group(2)}-{date_match.group(3)}"
                    except Exception as e:
                        logger.debug(f'Could not extract date for {event_name}: {e}')
                    
                    seen.add(full)
                    links.append({'url': full, 'event_name_hint': event_name, 'dates_hint': date_hint})
            except Exception as e:
                logger.debug(f'Error parsing link: {e}')
                continue
        
        logger.info(f'Found {len(links)} event links')
        return links

    def scrape_detail_page(self, page, url: str, event_hint: str = '', dates_hint: str = '') -> Dict[str, Any]:
        logger.info(f'Visiting detail page: {url}')
        page.goto(url, timeout=settings.TIMEOUT * 1000)
        page.wait_for_timeout(1500)
        
        body_text = page.inner_text('body') if page.query_selector('body') else ''
        
        # --- Event Name ---
        event_name = self._extract_event_name(body_text, event_hint, url)
        
        # --- City, Country, Region ---
        city, country, region = self._extract_geo_from_url(url)
        
        # --- Dates ---
        dates_str = dates_hint or self._extract_text_by_pattern(body_text, r'([A-Z][a-z]+)\s+(\d{1,2})-(\d{1,2})')
        
        # --- Season ---
        season_match = re.search(r'(spring-summer|fall-winter)-(\d{4})', url)
        season = f"{'SS' if season_match.group(1) == 'spring-summer' else 'FW'}{int(season_match.group(2)) - 2000}" if season_match else 'N/A'

        # --- Other Details (Venue, Organizer, etc.) ---
        # These are often not clearly structured. We use regex on the body text.
        venue = self._extract_text_by_pattern(body_text, r'Venue\s*:\s*([^\n]+)')
        organizer = self._extract_text_by_pattern(body_text, r'Organizer\s*:\s*([^\n]+)')
        element = page.query_selector('a[href*="www."][target="_blank"]')
        website = element.get_attribute('href') if element else 'N/A'
        
        # --- Categories ---
        # Categories from URL path (e.g., /men/ or /women/)
        category_part = url.split('/')[7] if len(url.split('/')) > 7 else ''
        categories = category_part.replace('-', ' ').title()

        return {
            'event_name': event_name,
            'event_type': 'Fashion_Week',
            'city': city,
            'country': country,
            'region': region,
            'dates_str': dates_str,
            'season': season,
            'venue': venue,
            'organizer': organizer,
            'website': website,
            'categories': categories,
            'source_url': url,
            'scraped_date': self.timestamp()
        }

    def _extract_event_name(self, body_text: str, event_hint: str, url: str) -> str:
        # Strategy 1: Look for text like "SS26 Milan Men's"
        match = re.search(r'SS\d+\s+([A-Za-z\s]+(?:Men\'s|Women\'s|Fashion Week))', body_text)
        if match:
            return match.group(0).strip()
        # Strategy 2: Use hint from list page
        if event_hint:
            return event_hint
        # Strategy 3: Build from URL
        parts = url.split('/')
        if len(parts) >= 6:
            city = parts[5].replace('-', ' ').title()
            cat = parts[6].replace('-', ' & ').title() if len(parts) > 6 else ''
            return f'{city} {cat} Fashion Week'.strip()
        return 'N/A'

    def _extract_geo_from_url(self, url: str) -> (str, str, str):
        parts = url.split('/')
        city_slug = parts[6] if len(parts) > 6 else 'N/A'
        city = city_slug.replace('-', ' ').title()
        
        country = settings.CITY_COUNTRY_MAP.get(city_slug.lower(), 'N/A')
        region = 'Asia' if country in settings.ASIA_COUNTRIES else 'Europe' if country in settings.EUROPE_COUNTRIES else 'N/A'
        
        return city, country, region

    def _extract_text_by_pattern(self, text: str, pattern: str) -> str:
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else 'N/A'

    def parse_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Cleans and formats the raw scraped data into the final CSV structure."""
        event_name = raw_data.get('event_name', 'N/A')
        city = raw_data.get('city', 'N/A')
        season = raw_data.get('season', 'N/A')
        
        # Generate unique ID
        event_id = f"FW-{season}-{city.replace(' ', '')}-{hash(event_name) % 10000}"
        
        # Parse dates
        start_date, end_date = self._parse_date_range(raw_data.get('dates_str', ''), season)

        return {
            'event_id': event_id,
            'event_name': event_name,
            'event_type': raw_data.get('event_type', 'N/A'),
            'start_date': start_date,
            'end_date': end_date,
            'city': city,
            'country': raw_data.get('country', 'N/A'),
            'region': raw_data.get('region', 'N/A'),
            'venue': raw_data.get('venue', 'N/A'),
            'organizer': raw_data.get('organizer', 'N/A'),
            'organizer_contact': 'N/A', # Not available on page
            'website': raw_data.get('website', 'N/A'),
            'exhibitors_count': 'N/A', # Requires scraping another section
            'exhibitor_list': 'N/A', # Requires scraping another section
            'categories': raw_data.get('categories', 'N/A'),
            'season': season,
            'description': f"{event_name} for {season}",
            'source_url': raw_data.get('source_url', 'N/A'),
            'scraped_date': raw_data.get('scraped_date', self.timestamp())
        }

    def _parse_date_range(self, date_str: str, season: str) -> (str, str):
        if not date_str or not season:
            return 'N/A', 'N/A'
        
        # Get year from season (e.g., SS26 -> 2026)
        year_match = re.search(r'\d{2}$', season)
        if not year_match: return 'N/A', 'N/A'
        year = f"20{year_match.group(0)}"
        
        # Pattern: "Month Day-Day" (e.g., "June 20-24")
        match = re.match(r'([A-Z][a-z]+)\s+(\d{1,2})-(\d{1,2})', date_str)
        if match:
            month, start_day, end_day = match.groups()
            try:
                start_dt = datetime.strptime(f'{year} {month} {start_day}', '%Y %B %d')
                end_dt = datetime.strptime(f'{year} {month} {end_day}', '%Y %B %d')
                return start_dt.strftime('%Y-%m-%d'), end_dt.strftime('%Y-%m-%d')
            except ValueError:
                return 'N/A', 'N/A'
        return 'N/A', 'N/A'


    def scrape(self):
        results = []
        try:
            self.start_browser()
            page = self.new_page()
            for list_url in self.get_list_page_urls():
                items = self.scrape_list_page(page, list_url)
                for item in items:
                    url = item.get('url')
                    if not url:
                        continue
                    if self.incremental.has(url):
                        logger.debug(f'Skipping already scraped url: {url}')
                        continue
                    try:
                        # Pass hints from list page to detail page scraper
                        event_hint = item.get('event_name_hint', '')
                        dates_hint = item.get('dates_hint', '')
                        detail = self.scrape_detail_page(page, url, event_hint, dates_hint)
                        parsed = self.parse_data(detail)
                        
                        # Apply geographic filtering: only Asia and Europe
                        if parsed.get('region') in ['Asia', 'Europe']:
                            results.append(parsed)
                            logger.info(f"Added: {parsed.get('event_name')} ({parsed.get('city')}, {parsed.get('country')})")
                        else:
                            logger.info(f"Skipped (not Asia/Europe): {parsed.get('event_name')} ({parsed.get('country')})")
                        
                        self.incremental.add(url)
                    except Exception as e:
                        logger.error(f'Failed to scrape detail {url}: {e}')
            
            # Save results
            if results:
                self.save_to_csv(results, 'data/processed/events_calendar.csv', mode='a')
                logger.info(f'Saved {len(results)} events to CSV')
            else:
                logger.warning('No events matched filters')
        finally:
            self.stop_browser()
