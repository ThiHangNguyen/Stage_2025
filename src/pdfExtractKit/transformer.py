from pathlib import Path
import json
import re

def _ensure_pages(obj):
    """
    Garantit que l'entrée (obj) est une liste de pages JSON.
    - Si c'est un chemin → charge le fichier JSON.
    - Si c'est un dict → cherche une clé candidate (pages, data, document, result).
    - Si déjà une liste → la retourne telle quelle.
    - Sinon → encapsule dans une liste.
    """
    
    if isinstance(obj, (str, Path)):
        with open(obj, "r", encoding="utf-8") as f:
            obj = json.load(f)
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict):
        for key in ("pages", "data", "document", "result"):
            if key in obj and isinstance(obj[key], list):
                return obj[key]
    return [obj]

def _split_figure_number(caption_text: str):
    """
    Try to split a leading 'Figure/FIG./Fig.' number from the caption.
    Returns (number, title). If no match, number="" and title=caption_text.
    """
    m = re.match(r'\s*(?:fig(?:ure)?\.?)\s*([A-Za-z]?\d[\w\.\-]*)\s*[:\-–—\.]?\s*(.*)',
                 caption_text, flags=re.IGNORECASE | re.DOTALL)
    if m:
        num = m.group(1) or ""
        title = m.group(2) or ""
        return num, title
    return "", caption_text

def parse_pdfek_json(pages_or_path, look_window=3):
    """
    Output:
      - titles_section: list[str]
      - tables:  list[{number:"", title, content, note}]   # (inchangé)
      - figures: list[{number, title, source}]
      - content_table: list[str]  # liste des `content` des tables retenues
    Rules:
      - No normalization of text content.
      - Ignore blocks with label 'figure' or 'image' as anchors (they’re visual content).
      - Create a figure when a caption block is found; attach sources found in a small
        window before/after the caption.
    """
    pages = _ensure_pages(pages_or_path)

    titles_section = []
    tables, figures = [], []
    content_table = []  # <--- nouveau

    TITLE_LABS = {"title"}

    TABLE_LABS  = {"table"}
    TABLE_CAPS  = {"table_caption", "table title", "table_caption_title", "table_caption_text"}
    TABLE_FOOTS = {"table_footnote", "table_note", "table footnote", "table_foot_note"}

    FIGURE_CAPS = {"figure_caption", "figure caption", "caption", "figure_caption_text"}
    FIGURE_SRCS = {"figure_source", "image_source", "credit", "figure_credit", "source", "figure_footnote"}
    FIGURE_VISUAL = {"figure", "image"}  # explicitly ignored as anchors

    for p_idx, page in enumerate(pages, start=1):
        pno = page.get("page") or p_idx
        blocks = page.get("blocks") or page.get("items") or []
        n = len(blocks)
        i = 0

        while i < n:
            b = blocks[i] or {}
            lab = (b.get("label", "") or "").strip().lower()
            txt = b.get("text", "") or ""

            # --- Titles of sections ---
            if lab in TITLE_LABS:
                titles_section.append(txt if txt is not None else "")

            # --- TABLES ---
            if lab in TABLE_CAPS and txt:
                pass
            if lab in TABLE_FOOTS and txt:
                pass

            if lab in TABLE_LABS:
                content = txt

                # collect caption/note blocks just BEFORE this table (within a small window)
                tab_caps_before, tab_notes_before = [], []
                k0 = max(0, i - look_window)
                for kk in range(k0, i):
                    b2 = blocks[kk] or {}
                    lab2 = (b2.get("label", "") or "").strip().lower()
                    txt2 = b2.get("text", "") or ""
                    if lab2 in TABLE_CAPS and txt2:
                        tab_caps_before.append(txt2)
                    elif lab2 in TABLE_FOOTS and txt2:
                        tab_notes_before.append(txt2)

                # lookahead AFTER the table for more caption/footnote blocks
                tab_caps_after, tab_notes_after = [], []
                j = i + 1
                while j < min(i + 1 + look_window, n):
                    b2 = blocks[j] or {}
                    lab2 = (b2.get("label", "") or "").strip().lower()
                    txt2 = b2.get("text", "") or ""
                    if lab2 in TABLE_CAPS and txt2:
                        tab_caps_after.append(txt2)
                    elif lab2 in TABLE_FOOTS and txt2:
                        tab_notes_after.append(txt2)
                    else:
                        break
                    j += 1

                tables.append({
                    "number": "",
                    "title": " ".join(tab_caps_before + tab_caps_after),
                    "content": content,
                    "note": " ".join(tab_notes_before + tab_notes_after),
                })
                content_table.append(content)  # <--- alimente la liste parallèle
                i += 1
                continue

            # --- FIGURES (no visual anchor; caption triggers a figure) ---
            if lab in FIGURE_CAPS and txt:
                # collect consecutive caption blocks
                caption_parts = [txt]
                j = i + 1
                while j < n:
                    b2 = blocks[j] or {}
                    lab2 = (b2.get("label", "") or "").strip().lower()
                    txt2 = b2.get("text", "") or ""
                    if lab2 in FIGURE_CAPS and txt2:
                        caption_parts.append(txt2)
                        j += 1
                    else:
                        break

                caption_text = " ".join(caption_parts)

                # sources before
                src_before = []
                k0 = max(0, i - look_window)
                for kk in range(k0, i):
                    b2 = blocks[kk] or {}
                    lab2 = (b2.get("label", "") or "").strip().lower()
                    txt2 = b2.get("text", "") or ""
                    if lab2 in FIGURE_SRCS and txt2:
                        src_before.append(txt2)

                # sources after
                src_after = []
                k1 = j
                k_end = min(j + look_window, n)
                while k1 < k_end:
                    b2 = blocks[k1] or {}
                    lab2 = (b2.get("label", "") or "").strip().lower()
                    txt2 = b2.get("text", "") or ""
                    if lab2 in FIGURE_SRCS and txt2:
                        src_after.append(txt2)
                        k1 += 1
                    else:
                        break

                number, title = _split_figure_number(caption_text)
                source = " ".join(src_before + src_after)

                figures.append({
                    "number": number,
                    "title": title,
                    "source": source,
                })

                i = j
                continue

            # explicitly ignore visual figure/image blocks
            if lab in FIGURE_VISUAL:
                i += 1
                continue

            i += 1

    return {
        "section_titles": titles_section,
        "tables": tables,
        "figures": figures,
        "content_table": content_table,   
        "tool": "pdf-extract-kit",
    }
