import subprocess
import argparse
import sys
import os
from pathlib import Path
from utils.io import read_xml, write_json
from utils.base_transformer import convert_to_base
from erudit.transformer import parse_erudit_xml
from grobid.transformer import parse_grobid_xml
from nougat.transformer import parse_nougat_md
from evaluation.evaluation import evaluate


#sys.path.append(str(Path(__file__).resolve().parent))
BASE_DIR = Path(__file__).resolve().parent.parent
TOOL_FILE_TYPES = {
    "grobid": "xml",
    "erudit": "xml",
    "nougat": "mmd",
}

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
    Transforme un fichier brut en JSON standardisé.

    Args:
        article_id (str): Nom de l’article sans extension (ex: "1039880ar")
        tool (str): Nom de l’outil ("grobid", "erudit", "nougat")
        subfolder (str): Sous-répertoire (ex: "ae49", "cqd27", etc.)
    """
    if tool not in TOOL_FILE_TYPES:
        raise ValueError(f"[ERREUR] Outil inconnu : {tool}")

    filetype = TOOL_FILE_TYPES[tool]

    input_base = BASE_DIR / "data" / "raw"
    output_base = BASE_DIR / "data" / "processed"

    # Dossier d'entrée spécifique par outil
    input_dir = input_base / f"{filetype}_{tool}"
    output_dir = output_base / tool

    # Construire chemins d'entrée / sortie
    if subfolder:
        input_path = input_dir / subfolder / f"{article_id}.{filetype}"
        output_path = output_dir / subfolder / f"{article_id}.json"
    else:
        input_path = input_dir / f"{article_id}.{filetype}"
        output_path = output_dir / f"{article_id}.json"

    # Lecture et parsing
    try:
        if tool == "nougat":
            parsed = parse_nougat_md(input_path)
        else:
            xml_tree = read_xml(input_path)
            parsed = parse_grobid_xml(xml_tree) if tool == "grobid" else parse_erudit_xml(xml_tree)
    except Exception as e:
        print(f"[ERREUR] Lecture/Parsing échoué pour {input_path} : {e}")
        return

    # Conversion et sauvegarde
    base_data = convert_to_base(parsed)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(base_data, output_path)

    print(f"[OK] {tool.upper()} => JSON standardisé : {output_path}")


def get_ids_from_raw(tool, folder):
    """
    Retourne les IDs des fichiers bruts (.xml, .latex, .mmd...) selon l’outil.
    """
    extension = TOOL_FILE_TYPES[tool]
    return [f.stem for f in Path(folder).glob(f"*.{extension}")]


def transformer_batch(tool, journals=None, subfolder=None):
    """
    Traite tous les fichiers pour un outil donné, soit dans un sous-dossier donné, soit pour plusieurs journaux.
    """
    base_dir = Path("data/raw") / f"{TOOL_FILE_TYPES[tool]}_{tool}"

    get_ids_func = get_ids_from_raw_xml  # car les IDs sont cohérents (ex : sans extension)
    get_ids_func = lambda folder: get_ids_from_raw(tool, folder)

    if journals:
        for journal in journals:
            dir_journal = base_dir / journal
            if not dir_journal.exists():
                print(f"[WARN] Le dossier {dir_journal} n'existe pas.")
                continue
            ids = get_ids_func(dir_journal)
            for article_id in ids:
                print(f"[INFO] Traitement de : {journal}/{article_id}")
                transformer_article(article_id, tool, subfolder=journal)
    else:
        if subfolder:
            base_dir = base_dir / subfolder
        ids = get_ids_func(base_dir)
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
    parser.add_argument("--tool", choices=["grobid", "erudit", "nougat"], help="Outil de transformation")
    parser.add_argument("--id", help="ID de l'article")
    parser.add_argument("--batch", action="store_true", help="Traiter tous les fichiers .xml dans le dossier racine")
    parser.add_argument("--journals", nargs="+", help="Liste des journaux à traiter (ex: cqd27 ae49 haf18)")
    parser.add_argument("--evaluation", action="store_true", help="Lancer l'évaluation Grobid vs Erudit")

    args = parser.parse_args()

    # --- Cas : ÉVALUATION uniquement ---
    if args.evaluation:
        if args.tool is None:
            print("[ERREUR] Spécifiez l'outil à évaluer avec --tool")
            return

        if args.id:
            evaluate(args.tool, "erudit", args.id)
        elif args.journals:
            evaluate_subfolder(args.tool, "erudit", journals=args.journals)
        else:
            print("[ERREUR] Pour l’évaluation, utilisez --id, --journals, --batch ou --xml_2cols")
            return


    # --- Cas : TRANSFORMATION ---
    elif args.tool:
        if args.id:
            transformer_article(args.id, args.tool)
        elif args.journals:
            transformer_batch(args.tool, journals=args.journals)
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