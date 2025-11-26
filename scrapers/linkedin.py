from scrapers.base import JobScraper, JobListing
from playwright.sync_api import sync_playwright
import time
import random
from typing import List
from utils.logger import get_logger, log_scraper_start, log_scraper_complete

logger = get_logger(__name__)

class LinkedinScraper(JobScraper):
    @classmethod
    def get_platform_name(cls) -> str:
        """Return the platform name."""
        return "LinkedIn"
    
    def scrape(self, keyword: str, location: str, limit: int = 100, days: int = 7) -> List[JobListing]:
        self.validate_config(keyword, location, limit, days)
        log_scraper_start(logger, "LinkedIn", keyword, location, days, limit)
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
                
                collected_links = []
                
                while len(collected_links) < limit and retries < 5:
                    # Parse current visible jobs
                    job_cards = page.query_selector_all("li")
                    
                    for card in job_cards:
                        if len(collected_links) >= limit:
                            break
                            
                        try:
                            # Try multiple selectors for title
                            title_elem = card.query_selector(".base-search-card__title")
                            if not title_elem:
                                title_elem = card.query_selector("h3.base-search-card__title")
                            if not title_elem:
                                title_elem = card.query_selector("a.job-card-list__title")
                            
                            # Try multiple selectors for link
                            link_elem = card.query_selector(".base-card__full-link")
                            if not link_elem:
                                link_elem = card.query_selector("a.base-card__full-link")
                            if not link_elem:
                                link_elem = card.query_selector("a[href*='/jobs/view/']")
                            
                            if title_elem and link_elem:
                                link = link_elem.get_attribute("href")
                                title = title_elem.inner_text().strip()
                                
                                # Filter by keyword in title
                                from utils.keyword_matcher import keyword_matches
                                if not keyword_matches(title, keyword):
                                    continue
                                
                                # Avoid duplicates
                                if any(l == link for l in collected_links):
                                    continue
                                    
                                collected_links.append(link)
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
                
                
                # Now visit each job to get details using multithreading
                logger.info(f"Collected {len(collected_links)} job links. Visiting each for details...")
                
                from utils.text_parser import parse_job_description
                from utils.keyword_matcher import keyword_matches
                from utils.date_parser import parse_relative_date
                from utils.parallel import parallel_fetch
                
                def fetch_job_detail(link):
                    """Fetch details for a single job"""
                    try:
                        with sync_playwright() as p:
                            browser = p.chromium.launch(headless=True)
                            context = browser.new_context(
                                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                            )
                            page = context.new_page()
                            
                            page.goto(link, timeout=30000)
                            time.sleep(random.uniform(1, 2))
                            
                            # Check if we hit a login/signup page instead of the job page
                            page_title = page.title()
                            if "Join" in page_title or "Sign" in page_title or "Log" in page_title:
                                logger.warning(f"Skipping {link} - redirected to login/signup page (title: {page_title})")
                                browser.close()
                                return None
                            
                            # Click "See more" if description is truncated
                            try:
                                see_more_desc = page.query_selector("button.show-more-less-html__button--more")
                                if see_more_desc:
                                    see_more_desc.click()
                                    time.sleep(1)
                            except:
                                pass
                                
                            # Extract details with multiple fallback selectors
                            title = "Unknown"
                            company = "Unknown"
                            loc = location
                            description = ""
                            
                            # Extract title with fallbacks
                            try:
                                title_elem = page.query_selector("h1.top-card-layout__title")
                                if not title_elem:
                                    title_elem = page.query_selector("h1.topcard__title")
                                if not title_elem:
                                    title_elem = page.query_selector("h1")
                                if title_elem:
                                    title = title_elem.inner_text().strip()
                                    if not title:
                                        title = "Unknown"
                                    # Additional check: if title looks like a login page, skip
                                    if title in ["Join LinkedIn", "Sign in", "Log in"]:
                                        logger.warning(f"Skipping {link} - detected login page (title: {title})")
                                        browser.close()
                                        return None
                            except Exception as e:
                                logger.debug(f"Could not extract title: {e}")
                            
                            # Extract company with fallbacks
                            try:
                                company_elem = page.query_selector("a.topcard__org-name-link")
                                if not company_elem:
                                    company_elem = page.query_selector(".topcard__org-name-link")
                                if not company_elem:
                                    company_elem = page.query_selector("a.sub-nav-cta__optional-url")
                                if company_elem:
                                    company = company_elem.inner_text().strip()
                                    if not company:
                                        company = "Unknown"
                            except Exception as e:
                                logger.debug(f"Could not extract company: {e}")
                            
                            # Extract location
                            try:
                                location_elem = page.query_selector("span.topcard__flavor--bullet")
                                if not location_elem:
                                    location_elem = page.query_selector(".topcard__flavor--bullet")
                                if location_elem:
                                    loc = location_elem.inner_text().strip()
                            except Exception as e:
                                logger.debug(f"Could not extract location: {e}")
                            
                            # Extract description
                            try:
                                desc_elem = page.query_selector("div.show-more-less-html__markup")
                                if not desc_elem:
                                    desc_elem = page.query_selector(".show-more-less-html__markup")
                                if not desc_elem:
                                    desc_elem = page.query_selector("div.description__text")
                                if desc_elem:
                                    description = desc_elem.inner_text().strip()
                            except Exception as e:
                                logger.debug(f"Could not extract description: {e}")
                            
                            # Extract posted date
                            posted_date = None
                            try:
                                date_elem = page.query_selector("span.posted-time-ago__text")
                                if not date_elem:
                                    date_elem = page.query_selector(".posted-time-ago__text")
                                if date_elem:
                                    date_text = date_elem.inner_text().strip()
                                    posted_date = parse_relative_date(date_text)
                            except Exception as e:
                                logger.debug(f"Could not extract posted date: {e}")
                            
                            parsed = parse_job_description(description)
                            
                            # Extract email from description
                            from utils.email_extractor import extract_email
                            email = extract_email(description)
                            
                            browser.close()
                            
                            return JobListing(
                                title=title,
                                company=company,
                                location=loc,
                                url=link,
                                platform="LinkedIn",
                                description=description,
                                key_responsibilities=parsed["responsibilities"],
                                skills=parsed["skills"],
                                years_of_experience=parsed["years_of_experience"],
                                posted_date=posted_date,
                                email=email
                            )
                    except Exception as e:
                        logger.error(f"Error scraping job detail {link}: {e}")
                        return None
                
                # Use parallel fetching with 5 workers
                jobs = parallel_fetch(fetch_job_detail, collected_links, max_workers=5, description="LinkedIn jobs")
                        
            except Exception as e:
                logger.error(f"Error scraping LinkedIn: {e}")
            finally:
                browser.close()
                
        return jobs
