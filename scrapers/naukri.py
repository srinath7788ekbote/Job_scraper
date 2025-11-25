import logging
from typing import List
from playwright.sync_api import sync_playwright
from scrapers.base import JobScraper, JobListing
from utils.stealth import apply_stealth

logger = logging.getLogger(__name__)

class NaukriScraper(JobScraper):
    def scrape(self, keyword: str, location: str, limit: int = 100, days: int = 7) -> List[JobListing]:
        logger.info(f"Scraping Naukri for {keyword} in {location} (Last {days} days, Limit: {limit})")
        jobs = []
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                viewport={'width': 1920, 'height': 1080}
            )
            page = context.new_page()
            apply_stealth(page)
            
            # Naukri Jobs Search URL
            # jobAge parameter filters by days
            formatted_keyword = keyword.replace(" ", "-")
            url = f"https://www.naukri.com/{formatted_keyword}-jobs?k={keyword}&l={location}&jobAge={days}"
            
            try:
                page.goto(url, timeout=60000)
                
                # Wait for results or "No jobs found" message
                try:
                    page.wait_for_selector(".srp-jobtuple-wrapper, .no-jobs-found", timeout=20000)
                except:
                    logger.warning("Naukri results not found or timeout.")
                    return []
                
                last_height = 0
                retries = 0
                
                while len(jobs) < limit and retries < 5:
                    job_cards = page.query_selector_all(".srp-jobtuple-wrapper")
                    
                    for card in job_cards:
                        if len(jobs) >= limit:
                            break
                            
                        try:
                            title_elem = card.query_selector(".title")
                            company_elem = card.query_selector(".comp-name")
                            location_elem = card.query_selector(".locWdth")
                            link_elem = card.query_selector(".title")
                            
                            if title_elem and link_elem:
                                link = link_elem.get_attribute("href")
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
                                    platform="Naukri"
                                ))
                        except Exception as e:
                            continue
                    
                    # Scroll down
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(random.uniform(2, 4))
                    
                    new_height = page.evaluate("document.body.scrollHeight")
                    if new_height == last_height:
                        retries += 1
                    else:
                        retries = 0
                        last_height = new_height
                        
            except Exception as e:
                logger.error(f"Error scraping Naukri: {e}")
            finally:
                browser.close()
                
        return jobs
