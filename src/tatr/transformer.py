from pathlib import Path
from typing import Dict, Any, List
import json

from utils.io import normalize_text  

def _to_str(x) -> str:
    """Convertit en str et normalise (gère None / listes)."""
    if x is None:
        return ""
    if isinstance(x, list):
        x = " ".join(str(e) for e in x)
    return normalize_text(str(x))

def parse_tatr_json(filepath: str, keep_empty: bool = True) -> Dict[str, Any]:
    """
    Lit un JSON TATR et renvoie un dict cohérent avec Nougat:
      {
        "tool": "tatr",
        "tables": [
          {"number": str, "title": str, "content": str, "note": str}, ...
        ],
        "content_table": [str, ...]  # liste des `content` des tables retenues
      }
    - handle: fichier racine = liste OU dict
    - keep_empty=True pour l'évaluation (conserver tables au content vide)
      -> `content_table` reflète le même filtrage que `tables`.
    """
    data = json.loads(Path(filepath).read_text(encoding="utf-8"))

    # Cas 1: racine = liste de tables
    if isinstance(data, list):
        raw_tables: List[dict] = [t for t in data if isinstance(t, dict)]
    # Cas 2: racine = dict (ex: {"tables":[...]})
    elif isinstance(data, dict):
        raw_tables = data.get("tables")
        if raw_tables is None:
            # fallback: essayer de récupérer une liste de dicts ressemblant à des tables
            raw_tables = []
            for v in data.values():
                if isinstance(v, list) and v and all(isinstance(x, dict) for x in v):
                    raw_tables = v
                    break
        if raw_tables is None:
            raw_tables = []
    else:
        raw_tables = []

    tables_out: List[Dict[str, str]] = []
    content_table: List[str] = []

    for t in raw_tables:
        number  = _to_str(t.get("number"))
        title   = _to_str(t.get("title"))
        content = _to_str(t.get("content"))
        # Harmoniser: TATR a souvent "sources" ; Nougat utilise "note" (chaîne)
        note    = _to_str(t.get("note") if "note" in t else t.get("sources", ""))

        if keep_empty or content.strip():
            tables_out.append({
                "number": number,     # string ("" si inconnu)
                "title": title,       # string
                "content": content,   # string
                "note": note          # string
            })
            content_table.append(content)

    return {"tool": "tatr", "tables": tables_out, "content_table": content_table}
