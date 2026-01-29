import sqlite3
import logging
import os
from contextlib import contextmanager
from typing import Optional, Generator
from config import DB_FILE
from utils.logger import logger

# Global connection and cursor
_conn: Optional[sqlite3.Connection] = None
_cur: Optional[sqlite3.Cursor] = None


def init_db():
    """Initialize the database connection and create tables if they don't exist."""
    global _conn, _cur
    
    try:
        # Ensure database directory exists
        db_dir = os.path.dirname(DB_FILE)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        
        # Initialize connection
        _conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        _conn.row_factory = sqlite3.Row  # Enable dict-like access
        _cur = _conn.cursor()
        
        # Create tables
        create_users_table()
        create_jobs_table()
        
        # Create indexes for better performance
        create_indexes()
        
        logger.info(f"Database initialized successfully at {DB_FILE}")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def create_users_table():
    """Create the users table."""
    if _cur is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    _cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        telegram_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT DEFAULT 'jobs',
        joined_at TEXT NOT NULL
    )
    """)


def create_jobs_table():
    """Create the jobs table."""
    if _cur is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    _cur.execute("""
    CREATE TABLE IF NOT EXISTS jobs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        company TEXT NOT NULL,
        link TEXT UNIQUE NOT NULL,
        type TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)


def create_indexes():
    """Create database indexes for better performance."""
    try:
        if _cur is None:
            raise RuntimeError("Database not initialized. Call init_db() first.")
            
        # Index for jobs by type and created_at for faster queries
        _cur.execute("CREATE INDEX IF NOT EXISTS idx_jobs_type_created ON jobs(type, created_at)")
        
        # Index for jobs by type for category filtering
        _cur.execute("CREATE INDEX IF NOT EXISTS idx_jobs_type ON jobs(type)")
        
        # Index for users by category
        _cur.execute("CREATE INDEX IF NOT EXISTS idx_users_category ON users(category)")
        
        if _conn:
            _conn.commit()
        logger.debug("Database indexes created successfully")
        
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")
        if _conn:
            _conn.rollback()


def get_connection() -> sqlite3.Connection:
    """Get the global database connection."""
    if _conn is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _conn


def get_cursor() -> sqlite3.Cursor:
    """Get the global database cursor."""
    if _cur is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _cur


@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager for database connections.
    Ensures proper connection handling and error management.
    """
    try:
        if _conn is None:
            raise RuntimeError("Database not initialized. Call init_db() first.")
        
        yield _conn
        _conn.commit()
    except Exception as e:
        if _conn:
            _conn.rollback()
        logger.error(f"Database transaction failed: {e}")
        raise


def close_db():
    """Close the database connection."""
    global _conn, _cur
    if _conn:
        try:
            _conn.close()
        except Exception as e:
            logger.error(f"Error closing database connection: {e}")
        finally:
            _conn = None
            _cur = None
        logger.info("Database connection closed")


def backup_db(backup_path: str):
    """
    Create a backup of the database.
    
    Args:
        backup_path: Path where the backup should be saved
    """
    try:
        if _conn is None:
            raise RuntimeError("Database not initialized")
        
        backup_conn = sqlite3.connect(backup_path)
        _conn.backup(backup_conn)
        backup_conn.close()
        logger.info(f"Database backup created at {backup_path}")
        
    except Exception as e:
        logger.error(f"Failed to create database backup: {e}")
        raise


def get_db_stats() -> dict:
    """
    Get database statistics for monitoring.
    
    Returns:
        dict: Database statistics
    """
    try:
        if _cur is None:
            raise RuntimeError("Database not initialized")
        
        stats = {}
        
        # User statistics
        _cur.execute("SELECT COUNT(*) FROM users")
        result = _cur.fetchone()
        stats['total_users'] = result[0] if result else 0
        
        # Job statistics
        _cur.execute("SELECT COUNT(*) FROM jobs")
        result = _cur.fetchone()
        stats['total_jobs'] = result[0] if result else 0
        
        # Jobs by type
        _cur.execute("SELECT type, COUNT(*) FROM jobs GROUP BY type")
        stats['jobs_by_type'] = dict(_cur.fetchall())
        
        # Recent jobs (last 24 hours)
        from datetime import datetime, timedelta
        yesterday = (datetime.utcnow() - timedelta(hours=24)).isoformat()
        _cur.execute("SELECT COUNT(*) FROM jobs WHERE created_at >= ?", (yesterday,))
        result = _cur.fetchone()
        stats['recent_jobs'] = result[0] if result else 0
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        return {}
