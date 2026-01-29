#!/usr/bin/env python3
"""
Comprehensive test suite for Job Alert Bot
Tests various components and functionality
"""

import os
import sys
import asyncio
import unittest
import tempfile
import sqlite3
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.logger import logger
from database.models import add_user, set_category, add_job, get_users, get_latest_jobs
from database.db import init_db, get_db_stats, close_db
from services.scraper_engine import scrape_remoteok, run_scrapers
from services.notifier import notify_users
from handlers.start import start, category_callback
from handlers.jobs import send_jobs
from handlers.admin import stats, broadcast
from main import app


class TestConfig(unittest.TestCase):
    """Test configuration loading and validation"""
    
    def setUp(self):
        """Set up test environment"""
        # Save original environment
        self.original_env = os.environ.copy()
        
    def tearDown(self):
        """Clean up test environment"""
        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_env)
    
    def test_missing_required_env_vars(self):
        """Test that missing required environment variables raise errors"""
        # Clear all environment variables
        os.environ.clear()
        
        # Should raise ValueError for missing required variables
        with self.assertRaises(ValueError):
            # This would be called when importing config
            import importlib
            import config
            importlib.reload(config)


class TestDatabase(unittest.TestCase):
    """Test database operations"""
    
    def setUp(self):
        """Set up test database"""
        # Use temporary database for testing
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Set database file path
        os.environ['DB_FILE'] = self.temp_db.name
        
        # Initialize database
        init_db()
    
    def tearDown(self):
        """Clean up test database"""
        close_db()
        os.unlink(self.temp_db.name)
    
    def test_user_operations(self):
        """Test user database operations"""
        # Test adding user
        result = add_user(12345, "Test User")
        self.assertTrue(result)
        
        # Test adding duplicate user
        result = add_user(12345, "Test User Updated")
        self.assertFalse(result)  # Should return False for duplicate
        
        # Test setting category
        result = set_category(12345, "remote")
        self.assertTrue(result)
        
        # Test invalid category
        result = set_category(12345, "invalid")
        self.assertFalse(result)
        
        # Test getting users
        users = get_users()
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0][0], 12345)
        self.assertEqual(users[0][1], "remote")
    
    def test_job_operations(self):
        """Test job database operations"""
        # Test adding job
        result = add_job("Test Job", "Test Company", "https://example.com", "jobs")
        self.assertTrue(result)
        
        # Test adding duplicate job
        result = add_job("Test Job", "Test Company", "https://example.com", "jobs")
        self.assertFalse(result)  # Should return False for duplicate
        
        # Test getting latest jobs
        jobs = get_latest_jobs("jobs", 5)
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0][0], "Test Job")
        self.assertEqual(jobs[0][1], "Test Company")
        self.assertEqual(jobs[0][2], "https://example.com")
    
    def test_db_stats(self):
        """Test database statistics"""
        # Add some test data
        add_user(11111, "User 1")
        add_user(22222, "User 2")
        add_job("Job 1", "Company 1", "https://example1.com", "jobs")
        add_job("Job 2", "Company 2", "https://example2.com", "remote")
        
        stats = get_db_stats()
        
        self.assertIn('total_users', stats)
        self.assertIn('total_jobs', stats)
        self.assertIn('jobs_by_type', stats)
        self.assertIn('recent_jobs', stats)
        
        self.assertEqual(stats['total_users'], 2)
        self.assertEqual(stats['total_jobs'], 2)


class TestScraper(unittest.TestCase):
    """Test scraping functionality"""
    
    @patch('services.scraper_engine.requests.get')
    def test_scrape_remoteok_success(self, mock_get):
        """Test successful RemoteOK scraping"""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = [
            {"position": "Test Job", "company": "Test Company", "url": "https://example.com"}
        ]
        mock_get.return_value = mock_response
        
        # This would normally add to database, but we're just testing the scraping logic
        # In a real test, you'd set up a test database
        result = scrape_remoteok()
        self.assertIsInstance(result, int)
    
    @patch('services.scraper_engine.requests.get')
    def test_scrape_remoteok_failure(self, mock_get):
        """Test RemoteOK scraping failure"""
        # Mock failed response
        mock_get.side_effect = Exception("Network error")
        
        result = scrape_remoteok()
        self.assertEqual(result, 0)


class TestHandlers(unittest.TestCase):
    """Test Telegram handlers"""
    
    def setUp(self):
        """Set up test handlers"""
        self.mock_update = Mock()
        self.mock_context = Mock()
        self.mock_user = Mock()
        self.mock_user.id = 12345
        self.mock_user.full_name = "Test User"
        self.mock_update.effective_user = self.mock_user
        self.mock_update.message = Mock()
        self.mock_update.message.reply_text = Mock()
        
        self.mock_query = Mock()
        self.mock_query.from_user.id = 12345
        self.mock_query.data = "jobs"
        self.mock_query.answer = Mock()
        self.mock_query.edit_message_text = Mock()
        
        self.mock_update.callback_query = self.mock_query
    
    @patch('handlers.start.add_user')
    @patch('handlers.start.set_category')
    def test_start_handler(self, mock_set_category, mock_add_user):
        """Test /start command handler"""
        mock_add_user.return_value = True
        mock_set_category.return_value = True
        
        # Test successful start
        asyncio.run(start(self.mock_update, self.mock_context))
        
        # Verify user was registered
        mock_add_user.assert_called_once_with(12345, "Test User")
        self.mock_update.message.reply_text.assert_called_once()
    
    @patch('handlers.start.set_category')
    def test_category_callback(self, mock_set_category):
        """Test category selection callback"""
        mock_set_category.return_value = True
        
        # Test successful category update
        asyncio.run(category_callback(self.mock_update, self.mock_context))
        
        # Verify category was set
        mock_set_category.assert_called_once_with(12345, "jobs")
        self.mock_query.answer.assert_called_once()
        self.mock_query.edit_message_text.assert_called_once()
    
    @patch('handlers.jobs.get_latest_jobs')
    def test_send_jobs(self, mock_get_jobs):
        """Test job sending functionality"""
        mock_get_jobs.return_value = [
            ("Test Job", "Test Company", "https://example.com")
        ]
        
        # Test sending jobs
        asyncio.run(send_jobs(self.mock_update, self.mock_context, "jobs"))
        
        # Verify message was sent
        self.mock_update.message.reply_text.assert_called_once()


class TestAdminHandlers(unittest.TestCase):
    """Test admin-only handlers"""
    
    def setUp(self):
        """Set up admin test handlers"""
        self.mock_update = Mock()
        self.mock_context = Mock()
        self.mock_user = Mock()
        self.mock_user.id = 12345  # This should NOT be the admin ID
        self.mock_update.effective_user = self.mock_user
        self.mock_update.message = Mock()
        self.mock_update.message.reply_text = Mock()
        
        # Set admin ID to different value
        os.environ['ADMIN_ID'] = '99999'
    
    def tearDown(self):
        """Clean up environment"""
        if 'ADMIN_ID' in os.environ:
            del os.environ['ADMIN_ID']
    
    @patch('handlers.admin.get_db_stats')
    def test_stats_non_admin(self, mock_get_stats):
        """Test stats command for non-admin user"""
        mock_get_stats.return_value = {'total_users': 10, 'total_jobs': 50}
        
        # Test that non-admin gets access denied
        asyncio.run(stats(self.mock_update, self.mock_context))
        
        # Verify access denied message
        self.mock_update.message.reply_text.assert_called_once_with("❌ Access denied. Admin only.")


class TestNotifier(unittest.TestCase):
    """Test notification system"""
    
    def setUp(self):
        """Set up notifier tests"""
        self.mock_bot = Mock()
        self.mock_bot.send_message = Mock()
    
    @patch('services.notifier.asyncio.sleep')
    def test_notify_users(self, mock_sleep):
        """Test user notification"""
        users = [(12345, "jobs"), (67890, "remote")]
        jobs = [("Test Job", "Test Company", "https://example.com")]
        
        # Mock successful message sending
        self.mock_bot.send_message.return_value = None
        
        # Test notification
        asyncio.run(notify_users(self.mock_bot, users, jobs))
        
        # Verify messages were sent
        self.assertEqual(self.mock_bot.send_message.call_count, 2)
        mock_sleep.assert_called()


class TestIntegration(unittest.TestCase):
    """Integration tests"""
    
    def setUp(self):
        """Set up integration tests"""
        # Set up test environment
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        os.environ['DB_FILE'] = self.temp_db.name
        os.environ['TELEGRAM_TOKEN'] = 'test_token'
        os.environ['ADMIN_ID'] = '12345'
        os.environ['WEBHOOK_BASE_URL'] = 'https://test.example.com'
        os.environ['WEBHOOK_TOKEN'] = 'test_token'
        
        init_db()
    
    def tearDown(self):
        """Clean up integration tests"""
        close_db()
        os.unlink(self.temp_db.name)
        # Clean up environment
        for key in ['DB_FILE', 'TELEGRAM_TOKEN', 'ADMIN_ID', 'WEBHOOK_BASE_URL', 'WEBHOOK_TOKEN']:
            if key in os.environ:
                del os.environ[key]
    
    def test_full_user_workflow(self):
        """Test complete user workflow"""
        # 1. Add user
        result = add_user(12345, "Test User")
        self.assertTrue(result)
        
        # 2. Set category
        result = set_category(12345, "remote")
        self.assertTrue(result)
        
        # 3. Add jobs
        result = add_job("Remote Job", "Remote Company", "https://remote.example.com", "remote")
        self.assertTrue(result)
        
        # 4. Get jobs
        jobs = get_latest_jobs("remote", 5)
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0][0], "Remote Job")
        
        # 5. Get stats
        stats = get_db_stats()
        self.assertEqual(stats['total_users'], 1)
        self.assertEqual(stats['total_jobs'], 1)


class TestHealthChecks(unittest.TestCase):
    """Test health check endpoints"""
    
    def test_health_endpoint_exists(self):
        """Test that health check endpoint exists"""
        # Verify the app has been configured
        self.assertIsNotNone(app, "FastAPI app should be configured")


if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)