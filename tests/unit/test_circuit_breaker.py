"""Unit tests for circuit breaker pattern."""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from job_alert_bot.utils.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    CircuitState,
    get_circuit_breaker,
    circuit_breaker
)


class TestCircuitBreaker:
    """Test cases for CircuitBreaker class."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=0.1,  # Short for testing
            half_open_max_calls=2,
            success_threshold=1
        )
    
    @pytest.fixture
    def breaker(self, config):
        """Create circuit breaker instance."""
        return CircuitBreaker("test_breaker", config)
    
    @pytest.mark.asyncio
    async def test_successful_call(self, breaker):
        """Test successful function call."""
        async def success_func():
            return "success"
        
        result = await breaker.call(success_func)
        assert result == "success"
        assert breaker.state == CircuitState.CLOSED
    
    @pytest.mark.asyncio
    async def test_failed_call(self, breaker):
        """Test failed function call."""
        async def fail_func():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            await breaker.call(fail_func)
        
        assert breaker.failure_count == 1
        assert breaker.state == CircuitState.CLOSED
    
    @pytest.mark.asyncio
    async def test_circuit_opens_after_failures(self, breaker):
        """Test circuit opens after threshold failures."""
        async def fail_func():
            raise ValueError("Test error")
        
        # Trigger failures
        for _ in range(3):
            with pytest.raises(ValueError):
                await breaker.call(fail_func)
        
        assert breaker.state == CircuitState.OPEN
        
        # Next call should fail immediately
        with pytest.raises(CircuitBreakerOpenError):
            await breaker.call(fail_func)
    
    @pytest.mark.asyncio
    async def test_circuit_half_open_recovery(self, breaker):
        """Test circuit transitions to half-open and recovers."""
        async def fail_func():
            raise ValueError("Test error")
        
        async def success_func():
            return "success"
        
        # Open the circuit
        for _ in range(3):
            with pytest.raises(ValueError):
                await breaker.call(fail_func)
        
        assert breaker.state == CircuitState.OPEN
        
        # Wait for recovery timeout
        await asyncio.sleep(0.15)
        
        # Circuit should be half-open
        result = await breaker.call(success_func)
        assert result == "success"
        assert breaker.state == CircuitState.CLOSED
    
    @pytest.mark.asyncio
    async def test_half_open_failure_reopens(self, breaker):
        """Test that failure in half-open reopens circuit."""
        async def fail_func():
            raise ValueError("Test error")
        
        # Open the circuit
        for _ in range(3):
            with pytest.raises(ValueError):
                await breaker.call(fail_func)
        
        # Wait for recovery
        await asyncio.sleep(0.15)
        
        # Fail in half-open
        with pytest.raises(ValueError):
            await breaker.call(fail_func)
        
        assert breaker.state == CircuitState.OPEN
    
    def test_get_state(self, breaker):
        """Test getting circuit breaker state."""
        state = breaker.get_state()
        assert state["name"] == "test_breaker"
        assert state["state"] == "closed"
        assert state["failure_count"] == 0
        assert state["success_count"] == 0


class TestCircuitBreakerRegistry:
    """Test cases for circuit breaker registry."""
    
    def test_get_circuit_breaker_creates_new(self):
        """Test getting new circuit breaker."""
        breaker = get_circuit_breaker("new_breaker")
        assert breaker.name == "new_breaker"
        assert breaker.state == CircuitState.CLOSED
    
    def test_get_circuit_breaker_returns_existing(self):
        """Test getting existing circuit breaker."""
        breaker1 = get_circuit_breaker("existing_breaker")
        breaker2 = get_circuit_breaker("existing_breaker")
        assert breaker1 is breaker2
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_decorator(self):
        """Test circuit breaker decorator."""
        call_count = 0
        
        @circuit_breaker("decorated_func_test")
        async def test_func():
            nonlocal call_count
            call_count += 1
            raise ValueError("Test error")
        
        # Should fail 3 times and open circuit
        for _ in range(3):
            with pytest.raises(ValueError):
                await test_func()
        
        # Circuit should be open now - 4th call should raise CircuitBreakerOpenError
        with pytest.raises(CircuitBreakerOpenError):
            await test_func()


class TestCircuitBreakerConcurrency:
    """Test circuit breaker thread safety."""
    
    @pytest.mark.asyncio
    async def test_concurrent_calls(self):
        """Test concurrent calls to circuit breaker."""
        config = CircuitBreakerConfig(failure_threshold=5)
        breaker = CircuitBreaker("concurrent_breaker", config)
        
        async def success_func():
            await asyncio.sleep(0.01)
            return "success"
        
        # Make concurrent calls
        tasks = [breaker.call(success_func) for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        assert all(r == "success" for r in results)
        assert breaker.state == CircuitState.CLOSED
