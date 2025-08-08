# -*- coding: utf-8 -*-
# Usage:
#   python layout_to_field_text.py <images_dir> <layout_json_dir> <out_dir>
# Example:
#   python layout_to_field_text.py outputs/pages_png outputs/layout_json outputs/fields_json
#
# Input assumptions:
# - <images_dir> contient des pages PNG propres: page_0001.png, ...
# - <layout_json_dir> contient des JSON par page avec "blocks": [{"label", "bbox", "score"}, ...]
#   bbox format attendu: [x1, y1, x2, y2] en pixels (coordonnées image)
#
# Output:
# - <out_dir>/page_0001.fields.json  -> {"title": "...", "plain text": "...", "table": "...", ...}
# - <out_dir>/document.fields.json   -> fusion de toutes les pages (texte concaténé par champ)

import sys, os, json, math
from pathlib import Path
from PIL import Image

# ---- Réglages OCR (adapte si besoin à ton arborescence)
USE_CLS = True  # désactive si tu n'as pas téléchargé le modèle CLS
OCR_DET = "models/OCR/det"
OCR_REC = "models/OCR/rec"
OCR_CLS = "models/OCR/cls"  # utilisé si USE_CLS=True

# ---- Filtrage layout (optionnel)
CONF_MIN = 0.30      # ignorer les blocs avec score < 0.30
KEEP_LABELS = None   # ex: {"title","plain text","table"} ; None = garder tous

# ---- Tri des blocs (lecture): top-to-bottom puis left-to-right
def sort_key(b):
    x1, y1, x2, y2 = b["bbox"]
    return (int(y1 // 30), y1, x1)  # regroupe par "ligne" de ~30 px

def clip_box(box, W, H):
    x1, y1, x2, y2 = box
    x1 = max(0, min(W-1, float(x1)))
    y1 = max(0, min(H-1, float(y1)))
    x2 = max(0, min(W-1, float(x2)))
    y2 = max(0, min(H-1, float(y2)))
    if x2 < x1: x1, x2 = x2, x1
    if y2 < y1: y1, y2 = y2, y1
    return [x1, y1, x2, y2]

def clean_text(s):
    if not s: return ""
    # petites normalisations de base
    s = s.replace("\u00AD","")        # soft hyphen
    s = s.replace("\r","\n")
    s = "\n".join(line.strip() for line in s.splitlines())
    while "\n\n\n" in s:
        s = s.replace("\n\n\n","\n\n")
    return s.strip()

def main():
    if len(sys.argv) != 4:
        print("Usage: python layout_to_field_text.py <images_dir> <layout_json_dir> <out_dir>")
        sys.exit(1)

    images_dir = Path(sys.argv[1])
    layout_dir = Path(sys.argv[2])
    out_dir    = Path(sys.argv[3])
    out_dir.mkdir(parents=True, exist_ok=True)

    # Charge OCR (PaddleOCR) — zéro sudo, modèles locaux
    from paddleocr import PaddleOCR
    ocr_kwargs = dict(det_model_dir=OCR_DET, rec_model_dir=OCR_REC, show_log=False, use_gpu=True)
    if USE_CLS and Path(OCR_CLS).exists():
        ocr_kwargs.update(dict(cls_model_dir=OCR_CLS, use_angle_cls=True))
    else:
        ocr_kwargs.update(dict(use_angle_cls=False))
    ocr = PaddleOCR(**ocr_kwargs)

    # Index des images par "base name" (sans extension)
    img_index = {p.stem: p for p in images_dir.glob("*.png")}
    if not img_index:
        print(f"⚠ Aucun PNG trouvé dans {images_dir}")
        sys.exit(2)

    doc_fields = {}  # fusion doc: label -> texte concaténé

    # Parcours des JSON de layout
    for jpath in sorted(layout_dir.glob("*.json")):
        with open(jpath, "r", encoding="utf-8") as f:
            layout = json.load(f)

        # retrouver l'image correspondante
        # on part du principe que le json s'appelle "page_0001.json" -> "page_0001.png"
        base = Path(jpath).stem
        # si jamais base contient "_layout", on l'enlève
        base = base.replace("_layout", "")
        if base not in img_index:
            # tente cas fréquent: json sauvegarde "image": "page_0001.png"
            img_name = (Path(layout.get("image","")).stem or base).replace("_layout","")
            img_path = img_index.get(img_name)
            if not img_path:
                print(f"⚠ Image correspondante introuvable pour {jpath.name}")
                continue
        else:
            img_path = img_index[base]

        img = Image.open(img_path).convert("RGB")
        W, H = img.size

        # récupérer les blocs
        blocks = layout.get("blocks") or layout.get("elements") or []
        # filtrage
        sel = []
        for b in blocks:
            label = b.get("label") or b.get("type") or "unknown"
            score = float(b.get("score", 1.0))
            if score < CONF_MIN: 
                continue
            if KEEP_LABELS and label not in KEEP_LABELS:
                continue
            bbox = b.get("bbox")
            if not bbox or len(bbox) != 4:
                continue
            x1, y1, x2, y2 = clip_box(bbox, W, H)
            sel.append({"label": label, "score": score, "bbox": [x1,y1,x2,y2]})

        # tri lecture
        sel.sort(key=sort_key)

        # OCR par bloc + agrégation par label
        page_fields = {}
        for b in sel:
            x1, y1, x2, y2 = map(int, b["bbox"])
            crop = img.crop((x1, y1, x2, y2))
            o = ocr.ocr(crop, cls=ocr_kwargs.get("use_angle_cls", False))
            lines = []
            if o and o[0]:
                for ln in o[0]:
                    lines.append(ln[1][0])
            txt = clean_text("\n".join(lines))
            if not txt:
                continue
            page_fields.setdefault(b["label"], []).append(txt)

        # Sauvegarde JSON par page
        # on concatène les textes d’un même label par doubles sauts de ligne
        page_out = {k: clean_text("\n\n".join(v)) for k, v in page_fields.items()}
        with open(out_dir / f"{img_path.stem}.fields.json", "w", encoding="utf-8") as f:
            json.dump(page_out, f, ensure_ascii=False, indent=2)

        # Fusion dans le doc global
        for k, v in page_out.items():
            if v:
                doc_fields[k] = clean_text((doc_fields.get(k, "") + "\n\n" + v).strip())

    # JSON global fusionné
    with open(out_dir / "document.fields.json", "w", encoding="utf-8") as f:
        json.dump(doc_fields, f, ensure_ascii=False, indent=2)

    print("✅ OK")
    print(f"📄 Pages → {out_dir}/*.fields.json")
    print(f"📄 Document → {out_dir}/document.fields.json")

if __name__ == "__main__":
    main()
