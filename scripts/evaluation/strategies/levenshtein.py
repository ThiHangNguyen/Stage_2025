from Levenshtein import ratio
from utils.io import normalize_text

"""
def levenshtein_match(guess, truth, threshold=0.8):
    # Appliquer parse_date puis normalisation
    g = normalize_text(guess) if guess else ""
    t = normalize_text(truth) if truth else ""

    # Calculer le score de similarité Levenshtein
    score = ratio(g, t)

    # Retourne [True] si le score dépasse le seuil
    return [score >= threshold]
"""
import Levenshtein
def levenshtein_match(a, b):
    if not isinstance(a, str):
        a = str(a)
    if not isinstance(b, str):
        b = str(b)
    return Levenshtein.ratio(a, b)
