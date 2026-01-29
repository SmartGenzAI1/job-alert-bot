"""Retry mechanism with exponential backoff for resilient operations."""

import asyncio
import random
from typing import Callable, TypeVar, Optional, Tuple, Type, Any
from functools import wraps
from dataclasses import dataclass
from utils.logger import logger

T = TypeVar('T')


@dataclass
class RetryConfig:
    """Configuration for retry mechanism."""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    jitter_max: float = 1.0
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,)
    on_retry: Optional[Callable[[Exception, int], None]] = None


class RetryExhaustedError(Exception):
    """Exception raised when all retry attempts are exhausted."""
    
    def __init__(self, message: str, last_exception: Optional[Exception] = None):
        super().__init__(message)
        self.last_exception = last_exception


async def retry_with_backoff(
    func: Callable[..., T],
    config: Optional[RetryConfig] = None,
    *args,
    **kwargs
) -> T:
    """Execute function with retry and exponential backoff.
    
    Args:
        func: Function to execute
        config: Retry configuration
        *args: Positional arguments for func
        **kwargs: Keyword arguments for func
        
    Returns:
        Result from func
        
    Raises:
        RetryExhaustedError: If all retries are exhausted
    """
    config = config or RetryConfig()
    last_exception: Optional[Exception] = None
    
    for attempt in range(1, config.max_attempts + 1):
        try:
            return await func(*args, **kwargs)
        except config.retryable_exceptions as e:
            last_exception = e
            
            if attempt == config.max_attempts:
                logger.error(f"All {config.max_attempts} retry attempts exhausted")
                raise RetryExhaustedError(
                    f"Failed after {config.max_attempts} attempts",
                    last_exception=e
                ) from e
            
            # Calculate delay with exponential backoff
            delay = min(
                config.base_delay * (config.exponential_base ** (attempt - 1)),
                config.max_delay
            )
            
            # Add jitter to prevent thundering herd
            if config.jitter:
                delay += random.uniform(0, config.jitter_max)
            
            logger.warning(
                f"Attempt {attempt}/{config.max_attempts} failed: {e}. "
                f"Retrying in {delay:.2f}s..."
            )
            
            if config.on_retry:
                config.on_retry(e, attempt)
            
            await asyncio.sleep(delay)
    
    # Should never reach here
    raise RetryExhaustedError("Unexpected end of retry loop", last_exception=last_exception)


def retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None
):
    """Decorator to add retry logic to a function.
    
    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Initial delay between retries
        max_delay: Maximum delay between retries
        retryable_exceptions: Exceptions that should trigger a retry
        on_retry: Callback function called on each retry
    """
    config = RetryConfig(
        max_attempts=max_attempts,
        base_delay=base_delay,
        max_delay=max_delay,
        retryable_exceptions=retryable_exceptions,
        on_retry=on_retry
    )
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            return await retry_with_backoff(func, config, *args, **kwargs)
        return wrapper
    return decorator


class AsyncRetryable:
    """Context manager for retryable operations."""
    
    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()
        self.attempt = 0
        self.last_exception: Optional[Exception] = None
        
    async def __aenter__(self) -> 'AsyncRetryable':
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        if exc_val is None:
            return True
            
        if not isinstance(exc_val, self.config.retryable_exceptions):
            return False
            
        self.attempt += 1
        self.last_exception = exc_val
        
        if self.attempt >= self.config.max_attempts:
            logger.error(f"All {self.config.max_attempts} retry attempts exhausted")
            return False
        
        delay = min(
            self.config.base_delay * (self.config.exponential_base ** (self.attempt - 1)),
            self.config.max_delay
        )
        
        if self.config.jitter:
            delay += random.uniform(0, self.config.jitter_max)
        
        logger.warning(
            f"Attempt {self.attempt}/{self.config.max_attempts} failed: {exc_val}. "
            f"Retrying in {delay:.2f}s..."
        )
        
        if self.config.on_retry:
            self.config.on_retry(exc_val, self.attempt)
        
        await asyncio.sleep(delay)
        return True  # Suppress exception and retry
