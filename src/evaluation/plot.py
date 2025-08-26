import pandas as pd
import matplotlib.pyplot as plt
import argparse
import os
import numpy as np


def plot_simple_grouped_bar_chart(df, directory, seuil=0.8, tool=None):
    df = df[df["directory"] == directory]
    if df.empty:
        print(f" Aucune donnée pour {directory}")
        return

    # Enlever les colonnes non-champ
    fields = [col for col in df.columns if col not in ["directory", "method"]]

    # Table transposée : rows = fields, cols = methods
    data = {method: df[df["method"] == method][fields].iloc[0] for method in ["strict", "soft", "levenshtein"]}
    df_transposed = pd.DataFrame(data)
    df_transposed["mean"] = df_transposed.mean(axis=1)
    df_transposed = df_transposed.sort_values(by="mean", ascending=False).drop(columns=["mean"])

    fields = df_transposed.index.tolist()
    methods = df_transposed.columns.tolist()
    x = range(len(fields))
    width = 0.25

    colors = {
        "strict": "#FF9999",        # rose clair
        "soft": "#FFD580",          # orange pâle
        "levenshtein": "#A6D785"    # vert pastel
    }
    plt.figure(figsize=(14, 6))
    for i, method in enumerate(methods):
        scores = df_transposed[method]
        plt.bar(
            [val + i * width for val in x],
            scores,
            width=width,
            label=method,
            color=colors.get(method, 'gray')
        )

    # Ligne seuil
    plt.axhline(y=seuil, color='blue', linestyle='--', label=f"Seuil = {seuil}")
    plt.xticks([val + width for val in x], fields, rotation=45, ha='right')
    plt.ylim(0, 1.05)
    plt.ylabel("Score de similarité")
    plt.title(
        f"{'['+tool+'] ' if tool else ''}Scores moyens par champ – {directory}",
        fontweight='bold',
        fontsize=14
    )
    plt.legend(loc="upper right")
    plt.tight_layout()
    plt.show()




def plot_structured_fields_all(df, directory, method="strict", seuil=0.8, tool=None):
    df = df[df["directory"] == directory]

    precision_metric = f"{method}_precision"
    recall_metric = f"{method}_recall"
    similarity_metric = f"{method}_avg_similarity"

    # Récupérer les champs
    fields = [col for col in df.columns if col not in ["directory", "metric"]]

    # Extraire les valeurs pour chaque métrique
    df_p = df[df["metric"] == precision_metric].iloc[0][fields]
    df_r = df[df["metric"] == recall_metric].iloc[0][fields]
    df_s = df[df["metric"] == similarity_metric].iloc[0][fields]

    # Trier les champs selon le rappel décroissant
    sorted_fields = df_r.sort_values(ascending=False).index.tolist()
    precision_vals = df_p[sorted_fields].values
    recall_vals = df_r[sorted_fields].values
    similarity_vals = df_s[sorted_fields].values

    x = np.arange(len(sorted_fields))
    width = 0.35

    plt.figure(figsize=(14, 6))
    # Barres précision et rappel
    plt.bar(x - width/2, precision_vals, width=width, label="Précision", color="cornflowerblue")
    bars = plt.bar(x + width/2, recall_vals, width=width, label="Rappel", color="gold")

    # Points pour similarité au-dessus de la barre de rappel
    plt.scatter(x + width/2, similarity_vals, label="Similarité", color="mediumseagreen", marker='D', s=80, zorder=5)

    # Texte sur les points
    for xi, yi in zip(x + width/2, similarity_vals):
        plt.text(xi, yi + 0.02, f"{yi:.2f}", ha='center', va='bottom', fontsize=9, color="green")

    # Ligne seuil
    plt.axhline(y=seuil, linestyle="--", color="blue", label=f"Seuil = {seuil}")

    # Mise en forme
    plt.xticks(x, sorted_fields, rotation=45, ha='right')
    plt.ylim(0, 1.1)
    plt.ylabel("Score")
    title_text = f"[{tool}] " if tool else ""
    title_text += f"{directory} – {method.capitalize()} - Scores par champ structuré"
    plt.title(title_text, fontweight='bold', fontsize=14)

    plt.legend(loc="upper right")
    plt.tight_layout()
    plt.show()


def get_sorted_fields_by_directory_priority(df_method, directories=None):
    """
    Trie les champs selon leur score moyen (par colonne).
    """
    fields = [col for col in df_method.columns if col not in ["directory", "method", "metric"]]
    sorted_fields = sorted(fields, key=lambda f: df_method[f].mean(), reverse=True)
    return sorted_fields


def plot_grouped_bars(df_method, sorted_fields, directories, method, tool=None):
    """
    Crée un graphique en barres groupées pour chaque répertoire.
    """
    seuil = 0.8
    x = range(len(sorted_fields))
    bar_width = 0.9 / len(directories)  # plus étroit
    space_between_groups = 0.4  # espace entre les groupes

    custom_colors = [
        "#66C2A5",  # vert doux
        "#FC8D62",  # orange saumon
        "#8DA0CB",  # bleu lavande
        "#F0B8DA" ,  # rose mauve
        "#E78AC3",  # rose doux
        "#A6D854",  # vert citron
        "#FFD92F",  # jaune vif
        "#E5C494",  # beige doré
           # gris moyen
    ]
    plt.figure(figsize=(12, 6))

    for i, dir_name in enumerate(directories):
        values = [df_method.loc[df_method["directory"] == dir_name, field].values[0] for field in sorted_fields]
        plt.bar(
            [pos * (1 + space_between_groups) + i * bar_width for pos in x],
            values,
            width=bar_width,
            label=dir_name,
            color=custom_colors[i % len(custom_colors)]

        )

    plt.axhline(y=seuil, color='blue', linestyle='--', label=f"Seuil = {seuil}")
    plt.xticks(
        [pos * (1 + space_between_groups) + bar_width * (len(directories) - 1) / 2 for pos in x],
        sorted_fields,
        rotation=45,
        ha="right"
    )
    plt.ylim(0, 1.05)
    plt.ylabel("Score")
    title_text = f"[{tool}] " if tool else ""
    title_text += f"Scores moyens par champ et journal — méthode {method}"
    plt.title(title_text, fontweight='bold', fontsize=14)
    plt.legend(title="Répertoire", loc="upper right")

    plt.tight_layout()
    plt.show()

def plot_simple_all_fields_grouped_by_directory(df, method, tool=None):
    """
    Affiche un graphique comparant tous les champs pour une méthode donnée,
    en groupant les barres par répertoire.
    """
    df_method = df[df["method"] == method]

    if df_method.empty:
        print(f"Aucune donnée pour la méthode '{method}'")
        return

    directories = df_method["directory"].tolist()
    sorted_fields = get_sorted_fields_by_directory_priority(df_method, directories)
    plot_grouped_bars(df_method, sorted_fields, directories, method, tool=tool)


def plot_structured_all_fields_grouped_by_directory(df, method, metric, tool=None):
    seuil = 0.8
    df_method = df[df["metric"] == f"{method}_{metric}"]

    if df_method.empty:
        print(f"Aucune donnée pour la combinaison méthode '{method}' et métrique '{metric}'")
        return

    directories = df_method["directory"].tolist()
    fields = [col for col in df_method.columns if col not in ["directory", "metric"]]
    sorted_fields = sorted(fields, key=lambda f: df_method[f].mean(), reverse=True)

    x = range(len(sorted_fields))
    bar_width = 0.9 / len(directories)
    space_between_groups = 0.4

    custom_colors = [
        "#66C2A5",  # vert doux
        "#FC8D62",  # orange saumon
        "#8DA0CB",  # bleu lavande
        "#F0B8DA" ,  # rose mauve
        "#E78AC3",  # rose doux
        "#A6D854",  # vert citron
        "#FFD92F",  # jaune vif
        "#E5C494",  # beige doré
           # gris moyen
    ]

    plt.figure(figsize=(12, 6))
    for i, dir_name in enumerate(directories):
        values = [df_method.loc[df_method["directory"] == dir_name, field].values[0] for field in sorted_fields]
        plt.bar(
            [pos * (1 + space_between_groups) + i * bar_width for pos in x],
            values,
            width=bar_width,
            label=dir_name,
            color=custom_colors[i % len(custom_colors)]
        )
    plt.axhline(y=seuil, color='blue', linestyle='--', label=f"Seuil = {seuil}")
    plt.xticks(
        [pos * (1 + space_between_groups) + bar_width * (len(directories) - 1) / 2 for pos in x],
        sorted_fields,
        rotation=45,
        ha="right"
    )
    plt.ylim(0, 1.05)
    plt.ylabel("Score")
    title_text = f"[{tool}] " if tool else ""
    title_text += f"{method.capitalize()} – {metric.capitalize()} sur les types de journaux"
    plt.title(title_text, fontweight='bold', fontsize=14)
    plt.legend(title="Répertoire", loc="upper right")
    plt.tight_layout()
    plt.show()



def compare_tools_on_fields(
    tools,
    method,
    metric,
    base_dir="results/csv",
    seuil=0.8,
    directory_target="2cols",
    field_type="structured",
    annot=True,                # écrire les valeurs dans les cellules
    cmap="YlOrRd",             # palette orange→rouge (alternatives: "OrRd", "inferno")
    fmt=".2f",                 # format des annotations
):
    all_dfs = []
    filename = "structured.csv" if field_type == "structured" else "simple.csv"

    # ----- chargement / filtrage (identique à avant) -----
    for tool in tools:
        path = os.path.join(base_dir, tool, "means", filename)
        if not os.path.exists(path):
            print(f"❌ Fichier introuvable : {path}")
            continue

        df_raw = pd.read_csv(path)

        if field_type == "structured":
            if "metric" not in df_raw.columns:
                print(f"⚠️ Format incorrect dans {path} : colonne 'metric' manquante")
                continue

            df_long = df_raw.melt(
                id_vars=["directory", "metric"],
                var_name="field",
                value_name="score"
            )
            df_long["method"] = df_long["metric"].apply(lambda x: x.split("_")[0])
            df_long["metric"] = df_long["metric"].apply(lambda x: "_".join(x.split("_")[1:]))
            df_long["tool"]  = tool

            df_filtered = df_long[
                (df_long["method"] == method)
                & (df_long["metric"] == metric)
                & (df_long["directory"] == directory_target)
            ]
        else:
            if "method" not in df_raw.columns:
                print(f"⚠️ Format incorrect dans {path} : colonne 'method' manquante")
                continue

            df_long = df_raw.melt(
                id_vars=["directory", "method"],
                var_name="field",
                value_name="score"
            )
            df_long["metric"] = "score"
            df_long["tool"]  = tool

            df_filtered = df_long[
                (df_long["method"] == method)
                & (df_long["directory"] == directory_target)
            ]

        if df_filtered.empty:
            print(f"⚠️ Aucune donnée pour {tool} (method={method}, metric={metric}, dir={directory_target})")
        else:
            all_dfs.append(df_filtered)

    if not all_dfs:
        print("🚫 Aucune donnée valide pour la comparaison.")
        return

    # ----- agrégation -----
    df_all = pd.concat(all_dfs, ignore_index=True)
    df_mean = (
        df_all.groupby(["field", "tool"], as_index=False)["score"]
        .mean()
        .rename(columns={"score": "mean_score"})
    )

    present_tools = [t for t in tools if t in df_mean["tool"].unique()]
    if not present_tools:
        print("🚫 Aucun outil présent après filtrage.")
        return

    pivot = df_mean.pivot(index="field", columns="tool", values="mean_score")
    pivot["_mean"] = pivot[present_tools].mean(axis=1)
    pivot = pivot.sort_values("_mean", ascending=False).drop(columns=["_mean"])
    pivot = pivot.reindex(columns=present_tools)

    data   = pivot.fillna(0.0).values
    fields = list(pivot.index)
    cols   = list(pivot.columns)

    # ----- heatmap matplotlib (orange→rouge + annotations) -----
    fig_w = max(8, 0.35 * len(cols))
    fig_h = max(6, 0.35 * len(fields))
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))

    im = ax.imshow(data, aspect="auto", vmin=0.0, vmax=1.0, cmap=cmap)

    ax.set_xticks(np.arange(len(cols)))
    ax.set_yticks(np.arange(len(fields)))
    ax.set_xticklabels(cols, rotation=30, ha="right")
    ax.set_yticklabels(fields)

    # titre/labels
    if field_type == "simple":
        title_text = f"similarité moyenne — méthode {method} — dossier '{directory_target}'"
        cbar_label = "score"
    else:
        title_text = f"{metric.capitalize()} — méthode {method} — dossier '{directory_target}'"
        cbar_label = metric
    ax.set_title(title_text, pad=12, fontweight="bold")
    ax.set_xlabel("Outils")
    ax.set_ylabel("Champs")

    # barre de couleur
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label(cbar_label, rotation=90, va="center")
    cbar.set_ticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])

    # annotations
    if annot:
        for i in range(data.shape[0]):
            for j in range(data.shape[1]):
                val = data[i, j]
                # option: n'afficher rien pour 0.0 -> décommente si voulu
                # if val == 0: continue
                ax.text(j, i, format(val, fmt), ha="center", va="center", fontsize=8)

    # rappel visuel du seuil (texte)
    ax.text(1.01, -0.08, f"Seuil visé : {seuil}", transform=ax.transAxes,
            ha="left", va="top", fontsize=9)

    # fines séparations (grille légère)
    ax.set_xlim(-0.5, data.shape[1]-0.5)
    ax.set_ylim(data.shape[0]-0.5, -0.5)
    ax.grid(which="both", color="white", linewidth=0.5, alpha=0.5)
    ax.set_xticks(np.arange(-0.5, data.shape[1], 1), minor=True)
    ax.set_yticks(np.arange(-0.5, data.shape[0], 1), minor=True)

    plt.tight_layout()
    plt.show()
    print("✅ Done ")


def compare_mean_per_field_across_dirs(tools, method, metric, seuil=0.8):
    all_dfs = []

    for tool in tools:
        path = os.path.join("results/csv", tool, "means", "structured.csv")
        if not os.path.exists(path):
            print(f"❌ Fichier introuvable : {path}")
            continue

        df_raw = pd.read_csv(path)
        if "metric" not in df_raw.columns:
            print(f"⚠️ Format incorrect dans {path} : colonne 'metric' manquante")
            continue

        # Transformation longue
        df_long = df_raw.melt(id_vars=["directory", "metric"], var_name="field", value_name="score")
        df_long = df_long.dropna(subset=["score"])
        df_long["method"] = df_long["metric"].apply(lambda x: x.split("_")[0])
        df_long["metric"] = df_long["metric"].apply(lambda x: "_".join(x.split("_")[1:]))
        df_long["tool"] = tool

        df_filtered = df_long[
            (df_long["method"] == method) & (df_long["metric"] == metric)
        ]

        if df_filtered.empty:
            print(f"⚠️ Aucune donnée pour {tool} avec méthode={method} et métrique={metric}")
        else:
            all_dfs.append(df_filtered)

    if not all_dfs:
        print("🚫 Aucune donnée valide pour la comparaison.")
        return

    # Fusionner et calculer la moyenne par outil et champ
    df_all = pd.concat(all_dfs, ignore_index=True)
    df_mean = df_all.groupby(["tool", "field"])["score"].mean().reset_index()

    fields = sorted(df_mean["field"].unique())
    N = len(fields)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    ax.spines["polar"].set_visible(False)

    for tool in tools:
        df_tool = df_mean[df_mean["tool"] == tool].set_index("field").reindex(fields)
        scores = df_tool["score"].tolist()
        scores += scores[:1]
        ax.plot(angles, scores, label=tool, linewidth=2)

    ax.set_yticks([])

    for val in [0, seuil, 1.0]:
        ax.text(1.5, val + 0.02, f"{val}", ha='center', va='bottom', fontsize=9, fontweight='bold')

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(fields, fontsize=9)
    ax.set_title(f"(MOYENNE) - Méthode: {method} / Métrique: {metric}", size=14, pad=20)
    ax.set_rlabel_position(30)
    ax.axhline(seuil, color="blue", linestyle="--", label=f"Seuil = {seuil}")
    ax.set_ylim(0, 1)
    ax.legend(loc='upper right', bbox_to_anchor=(1.2, 1.1))
    plt.tight_layout()
    plt.savefig(f"figures/radar_compare_mean_{method}_{metric}.png")
    plt.show()



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Visualisation des scores d’extraction par champ")

    # Options standards
    parser.add_argument('--tool', help="Nom de l’outil évalué (ex: grobid, nougat)")
    parser.add_argument("--tools", nargs="+", help="Liste des outils à comparer (ex: grobid nougat)")
    parser.add_argument('--dir', help="Nom du répertoire (ex: haf18)")
    parser.add_argument('--type', choices=["simple", "structured"], help="Type de score à tracer")
    parser.add_argument('--seuil', type=float, default=0.8, help="Seuil pour marquer 'bien extrait'")
    parser.add_argument('--method', type=str, default="strict", choices=["strict","soft", "levenshtein"],
                        help="Méthode de comparaison à afficher pour les champs structurés")
    parser.add_argument('--metric', choices=["precision", "recall", "avg_similarity"],
                        help="Métrique à comparer entre les répertoires (structuré seulement)")
    parser.add_argument("--mean", action="store_true", help="Utiliser la moyenne sur tous les répertoires")    # Comparaison multi-outils
    parser.add_argument('--compare_tools', action='store_true', help="Comparer plusieurs outils pour un champ donné")

    args = parser.parse_args()
    os.makedirs("figures", exist_ok=True)
    
    if args.mean:
        compare_mean_per_field_across_dirs(args.tools, args.method, args.metric, seuil=args.seuil)
        exit()
        # python3 src/evaluation/plot.py  --tools grobid nougat --method strict --metric recall --mean
    elif args.compare_tools:
        compare_tools_on_fields(
            tools=args.tools,
            method=args.method,
            metric=args.metric,
            seuil=args.seuil,
            directory_target=args.dir,
            field_type=args.type )
        exit()
    #python3 src/evaluation/plot.py --compare_tools --tools grobid nougat olmOCR --method levenshtein --metric recall --dir ae49 --type simple 
    #python3 src/evaluation/plot.py --compare_tools --tools grobid nougat tatr pdfExtractKit olmOCR pdfplumber --method levenshtein --metric recall --dir 2cols --type structured

    
    if not args.tool or not args.type:
        print("Erreur : --tool et --type sont requis sauf si --compare_tools est activé.")
        exit(1)

    base_path = f"results/csv/{args.tool}/means"

    if args.type == "simple":
        df = pd.read_csv(f"{base_path}/simple.csv")
        if args.dir:
            plot_simple_grouped_bar_chart(df, args.dir, seuil=args.seuil, tool=args.tool)
        elif args.method:
            plot_simple_all_fields_grouped_by_directory(df, method=args.method, tool=args.tool)

    elif args.type == "structured":
        df = pd.read_csv(f"{base_path}/structured.csv")

        if args.method and args.metric and not args.dir:
            plot_structured_all_fields_grouped_by_directory(df, method=args.method, metric=args.metric, tool=args.tool)
        elif args.dir and args.method:
            plot_structured_fields_all(df, args.dir, method=args.method, seuil=args.seuil, tool=args.tool)
        else:
            print("Veuillez spécifier au moins --dir et --method, ou --method et --metric pour 'structured'.")

#python3 src/evaluation/plot.py --dir haf18 --type structured --method soft
#python3 src/evaluation/plot.py --type structured --method soft --metric recall

#python3 src/evaluation/plot.py --dir haf18 --type simple
#python3 src/evaluation/plot.py --type simple --method soft
