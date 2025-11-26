# Contributing to Job Scraper

Thank you for your interest in contributing to the Job Scraper project! This guide will help you add new job portals to the scraper.

## Adding a New Job Portal

Follow these steps to add support for a new job platform:

### 1. Create a New Scraper File

Create a new Python file in the `scrapers/` directory named after the platform (e.g., `indeed.py`, `monster.py`).

### 2. Implement the Base Class

Your scraper must inherit from `JobScraper` and implement all required methods:

```python
from scrapers.base import JobScraper, JobListing
from typing import List
import logging

logger = logging.getLogger(__name__)


class YourPlatformScraper(JobScraper):
    """
    Scraper for YourPlatform job listings.
    
    This scraper extracts job postings from YourPlatform using [Playwright/Selenium/BeautifulSoup].
    """
    
    @classmethod
    def get_platform_name(cls) -> str:
        """
        Return the platform name.
        
        Returns:
            Platform name as it should appear in output (e.g., "Indeed", "Monster")
        """
        return "YourPlatform"
    
    def scrape(
        self,
        keyword: str,
        location: str,
        limit: int = 100,
        days: int = 7
    ) -> List[JobListing]:
        """
        Scrape jobs from YourPlatform.
        
        Args:
            keyword: Job search keyword
            location: Location to search in
            limit: Maximum number of jobs to scrape
            days: Number of days to look back (1 = last 24 hours)
            
        Returns:
            List of JobListing objects
        """
        # Validate configuration
        self.validate_config(keyword, location, limit, days)
        
        logger.info(f"Scraping {self.get_platform_name()} for {keyword} in {location} (Last {days} days, Limit: {limit})")
        
        jobs = []
        
        # TODO: Implement your scraping logic here
        # 1. Build search URL with keyword, location, and date filter
        # 2. Navigate to the search page
        # 3. Extract job listing URLs
        # 4. Visit each job URL and extract details
        # 5. Parse job description for responsibilities, skills, experience
        # 6. Extract posted date and convert to ISO format
        # 7. Create JobListing objects
        
        return jobs
```

### 3. Implement Scraping Logic

#### Step 3.1: Build Search URL

Construct the search URL with appropriate filters:

```python
# Example for date filtering
# Convert days to platform-specific format
if days == 1:
    date_filter = "last-24-hours"
elif days <= 7:
    date_filter = "last-week"
else:
    date_filter = "last-month"

url = f"https://yourplatform.com/jobs?q={keyword}&l={location}&date={date_filter}"
```

#### Step 3.2: Extract Job Listings

Use Playwright, Selenium, or BeautifulSoup to extract job URLs:

```python
from playwright.sync_api import sync_playwright
from utils.date_parser import parse_relative_date
from utils.text_parser import parse_job_description
from utils.keyword_matcher import keyword_matches

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    page.goto(url, timeout=60000)
    page.wait_for_selector(".job-card")  # Adjust selector
    
    # Extract job URLs
    job_cards = page.query_selector_all(".job-card")
    collected_links = []
    
    for card in job_cards:
        if len(collected_links) >= limit:
            break
        
        try:
            title_elem = card.query_selector(".job-title")
            link_elem = card.query_selector("a.job-link")
            
            if title_elem and link_elem:
                title = title_elem.inner_text().strip()
                link = link_elem.get_attribute("href")
                
                # Filter by keyword
                if keyword_matches(title, keyword):
                    collected_links.append(link)
        except Exception as e:
            logger.debug(f"Error parsing job card: {e}")
            continue
```

#### Step 3.3: Extract Job Details

Visit each job URL and extract detailed information:

```python
def fetch_job_detail(link):
    """Fetch details for a single job."""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(link, timeout=30000)
            
            # Extract fields (adjust selectors for your platform)
            title = page.query_selector("h1.job-title").inner_text().strip()
            company = page.query_selector(".company-name").inner_text().strip()
            location = page.query_selector(".job-location").inner_text().strip()
            description = page.query_selector(".job-description").inner_text().strip()
            
            # Extract posted date
            posted_date = None
            try:
                date_elem = page.query_selector(".posted-date")
                if date_elem:
                    date_text = date_elem.inner_text().strip()
                    posted_date = parse_relative_date(date_text)
            except Exception as e:
                logger.debug(f"Could not extract posted date: {e}")
            
            # Parse description for structured data
            parsed = parse_job_description(description)
            
            browser.close()
            
            return JobListing(
                title=title,
                company=company,
                location=location,
                url=link,
                platform=self.get_platform_name(),
                description=description,
                key_responsibilities=parsed["responsibilities"],
                skills=parsed["skills"],
                years_of_experience=parsed["years_of_experience"],
                posted_date=posted_date
            )
    except Exception as e:
        logger.error(f"Error scraping job detail {link}: {e}")
        return None

# Use parallel processing
from utils.parallel import parallel_fetch
jobs = parallel_fetch(fetch_job_detail, collected_links, max_workers=5, description="YourPlatform jobs")
```

### 4. Register the Scraper

The scraper will be automatically registered when imported. Update `scrapers/scraper_registry.py` to include your scraper:

```python
# In auto_register_scrapers() function
try:
    from scrapers.yourplatform import YourPlatformScraper
    ScraperRegistry.register(YourPlatformScraper)
except ImportError as e:
    logger.warning(f"Could not import YourPlatformScraper: {e}")
```

### 5. Testing Checklist

Before submitting your scraper, ensure:

- [ ] Scraper inherits from `JobScraper`
- [ ] `get_platform_name()` returns correct platform name
- [ ] `scrape()` method validates configuration
- [ ] Date filtering works correctly (test with `--days=1`, `--days=7`)
- [ ] All JobListing fields are populated (or None if unavailable)
- [ ] `posted_date` is in ISO format (YYYY-MM-DD)
- [ ] Keyword matching filters irrelevant jobs
- [ ] Error handling prevents crashes
- [ ] Logging provides useful information
- [ ] Parallel processing is used for job details
- [ ] Tested with different keywords and locations

### 6. Test Your Scraper

```bash
# Test with a small limit first
python main.py --platform yourplatform --keyword "Software Engineer" --location "US" --days 1 --limit 5

# Verify output
cat jobs.csv
```

### 7. Code Style Guidelines

- Use descriptive variable names
- Add docstrings to all methods
- Use type hints for function signatures
- Follow PEP 8 style guide
- Add comments for complex logic
- Use logging instead of print statements
- Handle exceptions gracefully

### 8. Common Pitfalls

**Selector Changes**: Job platforms frequently update their HTML structure. Use multiple fallback selectors:

```python
title_elem = (
    page.query_selector("h1.job-title") or
    page.query_selector(".title") or
    page.query_selector("h1")
)
```

**Rate Limiting**: Add delays between requests:

```python
import time
import random

time.sleep(random.uniform(1, 3))
```

**Anti-Bot Detection**: Use stealth techniques:

```python
from utils.stealth import apply_stealth

page = browser.new_page()
apply_stealth(page)
```

**Date Parsing**: Test with various date formats:

```python
# "Posted today" → 2025-11-26
# "Posted 2 days ago" → 2025-11-24
# "Posted 1 week ago" → 2025-11-19
```

## Example: Complete Scraper Template

See `scrapers/linkedin.py`, `scrapers/glassdoor.py`, or `scrapers/naukri.py` for complete examples.

## Questions?

If you have questions or need help, please open an issue on GitHub.

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.
