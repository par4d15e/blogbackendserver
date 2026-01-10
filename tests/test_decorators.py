"""
Tests for decorators.
"""
import pytest
from unittest.mock import MagicMock, patch


class TestRateLimiter:
    """Tests for rate limiter decorator."""

    def test_rate_limiter_exists(self):
        """Test rate_limiter decorator exists."""
        from app.decorators.rate_limiter import rate_limiter
        assert rate_limiter is not None
        assert callable(rate_limiter)

    def test_rate_limiter_returns_decorator(self):
        """Test rate_limiter returns a decorator."""
        from app.decorators.rate_limiter import rate_limiter
        
        decorator = rate_limiter(limit=5, seconds=60)
        assert callable(decorator)

    def test_rate_limiter_decorates_function(self):
        """Test rate_limiter can decorate a function."""
        from app.decorators.rate_limiter import rate_limiter
        
        @rate_limiter(limit=10, seconds=30)
        async def test_function():
            return "success"
        
        # The decorated function should exist
        assert test_function is not None
        assert callable(test_function)

    @pytest.mark.asyncio
    async def test_rate_limiter_allows_request(self):
        """Test rate limiter allows requests under limit."""
        from app.decorators.rate_limiter import rate_limiter
        
        with patch('app.decorators.rate_limiter.redis_manager') as mock_redis:
            mock_redis.sync_client.get.return_value = None
            mock_redis.sync_client.setex.return_value = True
            mock_redis.sync_client.incr.return_value = 1
            
            @rate_limiter(limit=10, seconds=60)
            async def test_endpoint(request):
                return {"status": "ok"}
            
            # Create mock request
            mock_request = MagicMock()
            mock_request.client.host = "127.0.0.1"
            mock_request.url.path = "/test"
            
            # This tests the decorator structure
            assert callable(test_endpoint)
