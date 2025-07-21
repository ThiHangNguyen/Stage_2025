from typing import Dict, List

STRUCTURED_KEYS = {
    "authors": ["first_name", "last_name"],
    "editorial_team": ["first_name", "category"],  
    "figures": ["label"],
    "tables": ["label"],
    "body": ["title"],
}

def make_hash_key(obj: Dict, type_: str) -> str:
    """
    Génère une clé unique à partir des champs définis pour un type structuré donné 

    Paramètres :
        obj (Dict) : L'objet structuré (dictionnaire) à partir duquel générer la clé.
        type_ (str) : Le type de l'objet (doit correspondre à une clé dans STRUCTURED_KEYS).

    Retour :
        str : Une chaîne représentant la clé unique de l'objet. Chaîne vide si aucune valeur pertinente n’est trouvée.
    """

    keys = STRUCTURED_KEYS.get(type_, [])
    values = [obj.get(k, "") for k in keys if isinstance(obj.get(k, ""), str) and obj.get(k, "").strip()]
    return ".".join(values).strip()


def hashmap(obj_list: List[Dict], type_: str) -> Dict[str, Dict]:
    """
    Crée un dictionnaire {clé_unique: objet} pour appariement rapide.
    Ignore les objets dont la clé générée est vide.

    Paramètres :
        obj_list (List[Dict]) : Liste d’objets structurés.
        type_ (str) : Type d’objet structuré, utilisé pour déterminer les champs clés de génération de la clé.

    Retour :
        Dict[str, Dict] : Dictionnaire de la forme {clé_unique : objet}.
    """
    result = {}
    for obj in obj_list:
        key = make_hash_key(obj, type_)
        if key:  
            result[key] = obj
    return result


