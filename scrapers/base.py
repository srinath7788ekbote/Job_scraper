from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class JobListing:
    title: str
    company: str
    location: str
    url: str
    platform: str
    description: Optional[str] = None
    posted_date: Optional[str] = None

class JobScraper(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def scrape(self, keyword: str, location: str, limit: int = 100, days: int = 7) -> List[JobListing]:
        """
        Scrape jobs for a given keyword and location.
        :param limit: Max number of jobs to scrape (default 100)
        :param days: Number of days to look back (default 7)
        """
        pass
