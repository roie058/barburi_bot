import pandas as pd
import json

def analyze_coverage():
    print("--- LEAGUE COVERAGE ANALYSIS ---")
    
    # Load Logs
    try:
        w_df = pd.read_csv("logs/winner_matches.csv")
        u_df = pd.read_csv("logs/unibet_matches.csv")
        with open("winner_to_unibet_leagues.json", "r", encoding="utf-8") as f:
            mapping = json.load(f)
    except Exception as e:
        print(f"Error loading logs: {e}")
        return

    # Normalize Unibet URL key for comparison
    # Structure of mapping: "Winner League Name" -> "URL"
    # We need "URL Suffix" -> "Winner League Name" to group Unibet rows
    
    url_to_league = {}
    for l_name, url in mapping.items():
        if "/betting/odds/" in url:
            suffix = url.split("/betting/odds/")[1]
            # Handle potential trailing slash or fragments? Usually clean in JSON.
            url_to_league[suffix] = l_name
            
    # Group Winner by League
    w_counts = w_df['league'].value_counts()
    
    # Valid Winner Leagues (that we TRIED to scrape)
    target_leagues = [l for l in w_counts.index if l in mapping and mapping[l]]
    
    print(f"\nComparing {len(target_leagues)} Mapped Leagues:\n")
    print(f"{'LEAGUE':<30} | {'WINNER':<7} | {'UNIBET':<7} | {'DIFF':<7}")
    print("-" * 60)
    
    # Determine Unibet counts per "Winner League"
    # Unibet CSV doesn't have "Winner League Name". It has "link" or similar?
    # Let's check Unibet columns. Assuming 'link' or we have to imply it?
    # The UnibetScraper adds 'link' = full url.
    
    u_counts_by_winner_league = {}
    
    if 'link' in u_df.columns:
        for idx, row in u_df.iterrows():
            link = str(row['link'])
            # Find which winner league matches this link
            # This is slow O(N*M) but N is small (100 leagues).
            found = False
            for suffix, w_name in url_to_league.items():
                if suffix in link:
                    u_counts_by_winner_league[w_name] = u_counts_by_winner_league.get(w_name, 0) + 1
                    found = True
                    break
    
    total_w = 0
    total_u = 0
    
    for l in sorted(target_leagues):
        wc = w_counts[l]
        uc = u_counts_by_winner_league.get(l, 0)
        
        diff = wc - uc
        total_w += wc
        total_u += uc
        
        # Highlight significant gaps
        marker = ""
        if wc > 0 and uc == 0: marker = " [!] ZERO"
        elif diff > 5: marker = " [!] GAP"
            
        print(f"{l[:30]:<30} | {wc:<7} | {uc:<7} | {diff:<7}{marker}")
        
    print("-" * 60)
    print(f"{'TOTAL':<30} | {total_w:<7} | {total_u:<7} | {total_w - total_u}")

if __name__ == "__main__":
    analyze_coverage()
