#!/bin/bash

# Liste des identifiants de journaux
journals=("haf18")

# Répertoire racine des PDF et des sorties XML
PDF_ROOT="/Tmp/nguyth/project/Stage_2025/data/pdfs"
XML_ROOT="/Tmp/nguyth/project/Stage_2025/data/raw/xml_grobid"

# Créer le répertoire de sortie global s'il n'existe pas
mkdir -p "$XML_ROOT"

# Lancer le traitement pour chaque journal
for journal in "${journals[@]}"; do
    INPUT_DIR="$PDF_ROOT/$journal"
    OUTPUT_DIR="$XML_ROOT/$journal"

    echo "Traitement du journal : $journal"
    mkdir -p "$OUTPUT_DIR"

    for f in "$INPUT_DIR"/*.pdf; do
        [ -e "$f" ] || continue  # ignore si aucun fichier PDF
        b=$(basename "$f" .pdf)
        echo "  -> Traitement de $b.pdf..."
        curl -s -X POST http://localhost:8070/api/processFulltextDocument -F input=@"$f" -F consolidateHeader=1 -F consolidateCitations=1 -F consolidateFunding=1 -F includeRawAffiliations=1 -F includeRawCitations=1 -F includeRawCopyright=1 -F segmentSentences=1 -F generateIDs=1 -F teiCoordinates=persName -F teiCoordinates=figure -F teiCoordinates=ref -F teiCoordinates=biblStruct -F teiCoordinates=formula -F teiCoordinates=head -F teiCoordinates=label -F teiCoordinates=figureDesc -F teiCoordinates=table -F teiCoordinates=tr -F teiCoordinates=s -o "$OUTPUT_DIR/$b.xml"

    done
done

