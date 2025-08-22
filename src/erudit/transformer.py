from utils.io import normalize_text, extract_from_path
from .road import chemins_erudit
from typing import List


ns_erudit = {"er": "http://www.erudit.org/xsd/article",
             "xlink": "http://www.w3.org/1999/xlink"}


def extract_biblio_text(node, ns) -> str:
    """
    Extrait tout le texte d'un <refbiblio>, sauf le contenu de <idpublic>.
    """
    parts = []

    # Prend tous les enfants sauf les balises <idpublic>
    for elem in node.xpath("node()[not(self::er:idpublic)]", namespaces=ns):
        if isinstance(elem, str):  # texte brut
            parts.append(elem)
        elif hasattr(elem, "itertext"):
            parts.append("".join(elem.itertext()))
        elif elem.tail:
            parts.append(elem.tail)

    texte = "".join(parts)
    return normalize_text(texte)


def extract_erudit_author_fields(root):
    """
    Extrait les champs associés aux auteurs d’un article Érudit, y compris :
    - prénom, nom
    - email, ORCID, site web
    - affiliations (concaténées)
    
    Retourne un dictionnaire avec une liste de valeurs pour chaque champ.
    """

    ns = {"er": "http://www.erudit.org/xsd/article"}

    result = {
        "author_first_name": [],
        "author_last_name": [],
        "author_email": [],
        "author_orcid": [],
        "author_website": [],
        "author_affiliation": [],
    }

    auteurs = root.xpath("//er:grauteur/er:auteur", namespaces=ns)

    for auteur in auteurs:
        first_name = auteur.xpath("er:nompers/er:prenom/text()", namespaces=ns)
        last_name_raw = auteur.xpath("er:nompers/er:nomfamille//text()", namespaces=ns)
        last_name_text = "".join(last_name_raw).strip()  # ← ce nom est correct

        email = auteur.xpath("er:courriel/er:liensimple/text()", namespaces=ns)
        orcid = auteur.xpath("er:idno[@type='orcid']/text()", namespaces=ns)
        website = auteur.xpath("er:liensimple[@type='web']/text()", namespaces=ns)
        affiliations = auteur.xpath("er:affiliation/er:alinea/text()", namespaces=ns)
        aff_clean = [a.strip() for a in affiliations if a.strip()]

        if not aff_clean:
            alt_aff = auteur.xpath("er:affiliation/er:alinea//text()", namespaces=ns)
            aff_clean = [a.strip() for a in alt_aff if a.strip()]

        result["author_first_name"].append(first_name[0] if first_name else "")
        result["author_last_name"].append(last_name_text if last_name_text else "")
        result["author_email"].append(email[0] if email else "")
        result["author_orcid"].append(orcid[0] if orcid else "")
        result["author_website"].append(website[0] if website else "")
        result["author_affiliation"].append(" ".join(aff_clean) if aff_clean else "")

    # Optionnel : transformer les listes d'affiliations en chaînes pour export CSV
    for i in range(len(result["author_affiliation"])):
        aff_list = result["author_affiliation"][i]
        if isinstance(aff_list, list):
            result["author_affiliation"][i] = " ".join(aff_list)

    return result


def extract_erudit_editorial_team(root):
    """
    Extrait les informations de l’équipe éditoriale depuis un document Érudit,
    y compris :
    - Directeurs (nom, sexe, fonction)
    - Rédacteurs en chef (nom, type)
    - Éditeurs institutionnels (organisation)
    
    Retourne une liste de dictionnaires plats, avec un champ 'category'.
    """

    ns = {"er": "http://www.erudit.org/xsd/article"}
    team_flat = []

    # Directeurs
    for d in root.xpath(".//er:directeur", namespaces=ns):
        sexe = d.attrib.get("sexe", "")
        prenom = d.findtext("er:nompers/er:prenom", default="", namespaces=ns)
        autreprenom = d.findtext("er:nompers/er:autreprenom", default="", namespaces=ns)
        nomfamille = d.findtext("er:nompers/er:nomfamille", default="", namespaces=ns)
        fonction = d.findtext("er:fonction", default="", namespaces=ns)

        team_flat.append({
            "first_name": prenom,
            "middle_name": autreprenom,
            "last_name": nomfamille,
            "gender": sexe,
            "role": fonction,
            "category": "director"
        })

    # Rédacteurs en chef
    for r in root.xpath(".//er:redacteurchef", namespaces=ns):
        typerc = r.attrib.get("typerc", "")
        prenom = r.findtext("er:nompers/er:prenom", default="", namespaces=ns)
        autreprenom = r.findtext("er:nompers/er:autreprenom", default="", namespaces=ns)
        nomfamille = r.findtext("er:nompers/er:nomfamille", default="", namespaces=ns)

        team_flat.append({
            "first_name": prenom,
            "middle_name": autreprenom,
            "last_name": nomfamille,
            "type": typerc,
            "category": "editor_in_chief"
        })

    # Éditeurs (organismes)
    # for e in root.xpath(".//er:editeur", namespaces=ns):
    #     org_name = e.findtext("er:nomorg", default="", namespaces=ns)
    #     if org_name:
    #         team_flat.append({
    #             "organization": org_name,
    #             "category": "editor"
    #         })

    return team_flat


def extract_source(element, ns):
    """
    Extrait tout le texte contenu dans <source>, y compris les balises imbriquées.
    Retourne une chaîne propre et normalisée.
    """
    source_elem = element.find("er:source", namespaces=ns)
    if source_elem is not None:
        # Récupère tout le texte récursivement, y compris dans les <marquage>, <liensimple>, etc.
        full_text = "".join(source_elem.itertext())
        return normalize_text(full_text)
    return ""

def extract_figures(root):
    """
    Extrait toutes les figures (simples et groupées) avec :
    - number (ex. "Figure 5")
    - title (texte de <titre>)
    - source (texte de <source>)
    - full_text (tout le texte brut de la figure normalisé)
    """
    ns = {"er": "http://www.erudit.org/xsd/article"}
    figures = []

    # Cas 1 : groupes de figures <grfigure>
    for grfig in root.findall(".//er:grfigure", namespaces=ns):
        group_number = grfig.findtext("er:no", default="", namespaces=ns)
        group_title = grfig.findtext("er:legende/er:titre", default="", namespaces=ns)
        group_source = extract_source(grfig, ns)
        group_text = normalize_text(" ".join(grfig.itertext()))

        figures.append({
            "number": normalize_text(group_number),
            "title": normalize_text(group_title),
            "source": group_source,
            "full_text": group_text
        })

    # Cas 2 : figures simples hors <grfigure>
    for fig in root.findall(".//er:figure", namespaces=ns):
        # Éviter les sous-figures dans les <grfigure>
        parent = fig.getparent()
        if parent is not None and parent.tag.endswith("grfigure"):
            continue

        fig_number = fig.findtext("er:no", default="", namespaces=ns)
        fig_title = fig.findtext("er:legende/er:titre", default="", namespaces=ns)
        fig_source = extract_source(fig, ns)
        fig_text = normalize_text(" ".join(fig.itertext()))

        figures.append({
            "number": normalize_text(fig_number),
            "title": normalize_text(fig_title),
            "source": fig_source,
            "full_text": fig_text
        })

    return figures


def extract_tabtexte_content(table_node, ns):
    lignes = []

    # En-tête
    for ligne in table_node.findall(".//er:tabentete/er:tabligne", namespaces=ns):
        cellules = ligne.findall(".//er:alinea", namespaces=ns)
        lignes.append("\t".join([c.text.strip() for c in cellules if c.text]))

    # Lignes de données
    for ligne in table_node.findall(".//er:tabgrligne/er:tabligne", namespaces=ns):
        cellules = ligne.findall(".//er:alinea", namespaces=ns)
        lignes.append("\t".join([c.text.strip() for c in cellules if c.text]))

    return "\n".join(lignes) if lignes else None



def extract_table_notes_and_source(table_elem, ns):
    """
    Concatène toutes les notes (alinea + notetabl + source) en une seule chaîne.
    Inclut aussi les éventuelles sources situées dans une balise <source>.
    """
    notes = []

    # Texte dans <source>
    source_node = table_elem.find("er:source", namespaces=ns)
    if source_node is not None:
        texte = normalize_text("".join(source_node.itertext()))
        if texte:
            notes.append(texte)

    # alinéas dans <legende>
    for alinea in table_elem.findall(".//er:legende/er:alinea", namespaces=ns):
        texte = normalize_text("".join(alinea.itertext()))
        if texte:
            notes.append(texte)

    # notes dans <notetabl>
    for note in table_elem.findall(".//er:notetabl", namespaces=ns):
        for alinea in note.findall("er:alinea", namespaces=ns):
            texte = normalize_text("".join(alinea.itertext()))
            if texte:
                notes.append(texte)

    return " ".join(notes) if notes else None



def extract_tables(root):
    """
    Extrait les tableaux simples et ceux contenus dans des groupes <grtableau>.
    Retourne :
    - number : numéro du tableau (ex. "Tableau 1" ou "a)")
    - title : titre textuel complet
    - content : contenu brut de <objetmedia><texte>
    - note : notes éventuelles (alinea, notetabl)
    - parent : None ou "numéro - titre" du groupe
    - full_text : concaténation du contenu textuel
    """
    ns = {"er": "http://www.erudit.org/xsd/article"}
    tables = []

    # Cas 1 : groupes de tableaux
    for grtab in root.findall(".//er:grtableau", namespaces=ns):
        parent_number = grtab.findtext("er:no", default="", namespaces=ns)
        parent_title_node = grtab.find("er:legende/er:titre", namespaces=ns)
        parent_title = normalize_text("".join(parent_title_node.itertext()) if parent_title_node is not None else "")
        parent_label = f"{normalize_text(parent_number)} - {parent_title}" if parent_title else normalize_text(parent_number)

        for table in grtab.findall("er:tableau", namespaces=ns):
            number = normalize_text(table.findtext("er:no", default="", namespaces=ns))
            titre_node = table.find("er:legende/er:titre", namespaces=ns)
            title = normalize_text("".join(titre_node.itertext()) if titre_node is not None else "")
            content = extract_tabtexte_content(table, ns)
            note = extract_table_notes_and_source(table, ns)

           #full_text = " ".join([str(x).strip() for x in [number, title, note, content] if x]).strip()

            tables.append({
                "number": number,
                "title": title,
                "content": content,
                "note": note,
                #"parent": parent_label,
                #"full_text": full_text
            })

    # Cas 2 : tableaux simples (pas dans un grtableau)
    for table in root.findall(".//er:tableau", namespaces=ns):
        if table.getparent().tag.endswith("grtableau"):
            continue  # déjà traité

        number = normalize_text(table.findtext("er:no", default="", namespaces=ns))
        titre_node = table.find("er:legende/er:titre", namespaces=ns)
        title = normalize_text("".join(titre_node.itertext()) if titre_node is not None else "")
        content = extract_tabtexte_content(table, ns)

        note = extract_table_notes_and_source(table, ns)

        #full_text = " ".join([str(x).strip() for x in [number, title, note, content] if x]).strip()

        tables.append({
            "number": number,
            "title": title,
            "content": content,
            "note": note,
            #"parent": None,
            #"full_text": full_text
        })

    return tables


def extract_section_titles_erudit(root):
    """
    Retourne une liste plate des titres de toutes les sections (section1 à section5) dans le corps,
    sous forme de chaînes de caractères.
    """

    titles = []

    def collect_titles(sec):
        titre_node = sec.find("er:titre", namespaces=ns_erudit)
        titre = normalize_text("".join(titre_node.itertext())) if titre_node is not None else ""
        if titre:
            titles.append(titre)

        # Chercher récursivement les sous-sections (section2 à section5)
        for level in range(2, 6):
            for sub in sec.findall(f"er:section{level}", namespaces=ns_erudit):
                collect_titles(sub)

    for sec1 in root.xpath("er:corps/er:section1", namespaces=ns_erudit):
        collect_titles(sec1)

    return titles


def extract_erudit_keywords_by_lang(root):

    # Si root est un ElementTree, on récupère son élément racine
    if hasattr(root, "getroot"):
        root = root.getroot()

    lang = root.get("{http://www.w3.org/XML/1998/namespace}lang") or root.get("lang")

    if not lang:
        return []

    xpath_expr = f".//er:grmotcle[@lang='{lang}']/er:motcle"
    return [normalize_text(elem.text) for elem in root.xpath(xpath_expr, namespaces=ns_erudit) if elem.text]

from typing import Dict, List


def extract_erudit_keywords_all_langs(root) -> Dict[str, List[str]]:
    """
    Récupère tous les <motcle> groupés par langue, en capturant le texte imbriqué
    (ex. <marquage typemarq="italique">Poa annua</marquage>).
    Retourne un dict {lang: [keywords...]} avec nettoyage + déduplication.
    Utilise le ns global `ns_erudit`.
    """
    # Si root est un ElementTree → prendre l'élément racine
    if hasattr(root, "getroot"):
        root = root.getroot()

    out: Dict[str, List[str]] = {}

    # On prend tous les groupes, même sans @lang (fallback "und")
    groups = root.xpath(".//er:grmotcle", namespaces=ns_erudit)

    for g in groups:
        lang = (g.get("{http://www.w3.org/XML/1998/namespace}lang")
                or g.get("lang")
                or "und").strip()

        # Collecter tous les <motcle> du groupe
        kws_raw: List[str] = []
        for mc in g.xpath("./er:motcle", namespaces=ns_erudit):
            tokens = [t.strip() for t in mc.itertext() if t and t.strip()]
            txt = " ".join(tokens)

            if txt:
                txt = normalize_text(txt)
                txt = re.sub(r"\s+", " ", txt).strip()
                txt = re.sub(r"^[\s\-\.,;:•|/]+|[\s\-\.,;:•|/]+$", "", txt)
                if txt:
                    kws_raw.append(txt)

        # Déduplication *dans* la langue tout en préservant l'ordre
        seen = set()
        dedup: List[str] = []
        for kw in kws_raw:
            key = kw.lower()
            if key not in seen:
                seen.add(key)
                dedup.append(kw)

        if dedup:
            out[lang] = dedup

    return out

def extract_table_contents_erudit(root) -> List[str]:
    """
    Retourne une liste de contenus de tableaux (chaîne TSV par tableau),
    basée sur `extract_tabtexte_content`. Ne renvoie QUE le contenu,
    sans numéro, titre ni note.
    """
    contents: List[str] = []

    # 1) Tableaux dans des groupes <grtableau>
    for table in root.findall(".//er:grtableau/er:tableau", namespaces=ns_erudit):
        tsv = extract_tabtexte_content(table, ns_erudit)
        if tsv:
            tsv = tsv.strip()
            if tsv:
                contents.append(tsv)

    # 2) Tableaux simples (hors groupe) — éviter les doublons
    for table in root.findall(".//er:tableau", namespaces=ns_erudit):
        parent = table.getparent()
        if parent is not None and parent.tag.endswith("grtableau"):
            continue  # déjà traité
        tsv = extract_tabtexte_content(table, ns_erudit)
        if tsv:
            tsv = tsv.strip()
            if tsv:
                contents.append(tsv)

    # Déduplication légère (insensible à la casse)
    seen = set()
    uniq: List[str] = []
    for s in contents:
        key = s.lower()
        if key not in seen:
            seen.add(key)
            uniq.append(s)

    return uniq
import re
def extract_erudit_keywords_all_langs(root) -> Dict[str, List[str]]:
    """
    Récupère tous les <motcle> groupés par langue, en capturant le texte imbriqué
    (ex. <marquage typemarq="italique">Poa annua</marquage>).
    Retourne un dict {lang: [keywords...]} avec nettoyage + déduplication.
    Utilise le ns global `ns_erudit`.
    """
    # Si root est un ElementTree → prendre l'élément racine
    if hasattr(root, "getroot"):
        root = root.getroot()

    out: Dict[str, List[str]] = {}

    # On prend tous les groupes, même sans @lang (fallback "und")
    groups = root.xpath(".//er:grmotcle", namespaces=ns_erudit)

    for g in groups:
        lang = (g.get("{http://www.w3.org/XML/1998/namespace}lang")
                or g.get("lang")
                or "und").strip()

        # Collecter tous les <motcle> du groupe
        kws_raw: List[str] = []
        for mc in g.xpath("./er:motcle", namespaces=ns_erudit):
            # Récupérer tout le texte, y compris dans <marquage>, <liensimple>, ...
            # On join sur espace pour éviter les mots collés autour des balises inline.
            tokens = [t.strip() for t in mc.itertext() if t and t.strip()]
            txt = " ".join(tokens)

            # Nettoyage léger: normalisation + trim de ponctuation parasite en bord
            if txt:
                txt = normalize_text(txt)
                txt = re.sub(r"\s+", " ", txt).strip()
                txt = re.sub(r"^[\s\-\.,;:•|/]+|[\s\-\.,;:•|/]+$", "", txt)
                if txt:
                    kws_raw.append(txt)

        # Déduplication *dans* la langue tout en préservant l'ordre
        seen = set()
        dedup: List[str] = []
        for kw in kws_raw:
            key = kw.lower()
            if key not in seen:
                seen.add(key)
                dedup.append(kw)

        if dedup:
            out[lang] = dedup

    return out


def parse_erudit_xml(root):

    """
    Fonction principale de parsing pour un fichier XML Érudit.
    """
    resultats = {}

    for champ, xpath in chemins_erudit.items():
        if champ == "editorial_team":
            resultats[champ] = extract_erudit_editorial_team(root)
            continue

        elif champ == "keywords":
            # Nouveau: tous les mots-clés, toutes langues
            kw_by_lang = extract_erudit_keywords_all_langs(root)
            resultats["keywords_by_lang"] = kw_by_lang  # nouveau champ structuré

            # Compat: liste à plat dédupliquée (toutes langues confondues)
            flat_seen = set()
            flat_list = []
            for lang, arr in kw_by_lang.items():
                for kw in arr:
                    key = kw.lower()
                    if key not in flat_seen:
                        flat_seen.add(key)
                        flat_list.append(kw)
            resultats["keywords"] = flat_list
            continue


        elif champ == "bibliographies":
            resultats[champ] = []
            for node in root.xpath(xpath, namespaces=ns_erudit):
                texte = extract_biblio_text(node, ns_erudit)
                if texte:
                    resultats[champ].append({
                        "raw_reference": normalize_text(texte)
                    })
            continue


        elif champ == "notes":
            resultats[champ] = []
            for note in root.xpath(".//er:grnote/er:note", namespaces=ns_erudit):
                no_node = note.find("er:no", namespaces=ns_erudit)
                alinea_node = note.find("er:alinea", namespaces=ns_erudit)

                numero = normalize_text(no_node.text) if no_node is not None and no_node.text else ""
                contenu = normalize_text("".join(alinea_node.itertext())) if alinea_node is not None else ""

                if numero or contenu:
                    texte_note = f"[{numero}] \"{contenu}\"" if numero else contenu
                    resultats[champ].append(texte_note)

        elif xpath:
            resultats[champ] = extract_from_path(root, xpath, ns_erudit)
        else:
            resultats[champ] = []
            
    # Extraction du body structuré (sections)

    author_fields = extract_erudit_author_fields(root)

    # Recombine les champs en liste de dicts
    nb_authors = max(len(v) for v in author_fields.values())
    authors = []

    for i in range(nb_authors):
        author = {
            "first_name": normalize_text(author_fields["author_first_name"][i]) if i < len(author_fields["author_first_name"]) else "",
            "last_name": normalize_text(author_fields["author_last_name"][i]) if i < len(author_fields["author_last_name"]) else "",
            "affiliation": normalize_text(author_fields["author_affiliation"][i]) if i < len(author_fields["author_affiliation"]) else "",
            "email": normalize_text(author_fields["author_email"][i]) if i < len(author_fields["author_email"]) else "",
            "website": normalize_text(author_fields["author_website"][i]) if i < len(author_fields["author_website"]) else "",
            "orcid": normalize_text(author_fields["author_orcid"][i]) if i < len(author_fields["author_orcid"]) else "",
        }
        authors.append(author)

    resultats["authors"] = authors
    resultats["section_titles"] = extract_section_titles_erudit(root)
    resultats["figures"] = extract_figures(root)
    resultats["tables"] = extract_tables(root)
    resultats["content_table"] = extract_table_contents_erudit(root)

    return resultats


#python3 transformers/main.py --id 1107141ar_2 --tool erudit