import subprocess
import argparse
import sys
import os
from pathlib import Path

#sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
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
        subfolder (str): Si défini, précise un sous-dossier comme "xml_2cols"
    """

    # Définir les chemins d’entrée et sortie
    base_input = Path("data/raw") / f"xml_{tool}"
    base_output = Path("data/processed") / tool

    if subfolder:
        base_input = base_input / subfolder
        base_output = base_output / subfolder

    input_path = base_input / f"{article_id}.xml"
    output_path = base_output / f"{article_id}.json"

    # Lire et parser le fichier XML
    try:
        xml_tree = read_xml(input_path)
    except Exception as e:
        print(f"[ERREUR] Échec de lecture du fichier {input_path}: {e}")
        return

    if tool == "grobid":
        parsed = parse_grobid_xml(xml_tree)
    elif tool == "erudit":
        parsed = parse_erudit_xml(xml_tree)
    else:
        raise ValueError(f"Outil inconnu : {tool}")

    # Conversion vers format base + sauvegarde
    base_data = convert_to_base(parsed)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(base_data, output_path)

    print(f"[OK] {tool.upper()} => forme_base : {output_path}")


def transformer_batch(tool, subfolder=None):
    base_dir = Path("data/raw") / f"xml_{tool}"
    if subfolder:
        base_dir = base_dir / subfolder

    ids = get_ids_from_raw_xml(base_dir)
    for article_id in ids:
        print(f"[INFO] Traitement de : {article_id}")
        transformer_article(article_id, tool, subfolder=subfolder)

def evaluate_subfolder(source: str, target: str, subfolder: str = None):
    """
    Évalue tous les fichiers JSON dans un (sous-)répertoire donné.
    Si subfolder est None, on évalue les fichiers dans le dossier racine de `target`.
    """
    if subfolder:
        base_dir = Path("data/processed") / target / subfolder
    else:
        base_dir = Path("data/processed") / target

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
    parser.add_argument("--tool", required=True, choices=["grobid", "erudit"], help="Outil de transformation")
    parser.add_argument("--id", help="ID de l'article")
    parser.add_argument("--batch", action="store_true", help="Traiter tous les fichiers .xml dans le dossier racine (pas les sous-dossiers)")
    parser.add_argument("--xml_2cols", action="store_true", help="Traiter un seul fichier dans xml_2cols/")
    parser.add_argument("--evaluation", action="store_true", help="Lancer l'évaluation Grobid vs Erudit")
    args = parser.parse_args()

    # --- Cas 1 : ÉVALUATION uniquement ---
    if args.evaluation:
            if args.id:
                evaluate("erudit", "grobid", args.id)
            elif args.xml_2cols:
                evaluate_subfolder("erudit", "grobid", "xml_2cols")
            elif args.batch:
                evaluate_subfolder("erudit", "grobid", None)
            else:
                print("[ERREUR] Pour l’évaluation, utilisez soit --id, soit --batch, soit --xml_2cols")
            return  # on quitte après l’évaluation

    # --- Cas 2 : TRANSFORMATION ---
    if args.id and args.tool:
        transformer_article(args.id, args.tool)
    elif args.batch and args.tool:
        transformer_batch(args.tool)
    elif args.xml_2cols and args.tool:
        transformer_batch(args.tool, subfolder="xml_2cols")
    else:
        print("[ERREUR] Pour la transformation, utilisez --tool avec --id, --batch ou --xml_2cols")


if __name__ == "__main__":
    main()
    # python3 src/main.py --tool erudit --id 1080394ar_2
    # python3 src/main.py --tool grobid --id 1080394ar_2 --evaluation