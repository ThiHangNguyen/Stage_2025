import pandas as pd
import os

input_path = "data/publishing_report_08b921a7-88f9-4f96-8a8c-68a6e94adefa.tsv"
df = pd.read_csv(input_path, sep="\t", dtype=str)

# Filtrer selon les conditions
filtered_df = df[
    (df["journal_localidentifier"] == "cqd27") &
    (df["document_processing_type"] == "complete")&
    (df["document_type"] == "article")
]

# Extraire jusqu’à 100 IDs
ids = filtered_df["document_localidentifier"].head(100).tolist()

group_name = "cqd27"
output_path = f"data/csv/article_ids_{group_name}.csv"
pd.Series(ids).to_csv(output_path, index=False, header=False)

print(f"{len(ids)} IDs sauvegardés dans : {output_path}")
