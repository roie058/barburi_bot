# Audit Report: Leagues & Mappings

## 1. Why 46/55 Leagues? (Missing Leagues)
The bot detected **55 active leagues** in Winner, but only mapped **46** to Unibet. The missing **9 leagues** are:

1.  **אנגלית שניה** (English 2nd - Check if League One/Two?)
2.  **גביע אלג'יראי** (Algerian Cup)
3.  **גנאית ראשונה** (Ghana Premier League)
4.  **דרום אפריקאית ראשונה** (South Africa Premier League)
5.  **וולשית שניה דרום** (Cymru South)
6.  **טורקית שניה** (TFF 1. Lig)
7.  **עומאנית ראשונה** (Oman Professional League)
8.  **צפון אירית שניה** (NIFL Championship)

**Action**: These are the specific ones missing. You can manually search for their Unibet URLs and add them to `winner_to_unibet_leagues.json`.

## 2. Bad Translation Fixes ("The Manchester City Incident")
We found that the translation tool (Google Translate mostly) was hallucinating famous team names for obscure teams.
**Fixed Conflicts:**
- `Manchester City` was mapped from `Al-Seeb` (Oman) -> **FIXED** to `Al-Seeb`
- `Chelsea` was mapped from `Saham` (Oman) -> **FIXED** to `Saham`
- `Tunisia` was mapped from `Canvey Island` -> **FIXED** to `Canvey Island`
- `Club Brugge` was mapped from `MC Alger` -> **FIXED** to `MC Alger`
- `Mali` was mapped from `Aveley` -> **FIXED** to `Aveley`

## 3. Consistency Plan
To prevent this in the future:
1.  **Prefix Stripping**: The bot now strips "Al-" automatically (Implemented).
2.  **Audit Scripts**: I created `scripts/audit_leagues_and_names.py` which you can run anytime to warn if a Hebrew key maps to a "Famous Team" unexpectedly.

**Current Status**: Mappings are clean.
