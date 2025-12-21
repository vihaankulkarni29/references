import requests
import re
import logging
from bs4 import BeautifulSoup

def analyze_site(url):
    """
    Checks site for tech stack and debt signals.
    Returns: {'tech_stack': '...', 'tech_debt_signal': 'Low/Med/High', 'cms': '...'}
    """
    if not url or 'http' not in url:
        return {'tech_stack': 'Unknown', 'tech_debt_signal': 'Unknown', 'cms': 'Unknown'}

    logging.info(f"Analyzing Tech Stack for: {url}")
    signals = {
        'tech_stack': [],
        'tech_debt_signal': 'Low',
        'cms': 'Unknown'
    }
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    try:
        resp = requests.get(url, headers=headers, timeout=10, verify=False)
        
        # 1. Header Analysis
        server = resp.headers.get('Server', '')
        x_powered = resp.headers.get('X-Powered-By', '')
        
        if 'IIS' in server or 'ASP.NET' in x_powered:
            signals['tech_stack'].append('Microsoft/IIS')
        if 'nginx' in server:
            signals['tech_stack'].append('Nginx')
        if 'PHP' in x_powered:
            signals['tech_stack'].append('PHP')
            
        # 2. Content Analysis
        text = resp.text.lower()
        soup = BeautifulSoup(resp.text, 'html.parser')
        generator = soup.find('meta', attrs={'name': 'generator'})
        gen_content = generator['content'].lower() if generator and generator.get('content') else ""
        
        # CMS Detection
        if 'wordpress' in gen_content or 'wp-content' in text:
            signals['cms'] = 'WordPress'
        elif 'shopify' in text:
            signals['cms'] = 'Shopify'
        elif 'wix' in text:
            signals['cms'] = 'Wix'
        elif 'magento' in text:
            signals['cms'] = 'Magento'
        elif 'drupal' in text:
            signals['cms'] = 'Drupal'
            
        # Tech Debt Signals
        debt_score = 0
        if 'copyright 201' in text and '202' not in text: # Old copyright
            debt_score += 1
            signals['tech_stack'].append('Old Copyright')
        if 'flash' in text and '.swf' in text:
            debt_score += 2
            signals['tech_stack'].append('Flash Detected')
        if not resp.url.startswith('https'):
            debt_score += 1
            signals['tech_stack'].append('Not HTTPS')
        if 'contact.php' in text or 'contact.asp' in text: # Classic sign of old logic
            signals['tech_stack'].append('Legacy Forms')
            
        if debt_score >= 2:
            signals['tech_debt_signal'] = 'High'
        elif debt_score == 1:
            signals['tech_debt_signal'] = 'Medium'
            
        # 3. Localization/Arabic Check (Phase 3 Rule)
        # Check for Arabic in HTML lang or content
        html_lang = soup.find('html').get('lang', '').lower()
        if 'ar' in html_lang:
            signals['localization'] = 'Arabic Supported'
        elif 'arabic' in text or 'dir="rtl"' in resp.text:
             signals['localization'] = 'Arabic Supported'
        else:
            signals['localization'] = 'English Only (Opportunity)'
            
    except Exception as e:
        logging.error(f"Error analyzing {url}: {e}")
        signals['tech_debt_signal'] = 'Analysis Failed'
        signals['localization'] = 'Unknown'
        
    signals['tech_stack'] = ', '.join(signals['tech_stack'])
    return signals
