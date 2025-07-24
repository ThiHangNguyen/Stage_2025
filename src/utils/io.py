import os
import json
import unicodedata
import re
from datetime import datetime
from lxml import etree
import pandas as pd

def normalize_date(date_str: str) -> str:
    """
    Nettoie une chaîne de date (au format YYYY, YYYY-MM, ou YYYY-MM-DD) 
    et vérifie si elle correspond à un format de date valide.

    Si valide, retourne la date sous forme de chaîne ; sinon, renvoie la chaîne inchangée.
    """

    if not date_str or not isinstance(date_str, str):
        return ""

    date_str = date_str.strip()

    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            dt = datetime.strptime(date_str, fmt)
            return date_str  
        except ValueError:
            continue

    return date_str

def read_json(path):

    """
    Lit un fichier JSON et retourne son contenu sous forme de dictionnaire.
    """
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def write_json(obj, path, indent=2):

    """
    Écrit un dictionnaire dans un fichier JSON avec indentation.
    Crée les dossiers nécessaires si le chemin n’existe pas.
    Gère les dates avec `isoformat()` si nécessaire.
    """

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, indent=indent, ensure_ascii=False)

def read_text(path):

    """
    Lit un fichier texte UTF-8 et retourne son contenu sous forme de chaîne.
    """
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def read_xml(path):

    """
    Lit et parse un fichier XML en utilisant lxml.etree, et retourne un arbre XML.
    """
    from lxml import etree
    with open(path, 'rb') as f:
        return etree.parse(f)

def save_xml(tree, path):

    """
    Sauvegarde un arbre XML (lxml.etree.ElementTree) dans un fichier,
    avec indentations et déclaration XML.
    """
    tree.write(path, pretty_print=True, xml_declaration=True, encoding='UTF-8')

def normalize_text(text):
    """
    Nettoie et normalise un texte :
    - Minuscule
    - Suppression des accents
    - Remplacement des caractères typographiques (tirets, apostrophes, guillemets)
    - Suppression des tirets et apostrophes
    - Réduction des espaces multiples
    
    Retourne une chaîne nettoyée.
    """
    if not isinstance(text, str):
        return ""
    # Normalisation unicode
    text = unicodedata.normalize("NFKD", text)
    # Suppression des accents (caractères non-spacing)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    # Remplacement des caractères typographiques fréquents
    text = text.replace("\u00a0", " ")  # espace insécable
    text = text.replace("–", "-")      # tiret moyen
    text = text.replace("—", "-")      # tiret long
    text = text.replace("’", "'")        # apostrophe courbe
    text = text.replace("‘", "'")        # apostrophe ouvrante
    text = text.replace("«", "")         # guillemet français ouvrant
    text = text.replace("»", "")         # guillemet français fermant
    text = text.replace('"', "")         # guillemet droit
    #Suppression des tirets et apostrophes
    text = re.sub(r"[-']", "", text)
    text = re.sub(r"\s+([,.])", r"\1", text)
    # Minuscule + strip + suppression des espaces multiples
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text



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

def load_json(tool, article_id, subfolder=None):
    if subfolder:
        path = f"data/processed/{tool}/{subfolder}/{article_id}.json"
    else:
        path = f"data/processed/{tool}/{article_id}.json"

    if not os.path.exists(path):
        raise FileNotFoundError(f"Fichier manquant : {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
    
def save_to_csv(tool, article_id, results, output_subfolder=None):
    """
    Sauvegarde les résultats d'évaluation dans un fichier CSV.
    
    Args:
        tool (str): Nom de l’outil évalué (ex: "grobid").
        article_id (str): ID de l’article.
        results (dict): Dictionnaire des résultats par champ.
        output_subfolder (str, optional): Sous-dossier de sortie (ex: "xml_2cols").
    """
    if output_subfolder:
        output_dir = os.path.join("results", "csv", tool, output_subfolder)
    else:
        output_dir = os.path.join("results", "csv", tool)

    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, f"{article_id}.csv")

    df = pd.DataFrame.from_dict(results, orient="index")
    df.index.name = "field"

    df.to_csv(path)
    print(f"Résultats sauvegardés dans {path}")



def extract_from_path(root, xpath, namespaces=None):
    """
    Extrait le texte des noeuds XML correspondant à un XPath donné.
    Renvoie une liste de chaînes normalisées.
    """
    if namespaces is None:
        namespaces = {}

    elements = root.xpath(xpath, namespaces=namespaces)

    result = []
    for el in elements:
        if isinstance(el, etree._Element):
            text = "".join(el.itertext()).strip()
            if text:
                result.append(text)
        elif isinstance(el, str):
            result.append(el.strip())

    return result


def first_or_empty(val):
    if isinstance(val, list):
        return normalize_text(val[0]) if val else ""
    elif isinstance(val, str):
        return normalize_text(val)
    return ""


def first_or_raw(val):
    """Retourne le premier élément brut (non modifié), utile pour des dates, DOIs, etc."""
    if isinstance(val, list):
        return val[0] if val else ""
    elif isinstance(val, str):
        return val
    return ""


def match_format(value: str, format_type: str) -> bool:
    """
    Vérifie si une chaîne 'value' correspond à un format donné.
    Formats pris en charge : email, date, year, number, word, issn, doi, id
    """
    if not isinstance(value, str):
        return False

    value = value.strip()

    patterns = {
        "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        "date": r"^\d{4}(-\d{2}){0,2}$",           # YYYY or YYYY-MM or YYYY-MM-DD
        "year": r"^\d{4}$",                        # Only YYYY
        "number": r"^-?\d+(\.\d+)?$",              # int or float
        "word": r"^[a-zA-ZÀ-ÿ]+$",                 # letters only
        "issn": r"^\d{4}-\d{3}[\dXx]$",            # ex: 1234-567X
        "doi": r"^10\.\d{4,9}/[-._;()/:a-zA-Z0-9]+$",
        "id": r"^[a-zA-Z0-9\-_]+$"
    }

    pattern = patterns.get(format_type)
    if pattern is None:
        raise ValueError(f"Format type '{format_type}' not supported.")

    return re.fullmatch(pattern, value) is not None

def has_data(value):
    """
    Retourne True si la valeur contient de l'information.
    - Pour une string : non vide
    - Pour une liste : au moins un élément non vide
    - Pour un dict : au moins un champ non vide
    - Pour None ou vide : False
    """
    if value in (None, "", [], {}):
        return False
    if isinstance(value, str):
        return value.strip() != ""
    if isinstance(value, list):
        return any(has_data(v) for v in value)
    if isinstance(value, dict):
        return any(has_data(v) for v in value.values())
    return True
