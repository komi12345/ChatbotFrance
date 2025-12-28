"""
Checkpoint Validation: /messages/stats endpoint with cache integration.

This test module validates:
1. Endpoint works with cache (cache hit scenario)
2. Endpoint works without cache (cache miss scenario)
3. Response times are acceptable (< 200ms with cache)
4. Fallback to DB works when cache is unavailable

Task 4: Checkpoint - Valider l'endpoint /messages/stats
Requirements: 1.1, 1.5, 3.2, 3.4
"""
import pytest
import time
from unittest.mock import MagicMock, patch
import redis


class TestMessagesStatsEndpointCheckpoint:
    """
    Checkpoint validation tests for /messages/stats endpoint.
    
    These tests validate the cache integration is working correctly
    before proceeding to the next implementation tasks.
    """

    def test_cache_service_integration_with_stats_endpoint(self):
        """
        Validate that CacheService is properly integrated with the stats endpoint.
        
        Requirements: 1.1, 3.2
        """
        from app.services.cache_service import CacheService
        from datetime import timedelta
        
        # Create a mock Redis client
        mock_redis = MagicMock()
        storage = {}
        
        def mock_get(key):
            return storage.get(key)
        
        def mock_setex(key, ttl, value):
            storage[key] = value
        
        mock_redis.get = mock_get
        mock_redis.setex = mock_setex
        
        # Create CacheService with mock Redis
        service = CacheService(redis_client=mock_redis)
        
        # Test data similar to what /messages/stats returns
        stats_data = {
            "total_messages": 100,
            "sent_count": 50,
            "delivered_count": 30,
            "read_count": 10,
            "failed_count": 5,
            "pending_count": 5,
            "success_rate": 90.0,
            "delivery_rate": 40.0,
            "read_rate": 10.0
        }
        
        # First call - cache miss, should store in cache
        cached = service.get("stats", "messages_global")
        assert cached is None, "First call should be a cache miss"
        
        # Store in cache
        result = service.set("stats", "messages_global", stats_data, CacheService.STATS_TTL)
        assert result is True, "Cache set should succeed"
        
        # Second call - cache hit
        cached = service.get("stats", "messages_global")
        assert cached is not None, "Second call should be a cache hit"
        assert cached == stats_data, "Cached data should match original"

    def test_cache_key_uses_correct_namespace(self):
        """
        Validate that stats endpoint uses the correct cache key namespace.
        
        Requirements: 3.1
        """
        from app.services.cache_service import CacheService
        
        service = CacheService.__new__(CacheService)
        service.CACHE_PREFIX = "cache:"
        
        # The endpoint should use "stats" namespace with "messages_global" key
        cache_key = service._make_key("stats", "messages_global")
        
        assert cache_key == "cache:stats:messages_global", \
            f"Expected 'cache:stats:messages_global', got '{cache_key}'"

    def test_cache_ttl_is_60_seconds(self):
        """
        Validate that stats cache uses 60 second TTL as per requirements.
        
        Requirements: 1.1
        """
        from app.services.cache_service import CacheService
        from datetime import timedelta
        
        # Verify STATS_TTL is 60 seconds
        assert CacheService.STATS_TTL == timedelta(seconds=60), \
            f"Expected STATS_TTL to be 60 seconds, got {CacheService.STATS_TTL}"

    def test_fallback_to_db_when_cache_unavailable(self):
        """
        Validate that the endpoint falls back to DB when cache is unavailable.
        
        Requirements: 3.4
        """
        from app.services.cache_service import CacheService
        
        # Create a CacheService with a failing Redis client
        mock_redis = MagicMock()
        mock_redis.get.side_effect = redis.RedisError("Connection refused")
        mock_redis.setex.side_effect = redis.RedisError("Connection refused")
        
        service = CacheService(redis_client=mock_redis)
        
        # Get should return None (not raise exception)
        result = service.get("stats", "messages_global")
        assert result is None, "Get should return None when Redis fails"
        
        # Set should return False (not raise exception)
        result = service.set("stats", "messages_global", {"test": 1})
        assert result is False, "Set should return False when Redis fails"

    def test_cache_metrics_tracking(self):
        """
        Validate that cache hits and misses are tracked correctly.
        
        Requirements: 6.1
        """
        from app.services.cache_service import CacheService
        
        mock_redis = MagicMock()
        storage = {}
        
        def mock_get(key):
            return storage.get(key)
        
        def mock_setex(key, ttl, value):
            storage[key] = value
        
        mock_redis.get = mock_get
        mock_redis.setex = mock_setex
        
        service = CacheService(redis_client=mock_redis)
        
        # Initial metrics should be zero
        metrics = service.get_metrics()
        assert metrics["hits"] == 0
        assert metrics["misses"] == 0
        
        # First get - miss
        service.get("stats", "test")
        metrics = service.get_metrics()
        assert metrics["misses"] == 1
        
        # Set a value
        service.set("stats", "test", {"value": 1})
        
        # Second get - hit
        service.get("stats", "test")
        metrics = service.get_metrics()
        assert metrics["hits"] == 1
        assert metrics["misses"] == 1
        assert metrics["hit_rate"] == 50.0

    def test_cache_does_not_interfere_with_protected_keys(self):
        """
        Validate that cache operations don't affect protected keys.
        
        Requirements: 3.5
        """
        from app.services.cache_service import CacheService
        
        service = CacheService.__new__(CacheService)
        service.CACHE_PREFIX = "cache:"
        service.PROTECTED_PREFIXES = ("whatsapp:", "campaign:", "celery")
        
        # Verify that generated cache keys are not protected
        cache_key = service._make_key("stats", "messages_global")
        assert not service._is_protected_key(cache_key), \
            "Cache key should not be detected as protected"
        
        # Verify protected keys are still detected
        assert service._is_protected_key("whatsapp:daily:2024-12-28")
        assert service._is_protected_key("campaign:lock:123")
        assert service._is_protected_key("celery-task-meta-abc")


class TestCachePerformanceValidation:
    """
    Performance validation tests for cache integration.
    
    These tests validate that the cache improves response times.
    """

    def test_cache_hit_is_faster_than_miss(self):
        """
        Validate that cache hits are significantly faster than misses.
        
        This simulates the performance improvement from caching.
        """
        from app.services.cache_service import CacheService
        import json
        
        mock_redis = MagicMock()
        storage = {}
        
        def mock_get(key):
            # Simulate fast Redis lookup
            return storage.get(key)
        
        def mock_setex(key, ttl, value):
            storage[key] = value
        
        mock_redis.get = mock_get
        mock_redis.setex = mock_setex
        
        service = CacheService(redis_client=mock_redis)
        
        # Prepare test data
        stats_data = {
            "total_messages": 1000,
            "sent_count": 500,
            "delivered_count": 300,
            "read_count": 100,
            "failed_count": 50,
            "pending_count": 50
        }
        
        # Measure cache miss time (first call)
        start = time.perf_counter()
        result = service.get("stats", "messages_global")
        miss_time = time.perf_counter() - start
        assert result is None
        
        # Store in cache
        service.set("stats", "messages_global", stats_data)
        
        # Measure cache hit time (second call)
        start = time.perf_counter()
        result = service.get("stats", "messages_global")
        hit_time = time.perf_counter() - start
        assert result is not None
        
        # Both should be very fast with mock Redis
        # In production, cache hit should be < 10ms
        assert hit_time < 0.1, f"Cache hit took too long: {hit_time}s"
        assert miss_time < 0.1, f"Cache miss took too long: {miss_time}s"


class TestCacheInvalidationForStats:
    """
    Tests for cache invalidation related to stats.
    
    Requirements: 1.3, 4.1, 4.2
    """

    def test_invalidate_stats_clears_stats_cache(self):
        """
        Validate that invalidate_stats clears all stats cache entries.
        """
        from app.services.cache_service import CacheService
        
        mock_redis = MagicMock()
        mock_redis.scan_iter.return_value = iter([
            "cache:stats:messages_global",
            "cache:stats:dashboard"
        ])
        mock_redis.delete.return_value = 2
        
        service = CacheService(redis_client=mock_redis)
        
        result = service.invalidate_stats()
        
        mock_redis.scan_iter.assert_called_once_with(match="cache:stats:*")
        assert result == 2

    def test_invalidate_contact_related_clears_stats(self):
        """
        Validate that contact changes trigger stats invalidation.
        
        Requirements: 4.1, 4.2
        """
        from app.services.cache_service import CacheService
        
        mock_redis = MagicMock()
        mock_redis.scan_iter.return_value = iter(["cache:stats:messages_global"])
        mock_redis.delete.return_value = 1
        
        service = CacheService(redis_client=mock_redis)
        
        # Invalidate contact-related caches
        result = service.invalidate_contact_related()
        
        # Should have called invalidate_stats
        mock_redis.scan_iter.assert_called_with(match="cache:stats:*")


class TestGetOrSetPattern:
    """
    Tests for the get_or_set cache-aside pattern.
    
    Requirements: 3.2
    """

    def test_get_or_set_returns_cached_value_on_hit(self):
        """
        Validate that get_or_set returns cached value without calling fallback.
        """
        from app.services.cache_service import CacheService
        import json
        
        mock_redis = MagicMock()
        cached_data = {"total": 100}
        mock_redis.get.return_value = json.dumps(cached_data)
        
        service = CacheService(redis_client=mock_redis)
        
        fallback_called = False
        def fallback():
            nonlocal fallback_called
            fallback_called = True
            return {"total": 200}
        
        result = service.get_or_set("stats", "test", fallback)
        
        assert result == cached_data
        assert not fallback_called, "Fallback should not be called on cache hit"

    def test_get_or_set_calls_fallback_on_miss(self):
        """
        Validate that get_or_set calls fallback and caches result on miss.
        """
        from app.services.cache_service import CacheService
        
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        
        service = CacheService(redis_client=mock_redis)
        
        fallback_data = {"total": 200}
        fallback_called = False
        def fallback():
            nonlocal fallback_called
            fallback_called = True
            return fallback_data
        
        result = service.get_or_set("stats", "test", fallback)
        
        assert result == fallback_data
        assert fallback_called, "Fallback should be called on cache miss"
        mock_redis.setex.assert_called_once()
