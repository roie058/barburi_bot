import pandas as pd
from difflib import SequenceMatcher
from datetime import datetime, timedelta

def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio() * 100

def parse_winner_date(d_str):
    # Format YYMMDD e.g. 260104 -> 2026-01-04
    try:
        return datetime.strptime(str(d_str), "%y%m%d")
    except:
        return None

def parse_unibet_date(d_str):
    # Format YYYY-MM-DD HH:MM
    try:
        return datetime.strptime(d_str, "%Y-%m-%d %H:%M")
    except:
        return None

def analyze():
    print("Loading CSVs...")
    try:
        winner_df = pd.read_csv("logs/winner_matches.csv")
        unibet_df = pd.read_csv("logs/unibet_matches.csv")
    except FileNotFoundError:
        print("Error: logs/winner_matches.csv or logs/unibet_matches.csv not found.")
        return

    print(f"Loaded {len(winner_df)} Winner games and {len(unibet_df)} Unibet games.")

    report_lines = []
    report_lines.append("# Unmatched Unibet Games Analysis")
    report_lines.append(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    
    # Filter Winner games that probably didn't match (assuming we don't have the exact IDs, we'll re-simulate)
    # Actually, let's just loop through ALL Winner games and see if we can find a Unibet match.
    # If we find a match that the main bot MISSED, we diagnose why.

    translation_issues = []
    date_issues = []
    not_found = []

    for idx, w_row in winner_df.iterrows():
        w_team1 = w_row['team1']
        w_team2 = w_row['team2']
        w_date_raw = w_row['date']
        w_date = parse_winner_date(w_date_raw)
        
        # Default match status
        found = False
        reason = "Unknown"
        candidate = None
        
        # 1. Try to find a fuzzy match in Unibet
        best_score = 0
        best_row = None
        
        for u_idx, u_row in unibet_df.iterrows():
            u_team1 = u_row['team1']
            u_team2 = u_row['team2']
            
            score = similarity(f"{w_team1} {w_team2}", f"{u_team1} {u_team2}")
            if score > best_score:
                best_score = score
                best_row = u_row
        
        if best_score > 70: # Decent match candidate found
            u_date = parse_unibet_date(best_row['date'])
            
            # Check Date
            date_diff = abs((w_date - u_date).days) if w_date and u_date else 999
            
            if date_diff > 1:
                date_issues.append({
                    "winner": f"{w_team1} - {w_team2}",
                    "winner_date": w_date.strftime("%Y-%m-%d"),
                    "unibet": f"{best_row['team1']} - {best_row['team2']}",
                    "unibet_date": u_date.strftime("%Y-%m-%d") if u_date else "None",
                    "diff": date_diff,
                    "unibet_raw_header": best_row.get('raw_header', 'N/A')
                })
            elif best_score < 85: # Date matched, but name score low -> Translation risk?
                 # If date matches perfectly, it's usually a good match, but if score is borderline, might be valid mapping missing
                 # But if main bot missed it, usually it's date or score < threshold
                 translation_issues.append({
                     "winner": f"{w_team1} - {w_team2}",
                     "unibet": f"{best_row['team1']} - {best_row['team2']}",
                     "score": best_score
                 })
            else:
                # Match is Good. If main bot missed it, why?
                # Maybe threshold is strictly 85?
                pass
        else:
            not_found.append(f"{w_team1} - {w_team2}")

    # Generate Report Section
    report_lines.append("## 1. Date Mismatches (Major Issue)")
    report_lines.append("These games were found in Unibet but ignored because the Dates differed by > 1 day.")
    report_lines.append("| Winner Game | Winner Date | Unibet Game | Unibet Date (Wrong?) | Header Source |")
    report_lines.append("|---|---|---|---|---|")
    for i in date_issues:
        report_lines.append(f"| {i['winner']} | {i['winner_date']} | {i['unibet']} | **{i['unibet_date']}** | {i['unibet_raw_header']} |")
    
    report_lines.append("\n## 2. Potential Translation/Naming Issues")
    report_lines.append("These matched by date (approx) but had low name similarity scores.")
    report_lines.append("| Winner Game | Unibet Candidate | Score |")
    report_lines.append("|---|---|---|")
    for i in translation_issues:
        report_lines.append(f"| {i['winner']} | {i['unibet']} | {i['score']} |")

    report_lines.append("\n## 3. Not Found in Unibet (Scraping Coverage)")
    report_lines.append("These games were not found in the Unibet CSV at all.")
    for i in not_found[:20]: # Limit output
        report_lines.append(f"- {i}")
    if len(not_found) > 20: report_lines.append(f"... and {len(not_found)-20} more.")

    with open("reports/unmatched_analysis.md", "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    
    print("Analysis saved to reports/unmatched_analysis.md")

if __name__ == "__main__":
    analyze()
