"""
Multi-platform job scraper with concurrent processing.

Scrapes job listings from LinkedIn, Glassdoor, and Naukri with support
for filtering by date, location, and keyword.
"""

import argparse
import logging
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

from scrapers.scraper_registry import ScraperRegistry
from scrapers.base import JobListing
from utils.exporter import export_to_csv, export_to_json
from utils.exceptions import ScraperException, ScraperConfigError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def scrape_platform_location(platform: str, keyword: str, location: str, limit: int, days: int) -> List[JobListing]:
    """
    Scrape a single platform for a single location.
    
    Args:
        platform: Platform name (e.g., "linkedin", "glassdoor")
        keyword: Job search keyword
        location: Location to search
        limit: Maximum number of jobs
        days: Number of days to look back
        
    Returns:
        List of JobListing objects
    """
    try:
        scraper = ScraperRegistry.create_scraper(platform)
        jobs = scraper.scrape(keyword, location, limit=limit, days=days)
        logger.info(f"✓ {platform.capitalize()}: Found {len(jobs)} jobs in {location}")
        return jobs
    except ScraperException as e:
        logger.error(f"✗ {platform.capitalize()}: Scraper error for {location}: {e}")
        return []
    except Exception as e:
        logger.error(f"✗ {platform.capitalize()}: Unexpected error for {location}: {e}")
        return []


def main():
    """Main entry point for the job scraper."""
    parser = argparse.ArgumentParser(
        description="Multi-platform Job Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape all platforms for SRE jobs in Berlin from last 24 hours
  python main.py --keyword "SRE" --location "Berlin" --days 1 --limit 10
  
  # Scrape only LinkedIn and Glassdoor for multiple locations
  python main.py --platform linkedin glassdoor --keyword "DevOps" --location "US" "UK" --days 7 --limit 50
  
  # Scrape Naukri for jobs in India from last 3 days
  python main.py --platform naukri --keyword "Python Developer" --location "India" --days 3 --limit 20
        """
    )
    
    parser.add_argument(
        "--platform",
        nargs="+",
        choices=ScraperRegistry.get_available_platforms(),
        help=f"Platforms to scrape (default: all). Available: {', '.join(ScraperRegistry.get_available_platforms())}"
    )
    parser.add_argument(
        "--location",
        nargs="+",
        required=True,
        help="Locations to search (e.g., 'Berlin' 'US' 'India')"
    )
    parser.add_argument(
        "--keyword",
        required=True,
        help="Job keyword to search for (e.g., 'SRE', 'DevOps Engineer')"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Max number of jobs to scrape per platform per location (default: 100)"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Filter jobs posted in last N days (default: 7). --days=1 means last 24 hours."
    )
    parser.add_argument(
        "--output",
        default="jobs.csv",
        help="Output base filename (default: jobs). Both .csv and .json files will be created."
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=3,
        help="Number of concurrent platform workers (default: 3)"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    try:
        if args.limit <= 0:
            raise ScraperConfigError("Limit must be positive")
        if args.days <= 0:
            raise ScraperConfigError("Days must be positive")
        if args.workers <= 0:
            raise ScraperConfigError("Workers must be positive")
    except ScraperConfigError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    
    # Determine platforms to scrape
    platforms = args.platform if args.platform else ScraperRegistry.get_available_platforms()
    locations = args.location
    
    logger.info("=" * 80)
    logger.info("JOB SCRAPER STARTED")
    logger.info("=" * 80)
    logger.info(f"Keyword: {args.keyword}")
    logger.info(f"Locations: {', '.join(locations)}")
    logger.info(f"Platforms: {', '.join(platforms)}")
    logger.info(f"Date filter: Last {args.days} day(s)")
    logger.info(f"Limit per platform/location: {args.limit}")
    logger.info(f"Concurrent workers: {args.workers}")
    logger.info("=" * 80)
    
    all_jobs = []
    seen_urls = set()  # Track URLs to avoid duplicates
    
    # Create tasks for parallel execution
    tasks = []
    for platform in platforms:
        for location in locations:
            tasks.append((platform, args.keyword, location, args.limit, args.days))
    
    logger.info(f"Processing {len(tasks)} platform-location combinations...")
    
    # Execute tasks in parallel
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_to_task = {
            executor.submit(scrape_platform_location, *task): task
            for task in tasks
        }
        
        for future in as_completed(future_to_task):
            task = future_to_task[future]
            platform, keyword, location, limit, days = task
            
            try:
                jobs = future.result()
                
                # Deduplicate jobs based on URL
                unique_jobs = []
                for job in jobs:
                    if job.url not in seen_urls:
                        seen_urls.add(job.url)
                        unique_jobs.append(job)
                
                duplicates = len(jobs) - len(unique_jobs)
                if duplicates > 0:
                    logger.info(f"  Removed {duplicates} duplicate(s) from {platform}/{location}")
                
                all_jobs.extend(unique_jobs)
                
            except Exception as e:
                logger.error(f"Failed to process {platform}/{location}: {e}")
    
    # Export results
    logger.info("=" * 80)
    logger.info("SCRAPING COMPLETED")
    logger.info("=" * 80)
    
    if all_jobs:
        try:
            # Determine base filename (without extension)
            import os
            base_filename = os.path.splitext(args.output)[0]
            csv_filename = f"{base_filename}.csv"
            json_filename = f"{base_filename}.json"
            
            # Export to both formats
            export_to_csv(all_jobs, csv_filename)
            export_to_json(all_jobs, json_filename)
            
            # Print statistics
            logger.info(f"Total unique jobs found: {len(all_jobs)}")
            
            # Jobs per platform
            platform_stats = {}
            for job in all_jobs:
                platform_stats[job.platform] = platform_stats.get(job.platform, 0) + 1
            
            logger.info("Jobs per platform:")
            for platform, count in sorted(platform_stats.items()):
                logger.info(f"  {platform}: {count}")
            
            # Jobs with posted dates
            jobs_with_dates = sum(1 for job in all_jobs if job.posted_date)
            logger.info(f"Jobs with posted dates: {jobs_with_dates}/{len(all_jobs)}")
            
            logger.info(f"Results saved to: {csv_filename} and {json_filename}")
            
        except Exception as e:
            logger.error(f"Failed to export results: {e}")
            sys.exit(1)
    else:
        logger.warning("No jobs found!")
    
    logger.info("=" * 80)


if __name__ == "__main__":
    main()

