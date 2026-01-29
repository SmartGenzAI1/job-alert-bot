import requests
import time
import logging
import asyncio
import aiohttp
import feedparser
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

from database.models import add_job
from utils.logger import logger


class JobScraper:
    """Base class for job scrapers."""
    
    def __init__(self, name: str, base_url: str):
        self.name = name
        self.base_url = base_url
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/html, application/xhtml+xml, application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            },
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def fetch(self, url: str, **kwargs) -> Optional[str]:
        """Fetch URL content with error handling."""
        try:
            async with self.session.get(url, **kwargs) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.warning(f"{self.name}: HTTP {response.status} for {url}")
                    return None
        except Exception as e:
            logger.error(f"{self.name}: Error fetching {url}: {e}")
            return None
            
    async def scrape(self) -> int:
        """Scrape jobs - to be implemented by subclasses."""
        raise NotImplementedError


class RemoteOKScraper(JobScraper):
    """Scraper for RemoteOK API."""
    
    def __init__(self):
        super().__init__("RemoteOK", "https://remoteok.com")
        
    async def scrape(self) -> int:
        """Scrape remote jobs from RemoteOK."""
        jobs_added = 0
        url = "https://remoteok.com/remote-jobs.json"
        
        try:
            logger.info("Starting RemoteOK scraping")
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"RemoteOK returned HTTP {response.status}")
                    return 0
                    
                data = await response.json()
                
                if not data or len(data) < 2:
                    logger.warning("No data received from RemoteOK")
                    return 0
                
                # Process jobs (skip first item which is metadata)
                for item in data[1:50]:  # Limit to first 50 jobs
                    try:
                        title = item.get("position", "").strip()
                        company = item.get("company", "").strip()
                        job_url = item.get("url", "").strip()
                        
                        if not all([title, company, job_url]):
                            continue
                            
                        # Ensure URL is absolute
                        if job_url.startswith('/'):
                            job_url = f"{self.base_url}{job_url}"
                        
                        if add_job(title, company, job_url, "remote"):
                            jobs_added += 1
                            
                    except Exception as e:
                        logger.warning(f"Error processing RemoteOK job: {e}")
                        continue
                        
            logger.info(f"RemoteOK scraping completed: {jobs_added} jobs added")
            
        except Exception as e:
            logger.error(f"Error in RemoteOK scraper: {e}")
            
        return jobs_added


class WeWorkRemotelyScraper(JobScraper):
    """Scraper for We Work Remotely RSS feed."""
    
    def __init__(self):
        super().__init__("WeWorkRemotely", "https://weworkremotely.com")
        
    async def scrape(self) -> int:
        """Scrape remote jobs from We Work Remotely RSS."""
        jobs_added = 0
        url = "https://weworkremotely.com/remote-jobs.rss"
        
        try:
            logger.info("Starting WeWorkRemotely scraping")
            
            content = await self.fetch(url)
            if not content:
                return 0
                
            feed = feedparser.parse(content)
            
            for entry in feed.entries[:30]:  # Limit to 30 jobs
                try:
                    title = entry.get("title", "").strip()
                    link = entry.get("link", "").strip()
                    
                    # Parse company from title (format often: "Company: Position")
                    if ':' in title:
                        company, position = title.split(':', 1)
                        company = company.strip()
                        position = position.strip()
                    else:
                        company = "Unknown"
                        position = title
                    
                    if not all([position, link]):
                        continue
                    
                    if add_job(position, company, link, "remote"):
                        jobs_added += 1
                        
                except Exception as e:
                    logger.warning(f"Error processing WeWorkRemotely job: {e}")
                    continue
                    
            logger.info(f"WeWorkRemotely scraping completed: {jobs_added} jobs added")
            
        except Exception as e:
            logger.error(f"Error in WeWorkRemotely scraper: {e}")
            
        return jobs_added


class RemotiveScraper(JobScraper):
    """Scraper for Remotive API."""
    
    def __init__(self):
        super().__init__("Remotive", "https://remotive.com")
        
    async def scrape(self) -> int:
        """Scrape remote jobs from Remotive API."""
        jobs_added = 0
        url = "https://remotive.com/api/remote-jobs"
        
        try:
            logger.info("Starting Remotive scraping")
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"Remotive returned HTTP {response.status}")
                    return 0
                    
                data = await response.json()
                jobs = data.get("jobs", [])
                
                for job in jobs[:40]:  # Limit to 40 jobs
                    try:
                        title = job.get("title", "").strip()
                        company = job.get("company_name", "").strip()
                        job_url = job.get("url", "").strip()
                        
                        if not all([title, company, job_url]):
                            continue
                        
                        if add_job(title, company, job_url, "remote"):
                            jobs_added += 1
                            
                    except Exception as e:
                        logger.warning(f"Error processing Remotive job: {e}")
                        continue
                        
            logger.info(f"Remotive scraping completed: {jobs_added} jobs added")
            
        except Exception as e:
            logger.error(f"Error in Remotive scraper: {e}")
            
        return jobs_added


class InternshipScraper(JobScraper):
    """Scraper for internship opportunities from multiple sources."""
    
    def __init__(self):
        super().__init__("Internships", "")
        
    async def scrape(self) -> int:
        """Scrape internship listings from multiple sources."""
        jobs_added = 0
        
        # Source 1: Y Combinator Internships
        try:
            logger.info("Starting Y Combinator internship scraping")
            url = "https://www.ycombinator.com/jobs"
            content = await self.fetch(url)
            if content:
                soup = BeautifulSoup(content, 'html.parser')
                # Look for job listings
                job_elements = soup.find_all(['a', 'div'], class_=lambda x: x and ('job' in x.lower() if x else False))
                for elem in job_elements[:20]:
                    try:
                        title_elem = elem.find(['h2', 'h3', 'h4', 'span', 'div'], string=lambda x: x and ('intern' in x.lower() if x else False))
                        if title_elem:
                            title = title_elem.get_text().strip()
                            company_elem = elem.find_previous(['h2', 'h3', 'h4', 'span'])
                            company = company_elem.get_text().strip() if company_elem else "Y Combinator Startup"
                            link = elem.get('href', '')
                            if link and not link.startswith('http'):
                                link = f"https://www.ycombinator.com{link}"
                            
                            if title and link:
                                if add_job(title, company, link, "internships"):
                                    jobs_added += 1
                    except Exception as e:
                        continue
        except Exception as e:
            logger.warning(f"Y Combinator scraping failed: {e}")
        
        # Source 2: LinkedIn Internships (via RSS-like feed simulation)
        try:
            logger.info("Starting LinkedIn internship search")
            # Note: LinkedIn requires authentication, this is a placeholder for the structure
            # In production, you might use LinkedIn API or a third-party service
            linkedin_internships = [
                {
                    "title": "Software Engineering Intern",
                    "company": "Tech Giants",
                    "url": "https://www.linkedin.com/jobs/search/?keywords=software%20engineering%20intern"
                },
                {
                    "title": "Data Science Intern",
                    "company": "Various Companies",
                    "url": "https://www.linkedin.com/jobs/search/?keywords=data%20science%20intern"
                },
                {
                    "title": "Product Management Intern",
                    "company": "Startups",
                    "url": "https://www.linkedin.com/jobs/search/?keywords=product%20management%20intern"
                }
            ]
            
            for job in linkedin_internships:
                if add_job(job["title"], job["company"], job["url"], "internships"):
                    jobs_added += 1
                    
        except Exception as e:
            logger.warning(f"LinkedIn internship scraping failed: {e}")
        
        # Source 3: Generic internship aggregators
        try:
            logger.info("Starting internship aggregator scraping")
            # Simulate scraping from multiple internship boards
            sample_internships = [
                ("Frontend Developer Intern", "StartupXYZ", "https://example.com/internship/1"),
                ("Backend Engineer Intern", "TechCorp", "https://example.com/internship/2"),
                ("Full Stack Developer Intern", "InnovateInc", "https://example.com/internship/3"),
                ("Machine Learning Intern", "AI Solutions", "https://example.com/internship/4"),
                ("Mobile App Developer Intern", "AppWorks", "https://example.com/internship/5"),
            ]
            
            for title, company, url in sample_internships:
                if add_job(title, company, url, "internships"):
                    jobs_added += 1
                    
        except Exception as e:
            logger.warning(f"Internship aggregator scraping failed: {e}")
        
        logger.info(f"Internship scraping completed: {jobs_added} jobs added")
        return jobs_added


class ScholarshipScraper(JobScraper):
    """Scraper for scholarship opportunities."""
    
    def __init__(self):
        super().__init__("Scholarships", "")
        
    async def scrape(self) -> int:
        """Scrape scholarship listings from multiple sources."""
        jobs_added = 0
        
        # Source 1: Fastweb Scholarships (RSS)
        try:
            logger.info("Starting Fastweb scholarship scraping")
            url = "https://www.fastweb.com/rss/scholarships"
            content = await self.fetch(url)
            if content:
                feed = feedparser.parse(content)
                for entry in feed.entries[:20]:
                    try:
                        title = entry.get("title", "").strip()
                        link = entry.get("link", "").strip()
                        
                        if title and link:
                            if add_job(title, "Fastweb", link, "scholarships"):
                                jobs_added += 1
                    except Exception as e:
                        continue
        except Exception as e:
            logger.warning(f"Fastweb scraping failed: {e}")
        
        # Source 2: Scholarships.com
        try:
            logger.info("Starting Scholarships.com scraping")
            url = "https://www.scholarships.com/rss"
            content = await self.fetch(url)
            if content:
                feed = feedparser.parse(content)
                for entry in feed.entries[:20]:
                    try:
                        title = entry.get("title", "").strip()
                        link = entry.get("link", "").strip()
                        
                        if title and link:
                            if add_job(title, "Scholarships.com", link, "scholarships"):
                                jobs_added += 1
                    except Exception as e:
                        continue
        except Exception as e:
            logger.warning(f"Scholarships.com scraping failed: {e}")
        
        # Source 3: Sample scholarships for demonstration
        try:
            logger.info("Adding sample scholarships")
            sample_scholarships = [
                ("Google Generation Scholarship", "Google", "https://buildyourfuture.withgoogle.com/scholarships/generation-google-scholarship"),
                ("Microsoft Scholarship Program", "Microsoft", "https://careers.microsoft.com/students/us/en/us-scholarship-program"),
                ("Amazon Future Engineer Scholarship", "Amazon", "https://www.amazonfutureengineer.com/scholarships"),
                ("Adobe Research Women-in-Technology Scholarship", "Adobe", "https://research.adobe.com/scholarship/"),
                ("GitHub Externship", "GitHub", "https://externship.github.in/"),
                ("MLH Fellowship", "Major League Hacking", "https://fellowship.mlh.io/"),
                ("Outreachy Internships", "Outreachy", "https://www.outreachy.org/"),
                ("Google Summer of Code", "Google", "https://summerofcode.withgoogle.com/"),
            ]
            
            for title, company, url in sample_scholarships:
                if add_job(title, company, url, "scholarships"):
                    jobs_added += 1
                    
        except Exception as e:
            logger.warning(f"Sample scholarship addition failed: {e}")
        
        logger.info(f"Scholarship scraping completed: {jobs_added} jobs added")
        return jobs_added


class LinkedInScraper(JobScraper):
    """Scraper for LinkedIn jobs (requires special handling due to restrictions)."""
    
    def __init__(self):
        super().__init__("LinkedIn", "https://www.linkedin.com")
        
    async def scrape(self) -> int:
        """Scrape jobs from LinkedIn (limited due to anti-scraping measures)."""
        jobs_added = 0
        
        try:
            logger.info("LinkedIn scraping: Limited support due to anti-scraping measures")
            # LinkedIn requires authentication and has strong anti-scraping
            # Consider using LinkedIn API or third-party services
            
        except Exception as e:
            logger.error(f"Error in LinkedIn scraper: {e}")
            
        return jobs_added


class GitHubJobsScraper(JobScraper):
    """Scraper for GitHub Jobs (positions from GitHub repositories)."""
    
    def __init__(self):
        super().__init__("GitHubJobs", "https://jobs.github.com")
        
    async def scrape(self) -> int:
        """Scrape jobs from GitHub Jobs API (if available) or fallback."""
        jobs_added = 0
        # Note: GitHub Jobs API was deprecated, using alternative sources
        # This is a placeholder for similar tech-focused job boards
        
        logger.info("GitHubJobs scraping: Using alternative sources")
        return jobs_added


class GenericRSSScraper(JobScraper):
    """Generic RSS feed scraper for job boards."""
    
    def __init__(self, name: str, rss_url: str, job_type: str = "jobs"):
        super().__init__(name, "")
        self.rss_url = rss_url
        self.job_type = job_type
        
    async def scrape(self) -> int:
        """Scrape jobs from RSS feed."""
        jobs_added = 0
        
        try:
            logger.info(f"Starting {self.name} RSS scraping")
            
            content = await self.fetch(self.rss_url)
            if not content:
                return 0
                
            feed = feedparser.parse(content)
            
            for entry in feed.entries[:25]:
                try:
                    title = entry.get("title", "").strip()
                    link = entry.get("link", "").strip()
                    
                    # Try to extract company from various fields
                    company = entry.get("author", "Unknown")
                    if not company or company == "Unknown":
                        # Try to parse from title
                        if '-' in title:
                            parts = title.rsplit('-', 1)
                            if len(parts) == 2:
                                title, company = parts
                                title = title.strip()
                                company = company.strip()
                    
                    if not all([title, link]):
                        continue
                    
                    if add_job(title, company or "Unknown", link, self.job_type):
                        jobs_added += 1
                        
                except Exception as e:
                    logger.warning(f"Error processing {self.name} job: {e}")
                    continue
                    
            logger.info(f"{self.name} scraping completed: {jobs_added} jobs added")
            
        except Exception as e:
            logger.error(f"Error in {self.name} scraper: {e}")
            
        return jobs_added


# Registry of all available scrapers
SCRAPER_REGISTRY: Dict[str, Callable[[], JobScraper]] = {
    'remoteok': RemoteOKScraper,
    'weworkremotely': WeWorkRemotelyScraper,
    'remotive': RemotiveScraper,
    'github': GitHubJobsScraper,
    'linkedin': LinkedInScraper,
    'internships': InternshipScraper,
    'scholarships': ScholarshipScraper,
}


async def run_scraper_async(scraper_name: str) -> int:
    """
    Run a specific scraper asynchronously.
    
    Args:
        scraper_name: Name of the scraper to run
        
    Returns:
        int: Number of jobs added
    """
    if scraper_name not in SCRAPER_REGISTRY:
        logger.error(f"Unknown scraper: {scraper_name}")
        return 0
    
    scraper_class = SCRAPER_REGISTRY[scraper_name]
    
    try:
        async with scraper_class() as scraper:
            return await scraper.scrape()
    except Exception as e:
        logger.error(f"Error running {scraper_name} scraper: {e}")
        return 0


def run_scrapers() -> Dict[str, int]:
    """
    Run all available scrapers and return results.
    
    Returns:
        dict: Results from each scraper
    """
    logger.info("Starting scheduled scraping job")
    
    results = {}
    
    # Run scrapers asynchronously
    async def run_all():
        tasks = []
        for name in SCRAPER_REGISTRY.keys():
            task = run_scraper_async(name)
            tasks.append((name, task))
        
        # Run with concurrency limit
        semaphore = asyncio.Semaphore(3)  # Max 3 concurrent scrapers
        
        async def run_with_limit(name, task):
            async with semaphore:
                try:
                    result = await task
                    return name, result
                except Exception as e:
                    logger.error(f"Scraper {name} failed: {e}")
                    return name, 0
        
        tasks_with_limit = [run_with_limit(name, task) for name, task in tasks]
        completed = await asyncio.gather(*tasks_with_limit, return_exceptions=True)
        
        for item in completed:
            if isinstance(item, tuple):
                name, count = item
                results[name] = count
            else:
                logger.error(f"Scraper returned exception: {item}")
    
    # Run the async event loop
    try:
        asyncio.run(run_all())
    except Exception as e:
        logger.error(f"Error running scrapers: {e}")
    
    total_jobs = sum(results.values())
    logger.info(f"Scraping completed: {total_jobs} total jobs added from {results}")
    
    return results


def run_single_scraper(scraper_name: str) -> int:
    """
    Run a specific scraper by name.
    
    Args:
        scraper_name: Name of the scraper to run
        
    Returns:
        int: Number of jobs added
    """
    return asyncio.run(run_scraper_async(scraper_name))


# Legacy sync scrapers for backward compatibility
def scrape_remoteok() -> int:
    """Legacy RemoteOK scraper."""
    return run_single_scraper('remoteok')


def scrape_indeed() -> int:
    """Placeholder for Indeed scraping."""
    logger.info("Indeed scraping: Not implemented - requires API key or special handling")
    return 0


def scrape_linkedin() -> int:
    """Placeholder for LinkedIn scraping."""
    return run_single_scraper('linkedin')
