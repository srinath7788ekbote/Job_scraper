"""
Date parsing utilities for job scrapers.

Handles parsing of relative date strings (e.g., "Posted 2 days ago") 
into absolute dates for consistent storage.
"""

import re
from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def parse_relative_date(date_string: str) -> Optional[str]:
    """
    Parse a relative date string into an ISO format date.
    
    Args:
        date_string: Relative date string like "Posted 2 days ago", "Today", "1 week ago"
        
    Returns:
        ISO format date string (YYYY-MM-DD) or None if parsing fails
        
    Examples:
        >>> parse_relative_date("Posted 2 days ago")
        "2025-11-24"
        >>> parse_relative_date("Today")
        "2025-11-26"
        >>> parse_relative_date("1 week ago")
        "2025-11-19"
    """
    if not date_string:
        return None
    
    date_string_lower = date_string.lower().strip()
    current_date = datetime.now()
    
    # Handle "today" or "just now"
    if any(word in date_string_lower for word in ['today', 'just now', 'just posted']):
        return current_date.strftime('%Y-%m-%d')
    
    # Handle "yesterday"
    if 'yesterday' in date_string_lower:
        return (current_date - timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Handle "X hours ago"
    hours_match = re.search(r'(\d+)\s*(?:hour|hr)s?\s*ago', date_string_lower)
    if hours_match:
        hours = int(hours_match.group(1))
        if hours < 24:
            return current_date.strftime('%Y-%m-%d')
        else:
            days = hours // 24
            return (current_date - timedelta(days=days)).strftime('%Y-%m-%d')
    
    # Handle "X days ago"
    days_match = re.search(r'(\d+)\s*(?:day|d)s?\s*ago', date_string_lower)
    if days_match:
        days = int(days_match.group(1))
        return (current_date - timedelta(days=days)).strftime('%Y-%m-%d')
    
    # Handle "X weeks ago"
    weeks_match = re.search(r'(\d+)\s*(?:week|wk)s?\s*ago', date_string_lower)
    if weeks_match:
        weeks = int(weeks_match.group(1))
        return (current_date - timedelta(weeks=weeks)).strftime('%Y-%m-%d')
    
    # Handle "X months ago" (approximate as 30 days)
    months_match = re.search(r'(\d+)\s*(?:month|mo)s?\s*ago', date_string_lower)
    if months_match:
        months = int(months_match.group(1))
        return (current_date - timedelta(days=months * 30)).strftime('%Y-%m-%d')
    
    # Handle "over X days ago"
    over_days_match = re.search(r'over\s+(\d+)\s*(?:day|d)s?\s*ago', date_string_lower)
    if over_days_match:
        days = int(over_days_match.group(1))
        return (current_date - timedelta(days=days + 1)).strftime('%Y-%m-%d')
    
    # Handle "30+ days ago"
    plus_days_match = re.search(r'(\d+)\+\s*(?:day|d)s?\s*ago', date_string_lower)
    if plus_days_match:
        days = int(plus_days_match.group(1))
        return (current_date - timedelta(days=days)).strftime('%Y-%m-%d')
    
    # Try to parse absolute dates (YYYY-MM-DD, MM/DD/YYYY, etc.)
    absolute_patterns = [
        r'(\d{4})-(\d{2})-(\d{2})',  # YYYY-MM-DD
        r'(\d{2})/(\d{2})/(\d{4})',  # MM/DD/YYYY
        r'(\d{2})-(\d{2})-(\d{4})',  # DD-MM-YYYY
    ]
    
    for pattern in absolute_patterns:
        match = re.search(pattern, date_string)
        if match:
            try:
                # Try different date formats
                if pattern == r'(\d{4})-(\d{2})-(\d{2})':
                    year, month, day = match.groups()
                    parsed_date = datetime(int(year), int(month), int(day))
                elif pattern == r'(\d{2})/(\d{2})/(\d{4})':
                    month, day, year = match.groups()
                    parsed_date = datetime(int(year), int(month), int(day))
                else:  # DD-MM-YYYY
                    day, month, year = match.groups()
                    parsed_date = datetime(int(year), int(month), int(day))
                
                return parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                continue
    
    logger.debug(f"Could not parse date string: {date_string}")
    return None


def is_within_days(posted_date: Optional[str], days: int) -> bool:
    """
    Check if a posted date is within the specified number of days from now.
    
    Args:
        posted_date: ISO format date string (YYYY-MM-DD) or None
        days: Number of days to check against
        
    Returns:
        True if the date is within the specified days, False otherwise
        If posted_date is None, returns True (assume it's recent)
    """
    if not posted_date:
        # If we don't have a date, assume it's recent
        return True
    
    try:
        posted = datetime.strptime(posted_date, '%Y-%m-%d')
        current = datetime.now()
        days_diff = (current - posted).days
        
        return days_diff <= days
    except (ValueError, TypeError) as e:
        logger.debug(f"Error checking date range: {e}")
        return True  # Assume it's recent if we can't parse
