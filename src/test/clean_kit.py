import os
import json
import re

# Répertoire contenant tes JSON
INPUT_DIR = "outputs/test_layout"
OUTPUT_FILE = "extraction_layout.json"

def clean_text(text):
    """Nettoie le texte : supprime espaces inutiles et retours multiples."""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)  # remplace espaces multiples par un seul
    return text.strip()

data_all = []

for filename in os.listdir(INPUT_DIR):
    if filename.lower().endswith(".json"):
        filepath = os.path.join(INPUT_DIR, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            try:
                page_data = json.load(f)
            except json.JSONDecodeError:
                print(f"⚠ Erreur JSON : {filename}")
                continue

        # Certains fichiers ont "blocks", d'autres "elements" selon l'outil
        blocks = page_data.get("blocks") or page_data.get("elements") or []

        for block in blocks:
            item = {
                "file": filename,
                "label": block.get("label"),
                "score": block.get("score"),
                "text": clean_text(block.get("text", "")),
                "bbox": block.get("bbox")  # utile si tu veux savoir où c'est sur la page
            }
            data_all.append(item)

# Sauvegarde dans un JSON unique
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(data_all, f, ensure_ascii=False, indent=2)

print(f"✅ Extraction terminée : {len(data_all)} blocs trouvés")
print(f"📄 Résultat dans : {OUTPUT_FILE}")
