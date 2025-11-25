import logging
from typing import List
from playwright.sync_api import sync_playwright
from scrapers.base import JobScraper, JobListing
from utils.stealth import apply_stealth
import time
import random

logger = logging.getLogger(__name__)

class IndeedScraper(JobScraper):
    def scrape(self, keyword: str, location: str, limit: int = 100, days: int = 7) -> List[JobListing]:
        logger.info(f"Scraping Indeed for {keyword} in {location} (Last {days} days, Limit: {limit})")
        jobs = []
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
            page = context.new_page()
            apply_stealth(page)
            
            # Indeed Jobs Search URL
            domain = "www.indeed.com"
            if "india" in location.lower() or "bengaluru" in location.lower() or "bangalore" in location.lower():
                domain = "in.indeed.com"
            
            start = 0
            while len(jobs) < limit:
                url = f"https://{domain}/jobs?q={keyword}&l={location}&fromage={days}&start={start}"
                
                try:
                    page.goto(url, timeout=60000)
                    time.sleep(random.uniform(2, 5))
                    
                    try:
                        page.wait_for_selector(".jobsearch-ResultsList, #mosaic-provider-jobcards", timeout=15000)
                    except:
                        logger.warning("Indeed results list not found, might be blocked or empty.")
                        break

                    job_cards = page.query_selector_all(".job_seen_beacon")
                    if not job_cards:
                        break
                        
                    for card in job_cards:
                        if len(jobs) >= limit:
                            break
                            
                        try:
                            title_elem = card.query_selector("h2.jobTitle span")
                            company_elem = card.query_selector(".companyName") or card.query_selector('[data-testid="company-name"]')
                            location_elem = card.query_selector(".companyLocation") or card.query_selector('[data-testid="text-location"]')
                            link_elem = card.query_selector("a.jcs-JobTitle")
                            
                            if title_elem and link_elem:
                                title = title_elem.inner_text().strip()
                                company = company_elem.inner_text().strip() if company_elem else "Unknown"
                                loc = location_elem.inner_text().strip() if location_elem else location
                                link = f"https://{domain}" + link_elem.get_attribute("href")
                                
                                if any(j.url == link for j in jobs):
                                    continue
                                
                                jobs.append(JobListing(
                                    title=title,
                                    company=company,
                                    location=loc,
                                    url=link,
                                    platform="Indeed"
                                ))
                        except Exception as e:
                            continue
                    
                    # Next page logic
                    start += 10
                    # Check if next button exists to avoid infinite loop on last page
                    try:
                        next_btn = page.query_selector('[data-testid="pagination-page-next"]')
                        if not next_btn:
                            break
                    except:
                        break
                        
                except Exception as e:
                    logger.error(f"Error scraping Indeed: {e}")
                    break
            
            browser.close()
                
        return jobs
