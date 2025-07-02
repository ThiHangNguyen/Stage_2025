def support(match_result) -> int:
    """
    Retourne 1 si une comparaison a été faite (même si incorrecte), 0 sinon.
    """
    return 1 if match_result is not None and match_result != "" else 0
