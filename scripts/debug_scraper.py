import requests
from bs4 import BeautifulSoup

def debug():
    url = "https://www.yellowpages-uae.com/uae/construction-companies/dubai"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        print(f"Status: {resp.status_code}")
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Print all links that look like company profiles
        print("--- Link Analysis ---")
        links = soup.find_all('a', href=True)
        count = 0
        for a in links:
            href = a['href']
            text = a.get_text().strip()
            if text and len(text) > 3:
                print(f"Text: {text} | Href: {href}")
                count += 1
                if count > 20:
                    break
                    
    except Exception as e:
        print(e)

if __name__ == "__main__":
    debug()
