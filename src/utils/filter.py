import pandas as pd

"""
- Extraire des sous-ensembles d'identifiants d'articles complets pour différents journaux
- Chaque groupe est filtré selon des conditions spécifiques
- Les identifiants sélectionnés sont sauvegardés dans un fichier CSV par journal
"""

input_path = "data/publishing_report_08b921a7-88f9-4f96-8a8c-68a6e94adefa.tsv"
df = pd.read_csv(input_path, sep="\t", dtype=str)

# Liste des journaux à traiter
journals = ["cqd27", "ae49", "haf18"]

all_ids = {}

for group_name in journals:
    # Filtrage par journal + conditions
    filtered_df = df[
        (df["journal_localidentifier"] == group_name) &
        (df["document_processing_type"] == "complete") &
        (df["document_type"] == "article")
    ]

    # Extraire jusqu’à 100 IDs
    ids = filtered_df["document_localidentifier"].head(100).tolist()

    if ids:  
        all_ids[group_name] = ids
        output_path = f"data/csv/article_ids_{group_name}.csv"
        pd.Series(ids).to_csv(output_path, index=False, header=False)
        print(f"{len(ids)} IDs sauvegardés dans : {output_path}")
    else:
        print(f"[INFO] Aucun article éligible pour le journal : {group_name}")

# all_ids contient maintenant les IDs par journal si tu veux les réutiliser


#informations complémentaires
# nb_complets = (df["document_processing_type"] == "complete").sum()
# print(f"Nombre de documents complets : {nb_complets}")

# nb_cqd27_complets = df[
#     (df["journal_localidentifier"] == "cqd27") &
#     (df["document_processing_type"] == "complete")
# ].shape[0]

# print(f"Nombre de documents 'complete' pour le journal cqd27 : {nb_cqd27_complets}")
