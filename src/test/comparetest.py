import re
from typing import Optional, Pattern

def match_with_regex(pattern: str, text: str, *, is_full_match: bool = False) -> bool:
    """Match text against a regex pattern.
    
    Args:
        pattern: Regular expression pattern
        text: String to check
        is_full_match: If True, entire string must match pattern
        
    Returns:
        bool: True if match is found
    """
    if is_full_match:
        return bool(re.fullmatch(pattern, text))
    return bool(re.search(pattern, text))



# Example usage
data_text = "ID: SecureData123, Code: SecureData456, Token: SecureData789"

# Simple pattern matching
is_match = match_with_regex(r"SecureData\d{3}", "SecureData456")
print(f"Pattern matches: {is_match}")  # True


import Levenshtein
import difflib

# Tes chaînes à comparer
string1 = "la pandémie de covid-19 a propulsé, en quelques heures, les enseignants des hautes écoles belges vers un apprentissage 100 % à distance.en quoi un dispositif pédagogique implémentant des tic, en cours d'expérimentation a-t-il constitué un support pour des étudiants également contraints de s'adapter au contexte?l'analyse de cette expérience pointe les apports et les difficultés constatés.une fois les cheminements parcourus par les apprenants et l'enseignant mis à jour, des ingrédients incontournables apparaissent pour penser le développement numérique en enseignement : accompagnement des étudiants et des enseignants, innovation pédagogique et projet numérique à vision systémique."
string2 = "la pandémie de covid-19 a propulsé, en quelques heures, les enseignants des hautes écoles belges vers un apprentissage 100 % à distance. en quoi un dispositif pédagogique implémentant des tic, en cours d'expérimentation a-t-il constitué un support pour des étudiants également contraints de s'adapter au contexte? l'analyse de cette expérience pointe les apports et les difficultés constatés. une fois les cheminements parcourus par les apprenants et l'enseignant mis à jour, des ingrédients incontournables apparaissent pour penser le développement numérique en enseignement : accompagnement des étudiants et des enseignants, innovation pédagogique et projet numérique à vision systémique."

# --- Méthode 1 : Levenshtein.ratio() ---
levenshtein_similarity = Levenshtein.ratio(string1, string2)
print(f"Levenshtein similarity: {levenshtein_similarity:.4f}")

# --- Méthode 2 : difflib.SequenceMatcher ---
matcher = difflib.SequenceMatcher(None, string1, string2)
difflib_similarity = matcher.ratio()
print(f"difflib similarity: {difflib_similarity:.4f}")



