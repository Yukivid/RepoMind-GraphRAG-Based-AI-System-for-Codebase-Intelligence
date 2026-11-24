def symbol_match_score(symbol_name, file_path, query_terms):
    score = 0
    name = symbol_name.lower()
    path = file_path.lower()

    for t in query_terms:
        if t in name:
            score += 5
        if t in path:
            score += 3

    return score
