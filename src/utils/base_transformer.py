from .io import normalize_date, normalize_text, first_or_empty, first_or_raw

def convert_section(section_data):
    """
    Objectif :
        Convertir une section d'article (et ses sous-sections) en une structure JSON normalisée dans le body,
        en nettoyant le contenu textuel et en structurant les éléments multimédias, citations et formules.

    Paramètres :
        section_data (dict) : Données d'une section, extraites d’un XML structuré (ex : body_sections),
                              contenant des champs comme titre, paragraphes, figures, formules, sous-sections, etc.

    Retour :
        dict : Section normalisée contenant :
            - "title" : titre de la section (chaîne nettoyée)
            - "paragraphs" : liste de paragraphes nettoyés
            - "citations" : liste d’objets citation {text, source}
            - "urls" : Liste de liens URL présents dans la section, nettoyés.
            - "formulas" : Liste de formules mathématiques
            - "media_objects" : Liste d’objets multimédias (images, vidéos, etc.) dans leur forme brute.
            - "references" : Liste de chaînes textuelles correspondant à des références ou renvois, nettoyées.
            - "subsections" : traitement récursif des sous-sections
    """

    return {
        "title": first_or_empty(section_data.get("title")),
        "paragraphs": [normalize_text(p) for p in section_data.get("paragraphs", [])],
        "citations": [
            {
                "text": normalize_text(c.get("text", "")),
                "source": normalize_text(c.get("source", "")) if "source" in c else ""
            }
            for c in section_data.get("citations", [])
        ],
        "formulas": [
            {
                "content": normalize_text(f.get("content", "")),
                "image_href": f.get("image_href", "")
            }
            for f in section_data.get("formulas", section_data.get("equations", []))
            if isinstance(f, dict)
        ],
        "urls": [normalize_text(u) for u in section_data.get("urls", [])],
        "media_objects": section_data.get("media_objects", []),
        "references": [normalize_text(r) for r in section_data.get("references", [])],
        "subsections": [convert_section(s) for s in section_data.get("subsections", [])],
    }


def convert_to_base(data):
    """
    Objectif :
        Transformer une structure de données hétérogène issue de fichiers XML
        en un format JSON unifié, structuré et nettoyé, conforme au schéma de comparaison de l’évaluation.

    Paramètres :
        data (dict) : Données d’entrée provenant d’un XML parsé 
                     contenant des champs bibliographiques, métadonnées, auteurs, corps de texte, etc.

    Retour :
        dict : Une structure JSON complète et homogène avec :
            - Des champs simples (titre, résumé, date, etc.)
            - Des listes (mots-clés, notes, figures, tables…)
            - Des objets structurés (auteurs, équipe éditoriale, bibliographies, body...)
            - Des valeurs normalisées (texte nettoyé, date formatée, chaînes vides supprimées)
    """

    base = {
        "title": first_or_empty(data.get("title")),
        "overline": first_or_empty(data.get("overline")), 
        "subtitle": first_or_empty(data.get("subtitle")),
        "authors": [],
        "abstract": first_or_empty(data.get("abstract")),
        "date": normalize_date(first_or_raw(data.get("date"))),
        "id": {
            "doi": first_or_empty(data.get("id")),
            "issn": first_or_empty(data.get("issn")),
        },
        "pagination": {
            "start_page": first_or_empty(data.get("start_page")),
            "end_page": first_or_empty(data.get("end_page")),
        },
        "rights": {
            "text": first_or_empty(data.get("rights_text")),
            "link": first_or_empty(data.get("rights_link")),
        },
        "editorial_team":[],# data.get("editorial_team", {}),
        "issue_number": first_or_empty(data.get("issue_number")),
        "volume": first_or_empty(data.get("volume")),
        "keywords": [normalize_text(k) for k in data.get("keywords", []) if isinstance(k, str)],
        "themes": [normalize_text(t) for t in data.get("themes", []) if isinstance(t, str)],
        "language": first_or_empty(data.get("language")),

        "acknowledgements": first_or_empty(data.get("acknowledgements")),
        "biographical_notes": [normalize_text(n) for n in data.get("biographical_notes", []) if isinstance(n, str)],
        "bibliographies": [
            {
                "authors": b.get("authors", []),
                "title": normalize_text(b.get("title", "")),
                "monograph_title": normalize_text(b.get("monograph_title", "")),
                "editors": b.get("editors", []),
                "publisher": normalize_text(b.get("publisher", "")),
                "place": normalize_text(b.get("place", "")),
                "date": normalize_date(b.get("date", "")),
                "pages": normalize_text(b.get("pages", "")),
                "volume": normalize_text(b.get("volume", "")),
                "issue": normalize_text(b.get("issue", "")),
                "organization": normalize_text(b.get("organization", "")),
                "notes": normalize_text(b.get("notes", "")),
                "url": normalize_text(b.get("url", "")),
                "doi": normalize_text(b.get("doi", "")),
                "raw_reference": normalize_text(b.get("raw_reference", ""))
            }
            for b in data.get("bibliographies", [])
            if isinstance(b, dict)
        ],

        "notes": [normalize_text(n) for n in data.get("notes", []) if isinstance(n, str)],
    }

    # Traitement des auteurs (prénom, nom, affiliation, etc.)
    first_names = data.get("author_first_name", [])
    last_names = data.get("author_last_name", [])
    affiliations = data.get("author_affiliation", [])
    emails = data.get("author_email", [])
    websites = data.get("author_website", [])
    orcids = data.get("author_orcid", [])

    nb_authors = max(len(first_names), len(last_names), len(affiliations), len(emails), len(websites), len(orcids))

    for i in range(nb_authors):
        author = {
            "first_name": normalize_text(first_names[i]) if i < len(first_names) else "",
            "last_name": normalize_text(last_names[i]) if i < len(last_names) else "",
            "affiliation": normalize_text(affiliations[i]) if i < len(affiliations) else "",
            "email": normalize_text(emails[i]) if i < len(emails) else "",
            "website": normalize_text(websites[i]) if i < len(websites) else "",
            "orcid": normalize_text(orcids[i]) if i < len(orcids) else "",
        }
        base["authors"].append(author)

    editorial_team = data.get("editorial_team", [])
    if isinstance(editorial_team, list):
        base["editorial_team"] = []
        for member in editorial_team:
            personne = {}
            for k, v in member.items():
                personne[k] = normalize_text(v) if isinstance(v, str) else v
            base["editorial_team"].append(personne)


    base["body"] = []
    for s in data.get("body_sections", []):
        if isinstance(s, dict):
            base["body"].append({
                "title": normalize_text(s.get("title", "")),
                "paragraphs": [normalize_text(p) for p in s.get("paragraphs", [])],
                "parent": normalize_text(s["parent"]) if s.get("parent") else None
            })


    base["figures"] = []
    for f in data.get("figures", []):
        if isinstance(f, dict):
            base["figures"].append({
                "number": normalize_text(f.get("number", "")),
                "title": normalize_text(f.get("title", "")),
                "source": normalize_text(f.get("source", "")),
            })


    base["tables"] = []
    for t in data.get("tables", []):
        if isinstance(t, dict):
            base["tables"].append({
                "number": normalize_text(t.get("number", "")),
                "title": normalize_text(t.get("title", "")),
                "content": normalize_text(t.get("content", "")),
                "note": normalize_text(t.get("note", "")),
                "parent": normalize_text(t.get("parent", "")) if t.get("parent") else None
            })


    return base