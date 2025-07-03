authors = [
    {
        "first_name": "megan",
        "last_name": "hebertlefebvre",
        "affiliation": "graphiste, agence niaka",
        "email": "",
        "website": "",
        "orcid": ""
    },
    {
        "first_name": "edgar",
        "last_name": "blanchet",
        "affiliation": "charge de projet en anthropologie sociale et culturelle",
        "email": "",
        "website": "",
        "orcid": ""
    }
]

STRUCTURED_KEYS = {
    "authors": ["first_name", "last_name"],
    "editorial_team": ["first_name", "category"],  
    "figures": ["title", "id"],
    "tables": ["title", "id"],
    "body": ["title"],
    # Ajoute ici d'autres types si nécessaire
}

def make_hash_key(obj: dict, type_: str) -> str:
    """
    Construit une clé d'identification unique pour un objet structuré,
    selon les champs définis pour ce type.
    """
    fields = STRUCTURED_KEYS.get(type_, [])

    # Cas spécial : fallback pour editorial_team
    if type_ == "editorial_team":
        if obj.get("first_name"):
            fields = ["first_name"]
        elif obj.get("organization"):
            fields = ["organization"]

    return "|".join([obj.get(f, "") for f in fields if f in obj])



for author in authors:
    key = make_hash_key(author, "authors")
    print(f"Key: {key}")

def index_by_key(obj_list: list[dict], type_: str) -> dict:
    """
    Construit un dictionnaire {clé_hash: objet} pour une liste d’objets structurés.
    """
    return {
        make_hash_key(obj, type_): obj
        for obj in obj_list
        if make_hash_key(obj, type_)  # exclure les clés vides
    }

indexed_authors = index_by_key(authors, "authors")

# 🔎 Voir les clés et leurs valeurs
for k, v in indexed_authors.items():
    print(f"Clé: {k} → Valeur: {v}")
