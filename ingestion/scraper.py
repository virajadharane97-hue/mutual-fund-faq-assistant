"""
Web Scraper for Groww Mutual Fund Pages

Fetches raw HTML from the 5 configured Groww URLs with retry logic,
timeout handling, and error management.
"""

import logging
import time
from datetime import datetime, timezone
import requests
from requests.exceptions import RequestException

# Optional Playwright for JS-rendered fallback
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

from config.settings import (
    GROWW_URLS,
    SCRAPER_TIMEOUT,
    SCRAPER_MAX_RETRIES,
    SCRAPER_RETRY_BACKOFF,
    SCRAPER_USER_AGENT,
    SCRAPER_MAX_HTML_SIZE,
)

logger = logging.getLogger(__name__)


def scrape_url_with_requests(url: str, timeout: int, user_agent: str) -> str:
    """Fetch HTML using standard requests."""
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    
    html = response.text
    if len(html.encode('utf-8')) > SCRAPER_MAX_HTML_SIZE:
        logger.warning(f"HTML size for {url} exceeds maximum limit. Truncating.")
        html = html[:int(SCRAPER_MAX_HTML_SIZE)]
        
    return html


def scrape_url_with_playwright(url: str, timeout: int) -> str:
    """Fetch HTML using Playwright (fallback for JS-rendered pages)."""
    if not PLAYWRIGHT_AVAILABLE:
        raise RuntimeError("Playwright is not installed.")
        
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            # Playwright timeout is in milliseconds
            page.goto(url, wait_until="networkidle", timeout=timeout * 1000)
            html = page.content()
            return html
        finally:
            browser.close()


def scrape_url(url: str) -> dict:
    """
    Scrape a single Groww URL and return raw HTML with metadata.
    
    Returns:
        dict: {"url": str, "html": str, "scraped_at": str, "status": int}
    """
    html_content = ""
    status_code = 200
    
    for attempt in range(1, SCRAPER_MAX_RETRIES + 1):
        try:
            logger.info(f"Scraping {url} (Attempt {attempt}/{SCRAPER_MAX_RETRIES})")
            html_content = scrape_url_with_requests(url, SCRAPER_TIMEOUT, SCRAPER_USER_AGENT)
            
            # Simple heuristic to check if it's mostly JS/empty body requiring a browser
            if len(html_content) < 5000 and PLAYWRIGHT_AVAILABLE:
                logger.info(f"Page seems JS-rendered. Falling back to Playwright for {url}")
                html_content = scrape_url_with_playwright(url, SCRAPER_TIMEOUT)
                
            status_code = 200
            break
            
        except RequestException as e:
            logger.warning(f"Request failed for {url}: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                status_code = e.response.status_code
            else:
                status_code = 500
                
            if attempt < SCRAPER_MAX_RETRIES:
                sleep_time = SCRAPER_RETRY_BACKOFF ** attempt
                logger.info(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                logger.error(f"Failed to scrape {url} after {SCRAPER_MAX_RETRIES} attempts.")
        except Exception as e:
            logger.error(f"Unexpected error scraping {url}: {str(e)}")
            status_code = 500
            if attempt < SCRAPER_MAX_RETRIES:
                time.sleep(SCRAPER_RETRY_BACKOFF ** attempt)
            else:
                break
                
    scraped_at = datetime.now(timezone.utc).isoformat()
    
    return {
        "url": url,
        "html": html_content,
        "scraped_at": scraped_at,
        "status": status_code
    }


def scrape_all_urls() -> list[dict]:
    """
    Scrape all configured Groww URLs.
    
    Returns:
        list[dict]: List of scraping results.
    """
    results = []
    for url in GROWW_URLS:
        result = scrape_url(url)
        results.append(result)
        
        # Add a small delay between requests to be polite
        if url != GROWW_URLS[-1]:
            time.sleep(2)
            
    return results

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting scraper...")
    results = scrape_all_urls()
    for r in results:
        status = r.get("status")
        html_len = len(r.get("html", ""))
        logger.info(f"Result for {r['url']}: Status={status}, HTML Length={html_len} chars")
