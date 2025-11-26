"""
Email extraction utilities for job listings.
"""

import re
from typing import Optional


def extract_email(text: str) -> Optional[str]:
    """
    Extract the first email address from text.
    
    Args:
        text: Text to search for email addresses
        
    Returns:
        First email address found, or None if no email found
    """
    if not text:
        return None
    
    # Comprehensive email regex pattern
    # Matches most common email formats
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    
    matches = re.findall(email_pattern, text)
    
    if matches:
        # Return the first email found
        return matches[0]
    
    return None


def extract_all_emails(text: str) -> list:
    """
    Extract all email addresses from text.
    
    Args:
        text: Text to search for email addresses
        
    Returns:
        List of all email addresses found (may be empty)
    """
    if not text:
        return []
    
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    
    matches = re.findall(email_pattern, text)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_emails = []
    for email in matches:
        if email.lower() not in seen:
            seen.add(email.lower())
            unique_emails.append(email)
    
    return unique_emails
