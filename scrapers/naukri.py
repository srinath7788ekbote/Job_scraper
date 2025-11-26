from scrapers.base import JobScraper, JobListing
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import random
from typing import List
from utils.logger import get_logger, log_scraper_start, log_scraper_complete

logger = get_logger(__name__)

class NaukriScraper(JobScraper):
    @classmethod
    def get_platform_name(cls) -> str:
        """Return the platform name."""
        return "Naukri"
    
    def scrape(self, keyword: str, location: str, limit: int = 100, days: int = 7) -> List[JobListing]:
        # Validate configuration
        self.validate_config(keyword, location, limit, days)
        
        log_scraper_start(logger, "Naukri", keyword, location, days, limit)
        jobs = []
        
        from utils.text_parser import parse_job_description
        from utils.keyword_matcher import keyword_matches
        from utils.date_parser import parse_relative_date
        
        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        driver = webdriver.Chrome(options=chrome_options)
        
        try:
            formatted_keyword = keyword.replace(" ", "-")
            url = f"https://www.naukri.com/{formatted_keyword}-jobs?k={keyword}&l={location}&jobAge={days}"
            logger.info(f"Navigating to: {url}")
            
            driver.get(url)
            time.sleep(random.uniform(4, 7))  # Initial wait for page load
            
            # Handle cookie consent
            try:
                cookie_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Got it')]"))
                )
                cookie_button.click()
                time.sleep(1)
                logger.info("Clicked cookie consent")
            except Exception as e:
                logger.debug(f"No cookie consent or already accepted: {e}")
            
            # Wait for job listings with extended timeout
            try:
                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".srp-jobtuple-wrapper, article.jobTuple, .cust-job-tuple"))
                )
                logger.info("Job listings loaded")
            except Exception as e:
                logger.error(f"Naukri job listings not found: {e}")
                return []
            
            # Wait for network to be idle
            time.sleep(5)
            
            scroll_attempts = 0
            max_scrolls = 5
            last_count = 0
            
            collected_links = []
            
            while len(collected_links) < limit and scroll_attempts < max_scrolls:
                # Try multiple selectors
                job_cards = driver.find_elements(By.CSS_SELECTOR, ".srp-jobtuple-wrapper")
                if not job_cards:
                    job_cards = driver.find_elements(By.CSS_SELECTOR, "article.jobTuple")
                if not job_cards:
                    job_cards = driver.find_elements(By.CSS_SELECTOR, ".cust-job-tuple")
                if not job_cards:
                    job_cards = driver.find_elements(By.CSS_SELECTOR, "article")
                
                logger.info(f"Found {len(job_cards)} job cards on scroll {scroll_attempts + 1}")
                
                if not job_cards:
                    logger.warning("No job cards found")
                    break
                
                for card in job_cards:
                    if len(collected_links) >= limit:
                        break
                    
                    try:
                        # Try multiple selector patterns for each field
                        title_elem = None
                        try:
                            title_elem = card.find_element(By.CSS_SELECTOR, "a.title")
                        except:
                            try:
                                title_elem = card.find_element(By.CSS_SELECTOR, ".title")
                            except:
                                try:
                                    title_elem = card.find_element(By.CSS_SELECTOR, "a[title]")
                                except:
                                    pass
                        
                        if not title_elem:
                            continue
                        
                        link = title_elem.get_attribute("href")
                        if not link:
                            continue
                        
                        # Avoid duplicates
                        if any(l == link for l in collected_links):
                            continue
                        
                        title = title_elem.text.strip()
                        if not title:
                            title = title_elem.get_attribute("title") or "Unknown"
                            
                        # Filter by keyword in title
                        if not keyword_matches(title, keyword):
                            continue
                        
                        collected_links.append(link)
                        
                    except Exception as e:
                        logger.debug(f"Error parsing Naukri job card: {e}")
                        continue
                
                # Check if we got new jobs
                if len(collected_links) == last_count:
                    logger.info("No new jobs found, stopping scroll")
                    break
                
                last_count = len(collected_links)
                
                # Gentle scroll if we need more jobs
                if len(collected_links) < limit and scroll_attempts < max_scrolls - 1:
                    driver.execute_script("window.scrollBy(0, 1000);")
                    time.sleep(random.uniform(4, 6))  # Longer wait after scroll
                    scroll_attempts += 1
                else:
                    break
            
            # Visit each job for details using multithreading
            logger.info(f"Collected {len(collected_links)} job links. Visiting each for details...")
            
            def fetch_job_detail(link):
                """Fetch details for a single job"""
                # Create a new driver for this thread
                chrome_options = Options()
                chrome_options.add_argument('--headless=new')
                chrome_options.add_argument('--disable-blink-features=AutomationControlled')
                chrome_options.add_argument('--window-size=1920,1080')
                chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
                
                driver = webdriver.Chrome(options=chrome_options)
                
                try:
                    driver.get(link)
                    time.sleep(random.uniform(2, 3))
                    
                    # Wait for job details to load - try multiple selectors
                    page_loaded = False
                    selectors_to_try = [
                        "h1.jd-header-title",
                        ".job-desc",
                        "article.jobDetails",
                        ".styles_jhc__jd-header",
                        "h1",  # Generic fallback
                        "article",  # Generic fallback
                    ]
                    
                    for selector in selectors_to_try:
                        try:
                            WebDriverWait(driver, 5).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                            )
                            page_loaded = True
                            logger.debug(f"Page loaded with selector: {selector}")
                            break
                        except:
                            continue
                    
                    if not page_loaded:
                        logger.warning(f"Job details not loaded for {link} - tried all selectors")
                        # Try to get page source for debugging
                        try:
                            page_title = driver.title
                            logger.debug(f"Page title: {page_title}")
                        except:
                            pass
                        driver.quit()
                        return None
                    
                    # Additional wait for dynamic content
                    time.sleep(1)
                    
                    # Extract details
                    title = "Unknown"
                    company = "Unknown"
                    loc = location
                    description = ""
                    
                    try:
                        title = driver.find_element(By.CSS_SELECTOR, "h1.jd-header-title").text.strip()
                    except:
                        try:
                            title = driver.find_element(By.CSS_SELECTOR, ".jd-header-title").text.strip()
                        except:
                            try:
                                title = driver.find_element(By.CSS_SELECTOR, "h1").text.strip()
                            except:
                                try:
                                    title = driver.find_element(By.CSS_SELECTOR, ".styles_jd-header-title").text.strip()
                                except:
                                    logger.warning(f"Could not extract title from {link}")
                                    pass
                        
                    try:
                        company = driver.find_element(By.CSS_SELECTOR, ".jd-header-comp-name a").text.strip()
                        logger.debug(f"Extracted company via .jd-header-comp-name a: {company}")
                    except:
                        try:
                            company = driver.find_element(By.CSS_SELECTOR, ".jd-header-comp-name").text.strip()
                            logger.debug(f"Extracted company via .jd-header-comp-name: {company}")
                        except:
                            try:
                                # Try to find company name in the header area
                                company = driver.find_element(By.CSS_SELECTOR, "a.comp-name").text.strip()
                                logger.debug(f"Extracted company via a.comp-name: {company}")
                            except:
                                try:
                                    # Look for any link with company name class
                                    company_elem = driver.find_element(By.CSS_SELECTOR, "a[class*='comp']")
                                    company = company_elem.text.strip()
                                    logger.debug(f"Extracted company via a[class*='comp']: {company}")
                                except:
                                    try:
                                        # Try getting from page body text - company is usually on second line
                                        body_text = driver.find_element(By.TAG_NAME, "body").text
                                        lines = [l.strip() for l in body_text.split('\n') if l.strip()]
                                        
                                        # Look for company name (usually after job title)
                                        if len(lines) > 1:
                                            # Company is typically the second non-empty line
                                            potential_company = lines[1]
                                            
                                            # Clean up: remove ratings and review counts
                                            import re
                                            # Remove patterns like "3.7", "21866 Reviews", "3.721866 Reviews"
                                            cleaned = re.sub(r'\d+\.\d+', '', potential_company)
                                            cleaned = re.sub(r'\d+\s+Reviews?', '', cleaned, flags=re.IGNORECASE)
                                            cleaned = cleaned.strip()
                                            
                                            # If we have something left and it's not too long, use it
                                            if cleaned and len(cleaned) > 2 and len(cleaned) < 100:
                                                company = cleaned
                                                logger.debug(f"Extracted company from body text: {company}")
                                    except Exception as e:
                                        logger.warning(f"Could not extract company from {link}: {e}")
                                        pass
                        
                    try:
                        loc = driver.find_element(By.CSS_SELECTOR, ".jd-header-loc").text.strip()
                    except:
                        try:
                            loc = driver.find_element(By.CSS_SELECTOR, ".location").text.strip()
                        except:
                            pass
                        
                    try:
                        desc_elem = driver.find_element(By.CSS_SELECTOR, ".job-desc")
                        description = desc_elem.text.strip()
                    except:
                        try:
                            desc_elem = driver.find_element(By.CSS_SELECTOR, ".dang-inner-html")
                            description = desc_elem.text.strip()
                        except:
                            try:
                                desc_elem = driver.find_element(By.CSS_SELECTOR, "div[class*='job-description']")
                                description = desc_elem.text.strip()
                            except:
                                try:
                                    desc_elem = driver.find_element(By.CSS_SELECTOR, "article.jobDetails")
                                    description = desc_elem.text.strip()
                                except:
                                    try:
                                        # Try to get any article or main content
                                        desc_elem = driver.find_element(By.CSS_SELECTOR, "article, main")
                                        description = desc_elem.text.strip()
                                    except:
                                        logger.warning(f"Could not extract description from {link}")
                                        pass
                    
                    
                    # If company is still Unknown or empty, try to extract from description
                    if (company == "Unknown" or not company) and description:
                        try:
                            # Company name is usually within the first few lines
                            desc_lines = [l.strip() for l in description.split('\n') if l.strip()]
                            import re
                            
                            # Check first 5 lines for company name
                            for i in range(min(5, len(desc_lines))):
                                line = desc_lines[i]
                                
                                # Skip the job title (usually first line)
                                if i == 0:
                                    continue
                                
                                # Clean the line: remove ratings and reviews
                                cleaned = re.sub(r'\d+\.\d+', '', line)
                                cleaned = re.sub(r'\d+\s+Reviews?', '', cleaned, flags=re.IGNORECASE)
                                cleaned = cleaned.strip()
                                
                                # Check if this looks like a company name
                                # Company names are usually 2-100 chars, not all numbers, not common words
                                if cleaned and len(cleaned) > 2 and len(cleaned) < 100:
                                    # Skip lines that are clearly not company names
                                    skip_patterns = [
                                        r'^\d+\s*-\s*\d+\s*years?$',  # "2 - 6 years"
                                        r'^not disclosed$',  # "Not Disclosed"
                                        r'^hybrid$',  # "Hybrid"
                                        r'^remote$',  # "Remote"
                                        r'^posted:',  # "Posted: 1 day ago"
                                        r'^applicants:',  # "Applicants: 50+"
                                        r'^openings:',  # "Openings: 10"
                                    ]
                                    
                                    should_skip = False
                                    for pattern in skip_patterns:
                                        if re.search(pattern, cleaned, re.IGNORECASE):
                                            should_skip = True
                                            break
                                    
                                    if not should_skip:
                                        company = cleaned
                                        logger.info(f"Extracted company from description line {i}: '{company}'")
                                        break
                        except Exception as e:
                            logger.debug(f"Could not extract company from description: {e}")
                    
                    parsed = parse_job_description(description)
                    
                    # Extract posted date
                    posted_date = None
                    try:
                        date_elem = driver.find_element(By.CSS_SELECTOR, ".job-post-day, span.job-post-day, .jd-stats span")
                        date_text = date_elem.text.strip()
                        posted_date = parse_relative_date(date_text)
                    except Exception as e:
                        logger.debug(f"Could not extract posted date: {e}")
                    
                    # Extract email from description
                    from utils.email_extractor import extract_email
                    email = extract_email(description)
                    
                    driver.quit()
                    
                    return JobListing(
                        title=title,
                        company=company,
                        location=loc,
                        url=link,
                        platform="Naukri",
                        description=description,
                        key_responsibilities=parsed["responsibilities"],
                        skills=parsed["skills"],
                        years_of_experience=parsed["years_of_experience"],
                        posted_date=posted_date,
                        email=email
                    )
                    
                except Exception as e:
                    logger.error(f"Error scraping job detail {link}: {e}")
                    try:
                        driver.quit()
                    except:
                        pass
                    return None
            
            # Use parallel fetching with 5 workers
            from utils.parallel import parallel_fetch
            jobs = parallel_fetch(fetch_job_detail, collected_links, max_workers=5, description="Naukri jobs")
        
        except Exception as e:
            logger.error(f"Error scraping Naukri: {e}")
        finally:
            driver.quit()
        
        return jobs
