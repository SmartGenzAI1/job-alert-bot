from datetime import datetime
import logging
from typing import Optional, List, Tuple
from .db import get_db_connection

logger = logging.getLogger(__name__)


# ---------- USERS ----------

def add_user(uid: int, name: str) -> bool:
    """
    Add a new user to the database.
    
    Args:
        uid: Telegram user ID
        name: User's full name
        
    Returns:
        bool: True if user was added, False if user already exists
    """
    try:
        if not isinstance(uid, int) or uid <= 0:
            logger.error(f"Invalid user ID: {uid}")
            return False
        
        if not name or not name.strip():
            logger.error("User name cannot be empty")
            return False
        
        # Sanitize name to prevent SQL injection
        name = name.strip()[:100]  # Limit name length
        
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT OR IGNORE INTO users VALUES(?,?,?,?)",
                (uid, name, "jobs", datetime.utcnow().isoformat())
            )
            
            if cur.rowcount > 0:
                logger.info(f"New user registered: {uid} - {name}")
                return True
            else:
                logger.debug(f"User already exists: {uid}")
                return False
            
    except Exception as e:
        logger.error(f"Error adding user {uid}: {e}")
        return False


def set_category(uid: int, cat: str) -> bool:
    """
    Set the job category preference for a user.
    
    Args:
        uid: Telegram user ID
        cat: Job category (jobs, remote, internships, scholarships)
        
    Returns:
        bool: True if category was updated, False otherwise
    """
    try:
        if not isinstance(uid, int) or uid <= 0:
            logger.error(f"Invalid user ID: {uid}")
            return False
        
        valid_categories = ["jobs", "remote", "internships", "scholarships"]
        if cat not in valid_categories:
            logger.error(f"Invalid category: {cat}")
            return False
        
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE users SET category=? WHERE telegram_id=?", (cat, uid))
            
            if cur.rowcount > 0:
                logger.info(f"User {uid} category updated to: {cat}")
                return True
            else:
                logger.warning(f"User {uid} not found for category update")
                return False
            
    except Exception as e:
        logger.error(f"Error updating category for user {uid}: {e}")
        return False


def get_users() -> List[Tuple[int, str]]:
    """
    Get all registered users and their categories.
    
    Returns:
        List of tuples containing (telegram_id, category)
    """
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            return cur.execute("SELECT telegram_id, category FROM users").fetchall()
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        return []


def get_user_count() -> int:
    """
    Get the total number of registered users.
    
    Returns:
        int: Number of users
    """
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            result = cur.execute("SELECT COUNT(*) FROM users").fetchone()
            return result[0] if result else 0
    except Exception as e:
        logger.error(f"Error counting users: {e}")
        return 0


# ---------- JOBS ----------

def add_job(title: str, company: str, link: str, typ: str) -> bool:
    """
    Add a new job listing to the database.
    
    Args:
        title: Job title
        company: Company name
        link: Job posting URL
        typ: Job type/category
        
    Returns:
        bool: True if job was added, False if duplicate or error occurred
    """
    try:
        if not all([title, company, link, typ]):
            logger.error("All job fields are required")
            return False
        
        # Sanitize inputs
        title = title.strip()[:200]
        company = company.strip()[:100]
        link = link.strip()[:500]
        
        valid_types = ["jobs", "remote", "internships", "scholarships"]
        if typ not in valid_types:
            logger.error(f"Invalid job type: {typ}")
            return False
        
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO jobs(title,company,link,type,created_at) VALUES(?,?,?,?,?)",
                (title, company, link, typ, datetime.utcnow().isoformat())
            )
            
            if cur.rowcount > 0:
                logger.info(f"New job added: {title} at {company}")
                return True
            else:
                logger.debug(f"Job already exists: {link}")
                return False
            
    except Exception as e:
        logger.error(f"Error adding job: {e}")
        return False


def get_latest_jobs(typ: str, limit: int = 10) -> List[Tuple[str, str, str]]:
    """
    Get the latest job listings for a specific type.
    
    Args:
        typ: Job type/category
        limit: Maximum number of jobs to return
        
    Returns:
        List of tuples containing (title, company, link)
    """
    try:
        valid_types = ["jobs", "remote", "internships", "scholarships"]
        if typ not in valid_types:
            logger.error(f"Invalid job type: {typ}")
            return []
        
        if limit <= 0 or limit > 100:
            limit = 10
        
        with get_db_connection() as conn:
            cur = conn.cursor()
            return cur.execute(
                "SELECT title,company,link FROM jobs WHERE type=? ORDER BY id DESC LIMIT ?",
                (typ, limit)
            ).fetchall()
        
    except Exception as e:
        logger.error(f"Error fetching jobs for type {typ}: {e}")
        return []


def get_job_count(typ: Optional[str] = None) -> int:
    """
    Get the total number of jobs, optionally filtered by type.
    
    Args:
        typ: Job type to filter by (optional)
        
    Returns:
        int: Number of jobs
    """
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            if typ:
                result = cur.execute("SELECT COUNT(*) FROM jobs WHERE type=?", (typ,)).fetchone()
            else:
                result = cur.execute("SELECT COUNT(*) FROM jobs").fetchone()
            return result[0] if result else 0
    except Exception as e:
        logger.error(f"Error counting jobs: {e}")
        return 0


def cleanup_old_jobs(days: int = 30) -> int:
    """
    Remove job listings older than specified days.
    
    Args:
        days: Number of days to keep job listings
        
    Returns:
        int: Number of jobs deleted
    """
    try:
        from datetime import timedelta
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM jobs WHERE created_at < ?", (cutoff_date,))
            
            deleted_count = cur.rowcount
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old job listings")
            
            return deleted_count
        
    except Exception as e:
        logger.error(f"Error cleaning up old jobs: {e}")
        return 0
