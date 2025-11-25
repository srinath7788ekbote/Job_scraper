import argparse
import logging
import sys
from pathlib import Path
from scrapers.linkedin import LinkedinScraper
from scrapers.indeed import IndeedScraper
from scrapers.glassdoor import GlassdoorScraper
from scrapers.naukri import NaukriScraper
from utils.exporter import export_to_csv, export_to_json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="SRE Job Scraper")
    parser.add_argument("--platform", nargs="+", choices=["linkedin", "indeed", "naukri", "glassdoor"], 
                        help="Platforms to scrape (default: all)")
    parser.add_argument("--location", nargs="+", 
                        help="Locations to search (default: India, Australia, UAE, Europe)")
    parser.add_argument("--keyword", default="Site Reliability Engineer", help="Job keyword")
    parser.add_argument("--limit", type=int, default=100, help="Max number of jobs to scrape per platform")
    parser.add_argument("--days", type=int, default=7, help="Filter jobs posted in last N days")
    parser.add_argument("--output", default="jobs.csv", help="Output file path")
    
    args = parser.parse_args()
    
    scraper_map = {
        "linkedin": LinkedinScraper,
        "indeed": IndeedScraper,
        "glassdoor": GlassdoorScraper,
        "naukri": NaukriScraper
    }
    
    platforms = args.platform if args.platform else list(scraper_map.keys())
    locations = args.location if args.location else ["India", "Australia", "UAE", "Europe"]
    
    all_jobs = []
    
    for platform in platforms:
        if platform in scraper_map:
            scraper_cls = scraper_map[platform]
            scraper = scraper_cls()
            
            for location in locations:
                try:
                    jobs = scraper.scrape(args.keyword, location, limit=args.limit, days=args.days)
                    all_jobs.extend(jobs)
                    logger.info(f"Found {len(jobs)} jobs on {platform} for {location}")
                except Exception as e:
                    logger.error(f"Failed to scrape {platform} for {location}: {e}")
                    
    if args.output.endswith(".json"):
        export_to_json(all_jobs, args.output)
    else:
        export_to_csv(all_jobs, args.output)
        
    logger.info(f"Total jobs found: {len(all_jobs)}")
    
if __name__ == "__main__":
    main()
