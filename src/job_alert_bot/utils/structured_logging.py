"""Structured logging with correlation IDs for request tracing."""

import logging
import json
import uuid
import sys
from typing import Any, Optional, Dict
from contextvars import ContextVar
from datetime import datetime
from pythonjsonlogger import jsonlogger

# Context variable for correlation ID
correlation_id: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


class CorrelationIdFilter(logging.Filter):
    """Add correlation ID to log records."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = correlation_id.get() or "no-correlation-id"
        return True


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter for structured logging."""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp
        log_record['timestamp'] = datetime.utcnow().isoformat()
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        log_record['source'] = f"{record.filename}:{record.lineno}"
        log_record['function'] = record.funcName
        
        # Add correlation ID
        log_record['correlation_id'] = getattr(record, 'correlation_id', 'no-correlation-id')
        
        # Add environment info
        log_record['service'] = 'job-alert-bot'
        log_record['version'] = '2.0.0'


def setup_structured_logging(log_level: str = "INFO", json_format: bool = True) -> logging.Logger:
    """Setup structured logging configuration.
    
    Args:
        log_level: Logging level
        json_format: Whether to use JSON formatting
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    logger.handlers = []
    
    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, log_level.upper()))
    
    # Add correlation ID filter
    handler.addFilter(CorrelationIdFilter())
    
    if json_format:
        # JSON formatter
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s'
        )
    else:
        # Human-readable formatter
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(correlation_id)s | %(name)s | %(message)s'
        )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


def get_correlation_id() -> str:
    """Get or create correlation ID for current context."""
    cid = correlation_id.get()
    if cid is None:
        cid = str(uuid.uuid4())
        correlation_id.set(cid)
    return cid


def set_correlation_id(cid: Optional[str] = None) -> str:
    """Set correlation ID for current context.
    
    Args:
        cid: Correlation ID to set (generates new if None)
        
    Returns:
        The correlation ID
    """
    if cid is None:
        cid = str(uuid.uuid4())
    correlation_id.set(cid)
    return cid


def clear_correlation_id() -> None:
    """Clear correlation ID from current context."""
    correlation_id.set(None)


class LogContext:
    """Context manager for correlation ID scoping."""
    
    def __init__(self, cid: Optional[str] = None):
        self.cid = cid or str(uuid.uuid4())
        self.token: Optional[Any] = None
        
    def __enter__(self) -> 'LogContext':
        self.token = correlation_id.set(self.cid)
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.token:
            correlation_id.reset(self.token)


class StructuredLogger:
    """Wrapper around standard logger with structured logging support."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        
    def _log(self, level: int, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log with extra fields."""
        if extra:
            # Merge extra fields into message for JSON logging
            structured_msg = {
                'message': message,
                'extra': extra
            }
            self.logger.log(level, json.dumps(structured_msg))
        else:
            self.logger.log(level, message)
            
    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        self._log(logging.DEBUG, message, extra)
        
    def info(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        self._log(logging.INFO, message, extra)
        
    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        self._log(logging.WARNING, message, extra)
        
    def error(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        self._log(logging.ERROR, message, extra)
        
    def critical(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        self._log(logging.CRITICAL, message, extra)
        
    def exception(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log exception with traceback."""
        if extra is None:
            extra = {}
        extra['exc_info'] = True
        self._log(logging.ERROR, message, extra)


def get_logger(name: str) -> StructuredLogger:
    """Get structured logger instance."""
    return StructuredLogger(name)
