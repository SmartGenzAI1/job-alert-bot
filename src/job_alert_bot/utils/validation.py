"""Input validation and sanitization utilities."""

import re
import html
from typing import Optional, List, Tuple, Any
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass
class ValidationResult:
    """Result of validation operation."""
    is_valid: bool
    value: Any
    error_message: Optional[str] = None


class Validator:
    """Input validation utilities."""
    
    # Regex patterns
    TELEGRAM_ID_PATTERN = re.compile(r'^\d+$')
    URL_PATTERN = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r'(\%27)|(\')|(\-\-)|(\%23)|(#)',
        r'((\%3D)|(=))[^\n]*((\%27)|(\')|(\-\-)|(\%3B)|(;))',
        r'\w*((\%27)|(\'))((\%6F)|o|(\%4F))((\%72)|r|(\%52))',
        r'((\%27)|(\'))union',
        r'exec(\s|\+)+(s|x)p\w+',
        r'UNION SELECT',
        r'INSERT INTO',
        r'DELETE FROM',
        r'DROP TABLE',
    ]
    
    @classmethod
    def validate_telegram_id(cls, user_id: Any) -> ValidationResult:
        """Validate Telegram user ID.
        
        Args:
            user_id: User ID to validate
            
        Returns:
            ValidationResult with validation status
        """
        if user_id is None:
            return ValidationResult(False, None, "User ID is required")
        
        try:
            uid = int(user_id)
            if uid <= 0:
                return ValidationResult(False, None, "User ID must be positive")
            return ValidationResult(True, uid)
        except (ValueError, TypeError):
            return ValidationResult(False, None, "User ID must be a valid integer")
    
    @classmethod
    def validate_username(cls, username: Optional[str]) -> ValidationResult:
        """Validate and sanitize username.
        
        Args:
            username: Username to validate
            
        Returns:
            ValidationResult with sanitized username
        """
        if not username:
            return ValidationResult(False, None, "Username is required")
        
        # Sanitize
        sanitized = html.escape(username.strip())
        
        # Check length
        if len(sanitized) > 100:
            sanitized = sanitized[:100]
        
        if len(sanitized) < 1:
            return ValidationResult(False, None, "Username cannot be empty")
        
        # Check for SQL injection
        if cls._contains_sql_injection(sanitized):
            return ValidationResult(False, None, "Invalid characters in username")
        
        return ValidationResult(True, sanitized)
    
    @classmethod
    def validate_url(cls, url: Optional[str]) -> ValidationResult:
        """Validate URL format.
        
        Args:
            url: URL to validate
            
        Returns:
            ValidationResult with validation status
        """
        if not url:
            return ValidationResult(False, None, "URL is required")
        
        url = url.strip()
        
        if len(url) > 500:
            return ValidationResult(False, None, "URL too long (max 500 chars)")
        
        if not cls.URL_PATTERN.match(url):
            return ValidationResult(False, None, "Invalid URL format")
        
        # Check for SQL injection
        if cls._contains_sql_injection(url):
            return ValidationResult(False, None, "Invalid characters in URL")
        
        return ValidationResult(True, url)
    
    @classmethod
    def validate_job_title(cls, title: Optional[str]) -> ValidationResult:
        """Validate job title.
        
        Args:
            title: Job title to validate
            
        Returns:
            ValidationResult with sanitized title
        """
        if not title:
            return ValidationResult(False, None, "Job title is required")
        
        # Sanitize
        sanitized = html.escape(title.strip())
        
        if len(sanitized) > 200:
            sanitized = sanitized[:200]
        
        if len(sanitized) < 2:
            return ValidationResult(False, None, "Job title too short")
        
        if cls._contains_sql_injection(sanitized):
            return ValidationResult(False, None, "Invalid characters in job title")
        
        return ValidationResult(True, sanitized)
    
    @classmethod
    def validate_company_name(cls, company: Optional[str]) -> ValidationResult:
        """Validate company name.
        
        Args:
            company: Company name to validate
            
        Returns:
            ValidationResult with sanitized company name
        """
        if not company:
            return ValidationResult(False, None, "Company name is required")
        
        # Sanitize
        sanitized = html.escape(company.strip())
        
        if len(sanitized) > 100:
            sanitized = sanitized[:100]
        
        if len(sanitized) < 1:
            return ValidationResult(False, None, "Company name cannot be empty")
        
        if cls._contains_sql_injection(sanitized):
            return ValidationResult(False, None, "Invalid characters in company name")
        
        return ValidationResult(True, sanitized)
    
    @classmethod
    def validate_category(cls, category: Optional[str]) -> ValidationResult:
        """Validate job category.
        
        Args:
            category: Category to validate
            
        Returns:
            ValidationResult with validated category
        """
        valid_categories = ["jobs", "remote", "internships", "scholarships"]
        
        if not category:
            return ValidationResult(False, None, "Category is required")
        
        category = category.strip().lower()
        
        if category not in valid_categories:
            return ValidationResult(
                False, 
                None, 
                f"Invalid category. Must be one of: {', '.join(valid_categories)}"
            )
        
        return ValidationResult(True, category)
    
    @classmethod
    def validate_message_text(cls, text: Optional[str], max_length: int = 4000) -> ValidationResult:
        """Validate message text for broadcasting.
        
        Args:
            text: Message text to validate
            max_length: Maximum allowed length
            
        Returns:
            ValidationResult with sanitized text
        """
        if not text:
            return ValidationResult(False, None, "Message text is required")
        
        # Sanitize
        sanitized = html.escape(text.strip())
        
        if len(sanitized) > max_length:
            return ValidationResult(
                False, 
                None, 
                f"Message too long (max {max_length} chars)"
            )
        
        if len(sanitized) < 1:
            return ValidationResult(False, None, "Message cannot be empty")
        
        if cls._contains_sql_injection(sanitized):
            return ValidationResult(False, None, "Invalid characters in message")
        
        return ValidationResult(True, sanitized)
    
    @classmethod
    def _contains_sql_injection(cls, value: str) -> bool:
        """Check if value contains SQL injection patterns.
        
        Args:
            value: String to check
            
        Returns:
            True if SQL injection detected
        """
        value_upper = value.upper()
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value_upper):
                return True
        return False
    
    @classmethod
    def sanitize_sql_input(cls, value: str) -> str:
        """Sanitize input for SQL queries.
        
        Args:
            value: Value to sanitize
            
        Returns:
            Sanitized value
        """
        # Remove null bytes
        value = value.replace('\x00', '')
        
        # Escape single quotes (though parameterized queries should be used)
        value = value.replace("'", "''")
        
        return value


class BatchValidator:
    """Batch validation utilities."""
    
    @staticmethod
    def validate_users_batch(users: List[Tuple[int, str]], max_batch_size: int = 100) -> ValidationResult:
        """Validate a batch of users.
        
        Args:
            users: List of (user_id, category) tuples
            max_batch_size: Maximum batch size
            
        Returns:
            ValidationResult
        """
        if not users:
            return ValidationResult(False, None, "No users provided")
        
        if len(users) > max_batch_size:
            return ValidationResult(
                False, 
                None, 
                f"Batch size exceeds maximum of {max_batch_size}"
            )
        
        validated_users = []
        for user in users:
            if not isinstance(user, tuple) or len(user) != 2:
                return ValidationResult(False, None, "Invalid user format")
            
            user_id, category = user
            
            # Validate user ID
            id_result = Validator.validate_telegram_id(user_id)
            if not id_result.is_valid:
                return ValidationResult(False, None, f"Invalid user ID: {id_result.error_message}")
            
            # Validate category
            cat_result = Validator.validate_category(category)
            if not cat_result.is_valid:
                return ValidationResult(False, None, f"Invalid category: {cat_result.error_message}")
            
            validated_users.append((id_result.value, cat_result.value))
        
        return ValidationResult(True, validated_users)
    
    @staticmethod
    def validate_jobs_batch(jobs: List[Tuple[str, str, str]], max_batch_size: int = 100) -> ValidationResult:
        """Validate a batch of jobs.
        
        Args:
            jobs: List of (title, company, link) tuples
            max_batch_size: Maximum batch size
            
        Returns:
            ValidationResult
        """
        if not jobs:
            return ValidationResult(False, None, "No jobs provided")
        
        if len(jobs) > max_batch_size:
            return ValidationResult(
                False, 
                None, 
                f"Batch size exceeds maximum of {max_batch_size}"
            )
        
        validated_jobs = []
        for job in jobs:
            if not isinstance(job, tuple) or len(job) != 3:
                return ValidationResult(False, None, "Invalid job format")
            
            title, company, link = job
            
            # Validate each field
            title_result = Validator.validate_job_title(title)
            if not title_result.is_valid:
                continue  # Skip invalid jobs
            
            company_result = Validator.validate_company_name(company)
            if not company_result.is_valid:
                company_result.value = "Unknown"
            
            link_result = Validator.validate_url(link)
            if not link_result.is_valid:
                continue  # Skip invalid jobs
            
            validated_jobs.append((
                title_result.value,
                company_result.value,
                link_result.value
            ))
        
        if not validated_jobs:
            return ValidationResult(False, None, "No valid jobs in batch")
        
        return ValidationResult(True, validated_jobs)
