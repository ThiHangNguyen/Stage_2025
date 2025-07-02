import argparse
import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np

def plot_metrics(csv_path, strategy, title_suffix=""):
    df = pd.read_csv(csv_path)
    metrics = ["accuracy", "f1", "recall"]
    colors = ["#5DCCF5", "#77DD77", "#FFB347"]

    if "field" not in df.columns:
        print("La colonne 'field' est absente du fichier.")
        return

    fields = df["field"]
    x_pos = np.arange(len(fields))
    bar_width = 0.2

    plt.figure(figsize=(max(10, len(fields) * 0.4), 6))

    for i, metric in enumerate(metrics):
        column = f"{metric}_{strategy}"
        if column not in df.columns:
            print(f"Colonne absente : {column}")
            return
        values = df[column]
        plt.bar(x_pos + (i - 1) * bar_width, values, width=bar_width,
                label=metric, color=colors[i])

    plt.xticks(x_pos, fields, rotation=90)
    plt.ylabel("Score")
    plt.title(f"Scores ({strategy}) par champ {title_suffix}")
    plt.ylim(0, 1.05)
    plt.legend()
    plt.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.show()

def list_matched(csv_path, strategy, match_value):
    df = pd.read_csv(csv_path)
    match_col = f"matched_{strategy}"
    if match_col not in df.columns:
        print(f"Colonne absente : {match_col}")
        return

    matched_df = df[df[match_col] == match_value]
    if matched_df.empty:
        print(f"Aucun champ {'matché' if match_value else 'non matché'} trouvé pour {strategy}")
        return

    print(f"\nChamps {'matchés' if match_value else 'non matchés'} ({strategy}) :")
    for field in matched_df["field"]:
        print(f"- {field}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tool", required=True, help="Nom de l’outil (ex: grobid)")
    parser.add_argument("--id", help="ID de l’article (ex: 1107141ar)")
    parser.add_argument("--strategy", choices=["strict", "soft", "levenshtein"], default="strict", help="Stratégie à visualiser")
    parser.add_argument("--matched", type=int, choices=[0, 1], help="Afficher uniquement les champs matchés (1) ou non matchés (0)")
    parser.add_argument("--avg", action="store_true", help="Afficher la moyenne globale (par outil)")

    args = parser.parse_args()

    if args.avg:
        csv_path = os.path.join("../results", "csv", "average", f"{args.tool}.csv")
        if not os.path.exists(csv_path):
            print(f"Fichier de moyenne non trouvé : {csv_path}")
            return
        plot_metrics(csv_path, args.strategy, title_suffix="(Moyenne)")
    else:
        if not args.id:
            print("Vous devez fournir un --id ou activer --avg.")
            return

        csv_path = os.path.join("../results", "csv", args.tool, f"{args.id}.csv")
        if not os.path.exists(csv_path):
            print(f"Fichier non trouvé : {csv_path}")
            return

        if args.matched is not None:
            list_matched(csv_path, args.strategy, args.matched)
        else:
            plot_metrics(csv_path, args.strategy, title_suffix=f"(ID: {args.id})")

if __name__ == "__main__":
    main()
