import subprocess
import argparse
import sys
import os
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

from utils.io import read_xml, write_json
from utils.base_transformer import convert_to_base
from erudit.transformer import parse_erudit_xml
from grobid.transformer import parse_grobid_xml
from evaluation.evaluation import evaluate

def run_command(cmd):
    print(f"\n[INFO] Commande : {' '.join(cmd)}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"[ERREUR] Échec : {' '.join(cmd)}")
        sys.exit(result.returncode)

def get_ids_from_raw_xml(directory):
    return [
        os.path.splitext(f)[0]
        for f in os.listdir(directory)
        if f.endswith(".xml")
    ]
def transformer_article(article_id, tool, subfolder=None):
    """
    Transforme un fichier XML brut en JSON standardisé.
    
    Args:
        article_id (str): L'identifiant de l'article (nom du fichier sans extension).
        tool (str): "grobid" ou "erudit"
        subfolder (str): Nom du journal (ex: "cqd27", "ae49", etc.)
    """

    # Chemins d’entrée et sortie
    base_input = Path("data/raw") / f"xml_{tool}"
    if subfolder:
        input_path = base_input / subfolder / f"{article_id}.xml"
        output_path = Path("data/processed") / tool / subfolder / f"{article_id}.json"
    else:
        input_path = base_input / f"{article_id}.xml"
        output_path = Path("data/processed") / tool / f"{article_id}.json"

    # Lecture XML
    try:
        xml_tree = read_xml(input_path)
    except Exception as e:
        print(f"[ERREUR] Échec de lecture du fichier {input_path}: {e}")
        return

    # Parsing
    if tool == "grobid":
        parsed = parse_grobid_xml(xml_tree)
    elif tool == "erudit":
        parsed = parse_erudit_xml(xml_tree)
    else:
        raise ValueError(f"Outil inconnu : {tool}")

    # Conversion en base + écriture
    base_data = convert_to_base(parsed)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(base_data, output_path)

    print(f"[OK] {tool.upper()} => forme_base : {output_path}")


def transformer_batch(tool, journals=None, subfolder=None):
    """
    Traite tous les fichiers .xml pour un outil donné, soit dans un sous-dossier donné, soit pour plusieurs journaux.
    """
    base_dir = Path("data/raw") / f"xml_{tool}"

    if journals:
        for journal in journals:
            dir_journal = base_dir / journal
            if not dir_journal.exists():
                print(f"[WARN] Le dossier {dir_journal} n'existe pas.")
                continue
            ids = get_ids_from_raw_xml(dir_journal)
            for article_id in ids:
                print(f"[INFO] Traitement de : {journal}/{article_id}")
                transformer_article(article_id, tool, subfolder=journal)
    else:
        if subfolder:
            base_dir = base_dir / subfolder
        ids = get_ids_from_raw_xml(base_dir)
        for article_id in ids:
            print(f"[INFO] Traitement de : {article_id}")
            transformer_article(article_id, tool, subfolder=subfolder)

def evaluate_subfolder(source: str, target: str, subfolder: str = None, journals=None):
    if journals:
        for journal in journals:
            base_dir = Path("data/processed") / target / journal
            if not base_dir.exists():
                print(f"[ERREUR] Le répertoire {base_dir} n'existe pas.")
                continue

            json_files = list(base_dir.glob("*.json"))
            if not json_files:
                print(f"[INFO] Aucun fichier JSON trouvé dans {base_dir}")
                continue

            print(f"[INFO] {len(json_files)} fichiers trouvés dans {base_dir}. Début de l’évaluation...")

            for path in json_files:
                article_id = path.stem
                try:
                    evaluate(source, target, article_id, subfolder=journal)
                except Exception as e:
                    print(f"[ERREUR] Échec de l’évaluation pour {article_id} : {e}")
    else:
        base_dir = Path("data/processed") / target
        if subfolder:
            base_dir = base_dir / subfolder

        if not base_dir.exists():
            print(f"[ERREUR] Le répertoire {base_dir} n'existe pas.")
            return

        json_files = list(base_dir.glob("*.json"))
        if not json_files:
            print(f"[INFO] Aucun fichier JSON trouvé dans {base_dir}")
            return

        print(f"[INFO] {len(json_files)} fichiers trouvés dans {base_dir}. Début de l’évaluation...")

        for path in json_files:
            article_id = path.stem
            try:
                evaluate(source, target, article_id, subfolder=subfolder)
            except Exception as e:
                print(f"[ERREUR] Échec de l’évaluation pour {article_id} : {e}")

def main():
    parser = argparse.ArgumentParser(description="Transforme un ou plusieurs fichiers XML vers forme_base.json")
    parser.add_argument("--tool", choices=["grobid", "erudit"], help="Outil de transformation")
    parser.add_argument("--id", help="ID de l'article")
    parser.add_argument("--batch", action="store_true", help="Traiter tous les fichiers .xml dans le dossier racine")
    parser.add_argument("--xml_2cols", action="store_true", help="Traiter un seul fichier dans xml_2cols/")
    parser.add_argument("--journals", nargs="+", help="Liste des journaux à traiter (ex: cqd27 ae49 haf18)")
    parser.add_argument("--evaluation", action="store_true", help="Lancer l'évaluation Grobid vs Erudit")

    args = parser.parse_args()

    # --- Cas : ÉVALUATION uniquement ---
    if args.evaluation:
        if args.id:
            evaluate("erudit", "grobid", args.id)
        elif args.journals:
            evaluate_subfolder("erudit", "grobid", journals=args.journals)
        elif args.xml_2cols:
            evaluate_subfolder("erudit", "grobid", subfolder="xml_2cols")
        elif args.batch:
            evaluate_subfolder("erudit", "grobid")
        else:
            print("[ERREUR] Pour l’évaluation, utilisez --id, --journals, --batch ou --xml_2cols")
            return

    # --- Cas : TRANSFORMATION ---
    elif args.tool:
        if args.id:
            transformer_article(args.id, args.tool)
        elif args.journals:
            transformer_batch(args.tool, journals=args.journals)
        elif args.xml_2cols:
            transformer_batch(args.tool, subfolder="xml_2cols")
        elif args.batch:
            transformer_batch(args.tool)
        else:
            print("[ERREUR] Pour la transformation, utilisez --tool avec --id, --batch, --journals ou --xml_2cols")

    else:
        print("[ERREUR] Spécifiez une action à effectuer (--tool ou --evaluation)")

if __name__ == "__main__":
    main()

    # python3 src/main.py --tool erudit --id 1080394ar_2
    # python3 src/main.py --tool grobid --id 1080394ar_2 --evaluation
    # python3 src/main.py --tool grobid --batch --evaluation