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

def process_article(article_id, tool):
    input_path = Path("data") / "raw" / f"xml_{tool}" / f"{article_id}.xml"
    output_path = Path("data") / "processed" / tool / f"{article_id}.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    xml_tree = read_xml(input_path)
    if tool == "grobid":
        print ("here")
        parsed = parse_grobid_xml(xml_tree)
    else:
        parsed = parse_erudit_xml(xml_tree)

    base_data = convert_to_base(parsed)
    write_json(base_data, output_path)

    print(f"[OK] Fichier {tool} → forme_base : {output_path}")


def transformer_article(article_id, tool):
    input_path = Path("data/raw") / f"xml_{tool}" / f"{article_id}.xml"
    output_path = Path("data/processed") / tool / f"{article_id}.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    xml_tree = read_xml(input_path)

    if tool == "grobid":
        parsed = parse_grobid_xml(xml_tree)
    elif tool == "erudit":
        parsed = parse_erudit_xml(xml_tree)
    else:
        raise ValueError(f"Outil inconnu : {tool}")

    base_data = convert_to_base(parsed)
    write_json(base_data, output_path)
    print(f"[OK] {tool.upper()} → forme_base : {output_path}")

def main():
    # parser = argparse.ArgumentParser()
    # parser.add_argument("--raw-dir", default="../data/raw", help="Dossier contenant les fichiers XML bruts")
    # parser.add_argument("--strategy", default="soft", choices=["strict", "soft", "levenshtein"],
    #                     help="Stratégie pour visualisation (default: soft)")
    # args = parser.parse_args()

    # ids = get_ids_from_raw_xml(args.raw_dir)
    # strategy = args.strategy

    # for article_id in ids:
    #     print(f"\n==========================")
    #     print(f"[INFO] Traitement de : {article_id}")
    #     print(f"==========================")

    #     # Étape 1 : Transformation GROBID
    #     run_command(["python3", "transformers/main.py", "--tool", "grobid", "--id", article_id])

    #     # Étape 2 : Transformation ÉRUDIT
    #     run_command(["python3", "transformers/main.py", "--tool", "erudit", "--id", article_id])

    #     # Étape 3 : Évaluation GROBID vs ÉRUDIT
    #     run_command(["python3", "-m", "evaluation.evaluation", "--tool", "grobid", "--id", article_id])

    #     # Étape 4 : Visualisation
    #     run_command(["python3", "-m", "evaluation.visualisation", "--tool", "grobid",
    #                  "--id", article_id, "--strategy", strategy])
    parser = argparse.ArgumentParser(description="Transforme un ou plusieurs fichiers XML vers forme_base.json")
    parser.add_argument("--tool", required=True, choices=["grobid", "erudit"], help="Outil de transformation")
    parser.add_argument("--id", required=True, help="ID de l'article")
    parser.add_argument("--evaluation", action="store_true", help="Lancer l'évaluation Grobid vs Erudit")
    args = parser.parse_args()
    if args.evaluation:
        # Étape : évaluation grobid vs erudit
        evaluate("erudit", "grobid", args.id)
    else:
        transformer_article(args.id, args.tool)


if __name__ == "__main__":
    main()
    # python3 scripts/main.py --tool erudit --id 018001ar_2
    # python3 src/main.py --tool grobid --id 1080394ar_2 --evaluation