from difflib import SequenceMatcher
from utils.io import normalize_text

from difflib import SequenceMatcher
def soft_match(a, b):
    if not isinstance(a, str):
        a = str(a)
    if not isinstance(b, str):
        b = str(b)
    return SequenceMatcher(None, a, b).ratio()

"""
def soft_match(guess, truth):
    g = normalize_text(guess) if guess else ""
    t = normalize_text(truth) if truth else ""
    ratio = SequenceMatcher(None, g, t).ratio()  # valeur entre 0 et 1
    return [ratio]  # score continu
"""