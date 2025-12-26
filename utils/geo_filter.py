from typing import Dict, Optional
from config.settings import ASIA_COUNTRIES, EUROPE_COUNTRIES


def country_included(country: Optional[str]) -> bool:
    if not country:
        return False
    c = country.strip().lower()
    for name in ASIA_COUNTRIES + EUROPE_COUNTRIES:
        if c == name.strip().lower():
            return True
    return False


def filter_by_geography(data: Dict, field: str = 'country') -> bool:
    country = data.get(field) or data.get('country')
    # ensure we pass a string or None to country_included
    return country_included(country if isinstance(country, str) else None)
