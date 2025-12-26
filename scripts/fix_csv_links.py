import pandas as pd
import urllib.parse

def fix_smart_links():
    csv_path = "dubai_whales_analyzed.csv"
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print("CSV not found.")
        return

    print(f"Fixing links for {len(df)} rows...")

    def repair_link(link_col, role):
        # Re-construct the link from Company Name to ensure correctness
        # We can't easily parse the broken link, better to rely on Company_Name column
        return df.apply(lambda row: generate_link(role, row['Company_Name']), axis=1)

    def generate_link(role, company_name):
        if pd.isna(company_name): return ""
        # Proper URL encoding (handles &, spaces, etc.)
        encoded_name = urllib.parse.quote(company_name)
        return f"https://www.linkedin.com/search/results/people/?keywords={role}%20{encoded_name}%20Dubai"

    df['Research_CEO_Link'] = repair_link('Research_CEO_Link', 'CEO')
    df['Research_CTO_Link'] = repair_link('Research_CTO_Link', 'CTO')
    
    output_path = "dubai_whales_analyzed_fixed.csv"
    df.to_csv(output_path, index=False)
    print(f"✅ Fixed broken LinkedIn links. Saved to '{output_path}'")

if __name__ == "__main__":
    fix_smart_links()
