def detect_intent(query: str):
    q = query.lower()
    if "where" in q and "implement" in q:
        return "find_implementation"
    return "general"
