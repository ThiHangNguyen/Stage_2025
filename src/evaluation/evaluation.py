from utils.io import has_data, load_json, save_to_csv
from utils.hashmap import hashmap
from evaluation.strategies.strict import strict_match
from evaluation.strategies.soft import soft_match
from evaluation.strategies.levenshtein import levenshtein_match
from evaluation.metrics.metrics import compute_metrics
import time  

STRATEGIES = {
    #"strict": strict_match,
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


def compare_dict_of_strings(expected_dict, predicted_dict, seuil=0.8):
    """
    Compare deux dictionnaires simples champ par champ.
    Pour chaque stratégie :
    - calcule précision, rappel, F1, support via compute_metrics
    - calcule la similarité moyenne des champs matchés
    """

    results = {}

    for strat_name, match_fn in STRATEGIES.items():
        tp = 0
        similarity_scores = []

        for key in expected_dict:
            val_exp = expected_dict.get(key, "")
            val_pred = predicted_dict.get(key, "")

            if not val_exp and not val_pred:
                continue  # ignorer les deux vides (ni TP ni FP)

            raw_score = match_fn(val_exp, val_pred)

            score = (
                float(raw_score[0]) if isinstance(raw_score, list)
                else float(raw_score) if not isinstance(raw_score, bool)
                else 1.0 if raw_score else 0.0
            )

            if score >= seuil:
                tp += 1
                similarity_scores.append(score)

        fn = len(expected_dict) - tp
        fp = len(predicted_dict) - tp
        metrics = compute_metrics(tp, fp, fn)
        avg_similarity = round(sum(similarity_scores) / len(similarity_scores), 3) if similarity_scores else 0.0

        results[strat_name] = {
            "precision": metrics["precision"],
            "recall": metrics["recall"],
            "avg_similarity": avg_similarity
        }

    return results



def compare_list_of_strings(predicted_list, expected_list, seuil=0.8):
    """
    Compare deux listes de chaînes de caractères :
    - predicted_list : la liste générée ex par GROBID (à évaluer)
    - expected_list  : la vérité de terrain (Érudit)
    
    Pour chaque stratégie de STRATEGIES :
    - aligne les éléments avec meilleure similarité ≥ seuil (1-to-1)
    - calcule précision, rappel, F1 via compute_metrics
    - calcule la similarité moyenne des appariements
    """

    scores = {}

    for name, fn in STRATEGIES.items():
        matched_pred = set()
        matched_exp = set()
        similarity_scores = []

        for i, val_pred in enumerate(predicted_list):
            best_score = 0.0
            best_j = None
            for j, val_exp in enumerate(expected_list):
                if j in matched_exp:
                    continue  # déjà utilisé

                raw_score = fn(val_pred, val_exp)
                score = (
                    float(raw_score[0]) if isinstance(raw_score, list)
                    else float(raw_score) if not isinstance(raw_score, bool)
                    else 1.0 if raw_score else 0.0
                )

                if score > best_score:
                    best_score = score
                    best_j = j

            if best_score >= seuil and best_j is not None:
                matched_pred.add(i)
                matched_exp.add(best_j)
                similarity_scores.append(best_score)

        tp = len(matched_pred)
        fp = len(predicted_list) - tp
        fn = len(expected_list) - tp
        metrics = compute_metrics(tp, fp, fn)
        avg_similarity = round(sum(similarity_scores) / len(expected_list), 3) if similarity_scores else 0.0

        scores[name] = {
            "precision": metrics["precision"],
            "recall": metrics["recall"],
            "avg_similarity": avg_similarity
        }

    return scores



def compare_structured_fields(pred_list, exp_list, type_: str = "", seuil=0.8):
    """
    Compare deux listes d’objets structurés.
    Pour chaque prédiction (GROBID), cherche le meilleur match dans la référence (Érudit).
    Utilise une similarité de clé ≥ seuil pour aligner.
    Calcule les métriques via compute_metrics.
    Retourne : précision, rappel, support, et similarité moyenne des objets prédits correctement.
    """

    scores = {}
    exp_map = hashmap(exp_list, type_)
    pred_map = hashmap(pred_list, type_)

    for strat_name, match_fn in STRATEGIES.items():
        matched_exp_keys = set()
        tp, fp, fn = 0, 0, 0
        obj_similarities = []

        for pred_key, pred_obj in pred_map.items():
            best_match_key = None
            best_key_score = 0.0

            for exp_key in exp_map:
                if exp_key in matched_exp_keys:
                    continue

                key_score = match_fn(pred_key, exp_key)
                if isinstance(key_score, list):
                    key_score = float(key_score[0])
                elif isinstance(key_score, bool):
                    key_score = 1.0 if key_score else 0.0
                else:
                    key_score = float(key_score)

                if key_score >= seuil and key_score > best_key_score:
                    best_match_key = exp_key
                    best_key_score = key_score

            if best_match_key:
                tp += 1
                matched_exp_keys.add(best_match_key)

                exp_obj = exp_map[best_match_key]
                field_scores = []

                for field in exp_obj:
                    val_exp = str(exp_obj.get(field, "")).strip().lower()
                    if not val_exp:
                        continue
                    val_pred = str(pred_obj.get(field, "")).strip().lower()

                    score = match_fn(val_exp, val_pred)
                    if isinstance(score, list):
                        score = float(score[0])
                    elif isinstance(score, bool):
                        score = 1.0 if score else 0.0
                    else:
                        score = float(score)

                    field_scores.append(score)

                if field_scores:
                    obj_score = sum(field_scores) / len(field_scores)

                    if type_ == "tables":
                        ct_ref = exp_obj.get("content", None)
                        if not has_data(ct_ref):
                            continue
                    obj_similarities.append(obj_score)

        fp = len(pred_list) - tp
        fn = len(exp_list) - tp

        metrics = compute_metrics(tp, fp, fn)
        avg_similarity = round(sum(obj_similarities) / len(obj_similarities), 3) if obj_similarities else 0.0

        scores[strat_name] = {
            "precision": metrics["precision"],
            "recall": metrics["recall"],
            "avg_similarity": avg_similarity
        }

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
    # "overline": compare_simple,
    # "subtitle": compare_simple,
    "abstract": compare_simple,
    "language": compare_simple,
    "date": compare_simple,
    "issue_number": compare_simple,
    "volume": compare_simple,
    "acknowledgements": compare_simple,

     #structured --f1
    "authors": compare_structured_fields, 
    #"editorial_team": compare_structured_fields,
    "tables": compare_structured_fields,
    "figures": compare_structured_fields,

    #list of strings --f1
    "keywords" : compare_list_of_strings,
    "themes": compare_list_of_strings,
    #"biographical_notes": compare_list_of_strings,
    "section_titles": compare_list_of_strings,
    "content_tables": compare_list_of_strings,

    "bibliographies": compare_list_of_strings,


    "id": compare_dict_of_strings,
    "pagination": compare_dict_of_strings, 
    "rights": compare_dict_of_strings, 

}



def evaluate_fields_from_json(source, target, fields_to_compare):
    results = {}
    presence_flags = {} 
    for field in fields_to_compare:
        val1 = source.get(field)
        val2 = target.get(field)
        has_ref = int(has_data(val2))
        has_extractor = int(has_data(val1))

        results[field] = {
            "has_ref": has_ref,
            "has_extractor": has_extractor,
        }
        func = FIELD_COMPARISON_FUNCTIONS.get(field, compare_simple)

        # Gestion des cas structurés nécessitant un type
        if field in {"authors", "editorial_team", "tables", "figures"}:
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

    save_to_csv(source, article_id, results, output_subfolder=subfolder)
    print("Résultats enregistrés")















