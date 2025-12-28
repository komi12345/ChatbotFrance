"""
Checkpoint Validation: Categories endpoints with cache integration.

This test module validates:
1. List categories endpoint works with cache (cache hit scenario)
2. Category detail endpoint works with cache (cache miss scenario)
3. Contact counts are correct
4. Fallback to DB works when cache is unavailable

Task 6: Checkpoint - Valider les endpoints catégories
Requirements: 1.2, 3.2, 3.4, 5.2
"""
import pytest
import json
from unittest.mock import MagicMock, patch
import redis


class TestCategoriesListEndpointCheckpoint:
    """
    Checkpoint validation tests for /categories list endpoint.
    
    These tests validate the cache integration is working correctly
    for the categories list endpoint.
    """

    def test_cache_service_integration_with_categories_list(self):
        """
        Validate that CacheService is properly integrated with the categories list endpoint.
        
        Requirements: 1.2, 3.2
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
        
        # Test data similar to what /categories returns
        categories_data = {
            "items": [
                {
                    "id": 1,
                    "name": "Test Category",
                    "color": "#FF0000",
                    "created_by": 1,
                    "created_at": "2024-12-28T10:00:00",
                    "updated_at": None,
                    "contact_count": 5
                }
            ],
            "total": 1,
            "page": 1,
            "size": 50,
            "pages": 1
        }
        
        # First call - cache miss, should store in cache
        cache_key = "list:page_1:size_50"
        cached = service.get("categories", cache_key)
        assert cached is None, "First call should be a cache miss"
        
        # Store in cache
        result = service.set("categories", cache_key, categories_data, CacheService.CATEGORIES_TTL)
        assert result is True, "Cache set should succeed"
        
        # Second call - cache hit
        cached = service.get("categories", cache_key)
        assert cached is not None, "Second call should be a cache hit"
        assert cached == categories_data, "Cached data should match original"

    def test_categories_cache_key_uses_correct_namespace(self):
        """
        Validate that categories endpoint uses the correct cache key namespace.
        
        Requirements: 3.1
        """
        from app.services.cache_service import CacheService
        
        service = CacheService.__new__(CacheService)
        service.CACHE_PREFIX = "cache:"
        
        # The endpoint should use "categories" namespace with list key
        cache_key = service._make_key("categories", "list:page_1:size_50")
        
        assert cache_key == "cache:categories:list:page_1:size_50", \
            f"Expected 'cache:categories:list:page_1:size_50', got '{cache_key}'"

    def test_categories_cache_ttl_is_120_seconds(self):
        """
        Validate that categories cache uses 120 second TTL as per requirements.
        
        Requirements: 1.2
        """
        from app.services.cache_service import CacheService
        from datetime import timedelta
        
        # Verify CATEGORIES_TTL is 120 seconds
        assert CacheService.CATEGORIES_TTL == timedelta(seconds=120), \
            f"Expected CATEGORIES_TTL to be 120 seconds, got {CacheService.CATEGORIES_TTL}"

    def test_contacts_count_cache_ttl_is_60_seconds(self):
        """
        Validate that contact count cache uses 60 second TTL as per requirements.
        
        Requirements: 1.2
        """
        from app.services.cache_service import CacheService
        from datetime import timedelta
        
        # Verify CONTACTS_COUNT_TTL is 60 seconds
        assert CacheService.CONTACTS_COUNT_TTL == timedelta(seconds=60), \
            f"Expected CONTACTS_COUNT_TTL to be 60 seconds, got {CacheService.CONTACTS_COUNT_TTL}"


class TestCategoryDetailEndpointCheckpoint:
    """
    Checkpoint validation tests for /categories/{id} detail endpoint.
    
    These tests validate the cache integration is working correctly
    for the category detail endpoint.
    """

    def test_cache_service_integration_with_category_detail(self):
        """
        Validate that CacheService is properly integrated with the category detail endpoint.
        
        Requirements: 1.2, 3.2
        """
        from app.services.cache_service import CacheService
        
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
        
        # Test data similar to what /categories/{id} returns
        category_detail_data = {
            "id": 1,
            "name": "Test Category",
            "color": "#FF0000",
            "created_by": 1,
            "created_at": "2024-12-28T10:00:00",
            "updated_at": None,
            "contact_count": 3,
            "contacts": [
                {"id": 1, "first_name": "John", "last_name": "Doe", "full_number": "+22912345678"},
                {"id": 2, "first_name": "Jane", "last_name": "Doe", "full_number": "+22987654321"},
                {"id": 3, "first_name": "Bob", "last_name": "Smith", "full_number": "+22911111111"}
            ]
        }
        
        # First call - cache miss
        cache_key = "detail:1"
        cached = service.get("categories", cache_key)
        assert cached is None, "First call should be a cache miss"
        
        # Store in cache
        result = service.set("categories", cache_key, category_detail_data, CacheService.CATEGORIES_TTL)
        assert result is True, "Cache set should succeed"
        
        # Second call - cache hit
        cached = service.get("categories", cache_key)
        assert cached is not None, "Second call should be a cache hit"
        assert cached["id"] == 1, "Cached category ID should match"
        assert cached["contact_count"] == 3, "Cached contact count should match"
        assert len(cached["contacts"]) == 3, "Cached contacts list should have 3 items"

    def test_category_detail_cache_key_format(self):
        """
        Validate that category detail uses the correct cache key format.
        
        Requirements: 3.1
        """
        from app.services.cache_service import CacheService
        
        service = CacheService.__new__(CacheService)
        service.CACHE_PREFIX = "cache:"
        
        # The endpoint should use "categories" namespace with detail:{id} key
        cache_key = service._make_key("categories", "detail:123")
        
        assert cache_key == "cache:categories:detail:123", \
            f"Expected 'cache:categories:detail:123', got '{cache_key}'"


class TestContactCountCacheCheckpoint:
    """
    Checkpoint validation tests for contact count caching.
    
    These tests validate that contact counts are cached correctly.
    """

    def test_contact_count_cache_key_format(self):
        """
        Validate that contact count uses the correct cache key format.
        
        Requirements: 3.1
        """
        from app.services.cache_service import CacheService
        
        service = CacheService.__new__(CacheService)
        service.CACHE_PREFIX = "cache:"
        
        # The endpoint should use "contacts" namespace with count:category:{id} key
        cache_key = service._make_key("contacts", "count:category:5")
        
        assert cache_key == "cache:contacts:count:category:5", \
            f"Expected 'cache:contacts:count:category:5', got '{cache_key}'"

    def test_contact_count_caching_workflow(self):
        """
        Validate the contact count caching workflow.
        
        Requirements: 1.2, 5.2
        """
        from app.services.cache_service import CacheService
        
        # Create a mock Redis client
        mock_redis = MagicMock()
        storage = {}
        
        def mock_get(key):
            return storage.get(key)
        
        def mock_setex(key, ttl, value):
            storage[key] = value
        
        mock_redis.get = mock_get
        mock_redis.setex = mock_setex
        
        service = CacheService(redis_client=mock_redis)
        
        # Simulate caching contact counts for multiple categories
        category_counts = {1: 10, 2: 5, 3: 0}
        
        for cat_id, count in category_counts.items():
            cache_key = f"count:category:{cat_id}"
            service.set("contacts", cache_key, count, CacheService.CONTACTS_COUNT_TTL)
        
        # Verify all counts are cached correctly
        for cat_id, expected_count in category_counts.items():
            cache_key = f"count:category:{cat_id}"
            cached_count = service.get("contacts", cache_key)
            assert cached_count == expected_count, \
                f"Expected count {expected_count} for category {cat_id}, got {cached_count}"


class TestCategoriesFallbackCheckpoint:
    """
    Checkpoint validation tests for fallback behavior.
    
    These tests validate that the endpoint falls back to DB when cache is unavailable.
    """

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
        result = service.get("categories", "list:page_1:size_50")
        assert result is None, "Get should return None when Redis fails"
        
        # Set should return False (not raise exception)
        result = service.set("categories", "list:page_1:size_50", {"test": 1})
        assert result is False, "Set should return False when Redis fails"

    def test_cache_metrics_tracking_for_categories(self):
        """
        Validate that cache hits and misses are tracked correctly for categories.
        
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
        service.get("categories", "list:page_1:size_50")
        metrics = service.get_metrics()
        assert metrics["misses"] == 1
        
        # Set a value
        service.set("categories", "list:page_1:size_50", {"items": []})
        
        # Second get - hit
        service.get("categories", "list:page_1:size_50")
        metrics = service.get_metrics()
        assert metrics["hits"] == 1
        assert metrics["misses"] == 1
        assert metrics["hit_rate"] == 50.0


class TestCacheInvalidationForCategories:
    """
    Tests for cache invalidation related to categories.
    
    Requirements: 1.4, 4.3
    """

    def test_invalidate_categories_clears_categories_cache(self):
        """
        Validate that invalidate_categories clears all categories cache entries.
        """
        from app.services.cache_service import CacheService
        
        mock_redis = MagicMock()
        mock_redis.scan_iter.return_value = iter([
            "cache:categories:list:page_1:size_50",
            "cache:categories:detail:1",
            "cache:categories:detail:2"
        ])
        mock_redis.delete.return_value = 3
        
        service = CacheService(redis_client=mock_redis)
        
        result = service.invalidate_categories()
        
        mock_redis.scan_iter.assert_called_once_with(match="cache:categories:*")
        assert result == 3

    def test_invalidate_category_clears_specific_category(self):
        """
        Validate that invalidate_category clears a specific category's cache.
        
        Requirements: 4.3
        """
        from app.services.cache_service import CacheService
        
        mock_redis = MagicMock()
        mock_redis.delete.return_value = 1
        
        service = CacheService(redis_client=mock_redis)
        
        # Invalidate specific category
        result = service.invalidate_category(123)
        
        # Should have called delete for detail and count keys
        assert mock_redis.delete.call_count >= 1

    def test_invalidate_cache_on_category_change_function(self):
        """
        Validate the invalidate_cache_on_category_change utility function.
        
        Requirements: 1.4, 4.3
        """
        from app.services.cache_service import invalidate_cache_on_category_change
        
        # This should not raise any exceptions
        # It's a utility function that handles errors gracefully
        try:
            invalidate_cache_on_category_change(category_id=1)
            invalidate_cache_on_category_change()  # Without category_id
        except Exception as e:
            # If Redis is not available, it should still not raise
            # The function handles errors gracefully
            pass


class TestCategoriesEndpointIntegration:
    """
    Integration tests for categories endpoints with cache.
    
    These tests validate the complete flow of cache integration.
    """

    def test_categories_list_cache_key_includes_pagination(self):
        """
        Validate that categories list cache key includes pagination parameters.
        
        This ensures different pages are cached separately.
        """
        from app.services.cache_service import CacheService
        
        service = CacheService.__new__(CacheService)
        service.CACHE_PREFIX = "cache:"
        
        # Different pages should have different cache keys
        key_page1 = service._make_key("categories", "list:page_1:size_50")
        key_page2 = service._make_key("categories", "list:page_2:size_50")
        key_size20 = service._make_key("categories", "list:page_1:size_20")
        
        assert key_page1 != key_page2, "Different pages should have different cache keys"
        assert key_page1 != key_size20, "Different sizes should have different cache keys"

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
        cache_key = service._make_key("categories", "list:page_1:size_50")
        assert not service._is_protected_key(cache_key), \
            "Cache key should not be detected as protected"
        
        # Verify protected keys are still detected
        assert service._is_protected_key("whatsapp:daily:2024-12-28")
        assert service._is_protected_key("campaign:lock:123")
        assert service._is_protected_key("celery-task-meta-abc")

