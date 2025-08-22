import csv

def parse_csv_content_table(csv_path, keep_min_cells: int = 1):
    """
    Construit content_table = [table_1_str, table_2_str, ...] à partir d'un CSV:
    - Séparation stricte par couple (page, idtable) = (col0, col1).
    - Ignore la première ligne (header du fichier).
    - Retire 'page' et 'idtable' du contenu (on ne garde que les colonnes 2..n).
    - Supprime les cellules vides à droite de chaque ligne.
    - Ignore les lignes entièrement vides.
    - Ne conserve un tableau que s'il contient au moins `keep_min_cells` cellules non vides.
    Retourne: {"content_table": ["row1_as_csv\\nrow2_as_csv", ...]}
    """
    def rstrip_empty_cells(row):
        last = -1
        for i, c in enumerate(row):
            if c != "":
                last = i
        return row[: last + 1] if last >= 0 else []

    def nonempty_cells_count(rows):
        return sum(1 for r in rows for c in r if c != "")

    content_table = []
    current_key = None
    current_rows = []

    def flush():
        nonlocal current_rows
        if not current_rows:
            return
        if nonempty_cells_count(current_rows) >= keep_min_cells:
            table_str = "\n".join(",".join(r) for r in current_rows)
            if table_str.strip():
                content_table.append(table_str)
        current_rows = []

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        # ignorer le header (ex: page,table_id, ...)
        next(reader, None)

        for raw in reader:
            raw = [(c or "").strip() for c in raw]
            if len(raw) < 2:
                continue

            # Couple de séparation (page, idtable)
            key = (raw[0], raw[1])

            # Changement de tableau ?
            if current_key is None:
                current_key = key
            elif key != current_key:
                flush()
                current_key = key

            # Contenu sans (page, idtable)
            row = rstrip_empty_cells(raw[2:])
            if any(cell != "" for cell in row):  # ignorer lignes vides
                current_rows.append(row)

    # dernier tableau
    flush()

    return {
        "tool": "pdfplumber",
        "content_table": content_table
    }