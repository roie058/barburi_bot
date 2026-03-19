
import json
import os
import sqlite3

def clean_name(name):
    if not name: return ""
    n = name.lower()
    replacements = [" fc", " afc", " sc", " town", " city", " limited", " b", " ii", " 2"]
    for r in replacements:
        n = n.replace(r, "")
    return n.strip()

def is_similar(unibet_name, eng_name):
    u = unibet_name.lower()
    e = eng_name.lower()
    
    if u == e: return True
    
    # Handle Vienna/Wien
    if ("vienna" in e and "wien" in u) or ("wien" in e and "vienna" in u):
        if u.replace("wien", "").strip() == e.replace("vienna", "").strip():
            return True
            
    # Handle Beograd/Belgrade
    if ("beograd" in u and "belgrade" in e) or ("belgrade" in u and "beograd" in e):
        if u.replace("beograd", "").strip() == e.replace("belgrade", "").strip():
            return True

    # Handle Nyonnais/Nyon
    if ("nyonnais" in u and "nyon" in e) or ("nyon" in u and "nyonnais" in e):
        if u.replace("nyonnais", "").strip() == e.replace("nyon", "").strip():
            return True

    # Handle Gorica/Goritza
    if ("gorica" in u and "goritza" in e) or ("goritza" in u and "gorica" in e):
        if u.replace("gorica", "").strip() == e.replace("goritza", "").strip():
            return True

    # Check if one is a cleaned version of the other
    c1, c2 = clean_name(u), clean_name(e)
    if c1 == c2 and c1 != "":
        return True
        
    return False

def bulk_map():
    unibet_path = r"c:\Users\roie0\anti-bets\barburi_bot\data\unibet_teams_map.json"
    mappings_json_path = r"c:\Users\roie0\anti-bets\barburi_bot\data\name_mappings.json"
    db_paths = [
        r"c:\Users\roie0\anti-bets\barburi_bot\data\name_db.sqlite",
        r"c:\Users\roie0\anti-bets\barburi_bot\data\new_names_db.sqlite"
    ]

    with open(unibet_path, "r", encoding="utf-8") as f:
        unibet_data = json.load(f)
    
    all_mappings = []
    if os.path.exists(mappings_json_path):
        with open(mappings_json_path, "r", encoding="utf-8") as f:
            name_mappings = json.load(f)
        for heb, eng in name_mappings.items():
            all_mappings.append((eng, heb))

    for db_path in db_paths:
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                cur = conn.cursor()
                cur.execute("SELECT en, he FROM names")
                rows = cur.fetchall()
                for en, he in rows:
                    if en and he:
                        all_mappings.append((en, he))
                conn.close()
            except Exception: pass

    empty_keys = [k for k, v in unibet_data.items() if v == ""]
    targets = empty_keys[:100]

    matched_count = 0
    for unibet_name in targets:
        found_heb = None
        
        for eng, heb in all_mappings:
            if is_similar(unibet_name, eng):
                found_heb = heb
                # Add suffix if needed
                if (" II" in unibet_name or " B" in unibet_name or " 2" in unibet_name) and " ב'" not in heb:
                    found_heb += " ב'"
                break

        if found_heb:
            unibet_data[unibet_name] = found_heb
            print(f"MATCH: '{unibet_name}' -> '{found_heb}' (Source: '{eng}')")
            matched_count += 1

    with open(unibet_path, "w", encoding="utf-8") as f:
        json.dump(unibet_data, f, ensure_ascii=False, indent=4)

    print(f"\nTotal matches found: {matched_count}")

if __name__ == "__main__":
    bulk_map()
