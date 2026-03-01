import pandas as pd
import json
import os

def audit():
    print("STARTING AUDIT...")
    
    # 1. Load Data
    try:
        winner_df = pd.read_csv("logs/winner_matches.csv")
        with open("winner_to_unibet_leagues.json", "r", encoding="utf-8") as f:
            league_map = json.load(f)
        with open("data/name_mappings.json", "r", encoding="utf-8") as f:
            name_map = json.load(f)
    except Exception as e:
        print(f"Error loading files: {e}")
        return

    # 2. League Audit
    if 'league' not in winner_df.columns:
        print("Error: 'league' column not found in winner_matches.csv")
        return

    active_leagues = sorted(winner_df['league'].unique().tolist())
    print(f"\n--- LEAGUE COVERAGE ({len(active_leagues)} Active) ---")
    
    missing_map = []
    empty_map = []
    mapped_count = 0
    
    for l in active_leagues:
        if l not in league_map:
            missing_map.append(l)
        elif not league_map[l]:
            empty_map.append(l)
        else:
            mapped_count += 1
            
    print(f"Successfully Mapped: {mapped_count}")
    print(f"Missing from JSON: {len(missing_map)}")
    print(f"Mapped to Empty/Null: {len(empty_map)}")
    
    if missing_map:
        print("\n[!] MISSING LEAGUES (No Entry in JSON):")
        for l in missing_map:
            print(f" - {l}")
            
    if empty_map:
        print("\n[!] UNMAPPED LEAGUES (Entry is Empty):")
        for l in empty_map:
            print(f" - {l}")

    # 3. Name Mapping Audit (Suspicious Translations)
    print(f"\n--- NAME MAPPING AUDIT ({len(name_map)} entries) ---")
    
    # Suspicious targets: Big clubs that shouldn't be mapped from random Hebrew strings
    suspicious_targets = [
        "Manchester City", "Chelsea", "Liverpool", "Arsenal", "Manchester United",
        "Tottenham", "Real Madrid", "Barcelona", "Bayern Munich", "Juventus",
        "Inter", "Milan", "PSG", "Paris Saint-Germain"
    ]
    
    suspicious_findings = []
    
    for heb, eng in name_map.items():
        # Check 1: Target is a big club
        if eng in suspicious_targets:
            # If the Hebrew key is just a transliteration, it's fine.
            # But if it's completely different, flag it.
            # Simple heuristic: heavily different length or no shared sound?
            # Hard to do phonetics here, so just list them for manual review.
            suspicious_findings.append(f"'{heb}' -> '{eng}'")
            
        # Check 2: Wait, duplicate values? 
        # (Multiple keys mapping to same English name is suspicious if they aren't aliases)
    
    # Reverse map check
    rev_map = {}
    for heb, eng in name_map.items():
        if eng not in rev_map: rev_map[eng] = []
        rev_map[eng].append(heb)
        
    duplicates = {k: v for k, v in rev_map.items() if len(v) > 1}
    
    print(f"\n[!] POTENTIAL BAD TRANSLATIONS (Manual Review Needed):")
    for s in suspicious_findings:
        print(f" - {s}")

    print(f"\n[!] DUPLICATE MAPPINGS (Multiple Hebrew -> Same English):")
    for eng, hebs in duplicates.items():
        if len(hebs) > 1:
            # Filter out reasonable aliases (e.g. mild spelling diffs)
            # If keys look very different, print.
            print(f" -> '{eng}': {hebs}")

if __name__ == "__main__":
    audit()
