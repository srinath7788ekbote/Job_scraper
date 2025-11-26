"""
Custom exception classes for the job scraper.

These exceptions provide better error handling and debugging capabilities.
"""


class ScraperException(Exception):
    """Base exception for all scraper-related errors."""
    pass


class ScraperConfigError(ScraperException):
    """Raised when scraper configuration is invalid."""
    pass


class ScraperNetworkError(ScraperException):
    """Raised when network-related errors occur during scraping."""
    pass


class ScraperParseError(ScraperException):
    """Raised when HTML parsing fails or expected elements are not found."""
    pass


class ScraperRateLimitError(ScraperException):
    """Raised when rate limiting is detected."""
    pass


class ScraperTimeoutError(ScraperException):
    """Raised when a scraping operation times out."""
    pass
