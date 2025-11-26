"""
Scraper registry for managing available job scrapers.

Provides a factory pattern for easy addition and discovery of new scrapers.
"""

from typing import Dict, Type, List
import logging
from scrapers.base import JobScraper

logger = logging.getLogger(__name__)


class ScraperRegistry:
    """
    Registry for managing available job scrapers.
    
    Provides a centralized way to register and retrieve scrapers.
    """
    
    _scrapers: Dict[str, Type[JobScraper]] = {}
    
    @classmethod
    def register(cls, scraper_class: Type[JobScraper]) -> None:
        """
        Register a scraper class.
        
        Args:
            scraper_class: Scraper class to register (must inherit from JobScraper)
            
        Raises:
            ValueError: If scraper_class is not a valid JobScraper subclass
        """
        if not issubclass(scraper_class, JobScraper):
            raise ValueError(f"{scraper_class.__name__} must inherit from JobScraper")
        
        platform_name = scraper_class.get_platform_name().lower()
        cls._scrapers[platform_name] = scraper_class
        logger.debug(f"Registered scraper: {platform_name} -> {scraper_class.__name__}")
    
    @classmethod
    def get(cls, platform_name: str) -> Type[JobScraper]:
        """
        Get a scraper class by platform name.
        
        Args:
            platform_name: Name of the platform (case-insensitive)
            
        Returns:
            Scraper class
            
        Raises:
            KeyError: If platform is not registered
        """
        platform_key = platform_name.lower()
        if platform_key not in cls._scrapers:
            available = ", ".join(cls._scrapers.keys())
            raise KeyError(f"Unknown platform: {platform_name}. Available: {available}")
        
        return cls._scrapers[platform_key]
    
    @classmethod
    def get_all(cls) -> Dict[str, Type[JobScraper]]:
        """
        Get all registered scrapers.
        
        Returns:
            Dictionary mapping platform names to scraper classes
        """
        return cls._scrapers.copy()
    
    @classmethod
    def get_available_platforms(cls) -> List[str]:
        """
        Get list of available platform names.
        
        Returns:
            List of platform names
        """
        return list(cls._scrapers.keys())
    
    @classmethod
    def create_scraper(cls, platform_name: str) -> JobScraper:
        """
        Create a scraper instance for the given platform.
        
        Args:
            platform_name: Name of the platform
            
        Returns:
            Scraper instance
            
        Raises:
            KeyError: If platform is not registered
        """
        scraper_class = cls.get(platform_name)
        return scraper_class()


# Auto-register scrapers when they are imported
def auto_register_scrapers():
    """
    Automatically register all available scrapers.
    
    This function imports all scraper modules and registers them.
    """
    try:
        from scrapers.linkedin import LinkedinScraper
        ScraperRegistry.register(LinkedinScraper)
    except ImportError as e:
        logger.warning(f"Could not import LinkedinScraper: {e}")
    
    try:
        from scrapers.glassdoor import GlassdoorScraper
        ScraperRegistry.register(GlassdoorScraper)
    except ImportError as e:
        logger.warning(f"Could not import GlassdoorScraper: {e}")
    
    try:
        from scrapers.naukri import NaukriScraper
        ScraperRegistry.register(NaukriScraper)
    except ImportError as e:
        logger.warning(f"Could not import NaukriScraper: {e}")
    
    logger.info(f"Registered {len(ScraperRegistry.get_available_platforms())} scrapers: {', '.join(ScraperRegistry.get_available_platforms())}")


# Initialize registry on module import
auto_register_scrapers()
