import os
import ast
import argparse
import pandas as pd
from collections import defaultdict

def is_structured(value):
    """
    Vérifie si une valeur représente un dictionnaire (JSON-like).
    
    Paramètres
    ----------
    value : str
        Valeur en texte (souvent issue d’un CSV).
    
    Retour
    ------
    bool : True si la valeur est un dictionnaire parsable, False sinon.
    """
    try:
        parsed = ast.literal_eval(value)
        return isinstance(parsed, dict)
    except:
        return False

def process_per_field(repertoires, base_dir):
    """
    Calcule les scores moyens par champ (simple et structuré) pour chaque répertoire.
    Génère deux CSV : simple.csv et structured.csv dans results/csv/<tool>/means/.

    Paramètres
    ----------
    repertoires : list[str]
        Liste des sous-dossiers (ex: ["haf18", "2cols"]).
    base_dir : str
        Chemin vers le dossier racine d’un outil (ex: results/csv/grobid).

    Résultat
    --------
    - results/csv/<tool>/means/simple.csv
    - results/csv/<tool>/means/structured.csv
    """

    simple_rows = []
    structured_rows = []

    for rep in repertoires:
        dir_path = os.path.join(base_dir, rep)
        if not os.path.isdir(dir_path):
            print(f"Répertoire introuvable : {dir_path}")
            continue

        simple_scores = defaultdict(lambda: defaultdict(list))
        structured_scores = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

        for file in os.listdir(dir_path):
            if not file.endswith(".csv"):
                continue
            file_path = os.path.join(dir_path, file)
            try:
                df = pd.read_csv(file_path)
            except Exception as e:
                print(f"Erreur lecture fichier {file_path}: {e}")
                continue

            df = df[df["has_ref"] == 1]  

            for _, row in df.iterrows():
                field = row["field"]
                for method in ["strict", "soft", "levenshtein"]:
                    val = row[method]
                    if is_structured(val):
                        parsed = ast.literal_eval(val)
                        for metric in ["precision", "recall", "avg_similarity"]:
                            structured_scores[field][method][metric].append(parsed.get(metric, 0.0))
                    else:
                        try:
                            simple_scores[field][method].append(float(val))
                        except:
                            simple_scores[field][method].append(0.0)

        all_simple_fields = sorted(simple_scores.keys())
        all_struct_fields = sorted(structured_scores.keys())

        #  simple.csv : une ligne par méthode
        for method in ["strict","soft", "levenshtein"]:
            row = {"directory": rep, "method": method}
            for field in all_simple_fields:
                values = simple_scores[field][method]
                row[field] = sum(values) / len(values) if values else 0.0
            simple_rows.append(row)

        #  structured.csv : une ligne par méthode+metric
        for method in ["strict","soft", "levenshtein"]:
            for metric in ["precision", "recall", "avg_similarity"]:
                row = {"directory": rep, "metric": f"{method}_{metric}"}
                for field in all_struct_fields:
                    values = structured_scores[field][method][metric]
                    row[field] = sum(values) / len(values) if values else 0.0
                structured_rows.append(row)

    # Export CSV
    out_dir = os.path.join(base_dir, "means")
    os.makedirs(out_dir, exist_ok=True)

    df_simple = pd.DataFrame(simple_rows)
    df_structured = pd.DataFrame(structured_rows)

    df_simple = df_simple[["directory", "method"] + sorted([col for col in df_simple.columns if col not in ["directory", "method"]])]
    df_structured = df_structured[["directory", "metric"] + sorted([col for col in df_structured.columns if col not in ["directory", "metric"]])]

    df_simple.to_csv(os.path.join(out_dir, "simple.csv"), index=False)
    df_structured.to_csv(os.path.join(out_dir, "structured.csv"), index=False)

    print(f"Résultats sauvegardés dans :\n  - {out_dir}/simple.csv\n  - {out_dir}/structured.csv")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Calcul des moyennes par champ avec has_ref=1")
    parser.add_argument('--dirs', nargs='+', required=True, help="Liste des sous-dossiers dans results/csv/<tool>/")
    parser.add_argument('--tool', required=True, help="Nom de l’outil évalué (ex: grobid, nougat)")
    args = parser.parse_args()

    BASE_DIR = f"results/csv/{args.tool}"
    process_per_field(args.dirs, BASE_DIR)
