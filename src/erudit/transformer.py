from utils.io import normalize_text, extract_from_path
from .road import chemins_erudit
import re

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

"""
def extract_erudit_editorial_team(root):
    ns = {"er": "http://www.erudit.org/xsd/article"}
    team = {"directors": [], "editors_in_chief": [], "editors": []}

    # Directeurs
    for d in root.xpath(".//er:directeur", namespaces=ns):
        sexe = d.attrib.get("sexe", "")
        prenom = d.findtext("er:nompers/er:prenom", default="", namespaces=ns)
        autreprenom = d.findtext("er:nompers/er:autreprenom", default="", namespaces=ns)
        nomfamille = d.findtext("er:nompers/er:nomfamille", default="", namespaces=ns)
        fonction = d.findtext("er:fonction", default="", namespaces=ns)

        team["directors"].append({
            "first_name": prenom,
            "middle_name": autreprenom,
            "last_name": nomfamille,
            "gender": sexe,
            "role": fonction
        })

    # Rédacteurs en chef
    for r in root.xpath(".//er:redacteurchef", namespaces=ns):
        typerc = r.attrib.get("typerc", "")
        prenom = r.findtext("er:nompers/er:prenom", default="", namespaces=ns)
        autreprenom = r.findtext("er:nompers/er:autreprenom", default="", namespaces=ns)
        nomfamille = r.findtext("er:nompers/er:nomfamille", default="", namespaces=ns)

        team["editors_in_chief"].append({
            "first_name": prenom,
            "middle_name": autreprenom,
            "last_name": nomfamille,
            "type": typerc
        })

    # Éditeurs (organismes)
    for e in root.xpath(".//er:editeur", namespaces=ns):
        org_name = e.findtext("er:nomorg", default="", namespaces=ns)
        if org_name:
            team["editors"].append({"organization": org_name})

    return team

"""
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
    #print(f"[DEBUG] Nombre d'auteurs trouvés : {len(auteurs)}")

    for auteur in auteurs:
        first_name = auteur.xpath("er:nompers/er:prenom/text()", namespaces=ns)
        last_name = auteur.xpath("er:nompers/er:nomfamille/text()", namespaces=ns)
        email = auteur.xpath("er:courriel/er:liensimple/text()", namespaces=ns)
        orcid = auteur.xpath("er:idno[@type='orcid']/text()", namespaces=ns)
        website = auteur.xpath("er:liensimple[@type='web']/text()", namespaces=ns)
        affiliations = auteur.xpath("er:affiliation/er:alinea/text()", namespaces=ns)

        aff_clean = [a.strip() for a in affiliations if a.strip()]
        #print(f"[DEBUG] Affiliations auteur : {aff_clean}")

        result["author_first_name"].append(first_name[0] if first_name else "")
        result["author_last_name"].append(last_name[0] if last_name else "")
        result["author_email"].append(email[0] if email else "")
        result["author_orcid"].append(orcid[0] if orcid else "")
        result["author_website"].append(website[0] if website else "")
        result["author_affiliation"].append(aff_clean if aff_clean else [""])

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
    for e in root.xpath(".//er:editeur", namespaces=ns):
        org_name = e.findtext("er:nomorg", default="", namespaces=ns)
        if org_name:
            team_flat.append({
                "organization": org_name,
                "category": "editor"
            })

    return team_flat

def extract_erudit_body_sections(root):

    """
    Extrait les sections du corps de texte de l’article (section1, section2...).
    Pour chaque section :
    - titre
    - paragraphes
    - formules (équations avec image)
    - objets médias (images, vidéos)
    - sous-sections récursives
    
    Retourne une liste structurée reflétant la hiérarchie du texte.
    """

    def parse_section(sec):
        titre_node = sec.find("er:titre", namespaces=ns_erudit)
        titre = normalize_text("".join(titre_node.itertext())) if titre_node is not None else ""

        # Paragraphes
        paras = []
        for para in sec.findall(".//er:para", namespaces=ns_erudit):
            alinea_node = para.find("er:alinea", namespaces=ns_erudit)
            texte = normalize_text("".join(alinea_node.itertext())) if alinea_node is not None else ""
            if texte:
                paras.append(texte)

        """# Figures
        figures_data = []
        for fig in sec.findall(".//er:figure", namespaces=ns_erudit):
            fig_id = fig.attrib.get("id", "")
            fig_label = fig.findtext("er:no", default="", namespaces=ns_erudit)
            alinea_node = fig.find(".//er:legende/er:alinea", namespaces=ns_erudit)
            fig_caption = "".join(alinea_node.itertext()) if alinea_node is not None else ""
            fig_source = fig.findtext("er:source", default="", namespaces=ns_erudit)
            figures_data.append({
                "id": fig_id,
                "label": normalize_text(fig_label),
                "caption": normalize_text(fig_caption),
                "source": normalize_text(fig_source),
            })
        """
        formulas = []
        for eq in sec.xpath(".//er:equation", namespaces=ns_erudit):
            label_node = eq.find("er:no", namespaces=ns_erudit)
            image_node = eq.find("er:objetmedia/er:image", namespaces=ns_erudit)
            if image_node is not None:
                label = label_node.text.strip() if label_node is not None and label_node.text else ""
                href = image_node.attrib.get("{http://www.w3.org/1999/xlink}href", "")
                formulas.append({
                    "label": normalize_text(label),
                    "image_href": href
                })


        # Médias
        media_objects = []
        for obj in sec.xpath(".//er:objetmedia", namespaces=ns_erudit):
            img = obj.find("er:image", namespaces=ns_erudit)
            if img is not None:
                href = img.attrib.get("{http://www.w3.org/1999/xlink}href", "")
                media_type = img.attrib.get("typeimage", "")
                title = img.attrib.get("{http://www.w3.org/1999/xlink}title", "")
                if href:
                    media_objects.append({
                        "type": media_type,
                        "href": href,
                        "title": title
                    })

        # Sous-sections récursives (section2, section3, etc.)
        subsections = []
        for level in range(2, 6):  # tu peux ajuster la profondeur
            for sub in sec.findall(f"er:section{level}", namespaces=ns_erudit):
                subsections.append(parse_section(sub))

        return {
            "title": titre,
            "paragraphs": paras,
            "formulas": formulas,
            "media_objects": media_objects,
            "subsections": subsections,
        }

    # Lancer l’analyse depuis section1
    return [parse_section(sec) for sec in root.xpath("er:corps/er:section1", namespaces=ns_erudit)]


def extract_erudit_global_figures(root):

    """
    Extrait toutes les figures globales dans le document :
    - Groupes de figures (<grfigure>) avec sous-figures, label, caption, legends
    - Figures simples (<figure>) en dehors des groupes
    
    Chaque figure retourne :
    - label (ex. "Figure 1")
    - caption (titre général)
    - legends (listes d’annotations ou descriptions)
    - subfigures (sous-figures avec label et caption)
    """

    ns = {"er": "http://www.erudit.org/xsd/article"}
    figures = []

    # Cas 1 : groupes de figures (grfigure)
    for grfig in root.findall(".//er:grfigure", namespaces=ns):
        group_label = grfig.findtext("er:no", default="", namespaces=ns)
        titre = grfig.findtext("er:legende/er:titre", default="", namespaces=ns)
        # Légendes de l'ensemble du groupe
        alineas = grfig.findall("er:legende/er:alinea", namespaces=ns)
        legends = []
        for alinea in alineas:
            texte = "".join(alinea.itertext()).strip()
            if texte:
                legends.append(normalize_text(texte))

        # Sous-figures
        subfigures = []
        for subfig in grfig.findall(".//er:figure", namespaces=ns):
            sub_label = subfig.findtext("er:no", default="", namespaces=ns)
            sub_titre = subfig.findtext("er:legende/er:titre", default="", namespaces=ns)

            subfigures.append({
                "label": normalize_text(sub_label),
                "caption": normalize_text(sub_titre),
            })

        figures.append({
            "label": normalize_text(group_label),
            "caption": normalize_text(titre),
            "legends": legends,
            "subfigures": subfigures,
        })

    # Cas 2 : figures simples hors des groupes
    for fig in root.findall(".//er:figure", namespaces=ns):
        if fig.getparent().tag.endswith("grfigure"):
            continue

        fig_label = fig.findtext("er:no", default="", namespaces=ns)
        titre = fig.findtext("er:legende/er:titre", default="", namespaces=ns)

        alineas = fig.findall("er:legende/er:alinea", namespaces=ns)
        legends = []
        for alinea in alineas:
            for media in alinea.findall("er:objetmedia", namespaces=ns):
                if media.tail:
                    texte = normalize_text(media.tail)
                    if texte:
                        legends.append(texte)
        figures.append({
            "label": normalize_text(fig_label),
            "caption": normalize_text(titre),
            "legends": legends,
            "subfigures": []
        })

    return figures



def extract_erudit_global_tables(root):

    """
    Extrait toutes les tables (<tableau>) du document.
    Pour chaque tableau :
    - label (numéro)
    - caption (titre)
    - source (chemin de l’image s’il y en a une)
    - lignes de contenu (texte principal + note)
    
    Retourne une liste de dictionnaires.
    """


    ns = {"er": "http://www.erudit.org/xsd/article"}

    tables = []
    for tab in root.findall(".//er:tableau", namespaces=ns):
        no = tab.findtext("er:no", default="", namespaces=ns)
        titre = tab.findtext("er:legende/er:titre", default="", namespaces=ns)
        image_node = tab.find(".//er:image", namespaces=ns)
        texte = tab.findtext(".//er:texte", default="", namespaces=ns)
        note = tab.findtext(".//er:notetabl", default="", namespaces=ns)
        image_href = image_node.get("{http://www.w3.org/1999/xlink}href", "") if image_node is not None else ""

        tables.append({
            "label": normalize_text(no),
            "caption": normalize_text(titre),
            "source": normalize_text(image_href),
            "rows": [[normalize_text(texte), normalize_text(note)]]
        })

    return tables



def parse_erudit_xml(root):

    """
    Fonction principale de parsing pour un fichier XML Érudit.
    """
    resultats = {}

    for champ, xpath in chemins_erudit.items():
        if champ == "editorial_team":
            resultats[champ] = extract_erudit_editorial_team(root)
            #print(resultats[champ])
            continue
        
        elif champ.startswith("author_"):
            author_fields = extract_erudit_author_fields(root)
            for key, values in author_fields.items():
                resultats[key] = values
            #resultats["authors"] = author_fields
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
            print("A REVOIR")
            print(champ)
            resultats[champ] = []
            
    # Extraction du body structuré (sections)
    resultats["body_sections"] = extract_erudit_body_sections(root)
    resultats["figures"] = extract_erudit_global_figures(root)
    resultats["tables"] = extract_erudit_global_tables(root)
    return resultats


#python3 transformers/main.py --id 1107141ar_2 --tool erudit