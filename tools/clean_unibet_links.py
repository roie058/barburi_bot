import json
import os

def clean_leagues():
    file_path = "data/unibet_leagues.json"
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        urls = json.load(f)

    print(f"Total URLs before cleaning: {len(urls)}")
    
    cleaned_urls = []
    ignored = []
    
    for url in urls:
        # Filter logic
        if "-vs-" in url:
            ignored.append(url)
            continue
        if "/outrights" in url:
            ignored.append(url)
            continue
        if "/all/all" in url: # redundant "all" filters
            ignored.append(url)
            continue
            
        cleaned_urls.append(url)
        
    # Deduplicate
    cleaned_urls = sorted(list(set(cleaned_urls)))
    
    print(f"Ignored {len(ignored)} match/bad URLs.")
    print(f"Total URLs after cleaning: {len(cleaned_urls)}")
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(cleaned_urls, f, indent=2)
        
    print("Cleaned JSON saved.")

if __name__ == "__main__":
    clean_leagues()
