
import pandas as pd
import difflib
from datetime import datetime, timedelta
import sys
import os

# Add parent dir to path to import utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import match_datasets, GameWrapper

def analyze_logs():
    print("Reading logs...")
    try:
        w_df = pd.read_csv("logs/winner_matches.csv")
        u_df = pd.read_csv("logs/unibet_matches.csv")
    except Exception as e:
        print(f"Error reading logs: {e}")
        return

    print(f"Winner Rows: {len(w_df)}")
    print(f"Unibet Rows: {len(u_df)}")
    
    # 1. Deduplicate Unibet
    u_df.drop_duplicates(subset=['game', 'date'], inplace=True)
    print(f"Unique Unibet Games: {len(u_df)}")

    # 2. Match
    matched_count, matched_pairs, unmatched_winner = match_datasets(w_df, u_df)
    print(f"Matched: {matched_count}")
    print(f"Unmatched Winner: {len(unmatched_winner)}")

    report_path = "reports/log_analysis.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Log Analysis Report\n\n")
        f.write(f"Winner Games: {len(w_df)}\n")
        f.write(f"Unibet Games: {len(u_df)} (Unique)\n")
        f.write(f"Matched: {matched_count} ({matched_count/len(w_df)*100:.1f}%)\n\n")
        
        f.write("## Unmatched Winner Games Analysis\n\n")
        
        # Analyze why unmatched
        # Group by Date
        u_dates = set(u_df['date'].tolist())
        
        for g in unmatched_winner:
            w_date = g.date.split(' ')[0] if ' ' in g.date else g.date
            # Check if Unibet has ANY games on this date
            has_date = False
            # Check date +/- 1 day
            try:
                dt = datetime.strptime(w_date, "%Y-%m-%d")
                d_prev = (dt - timedelta(days=1)).strftime("%Y-%m-%d")
                d_next = (dt + timedelta(days=1)).strftime("%Y-%m-%d")
                
                check_dates = [w_date, d_prev, d_next]
                if any(d in u_dates for d in check_dates):
                    has_date = True
            except:
                pass
                
            f.write(f"### [{g.date}] {g.team1} ({g.team1_hebrew}) vs {g.team2} ({g.team2_hebrew})\n")
            if not has_date:
                f.write(f"- No Unibet games found near date {w_date}\n")
            else:
                # Fuzzy search in Unibet for that date
                candidates = u_df[u_df['date'].str.contains(w_date, na=False)]
                if candidates.empty:
                     # Try +/- 1 day
                     candidates = u_df[u_df['date'].isin(check_dates)]
                
                if not candidates.empty:
                    f.write("- Potential Candidates on Date:\n")
                    # Find closest name match
                    best_score = 0
                    best_cand = None
                    for _, row in candidates.iterrows():
                        u_str = f"{row['team1']} - {row['team2']}"
                        s = difflib.SequenceMatcher(None, g.game, u_str).ratio()
                        if s > best_score:
                            best_score = s
                            best_cand = u_str
                    
                    if best_cand:
                        f.write(f"  - Best Match: {best_cand} (Score: {best_score:.2f})\n")
                else:
                    f.write("- No Unibet games found on date (despite date existing in set?)\n")
            
            f.write("\n")

    print(f"Report saved to {report_path}")

if __name__ == "__main__":
    analyze_logs()
