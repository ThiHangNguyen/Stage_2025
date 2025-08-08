# Dossiers cibles
mkdir -p models/OCR/{det,rec,cls}

# DET (PP-OCRv4 anglais)
python - <<'PY'
from huggingface_hub import snapshot_download
snapshot_download("PaddlePaddle/PP-OCRv4_en_det",
                  local_dir="models/OCR/det",
                  local_dir_use_symlinks=False)
print("✅ DET -> models/OCR/det")
PY

# REC (PP-OCRv4 anglais)
python - <<'PY'
from huggingface_hub import snapshot_download
snapshot_download("PaddlePaddle/PP-OCRv4_en_rec",
                  local_dir="models/OCR/rec",
                  local_dir_use_symlinks=False)
print("✅ REC -> models/OCR/rec")
PY

# (optionnel) CLS (orientation)
python - <<'PY'
from huggingface_hub import snapshot_download
snapshot_download("PaddlePaddle/PP-OCRv3_cls",
                  local_dir="models/OCR/cls",
                  local_dir_use_symlinks=False)
print("✅ CLS -> models/OCR/cls")
PY
