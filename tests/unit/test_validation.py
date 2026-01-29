"""Unit tests for validation utilities."""

import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from job_alert_bot.utils.validation import Validator, BatchValidator, ValidationResult


class TestValidator:
    """Test cases for Validator class."""
    
    def test_validate_telegram_id_valid(self):
        """Test valid Telegram ID validation."""
        result = Validator.validate_telegram_id(123456789)
        assert result.is_valid is True
        assert result.value == 123456789
        assert result.error_message is None
    
    def test_validate_telegram_id_none(self):
        """Test None Telegram ID validation."""
        result = Validator.validate_telegram_id(None)
        assert result.is_valid is False
        assert result.error_message == "User ID is required"
    
    def test_validate_telegram_id_zero(self):
        """Test zero Telegram ID validation."""
        result = Validator.validate_telegram_id(0)
        assert result.is_valid is False
        assert result.error_message == "User ID must be positive"
    
    def test_validate_telegram_id_negative(self):
        """Test negative Telegram ID validation."""
        result = Validator.validate_telegram_id(-1)
        assert result.is_valid is False
    
    def test_validate_telegram_id_string_number(self):
        """Test string number Telegram ID validation."""
        result = Validator.validate_telegram_id("123456789")
        assert result.is_valid is True
        assert result.value == 123456789
    
    def test_validate_telegram_id_invalid_string(self):
        """Test invalid string Telegram ID validation."""
        result = Validator.validate_telegram_id("not_a_number")
        assert result.is_valid is False
    
    def test_validate_username_valid(self):
        """Test valid username validation."""
        result = Validator.validate_username("John Doe")
        assert result.is_valid is True
        assert result.value == "John Doe"
    
    def test_validate_username_empty(self):
        """Test empty username validation."""
        result = Validator.validate_username("")
        assert result.is_valid is False
        assert result.error_message == "Username is required"
    
    def test_validate_username_none(self):
        """Test None username validation."""
        result = Validator.validate_username(None)
        assert result.is_valid is False
    
    def test_validate_username_too_long(self):
        """Test too long username validation."""
        long_name = "A" * 150
        result = Validator.validate_username(long_name)
        assert result.is_valid is True
        assert len(result.value) == 100  # Should be truncated
    
    def test_validate_username_html_escaping(self):
        """Test HTML escaping in username."""
        result = Validator.validate_username("<script>alert('xss')</script>")
        assert result.is_valid is True
        assert "<script>" not in result.value
    
    def test_validate_url_valid(self):
        """Test valid URL validation."""
        result = Validator.validate_url("https://example.com/job/123")
        assert result.is_valid is True
    
    def test_validate_url_invalid(self):
        """Test invalid URL validation."""
        result = Validator.validate_url("not_a_url")
        assert result.is_valid is False
    
    def test_validate_url_empty(self):
        """Test empty URL validation."""
        result = Validator.validate_url("")
        assert result.is_valid is False
    
    def test_validate_url_too_long(self):
        """Test too long URL validation."""
        long_url = "https://example.com/" + "a" * 500
        result = Validator.validate_url(long_url)
        assert result.is_valid is False
    
    def test_validate_job_title_valid(self):
        """Test valid job title validation."""
        result = Validator.validate_job_title("Software Engineer")
        assert result.is_valid is True
    
    def test_validate_job_title_empty(self):
        """Test empty job title validation."""
        result = Validator.validate_job_title("")
        assert result.is_valid is False
    
    def test_validate_job_title_too_short(self):
        """Test too short job title validation."""
        result = Validator.validate_job_title("A")
        assert result.is_valid is False
    
    def test_validate_company_name_valid(self):
        """Test valid company name validation."""
        result = Validator.validate_company_name("Acme Corp")
        assert result.is_valid is True
    
    def test_validate_company_name_empty(self):
        """Test empty company name validation."""
        result = Validator.validate_company_name("")
        assert result.is_valid is False
    
    def test_validate_category_valid(self):
        """Test valid category validation."""
        for cat in ["jobs", "remote", "internships", "scholarships"]:
            result = Validator.validate_category(cat)
            assert result.is_valid is True
            assert result.value == cat
    
    def test_validate_category_invalid(self):
        """Test invalid category validation."""
        result = Validator.validate_category("invalid_category")
        assert result.is_valid is False
    
    def test_validate_category_case_insensitive(self):
        """Test category validation is case insensitive."""
        result = Validator.validate_category("JOBS")
        assert result.is_valid is True
        assert result.value == "jobs"
    
    def test_validate_message_text_valid(self):
        """Test valid message text validation."""
        result = Validator.validate_message_text("Hello, this is a test message.")
        assert result.is_valid is True
    
    def test_validate_message_text_empty(self):
        """Test empty message text validation."""
        result = Validator.validate_message_text("")
        assert result.is_valid is False
    
    def test_validate_message_text_too_long(self):
        """Test too long message text validation."""
        long_message = "A" * 4001
        result = Validator.validate_message_text(long_message)
        assert result.is_valid is False
    
    def test_sql_injection_detection(self):
        """Test SQL injection pattern detection."""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "UNION SELECT * FROM passwords",
            "admin'--",
        ]
        for inp in malicious_inputs:
            result = Validator._contains_sql_injection(inp)
            assert result is True, f"Failed to detect SQL injection in: {inp}"


class TestBatchValidator:
    """Test cases for BatchValidator class."""
    
    def test_validate_users_batch_valid(self):
        """Test valid users batch validation."""
        users = [
            (123456789, "jobs"),
            (987654321, "remote"),
        ]
        result = BatchValidator.validate_users_batch(users)
        assert result.is_valid is True
        assert len(result.value) == 2
    
    def test_validate_users_batch_empty(self):
        """Test empty users batch validation."""
        result = BatchValidator.validate_users_batch([])
        assert result.is_valid is False
    
    def test_validate_users_batch_too_large(self):
        """Test too large users batch validation."""
        users = [(i, "jobs") for i in range(101)]
        result = BatchValidator.validate_users_batch(users)
        assert result.is_valid is False
    
    def test_validate_users_batch_invalid_format(self):
        """Test invalid format users batch validation."""
        users = ["invalid_format"]
        result = BatchValidator.validate_users_batch(users)
        assert result.is_valid is False
    
    def test_validate_jobs_batch_valid(self):
        """Test valid jobs batch validation."""
        jobs = [
            ("Software Engineer", "Acme Corp", "https://example.com/job/1"),
            ("Data Scientist", "Tech Inc", "https://example.com/job/2"),
        ]
        result = BatchValidator.validate_jobs_batch(jobs)
        assert result.is_valid is True
        assert len(result.value) == 2
    
    def test_validate_jobs_batch_empty(self):
        """Test empty jobs batch validation."""
        result = BatchValidator.validate_jobs_batch([])
        assert result.is_valid is False
    
    def test_validate_jobs_batch_skips_invalid(self):
        """Test that invalid jobs are skipped."""
        jobs = [
            ("Software Engineer", "Acme Corp", "https://example.com/job/1"),
            ("", "Bad Corp", "invalid_url"),  # Invalid
            ("Data Scientist", "Tech Inc", "https://example.com/job/2"),
        ]
        result = BatchValidator.validate_jobs_batch(jobs)
        assert result.is_valid is True
        assert len(result.value) == 2  # One invalid job skipped
