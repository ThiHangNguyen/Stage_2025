def extract_title_from_nougat_md(filepath):
    extracted_lines = []
    found_title_start = False

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()

            if not stripped:
                continue

            # Début du titre : première ligne qui commence par "# "
            if not found_title_start:
                if stripped.startswith("# "):
                    extracted_lines.append(stripped[2:].strip())  # Enlève "# "
                    found_title_start = True
                continue

            # Si on est dans le titre mais qu'on atteint une ligne qui commence par une majuscule → stop
            first_word = stripped.split()[0] if stripped.split() else ""
            if first_word and first_word[0].isupper():
                break

            extracted_lines.append(stripped)

    return " ".join(extracted_lines)

import re
import re

def extract_abstract_from_nougat_md(filepath):
    abstract_lines = []
    in_abstract = False
    abstract_pattern = re.compile(r"^#{2,6}\s+(abstract|résumé|resume)\s*$", re.IGNORECASE)
    heading_pattern = re.compile(r"^#{1,6}\s+")  # pour détecter le prochain titre

    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        stripped = line.strip()

        if not in_abstract:
            if abstract_pattern.match(stripped):
                in_abstract = True
                continue  # on passe à la ligne suivante
        else:
            if heading_pattern.match(stripped):
                break  # fin du bloc abstract
            if stripped:  # ignorer lignes vides
                abstract_lines.append(stripped)

    return " ".join(abstract_lines)






def extract_references_from_nougat_md(filepath):
    references = []
    in_references = False
    is_bibliography_format = False  # Pour savoir si on est dans un bloc "Bibliography"

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()

            # Début de la section "References"
            if not in_references and re.match(r"^#{2,6}.*\breferences\b", stripped, re.IGNORECASE):
                in_references = True
                is_bibliography_format = False  # C'est le format avec [année]
                continue

            # Début de la section "Bibliography"
            if not in_references and re.match(r"^#{2,6}.*\bbibliography\b", stripped, re.IGNORECASE):
                in_references = True
                is_bibliography_format = True  # Format paragraphe classique
                continue

            if in_references:
                # Fin de section si un nouveau bloc markdown commence
                if re.match(r"^#{1,6}\s", stripped):
                    break

                if not stripped:
                    continue  # Ignorer lignes vides

                if is_bibliography_format:
                    # Bibliography : ajouter ligne entière
                    references.append(stripped)
                else:
                    # References : matcher "* [1990] Texte"
                    match = re.match(r"\*\s*\[\d{4}\]\s+(.*)", stripped)
                    if match:
                        references.append(match.group(1).strip())

    return references

import re
import re

def clean_reference_line(text):
    # 1. Numéro : N\({}^{\circ}\) → N°
    text = re.sub(r'N\\\(\{\}\^\{\\circ\}\\\)', 'N°', text)
    
    # 2. Ordinal (ex: 5\({}^{\circ}\)) → 5°
    text = re.sub(r'(\d+)\\\(\{\}\^\{\\circ\}\\\)', r'\1°', text)

    # 3. Guillemets français LaTeX << >> → “ ”
    text = text.replace('<<', '“').replace('>>', '”')

    # 4. Texte en italique `_texte_` → texte
    text = re.sub(r'_(.*?)_', r'\1', text)

    # 5. Suppression des caractères LaTeX inutiles restants (facultatif)
    text = text.replace('\\\\', ' ')         # double anti-slash LaTeX
    text = text.replace('\\', '')            # simple anti-slash résiduel

    # 6. Nettoyage des espaces doubles ou plus
    text = re.sub(r'\s{2,}', ' ', text)

    return text.strip()


# def clean_reference_line(line):
#     return line.replace("N\\({}^{\\circ}\\)", "No").replace("\\({}^{\\circ}\\)", "No")

def extract_references_from_nougat_md(filepath):
    references = []
    in_references = False
    is_bibliography_format = False

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()

            # --- Détection du début de section de références ---
            if not in_references:
                # Cas 1 : titres markdown comme ## References ou ## Bibliography
                if re.match(r"^#{1,6}\s*(\d+(\.\d+)*\s+)?(references?|références?|bibliograph\w*|biblio\w*)", stripped, re.IGNORECASE):
                    in_references = True
                    is_bibliography_format = "biblio" in stripped.lower()
                    continue

                # Cas 2 : mot seul (ex: BIBIBIBIOGRAPHIE)
                if re.fullmatch(r"(references?|.*biographie\w*)", stripped, re.IGNORECASE):
                    in_references = True
                    is_bibliography_format = "biblio" in stripped.lower()
                    continue

            # --- Traitement des lignes de référence ---
            if in_references:
                # Fin de section si nouveau header
                if re.match(r"^#{1,6}\s", stripped):
                    break
                if not stripped:
                    continue

                cleaned = clean_reference_line(stripped)

                if is_bibliography_format:
                    # Nettoyage du * si présent
                    if cleaned.startswith("*"):
                        cleaned = cleaned.lstrip("*").strip()
                    references.append(cleaned)
                else:
                    # Cas [année]
                    match = re.match(r"\*\s*\[\d{4}\]\s+(.*)", cleaned)
                    if match:
                        references.append(match.group(1).strip())
                    else:
                        # Cas juste * Texte
                        match2 = re.match(r"\*\s+(.*)", cleaned)
                        if match2:
                            references.append(match2.group(1).strip())

    return references





def extract_body_section_titles(filepath):
    section_titles = []
    
    #excluded_keywords = ["abstract", "résumé", "resume", "references", "bibliography", "bibliographie", "bibliographies", "annexe"]
    excluded_keywords = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            match = re.match(r"^(#{2,6})\s+(.*)", stripped)  # niveaux ## à ######
            if match:
                _, title = match.groups()
                title_clean = title.strip()
                title_lower = title_clean.lower()

                # Exclure si le titre contient un mot-clé interdit
                if any(exclu in title_lower for exclu in excluded_keywords):
                    continue

                section_titles.append(title_clean)

    return section_titles


import re

def clean_latex_expression(expr):
    # Supprimer les parenthèses LaTeX \(...\)
    expr = re.sub(r"\\\(|\\\)|\$", "", expr)

    # Convertir I_{1} → I1, X_{abc} → Xabc
    expr = re.sub(r"_\{([^}]+)\}", r"\1", expr)
    expr = re.sub(r"_(\w)", r"\1", expr)

    # Supprimer autres balises LaTeX inutiles
    expr = re.sub(r"\\text\{([^}]+)\}", r"\1", expr)
    expr = re.sub(r"\\mathrm\{([^}]+)\}", r"\1", expr)
    expr = re.sub(r"\\[a-zA-Z]+\s*", "", expr)

    return expr.strip()



def clean_latex_text(text):
    if not text or len(text) > 1000 or text.count("#") > 30:
        return None  # Bruit probable

    # Supprimer les maths : \( \), \[ \], $ $
    text = re.sub(r"\\\((.*?)\\\)", r"\1", text)
    text = re.sub(r"\\\[(.*?)\\\]", r"\1", text)
    text = re.sub(r"\$(.*?)\$", r"\1", text)

    # Remplacer \multicolumn{n}{format}{contenu} par juste le contenu
    text = re.sub(r"\\multicolumn\{\d+\}\{[^\}]*\}\{([^\}]*)\}", r"\1", text)


    # Supprimer les commandes \command{...}
    text = re.sub(r"\\[a-zA-Z]+\*?\{([^}]*)\}", r"\1", text)

    # Extraire le contenu des multicolumns et remplacer par le contenu réel
    text = re.sub(r"\\multicolumn\{\d+\}\{[lcr|]+\}\{([^}]*)\}", r"\1", text)

    # Supprimer les commandes simples (sans arguments)
    text = re.sub(r"\\[a-zA-Z]+\*?", "", text)

    # Caractères spéciaux LaTeX
    text = text.replace(r"\&", "&").replace(r"\%", "%")
    text = text.replace(r"\_", "_").replace(r"\$", "$")
    text = text.replace(r"\\", " ")

    # Supprimer les définitions de colonnes LaTeX : |p{...}|, |c|, etc.
    text = re.sub(r"\|?(p|c|l|r)\{[^}]+\}\|?", "", text)

    # Supprimer les balises Markdown accidentelles (** ou *)
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)

    # Supprimer les accolades
    text = text.replace("{", "").replace("}", "")

    # Supprimer les barres ou caractères répétés
    text = re.sub(r"[\\/^]{3,}", "", text)

    # Nettoyage final
    cleaned = " ".join(text.strip().split())

    if not cleaned or len(cleaned) < 2:
        return None
    return cleaned

import re
import re

def clean_latex_text(text):
    if not text or len(text) > 1000 or text.count("#") > 30:
        return None  # Probablement du bruit ou une cellule vide trop grande

    # 1. Supprimer les expressions mathématiques LaTeX
    text = re.sub(r"\\\((.*?)\\\)", r"\1", text)
    text = re.sub(r"\\\[(.*?)\\\]", r"\1", text)
    text = re.sub(r"\$(.*?)\$", r"\1", text)

    # 2. Supprimer les multicolumns
    text = re.sub(r"\\multicolumn\{\d+\}\{[^\}]*\}\{([^\}]*)\}", r"\1", text)

    # 3. Supprimer les commandes LaTeX avec argument : \command{...}
    text = re.sub(r"\\[a-zA-Z]+\*?\{([^}]*)\}", r"\1", text)

    # 4. Supprimer les commandes simples sans argument : \command
    text = re.sub(r"\\[a-zA-Z]+\*?", "", text)

    # 5. Nettoyer les caractères spéciaux échappés
    text = text.replace(r"\&", "&")
    text = text.replace(r"\%", "%")
    text = text.replace(r"\_", "_")
    text = text.replace(r"\$", "$")
    text = text.replace(r"\#", "#")  # Peut être remplacé ou supprimé selon le cas

    # 6. Supprimer les définitions de colonnes LaTeX : |c|, |p{...}|, etc.
    text = re.sub(r"\|?(p|c|l|r)\{[^}]+\}\|?", "", text)

    # 7. Supprimer les doubles backslashes \\ ou similaires
    text = re.sub(r"(\\\\|\\)", " ", text)

    # 8. Nettoyage Markdown (**...**) et autres
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)

    # 9. Supprimer les accolades restantes
    text = text.replace("{", "").replace("}", "")

    # 10. Supprimer les mots contenant des # suspects (optionnel mais utile)
    text = re.sub(r"\S*#\S*", "", text)

    # 11. Suppression de caractères spéciaux répétés ou parasites
    text = re.sub(r"[\\/^]{3,}", "", text)

    text = re.sub(r"\[(MISSING_PAGE|NOTE|FOOTNOTE|OCR_ERROR)[^\]]*\]", "", text)

    # 12. Nettoyage final
    cleaned = " ".join(text.strip().split())

    if not cleaned or len(cleaned) < 2:
        return None
    return cleaned



def extract_notes_around_tabular(latex: str) -> list[str]:
    """
    Cherche les notes directement après les environnements tabular
    comme "Note:", "Source:", "ND:" etc.
    """
    note_lines = []
    pattern = re.compile(
        r'(\\end\{tabular\*?\})(.*?)(?=\\begin|\Z)',  # ce qu'il y a après un \end{tabular}
        flags=re.DOTALL
    )
    for match in pattern.finditer(latex):
        after = match.group(2).strip()
        # Check first line after \end{tabular}
        first_line = after.split('\n')[0].strip()
        if re.match(r'^(Note|Source|ND)\s*:', first_line, re.IGNORECASE):
            note_lines.append(first_line)
    return note_lines

def extract_tables_from_nougat_latex(filepath):
    tables = []

    with open(filepath, encoding="utf-8") as f:
        md_text = f.read()

    # Trouver les blocs \begin{tabular}...\end{tabular}
    tabular_blocks = list(re.finditer(
        r"(\\begin\{tabular\}\{.*?\}.*?\\end\{tabular\})",
        md_text,
        flags=re.DOTALL
    ))

    # Trouver les titres : Table X: Titre
    titles = list(re.finditer(
        r"Table\s+(\d+)\s*:\s*(.*?)(?=\n|\\n)",
        md_text
    ))
    title_dict = {match.start(): (match.group(1), match.group(2).strip()) for match in titles}

    # Trouver les notes : lignes après un tableau commençant par "Note:" ou "Source:"
    note_candidates = list(re.finditer(
        r"(Note|Source)\s*:?\s*(.+?)(?=\n|\\n)",
        md_text,
        flags=re.IGNORECASE
    ))
    note_dict = {match.start(): match.group(0).strip() for match in note_candidates}

    for block in tabular_blocks:
        block_start = block.start()
        block_full_text = block.group(1)

        content_match = re.search(r"\\begin\{tabular\}\{.*?\}(.*?)\\end\{tabular\}", block_full_text, flags=re.DOTALL)
        block_text = content_match.group(1).strip() if content_match else ""
        raw_rows = re.split(r'\\\\', block_text)

        lines = []
        for row in raw_rows:
            row = row.strip()
            if not row:
                continue
            row = row.replace(r"\hline", "").strip()
            columns = [clean_latex_text(col.strip()) for col in row.split('&')]
            columns = [col for col in columns if col is not None]
            if columns:
                lines.append(" ".join(columns))

        if not lines:
            continue  # ignorer tableaux vides

        # Associer le titre le plus proche après le bloc
        closest_title = None
        for pos, (num, title) in sorted(title_dict.items()):
            if pos > block_start:
                closest_title = (num, title)
                break

        number = f"{closest_title[0]}" if closest_title else "tableau ?"
        title = clean_latex_text(closest_title[1]) if closest_title else ""

        # Associer une note (proche après le tableau)
        closest_note = ""
        for pos, note in sorted(note_dict.items()):
            if block.end() < pos < block.end() + 500:  # note dans les ~10 lignes suivantes
                closest_note = clean_latex_text(note)
                break

        tables.append({
            "number": number,
            "title": title,
            "content": " ".join(lines),
            "note": closest_note or ""
        })

    return tables


def parse_nougat_md(filepath):
    resultats = {}

    # Métadonnées principales
    resultats["tool"] = "nougat"
    resultats["title"] = extract_title_from_nougat_md(filepath)
    resultats["abstract"] = extract_abstract_from_nougat_md(filepath)

    # Sections, figures, tableaux
    resultats["section_titles"] = extract_body_section_titles(filepath)
    resultats["tables"] = extract_tables_from_nougat_latex(filepath)
    resultats["figures"] = []  # tu pourras ajouter une fonction extract_nougat_figures_md(filepath) plus tard

    # Notes de bas de page
    resultats["notes"] = []  # pareil, tu peux ajouter une fonction si besoin

    # Références / bibliographie
    references = extract_references_from_nougat_md(filepath)
    resultats["bibliographies"] = [
        {"raw_reference": ref.strip()} for ref in references if isinstance(ref, str)
    ]

    return resultats
