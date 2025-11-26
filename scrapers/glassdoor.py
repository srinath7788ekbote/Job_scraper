from scrapers.base import JobScraper, JobListing
from playwright.sync_api import sync_playwright
from utils.stealth import apply_stealth
import time
import random
from typing import List
from utils.logger import get_logger, log_scraper_start, log_scraper_complete

logger = get_logger(__name__)

class GlassdoorScraper(JobScraper):
    @classmethod
    def get_platform_name(cls) -> str:
        """Return the platform name."""
        return "Glassdoor"
    
    def scrape(self, keyword: str, location: str, limit: int = 100, days: int = 7) -> List[JobListing]:
        # Validate configuration
        self.validate_config(keyword, location, limit, days)
        
        log_scraper_start(logger, "Glassdoor", keyword, location, days, limit)
        jobs = []
        
        from utils.text_parser import parse_job_description
        from utils.keyword_matcher import keyword_matches
        from utils.date_parser import parse_relative_date
        
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
            
            # Glassdoor Jobs Search URL - using location in search query for better filtering
            # Note: Glassdoor's location filtering is not perfect, especially for generic terms like "UK" or "US"
            # Remote jobs may still appear in results
            search_query = f"{keyword} {location}"
            url = f"https://www.glassdoor.com/Job/jobs.htm?sc.keyword={search_query}&fromAge={days}"
            
            logger.info(f"Glassdoor search URL: {url}")
            
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
                
                collected_links = []
                
                while len(collected_links) < limit and retries < 5:
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
                        if len(collected_links) >= limit:
                            break
                            
                        try:
                            # Try multiple selector patterns for each field
                            title_elem = (card.query_selector("a[data-test='job-title']") or 
                                        card.query_selector(".JobCard_jobTitle__GLrKV") or
                                        card.query_selector(".job-title"))
                            
                            link_elem = title_elem  # Title element usually contains the link
                            
                            if title_elem and link_elem:
                                link = link_elem.get_attribute("href")
                                if not link:
                                    continue
                                    
                                # Make absolute URL if needed
                                if not link.startswith("http"):
                                    link = "https://www.glassdoor.com" + link
                                    
                                # Avoid duplicates
                                if any(l == link for l in collected_links):
                                    continue
                                
                                title = title_elem.inner_text().strip()
                                
                                # Filter by keyword in title
                                if not keyword_matches(title, keyword):
                                    continue
                                    
                                collected_links.append(link)
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
                
                # Visit each job for details using multithreading
                logger.info(f"Collected {len(collected_links)} job links. Visiting each for details...")
                
                def fetch_job_detail(link):
                    """Fetch details for a single job"""
                    try:
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
                            
                            page.goto(link, timeout=30000)
                            time.sleep(random.uniform(2, 3))
                            
                            # Handle potential popup/modal
                            try:
                                close_button = page.query_selector("button[aria-label='Close'], .modal_closeIcon, [data-test='close-icon']")
                                if close_button:
                                    close_button.click()
                                    time.sleep(1)
                            except:
                                pass
                            
                            # Wait for job details to load
                            try:
                                page.wait_for_selector("div[data-test='job-title'], h1, h2", timeout=10000)
                            except:
                                logger.warning(f"Job details not loaded for {link}")
                                browser.close()
                                return None
                                
                            # Click "Show more" for description if present
                            try:
                                show_more = page.query_selector("button[data-test='show-more'], button:has-text('Show more'), div.JobDetails_showMore__text")
                                if show_more and show_more.is_visible():
                                    show_more.click()
                                    time.sleep(1)
                            except Exception as e:
                                logger.debug(f"No show more button or error clicking: {e}")
                                
                            # Extract details with multiple selector fallbacks
                            title = "Unknown"
                            company = "Unknown"
                            loc = location
                            description = ""
                            
                            # Try multiple selectors for title - based on actual page structure
                            try:
                                title_elem = (page.query_selector("div[data-test='job-title']") or 
                                             page.query_selector("h1") or
                                             page.query_selector("h2") or
                                             page.query_selector("[class*='jobTitle']") or
                                             page.query_selector(".JobDetails_jobTitle__Rw_sS"))
                                if title_elem:
                                    title = title_elem.inner_text().strip()
                                    logger.debug(f"Extracted title: {title}")
                                else:
                                    logger.warning(f"No title element found for {link}")
                            except Exception as e:
                                logger.error(f"Error extracting title: {e}")
                            
                            # Try multiple selectors for company
                            try:
                                company_elem = (page.query_selector("div[data-test='employer-name']") or
                                               page.query_selector("a[data-test='employer-name']") or
                                               page.query_selector("div[class*='employer']") or
                                               page.query_selector(".EmployerProfile_employerName") or
                                               page.query_selector(".JobDetails_jobDetailsHeader__i_I2D a"))
                                if company_elem:
                                    company = company_elem.inner_text().strip()
                                    logger.debug(f"Extracted company: {company}")
                            except Exception as e:
                                logger.error(f"Error extracting company: {e}")
                            
                            # Try multiple selectors for location
                            try:
                                location_elem = (page.query_selector("div[data-test='location']") or
                                                page.query_selector("div[class*='location']") or
                                                page.query_selector(".JobDetails_location__MbnUM"))
                                if location_elem:
                                    loc = location_elem.inner_text().strip()
                                    logger.debug(f"Extracted location: {loc}")
                            except Exception as e:
                                logger.error(f"Error extracting location: {e}")
                            
                            # Try multiple selectors for description
                            try:
                                desc_elem = (page.query_selector("div#JobDescriptionContainer") or
                                            page.query_selector("div[class*='JobDetails_jobDescription']") or
                                            page.query_selector("div[class*='jobDescriptionContent']") or
                                            page.query_selector("section[class*='description']") or
                                            page.query_selector("div[data-test='job-description']"))
                                if desc_elem:
                                    description = desc_elem.inner_text().strip()
                                    logger.debug(f"Extracted description length: {len(description)}")
                                else:
                                    logger.warning(f"No description element found for {link}")
                            except Exception as e:
                                logger.error(f"Error extracting description: {e}")
                            
                            parsed = parse_job_description(description)
                            
                            # Extract posted date
                            posted_date = None
                            try:
                                date_elem = page.query_selector("div[data-test='job-age'], .JobDetails_jobPostingDate__Mmbjj, span.css-1saizt3")
                                if date_elem:
                                    date_text = date_elem.inner_text().strip()
                                    posted_date = parse_relative_date(date_text)
                            except Exception as e:
                                logger.debug(f"Could not extract posted date: {e}")
                            
                            browser.close()
                            
                            # Verify location matches (allow Remote jobs)
                            loc_lower = loc.lower()
                            location_lower = location.lower()
                            
                            # Check if location matches or is remote
                            location_matches = (
                                "remote" in loc_lower or
                                location_lower in loc_lower or
                                any(word in loc_lower for word in location_lower.split())
                            )
                            
                            if not location_matches:
                                logger.info(f"Skipping job with non-matching location: {title} (location: {loc}, searched: {location})")
                                return None
                            
                            # Extract email from description
                            from utils.email_extractor import extract_email
                            email = extract_email(description)
                            
                            job_listing = JobListing(
                                title=title,
                                company=company,
                                location=loc,
                                url=link,
                                platform="Glassdoor",
                                description=description,
                                key_responsibilities=parsed["responsibilities"],
                                skills=parsed["skills"],
                                years_of_experience=parsed["years_of_experience"],
                                posted_date=posted_date,
                                email=email
                            )
                            
                            logger.info(f"Successfully extracted Glassdoor job: {title} at {company} (location: {loc})")
                            return job_listing
                    except Exception as e:
                        logger.error(f"Error scraping job detail {link}: {e}")
                        return None
                
                # Use parallel fetching with 5 workers
                from utils.parallel import parallel_fetch
                jobs = parallel_fetch(fetch_job_detail, collected_links, max_workers=5, description="Glassdoor jobs")
                        
            except Exception as e:
                logger.error(f"Error scraping Glassdoor: {e}")
            finally:
                browser.close()
                
        return jobs
