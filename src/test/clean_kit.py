# save as make_layout_json.py
# Usage: python make_layout_json.py outputs/test_layout outputs/layout_json
import os, sys, json, glob
from pathlib import Path
from PIL import Image
from doclayout_yolo.models.yolov10 import YOLOv10

src = Path(sys.argv[1])              # dossier avec tes PNG (ex: outputs/test_layout)
dst = Path(sys.argv[2])              # dossier de sortie JSON
dst.mkdir(parents=True, exist_ok=True)

WEIGHTS = "models/Layout/YOLO/doclayout_yolo_ft.pt"
CONF_MIN = 0.50                      # garde seulement score >= 0.50

model = YOLOv10(WEIGHTS)
names = model.model.names if hasattr(model, "model") else {}

def is_img(p):
    return p.suffix.lower() in {".png",".jpg",".jpeg",".webp",".bmp"}

imgs = sorted([p for p in src.iterdir() if p.is_file() and is_img(p)])
all_items = []
for img_path in imgs:
    img = Image.open(img_path).convert("RGB")
    res = model.predict(img)
    page_items = []
    if res and hasattr(res[0], "boxes") and res[0].boxes is not None:
        boxes = res[0].boxes
        xyxy = boxes.xyxy.cpu().numpy()
        cls  = boxes.cls.cpu().numpy()
        conf = boxes.conf.cpu().numpy()
        for (x1,y1,x2,y2), c, s in zip(xyxy, cls, conf):
            if s < CONF_MIN: 
                continue
            item = {
                "label": names.get(int(c), str(int(c))),
                "class_id": int(c),
                "score": float(s),
                "bbox": [float(x1), float(y1), float(x2), float(y2)]
            }
            page_items.append(item)
            all_items.append({"file": img_path.name, **item})

    out_json = dst / (img_path.stem + ".json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump({"image": img_path.name, "blocks": page_items}, f, ensure_ascii=False, indent=2)

# JSON global en plus (optionnel)
with open(dst / "all_pages.json", "w", encoding="utf-8") as f:
    json.dump(all_items, f, ensure_ascii=False, indent=2)

print("✅ JSON par image ->", dst)
