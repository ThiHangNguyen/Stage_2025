def f1_score(results: list[bool]) -> float:
    if not results:
        return 0.0
    tp = sum(results)
    fp_fn = len(results) - tp
    if tp + 0.5 * fp_fn == 0:
        return 0.0
    return tp / (tp + 0.5 * fp_fn)
