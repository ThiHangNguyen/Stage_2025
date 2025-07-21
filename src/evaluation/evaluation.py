from utils.io import has_data, load_json, save_to_csv
from utils.hashmap import hashmap
from evaluation.strategies.strict import strict_match
from evaluation.strategies.soft import soft_match
from evaluation.strategies.levenshtein import levenshtein_match
from evaluation.metrics.metrics import compute_metrics
import time  

STRATEGIES = {
    "strict": strict_match,
    "soft": soft_match, #matchesequence 
    "levenshtein": levenshtein_match,
}

def compare_dict_of_strings(exp_dict, pred_dict, seuil=0.8):
    """
    Compare deux dictionnaires simples (ex: id, pagination, rights),
    en appliquant des similarités sur chaque champ,
    et en calculant un F1 global.
    """

    results = {}

    for strat_name, match_fn in STRATEGIES.items():
        tp = 0
        fp = 0
        fn = 0
        for k in exp_dict:
            val1 = exp_dict[k]
            val2 = pred_dict[k]
            if not val1 and not val2:
                score = 0.0
            else:
                raw = match_fn(val1, val2)

                if isinstance(raw, list):
                    score = float(raw[0])
                elif isinstance(raw, bool):
                    score = 1.0 if raw else 0.0
                else:
                    score = float(raw)

                if score >= seuil:
                    tp += 1
                            
        fn = len(exp_dict) - tp
        fp = len(pred_dict) - tp
        metrics = compute_metrics(tp, fp, fn)
        results[f"{strat_name}"] = round(metrics["f1"], 3)

    return results

def compare_list_of_strings(list1, list2, seuil=0.8):
    """
    Compare deux listes de chaînes de caractères, en utilisant STRATEGIES.
    Renvoie un dictionnaire contenant les F1-scores pour chaque stratégie.
    """
    scores = {}

    for name, fn in STRATEGIES.items():
        matched_1 = set()
        matched_2 = set()

        for i, val1 in enumerate(list1):
            best_score = 0.0
            best_j = None
            for j, val2 in enumerate(list2):
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
        fp = len(list2) - tp
        fn = len(list1) - tp
        metrics = compute_metrics(tp, fp, fn)
        scores[f"{name}"] = round(metrics["f1"], 3)

    return scores

def compare_structured_fields(pred_list, exp_list, type_: str = "", seuil=0.8):
    """
    Compare deux listes d’objets structurés (comme authors, bibliographies).
    Calcule un F1-score par champ + un F1 global sur les objets entiers.
    Utilise une correspondance basée sur des clés générées via STRUCTURED_KEYS.
    """

    scores = {}
    exp_map = hashmap(exp_list, type_)
    pred_map = hashmap(pred_list, type_)
    for strat_name, match_fn in STRATEGIES.items():
        matched_pred_keys = set()
        tp, fp, fn = 0, 0, 0
        
        for key, exp_obj in exp_map.items():
            pred_obj = pred_map.get(key)
            if pred_obj:
                all_match = True
                for field in exp_obj:
                    val_exp = str(exp_obj.get(field, "")).strip().lower()
                    val_pred = str(pred_obj.get(field, "")).strip().lower()
                    if not val_exp and not val_pred:
                        score = 0
                        continue
                    else: 
                        score = match_fn(val_exp, val_pred)
                        if isinstance(score, list):
                            score = float(score[0])
                        elif isinstance(score, bool):
                            score = 1.0 if score else 0.0
                        else:
                            score = float(score)
                        #print(score)
                        if score <= seuil:
                            all_match = False
                            break

                if all_match:
                    tp += 1
                    matched_pred_keys.add(key)

        unmatched_pred = set(pred_map.keys()) - matched_pred_keys
        fp = len(unmatched_pred)
        fn = len(pred_list) - tp
        metrics = compute_metrics(tp, fp, fn)
        #print(f"[{strat_name}] metrics: {metrics}")
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

    for strat_name, strat_fn in STRATEGIES.items():
        try:
            score = strat_fn(text1, text2)
            #print(score)
            #print(f"  Résultat brut : {score} (type: {type(score)})")
            scores[strat_name] = round(float(score), 3)
        except Exception:
            scores[strat_name] = 0.0
    return scores

def compare_raw_bibliographies(erudit_bib, grobid_bib):
    erudit_refs = [ref.get("raw_reference", "").strip() for ref in erudit_bib if "raw_reference" in ref]
    grobid_refs = [ref.get("raw_reference", "").strip() for ref in grobid_bib if "raw_reference" in ref]
    return compare_list_of_strings(erudit_refs, grobid_refs)


FIELD_COMPARISON_FUNCTIONS = {
    # champs simples (string) -- similar score
    "title": compare_simple,
    "overline": compare_simple,
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
    "biographical_notes": compare_list_of_strings,

    "id": compare_dict_of_strings,
    "pagination": compare_dict_of_strings, 
    "rights": compare_dict_of_strings, 

    "bibliographies": compare_raw_bibliographies,
}



def evaluate_fields_from_json(source, target, fields_to_compare):
    results = {}
    presence_flags = {} 
    for field in fields_to_compare:
        val1 = source.get(field)
        val2 = target.get(field)
        has_ref = int(has_data(val1))
        has_extractor = int(has_data(val2))

        results[field] = {
            "has_ref": has_ref,
            "has_extractor": has_extractor,
        }
        func = FIELD_COMPARISON_FUNCTIONS.get(field, compare_simple)

        # Gestion des cas structurés nécessitant un type
        if field in {"authors", "editorial_team", "body", "tables", "figures"}:
            # Appel explicite avec le paramètre type_
            start = time.perf_counter()
            scores = compare_structured_fields(val1, val2, type_=field)
            end = time.perf_counter()

        else:
            # Cas normal sans type_
            start = time.perf_counter()
            scores = func(val1, val2)
            end = time.perf_counter()
        duration = round(end - start, 3)

        print(f"Champ '{field}' évalué en {duration} secondes")
        results[field].update(scores)

    return results


def evaluate(source: str, target: str, article_id: str, subfolder: str = None):
    """
    Évalue un article donné entre deux outils (source et target),
    en comparant leurs fichiers JSON transformés.

    Args:
        source (str): Nom de l'outil source (ex: "erudit").
        target (str): Nom de l'outil cible (ex: "grobid").
        article_id (str): Identifiant de l'article.
        subfolder (str, optional): Sous-répertoire dans data/processed/<tool>/ (ex: "xml_2cols").
    """
    source_data = load_json(source, article_id, subfolder=subfolder)
    target_data = load_json(target, article_id, subfolder=subfolder)

    print("commencer l'evaluation")

    results = evaluate_fields_from_json(source_data, target_data, FIELD_COMPARISON_FUNCTIONS)
    print(f"[INFO] Évaluation terminée pour {article_id}")
    #print(results)

    save_to_csv(target, article_id, results, output_subfolder=subfolder)
    print("Résultats enregistrés")















