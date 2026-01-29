"""Configuration management for multiple environments."""

import os
from typing import Optional, List
from dataclasses import dataclass, field
from enum import Enum


class Environment(Enum):
    """Application environments."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


@dataclass
class DatabaseConfig:
    """Database configuration."""
    db_file: str = "database.db"
    max_connections: int = 10
    timeout: float = 30.0
    enable_wal: bool = True


@dataclass
class TelegramConfig:
    """Telegram bot configuration."""
    token: str = ""
    admin_id: int = 0
    webhook_base_url: str = ""
    webhook_token: str = ""
    
    def __post_init__(self):
        if not self.token:
            raise ValueError("TELEGRAM_TOKEN is required")
        if self.admin_id <= 0:
            raise ValueError("ADMIN_ID must be a positive integer")


@dataclass
class SchedulerConfig:
    """Scheduler configuration."""
    timezone: str = "Asia/Kolkata"
    scrape_interval_hours: int = 3
    daily_alert_hour: int = 9
    max_concurrent_scrapers: int = 3


@dataclass
class MessagingConfig:
    """Messaging configuration."""
    send_batch_size: int = 25
    send_batch_sleep: float = 0.6
    max_message_length: int = 4000
    rate_limit_per_second: int = 30


@dataclass
class ScraperConfig:
    """Scraper configuration."""
    request_timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    rate_limit_delay: float = 0.5
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: float = 60.0


@dataclass
class MonitoringConfig:
    """Monitoring and logging configuration."""
    log_level: str = "INFO"
    json_logging: bool = True
    enable_metrics: bool = True
    metrics_port: int = 9090
    health_check_interval: int = 30


@dataclass
class SecurityConfig:
    """Security configuration."""
    allowed_hosts: List[str] = field(default_factory=list)
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    enable_ssl: bool = True
    max_request_size: int = 10 * 1024 * 1024  # 10MB


@dataclass
class Config:
    """Main application configuration."""
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    telegram: TelegramConfig = field(default_factory=TelegramConfig)
    scheduler: SchedulerConfig = field(default_factory=SchedulerConfig)
    messaging: MessagingConfig = field(default_factory=MessagingConfig)
    scraper: ScraperConfig = field(default_factory=ScraperConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    
    @classmethod
    def from_env(cls) -> 'Config':
        """Load configuration from environment variables."""
        env = Environment(os.getenv("ENVIRONMENT", "development"))
        
        # Determine debug mode
        debug = os.getenv("DEBUG", "false").lower() == "true"
        if env == Environment.DEVELOPMENT:
            debug = True
            
        # Telegram config
        telegram = TelegramConfig(
            token=os.getenv("TELEGRAM_TOKEN", ""),
            admin_id=int(os.getenv("ADMIN_ID", "0")),
            webhook_base_url=os.getenv("WEBHOOK_BASE_URL", ""),
            webhook_token=os.getenv("WEBHOOK_TOKEN", ""),
        )
        
        # Database config
        database = DatabaseConfig(
            db_file=os.getenv("DB_FILE", "database.db"),
            max_connections=int(os.getenv("DB_MAX_CONNECTIONS", "10")),
            timeout=float(os.getenv("DB_TIMEOUT", "30.0")),
            enable_wal=os.getenv("DB_ENABLE_WAL", "true").lower() == "true",
        )
        
        # Scheduler config
        scheduler = SchedulerConfig(
            timezone=os.getenv("TIMEZONE", "Asia/Kolkata"),
            scrape_interval_hours=int(os.getenv("SCRAPE_INTERVAL_HOURS", "3")),
            daily_alert_hour=int(os.getenv("DAILY_ALERT_HOUR", "9")),
            max_concurrent_scrapers=int(os.getenv("MAX_CONCURRENT_SCRAPERS", "3")),
        )
        
        # Messaging config
        messaging = MessagingConfig(
            send_batch_size=int(os.getenv("SEND_BATCH_SIZE", "25")),
            send_batch_sleep=float(os.getenv("SEND_BATCH_SLEEP", "0.6")),
            max_message_length=int(os.getenv("MAX_MESSAGE_LENGTH", "4000")),
            rate_limit_per_second=int(os.getenv("RATE_LIMIT_PER_SECOND", "30")),
        )
        
        # Scraper config
        scraper = ScraperConfig(
            request_timeout=int(os.getenv("SCRAPER_TIMEOUT", "30")),
            max_retries=int(os.getenv("SCRAPER_MAX_RETRIES", "3")),
            retry_delay=float(os.getenv("SCRAPER_RETRY_DELAY", "1.0")),
            user_agent=os.getenv(
                "SCRAPER_USER_AGENT",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            ),
            rate_limit_delay=float(os.getenv("SCRAPER_RATE_LIMIT_DELAY", "0.5")),
            circuit_breaker_threshold=int(os.getenv("CIRCUIT_BREAKER_THRESHOLD", "5")),
            circuit_breaker_timeout=float(os.getenv("CIRCUIT_BREAKER_TIMEOUT", "60.0")),
        )
        
        # Monitoring config
        monitoring = MonitoringConfig(
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            json_logging=os.getenv("JSON_LOGGING", "true").lower() == "true",
            enable_metrics=os.getenv("ENABLE_METRICS", "true").lower() == "true",
            metrics_port=int(os.getenv("METRICS_PORT", "9090")),
            health_check_interval=int(os.getenv("HEALTH_CHECK_INTERVAL", "30")),
        )
        
        # Security config
        allowed_hosts_str = os.getenv("ALLOWED_HOSTS", "")
        allowed_hosts = [h.strip() for h in allowed_hosts_str.split(",") if h.strip()]
        
        cors_origins_str = os.getenv("CORS_ORIGINS", "*")
        cors_origins = [o.strip() for o in cors_origins_str.split(",") if o.strip()]
        
        security = SecurityConfig(
            allowed_hosts=allowed_hosts,
            cors_origins=cors_origins,
            enable_ssl=os.getenv("ENABLE_SSL", "true").lower() == "true",
            max_request_size=int(os.getenv("MAX_REQUEST_SIZE", str(10 * 1024 * 1024))),
        )
        
        return cls(
            environment=env,
            debug=debug,
            database=database,
            telegram=telegram,
            scheduler=scheduler,
            messaging=messaging,
            scraper=scraper,
            monitoring=monitoring,
            security=security,
        )
    
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == Environment.DEVELOPMENT
    
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == Environment.PRODUCTION
    
    def is_testing(self) -> bool:
        """Check if running in testing mode."""
        return self.environment == Environment.TESTING


# Global config instance
_config: Optional[Config] = None


def load_config() -> Config:
    """Load and cache configuration."""
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config


def get_config() -> Config:
    """Get cached configuration."""
    if _config is None:
        return load_config()
    return _config


def reload_config() -> Config:
    """Reload configuration from environment."""
    global _config
    _config = Config.from_env()
    return _config
