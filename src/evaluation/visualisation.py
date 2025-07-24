import os
import argparse
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

def collect_scores_by_field_and_method(directory, field_name, method_name):
    """
    Lit tous les fichiers CSV dans `directory`, extrait les scores pour le champ et la méthode spécifiés.
    Retourne un DataFrame avec une seule colonne : les scores.
    """
    data = []

    for file in sorted(os.listdir(directory)):
        full_path = os.path.join(directory, file)
        if file.endswith(".csv") and os.path.isfile(full_path):
            df = pd.read_csv(full_path, index_col="field")
            if ( field_name in df.index and method_name in df.columns and "has_ref" in df.columns and df.at[field_name, "has_ref"] == 1):
                score = df.at[field_name, method_name]
                data.append({"file": file.replace(".csv", ""), "score": score})

    if not data:
        raise ValueError(f"Aucune donnée trouvée pour le champ '{field_name}' et la méthode '{method_name}'")

    return pd.DataFrame(data).set_index("file")


def plot_scores(df, field_name, method_name):
    """
    Affiche une courbe simple des scores pour un champ et une méthode.
    Ajoute un effet de survol (hover) pour voir l'ID de l’article.
    """
    df.sort_index(inplace=True)
    fig, ax = plt.subplots(figsize=(12, 5))
    
    x_vals = range(len(df))
    y_vals = df["score"].values
    labels = df.index.tolist()

    points = ax.plot(x_vals, y_vals, marker='o', linestyle='-', label="Score")

    ax.set_title(f"Scores '{method_name}' pour le champ '{field_name}'")
    ax.set_ylabel("Score")
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("Article ID")
    ax.grid(True, linestyle='--', alpha=0.5)

    annot = ax.annotate("", xy=(0, 0), xytext=(15, 15), textcoords="offset points",
                        bbox=dict(boxstyle="round", fc="w"),
                        arrowprops=dict(arrowstyle="->"))
    annot.set_visible(False)

    def update_annot(ind):
        idx = ind["ind"][0]
        annot.xy = (x_vals[idx], y_vals[idx])
        text = f"{labels[idx]}: {y_vals[idx]:.3f}"
        annot.set_text(text)

    def hover(event):
        vis = annot.get_visible()
        if event.inaxes == ax:
            cont, ind = points[0].contains(event)
            if cont:
                update_annot(ind)
                annot.set_visible(True)
                fig.canvas.draw_idle()
            elif vis:
                annot.set_visible(False)
                fig.canvas.draw_idle()

    fig.canvas.mpl_connect("motion_notify_event", hover)
    plt.tight_layout()
    plt.show()

def plot_mean_scores_per_field_comparative(tool_dirs: dict, method_name: str):
    """
    Compare plusieurs outils sur les scores moyens par champ (méthode donnée).
    Affiche un scatter plot avec info-bulle dynamique.
    """

    combined = []

    for tool, directory in tool_dirs.items():
        all_dfs = []

        for file in sorted(os.listdir(directory)):
            full_path = os.path.join(directory, file)
            if file.endswith(".csv") and os.path.isfile(full_path):
                df = pd.read_csv(full_path, index_col="field")
                if "has_ref" not in df.columns or "has_extractor" not in df.columns:
                    print(f"[Avertissement] Colonnes nécessaires manquantes dans {file}, ignoré.")
                    continue

                # Filtrer uniquement les champs ayant au moins un has_ref et has_extractor
                df_filtered = df[(df["has_ref"] == 1) & (df["has_extractor"] == 1)]

                if method_name in df_filtered.columns:
                    all_dfs.append(df_filtered[[method_name]])

        if not all_dfs:
            print(f"[Avertissement] Aucun CSV valide trouvé pour {tool} avec la méthode '{method_name}'")
            continue

        merged = pd.concat(all_dfs, axis=1)
        mean_scores = merged.mean(axis=1)
        field_counts = merged.count(axis=1)

        for field in mean_scores.index:
            combined.append({
                "tool": tool,
                "field": field,
                "score": mean_scores[field],
                "count": field_counts[field]
            })

    df_combined = pd.DataFrame(combined)
    if df_combined.empty:
        print("[Erreur] Aucun champ n’a pu être affiché avec has_ref=1 et has_extractor=1.")
        return

    # Nom du répertoire (ex: ae49)
    repertoire_name = os.path.basename(os.path.normpath(list(tool_dirs.values())[0]))
    nb_fields = df_combined["field"].nunique()

    # Plot interactif
    fig, ax = plt.subplots(figsize=(12, 6))
    colors = {"grobid": "blue", "autre": "orange"}

    sc = []
    for tool in df_combined["tool"].unique():
        subset = df_combined[df_combined["tool"] == tool]
        scatter = ax.scatter(
            subset["field"],
            subset["score"],
            s=subset["score"] * 1000,
            alpha=0.6,
            label=tool,
            color=colors.get(tool, "gray"),
        )
        sc.append(scatter)

    ax.set_title(f"[{repertoire_name}] Moyenne des scores par champ ({method_name}) - {nb_fields} champs trouvés")
    ax.set_ylabel("Score moyen")
    ax.set_ylim(0, 1.05)
    ax.set_xticks(range(len(df_combined["field"].unique())))
    ax.set_xticklabels(df_combined["field"].unique(), rotation=45, ha="right")
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    ax.legend()

    # Info-bulle
    annot = ax.annotate("", xy=(0, 0), xytext=(15, 15), textcoords="offset points",
                        bbox=dict(boxstyle="round", fc="w"),
                        arrowprops=dict(arrowstyle="->"))
    annot.set_visible(False)

    def update_annot(ind, scatter, tool):
        index = ind["ind"][0]
        point = scatter.get_offsets()[index]
        field = df_combined[
            (df_combined["tool"] == tool) &
            (df_combined["score"] == point[1]) &
            (df_combined["field"] == point[0])
        ].iloc[0]
        annot.xy = point
        text = f"{field['field']}\n{tool}\nscore={field['score']:.3f}\nn={int(field['count'])}"
        annot.set_text(text)
        annot.get_bbox_patch().set_facecolor(colors.get(tool, "gray"))
        annot.get_bbox_patch().set_alpha(0.8)

    def on_hover(event):
        visible = annot.get_visible()
        for scatter, tool in zip(sc, df_combined["tool"].unique()):
            cont, ind = scatter.contains(event)
            if cont:
                update_annot(ind, scatter, tool)
                annot.set_visible(True)
                fig.canvas.draw_idle()
                return
        if visible:
            annot.set_visible(False)
            fig.canvas.draw_idle()

    fig.canvas.mpl_connect("motion_notify_event", on_hover)

    plt.tight_layout()
    plt.show()

    # Enregistrement CSV avec 'field', 'score', 'count'
    means_dir = f"results/csv/grobid/means"
    os.makedirs(means_dir, exist_ok=True)
    output_file = os.path.join(means_dir, f"{repertoire_name}.csv")
    df_combined_sorted = df_combined.sort_values("field")
    df_combined_sorted[["field", "score", "count"]].drop_duplicates("field").to_csv(output_file, index=False)
    print(f"[Info] Scores moyens enregistrés dans {output_file}")



def main():
    parser = argparse.ArgumentParser(description="Visualise les scores de comparaison d’outils")

    parser.add_argument("--field", help="Champ à visualiser (ex: title, abstract, etc.)")
    parser.add_argument("--method", required=True, choices=["strict", "soft", "levenshtein"], help="Méthode à visualiser")
    parser.add_argument("--tool", required=True, help="Nom de l'outil à visualiser (ex: grobid)")
    parser.add_argument("--dir", default="results/csv/grobid", help="Répertoire contenant les fichiers CSV")
    parser.add_argument("--2cols", action="store_true", help="Utiliser les résultats du sous-répertoire xml_2cols/")
    parser.add_argument("--compare", action="store_true", help="Comparer plusieurs outils (ex: GROBID vs autres)")

    args = parser.parse_args()

    base_path = os.path.join("results", "csv", args.tool)
    if args.dir:
        base_path = os.path.join(base_path, args.dir)

    if not os.path.isdir(base_path):
        print(f"[ERREUR] Le répertoire {base_path} n'existe pas.")
        return

    if args.compare:
        # Pour l'instant, comparer uniquement grobid
        tool_dirs = {
            args.tool: base_path
        }
        plot_mean_scores_per_field_comparative(tool_dirs, args.method)

    elif args.field:
        df = collect_scores_by_field_and_method(base_path, args.field, args.method)
        print(df.round(3))
        plot_scores(df, args.field, args.method)

    else:
        print("[ERREUR] Vous devez spécifier soit --field pour visualiser un champ, soit --compare pour comparer plusieurs outils.")

if __name__ == "__main__":
    main()

#python3  src/evaluation/visualisation.py --method levenshtein --2cols --compare
#python3  src/evaluation/visualisation.py --field title --method levenshtein