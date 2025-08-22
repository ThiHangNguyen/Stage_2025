from utils.io import normalize_date, normalize_text, extract_from_path
from .road import chemins_grobid
import re

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


# def extract_grobid_tables(root):
#     ns = {"tei": "http://www.tei-c.org/ns/1.0"}
#     tables = []

#     for figure in root.findall(".//tei:figure", namespaces=ns):
#         print("Found <figure>")

#         table_node = figure.find("tei:table", namespaces=ns)
#         if table_node is None:
#             print("  -> No <tei:table> inside.")
#             continue

#         label_node = figure.find("tei:label", namespaces=ns)
#         number = normalize_text(" ".join(label_node.itertext())) if label_node is not None else ""

#         figdesc_node = figure.find("tei:figDesc", namespaces=ns)
#         title = normalize_text(" ".join(figdesc_node.itertext())) if figdesc_node is not None else ""

#         rows = []
#         for row in table_node.findall("tei:row", namespaces=ns):
#             cells = [normalize_text(" ".join(cell.itertext())) for cell in row.findall("tei:cell", namespaces=ns)]
#             rows.append(cells)

#         full_text = f"{number} {title}".strip()
#         tables.append({
#             "number": number,
#             "title": title,
#             "rows": rows,
#             "full_text": full_text if full_text else None
#         })

#     print(f"{len(tables)} tables found")
#     return tables
def extract_grobid_tables(root):
    NS = {"tei": "http://www.tei-c.org/ns/1.0"}
    tables = []

    def _itxt(n): return " ".join(n.itertext()) if n is not None else ""
    def _norm(s): return normalize_text(s) if s else ""

    figures_with_tables = 0

    # (A) tables sous figure
    for fig in root.xpath(".//tei:figure", namespaces=NS):
        table_elem = fig.find("tei:table", namespaces=NS)
        if table_elem is None:
            continue
        figures_with_tables += 1

        label = _norm(_itxt(fig.find("tei:label", namespaces=NS)))
        title = _norm(_itxt(fig.find("tei:figDesc", namespaces=NS))) or _norm(_itxt(table_elem.find("tei:head", namespaces=NS)))

        # content: concat de toutes les cellules
        all_text = []
        for row in table_elem.findall(".//tei:row", namespaces=NS):
            for cell in row.findall("tei:cell", namespaces=NS):
                t = _norm(_itxt(cell)).strip()
                if t:
                    all_text.append(t)
        content = _norm(" ".join(all_text))

        # note: notes + éventuels "Source" dans label/figDesc
        note_parts = []
        for n in fig.findall(".//tei:note", namespaces=NS):
            nt = _norm(_itxt(n))
            if nt: note_parts.append(nt)
        if ("source" in (label or "").lower()):
            note_parts.append(label)
        if ("source" in (title or "").lower()):
            note_parts.append(title)
        seen = set()
        note = " ".join(x for x in note_parts if not (x in seen or seen.add(x))).strip()

        tables.append({"number": label, "title": title, "content": content, "note": note})

    # (B) optionnel: tables hors figure (aucune “devinette”, toujours <tei:table>)
    for table_elem in root.xpath(".//tei:table[not(ancestor::tei:figure)]", namespaces=NS):
        head = _norm(_itxt(table_elem.find("tei:head", namespaces=NS)))
        all_text = []
        for row in table_elem.findall(".//tei:row", namespaces=NS):
            for cell in row.findall("tei:cell", namespaces=NS):
                t = _norm(_itxt(cell)).strip()
                if t:
                    all_text.append(t)
        content = _norm(" ".join(all_text))
        note_parts = []
        for n in table_elem.findall(".//tei:note", namespaces=NS):
            nt = _norm(_itxt(n))
            if nt: note_parts.append(nt)
        seen = set()
        note = " ".join(x for x in note_parts if not (x in seen or seen.add(x))).strip()
        tables.append({"number": "", "title": head, "content": content, "note": note})

    # petit log utile en dev
    print(f"[tables] figures_with_tables={figures_with_tables}, tables_total={len(tables)}")
    return tables

def extract_table_contents_grobid(root):
    """
    Retourne une liste[str], chaque élément = contenu d’un <tei:table>
    obtenu en fusionnant le texte de toutes les cellules (ordre lignes→cellules).
    Aucun fallback textuel: on ne prend que les vrais <tei:table>.
    """
    ns = globals().get("ns_grobid", {"tei": "http://www.tei-c.org/ns/1.0"})
    out = []

    def _itxt(node):
        return " ".join(node.itertext()) if node is not None else ""

    for table in root.findall(".//tei:table", namespaces=ns):
        all_cells = []
        for row in table.findall(".//tei:row", namespaces=ns):
            for cell in row.findall("tei:cell", namespaces=ns):
                t = normalize_text(_itxt(cell)).strip()
                if t:
                    all_cells.append(t)
        merged = normalize_text(" ".join(all_cells)) if all_cells else ""
        if merged:
            out.append(merged)

    return out

import re

def extract_grobid_figures_from_text(root):
    """
    Extrait les figures depuis <tei:figure> uniquement.
    Retourne une liste de dicts {number, title, source}.
    - number = préfixe + identifiant (ex. 'figure 1', 'graphique II'), principalement depuis <label>
    - title  = 1re phrase de <figDesc> (après nettoyage de 'Figure X ...')
    - source = uniquement notes de bas de page liées à la figure (inline <note> ou via <noteRef>/<ref>/<ptr> => <note xml:id>)
              AUCUN fallback 'Source:' dans le texte de la légende.
    """
    ns = {"tei": "http://www.tei-c.org/ns/1.0"}
    figures = []

    def N(s):
        try:
            return normalize_text(s) if s else ""
        except NameError:
            return " ".join(str(s).split()) if s else ""

    for fig in root.findall(".//tei:figure", namespaces=ns):
        # ---- number (prefix + id) ----
        num_word, num_id = "", ""

        # 1) depuis <label>
        label = fig.find("tei:label", namespaces=ns)
        if label is not None:
            label_text = N(" ".join(label.itertext())).strip()
            m = re.search(r'(fig(?:ure)?|graphiq(?:ue)?|graphique)\s*([0-9IVXLC]+)', label_text, flags=re.I)
            if m:
                num_word = m.group(1).lower()
                num_id   = m.group(2)
            else:
                # au moins essayer de récupérer un identifiant numérique/romain
                m2 = re.search(r'([0-9IVXLC]+)', label_text, flags=re.I)
                if m2:
                    num_word = "figure"
                    num_id   = m2.group(1)

        number = f"{(num_word or 'figure')} {num_id}".strip() if num_id else ""

        # ---- title depuis figDesc ----
        title = ""
        figdesc = fig.find("tei:figDesc", namespaces=ns)
        desc_text = N(" ".join(figdesc.itertext())) if figdesc is not None else ""

        # on nettoie 'Figure X'/'Graphique X' AU SEIN du titre (si id connu)
        desc_clean = desc_text
        if desc_clean and num_id:
            desc_clean = re.sub(
                rf'^(?:fig(?:ure)?|graphiq(?:ue)?|graphique)\s*{re.escape(num_id)}\s*[ .:\-–—]*',
                '', desc_clean, flags=re.I
            )

        # première phrase non vide comme titre
        if desc_clean:
            sentences = re.split(r'(?<=[.!?])\s+', desc_clean)
            if sentences:
                title = sentences[0].strip()

        # ---- source : uniquement notes/footnotes rattachées à la figure ----
        source = ""
        notes_texts = []

        # (1) Notes inline sous <figure> (on garde seulement les notes de bas de page)
        for note in fig.findall(".//tei:note", namespaces=ns):
            kind = f"{(note.get('type') or '').lower()} {(note.get('place') or '').lower()}".strip()
            if ("foot" in kind) or (note.get("type", "").lower() in {"foot", "footnote"}):
                t = N(" ".join(note.itertext())).strip()
                if t:
                    notes_texts.append(t)

        # (2) Notes référencées depuis la figure : <noteRef>, <ref type='foot'>, <ptr type='foot'>
        targets = set()

        for elt in fig.findall(".//tei:noteRef", namespaces=ns):
            tgt = (elt.get("target") or "").strip()
            if tgt.startswith("#"):
                targets.add(tgt[1:])

        for elt in fig.findall(".//tei:ref", namespaces=ns):
            if elt.get("type", "").lower() in {"foot", "footnote", "note", "fn"}:
                tgt = (elt.get("target") or "").strip()
                if tgt.startswith("#"):
                    targets.add(tgt[1:])

        for elt in fig.findall(".//tei:ptr", namespaces=ns):
            if elt.get("type", "").lower() in {"foot", "footnote", "note", "fn"}:
                tgt = (elt.get("target") or "").strip()
                if tgt.startswith("#"):
                    targets.add(tgt[1:])

        # (3) Résoudre les cibles -> texte des <note> correspondantes (dans tout le doc)
        if targets:
            XML_ID = "{http://www.w3.org/XML/1998/namespace}id"
            for n in root.findall(".//tei:note", namespaces=ns):
                nid = n.get(XML_ID) or n.get("xml:id")
                if nid and nid in targets:
                    kind = f"{(n.get('type') or '').lower()} {(n.get('place') or '').lower()}".strip()
                    if ("foot" in kind) or (n.get("type", "").lower() in {"foot", "footnote"}):
                        t = N(" ".join(n.itertext())).strip()
                        if t:
                            notes_texts.append(t)

        # (4) Déduplication + fusion (pas de fallback "Source:")
        seen, ordered = set(), []
        for t in notes_texts:
            if t and t not in seen:
                ordered.append(t)
                seen.add(t)

        source = " | ".join(ordered)

        if not (number or title or source):
            continue

        figures.append({
            "number": number,
            "title": title,
            "source": source
        })

    return figures


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
        #print (affiliations)
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
    resultats["section_titles"] = extract_section_titles(root)
    resultats["figures"] = extract_grobid_figures_from_text(root)
    resultats["tables"] = extract_grobid_tables(root)
    resultats["content_table"] = extract_table_contents_grobid(root)
    resultats["tool"] = "grobid"
    return resultats

#python3 transformers/main.py --id 1107141ar_2 --source grobid 
