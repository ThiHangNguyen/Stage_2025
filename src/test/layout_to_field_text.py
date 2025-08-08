import os
import json
import argparse
from pathlib import Path
from paddleocr import PaddleOCR
from pdf2image import convert_from_path
from tqdm import tqdm

def pdf_to_images(pdf_path):
    """
    Convert a PDF into a list of PIL images (one per page)
    """
    images = convert_from_path(pdf_path)
    return images

def run_ocr_on_images(images, ocr):
    """
    Run OCR on a list of images and return structured results
    """
    results = []
    for idx, img in enumerate(tqdm(images, desc="Processing pages")):
        ocr_result = ocr.ocr(img, cls=False)
        page_data = []
        for line in ocr_result[0]:
            bbox = line[0]  # Bounding box
            text = line[1][0]  # Detected text
            score = line[1][1]  # Confidence
            page_data.append({
                "bbox": bbox,
                "text": text,
                "score": score
            })
        results.append({
            "page": idx + 1,
            "content": page_data
        })
    return results

def save_results(results, output_dir, pdf_filename):
    """
    Save OCR results as a JSON file
    """
    os.makedirs(output_dir, exist_ok=True)
    output_file = Path(output_dir) / f"{Path(pdf_filename).stem}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"[OK] JSON saved at: {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Extract text & fields from PDF to JSON")
    parser.add_argument("--pdf_path", required=True, help="Path to the PDF file")
    parser.add_argument("--output_dir", required=True, help="Directory to store JSON output")
    args = parser.parse_args()

    # Init OCR (English models only)
    ocr = PaddleOCR(
        lang="en",                   # Force English
        det_model_dir="models/OCR/det",
        rec_model_dir="models/OCR/rec",
        use_angle_cls=False,
        show_log=False,
        use_gpu=True
    )

    print("[INFO] Converting PDF to images...")
    images = pdf_to_images(args.pdf_path)

    print("[INFO] Running OCR...")
    results = run_ocr_on_images(images, ocr)

    print("[INFO] Saving JSON...")
    save_results(results, args.output_dir, args.pdf_path)

if __name__ == "__main__":
    main()
