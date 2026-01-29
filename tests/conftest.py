"""Pytest configuration and fixtures."""

import sys
import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from typing import Generator

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def async_client():
    """Create async HTTP client for testing."""
    from httpx import AsyncClient
    async with AsyncClient() as client:
        yield client


@pytest.fixture
def temp_db_path() -> Generator[str, None, None]:
    """Create temporary database file."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    os.unlink(path)


@pytest.fixture
def mock_telegram_bot():
    """Mock Telegram bot for testing."""
    from unittest.mock import AsyncMock, MagicMock
    
    bot = MagicMock()
    bot.send_message = AsyncMock(return_value=True)
    bot.set_webhook = AsyncMock(return_value=True)
    bot.delete_webhook = AsyncMock(return_value=True)
    bot.get_me = AsyncMock(return_value={"id": 123456, "username": "test_bot"})
    
    return bot


@pytest.fixture
def mock_telegram_update():
    """Mock Telegram update for testing."""
    from unittest.mock import MagicMock
    
    update = MagicMock()
    update.effective_user.id = 123456789
    update.effective_user.full_name = "Test User"
    update.effective_user.username = "testuser"
    update.message.text = "/start"
    update.message.chat_id = 123456789
    
    return update


@pytest.fixture
def mock_telegram_context():
    """Mock Telegram context for testing."""
    from unittest.mock import MagicMock, AsyncMock
    
    context = MagicMock()
    context.bot = MagicMock()
    context.bot.send_message = AsyncMock()
    context.args = []
    context.user_data = {}
    
    return context


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances before each test."""
    yield


@pytest.fixture
def test_config():
    """Create test configuration."""
    from job_alert_bot.config.settings import Config, Environment
    
    return Config(
        environment=Environment.TESTING,
        debug=True,
    )
