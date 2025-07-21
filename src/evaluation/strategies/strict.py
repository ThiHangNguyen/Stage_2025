
"""
def strict_match(guess, truth):
    if not guess and not truth:
        return [True]

    if isinstance(guess, list):
        guess = " ".join(map(str, guess))
    elif isinstance(guess, dict):
        guess = str(guess)

    if isinstance(truth, list):
        truth = " ".join(map(str, truth))
    elif isinstance(truth, dict):
        truth = str(truth)

    return [guess == truth]

"""
def strict_match(guess, truth):
    """
    Retourne 1 si guess == truth, sinon 0 (évaluation stricte).
    Les listes et dictionnaires sont convertis en chaînes.
    """
    if not guess and not truth:
        return 1

    if isinstance(guess, list):
        guess = " ".join(map(str, guess))
    elif isinstance(guess, dict):
        guess = str(guess)

    if isinstance(truth, list):
        truth = " ".join(map(str, truth))
    elif isinstance(truth, dict):
        truth = str(truth)

    return int(guess == truth)
