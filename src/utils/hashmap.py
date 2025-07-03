from typing import Dict, List

STRUCTURED_KEYS = {
    "authors": ["first_name", "last_name"],
    "editorial_team": ["first_name", "category"],  
    "figures": ["label"],
    "tables": ["label"],
    "body": ["title"],
}

def make_hash_key(obj: Dict, type_: str) -> str:
    keys = STRUCTURED_KEYS.get(type_, [])
    values = [obj.get(k, "") for k in keys if isinstance(obj.get(k, ""), str) and obj.get(k, "").strip()]
    return ".".join(values).strip()


def hashmap(obj_list: List[Dict], type_: str) -> Dict[str, Dict]:
    """
    Crée un dictionnaire {clé_unique: objet} pour appariement rapide.
    Ignore les objets dont la clé générée est vide.
    """
    result = {}
    for obj in obj_list:
        key = make_hash_key(obj, type_)
        if key:  
            result[key] = obj
    return result


