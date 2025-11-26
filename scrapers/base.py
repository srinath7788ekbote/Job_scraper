"""
Base classes and data structures for job scrapers.

Defines the common interface that all platform-specific scrapers must implement.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class JobListing:
    """
    Data structure representing a job listing.
    
    Attributes:
        title: Job title
        company: Company name
        location: Job location
        url: URL to the job posting
        platform: Platform where the job was found (e.g., "LinkedIn", "Glassdoor")
        description: Full job description text
        key_responsibilities: Extracted key responsibilities
        skills: Required skills
        years_of_experience: Required years of experience
        posted_date: Date when the job was posted (ISO format: YYYY-MM-DD)
        email: Contact email address if provided in the job listing
    """
    title: str
    company: str
    location: str
    url: str
    platform: str
    description: Optional[str] = None
    key_responsibilities: Optional[str] = None
    skills: Optional[str] = None
    years_of_experience: Optional[str] = None
    posted_date: Optional[str] = None
    email: Optional[str] = None


class JobScraper(ABC):
    """
    Abstract base class for job scrapers.
    
    All platform-specific scrapers must inherit from this class and implement
    the required abstract methods.
    """
    
    def __init__(self):
        """Initialize the scraper."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @classmethod
    @abstractmethod
    def get_platform_name(cls) -> str:
        """
        Get the name of the platform this scraper targets.
        
        Returns:
            Platform name (e.g., "LinkedIn", "Glassdoor", "Naukri")
        """
        pass
    
    @abstractmethod
    def scrape(
        self,
        keyword: str,
        location: str,
        limit: int = 100,
        days: int = 7
    ) -> List[JobListing]:
        """
        Scrape jobs for a given keyword and location.
        
        Args:
            keyword: Job search keyword (e.g., "SRE", "DevOps Engineer")
            location: Location to search in (e.g., "Berlin", "US", "India")
            limit: Maximum number of jobs to scrape (default: 100)
            days: Number of days to look back (default: 7)
                  days=1 means last 24 hours
                  days=7 means last 7 days
        
        Returns:
            List of JobListing objects
            
        Raises:
            ScraperConfigError: If configuration is invalid
            ScraperNetworkError: If network errors occur
            ScraperParseError: If parsing fails
        """
        pass
    
    def validate_config(self, keyword: str, location: str, limit: int, days: int) -> None:
        """
        Validate scraper configuration parameters.
        
        Args:
            keyword: Job search keyword
            location: Location to search in
            limit: Maximum number of jobs
            days: Number of days to look back
            
        Raises:
            ScraperConfigError: If any parameter is invalid
        """
        from utils.exceptions import ScraperConfigError
        
        if not keyword or not keyword.strip():
            raise ScraperConfigError("Keyword cannot be empty")
        
        if not location or not location.strip():
            raise ScraperConfigError("Location cannot be empty")
        
        if limit <= 0:
            raise ScraperConfigError(f"Limit must be positive, got {limit}")
        
        if days <= 0:
            raise ScraperConfigError(f"Days must be positive, got {days}")
        
        self.logger.debug(f"Configuration validated: keyword={keyword}, location={location}, limit={limit}, days={days}")

