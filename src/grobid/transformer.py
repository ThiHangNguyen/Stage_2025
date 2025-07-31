from utils.io import normalize_date, normalize_text, extract_from_path
from .road import chemins_grobid
ns_grobid = {"tei": "http://www.tei-c.org/ns/1.0"}


def extract_grobid_footnotes(root):
    """
    Extrait uniquement les notes de bas de page (place='foot') qui ont un numéro (@n).
    Format final : [n] texte
    """
    notes = []
    for note in root.xpath("//tei:note[@place='foot' and @n]", namespaces=ns_grobid):
        numero = note.attrib.get("n")
        #print(numero)
        texte = " ".join(note.itertext())
        #print (texte)
        if numero and texte:
            notes.append(f"[{numero}] {normalize_text(texte)}")
    return notes



def extract_grobid_biblio_dicts(root):
    biblios = []
    bibl_structs = root.xpath(".//tei:back//tei:div[@type='references']//tei:listBibl//tei:biblStruct", namespaces=ns_grobid)
    print(len(bibl_structs))
    for bibl in root.xpath(".//tei:back//tei:div[@type='references']//tei:listBibl//tei:biblStruct", namespaces=ns_grobid):
       
        entry = {
            "authors": [],
            "title": "",
            "monograph_title": "",
            "editors": [],
            "publisher": "",
            "place": "",
            "date": "",
            "pages": "",
            "volume": "",
            "issue": "",
            "organization": "",
            "type_note": "",
            "url": "",
            "doi": ""
        }

        # Authors (from both analytic and monogr)
        authors = bibl.xpath(".//tei:analytic//tei:author//tei:persName", namespaces=ns_grobid) + \
                  bibl.xpath(".//tei:monogr//tei:author//tei:persName", namespaces=ns_grobid)
        for author in authors:
            fn = author.findtext("tei:forename", namespaces=ns_grobid)
            ln = author.findtext("tei:surname", namespaces=ns_grobid)
            if ln:
                full = f"{ln}, {fn}" if fn else ln
            elif fn:
                full = fn
            else:
                full = author.text or ""
            if full.strip():
                entry["authors"].append(full.strip())

        # Editors
        editors = bibl.xpath(".//tei:editor//tei:persName", namespaces=ns_grobid)
        for ed in editors:
            fn = ed.findtext("tei:forename", namespaces=ns_grobid)
            ln = ed.findtext("tei:surname", namespaces=ns_grobid)
            if ln:
                full = f"{ln}, {fn}" if fn else ln
            elif fn:
                full = fn
            else:
                full = ed.text or ""
            if full.strip():
                entry["editors"].append(full.strip())

        # Titles
        title_analytic = bibl.findtext(".//tei:analytic/tei:title", namespaces=ns_grobid)
        title_monogr = bibl.findtext(".//tei:monogr/tei:title", namespaces=ns_grobid)
        entry["title"] = title_analytic or ""
        entry["monograph_title"] = title_monogr or ""

        # Publisher, Place, Date
        entry["publisher"] = bibl.findtext(".//tei:imprint/tei:publisher", namespaces=ns_grobid) or ""
        entry["place"] = bibl.findtext(".//tei:meeting/tei:address/tei:addrLine", namespaces=ns_grobid) or \
                         bibl.findtext(".//tei:imprint/tei:pubPlace", namespaces=ns_grobid) or ""
        entry["date"] = normalize_date(bibl.findtext(".//tei:imprint/tei:date", namespaces=ns_grobid) or "")

        # Volume, Issue
        entry["volume"] = bibl.findtext(".//tei:biblScope[@unit='volume']", namespaces=ns_grobid) or ""
        entry["issue"] = bibl.findtext(".//tei:biblScope[@unit='issue']", namespaces=ns_grobid) or ""

        # Pages (from/to)
        pages = bibl.find(".//tei:biblScope[@unit='page']", namespaces=ns_grobid)
        if pages is not None:
            f = pages.attrib.get("from")
            t = pages.attrib.get("to")
            if f and t:
                entry["pages"] = f"{f}–{t}"
            elif f:
                entry["pages"] = f
            elif pages.text:
                entry["pages"] = pages.text.strip()

        # DOI
        entry["doi"] = bibl.findtext(".//tei:idno[@type='DOI']", namespaces=ns_grobid) or ""

        # Organization (from respStmt)
        entry["organization"] = bibl.findtext(".//tei:respStmt/tei:orgName", namespaces=ns_grobid) or ""

        # Notes sans attribut @type directement sous <biblStruct>
        note_nodes = bibl.xpath("./tei:note[not(@type)]", namespaces=ns_grobid)
        entry["notes"] = " ".join(normalize_text(n.text) for n in note_nodes if n is not None and n.text)

        # URL (ptr target)
        ptr = bibl.find(".//tei:ptr", namespaces=ns_grobid)
        if ptr is not None:
            entry["url"] = ptr.attrib.get("target", "")

        raw_refs = [
            normalize_text(" ".join(note.itertext()))
            for note in bibl.findall("tei:note[@type='raw_reference']", namespaces=ns_grobid)
        ]
        entry["raw_reference"] = " ".join(raw_refs) if raw_refs else ""

        # Normaliser les champs
        for k, v in entry.items():
            if isinstance(v, list):
                entry[k] = [normalize_text(x) for x in v if x]
            else:
                entry[k] = normalize_text(v)

        biblios.append(entry)

    return biblios



def extract_grobid_author_affiliations_flat(root):
    """
    #Extrait les affiliations des auteurs dans GROBID (plate et simple).
    """
    affiliations = []
    authors = root.xpath("//tei:sourceDesc//tei:author", namespaces={"tei": "http://www.tei-c.org/ns/1.0"})

    for author in authors:
        aff_nodes = author.xpath(".//tei:affiliation//tei:orgName", namespaces={"tei": "http://www.tei-c.org/ns/1.0"})
        if aff_nodes:
            aff_text = " ".join([a.text for a in aff_nodes if a.text])
            if aff_text:
                affiliations.append(aff_text.strip())

    return affiliations


def extract_body(root):
    sections = []

    body = root.find(".//tei:text/tei:body", namespaces=ns_grobid)
    if body is None:
        return []

    for div in body.findall("tei:div", namespaces=ns_grobid):
        section = {}

        # Titre de section
        head_node = div.find("tei:head", namespaces=ns_grobid)
        section["title"] = " ".join(head_node.itertext()) if head_node is not None else ""

        # Paragraphes (p + items)
        paragraphs = []
        for child in div:
            if child.tag == f"{{{ns_grobid['tei']}}}p":
                text = " ".join(child.itertext())
                if text.strip():
                    paragraphs.append(text.strip())
            elif child.tag == f"{{{ns_grobid['tei']}}}list":
                for item in child.findall("tei:item", namespaces=ns_grobid):
                    item_text = " ".join(item.itertext())
                    if item_text.strip():
                        paragraphs.append(item_text.strip())

        section["paragraphs"] = paragraphs
        sections.append(section)

    return sections

#title section - body
def extract_section_titles(root):
    """
    Extrait uniquement les titres des sections (<head>) du corps (<body>) du document TEI GROBID.
    Retourne une liste de chaînes de caractères.
    """
    section_titles = []

    body = root.find(".//tei:text/tei:body", namespaces=ns_grobid)
    if body is None:
        return []

    for div in body.findall("tei:div", namespaces=ns_grobid):
        head_node = div.find("tei:head", namespaces=ns_grobid)
        title = " ".join(head_node.itertext()).strip() if head_node is not None else ""
        if title:
            section_titles.append(title)

    return section_titles


def extract_grobid_tables(root):
    ns = {"tei": "http://www.tei-c.org/ns/1.0"}
    tables = []

    for figure in root.findall(".//tei:figure", namespaces=ns):
        print("Found <figure>")

        table_node = figure.find("tei:table", namespaces=ns)
        if table_node is None:
            print("  -> No <tei:table> inside.")
            continue

        label_node = figure.find("tei:label", namespaces=ns)
        number = normalize_text(" ".join(label_node.itertext())) if label_node is not None else ""

        figdesc_node = figure.find("tei:figDesc", namespaces=ns)
        title = normalize_text(" ".join(figdesc_node.itertext())) if figdesc_node is not None else ""

        rows = []
        for row in table_node.findall("tei:row", namespaces=ns):
            cells = [normalize_text(" ".join(cell.itertext())) for cell in row.findall("tei:cell", namespaces=ns)]
            rows.append(cells)

        full_text = f"{number} {title}".strip()
        tables.append({
            "number": number,
            "title": title,
            "rows": rows,
            "full_text": full_text if full_text else None
        })

    print(f"{len(tables)} tables found")
    return tables


def extract_grobid_figures_from_text(root):
    """
    Extrait uniquement les titres de figures détectés dans le texte OCR GROBID.
    Ne récupère que les phrases commençant par "GRAPHIQUE" ou "FIGURE".
    Ajoute un champ "type" et "full_text" sans récupérer le contenu de la figure.
    """
    ns = {"tei": "http://www.tei-c.org/ns/1.0"}
    figures = []

    for s in root.xpath(".//tei:s", namespaces=ns):
        raw_text = " ".join(s.itertext()).strip()
        text = normalize_text(raw_text)

        upper_text = text.upper()
        if upper_text.startswith("GRAPHIQUE") or upper_text.startswith("FIGURE"):
            words = text.split()
            if not words:
                continue

            first_word = words[0].upper()
            figure_type = "graphique" if first_word == "GRAPHIQUE" else "figure"
            number = words[1] if len(words) > 1 else ""
            title = " ".join(words[2:]) if len(words) > 2 else ""

            figures.append({
                "type": figure_type,
                "number": number,
                "title": title,
                "source": "",
                "full_text": text
            })

    return figures



import re

def guess_name_from_affiliation(text):
    """
    Essaie d'extraire un prénom et un nom depuis une chaîne d'affiliation brute.
    Hypothèse : le nom est au début de la chaîne (avant la première virgule).
    """
    if not text:
        return "", ""

    # Supprimer label type "**" ou autres caractères spéciaux
    text = re.sub(r'^\*+\s*', '', text)
    text = text.strip()

    # Prendre les mots avant la première virgule
    parts = text.split(",", 1)
    if parts:
        name_part = parts[0].strip()

        # Tenter de séparer en prénom / nom
        name_tokens = name_part.split()
        if len(name_tokens) >= 2:
            return name_tokens[0], " ".join(name_tokens[1:])
        else:
            return "", name_tokens[0]  # Si un seul mot, on suppose que c’est le nom

    return "", ""

def extract_grobid_author_dicts(root):
    ns = {"tei": "http://www.tei-c.org/ns/1.0"}
    authors_elements = root.xpath("//tei:sourceDesc//tei:author", namespaces=ns)

    authors = []

    for elem in authors_elements:
        persName = elem.find("tei:persName", namespaces=ns)
        affiliations = elem.findall("tei:affiliation", namespaces=ns)
        print (affiliations)
        email_elem = elem.find("tei:email", namespaces=ns)

        current_author = {
            "first_name": "",
            "last_name": "",
            "affiliation": "",
            "email": "",
            "website": "",
            "orcid": ""
        }

        # S’il y a un nom → on l’utilise
        if persName is not None:
            first_name = persName.find("tei:forename[@type='first']", namespaces=ns)
            last_name = persName.find("tei:surname", namespaces=ns)

            current_author["first_name"] = normalize_text(first_name.text) if first_name is not None else ""
            current_author["last_name"] = normalize_text(last_name.text) if last_name is not None else ""

        # S’il y a un email
        if email_elem is not None and email_elem.text:
            current_author["email"] = normalize_text(email_elem.text)

        # S’il y a une affiliation avec note
        affiliation_texts = []
        for aff in affiliations:
            note = aff.find("tei:note[@type='raw_affiliation']", namespaces=ns)
            if note is not None:
                # Supprimer le contenu des balises <label> dans la note
                note_text = " ".join(
                    normalize_text(t)
                    for t in note.itertext()
                    if not (t.strip().isdigit() and note.find("tei:label", namespaces=ns) is not None and t.strip() in note.find("tei:label", namespaces=ns).itertext())
                )
                if note_text:
                    affiliation_texts.append(note_text)

                    # Deviner nom si vide
                    if not current_author["first_name"] and not current_author["last_name"]:
                        guess_first, guess_last = guess_name_from_affiliation(note_text)
                        current_author["first_name"] = guess_first
                        current_author["last_name"] = guess_last

        current_author["affiliation"] = " ; ".join(affiliation_texts)

        # Ajouter l’auteur même si minimal (si au moins une info)
        if any(current_author.values()):
            authors.append(current_author)

    return authors





def parse_grobid_xml(root):
    resultats = {}

    for champ, xpath in chemins_grobid.items():
        if champ == "date":
            raw_dates = extract_from_path(root, chemins_grobid["date"], ns_grobid)
            resultats[champ] = [normalize_date(d) for d in raw_dates if d]

        elif champ == "editorial_team":
            resultats[champ] = []

        # elif champ == "author_affiliation":
        #     resultats[champ] = extract_grobid_author_affiliations_flat(root)

        elif champ == "erudit_id":
            doi = extract_from_path(root, chemins_grobid["id"], ns_grobid)
            if doi and isinstance(doi[0], str) and "/" in doi[0]:
                resultats[champ] = [doi[0].split("/")[-1]]
            else:
                resultats[champ] = []
        elif champ == "notes":
            resultats[champ] = extract_grobid_footnotes(root)

        elif champ == "bibliographies":
            biblio_dicts = extract_grobid_biblio_dicts(root)
            for b in biblio_dicts:
                raw = b.get("raw_reference", "")
                if isinstance(raw, list):
                    b["raw_reference"] = " ".join([normalize_text(r) for r in raw if isinstance(r, str)])
                elif isinstance(raw, str):
                    b["raw_reference"] = normalize_text(raw)
                else:
                    b["raw_reference"] = ""

            resultats["bibliographies"] = biblio_dicts
            continue



        elif xpath:
            resultats[champ] = extract_from_path(root, xpath, ns_grobid)
        else:
            resultats[champ] = []
        
        # Normaliser tous les textes extraits
        if isinstance(resultats[champ], list):
            resultats[champ] = [normalize_text(x) for x in resultats[champ] if isinstance(x, str)]
        elif isinstance(resultats[champ], str):
            resultats[champ] = normalize_text(resultats[champ])

    resultats["authors"] = extract_grobid_author_dicts(root)
    resultats["body"] = extract_section_titles(root)
    resultats["figures"] = extract_grobid_figures_from_text(root)
    resultats["tables"] = extract_grobid_tables(root)


    resultats["tool"] = "grobid"
    return resultats

#python3 transformers/main.py --id 1107141ar_2 --source grobid 
