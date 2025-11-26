import re

def parse_job_description(text: str) -> dict:
    """
    Parse the full job description to extract Key Responsibilities, Skills, and Years of Experience.
    Returns a dictionary with 'responsibilities', 'skills', and 'years_of_experience'.
    """
    if not text:
        return {"responsibilities": None, "skills": None, "years_of_experience": None}
    
    # Normalize text
    text_lower = text.lower()
    
    # Extract years of experience
    years_of_exp = None
    exp_patterns = [
        r'(\d+)\+?\s*(?:to|\-|–)\s*(\d+)\+?\s*years?',  # "3-5 years", "3 to 5 years"
        r'(\d+)\+\s*years?',  # "3+ years"
        r'minimum\s+of\s+(\d+)\+?\s*years?',  # "minimum of 3 years"
        r'at\s+least\s+(\d+)\+?\s*years?',  # "at least 3 years"
        r'(\d+)\s*years?\s+of\s+experience',  # "3 years of experience"
    ]
    
    for pattern in exp_patterns:
        match = re.search(pattern, text_lower)
        if match:
            if len(match.groups()) == 2:
                years_of_exp = f"{match.group(1)}-{match.group(2)} years"
            else:
                years_of_exp = f"{match.group(1)}+ years"
            break
    
    # Define patterns for sections
    resp_patterns = [
        r"(?:key )?responsibilities:?",
        r"what you(?:'ll| will) do:?",
        r"duties:?",
        r"role overview:?",
        r"job description:?"
    ]
    
    skill_patterns = [
        r"(?:required )?skills:?",
        r"qualifications:?",
        r"requirements:?",
        r"what we(?:'re| are) looking for:?",
        r"who you are:?",
        r"must haves?:?"
    ]
    
    # Helper to find section start
    def find_section_start(patterns, text_lower):
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                return match.start(), match.end()
        return -1, -1

    resp_start, resp_end_idx = find_section_start(resp_patterns, text_lower)
    skill_start, skill_end_idx = find_section_start(skill_patterns, text_lower)
    
    responsibilities = ""
    skills = ""
    
    # Extract based on which section comes first
    if resp_start != -1 and skill_start != -1:
        if resp_start < skill_start:
            responsibilities = text[resp_end_idx:skill_start].strip()
            skills = text[skill_end_idx:].strip()
        else:
            skills = text[skill_end_idx:resp_start].strip()
            responsibilities = text[resp_end_idx:].strip()
    elif resp_start != -1:
        responsibilities = text[resp_end_idx:].strip()
    elif skill_start != -1:
        skills = text[skill_end_idx:].strip()
        
    # Cleanup - limit length if too long or empty
    if len(responsibilities) > 2000:
        responsibilities = responsibilities[:2000] + "..."
    if len(skills) > 2000:
        skills = skills[:2000] + "..."
        
    return {
        "responsibilities": responsibilities if responsibilities else None,
        "skills": skills if skills else None,
        "years_of_experience": years_of_exp
    }
