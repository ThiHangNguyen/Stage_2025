
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

    # Éventuellement parser les dates 
    #guess = parse_date(guess)
    #truth = parse_date(truth)

    return [guess == truth]
