# Translation Fixes Report

Here are the changes applied to the translation mappings:

## Hebrew -> New Translation
| Hebrew Source | Old Translation | **New Translation** |
|---------------|-----------------|---------------------|
| `נאום` | `speech` | **`Neom SC`** |
| `קומו` | `get up` | **`Como`** |
| `אל קדיסיה` | `to Cadizia` | **`Al Qadsiah`** |
| `אל טאי` | `to Tai` | **`Al-Tai`** |
| `אל סאלייה` | `to Saleya` | **`Al-Sailiya`** |
| `אל ריאד` | `to Riyadh` | **`Al-Riyadh`** |
| `אל אורובה` | `to Urova` | **`Al-Orobah`** |
| `באינגקרה` | `in Angkara` | **`Bhayangkara FC`** |
| `בלואיזדד` | `in Louisedad` | **`CR Belouizdad`** |

## Critical Fixes
| Source | Old Mapped Value | **New Fixed Value** |
|--------|------------------|---------------------|
| `Maccabi Tel Aviv` | `Maccabi Netanya` | **`Maccabi Tel Aviv`** |

## Other Cleanup
- Consolidated English-to-English mappings derived from the bad auto-translations (e.g., `to Tai` -> `Al-Tai`) to prevent them from reverting if re-ingested.

## Additional Deep Fixes
| Hebrew/Source | Old Value | New Fixed Value |
|---------------|-----------|-----------------|
| סטיף | Stiff | **ES Setif** |
| דנדי | Dandy | **Dundee FC** |
| סט. מירן | Set. Mirren | **St Mirren** |
| מקאסר | rom Cassar | **PSM Makassar** |
| פרדו | Pardo | **Paradou AC** |
| מ.ס. אשדוד | 	ax. Ashdod | **FC Ashdod** |
| מ.ס. אלג'ר | 	ax. Alger | **MC Alger** |
| מ.ס. דימונה | 	ax. Dimona | **MS Dimona** |
| סט. ג'ורג' | Set. george | **Saint George** |

## Comprehensive Manual Cleanup (100+ Fixes)
Applied batched fixes for UK, Italy, Israel, Egypt, and other leagues based on football knowledge.
Examples of fixes:
- Weymouth -> Weymouth (was Bournemouth)
- Evesham United -> Evesham United (was West Ham United)
- Hapoel Jerusalem -> Hapoel Jerusalem (was Beitar Jerusalem)
- Bukaspor -> Bucaspor 1928 (was Vanspor)
- Destruction to the cut -> Smouha
- Claopra ceramic -> Ceramica Cleopatra
Full list applied in scripts/comprehensive_cleanup.py

## Unmatched Report & User Feedback Fixes
Fixed bad translations identified in the unmatched report and by user:
| Old / Bad Value | Fixed Value |
|---|---|
| Don't fart | **Al Fayha** |
| Chorum | **Corum FK** |
| Anchorage | **Ankaragucu** |
| Iskandron | **Iskenderunspor** |
| Arbaspor | **Erbaaspor** |
| Bioglo Yeni Chershi | **Beyoglu Yeni Carsi** |
| Merchant (Hebrew: סוחר) | **Tajer** |
| AS Rosso (Hebrew: רוסה) | **MB Rouisset** |
| Erzorumspur | **Erzurumspor FK** |
| Carrassa 1908 | **Carrarese** |
| Acco Olympic | **Olympique Akbou** |

## Standardization (To Match Pinnacle)
Applied standard names to ensure exact matches instead of fuzzy matches:
| Winner/Unstandardized | New Standardized Name |
|---|---|
| Wolves | **Wolverhampton Wanderers** |
| Milan | **AC Milan** |
| Inter | **Internazionale** |
| Verona | **Hellas Verona** |
| Sporting Lisbon | **Sporting CP** |
| Al Shamal | **Al-Shamal** |
| I.V.S | **AVS** |
| Vittoria Gimraiish | **Vitoria Guimaraes** |

## User Requested Fixes
Fixed bad translations based on user feedback:
| Original/Error | Corrected Name |
|---|---|
| 	o the arena | **Larne** |
| macla 70 monument | **Mekelle 70 Enderta** |
| Maccabi brother of Nazareth | **Maccabi Ahi Nazareth** |
| Al Tawan | **Al Taawoun** (Standardized) |

## False Positive Fix Verification
Verified effectiveness of standardizations on reported mismatched games:
- **Case 1 (Saudi/Bahrain):** Al Tawan vs Al Muharraq match score dropped from **>0.8** to **0.49** (Fixed).
- **Case 2 (Turkey):** Bukaspor vs Serik match score dropped from **0.72** to **0.63** (Fixed, below 0.65 threshold).

## Bulk Standardization & Cleanup
Removed 240+ English keys per request. Standardized ~120 Hebrew translations to match Pinnacle exact names.
