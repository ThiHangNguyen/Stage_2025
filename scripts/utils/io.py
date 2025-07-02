import os
import json
import unicodedata
import re
from datetime import datetime


def normalize_date(date_str: str) -> str:
    if not date_str or not isinstance(date_str, str):
        return ""

    date_str = date_str.strip()

    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            dt = datetime.strptime(date_str, fmt)
            return date_str  # retourne tel quel
        except ValueError:
            continue

    return date_str

normalize_date

def parse_date(d):
    if not d:
        return None
    for fmt in ["%Y-%m-%d", "%Y-%m", "%Y"]:
        try:
            return datetime.strptime(d, fmt).date()
        except ValueError:
            continue
    return None
def compare_dates(date1: str, date2: str) -> bool:
    d1 = normalize_date(date1)
    d2 = normalize_date(date2)
    return d1 == d2 and d1 != ""

def read_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def write_json(obj, path, indent=2):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, indent=indent, ensure_ascii=False)

def read_text(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def read_xml(path):
    from lxml import etree
    with open(path, 'rb') as f:
        return etree.parse(f)

def save_xml(tree, path):
    tree.write(path, pretty_print=True, xml_declaration=True, encoding='UTF-8')

def normalize_text(text):
    """
    Nettoie et normalise un texte : minuscules, unicode, tirets, espaces.
    """
    if not isinstance(text, str):
        return ""
    # Normalisation unicode
    text = unicodedata.normalize("NFKD", text)
    # Remplacement des caractères typographiques fréquents
    text = text.replace("\u00a0", " ")  # espace insécable
    text = text.replace("–", "-")      # tiret moyen
    text = text.replace("—", "-")      # tiret long
    text = text.replace("’", "'")      # apostrophe courbe
    # Minuscule + strip + suppression des espaces multiples
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text



def first_or_empty(x):
    """
    Retourne le premier élément d’une liste ou une chaîne vide si vide ou None.
    """
    return x[0] if isinstance(x, list) and x else ""


def write_json(data, path):
    """
    Écrit un dictionnaire Python dans un fichier JSON.
    Les objets datetime.date sont convertis en chaînes.
    """
    def convert(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, datetime.date):
            return obj.isoformat()
        return str(obj)

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=convert)


def one_empty_list(val1, val2):
    return ((not val1 or len(val1) == 0) and val2) or ((not val2 or len(val2) == 0) and val1)

def one_empty(val1, val2):
    return (
        (not val1 or val1.strip() == "") and (val2 and val2.strip() != "")
    ) or (
        (not val2 or val2.strip() == "") and (val1 and val1.strip() != "")
    )

def both_empty_list(val1, val2):
    return (not val1 or len(val1) == 0) and (not val2 or len(val2) == 0)

def both_empty(val1, val2):
    return (
        (not val1 or val1.strip() == "") and (not val2 or val2.strip() == "")
    )


def load_json(tool, article_id):
    path = f"data/processed/{tool}/{article_id}.json"
    if not os.path.exists(path):
        raise FileNotFoundError(f"Fichier manquant : {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_to_csv(tool, article_id, results):
    import pandas as pd
    import os

    output_dir = f"../results/csv/{tool}"
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, f"{article_id}.csv")

    # Création du DataFrame
    df = pd.DataFrame.from_dict(results, orient="index")
    df.index.name = "field"

    # Colonnes souhaitées : uniquement les versions sans _unordered
    strategies = ["strict", "soft", "levenshtein"]
    metrics = ["accuracy", "f1", "recall", "support", "matched"]

    ordered_columns = []

    for strat in strategies:
        for metric in metrics:
            col = f"{metric}_{strat}"
            if col in df.columns:
                ordered_columns.append(col)

    # Ajouter les colonnes restantes à la fin si besoin
    for col in df.columns:
        if col not in ordered_columns:
            ordered_columns.append(col)

    df = df[ordered_columns]
    df.to_csv(path)

