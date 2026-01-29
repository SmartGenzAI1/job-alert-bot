"""Thread-safe database connection pool with transaction management."""

import sqlite3
import threading
import queue
import logging
from typing import Optional, Generator, Any
from contextlib import contextmanager
from dataclasses import dataclass
from utils.structured_logging import get_logger

logger = get_logger(__name__)


@dataclass
class PoolConfig:
    """Configuration for connection pool."""
    max_connections: int = 10
    timeout: float = 30.0
    check_same_thread: bool = False
    isolation_level: Optional[str] = None  # None = autocommit mode


class ConnectionPool:
    """Thread-safe SQLite connection pool."""
    
    def __init__(self, db_path: str, config: Optional[PoolConfig] = None):
        self.db_path = db_path
        self.config = config or PoolConfig()
        self._pool: queue.Queue[sqlite3.Connection] = queue.Queue(
            maxsize=self.config.max_connections
        )
        self._lock = threading.RLock()
        self._connections_created = 0
        self._local = threading.local()
        
    def _create_connection(self) -> sqlite3.Connection:
        """Create a new database connection."""
        conn = sqlite3.connect(
            self.db_path,
            timeout=self.config.timeout,
            check_same_thread=self.config.check_same_thread,
            isolation_level=self.config.isolation_level
        )
        conn.row_factory = sqlite3.Row
        
        # Enable WAL mode for better concurrency
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=10000")
        conn.execute("PRAGMA temp_store=MEMORY")
        
        self._connections_created += 1
        logger.debug(f"Created new connection #{self._connections_created}")
        
        return conn
    
    def get_connection(self) -> sqlite3.Connection:
        """Get a connection from the pool or create a new one."""
        # Check for thread-local connection (for nested transactions)
        if hasattr(self._local, 'connection') and self._local.connection:
            return self._local.connection
        
        try:
            # Try to get from pool without blocking
            conn = self._pool.get_nowait()
            logger.debug("Got connection from pool")
            return conn
        except queue.Empty:
            with self._lock:
                if self._connections_created < self.config.max_connections:
                    return self._create_connection()
            
            # Wait for a connection
            logger.debug("Waiting for available connection...")
            conn = self._pool.get(timeout=self.config.timeout)
            return conn
    
    def return_connection(self, conn: sqlite3.Connection, is_broken: bool = False) -> None:
        """Return a connection to the pool.
        
        Args:
            conn: Connection to return
            is_broken: Whether connection should be discarded
        """
        # Don't return thread-local connections
        if hasattr(self._local, 'connection') and self._local.connection is conn:
            return
        
        if is_broken:
            try:
                conn.close()
            except Exception:  # nosec B110 - Intentionally suppressing close errors
                pass  # Best effort cleanup, ignore errors on close
            self._connections_created -= 1
            logger.debug("Closed broken connection")
            return
        
        try:
            self._pool.put_nowait(conn)
            logger.debug("Returned connection to pool")
        except queue.Full:
            conn.close()
            self._connections_created -= 1
            logger.debug("Pool full, closed connection")
    
    def close_all(self) -> None:
        """Close all connections in the pool."""
        with self._lock:
            while not self._pool.empty():
                try:
                    conn = self._pool.get_nowait()
                    conn.close()
                except Exception as e:
                    logger.warning(f"Error closing connection: {e}")
            self._connections_created = 0
            logger.info("All connections closed")
    
    @contextmanager
    def acquire(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager for acquiring a connection."""
        conn = None
        is_broken = False
        try:
            conn = self.get_connection()
            yield conn
        except Exception as e:
            is_broken = True
            logger.error(f"Connection error: {e}")
            raise
        finally:
            if conn:
                self.return_connection(conn, is_broken)


class TransactionManager:
    """Manage database transactions with proper rollback/commit."""
    
    def __init__(self, pool: ConnectionPool):
        self.pool = pool
        self._local = threading.local()
    
    @contextmanager
    def transaction(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager for database transactions.
        
        Supports nested transactions using savepoints.
        """
        # Check if already in transaction
        if hasattr(self._local, 'connection') and self._local.connection:
            # Use savepoint for nested transaction
            conn = self._local.connection
            cursor = conn.cursor()
            savepoint_name = f"sp_{id(cursor)}"
            cursor.execute(f"SAVEPOINT {savepoint_name}")
            logger.debug(f"Created savepoint {savepoint_name}")
            
            try:
                yield conn
                cursor.execute(f"RELEASE SAVEPOINT {savepoint_name}")
                logger.debug(f"Released savepoint {savepoint_name}")
            except Exception as e:
                cursor.execute(f"ROLLBACK TO SAVEPOINT {savepoint_name}")
                logger.error(f"Rolled back to savepoint {savepoint_name}: {e}")
                raise
        else:
            # Start new transaction
            conn = self.pool.get_connection()
            self._local.connection = conn
            self._local.transaction_depth = 1
            
            try:
                conn.execute("BEGIN")
                logger.debug("Started transaction")
                yield conn
                conn.commit()
                logger.debug("Committed transaction")
            except Exception as e:
                conn.rollback()
                logger.error(f"Rolled back transaction: {e}")
                raise
            finally:
                self._local.connection = None
                self._local.transaction_depth = 0
                self.pool.return_connection(conn)
    
    def execute_with_retry(self, query: str, params: tuple = (), max_retries: int = 3) -> Any:
        """Execute query with automatic retry on database lock.
        
        Args:
            query: SQL query
            params: Query parameters
            max_retries: Maximum retry attempts
            
        Returns:
            Query result
        """
        for attempt in range(max_retries):
            try:
                with self.transaction() as conn:
                    cursor = conn.execute(query, params)
                    return cursor.fetchall()
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    import time
                    wait_time = 0.1 * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Database locked, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise


# Global pool instance
_pool: Optional[ConnectionPool] = None
_transaction_manager: Optional[TransactionManager] = None


def init_connection_pool(db_path: str, config: Optional[PoolConfig] = None) -> ConnectionPool:
    """Initialize global connection pool.
    
    Args:
        db_path: Path to database file
        config: Pool configuration
        
    Returns:
        ConnectionPool instance
    """
    global _pool, _transaction_manager
    _pool = ConnectionPool(db_path, config)
    _transaction_manager = TransactionManager(_pool)
    logger.info(f"Initialized connection pool for {db_path}")
    return _pool


def get_pool() -> ConnectionPool:
    """Get global connection pool.
    
    Returns:
        ConnectionPool instance
        
    Raises:
        RuntimeError: If pool not initialized
    """
    if _pool is None:
        raise RuntimeError("Connection pool not initialized. Call init_connection_pool() first.")
    return _pool


def get_transaction_manager() -> TransactionManager:
    """Get global transaction manager.
    
    Returns:
        TransactionManager instance
        
    Raises:
        RuntimeError: If not initialized
    """
    if _transaction_manager is None:
        raise RuntimeError("Transaction manager not initialized. Call init_connection_pool() first.")
    return _transaction_manager


@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """Get database connection from pool."""
    pool = get_pool()
    with pool.acquire() as conn:
        yield conn


@contextmanager
def transaction() -> Generator[sqlite3.Connection, None, None]:
    """Start a database transaction."""
    tm = get_transaction_manager()
    with tm.transaction() as conn:
        yield conn
