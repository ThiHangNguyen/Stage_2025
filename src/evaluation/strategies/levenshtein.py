import Levenshtein
def levenshtein_match(a, b):
    if not isinstance(a, str):
        a = str(a)
    if not isinstance(b, str):
        b = str(b)
    return Levenshtein.ratio(a, b)
