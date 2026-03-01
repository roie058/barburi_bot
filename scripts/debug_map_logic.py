import pandas as pd
import json
import os

def debug_mapping():
    print("Loading Winner CSV...")
    try:
        df = pd.read_csv("logs/winner_matches.csv")
        active_leagues = df['league'].unique()
        print(f"Active Leagues in CSV: {active_leagues}")
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return

    print("\nLoading Mapping JSON...")
    mapping = {}
    try:
        with open("winner_to_unibet_leagues.json", "r", encoding="utf-8") as f:
            mapping = json.load(f)
        print(f"Loaded {len(mapping)} keys.")
        # Print first few keys to check encoding
        print(f"Sample keys: {list(mapping.keys())[:5]}")
    except Exception as e:
        print(f"Error loading JSON: {e}")
        return

    print("\nChecking Matches...")
    matched = []
    for l in active_leagues:
        if l in mapping:
            print(f"MATCH: '{l}' -> '{mapping[l]}'")
            matched.append(mapping[l])
        else:
            print(f"MISS: '{l}'")

    print(f"\nTotal Matched: {len(matched)}")

if __name__ == "__main__":
    debug_mapping()
