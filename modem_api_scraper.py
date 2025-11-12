"""
ModemOnline API Scraper (Approach 2)

This module implements the API-based scraping approach described in the PRD.
It queries the WordPress JSON API endpoints directly for structured data.

Author: Vihaan Kulkarni
Date: 12 November 2025
Version: 1.0
"""

import requests
import json
import time
import string
from typing import List, Dict, Any, Optional
from pathlib import Path
import csv
from datetime import datetime

class ModemAPIClient:
    """Client for accessing ModemOnline's internal JSON API"""
    
    def __init__(self):
        self.base_url = "https://www.modemonline.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'application/json',
            'Referer': 'https://www.modemonline.com/'
        }
        self.delay = 1  # 1 second politeness delay between requests
        
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Make an API request with error handling"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            print(f"  Requesting: {url}")
            if params:
                print(f"  Params: {params}")
            
            response = requests.get(
                url,
                params=params,
                headers=self.headers,
                timeout=30
            )
            
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                # Check if response is JSON
                content_type = response.headers.get('content-type', '')
                if 'application/json' in content_type:
                    return response.json()
                else:
                    print(f"  Warning: Non-JSON response (Content-Type: {content_type})")
                    return None
            elif response.status_code == 404:
                print(f"  Endpoint not found")
                return None
            else:
                print(f"  Error: HTTP {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            print(f"  Timeout error")
            return None
        except requests.exceptions.RequestException as e:
            print(f"  Request error: {e}")
            return None
        except json.JSONDecodeError:
            print(f"  JSON decode error")
            return None
        finally:
            time.sleep(self.delay)  # Politeness delay
    
    def get_brands_by_letter(self, letter: str, per_page: int = 10000) -> Optional[List[Dict]]:
        """
        Fetch brands starting with a specific letter
        
        Tries multiple potential endpoint patterns:
        1. /wp-json/mode/v1/brands
        2. /wp-json/wp/v2/brands
        3. /api/brands
        """
        potential_endpoints = [
            '/wp-json/mode/v1/brands',
            '/wp-json/wp/v2/brands',
            '/api/brands',
            '/wp-json/modem/v1/brands'
        ]
        
        params = {
            'letter': letter.upper(),
            'per_page': per_page
        }
        
        for endpoint in potential_endpoints:
            result = self._make_request(endpoint, params)
            if result:
                return result
        
        return None
    
    def get_all_brands(self) -> List[Dict]:
        """Fetch all brands by iterating through A-Z"""
        all_brands = []
        
        print("="*60)
        print("FETCHING ALL BRANDS (A-Z)")
        print("="*60)
        
        for letter in string.ascii_uppercase:
            print(f"\nFetching brands starting with '{letter}'...")
            brands = self.get_brands_by_letter(letter)
            
            if brands:
                count = len(brands) if isinstance(brands, list) else 0
                print(f"  ✓ Found {count} brands")
                if isinstance(brands, list):
                    all_brands.extend(brands)
            else:
                print(f"  ✗ No brands found or API unavailable")
        
        print(f"\n{'='*60}")
        print(f"TOTAL BRANDS COLLECTED: {len(all_brands)}")
        print(f"{'='*60}\n")
        
        return all_brands
    
    def get_events(self) -> Optional[List[Dict]]:
        """
        Fetch fashion events/calendar
        
        Tries multiple potential endpoint patterns
        """
        potential_endpoints = [
            '/wp-json/mode/v1/calendar',
            '/wp-json/wp/v2/events',
            '/api/calendar',
            '/api/events'
        ]
        
        print("="*60)
        print("FETCHING EVENTS CALENDAR")
        print("="*60)
        
        for endpoint in potential_endpoints:
            result = self._make_request(endpoint)
            if result:
                count = len(result) if isinstance(result, list) else 0
                print(f"\n✓ Found {count} events")
                return result
        
        print("\n✗ No events found or API unavailable")
        return None


class ModemDataExporter:
    """Export scraped data to CSV and JSON formats"""
    
    def __init__(self, output_dir: str = 'data/api_extracted'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export_brands(self, brands: List[Dict]) -> None:
        """Export brands to both CSV and JSON"""
        if not brands:
            print("No brands to export")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Define schema mapping
        schema = {
            'name': '',
            'website': '',
            'email': '',
            'phone': '',
            'country': '',
            'address': '',
            'description': '',
            'modem_link': ''
        }
        
        # Normalize data to schema
        normalized_brands = []
        for brand in brands:
            normalized = {}
            for key in schema.keys():
                normalized[key] = brand.get(key, 'N/A')
            normalized_brands.append(normalized)
        
        # Export to CSV
        csv_path = self.output_dir / 'modemonline_brands.csv'
        with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=schema.keys())
            writer.writeheader()
            writer.writerows(normalized_brands)
        
        print(f"✓ Exported {len(normalized_brands)} brands to {csv_path}")
        
        # Export to JSON
        json_path = self.output_dir / 'modemonline_brands.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(normalized_brands, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Exported {len(normalized_brands)} brands to {json_path}")
    
    def export_events(self, events: List[Dict]) -> None:
        """Export events to CSV"""
        if not events:
            print("No events to export")
            return
        
        schema = {
            'event_name': '',
            'event_type': '',
            'start_date': '',
            'end_date': '',
            'city': '',
            'country': ''
        }
        
        # Normalize data
        normalized_events = []
        for event in events:
            normalized = {}
            for key in schema.keys():
                normalized[key] = event.get(key, 'N/A')
            normalized_events.append(normalized)
        
        # Export to CSV
        csv_path = self.output_dir / 'modemonline_events.csv'
        with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=schema.keys())
            writer.writeheader()
            writer.writerows(normalized_events)
        
        print(f"✓ Exported {len(normalized_events)} events to {csv_path}")


def main():
    """Main execution function"""
    print("\n" + "="*60)
    print("MODEMONLINE DATA ENGINE (v1.0)")
    print("Approach 2: Direct API Access")
    print("="*60 + "\n")
    
    # Initialize client and exporter
    client = ModemAPIClient()
    exporter = ModemDataExporter()
    
    # Fetch brands
    brands = client.get_all_brands()
    
    if brands:
        exporter.export_brands(brands)
    else:
        print("\n⚠ WARNING: API endpoints may not be available.")
        print("The /wp-json/mode/v1/ API mentioned in the PRD appears to be:")
        print("  1. Disabled or protected on the live site")
        print("  2. Only available to authenticated users")
        print("  3. Using a different endpoint structure")
        print("\nRECOMMENDATION: Approach 1 (DOM scraping) may be more reliable.")
    
    # Fetch events
    events = client.get_events()
    if events:
        exporter.export_events(events)
    
    print("\n" + "="*60)
    print("EXTRACTION COMPLETE")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
