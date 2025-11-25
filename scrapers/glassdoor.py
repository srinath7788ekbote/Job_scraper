import logging
from typing import List
from playwright.sync_api import sync_playwright
from scrapers.base import JobScraper, JobListing
from utils.stealth import apply_stealth
import time
import random

logger = logging.getLogger(__name__)

class GlassdoorScraper(JobScraper):
    def scrape(self, keyword: str, location: str, limit: int = 100, days: int = 7) -> List[JobListing]:
        logger.info(f"Scraping Glassdoor for {keyword} in {location} (Last {days} days, Limit: {limit})")
        jobs = []
        
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"]
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={'width': 1920, 'height': 1080}
            )
            page = context.new_page()
            apply_stealth(page)
            
            # Glassdoor Jobs Search URL
            url = f"https://www.glassdoor.com/Job/jobs.htm?sc.keyword={keyword}&locT=C&locId=0&locKeyword={location}&fromAge={days}"
            
            try:
                page.goto(url, timeout=60000)
                time.sleep(random.uniform(3, 5))
                
                # Handle potential popup/modal
                try:
                    close_button = page.query_selector("button[aria-label='Close'], .modal_closeIcon, [data-test='close-icon']")
                    if close_button:
                        close_button.click()
                        time.sleep(1)
                except:
                    pass

                # Wait for job listings to load
                try:
                    page.wait_for_selector("li[data-test='jobListing'], .react-job-listing, .JobsList_jobListItem__JBBUV", timeout=15000)
                except Exception as e:
                    logger.warning(f"Glassdoor job listings not found: {e}")
                    browser.close()
                    return []

                last_height = 0
                retries = 0
                
                while len(jobs) < limit and retries < 5:
                    # Try multiple selector patterns
                    job_cards = page.query_selector_all("li[data-test='jobListing']")
                    if not job_cards:
                        job_cards = page.query_selector_all(".react-job-listing")
                    if not job_cards:
                        job_cards = page.query_selector_all(".JobsList_jobListItem__JBBUV")
                    
                    if not job_cards:
                        logger.warning("No job cards found with any selector")
                        break
                    
                    for card in job_cards:
                        if len(jobs) >= limit:
                            break
                            
                        try:
                            # Try multiple selector patterns for each field
                            title_elem = (card.query_selector("a[data-test='job-title']") or 
                                        card.query_selector(".JobCard_jobTitle__GLrKV") or
                                        card.query_selector(".job-title"))
                            
                            company_elem = (card.query_selector("div[data-test='employer-name']") or
                                          card.query_selector(".EmployerProfile_employerName__Xemli") or
                                          card.query_selector(".job-search-key-l2wjgv"))
                            
                            location_elem = (card.query_selector("div[data-test='emp-location']") or
                                           card.query_selector(".JobCard_location__N_iYE") or
                                           card.query_selector(".job-search-key-iii9i8"))
                            
                            link_elem = title_elem  # Title element usually contains the link
                            
                            if title_elem and link_elem:
                                link = link_elem.get_attribute("href")
                                if not link:
                                    continue
                                    
                                # Avoid duplicates
                                if any(j.url == link for j in jobs):
                                    continue
                                
                                # Make absolute URL if needed
                                if not link.startswith("http"):
                                    link = "https://www.glassdoor.com" + link
                                
                                title = title_elem.inner_text().strip()
                                company = company_elem.inner_text().strip() if company_elem else "Unknown"
                                loc = location_elem.inner_text().strip() if location_elem else location
                                
                                jobs.append(JobListing(
                                    title=title,
                                    company=company,
                                    location=loc,
                                    url=link,
                                    platform="Glassdoor"
                                ))
                        except Exception as e:
                            logger.debug(f"Error parsing Glassdoor job card: {e}")
                            continue
                    
                    # Scroll down to load more jobs
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(random.uniform(2, 4))
                    
                    # Check if we've reached the bottom
                    new_height = page.evaluate("document.body.scrollHeight")
                    if new_height == last_height:
                        retries += 1
                    else:
                        retries = 0
                        last_height = new_height
                        
            except Exception as e:
                logger.error(f"Error scraping Glassdoor: {e}")
            finally:
                browser.close()
                
        return jobs
