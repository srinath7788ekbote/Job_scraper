"""
Centralized logging configuration for the job scraper.

Provides consistent logging setup across all scraper modules.
"""

import logging
import sys
from typing import Optional


def setup_logger(
    name: str,
    level: int = logging.INFO,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Set up a logger with consistent formatting.
    
    Args:
        name: Logger name (typically __name__ from calling module)
        level: Logging level (default: INFO)
        format_string: Custom format string (optional)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only configure if not already configured
    if not logger.handlers:
        logger.setLevel(level)
        
        # Create console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        
        # Set format
        if format_string is None:
            format_string = '%(asctime)s - %(levelname)s - [%(name)s] %(message)s'
        
        formatter = logging.Formatter(
            format_string,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with default configuration.
    
    Args:
        name: Logger name (typically __name__ from calling module)
        
    Returns:
        Configured logger instance
    """
    return setup_logger(name)


# Logging helper functions for common patterns
def log_scraper_start(logger: logging.Logger, platform: str, keyword: str, location: str, days: int, limit: int):
    """Log the start of a scraping operation."""
    logger.info(f"Scraping {platform} for {keyword} in {location} (Last {days} days, Limit: {limit})")


def log_scraper_progress(logger: logging.Logger, platform: str, current: int, total: int, item_type: str = "items"):
    """Log progress during scraping."""
    logger.info(f"✓ Processed {current}/{total} {platform} {item_type}")


def log_scraper_complete(logger: logging.Logger, platform: str, count: int, location: str):
    """Log completion of scraping operation."""
    logger.info(f"✓ {platform}: Found {count} jobs in {location}")


def log_scraper_error(logger: logging.Logger, platform: str, error: Exception, context: str = ""):
    """Log an error during scraping."""
    if context:
        logger.error(f"Error in {platform} - {context}: {error}")
    else:
        logger.error(f"Error in {platform}: {error}")
