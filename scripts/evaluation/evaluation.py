import argparse
from utils.io import normalize_text, load_json, save_to_csv
from evaluation.strategies.strict import strict_match
from evaluation.strategies.soft import soft_match
from evaluation.strategies.levenshtein import levenshtein_match
from evaluation.metrics.accuracy import accuracy
from evaluation.metrics.f1 import f1_score
from evaluation.metrics.recall import recall
from evaluation.metrics.support import support
from collections import defaultdict
from evaluation.metrics.metrics import compute_metrics
import time  

STRATEGIES = {
    "strict": strict_match,
    "soft": soft_match,
    "levenshtein": levenshtein_match,
}

METRICS = {
    "accuracy": accuracy,
    "f1": f1_score,
    "recall": recall,
    "support": support,
}


def compare_dict_of_strings(exp_dict, pred_dict, seuil=0.8):
    """
    Compare deux dictionnaires simples (ex: id, pagination, rights),
    en appliquant des similarités sur chaque champ,
    et en calculant un F1 global.
    """
    norm_exp = {k: normalize_text(v) for k, v in exp_dict.items()}
    norm_pred = {k: normalize_text(pred_dict.get(k, "")) for k in norm_exp}

    results = {}

    for strat_name, match_fn in STRATEGIES.items():
        tp = 0
        fp = 0
        fn = 0

        for k in norm_exp:
            val1 = norm_exp[k]
            val2 = norm_pred[k]
            raw = match_fn(val1, val2)

            if isinstance(raw, list):
                score = float(raw[0])
            elif isinstance(raw, bool):
                score = 1.0 if raw else 0.0
            else:
                score = float(raw)

            if val1:  
                if score >= seuil:
                    tp += 1
                else:
                    fn += 1
            else:
                if val2: 
                    fp += 1

        metrics = compute_metrics(tp, fp, fn)
        results[f"{strat_name}"] = round(metrics["f1"], 3)

    return results

def compare_list_of_strings(list1, list2, seuil=0.8):
    """
    Compare deux listes de chaînes de caractères, en utilisant STRATEGIES.
    Renvoie un dictionnaire contenant les F1-scores pour chaque stratégie.
    """

    scores = {}
    norm1 = [s.strip().lower() for s in list1 if s.strip()]
    norm2 = [s.strip().lower() for s in list2 if s.strip()]

    for name, fn in STRATEGIES.items():
        matched_1 = set()
        matched_2 = set()

        for i, val1 in enumerate(norm1):
            best_score = 0.0
            best_j = None
            for j, val2 in enumerate(norm2):
                raw_score = fn(val1, val2)
                score = (
                    float(raw_score[0]) if isinstance(raw_score, list)
                    else float(raw_score) if not isinstance(raw_score, bool)
                    else 1.0 if raw_score else 0.0
                )
                if score > best_score:
                    best_score = score
                    best_j = j

            if best_score >= seuil and best_j is not None:
                matched_1.add(i)
                matched_2.add(best_j)

        tp = len(matched_1)
        fp = len(norm2) - tp
        fn = len(norm1) - tp
        metrics = compute_metrics(tp, fp, fn)
        scores[f"{name}"] = round(metrics["f1"], 3)

    return scores

def compare_structured_fields(pred_list, exp_list, seuil=0.8):
    """
    Compare deux listes d’objets structurés (comme authors, bibliographies).
    Calcule un F1-score par champ + un F1 global sur les objets entiers.
    """

    all_fields = set()
    for d in pred_list + exp_list:
        all_fields.update(d.keys())
    champs =sorted(all_fields)

    # Initialiser les compteurs pour chaque champ
    field_matches = {champ: 0 for champ in champs}
    field_totals_exp = {champ: 0 for champ in champs}
    field_totals_pred = {champ: 0 for champ in champs}

    scores = {}            


    for strat_name, match_fn in STRATEGIES.items():
        # Pour le score global
        matched_pred = set()
        matched_exp = set()

        for i, exp in enumerate(exp_list):
            for j, pred in enumerate(pred_list):
                if j in matched_pred:
                    continue

                all_fields_match = True
                for champ in champs:
                    val_exp = str(exp.get(champ, "")).strip().lower()
                    val_pred = str(pred.get(champ, "")).strip().lower()

                    if val_exp:
                        field_totals_exp[champ] += 1
                    if val_pred:
                        field_totals_pred[champ] += 1

                    raw_score = match_fn(val_exp, val_pred)
                    if isinstance(raw_score, list):
                        score = float(raw_score[0])
                    elif isinstance(raw_score, bool):
                        score = 1.0 if raw_score else 0.0
                    else:
                        score = float(raw_score)

                    if score <= 0.8:
                        all_fields_match = False
                    elif val_exp:
                        # On ne compte match que s'il y avait bien une valeur attendue
                        field_matches[champ] += 1

                if all_fields_match:
                    matched_pred.add(j)
                    matched_exp.add(i)
                    break
        # F1 global sur l’objet entier
        tp = len(matched_exp)
        fp = len(pred_list) - len(matched_pred)
        fn = len(exp_list) - len(matched_exp)

        print(f"[{strat_name}] tp: {tp}, fp: {fp}, fn: {fn}")
        metrics = compute_metrics(tp, fp, fn)
        print(f"[{strat_name}] metrics: {metrics}")

        scores[strat_name] = round(metrics["f1"], 3)

    return scores

def compare_simple(text1: str, text2: str) -> dict:
    """
    Compare deux chaînes de caractères avec plusieurs stratégies (strict, soft, levenshtein).
    Retourne un score unique entre 0 et 1 par stratégie.
    - Si les deux textes sont vides : score = 0
    - Si l’un est vide et pas l’autre : score = 0
    - Sinon : application des fonctions de similarité
    """
    scores = {}

    if not text1 or not text2:
        for strat_name in STRATEGIES:
            scores[strat_name] = 0.0
        return scores

    norm1 = normalize_text(text1)
    #print(norm1)
    norm2 = normalize_text(text2)
    #print(norm2)
    for strat_name, strat_fn in STRATEGIES.items():
        print(strat_fn)
        print(strat_name)
        try:
            score = strat_fn(norm1, norm2)
            #print(score)
            print(f"  Résultat brut : {score} (type: {type(score)})")
            scores[strat_name] = round(float(score), 3)
            print(scores[strat_name])
        except Exception:
            scores[strat_name] = 0.0
    print(scores)
    return scores

def compare_raw_bibliographies(erudit_bib, grobid_bib):
    erudit_refs = [ref.get("raw_reference", "").strip() for ref in erudit_bib if "raw_reference" in ref]
    grobid_refs = [ref.get("raw_reference", "").strip() for ref in grobid_bib if "raw_reference" in ref]
    return compare_list_of_strings(erudit_refs, grobid_refs)


FIELD_COMPARISON_FUNCTIONS = {
    # champs simples (string) -- similar score
    "title": compare_simple,
    "subtitle": compare_simple,
    "abstract": compare_simple,
    "language": compare_simple,
    "date": compare_simple,
    "issue_number": compare_simple,
    "volume": compare_simple,
    "acknowledgements": compare_simple,

     #structured --f1
    "authors": compare_structured_fields, 
    "editorial_team": compare_structured_fields,
    "body": compare_structured_fields,
    "tables": compare_structured_fields,
    "figures": compare_structured_fields,

    #list of strings --f1
    "keywords" : compare_list_of_strings,
    "themes": compare_list_of_strings,
    "annexes": compare_list_of_strings, 
    "biographical_notes": compare_list_of_strings,

    "id": compare_dict_of_strings,
    "pagination": compare_dict_of_strings, 
    "rights": compare_dict_of_strings, 

    "bibliographies": compare_raw_bibliographies,
}



def evaluate_fields_from_json(source, target, fields_to_compare):
    results = {}
    for field in fields_to_compare:
        val1 = source.get(field)
        val2 = target.get(field)

        func = FIELD_COMPARISON_FUNCTIONS.get(field, compare_simple)

        start = time.perf_counter()  # début du chronométrage

    
        results[field] = func(val1, val2)
        print(results[field])
        end = time.perf_counter()
        duration = round(end - start, 3)

        print(f"Champ '{field}' évalué en {duration} secondes")
        #print("ok")
    return results

def evaluate(source: str, target: str, article_id: str):
    source_data = load_json(source, article_id)
    target_data = load_json(target, article_id)
    results = evaluate_fields_from_json(source_data, target_data, FIELD_COMPARISON_FUNCTIONS)
    print('finish evaluation')
    save_to_csv(target, article_id, results)

"""
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", required=True, help="ID de l'article")
    parser.add_argument("--source", required=True, help="Nom de la source de vérité (ex: erudit)")
    parser.add_argument("--target", required=True, help="Nom de l'outil à évaluer (ex: grobid)")
    args = parser.parse_args()

    source_data = load_json(args.source, args.id)
    target_data = load_json(args.target, args.id)

    # Compare chaque champ selon la logique associée
    #results = evaluate_fields_from_json(source_data, target_data)
    results = evaluate_fields_from_json(source_data, target_data, FIELD_COMPARISON_FUNCTIONS)
    print('finish evaluation')
    # Enregistre le résultat
    save_to_csv(args.target, args.id, results)

if __name__ == "__main__":
    main()
# PYTHONPATH=. python3 -m evaluation.evaluation --id 029574ar_2 --source erudit --target grobid

"""















