def compute_metrics(tp: int, fp: int, fn: int) -> dict:
    """
    Calcule précision, rappel, F1-score à partir des vrais positifs, faux positifs, faux négatifs.
    """
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    return {
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "support": tp + fn  # nombre d'éléments attendus
    }
