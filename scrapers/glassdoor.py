import logging
from typing import List
from playwright.sync_api import sync_playwright
from scrapers.base import JobScraper, JobListing
import time
import random

logger = logging.getLogger(__name__)

class GlassdoorScraper(JobScraper):
    def scrape(self, keyword: str, location: str, limit: int = 100, days: int = 7) -> List[JobListing]:
        logger.info(f"Scraping Glassdoor for {keyword} in {location} (Last {days} days, Limit: {limit})")
        jobs = []
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
            page = context.new_page()
            
            # Glassdoor Jobs Search URL
            # fromAge={days}
            url = f"https://www.glassdoor.com/Job/jobs.htm?sc.keyword={keyword}&locT=C&locId=0&locKeyword={location}&fromAge={days}"
            
            try:
                page.goto(url, timeout=60000)
                
                # Handle potential popup
                try:
                    page.click(".modal_closeIcon", timeout=5000)
                except:
                    pass

                job_cards = page.query_selector_all("li.react-job-listing")
                
                for card in job_cards:
                    if len(jobs) >= limit:
                        break
                        
                    try:
                        title_elem = card.query_selector(".job-title") or card.query_selector('[data-test="job-title"]')
                        company_elem = card.query_selector(".job-search-key-l2wjgv")
                        location_elem = card.query_selector(".job-search-key-iii9i8")
                        link_elem = card.query_selector("a.job-link")
                        
                        if title_elem and link_elem:
                            title = title_elem.inner_text().strip()
                            company = company_elem.inner_text().strip() if company_elem else "Unknown"
                            loc = location_elem.inner_text().strip() if location_elem else location
                            link = "https://www.glassdoor.com" + link_elem.get_attribute("href")
                            
                            jobs.append(JobListing(
                                title=title,
                                company=company,
                                location=loc,
                                url=link,
                                platform="Glassdoor"
                            ))
                    except Exception as e:
                        continue
                        
            except Exception as e:
                logger.error(f"Error scraping Glassdoor: {e}")
            finally:
                browser.close()
                
        return jobs
