def compute(matches: list[float], truths: list[int]) -> float:
    true_positives = sum(1 for match, truth in zip(matches, truths) if match >= 0.5 and truth == 1)
    predicted_positives = sum(1 for match in matches if match >= 0.5)
    if predicted_positives == 0:
        return 0.0
    return true_positives / predicted_positives
