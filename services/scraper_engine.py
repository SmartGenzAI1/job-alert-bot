import requests
import time
import logging
from typing import List, Dict, Any

from database.models import add_job
from utils.logger import logger


def scrape_remoteok() -> int:
    """
    Scrape job listings from RemoteOK API.
    
    Returns:
        int: Number of jobs added
    """
    url = "https://remoteok.com/remote-jobs.json"
    jobs_added = 0
    
    try:
        logger.info("Starting RemoteOK scraping")
        
        # Set up headers to mimic a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        if not data or len(data) < 2:
            logger.warning("No data received from RemoteOK")
            return 0
        
        # Process jobs (skip first item which might be metadata)
        for item in data[1:40]:  # Limit to first 40 jobs
            try:
                title = item.get("position", "").strip()
                company = item.get("company", "").strip()
                url = item.get("url", "").strip()
                
                # Skip incomplete job listings
                if not all([title, company, url]):
                    continue
                
                # Add job to database
                if add_job(title, company, url, "remote"):
                    jobs_added += 1
                    
            except Exception as e:
                logger.warning(f"Error processing RemoteOK job item: {e}")
                continue
        
        logger.info(f"RemoteOK scraping completed: {jobs_added} jobs added")
        return jobs_added
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error in RemoteOK scraping: {e}")
        return 0
    except Exception as e:
        logger.error(f"Unexpected error in RemoteOK scraping: {e}")
        return 0


def scrape_indeed() -> int:
    """
    Placeholder for Indeed scraping (would need proper implementation).
    
    Returns:
        int: Number of jobs added (0 for now)
    """
    logger.info("Indeed scraping: Not implemented yet")
    return 0


def scrape_linkedin() -> int:
    """
    Placeholder for LinkedIn scraping (would need proper implementation).
    
    Returns:
        int: Number of jobs added (0 for now)
    """
    logger.info("LinkedIn scraping: Not implemented yet")
    return 0


def run_scrapers() -> Dict[str, int]:
    """
    Run all available scrapers and return results.
    
    Returns:
        dict: Results from each scraper
    """
    logger.info("Starting scheduled scraping job")
    
    results = {}
    
    # Run RemoteOK scraper
    try:
        results['remoteok'] = scrape_remoteok()
    except Exception as e:
        logger.error(f"RemoteOK scraper failed: {e}")
        results['remoteok'] = 0
    
    # Run other scrapers (placeholders for now)
    try:
        results['indeed'] = scrape_indeed()
    except Exception as e:
        logger.error(f"Indeed scraper failed: {e}")
        results['indeed'] = 0
    
    try:
        results['linkedin'] = scrape_linkedin()
    except Exception as e:
        logger.error(f"LinkedIn scraper failed: {e}")
        results['linkedin'] = 0
    
    total_jobs = sum(results.values())
    logger.info(f"Scraping completed: {total_jobs} total jobs added")
    
    return results


def run_single_scraper(scraper_name: str) -> int:
    """
    Run a specific scraper by name.
    
    Args:
        scraper_name: Name of the scraper to run
        
    Returns:
        int: Number of jobs added
    """
    scrapers = {
        'remoteok': scrape_remoteok,
        'indeed': scrape_indeed,
        'linkedin': scrape_linkedin,
    }
    
    if scraper_name not in scrapers:
        logger.error(f"Unknown scraper: {scraper_name}")
        return 0
    
    try:
        return scrapers[scraper_name]()
    except Exception as e:
        logger.error(f"Error running {scraper_name} scraper: {e}")
        return 0
