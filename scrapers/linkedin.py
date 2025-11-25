import logging
from typing import List
from playwright.sync_api import sync_playwright
from scrapers.base import JobScraper, JobListing
import time
import random

logger = logging.getLogger(__name__)

class LinkedinScraper(JobScraper):
    def scrape(self, keyword: str, location: str, limit: int = 100, days: int = 7) -> List[JobListing]:
        logger.info(f"Scraping LinkedIn for {keyword} in {location} (Last {days} days, Limit: {limit})")
        jobs = []
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
            page = context.new_page()
            
            # LinkedIn Jobs Search URL
            # f_TPR is time posted range in seconds. r604800 = 7 days.
            seconds = days * 24 * 60 * 60
            url = f"https://www.linkedin.com/jobs/search?keywords={keyword}&location={location}&f_TPR=r{seconds}"
            
            try:
                page.goto(url, timeout=60000)
                page.wait_for_selector(".jobs-search__results-list", timeout=10000)
                
                # Scroll and load more jobs until limit is reached
                last_height = 0
                retries = 0
                
                while len(jobs) < limit and retries < 5:
                    # Parse current visible jobs
                    job_cards = page.query_selector_all("li")
                    
                    current_jobs_count = len(jobs)
                    
                    for card in job_cards:
                        if len(jobs) >= limit:
                            break
                            
                        try:
                            title_elem = card.query_selector(".base-search-card__title")
                            company_elem = card.query_selector(".base-search-card__subtitle")
                            location_elem = card.query_selector(".job-search-card__location")
                            link_elem = card.query_selector(".base-card__full-link")
                            
                            if title_elem and link_elem:
                                link = link_elem.get_attribute("href")
                                # Avoid duplicates
                                if any(j.url == link for j in jobs):
                                    continue

                                title = title_elem.inner_text().strip()
                                company = company_elem.inner_text().strip() if company_elem else "Unknown"
                                loc = location_elem.inner_text().strip() if location_elem else location
                                
                                jobs.append(JobListing(
                                    title=title,
                                    company=company,
                                    location=loc,
                                    url=link,
                                    platform="LinkedIn"
                                ))
                        except Exception as e:
                            continue
                    
                    # Scroll down
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(random.uniform(2, 4))
                    
                    # Check if we reached bottom or button "See more jobs"
                    try:
                        see_more = page.query_selector("button.infinite-scroller__show-more-button")
                        if see_more and see_more.is_visible():
                            see_more.click()
                            time.sleep(2)
                    except:
                        pass

                    new_height = page.evaluate("document.body.scrollHeight")
                    if new_height == last_height:
                        retries += 1
                    else:
                        retries = 0
                        last_height = new_height
                        
            except Exception as e:
                logger.error(f"Error scraping LinkedIn: {e}")
            finally:
                browser.close()
                
        return jobs
