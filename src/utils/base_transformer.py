import re
import html
from .io import normalize_date, normalize_text, first_or_empty, first_or_raw


def convert_section(section_data):

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
        "figures": [
            {
                #"id": normalize_text(f.get("id", "")),
                "label": normalize_text(f.get("label", "")),
                "caption": normalize_text(f.get("caption", "")),
                "source": normalize_text(f.get("source", ""))
            }
            for f in section_data.get("figures", [])
            if isinstance(f, dict)
        ],
        "formulas": [
            {
                "content": normalize_text(f.get("content", "")),
                "image_href": f.get("image_href", "")
            }
            for f in section_data.get("formulas", section_data.get("equations", []))
            if isinstance(f, dict)
        ],
        "tables": section_data.get("tables", []), 
        "urls": [normalize_text(u) for u in section_data.get("urls", [])],
        "media_objects": section_data.get("media_objects", []),
        "references": [normalize_text(r) for r in section_data.get("references", [])],
        "subsections": [convert_section(s) for s in section_data.get("subsections", [])],
    }
"""
"lists": {
    "ordonnees": [normalize_text(l) for l in section_data.get("lists", {}).get("ordonnees", [])],
    "non_ordonnes": [normalize_text(l) for l in section_data.get("lists", {}).get("non_ordonnes", [])],
    "relation": [normalize_text(l) for l in section_data.get("lists", {}).get("relation", [])],
},
"""


def convert_to_base(data):
    base = {
        "title": first_or_empty(data.get("title")),
        "overline": first_or_empty(data.get("overline")), #surtitre
        "subtitle": first_or_empty(data.get("subtitle")),
        "authors": [],
        "abstract": first_or_empty(data.get("abstract")),
        "date": normalize_date(first_or_raw(data.get("date"))),
        "id": {
            #"ori": first_or_empty(data.get("id")),
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

        # Nouveaux champs pour des annexes
        #"annexes": [normalize_text(a) for a in data.get("annexes", []) if isinstance(a, str)],
        "acknowledgements": first_or_empty(data.get("acknowledgements")),
        "biographical_notes": [normalize_text(n) for n in data.get("biographical_notes", []) if isinstance(n, str)],
        #"bibliographies": [normalize_text(b) for b in data.get("bibliographies", []) if isinstance(b, str)],
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
    #print(affiliations)
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


    base["body"] = [convert_section(s) for s in data.get("body_sections", [])]
    # Ajouter les figures globales si elles existent
    base["figures"] = []
    for f in data.get("figures", []):
        if isinstance(f, dict):
            base["figures"].append({
                "label": normalize_text(f.get("label", "")),
                "caption": normalize_text(f.get("caption", "")),
                "legends" : f.get("legends", []),
                "subfigures": f.get("subfigures", [])
            })

    base["tables"] = []
    for t in data.get("tables", []):
        if isinstance(t, dict):
            base["tables"].append({
                "label": normalize_text(t.get("label", "")),
                "caption": normalize_text(t.get("caption", "")),
                "rows": t.get("rows", [])
            })

    return base