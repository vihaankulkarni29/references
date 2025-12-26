"""
Email Enrichment Module v2.0
Enriches master_leads.csv with professional email addresses using Apollo.io API
"""

import pandas as pd
import requests
import os
import time
from tqdm import tqdm
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables (for API key)
load_dotenv()
APOLLO_API_KEY = os.environ.get('APOLLO_API_KEY')
if not APOLLO_API_KEY:
    print("Error: APOLLO_API_KEY not found. Please set it in your .env file.")
    print("\nTo fix this:")
    print("1. Create a .env file in the project root")
    print("2. Add this line: APOLLO_API_KEY=your_api_key_here")
    print("3. Get your API key from: https://app.apollo.io/#/settings/integrations/api")
    exit()

# Apollo.io API configuration
APOLLO_ENDPOINT = "https://api.apollo.io/v1/mixed_people/search"
APOLLO_HEADERS = {
    'X-Api-Key': APOLLO_API_KEY,
    'Content-Type': 'application/json'
}

def find_contact(company_name):
    """
    Search Apollo.io API for a contact at the given company
    
    Args:
        company_name (str): Company name to search for
        
    Returns:
        str: Email address if found, None otherwise
    """
    if not company_name or company_name == 'N/A':
        return None
    
    # Construct payload for Apollo API
    # Search for key decision makers and PR contacts
    payload = {
        "q_organization_name": company_name,
        "person_titles": [
            "Founder",
            "CEO",
            "Marketing",
            "Press",
            "PR Manager",
            "Communications",
            "Owner",
            "Director"
        ],
        "page": 1,
        "per_page": 5  # Get top 5 results
    }
    
    try:
        # Send POST request to Apollo API
        response = requests.post(
            APOLLO_ENDPOINT,
            headers=APOLLO_HEADERS,
            json=payload,
            timeout=10
        )
        
        # Check if request was successful
        if response.status_code == 200:
            data = response.json()
            
            # Extract people from response
            people = data.get('people', [])
            
            if people:
                # Prioritize verified emails
                for person in people:
                    email = person.get('email')
                    email_status = person.get('email_status')
                    
                    # Return first verified email found
                    if email and email_status == 'verified':
                        return email
                
                # If no verified email, return first available email
                for person in people:
                    email = person.get('email')
                    if email:
                        return email
        
        elif response.status_code == 429:
            # Rate limit exceeded
            print(f"\n[WARN] Rate limit exceeded. Waiting 60 seconds...")
            time.sleep(60)
            return None
        
        else:
            # Other error
            print(f"\n[WARN] API error for {company_name}: {response.status_code}")
            return None
    
    except requests.exceptions.Timeout:
        print(f"\n[WARN] Timeout for {company_name}")
        return None
    
    except Exception as e:
        print(f"\n[WARN] Error for {company_name}: {str(e)}")
        return None
    
    return None


def scrape_email_from_website(url):
    """
    Fallback function to scrape email from company website
    
    Args:
        url (str): Website URL to scrape
        
    Returns:
        str: Email address if found, None otherwise
        
    Note: This is a placeholder for future implementation.
    The master_leads.csv only has modemonline.com mini-sites (modem_link),
    not the actual company websites. Future version could follow links
    to find official websites and scrape contact pages.
    """
    # Placeholder - not implemented yet
    # Would need to:
    # 1. Visit the modem_link
    # 2. Find link to official company website
    # 3. Visit official website
    # 4. Scrape contact page for email
    return None


def enrich_emails(input_file='data/processed/master_leads.csv', 
                  output_file='data/enriched/master_leads_enriched.csv'):
    """
    Main enrichment function
    
    Args:
        input_file (str): Path to input CSV file
        output_file (str): Path to output enriched CSV file
    """
    print("=" * 80)
    print("Email Enrichment Module v2.0")
    print("=" * 80)
    
    # Check if input file exists
    input_path = Path(input_file)
    if not input_path.exists():
        print(f"\n[ERROR] Input file not found: {input_file}")
        return
    
    # Load data
    print(f"\nLoading data from {input_file}...")
    df = pd.read_csv(input_file, encoding='utf-8-sig')
    print(f"Loaded {len(df)} leads")
    
    # Check for existing email column
    has_existing_emails = 'email' in df.columns
    if has_existing_emails:
        existing_count = df['email'].notna().sum()
        print(f"Found {existing_count} existing emails in dataset")
    else:
        df['email'] = None
        existing_count = 0
    
    # Initialize progress bar
    tqdm.pandas(desc="Enriching emails")
    
    print(f"\nStarting email enrichment via Apollo.io API...")
    print(f"Target: {len(df)} companies")
    print(f"Rate limit: 1 request per second")
    print(f"Estimated time: ~{len(df) // 60} minutes\n")
    
    # Track statistics
    emails_found = 0
    api_calls = 0
    
    def enrich_row(row):
        nonlocal emails_found, api_calls
        
        # Skip if email already exists
        if has_existing_emails and pd.notna(row['email']) and row['email'] != 'N/A':
            return row['email']
        
        # Try Apollo API
        company_name = row.get('company_name', 'N/A')
        email = find_contact(company_name)
        
        api_calls += 1
        
        if email:
            emails_found += 1
            print(f"\n✓ Found email for {company_name}: {email}")
        
        # Rate limiting: 1 request per second
        time.sleep(1)
        
        return email if email else 'N/A'
    
    # Apply enrichment to each row
    df['email'] = df.progress_apply(enrich_row, axis=1)
    
    # Create output directory if it doesn't exist
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save enriched data
    print(f"\n\nSaving enriched data to {output_file}...")
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    # Print summary
    print("\n" + "=" * 80)
    print("Enrichment Complete!")
    print("=" * 80)
    print(f"Total leads processed: {len(df)}")
    print(f"API calls made: {api_calls}")
    print(f"New emails found: {emails_found}")
    print(f"Success rate: {(emails_found / api_calls * 100) if api_calls > 0 else 0:.1f}%")
    
    # Email coverage statistics
    total_emails = df['email'].notna().sum()
    total_emails -= (df['email'] == 'N/A').sum()  # Exclude 'N/A'
    email_coverage = (total_emails / len(df) * 100) if len(df) > 0 else 0
    
    print(f"\nFinal email coverage: {total_emails}/{len(df)} ({email_coverage:.1f}%)")
    print(f"Output saved to: {output_file}")
    print("=" * 80)
    
    # Show sample of enriched data
    if emails_found > 0:
        print("\nSample enriched records:")
        enriched_sample = df[df['email'].notna() & (df['email'] != 'N/A')].head(5)
        print(enriched_sample[['company_name', 'email', 'city', 'country']])


if __name__ == '__main__':
    # Run enrichment
    enrich_emails()
