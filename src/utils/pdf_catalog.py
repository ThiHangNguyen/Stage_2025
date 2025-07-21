import os
import pandas as pd
from PyPDF2 import PdfReader

# === Chemins ===
report_path = "data/publishing_report_08b921a7-88f9-4f96-8a8c-68a6e94adefa.tsv"
pdf_dirs = {
    "standard": "data/pdfs",
    "2cols": "data/pdfs/pdf_2cols"
}
output_csv = "data/csv/pdf_info.csv"

# === Lecture du rapport (TSV avec tabulations) ===
try:
    report_df = pd.read_csv(report_path, sep="\t", on_bad_lines="warn", low_memory=False)

except Exception as e:
    print(f"Erreur lors de la lecture du fichier TSV : {e}")
    exit(1)

# === Création du mapping id => journal ===
journal_map = dict(zip(report_df["document_localidentifier"], report_df["journal_localidentifier"]))

# === Fonction pour lire les PDFs d'un répertoire ===
def get_pdf_infos(pdf_dir, fmt_label):
    rows = []
    for fname in os.listdir(pdf_dir):
        if not fname.lower().endswith(".pdf"):
            continue

        pdf_id = os.path.splitext(fname)[0]
        pdf_path = os.path.join(pdf_dir, fname)

        try:
            with open(pdf_path, "rb") as f:
                reader = PdfReader(f)
                num_pages = len(reader.pages)
        except Exception as e:
            print(f"[Erreur] PDF corrompu ou illisible : {fname} → {e}")
            num_pages = -1

        # Récupérer le journal
        journal = journal_map.get(pdf_id, "")

        rows.append({
            "id": pdf_id,
            "format": fmt_label,
            "journal": journal,
            "pages": num_pages
        })
    return rows

# === Fusion des résultats des deux dossiers PDF ===
all_rows = []
for fmt, directory in pdf_dirs.items():
    if os.path.exists(directory):
        all_rows.extend(get_pdf_infos(directory, fmt))
    else:
        print(f"[Avertissement] Dossier inexistant : {directory}")

# === Export vers CSV ===
df = pd.DataFrame(all_rows)
df.sort_values(by="id", inplace=True)
df.to_csv(output_csv, index=False, encoding="utf-8")
print(f"Fichier généré : {output_csv} avec {len(df)} lignes.")
