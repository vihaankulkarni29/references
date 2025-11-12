# Base Configuration
BASE_URL = "https://www.modemonline.com"
OUTPUT_DIR = "data/processed"
RAW_DATA_DIR = "data/raw"
LOG_DIR = "logs"
SCHEDULE_EVERY_DAYS = 2

# Scraping Settings
REQUEST_DELAY = 2  # seconds between requests
RETRY_ATTEMPTS = 3
RETRY_DELAY = 5  # seconds
TIMEOUT = 30  # seconds
HEADLESS = True

# Geographic Filters
ASIA_COUNTRIES = [
    "Japan", "South Korea", "China", "Taiwan", "Singapore",
    "Thailand", "India", "Hong Kong", "Indonesia", "Malaysia",
    "Philippines", "Vietnam"
]

EUROPE_COUNTRIES = [
    "United Kingdom", "UK", "France", "Italy", "Germany", "Spain",
    "Denmark", "Portugal", "Netherlands", "Belgium", "Switzerland",
    "Austria", "Sweden", "Norway", "Poland", "Czech Republic",
    "Ukraine", "Greece", "Ireland", "Finland", "Hungary", "Turkey"
]

# Region Mapping
REGION_MAPPING = {}
for country in ASIA_COUNTRIES:
    REGION_MAPPING[country] = "Asia"
for country in EUROPE_COUNTRIES:
    REGION_MAPPING[country] = "Europe"

# Target regions for scraping
TARGET_REGIONS = ["Asia", "Europe"]

# CSV Export Settings

CSV_ENCODING = "utf-8-sig"  # UTF-8 with BOM for Excel

CSV_DATE_FORMAT = "%Y-%m-%d"

CSV_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"



# City to Country Mapping

CITY_COUNTRY_MAP = {

    # Europe

    'paris': 'France', 'milan': 'Italy', 'london': 'United Kingdom',

    'berlin': 'Germany', 'copenhagen': 'Denmark', 'lisbon': 'Portugal',

    'madrid': 'Spain', 'barcelona': 'Spain', 'amsterdam': 'Netherlands',

    'brussels': 'Belgium', 'antwerp': 'Belgium', 'zurich': 'Switzerland',

    'vienna': 'Austria', 'stockholm': 'Sweden', 'oslo': 'Norway',

    'warsaw': 'Poland', 'prague': 'Czech Republic', 'kiev': 'Ukraine',

    'athens': 'Greece', 'dublin': 'Ireland', 'helsinki': 'Finland',

    'budapest': 'Hungary',

    # Asia

    'tokyo': 'Japan', 'seoul': 'South Korea', 'shanghai': 'China',

    'hong-kong': 'Hong Kong', 'taipei': 'Taiwan', 'singapore': 'Singapore',

    'bangkok': 'Thailand', 'mumbai': 'India', 'delhi': 'India',

    'jakarta': 'Indonesia', 'kuala-lumpur': 'Malaysia', 'manila': 'Philippines',

    'hanoi': 'Vietnam', 'ho-chi-minh': 'Vietnam',

    # North America (for exclusion)

    'new-york': 'USA', 'los-angeles': 'USA', 'miami': 'USA',

    'toronto': 'Canada', 'vancouver': 'Canada', 'mexico-city': 'Mexico',

    # Special/digital

    'digital': 'N/A', 'extra': 'N/A'

}
