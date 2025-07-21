from difflib import SequenceMatcher

def soft_match(a, b):
    """
    Calcule une similarité floue (entre 0 et 1) entre deux chaînes de caractères.

    Paramètres :a, b sont des chaines de caractères
    Retour :
    - float : un score de similarité basé sur l’algorithme de Ratcliff/Obershelp (utilisé par SequenceMatcher).
    1.0 signifie égalité parfaite, 
    0.0 signifie aucune similarité.

    """

    if not isinstance(a, str):
        a = str(a)
    if not isinstance(b, str):
        b = str(b)
    return SequenceMatcher(None, a, b).ratio()

