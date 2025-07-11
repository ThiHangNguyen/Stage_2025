 

#!/bin/bash 

INPUT_DIR="/Tmp/nguyth/project/Stage_2025/data/pdfs" 
OUTPUT_DIR="/Tmp/nguyth/project/Stage_2025/data/raw/xml_grobid/" 
mkdir -p "$OUTPUT_DIR"

for f in "$INPUT_DIR"/*.pdf; do 
	b=$(basename "$f" .pdf) 
	echo "Processing $f..." 
	curl -s -X POST http://localhost:8070/api/processFulltextDocument -F input=@"$f" -F consolidateHeader=1 -F consolidateCitations=1 -F consolidateFunding=1 -F includeRawAffiliations=1 -F includeRawCitations=1 -F includeRawCopyright=1 -F segmentSentences=1 -F generateIDs=1 -F teiCoordinates=persName -F teiCoordinates=figure -F teiCoordinates=ref -F teiCoordinates=biblStruct -F teiCoordinates=formula -F teiCoordinates=head -F teiCoordinates=label -F teiCoordinates=figureDesc -F teiCoordinates=table -F teiCoordinates=tr -F teiCoordinates=s -o "$OUTPUT_DIR/$b.xml" 
done 