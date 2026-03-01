
import pandas as pd
import difflib
import json
import os
from datetime import datetime

# Helper to normalize team names for comparison
def _clean_name(name):
    name = str(name).lower()
    suffixes = [
        "town", "city", "united", "rovers", "athletic", "fc", "afc", " wanderers", 
        " county", " hotspur", " albion", " borough", " argyle", " alexandra",
        " metropolitan", " orient", " downs", " sporting"
    ]
    for s in suffixes:
        name = name.replace(s.lower(), "")
    if "congo" in name: name = "congo dr"
    return name.strip()

def are_names_similar(n1, n2, threshold=0.8):
    return difflib.SequenceMatcher(None, _clean_name(n1), _clean_name(n2)).ratio() > threshold

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import match_datasets

def suggest_translations(winner_df, unibet_df):
    suggestions = {}
    
    # 1. Comparison Step (Find unmatched games)
    print("Running comparison (Winner vs Unibet)...")
    matched_count, _, unmatched_games = match_datasets(winner_df, unibet_df)
    
    print(f"Comparison Results:")
    print(f" - Matched: {matched_count}")
    print(f" - Unmatched Winner Games: {len(unmatched_games)}")
    
    if not unmatched_games:
        print("All games matched! No suggestions needed.")
        return {}

    # Generate detailed investigation report
    print("Generating unmatched games investigation report...")
    generate_unmatched_report(unmatched_games, unibet_df)

    # 2. Normalize dates for Unibet lookup
    def get_date_str(d):
        s = str(d)
        if " " in s: return s.split(" ")[0]
        if "T" in s: return s.split("T")[0]
        if len(s) == 6 and s.isdigit():
            return f"20{s[0:2]}-{s[2:4]}-{s[4:6]}"
        return s

    unibet_df['norm_date'] = unibet_df['date'].apply(get_date_str)
    unibet_by_date = unibet_df.groupby('norm_date')
    
    # 3. Iterate ONLY Unmatched Winner matches
    print(f"Analyzing {len(unmatched_games)} unmatched games for partial matches...")
    
    for g in unmatched_games:
        # g is GameWrapper object from utils
        w_row = g.data
        date = get_date_str(g.date)
        w_team1 = g.team1
        w_team2 = g.team2
        
        if date not in unibet_by_date.groups:
            continue
            
        u_candidates = unibet_by_date.get_group(date)
        
        for _, u_row in u_candidates.iterrows():
            u_team1 = u_row['team1']
            u_team2 = u_row['team2']
            
            # Check for partial matches
            match_t1_t1 = are_names_similar(w_team1, u_team1)
            match_t1_t2 = are_names_similar(w_team1, u_team2)
            match_t2_t1 = are_names_similar(w_team2, u_team1)
            match_t2_t2 = are_names_similar(w_team2, u_team2)
            
            # Since these are confirmed UNMATCHED by match_datasets, 
            # we don't need to check for full matches here (though safe to ignore).
            # We focus on the cases where ONE team matched.
            
            target_hebrew_cand = None
            target_english_cand = None
            
            if match_t1_t1:
                # w1 matched u1. w2 is the mismatch.
                target_english_cand = u_team2
                target_hebrew_cand = w_row.get('team2_hebrew', w_team2)
            elif match_t1_t2:
                # w1 matched u2. w2 is the mismatch.
                target_english_cand = u_team1
                target_hebrew_cand = w_row.get('team2_hebrew', w_team2)
            elif match_t2_t1:
                 # w2 matched u1. w1 is the mismatch.
                target_english_cand = u_team2
                target_hebrew_cand = w_row.get('team1_hebrew', w_team1)
            elif match_t2_t2:
                 # w2 matched u2. w1 is the mismatch.
                target_english_cand = u_team1
                target_hebrew_cand = w_row.get('team1_hebrew', w_team1)
            
            if target_hebrew_cand and target_hebrew_cand not in suggestions:
                suggestions[target_hebrew_cand] = target_english_cand
            
    return suggestions

def save_suggestions(suggestions, filename='reports/translation_suggestions.json'):
    # Load existing if exists to merge? No, overwrite or append.
    # User wants a file to review.
    # JSON is good.
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(suggestions, f, ensure_ascii=False, indent=4)
    print(f"Saved {len(suggestions)} translation suggestions to {filename}")

def generate_unmatched_report(unmatched_games, unibet_df, filename='reports/unmatched_investigation.md'):
    report = []
    report.append("# Unmatched Winner Games Investigation")
    report.append(f"Generated at: {datetime.now()}")
    report.append(f"Total Unmatched: {len(unmatched_games)}")
    report.append("")
    
    # Normalize unibet dates
    def get_date_str(d):
        s = str(d)
        if " " in s: return s.split(" ")[0]
        if "T" in s: return s.split("T")[0]
        if len(s) == 6 and s.isdigit():
            return f"20{s[0:2]}-{s[2:4]}-{s[4:6]}"
        return s
        
    unibet_df['norm_date'] = unibet_df['date'].apply(get_date_str)
    unibet_by_date = unibet_df.groupby('norm_date')
    
    for g in unmatched_games:
        w_row = g.data
        date = get_date_str(g.date)
        w_team1 = g.team1
        w_team2 = g.team2
        w_team1_he = w_row.get('team1_hebrew', w_team1)
        w_team2_he = w_row.get('team2_hebrew', w_team2)
        
        report.append(f"### [{date}] {w_team1} ({w_team1_he}) vs {w_team2} ({w_team2_he})")
        
        if date not in unibet_by_date.groups:
            report.append(f"- No Unibet games found for date {date}")
            report.append("")
            continue
            
        candidates = unibet_by_date.get_group(date)
        report.append(f"**Unibet Candidates ({len(candidates)} found):**")
        
        # Sort candidates by similarity to ANY of the teams
        scored_candidates = []
        for _, u_row in candidates.iterrows():
            u_t1 = u_row['team1']
            u_t2 = u_row['team2']
            
            # Max fuzzy score against either team
            s1 = difflib.SequenceMatcher(None, _clean_name(w_team1), _clean_name(u_t1)).ratio()
            s2 = difflib.SequenceMatcher(None, _clean_name(w_team1), _clean_name(u_t2)).ratio()
            s3 = difflib.SequenceMatcher(None, _clean_name(w_team2), _clean_name(u_t1)).ratio()
            s4 = difflib.SequenceMatcher(None, _clean_name(w_team2), _clean_name(u_t2)).ratio()
            max_score = max(s1, s2, s3, s4)
            scored_candidates.append((max_score, u_t1, u_t2, s1, s2, s3, s4))
            
        # Top 5 closest
        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        
        for cand in scored_candidates[:10]:
            score, u1, u2, s1, s2, s3, s4 = cand
            matches_str = []
            if s1 > 0.4: matches_str.append(f"T1-T1({s1:.2f})")
            if s2 > 0.4: matches_str.append(f"T1-T2({s2:.2f})")
            if s3 > 0.4: matches_str.append(f"T2-T1({s3:.2f})")
            if s4 > 0.4: matches_str.append(f"T2-T2({s4:.2f})")
            
            match_details = ", ".join(matches_str) if matches_str else "No close match"
            report.append(f"- {u1} vs {u2} [Max Score: {score:.2f}] {match_details}")
            
        report.append("")
        
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("\n".join(report))
    print(f"Detailed unmatched report saved to {filename}")
