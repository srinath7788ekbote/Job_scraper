import logging
from typing import List
from scrapers.base import JobScraper, JobListing
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import random

logger = logging.getLogger(__name__)

class NaukriScraper(JobScraper):
    def scrape(self, keyword: str, location: str, limit: int = 100, days: int = 7) -> List[JobListing]:
        logger.info(f"Scraping Naukri for {keyword} in {location} (Last {days} days, Limit: {limit})")
        jobs = []
        
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
                # Take screenshot for debugging
                try:
                    driver.save_screenshot("naukri_error.png")
                    logger.info("Screenshot saved to naukri_error.png")
                except:
                    pass
                return []
            
            # Wait for network to be idle
            time.sleep(5)
            
            scroll_attempts = 0
            max_scrolls = 5
            last_count = 0
            
            while len(jobs) < limit and scroll_attempts < max_scrolls:
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
                    if len(jobs) >= limit:
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
                        if any(j.url == link for j in jobs):
                            continue
                        
                        title = title_elem.text.strip()
                        if not title:
                            title = title_elem.get_attribute("title") or "Unknown"
                        
                        # Get company
                        company = "Unknown"
                        try:
                            company_elem = card.find_element(By.CSS_SELECTOR, "a.comp-name")
                            company = company_elem.text.strip()
                        except:
                            try:
                                company_elem = card.find_element(By.CSS_SELECTOR, ".comp-name")
                                company = company_elem.text.strip()
                            except:
                                pass
                        
                        # Get location
                        loc = location
                        try:
                            location_elem = card.find_element(By.CSS_SELECTOR, ".locWdth")
                            loc = location_elem.text.strip()
                        except:
                            try:
                                location_elem = card.find_element(By.CSS_SELECTOR, ".location")
                                loc = location_elem.text.strip()
                            except:
                                pass
                        
                        jobs.append(JobListing(
                            title=title,
                            company=company,
                            location=loc,
                            url=link,
                            platform="Naukri"
                        ))
                        
                    except Exception as e:
                        logger.debug(f"Error parsing Naukri job card: {e}")
                        continue
                
                # Check if we got new jobs
                if len(jobs) == last_count:
                    logger.info("No new jobs found, stopping scroll")
                    break
                
                last_count = len(jobs)
                
                # Gentle scroll if we need more jobs
                if len(jobs) < limit and scroll_attempts < max_scrolls - 1:
                    driver.execute_script("window.scrollBy(0, 1000);")
                    time.sleep(random.uniform(4, 6))  # Longer wait after scroll
                    scroll_attempts += 1
                else:
                    break
        
        except Exception as e:
            logger.error(f"Error scraping Naukri: {e}")
        finally:
            driver.quit()
        
        return jobs
