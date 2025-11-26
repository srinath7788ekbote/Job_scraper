"""
Concurrency configuration for the job scraper.

Defines default settings for threading and multiprocessing.
"""

import os
from dataclasses import dataclass


@dataclass
class ConcurrencyConfig:
    """Configuration for concurrent scraping operations."""
    
    # Threading configuration (for I/O-bound web scraping)
    thread_workers: int = 5
    
    # Multiprocessing configuration (for CPU-bound parsing)
    process_workers: int = max(1, os.cpu_count() - 1) if os.cpu_count() else 2
    
    # Rate limiting
    min_delay_seconds: float = 1.0
    max_delay_seconds: float = 3.0
    
    # Timeouts
    page_load_timeout: int = 60000  # milliseconds
    element_wait_timeout: int = 10000  # milliseconds
    
    # Retry configuration
    max_retries: int = 3
    retry_delay: float = 2.0
    retry_backoff_factor: float = 2.0  # Exponential backoff multiplier
    
    def get_retry_delay(self, attempt: int) -> float:
        """
        Calculate retry delay with exponential backoff.
        
        Args:
            attempt: Current retry attempt (0-indexed)
            
        Returns:
            Delay in seconds
        """
        return self.retry_delay * (self.retry_backoff_factor ** attempt)


# Default configuration instance
DEFAULT_CONFIG = ConcurrencyConfig()
