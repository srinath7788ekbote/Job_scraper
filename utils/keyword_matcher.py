def keyword_matches(title: str, keyword: str) -> bool:
    """
    Check if a job title matches the given keyword.
    Uses flexible matching to handle abbreviations and variations.
    """
    title_lower = title.lower()
    keyword_lower = keyword.lower()
    
    # Direct substring match
    if keyword_lower in title_lower:
        return True
    
    # Handle common abbreviations and variations
    keyword_variations = {
        'sre': ['site reliability engineer', 'site reliability', 'sre'],
        'devops': ['devops', 'dev ops', 'development operations'],
        'ml': ['machine learning', 'ml'],
        'ai': ['artificial intelligence', 'ai'],
        'qa': ['quality assurance', 'qa', 'quality engineer'],
        'ui': ['user interface', 'ui'],
        'ux': ['user experience', 'ux'],
    }
    
    # Check if keyword has known variations
    if keyword_lower in keyword_variations:
        for variation in keyword_variations[keyword_lower]:
            if variation in title_lower:
                return True
    
    # Check if any word in keyword appears in title
    keyword_words = keyword_lower.split()
    if len(keyword_words) > 1:
        # For multi-word keywords, check if all words appear (not necessarily together)
        if all(word in title_lower for word in keyword_words):
            return True
    
    return False
