"""Prometheus metrics and health check endpoints."""

import time
from typing import Optional, Callable, Any
from functools import wraps
from dataclasses import dataclass
from enum import Enum

try:
    from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

from utils.structured_logging import get_logger

logger = get_logger(__name__)


class HealthStatus(Enum):
    """Health check status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheck:
    """Health check result."""
    name: str
    status: HealthStatus
    message: str
    response_time_ms: float
    metadata: Optional[dict] = None


# Prometheus metrics (only created if prometheus_client is available)
if PROMETHEUS_AVAILABLE:
    # Request metrics
    REQUEST_COUNT = Counter(
        'job_bot_requests_total',
        'Total requests',
        ['method', 'endpoint', 'status']
    )
    
    REQUEST_DURATION = Histogram(
        'job_bot_request_duration_seconds',
        'Request duration in seconds',
        ['method', 'endpoint']
    )
    
    # Scraper metrics
    SCRAPER_JOBS_ADDED = Counter(
        'job_bot_scraper_jobs_added_total',
        'Total jobs added by scraper',
        ['source']
    )
    
    SCRAPER_ERRORS = Counter(
        'job_bot_scraper_errors_total',
        'Total scraper errors',
        ['source', 'error_type']
    )
    
    SCRAPER_DURATION = Histogram(
        'job_bot_scraper_duration_seconds',
        'Scraper execution duration',
        ['source']
    )
    
    # Bot metrics
    MESSAGES_SENT = Counter(
        'job_bot_messages_sent_total',
        'Total messages sent',
        ['type']
    )
    
    MESSAGES_FAILED = Counter(
        'job_bot_messages_failed_total',
        'Total failed messages',
        ['type', 'error']
    )
    
    # Database metrics
    DB_CONNECTIONS = Gauge(
        'job_bot_db_connections',
        'Current database connections'
    )
    
    DB_QUERY_DURATION = Histogram(
        'job_bot_db_query_duration_seconds',
        'Database query duration'
    )
    
    # User metrics
    ACTIVE_USERS = Gauge(
        'job_bot_active_users',
        'Number of active users'
    )
    
    TOTAL_JOBS = Gauge(
        'job_bot_total_jobs',
        'Total number of jobs in database',
        ['category']
    )
    
    # Circuit breaker metrics
    CIRCUIT_BREAKER_STATE = Gauge(
        'job_bot_circuit_breaker_state',
        'Circuit breaker state (0=closed, 1=half-open, 2=open)',
        ['name']
    )
    
    # Application info
    APP_INFO = Info('job_bot', 'Application information')
else:
    # Dummy metrics for when prometheus is not available
    class DummyMetric:
        def inc(self, *args, **kwargs): pass
        def observe(self, *args, **kwargs): pass
        def set(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
        def info(self, *args, **kwargs): pass
    
    REQUEST_COUNT = DummyMetric()
    REQUEST_DURATION = DummyMetric()
    SCRAPER_JOBS_ADDED = DummyMetric()
    SCRAPER_ERRORS = DummyMetric()
    SCRAPER_DURATION = DummyMetric()
    MESSAGES_SENT = DummyMetric()
    MESSAGES_FAILED = DummyMetric()
    DB_CONNECTIONS = DummyMetric()
    DB_QUERY_DURATION = DummyMetric()
    ACTIVE_USERS = DummyMetric()
    TOTAL_JOBS = DummyMetric()
    CIRCUIT_BREAKER_STATE = DummyMetric()
    APP_INFO = DummyMetric()


class MetricsCollector:
    """Collect and expose metrics."""
    
    def __init__(self):
        self.health_checks: dict[str, Callable[[], HealthCheck]] = {}
        self.start_time = time.time()
        
    def register_health_check(self, name: str, check_func: Callable[[], HealthCheck]) -> None:
        """Register a health check function.
        
        Args:
            name: Health check name
            check_func: Function that returns HealthCheck
        """
        self.health_checks[name] = check_func
        logger.info(f"Registered health check: {name}")
        
    async def run_health_checks(self) -> dict:
        """Run all registered health checks.
        
        Returns:
            Dictionary with health check results
        """
        results = {
            "status": HealthStatus.HEALTHY.value,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "uptime_seconds": int(time.time() - self.start_time),
            "checks": {}
        }
        
        for name, check_func in self.health_checks.items():
            start = time.time()
            try:
                check = check_func()
                check.response_time_ms = (time.time() - start) * 1000
                
                results["checks"][name] = {
                    "status": check.status.value,
                    "message": check.message,
                    "response_time_ms": round(check.response_time_ms, 2),
                    "metadata": check.metadata or {}
                }
                
                # Update overall status
                if check.status == HealthStatus.UNHEALTHY:
                    results["status"] = HealthStatus.UNHEALTHY.value
                elif check.status == HealthStatus.DEGRADED and results["status"] == HealthStatus.HEALTHY.value:
                    results["status"] = HealthStatus.DEGRADED.value
                    
            except Exception as e:
                results["checks"][name] = {
                    "status": HealthStatus.UNHEALTHY.value,
                    "message": f"Health check failed: {str(e)}",
                    "response_time_ms": round((time.time() - start) * 1000, 2),
                    "metadata": {}
                }
                results["status"] = HealthStatus.UNHEALTHY.value
                
        return results
    
    def get_prometheus_metrics(self) -> tuple[str, str]:
        """Get Prometheus-formatted metrics.
        
        Returns:
            Tuple of (content, content_type)
        """
        if not PROMETHEUS_AVAILABLE:
            return "# Prometheus client not installed", "text/plain"
        
        return generate_latest().decode('utf-8'), CONTENT_TYPE_LATEST


# Global metrics collector
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create global metrics collector."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
        
        # Set app info
        APP_INFO.info({
            'version': '2.0.0',
            'name': 'job-alert-bot'
        })
        
    return _metrics_collector


def track_request_duration(method: str, endpoint: str):
    """Decorator to track request duration."""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                status = "success"
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start
                REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)
                REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
        return wrapper
    return decorator


def track_scraper_duration(source: str):
    """Decorator to track scraper execution."""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                if isinstance(result, int):
                    SCRAPER_JOBS_ADDED.labels(source=source).inc(result)
                return result
            except Exception as e:
                SCRAPER_ERRORS.labels(source=source, error_type=type(e).__name__).inc()
                raise
            finally:
                duration = time.time() - start
                SCRAPER_DURATION.labels(source=source).observe(duration)
        return wrapper
    return decorator


def update_circuit_breaker_metric(name: str, state: str) -> None:
    """Update circuit breaker state metric.
    
    Args:
        name: Circuit breaker name
        state: Circuit state (closed, half_open, open)
    """
    state_map = {
        "closed": 0,
        "half_open": 1,
        "open": 2
    }
    CIRCUIT_BREAKER_STATE.labels(name=name).set(state_map.get(state, 0))
