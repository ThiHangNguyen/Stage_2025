# -*- coding: utf-8 -*-
"""
Extracteurs OCR/Markdown (FR/EN) pour titres, résumés, mots-clés, sections,
références, tableaux et figures.

⚠️ Invariant : parse_olmocr_markdown conserve sa signature et son comportement.
"""

import os
import re
from typing import List, Dict, Tuple, Optional

# Helpers externes
from utils.io import normalize_date, normalize_text  # normalize_date non utilisé ici mais conservé

# ------------------------------------------------------------------------------
# Constantes & motifs communs
# ------------------------------------------------------------------------------

# Espaces/tirets Unicode à normaliser
_UNICODE_SPACES = (
    "\u00A0"  # NBSP
    "\u202F"  # NNBSP
    "\u2009"  # thin space
    "\u2007"  # figure space
    "\u2002\u2003\u2004\u2005\u2006\u2008\u200A"  # en/em etc.
)

FIGURE_PREFIXES = (r"FIGURE", r"GRAPHIQUE")
TABLE_PREFIXES  = (r"TABLEAU", r"TABLE")

# ---------- Références / Bibliographie ----------

HEADER_RE = re.compile(
    r"(?mi)^\s*"
    r"(?:\d{1,2}[.)]\s*)?"                      # ex: "4." ou "IV)" optionnel
    r"(?:#{1,3}\s*)?(?:\*\*|__)?\s*"           # markdown/gras optionnel
    r"(Références?(?:\s+bibliographiques?)?"
    r"|Bibliographie(?:\s+sélective)?"
    r"|Sources?"
    r"|Travaux\s+cités?"
    r"|(?:Oe|Œ)uvres\s+citées?"
    r"|References?(?:\s+list)?"
    r"|Bibliograph(?:y|ies)(?:\s+selected)?"
    r"|Works\s+Cited"
    r"|Literature\s+Cited"
    r"|Selected\s+Bibliography"
    r"|Annexes?"
    r"|Appendix(?:es)?)"
    r"\s*(?:[:\-])?\s*(?:\*\*|__)?\s*$"
)

# en-tête fort pour délimiter une section
STRONG_HEADER_RE = re.compile(
    r"(?m)^(?:#{1,3}\s+.+$|(?:\*\*|__).+(?:\*\*|__)$|[A-ZÉÈÀÂÎÔÛÄËÏÖÜ][A-ZÉÈÀÂÎÔÛÄËÏÖÜ \-]{3,}$)"
)

# puces / numérotations
IS_BULLET = re.compile(r"^\s*(?:[-*•]|[0-9]{1,3}[.)])\s+")

# ---------- Mots-clés ----------

# Séparateurs entre mots-clés (le tiret ne sépare que s’il est suivi d’un espace)
_KEYWORD_SEP = re.compile(
    r"\s*(?:;|,|/|\||•|·|(?:[-–—](?=\s))|\s+(?:and|et)\s+)\s*",
    flags=re.IGNORECASE
)

# Toutes les étiquettes possibles FR/EN
KEYWORD_LABELS = (
    r"keywords?",
    r"key\s*words?",
    r"(?:mots?|mot)\s*[- ]?\s*(?:cl[eé]s?|clefs?)",
    r"descripteurs?"
)

# Étiquette + contenu sur la même ligne (gras Markdown toléré)
LABEL_RE = re.compile(
    rf"""^\s*
        (?:(?:\*\*|__)\s*)?
        (?:{ "|".join(KEYWORD_LABELS) })
        (?:\s*(?::|-))?
        (?:\s*(?:\*\*|__))?
        \s*(?::|-)?\s*
        (.+)$
    """,
    flags=re.IGNORECASE | re.UNICODE | re.VERBOSE
)

# ---------- Tableaux ----------

_TABLE_SEP_LINE  = re.compile(r"^\s*[|+:\-=\s\.]+\s*$")  # lignes de séparation
_TABLE_PIPEY     = re.compile(r"\|.*\|")                 # ≥ 2 pipes
_TABLE_GRID_HINT = re.compile(r"^\s*(?:\S+\s{2,}\S+).*$")# colonnes via ≥2 espaces

# ---------- Figures ----------

FIG_INLINE = re.compile(
    r"""
    (?:\*\*|__)?\s*
    (?P<label>Figure|Graphique|Graph|Chart)
    \s*(?P<num>[0-9IVXLC]+)
    \s*[\.\-–:]?\s*
    (?P<title>.+?)
    (?:\*\*|__)?\s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)

FIG_LINE = re.compile(
    r"^\s*(?P<label>Figure|Graphique|Graph|Chart)\s*(?P<num>[0-9IVXLC]+)\s*[\.\-–:]?\s*(?P<title>.+?)\s*$",
    re.IGNORECASE | re.MULTILINE,
)

SRC_RE = re.compile(r"^\s*(Source|Sources)\s*[:\-]\s*(.+)$", re.IGNORECASE)

# ---------- Légendes/notes de tableaux ----------

CAPTION_RE = re.compile(
    r"^\s*(Tableau|TABLEAU|Table|TABLE)\s*"
    r"(?P<num>[0-9IVXLC]+)?\s*[.:–-]?\s*(?P<title>.+?)\s*$",
    re.IGNORECASE
)
CAPTION_LONE_RE = re.compile(
    r"^\s*(Tableau|TABLEAU|Table|TABLE)\s*(?P<num>[0-9IVXLC]+)\s*$",
    re.IGNORECASE
)
NOTE_RE = re.compile(r"^\s*(Note|Notes?|Source|Sources)\s*[:\-]\s*(.+)$", re.IGNORECASE)

# ------------------------------------------------------------------------------
# Normalisation & utilitaires génériques
# ------------------------------------------------------------------------------

def _read_markdown(md_or_path: str) -> str:
    """Lit un fichier markdown si le chemin existe, sinon retourne la chaîne telle quelle."""
    if os.path.exists(md_or_path):
        with open(md_or_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    return md_or_path


def _clean_space(s: str) -> str:
    """Trim + compaction + normalisation (accents/cas via normalize_text)."""
    return normalize_text(re.sub(r"[ \t]+", " ", s.strip()))


def _pre_norm(text: str) -> str:
    """Normalise sauts de ligne, espaces/tirets Unicode et compacte les espaces."""
    t = text.replace("\r\n", "\n").replace("\r", "\n")
    for ch in _UNICODE_SPACES:
        t = t.replace(ch, " ")
    t = (t
         .replace("\u00B7", " ")   # ·
         .replace("\u2013", "-")   # –
         .replace("\u2014", "-"))  # —
    t = re.sub(r"[ \t]{2,}", " ", t)
    return t


def _norm_text(text: str) -> str:
    """Version légère pour scans (tab/figures)."""
    return (text.replace("\r\n", "\n").replace("\r", "\n")
                .replace("\u00A0"," ").replace("\u202F"," ").replace("\u2009"," ")
                .replace("\u2013","-").replace("\u2014","-"))


def _norm_lines(text: str) -> List[str]:
    """Normalise légèrement puis découpe en lignes."""
    return _norm_text(text).split("\n")


def _extract_between(text: str, pattern: str) -> str:
    """Capture non-gourmande avec flags standards, sinon chaîne vide."""
    m = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL | re.UNICODE)
    return (m.group(1) if m else "").strip()


# ------------------------------------------------------------------------------
# Extracteurs
# ------------------------------------------------------------------------------

def extract_title(text: str) -> str:
    """
    Extrait uniquement le titre d'un document OCR/Markdown.
    Hypothèse : le titre est la première ligne non vide.
    """
    for l in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if l.strip():
            return normalize_text(l)
    return ""


def extract_abstracts(text: str) -> Tuple[str, str]:
    """
    Renvoie (abstract_principal_FR_si_dispo_sinon_EN, abstract_EN).
    Gère 'RÉSUMÉ – ...', espaces insécables et tirets typographiques.
    """
    t = _pre_norm(text)

    STOP = r"(?:\n\s*\*\*|\n\s*#+\s|^\s*[A-ZÉÀ][A-ZÉÀa-z\- ]{2,40}\s*$|\n\s*(?:Abstract|ABSTRACT)\b|\n\*\s|\n{2,}|\Z)"
    fr_pat = rf"(?:^|\n)\s*(?:Résumé|RÉSUMÉ|RESUME)\s*(?::|-)?\s*(.+?)(?={STOP})"
    en_pat = rf"(?:^|\n)\s*(?:Article\s+abstract|Abstract)\s*(?::|-)?\s*(.+?)(?={STOP})"

    abs_fr = _extract_between(t, fr_pat)
    abs_en = _extract_between(t, en_pat)
    principal = abs_fr if abs_fr else abs_en
    return (principal, abs_en)


def extract_section_titles(text: str) -> List[str]:
    """Collecte des titres de sections via # Markdown, **gras**, ou majuscules typographiques."""
    titles: set[str] = set()

    # En-têtes Markdown
    for m in re.finditer(r"^\s{0,3}#{1,6}\s+(.+)$", text, re.MULTILINE):
        titles.add(_clean_space(m.group(1)))

    # Titres gras sur une ligne
    for m in re.finditer(r"^\s*\*\*(.+?)\*\*\s*$", text, re.MULTILINE):
        t = _clean_space(m.group(1))
        if len(t) >= 3:
            titles.add(t)

    # Blocs “SECTION : …” en capitales
    for m in re.finditer(r"^\s*([A-ZÉÈÀÂÎÔÛÄËÏÖÜ][A-ZÉÈÀÂÎÔÛÄËÏÖÜ \-]{3,})\s*$", text, re.MULTILINE):
        t = _clean_space(m.group(1).title())
        if 3 <= len(t) <= 120 and not re.search(r"^(Figure|Tableau|Table|Keywords|Mots)", t, re.I):
            titles.add(t)

    return [t for t in titles if t]


# -------------------- Références --------------------

def _block_to_entries(block: str) -> List[str]:
    """
    Transforme un bloc multi-lignes en entrées (séparation par ligne vide/puce/numéro).
    Concatène les lignes de continuation avec un espace.
    """
    lines = [l.rstrip() for l in block.split("\n")]
    entries, cur = [], []

    def flush():
        if cur:
            txt = re.sub(r"\s+", " ", " ".join(cur)).strip(" ;,")
            if txt:
                entries.append(txt)
        cur.clear()

    for ln in lines:
        stripped = ln.strip()
        if not stripped:
            flush()
            continue
        if IS_BULLET.match(stripped):
            flush()
            stripped = IS_BULLET.sub("", stripped, count=1).strip()
        cur.append(stripped)

    flush()

    if len(entries) == 0 and block.strip():
        entries = [re.sub(r"\s+", " ", block.strip())]

    return entries


def extract_bibliographies(text: str) -> List[Dict[str, str]]:
    """
    Capture le texte qui suit 'Références/Bibliographie' jusqu'au prochain en-tête fort,
    puis découpe en entrées.
    """
    t = _pre_norm(text)
    m = HEADER_RE.search(t)
    if not m:
        return []

    start = m.end()
    next_hdr = STRONG_HEADER_RE.search(t, pos=start)
    block = t[start:] if not next_hdr else t[start:next_hdr.start()]
    entries = _block_to_entries(block)
    return [{"raw_reference": e} for e in entries if e]


# -------------------- Mots-clés --------------------

def _kw_pre_norm(text: str) -> str:
    t = text.replace("\r\n", "\n").replace("\r", "\n")
    for ch in _UNICODE_SPACES:
        t = t.replace(ch, " ")
    return (t.replace("\u2013", "-").replace("\u2014", "-").replace("\u00B7", " "))


def extract_keywords(text: str) -> List[str]:
    """
    Détecte TOUS les blocs FR/EN (y compris en gras Markdown) et fusionne en une seule liste nettoyée.
    """
    t = _kw_pre_norm(text)
    lines = t.split("\n")

    all_parts: List[str] = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        m = LABEL_RE.match(line)
        if not m:
            i += 1
            continue

        buf = [m.group(1).strip()] if m.group(1) else []

        j = i + 1
        while j < len(lines):
            nxt = lines[j].strip()
            if (not nxt or
                nxt.startswith("#") or
                nxt.startswith("**") or
                re.match(r"^[A-ZÉÀ][A-ZÉÀa-z\- ]{2,40}\s*$", nxt) or
                LABEL_RE.match(nxt)):
                break
            buf.append(nxt)
            j += 1

        raw = " ".join(buf)
        parts = [p.strip(" .,:;·•|/-–—\t") for p in _KEYWORD_SEP.split(raw) if p.strip()]
        all_parts.extend(parts)

        i = j

    seen = set()
    cleaned: List[str] = []
    for kw in all_parts:
        k = re.sub(r"\s+", " ", kw).strip()
        if len(k) <= 1:
            continue
        key = k.lower()
        if key not in seen:
            seen.add(key)
            cleaned.append(k)

    return cleaned


# -------------------- Contenu des tableaux (fusionné) --------------------

def _looks_table_line(s: str) -> bool:
    ss = s.rstrip()
    if not ss:
        return False
    return bool(_TABLE_PIPEY.search(ss) or _TABLE_SEP_LINE.match(ss) or _TABLE_GRID_HINT.match(ss))


def _clean_table_block_to_string(block: str) -> str:
    """
    Nettoie un bloc de lignes de tableau et le fusionne en une seule chaîne.
    - supprime les séparateurs (|----|, +----+, etc.)
    - remplace '|' et '+' par des espaces
    - compacte les espaces
    """
    lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
    kept: List[str] = []
    for ln in lines:
        if _TABLE_SEP_LINE.match(ln):   # ignorer les lignes de séparateurs purs
            continue
        ln = ln.replace("|", " ").replace("+", " ")
        ln = re.sub(r"\s+", " ", ln).strip()
        if ln:
            kept.append(ln)
    fused = " ".join(kept)
    return normalize_text(fused)


def extract_table_contents(text: str) -> List[str]:
    """
    Détecte des blocs de tableaux (ASCII/Markdown) et renvoie une liste de contenus,
    chacun **fusionné** en une seule chaîne.
    """
    lines = _norm_lines(text)
    contents: List[str] = []

    cur: List[str] = []
    in_table = False

    def flush():
        nonlocal cur, in_table
        if cur:
            tbl = "\n".join(cur).strip("\n")
            s = _clean_table_block_to_string(tbl)
            if s:
                contents.append(s)
        cur = []
        in_table = False

    for ln in lines:
        if _looks_table_line(ln):
            cur.append(ln.rstrip())
            in_table = True
        else:
            if in_table:
                flush()
    if in_table:
        flush()

    # déduplication légère
    seen = set()
    uniq: List[str] = []
    for s in contents:
        key = s.lower()
        if key not in seen:
            seen.add(key)
            uniq.append(s)
    return uniq


# -------------------- Tableaux (avec légende/note) --------------------

def _scan_caption_around(lines: List[str], start: int, end: int) -> Dict[str, str]:
    """Recherche d'une légende autour du bloc table."""
    number, title = "", ""

    # au-dessus
    for k in range(max(0, start - 3), start)[::-1]:
        line = lines[k].strip()
        if not line:
            continue
        m = CAPTION_RE.match(line)
        if m:
            number = (m.group("num") or "").strip()
            title = normalize_text(m.group("title"))
            return {"number": number, "title": title}
        m2 = CAPTION_LONE_RE.match(line)
        if m2 and k + 1 < len(lines) and lines[k + 1].strip():
            number = (m2.group("num") or "").strip()
            title = normalize_text(lines[k + 1].strip())
            return {"number": number, "title": title}

    # en dessous
    for k in range(end, min(len(lines), end + 2)):
        line = lines[k].strip()
        if not line:
            continue
        m = CAPTION_RE.match(line)
        if m:
            number = (m.group("num") or "").strip()
            title = normalize_text(m.group("title"))
            return {"number": number, "title": title}
        m2 = CAPTION_LONE_RE.match(line)
        if m2 and k + 1 < len(lines) and lines[k + 1].strip():
            number = (m2.group("num") or "").strip()
            title = normalize_text(lines[k + 1].strip())
            return {"number": number, "title": title}

    return {"number": "", "title": ""}


def _scan_note_below(lines: List[str], end: int, max_look: int = 6) -> str:
    """Recherche des 'Note/Source:' dans les lignes qui suivent un tableau."""
    note_parts: List[str] = []
    for k in range(end, min(len(lines), end + max_look)):
        line = lines[k].strip()
        if not line:
            if note_parts:
                break
            else:
                continue
        m = NOTE_RE.match(line)
        if m:
            note_parts.append(normalize_text(m.group(2)))
            continue
        if re.match(r"^(Tableau|Table|Figure|Graphique)\b", line, re.IGNORECASE):
            break
    return " ".join(note_parts)


def extract_tables_with_context(text: str) -> List[Dict[str, str]]:
    """
    Détecte des tableaux et renvoie dicts :
    {number, title, content, note}
    """
    t = _norm_text(text)
    lines = t.split("\n")
    out: List[Dict[str, str]] = []

    i = 0
    while i < len(lines):
        if _looks_table_line(lines[i]):
            start = i
            buf = [lines[i]]
            i += 1
            while i < len(lines) and _looks_table_line(lines[i]):
                buf.append(lines[i])
                i += 1
            end = i

            block = "\n".join(buf)
            content = _clean_table_block_to_string(block)
            if not content:
                continue

            cap = _scan_caption_around(lines, start, end)
            note = _scan_note_below(lines, end)
            out.append({
                "number": cap.get("number", ""),
                "title":  cap.get("title", ""),
                "content": content,
                "note": note
            })
        else:
            i += 1
    return out


# -------------------- Figures --------------------

def extract_figures(text: str) -> List[Dict[str, str]]:
    """
    Renvoie des dicts {"number": "<label> <num>", "title": "...", "source": "..."}.
    - label: figure/graphique/graph/chart (en minuscules)
    - num: chiffre ou romain
    - title: texte jusqu'à fin de ligne (ou la ligne suivante si vide)
    - source: 'Source:' dans les 4 lignes suivantes
    """
    t = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = t.split("\n")
    out: List[Dict[str, str]] = []

    for i, raw in enumerate(lines):
        line = raw.strip()
        if not line:
            continue

        m = FIG_INLINE.search(line) or FIG_LINE.match(line)
        if not m:
            continue

        label = (m.group("label") or "").strip().lower()
        num   = (m.group("num") or "").strip()
        number_field = f"{label} {num}".strip()

        title = normalize_text((m.group("title") or "").strip())
        title = re.sub(r":\s*$", "", title)
        if not title and i + 1 < len(lines) and lines[i + 1].strip():
            title = normalize_text(lines[i + 1].strip())

        source = ""
        for k in range(i + 1, min(len(lines), i + 5)):
            ms = SRC_RE.match(lines[k].strip())
            if ms:
                source = normalize_text(ms.group(2))
                break

        out.append({"number": number_field, "title": title, "source": source})

    # dédup légère
    seen, uniq = set(), []
    for f in out:
        key = (f["number"], f["title"])
        if key not in seen:
            seen.add(key)
            uniq.append(f)
    return uniq


# ------------------------------------------------------------------------------
# Point d’entrée
# ------------------------------------------------------------------------------

def parse_olmocr_markdown(md_or_path: str) -> Dict:
    """
    Point d’entrée : lit le texte et regroupe tous les extracteurs.
    """
    text = _read_markdown(md_or_path)
    title = extract_title(text)
    abs_fr_or_main, abs_en = extract_abstracts(text)

    data = {
        "title": title,
        "abstract": abs_fr_or_main or abs_en,
        "keywords": extract_keywords(text),
        "section_titles": extract_section_titles(text),
        "bibliographies": extract_bibliographies(text),
        "content_table": extract_table_contents(text),
        "figures": extract_figures(text),
        "tables": extract_tables_with_context(text),
        "tool": "olmOCR",
    }
    return data
