import json
import os

mappings_to_add = {
    "אוקזר": "Auxerre",
    "ברסט": "Brest", 
    "אלברקה": "Alverca", 
    "פמליקאו": "Famalicao",
    "סנטה קלרה אזורס": "Santa Clara", 
    "פורטו": "FC Porto", # Unibet often uses FC Porto or Porto? check later
    "בנפיקה ליסבון": "Benfica", 
    "אשטוריל": "Estoril",
    "ריו אווה": "Rio Ave", 
    "קאסה פיה ליסבון": "Casa Pia", 
    "טונדלה": "Tondela", 
    "ארוקה": "Arouca",
    "אסטרלה אמדורה": "Estrela", 
    "בראגה": "Braga",
    "סאוטה": "Ceuta", 
    "פ.צ. אנדורה": "FC Andorra",
    "אמיין": "Amiens", 
    "נאנסי": "Nancy",
    "עירוני טבריה": "Ironi Tiberias", 
    "מכבי נתניה": "Maccabi Netanya",
    "טרבזונספור": "Trabzonspor",
    "סמסונספור": "Samsunspor",
    "מאת'רוול": "Motherwell", 
    "סט. מירן": "St Mirren",
    "אל סאלייה": "Al Sailiya", 
    "אל ריאן": "Al Rayyan",
    "בוריראם יונייטד": "Buriram United"
}

path = "data/name_mappings.json"
with open(path, "r", encoding="utf-8") as f:
    current = json.load(f)

for k, v in mappings_to_add.items():
    if k not in current or current[k] != v:
        print(f"Adding/Updating: {k} -> {v}")
        current[k] = v

with open(path, "w", encoding="utf-8") as f:
    json.dump(current, f, indent=4, ensure_ascii=False)
print("Manual mappings applied.")
