import json
import base64

def find_hidden_odds():
    with open('pinnacle.har', 'r', encoding='utf-8') as f:
        d = json.load(f)
    
    entries = d['log']['entries']
    found = 0
    for e in entries:
        req_url = e['request']['url']
        resp_content = e['response']['content']
        text = resp_content.get('text', '')
        
        # Check standard text
        if text and ('price' in text.lower() or 'moneyline' in text.lower() or 'odds' in text.lower()):
            if 'pinnacle.com' in req_url and 'api' in req_url:
                print(f"FOUND IN PLAINTEXT: {req_url}")
                found += 1
                
        # Check base64
        if resp_content.get('encoding') == 'base64' and text:
            try:
                decoded = base64.b64decode(text).decode('utf-8')
                if 'price' in decoded.lower() or 'moneyline' in decoded.lower():
                    print(f"FOUND IN BASE64: {req_url}")
                    found += 1
            except:
                pass
                
    print(f"Total endpoints found containing odds keywords: {found}")

if __name__ == '__main__':
    find_hidden_odds()
