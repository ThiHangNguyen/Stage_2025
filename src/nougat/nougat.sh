#!/bin/bash 

INPUT_DIR="/Tmp/nguyth/project/Stage_2025/data/pdfs"
OUTPUT_DIR="/Tmp/nguyth/project/Stage_2025/data/raw/latex_nougat" 

find "$INPUT_DIR" -type f -name "*.pdf" | while read -r pdf_file; do 
    rel_path="${pdf_file#$INPUT_DIR/}" # ex: revue1/id1.pdf 
    subdir=$(dirname "$rel_path") # ex: revue1 
    id=$(basename "$pdf_file" .pdf) # ex: id1 

    mkdir -p "$OUTPUT_DIR/$subdir" 
    out_path="$OUTPUT_DIR/$subdir/$id.mmd" 
    
    echo "Processing $rel_path → $out_path" 
    nougat "$pdf_file" --recompute --no-skipping > "$out_path" 
  

done 