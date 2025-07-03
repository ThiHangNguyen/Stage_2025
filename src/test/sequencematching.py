import difflib
from typing import Union, Sequence

def fuzzy_compare(s1: str, s2: str, *, autojunk: bool = False) -> float:
    """
    Compute the similarity ratio between two strings using difflib.SequenceMatcher.
    
    Args:
        s1: First string.
        s2: Second string.
        autojunk: Automatically ignore certain junk elements (like blank lines in text)
    
    Returns:
        A float between 0 and 1 indicating the similarity (1 = identical).
    """
    matcher = difflib.SequenceMatcher(None, s1, s2, autojunk=autojunk)
    return matcher.ratio()

def get_matching_blocks(s1: str, s2: str) -> list:
    """
    Get the matching blocks between two strings.
    
    Args:
        s1: First string.
        s2: Second string.
        
    Returns:
        List of matching blocks as (i, j, n) tuples where i is the index in s1,
        j is the index in s2, and n is the length of the match.
    """
    matcher = difflib.SequenceMatcher(None, s1, s2)
    return matcher.get_matching_blocks()

# Example usage
string_a = "SecureDataProcessing"
string_b = "SecureDataProcess"
similarity_ratio = fuzzy_compare(string_a, string_b)
print(f"Similarity ratio: {similarity_ratio:.4f}")

# Get matching blocks
matches = get_matching_blocks(string_a, string_b)
print("Matching blocks:")
for i, j, n in matches:
    if n > 0:  # Skip the last match which is always (len(s1), len(s2), 0)
        print(f"  Match of length {n} at position {i} in string_a and {j} in string_b")