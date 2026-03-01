import json
import os

def fix_mappings_v5():
    path = "data/name_mappings.json"
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            mappings = json.load(f)
    except Exception as e:
        print(f"Error: {e}")
        return

    # Corrections based on Audit
    # Removing bad duplicate mappings (where a random Hebrew string maps to a known team)
    
    # 1. "Club Brugge" -> "מ.ס. אלג'ר" (MC Alger?) - BAD.
    # Hebrew: מ.ס. אלג'ר -> MC Alger.
    if mappings.get("מ.ס. אלג'ר") == "Club Brugge":
        print("Fixing: 'מ.ס. אלג'ר' -> 'MC Alger'")
        mappings["מ.ס. אלג'ר"] = "MC Alger"

    # 2. "Tunisia" -> "קנווי איילנד" (Canvey Island)
    # Hebrew: קנווי איילנד -> Canvey Island.
    if mappings.get("קנווי איילנד") == "Tunisia":
        print("Fixing: 'קנווי איילנד' -> 'Canvey Island'")
        mappings["קנווי איילנד"] = "Canvey Island"

    # 3. "Chesham United" -> "איבשם יונייטד" (Evesham United)
    # Hebrew: איבשם יונייטד -> Evesham United.
    if mappings.get("איבשם יונייטד") == "Chesham United":
        print("Fixing: 'איבשם יונייטד' -> 'Evesham United'")
        mappings["איבשם יונייטד"] = "Evesham United"

    # 4. "Al-Khaleej Club" -> "אהלי" (Ahli?)
    # "אהלי" usually Al Ahli. Ambiguous.
    if mappings.get("אהלי") == "Al-Khaleej Club":
        print("Fixing: 'אהלי' -> 'Al Ahli'") # Generic, but better than Khaleej
        mappings["אהלי"] = "Al Ahli"

    # 5. "Mali" -> "אבלי" (Avlai/Aveley?)
    # Hebrew: אבלי -> Aveley (English non-league).
    if mappings.get("אבלי") == "Mali":
        print("Fixing: 'אבלי' -> 'Aveley'")
        mappings["אבלי"] = "Aveley"

    with open(path, "w", encoding="utf-8") as f:
        json.dump(mappings, f, ensure_ascii=False, indent=4)
        
    print("Fixed bad duplicate mappings.")

if __name__ == "__main__":
    fix_mappings_v5()
