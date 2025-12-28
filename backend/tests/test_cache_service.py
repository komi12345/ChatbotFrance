"""
Unit tests for CacheService.

Tests the core functionality of the cache service including:
- Key generation with correct prefix
- Protection of existing keys (whatsapp:*, campaign:*, celery*)
- Error handling when Redis is unavailable

Requirements: 3.1, 3.5
"""
import pytest
from unittest.mock import MagicMock, patch
import redis


class TestCacheKeyGeneration:
    """
    Tests for cache key generation with correct prefix.
    
    Requirements: 3.1
    """

    def test_make_key_adds_cache_prefix(self):
        """Key generation should add 'cache:' prefix."""
        from app.services.cache_service import CacheService
        
        service = CacheService.__new__(CacheService)
        service.CACHE_PREFIX = "cache:"
        
        result = service._make_key("stats", "messages_global")
        
        assert result == "cache:stats:messages_global"

    def test_make_key_with_different_namespaces(self):
        """Key generation should work with different namespaces."""
        from app.services.cache_service import CacheService
        
        service = CacheService.__new__(CacheService)
        service.CACHE_PREFIX = "cache:"
        
        assert service._make_key("stats", "dashboard") == "cache:stats:dashboard"
        assert service._make_key("categories", "list") == "cache:categories:list"
        assert service._make_key("contacts", "count:category:1") == "cache:contacts:count:category:1"

    def test_make_key_with_numeric_key(self):
        """Key generation should work with numeric keys."""
        from app.services.cache_service import CacheService
        
        service = CacheService.__new__(CacheService)
        service.CACHE_PREFIX = "cache:"
        
        result = service._make_key("categories", "detail:123")
        
        assert result == "cache:categories:detail:123"


class TestProtectedKeyDetection:
    """
    Tests for protection of existing keys.
    
    Requirements: 3.5
    """

    def test_is_protected_key_detects_whatsapp_prefix(self):
        """Should detect whatsapp:* keys as protected."""
        from app.services.cache_service import CacheService
        
        service = CacheService.__new__(CacheService)
        service.PROTECTED_PREFIXES = ("whatsapp:", "campaign:", "celery")
        
        assert service._is_protected_key("whatsapp:daily:2024-12-28") is True
        assert service._is_protected_key("whatsapp:message_1") is True

    def test_is_protected_key_detects_campaign_prefix(self):
        """Should detect campaign:* keys as protected."""
        from app.services.cache_service import CacheService
        
        service = CacheService.__new__(CacheService)
        service.PROTECTED_PREFIXES = ("whatsapp:", "campaign:", "celery")
        
        assert service._is_protected_key("campaign:lock:123") is True
        assert service._is_protected_key("campaign:status:456") is True

    def test_is_protected_key_detects_celery_prefix(self):
        """Should detect celery* keys as protected."""
        from app.services.cache_service import CacheService
        
        service = CacheService.__new__(CacheService)
        service.PROTECTED_PREFIXES = ("whatsapp:", "campaign:", "celery")
        
        assert service._is_protected_key("celery-task-meta-abc123") is True
        assert service._is_protected_key("celerybeat-schedule") is True

    def test_is_protected_key_allows_cache_prefix(self):
        """Should allow cache:* keys (not protected)."""
        from app.services.cache_service import CacheService
        
        service = CacheService.__new__(CacheService)
        service.PROTECTED_PREFIXES = ("whatsapp:", "campaign:", "celery")
        
        assert service._is_protected_key("cache:stats:messages") is False
        assert service._is_protected_key("cache:categories:list") is False


class TestCacheSetProtection:
    """
    Tests for set operation protection against protected keys.
    
    Requirements: 3.5
    """

    def test_set_rejects_protected_key_pattern(self):
        """Set should reject attempts to write to protected key patterns."""
        from app.services.cache_service import CacheService
        
        service = CacheService.__new__(CacheService)
        service.CACHE_PREFIX = "cache:"
        service.PROTECTED_PREFIXES = ("whatsapp:", "campaign:", "celery")
        service._redis = MagicMock()
        
        # Manually override _make_key to return a protected key
        # This simulates a bug where someone tries to bypass protection
        original_make_key = service._make_key
        service._make_key = lambda ns, k: "whatsapp:daily:2024-12-28"
        
        result = service.set("stats", "test", {"value": 1})
        
        assert result is False
        service._redis.setex.assert_not_called()
        
        # Restore original method
        service._make_key = original_make_key


class TestCacheErrorHandling:
    """
    Tests for error handling when Redis is unavailable.
    
    Requirements: 3.4
    """

    def test_get_returns_none_on_redis_error(self):
        """Get should return None when Redis raises an error."""
        from app.services.cache_service import CacheService
        
        service = CacheService.__new__(CacheService)
        service.CACHE_PREFIX = "cache:"
        service.PROTECTED_PREFIXES = ("whatsapp:", "campaign:", "celery")
        service._hits = 0
        service._misses = 0
        
        mock_redis = MagicMock()
        mock_redis.get.side_effect = redis.RedisError("Connection refused")
        service._redis = mock_redis
        
        result = service.get("stats", "messages_global")
        
        assert result is None
        assert service._misses == 1

    def test_set_returns_false_on_redis_error(self):
        """Set should return False when Redis raises an error."""
        from app.services.cache_service import CacheService
        from datetime import timedelta
        
        service = CacheService.__new__(CacheService)
        service.CACHE_PREFIX = "cache:"
        service.PROTECTED_PREFIXES = ("whatsapp:", "campaign:", "celery")
        service.DEFAULT_TTL = timedelta(seconds=60)
        
        mock_redis = MagicMock()
        mock_redis.setex.side_effect = redis.RedisError("Connection refused")
        service._redis = mock_redis
        
        result = service.set("stats", "messages_global", {"total": 100})
        
        assert result is False

    def test_delete_returns_false_on_redis_error(self):
        """Delete should return False when Redis raises an error."""
        from app.services.cache_service import CacheService
        
        service = CacheService.__new__(CacheService)
        service.CACHE_PREFIX = "cache:"
        service.PROTECTED_PREFIXES = ("whatsapp:", "campaign:", "celery")
        
        mock_redis = MagicMock()
        mock_redis.delete.side_effect = redis.RedisError("Connection refused")
        service._redis = mock_redis
        
        result = service.delete("stats", "messages_global")
        
        assert result is False

    def test_get_returns_none_on_json_decode_error(self):
        """Get should return None when JSON decoding fails."""
        from app.services.cache_service import CacheService
        
        service = CacheService.__new__(CacheService)
        service.CACHE_PREFIX = "cache:"
        service.PROTECTED_PREFIXES = ("whatsapp:", "campaign:", "celery")
        service._hits = 0
        service._misses = 0
        
        mock_redis = MagicMock()
        mock_redis.get.return_value = "invalid json {"
        service._redis = mock_redis
        
        result = service.get("stats", "messages_global")
        
        assert result is None
        assert service._misses == 1


class TestCacheRoundTrip:
    """
    Tests for cache round-trip consistency.
    
    Requirements: 3.2
    """

    def test_set_and_get_returns_same_value(self):
        """Setting and getting a value should return the same data."""
        from app.services.cache_service import CacheService
        from datetime import timedelta
        import json
        
        service = CacheService.__new__(CacheService)
        service.CACHE_PREFIX = "cache:"
        service.PROTECTED_PREFIXES = ("whatsapp:", "campaign:", "celery")
        service.DEFAULT_TTL = timedelta(seconds=60)
        service._hits = 0
        service._misses = 0
        
        # Store the value that was set
        stored_value = None
        
        def mock_setex(key, ttl, value):
            nonlocal stored_value
            stored_value = value
        
        def mock_get(key):
            return stored_value
        
        mock_redis = MagicMock()
        mock_redis.setex = mock_setex
        mock_redis.get = mock_get
        service._redis = mock_redis
        
        original_data = {"total_contacts": 150, "total_messages": 500}
        
        # Set the value
        set_result = service.set("stats", "dashboard", original_data)
        assert set_result is True
        
        # Get the value back
        retrieved_data = service.get("stats", "dashboard")
        
        assert retrieved_data == original_data


class TestCacheMetrics:
    """
    Tests for cache metrics tracking.
    
    Requirements: 6.1, 6.3
    """

    def test_get_metrics_returns_correct_structure(self):
        """Get metrics should return hits, misses, total, and hit_rate."""
        from app.services.cache_service import CacheService
        
        service = CacheService.__new__(CacheService)
        service._hits = 80
        service._misses = 20
        
        metrics = service.get_metrics()
        
        assert "hits" in metrics
        assert "misses" in metrics
        assert "total" in metrics
        assert "hit_rate" in metrics
        assert metrics["hits"] == 80
        assert metrics["misses"] == 20
        assert metrics["total"] == 100
        assert metrics["hit_rate"] == 80.0

    def test_get_metrics_handles_zero_total(self):
        """Get metrics should handle zero total without division error."""
        from app.services.cache_service import CacheService
        
        service = CacheService.__new__(CacheService)
        service._hits = 0
        service._misses = 0
        
        metrics = service.get_metrics()
        
        assert metrics["total"] == 0
        assert metrics["hit_rate"] == 0.0

    def test_reset_metrics_clears_counters(self):
        """Reset metrics should clear hits and misses."""
        from app.services.cache_service import CacheService
        
        service = CacheService.__new__(CacheService)
        service._hits = 100
        service._misses = 50
        
        service.reset_metrics()
        
        assert service._hits == 0
        assert service._misses == 0


class TestCacheInvalidation:
    """
    Tests for cache invalidation methods.
    
    Requirements: 1.3, 1.4, 4.1, 4.2, 4.3
    """

    def test_invalidate_stats_calls_invalidate_pattern(self):
        """Invalidate stats should call invalidate_pattern with stats:*."""
        from app.services.cache_service import CacheService
        
        service = CacheService.__new__(CacheService)
        service.CACHE_PREFIX = "cache:"
        service.PROTECTED_PREFIXES = ("whatsapp:", "campaign:", "celery")
        
        mock_redis = MagicMock()
        mock_redis.scan_iter.return_value = iter(["cache:stats:dashboard", "cache:stats:messages"])
        mock_redis.delete.return_value = 2
        service._redis = mock_redis
        
        result = service.invalidate_stats()
        
        mock_redis.scan_iter.assert_called_once_with(match="cache:stats:*")
        assert result == 2

    def test_invalidate_categories_calls_invalidate_pattern(self):
        """Invalidate categories should call invalidate_pattern with categories:*."""
        from app.services.cache_service import CacheService
        
        service = CacheService.__new__(CacheService)
        service.CACHE_PREFIX = "cache:"
        service.PROTECTED_PREFIXES = ("whatsapp:", "campaign:", "celery")
        
        mock_redis = MagicMock()
        mock_redis.scan_iter.return_value = iter(["cache:categories:list"])
        mock_redis.delete.return_value = 1
        service._redis = mock_redis
        
        result = service.invalidate_categories()
        
        mock_redis.scan_iter.assert_called_once_with(match="cache:categories:*")
        assert result == 1

    def test_invalidate_pattern_skips_protected_keys(self):
        """Invalidate pattern should skip any protected keys found."""
        from app.services.cache_service import CacheService
        
        service = CacheService.__new__(CacheService)
        service.CACHE_PREFIX = "cache:"
        service.PROTECTED_PREFIXES = ("whatsapp:", "campaign:", "celery")
        
        mock_redis = MagicMock()
        # Simulate a scenario where scan returns both cache and protected keys
        mock_redis.scan_iter.return_value = iter([
            "cache:stats:dashboard",
            "whatsapp:daily:2024-12-28"  # This should be skipped
        ])
        mock_redis.delete.return_value = 1
        service._redis = mock_redis
        
        result = service.invalidate_pattern("stats:*")
        
        # Only the cache key should be deleted
        mock_redis.delete.assert_called_once_with("cache:stats:dashboard")
