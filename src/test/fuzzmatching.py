from thefuzz import fuzz, process
import difflib
import Levenshtein 
def fuzzy_ratio(string1: str, string2: str) -> int:
    """
    Calculate similarity between two strings using Levenshtein distance.
    
    Args:
        string1: First string
        string2: Second string
        
    Returns:
        int: Similarity score between 0 and 100
    """
    return fuzz.ratio(string1, string2)

def fuzzy_partial_ratio(string1: str, string2: str) -> int:
    """
    Calculate partial similarity, helpful when one string is a substring of another.
    
    Args:
        string1: First string
        string2: Second string
        
    Returns:
        int: Partial similarity score between 0 and 100
    """
    return fuzz.partial_ratio(string1, string2)

def find_best_match(query: str, choices: list[str]) -> tuple[str, int]:
    """
    Find the best matching string from a list of choices.
    
    Args:
        query: String to search for
        choices: List of strings to search in
        
    Returns:
        tuple: (best_match, score)
    """
    return process.extractOne(query, choices)

# Example usage
string1 = "SecureDataProcessing"
string2 = "SecureDataProcess"
similarity = fuzzy_ratio(string1, string2)
print(f"Fuzzy similarity ratio: {similarity}")

levenshtein = Levenshtein.ratio(string1, string2)
print(f"levenshtein: {levenshtein}")

# Partial ratio example
partial_similarity = fuzzy_partial_ratio(string1, string2)
print(f"Fuzzy partial ratio: {partial_similarity}")

# Finding best match from multiple options
search_term = "DataProcess"
options = ["SecureDataProcessing", "DataProcessor", "SecureProcess", "ProcessData"]
best_match, score = find_best_match(search_term, options)
print(f"Best match for '{search_term}': '{best_match}' with score {score}")