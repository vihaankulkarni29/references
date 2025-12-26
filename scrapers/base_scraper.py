from typing import List, Dict, Any, Optional
import time
import csv
from datetime import datetime
from pathlib import Path
try:
    import pandas as pd
except ImportError:
    pd = None
from playwright.sync_api import sync_playwright, Page, Browser
from config import settings


class BaseScraper:
    """Base class for scrapers. Concrete scrapers should inherit and implement required methods.

    This implementation provides Playwright browser lifecycle helpers, simple retry/backoff,
    CSV saving helper and a small sleep delay between requests.
    """

    def __init__(self, region_filter: List[str] = ["Asia", "Europe"], headless: bool = True):
        self.region_filter = region_filter
        self.delay = getattr(settings, 'REQUEST_DELAY', 2)
        self.retry_attempts = getattr(settings, 'RETRY_ATTEMPTS', 3)
        self.retry_delay = getattr(settings, 'RETRY_DELAY', 5)
        self.headless = headless
        self._playwright = None
        self._browser: Optional[Browser] = None

    # ----------------
    # Methods to implement in subclasses
    # ----------------
    def get_list_page_urls(self) -> List[str]:
        """Return list of listing pages to visit."""
        raise NotImplementedError()

    def scrape_list_page(self, page: Page, url: str) -> List[Dict[str, Any]]:
        """Scrape items (detail page URLs or brief records) from a list page."""
        raise NotImplementedError()

    def scrape_detail_page(self, page: Page, url: str) -> Dict[str, Any]:
        """Scrape a single detail page and return structured data."""
        raise NotImplementedError()

    def parse_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize and return parsed record."""
        raise NotImplementedError()

    # ----------------
    # Browser lifecycle / helpers
    # ----------------
    def start_browser(self):
        if self._browser:
            return
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=self.headless)

    def stop_browser(self):
        if self._browser:
            self._browser.close()
            self._browser = None
        if self._playwright:
            self._playwright.stop()
            self._playwright = None

    def new_page(self, **kwargs) -> Page:
        if not self._browser:
            self.start_browser()
        assert self._browser is not None, 'Browser not started'
        context = self._browser.new_context(**kwargs)
        return context.new_page()

    def _with_retries(self, fn, *args, **kwargs):
        attempts = 0
        delay = self.retry_delay
        while attempts < self.retry_attempts:
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                attempts += 1
                if attempts >= self.retry_attempts:
                    raise
                time.sleep(delay)
                delay *= 2

    def handle_cookie_consent(self, page: Page, timeout: int = 5000) -> bool:
        """Detect and accept cookie consent dialogs (Cookiebot, OneTrust, etc.).
        
        Args:
            page: Playwright Page instance
            timeout: Milliseconds to wait for consent dialog (default 5000ms)
            
        Returns:
            True if consent was handled, False if no dialog found
        """
        try:
            # Common consent dialog selectors (in priority order)
            consent_selectors = [
                # Cookiebot
                '#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll',
                '#CybotCookiebotDialogBodyButtonAccept',
                'a#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll',
                
                # OneTrust
                '#onetrust-accept-btn-handler',
                'button#onetrust-accept-btn-handler',
                
                # Generic patterns
                'button:has-text("Accept")',
                'button:has-text("Accept All")',
                'button:has-text("I Accept")',
                'button:has-text("Agree")',
                'button:has-text("Allow All")',
                'a:has-text("Accept All Cookies")',
            ]
            
            for selector in consent_selectors:
                try:
                    # Check if element exists and is visible
                    element = page.locator(selector).first
                    if element.is_visible(timeout=timeout):
                        element.click()
                        # Wait a moment for dialog to close
                        time.sleep(0.5)
                        return True
                except Exception:
                    # Try next selector
                    continue
            
            return False
        except Exception as e:
            # Log but don't fail - consent handling is best-effort
            print(f"[WARN] Cookie consent handling failed: {e}")
            return False

    # ----------------
    # Orchestration
    # ----------------
    def scrape(self):
        """Main orchestration helper - iterates list pages and detail pages.

        Subclasses should typically call super().scrape() or implement their own orchestration
        using the helpers provided here (start_browser, new_page, _with_retries, save_to_csv).
        """
        raise NotImplementedError()

    # ----------------
    # Persistence helpers
    # ----------------
    def save_to_csv(self, data: List[Dict[str, Any]], filename: str, mode: str = 'w'):
        if not data:
            return
        
        # Ensure parent directory exists
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        
        if pd is not None:
            # Use pandas if available
            df = pd.DataFrame(data)
            if mode == 'a' and Path(filename).exists():
                df.to_csv(filename, mode='a', index=False, header=False, encoding=getattr(settings, 'CSV_ENCODING', 'utf-8-sig'))
            else:
                df.to_csv(filename, index=False, encoding=getattr(settings, 'CSV_ENCODING', 'utf-8-sig'))
        else:
            # Fallback to standard library csv module
            encoding = getattr(settings, 'CSV_ENCODING', 'utf-8-sig')
            keys = list(data[0].keys())
            file_exists = Path(filename).exists()
            
            with open(filename, mode, encoding=encoding, newline='') as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                if mode == 'w' or not file_exists:
                    writer.writeheader()
                for row in data:
                    writer.writerow(row)

    def timestamp(self) -> str:
        return datetime.utcnow().strftime(getattr(settings, 'CSV_DATETIME_FORMAT', '%Y-%m-%d %H:%M:%S'))
