"""
Checkpoint Validation: Cache Invalidation After Mutations.

This test module validates Task 8:
1. Creating a contact invalidates stats cache and updates correctly
2. Modifying a category invalidates category cache and updates correctly
3. Deleting a contact invalidates stats and category counts

Task 8: Checkpoint - Valider l'invalidation du cache
Requirements: 1.3, 1.4, 4.1, 4.2, 4.3
"""
import pytest
import json
from unittest.mock import MagicMock, patch, call
from datetime import timedelta
from typing import List, Dict, Any


class TestContactCreationInvalidatesCache:
    """
    Checkpoint validation: Creating a contact invalidates stats cache.
    
    Requirements: 1.3, 4.1
    """

    def test_contact_creation_triggers_cache_invalidation(self):
        """
        Validate that creating a contact triggers cache invalidation.
        
        When a contact is created:
        - Stats cache should be invalidated
        - Associated category caches should be invalidated
        
        Requirements: 1.3, 4.1
        """
        from app.services.cache_service import CacheService
        
        # Create mock Redis
        mock_redis = MagicMock()
        storage = {}
        deleted_keys = []
        
        def mock_get(key):
            return storage.get(key)
        
        def mock_setex(key, ttl, value):
            storage[key] = value
        
        def mock_delete(*keys):
            for k in keys:
                deleted_keys.append(k)
                if k in storage:
                    del storage[k]
            return len(keys)
        
        def mock_scan_iter(match):
            prefix = match.replace("*", "")
            return iter([k for k in storage.keys() if k.startswith(prefix)])
        
        mock_redis.get = mock_get
        mock_redis.setex = mock_setex
        mock_redis.delete = mock_delete
        mock_redis.scan_iter = mock_scan_iter
        
        service = CacheService(redis_client=mock_redis)
        
        # Pre-populate cache with stats data
        service.set("stats", "messages_global", {"total_contacts": 100})
        service.set("stats", "dashboard", {"contacts": 100})
        
        # Verify cache is populated
        assert service.get("stats", "messages_global") is not None
        assert service.get("stats", "dashboard") is not None
        
        # Simulate contact creation - invalidate cache
        service.invalidate_contact_related(category_ids=[1, 2])
        
        # Verify stats cache is invalidated (cache miss)
        assert service.get("stats", "messages_global") is None, \
            "Stats cache should be invalidated after contact creation"
        assert service.get("stats", "dashboard") is None, \
            "Dashboard stats should be invalidated after contact creation"

    def test_contact_creation_invalidates_associated_category_counts(self):
        """
        Validate that creating a contact invalidates associated category counts.
        
        Requirements: 4.1
        """
        from app.services.cache_service import CacheService
        
        mock_redis = MagicMock()
        storage = {}
        
        def mock_get(key):
            return storage.get(key)
        
        def mock_setex(key, ttl, value):
            storage[key] = value
        
        def mock_delete(*keys):
            for k in keys:
                if k in storage:
                    del storage[k]
            return len(keys)
        
        def mock_scan_iter(match):
            prefix = match.replace("*", "")
            return iter([k for k in storage.keys() if k.startswith(prefix)])
        
        mock_redis.get = mock_get
        mock_redis.setex = mock_setex
        mock_redis.delete = mock_delete
        mock_redis.scan_iter = mock_scan_iter
        
        service = CacheService(redis_client=mock_redis)
        
        # Pre-populate cache with category contact counts
        category_ids = [1, 2, 3]
        for cat_id in category_ids:
            service.set("contacts", f"count:category:{cat_id}", 10)
            service.set("categories", f"detail:{cat_id}", {"id": cat_id, "name": f"Cat {cat_id}"})
        
        # Verify cache is populated
        for cat_id in category_ids:
            assert service.get("contacts", f"count:category:{cat_id}") == 10
        
        # Simulate contact creation with categories 1 and 2
        service.invalidate_contact_related(category_ids=[1, 2])
        
        # Verify associated category caches are invalidated
        assert service.get("contacts", f"count:category:1") is None, \
            "Category 1 count should be invalidated"
        assert service.get("contacts", f"count:category:2") is None, \
            "Category 2 count should be invalidated"
        
        # Category 3 should NOT be invalidated (not associated)
        assert service.get("contacts", f"count:category:3") == 10, \
            "Category 3 count should NOT be invalidated (not associated)"


class TestCategoryModificationInvalidatesCache:
    """
    Checkpoint validation: Modifying a category invalidates category cache.
    
    Requirements: 1.4, 4.3
    """

    def test_category_update_invalidates_category_cache(self):
        """
        Validate that updating a category invalidates its cache.
        
        When a category is modified:
        - Category detail cache should be invalidated
        - Categories list cache should be invalidated
        
        Requirements: 1.4, 4.3
        """
        from app.services.cache_service import CacheService
        
        mock_redis = MagicMock()
        storage = {}
        
        def mock_get(key):
            return storage.get(key)
        
        def mock_setex(key, ttl, value):
            storage[key] = value
        
        def mock_delete(*keys):
            for k in keys:
                if k in storage:
                    del storage[k]
            return len(keys)
        
        def mock_scan_iter(match):
            prefix = match.replace("*", "")
            return iter([k for k in storage.keys() if k.startswith(prefix)])
        
        mock_redis.get = mock_get
        mock_redis.setex = mock_setex
        mock_redis.delete = mock_delete
        mock_redis.scan_iter = mock_scan_iter
        
        service = CacheService(redis_client=mock_redis)
        
        # Pre-populate cache with category data
        category_id = 5
        service.set("categories", f"detail:{category_id}", {
            "id": category_id,
            "name": "Old Name",
            "color": "#FF0000"
        })
        service.set("categories", "list:page_1:size_50", {
            "items": [{"id": category_id, "name": "Old Name"}],
            "total": 1
        })
        
        # Verify cache is populated
        assert service.get("categories", f"detail:{category_id}") is not None
        assert service.get("categories", "list:page_1:size_50") is not None
        
        # Simulate category update - invalidate cache
        service.invalidate_category(category_id)
        service.invalidate_categories()
        
        # Verify category caches are invalidated
        assert service.get("categories", f"detail:{category_id}") is None, \
            "Category detail cache should be invalidated after update"
        assert service.get("categories", "list:page_1:size_50") is None, \
            "Categories list cache should be invalidated after update"

    def test_category_creation_invalidates_list_cache(self):
        """
        Validate that creating a category invalidates the list cache.
        
        Requirements: 1.4, 4.3
        """
        from app.services.cache_service import CacheService
        
        mock_redis = MagicMock()
        storage = {}
        
        def mock_get(key):
            return storage.get(key)
        
        def mock_setex(key, ttl, value):
            storage[key] = value
        
        def mock_delete(*keys):
            for k in keys:
                if k in storage:
                    del storage[k]
            return len(keys)
        
        def mock_scan_iter(match):
            prefix = match.replace("*", "")
            return iter([k for k in storage.keys() if k.startswith(prefix)])
        
        mock_redis.get = mock_get
        mock_redis.setex = mock_setex
        mock_redis.delete = mock_delete
        mock_redis.scan_iter = mock_scan_iter
        
        service = CacheService(redis_client=mock_redis)
        
        # Pre-populate cache with categories list
        service.set("categories", "list:page_1:size_50", {
            "items": [{"id": 1, "name": "Existing"}],
            "total": 1
        })
        service.set("categories", "list:page_2:size_50", {
            "items": [],
            "total": 1
        })
        
        # Verify cache is populated
        assert service.get("categories", "list:page_1:size_50") is not None
        
        # Simulate category creation - invalidate list cache
        service.invalidate_categories()
        
        # Verify all list caches are invalidated
        assert service.get("categories", "list:page_1:size_50") is None, \
            "Categories list page 1 should be invalidated"
        assert service.get("categories", "list:page_2:size_50") is None, \
            "Categories list page 2 should be invalidated"

    def test_category_deletion_invalidates_all_related_caches(self):
        """
        Validate that deleting a category invalidates all related caches.
        
        Requirements: 1.4, 4.3
        """
        from app.services.cache_service import CacheService
        
        mock_redis = MagicMock()
        storage = {}
        
        def mock_get(key):
            return storage.get(key)
        
        def mock_setex(key, ttl, value):
            storage[key] = value
        
        def mock_delete(*keys):
            for k in keys:
                if k in storage:
                    del storage[k]
            return len(keys)
        
        def mock_scan_iter(match):
            prefix = match.replace("*", "")
            return iter([k for k in storage.keys() if k.startswith(prefix)])
        
        mock_redis.get = mock_get
        mock_redis.setex = mock_setex
        mock_redis.delete = mock_delete
        mock_redis.scan_iter = mock_scan_iter
        
        service = CacheService(redis_client=mock_redis)
        
        # Pre-populate cache
        category_id = 10
        service.set("categories", f"detail:{category_id}", {"id": category_id})
        service.set("categories", "list:page_1:size_50", {"items": []})
        service.set("contacts", f"count:category:{category_id}", 5)
        
        # Simulate category deletion
        service.invalidate_category(category_id)
        service.invalidate_categories()
        
        # Verify all related caches are invalidated
        assert service.get("categories", f"detail:{category_id}") is None
        assert service.get("categories", "list:page_1:size_50") is None
        assert service.get("contacts", f"count:category:{category_id}") is None


class TestContactDeletionInvalidatesCache:
    """
    Checkpoint validation: Deleting a contact invalidates stats and category counts.
    
    Requirements: 1.3, 4.2
    """

    def test_contact_deletion_invalidates_stats_cache(self):
        """
        Validate that deleting a contact invalidates stats cache.
        
        Requirements: 1.3, 4.2
        """
        from app.services.cache_service import CacheService
        
        mock_redis = MagicMock()
        storage = {}
        
        def mock_get(key):
            return storage.get(key)
        
        def mock_setex(key, ttl, value):
            storage[key] = value
        
        def mock_delete(*keys):
            for k in keys:
                if k in storage:
                    del storage[k]
            return len(keys)
        
        def mock_scan_iter(match):
            prefix = match.replace("*", "")
            return iter([k for k in storage.keys() if k.startswith(prefix)])
        
        mock_redis.get = mock_get
        mock_redis.setex = mock_setex
        mock_redis.delete = mock_delete
        mock_redis.scan_iter = mock_scan_iter
        
        service = CacheService(redis_client=mock_redis)
        
        # Pre-populate cache with stats
        service.set("stats", "messages_global", {"total_contacts": 100})
        service.set("stats", "dashboard", {"contacts": 100})
        
        # Verify cache is populated
        assert service.get("stats", "messages_global") is not None
        
        # Simulate contact deletion - invalidate cache
        service.invalidate_contact_related(category_ids=[1])
        
        # Verify stats cache is invalidated
        assert service.get("stats", "messages_global") is None, \
            "Stats cache should be invalidated after contact deletion"
        assert service.get("stats", "dashboard") is None, \
            "Dashboard stats should be invalidated after contact deletion"

    def test_contact_deletion_invalidates_associated_category_counts(self):
        """
        Validate that deleting a contact invalidates associated category counts.
        
        Requirements: 4.2
        """
        from app.services.cache_service import CacheService
        
        mock_redis = MagicMock()
        storage = {}
        
        def mock_get(key):
            return storage.get(key)
        
        def mock_setex(key, ttl, value):
            storage[key] = value
        
        def mock_delete(*keys):
            for k in keys:
                if k in storage:
                    del storage[k]
            return len(keys)
        
        def mock_scan_iter(match):
            prefix = match.replace("*", "")
            return iter([k for k in storage.keys() if k.startswith(prefix)])
        
        mock_redis.get = mock_get
        mock_redis.setex = mock_setex
        mock_redis.delete = mock_delete
        mock_redis.scan_iter = mock_scan_iter
        
        service = CacheService(redis_client=mock_redis)
        
        # Pre-populate cache with category counts
        # Contact was in categories 1 and 3
        service.set("contacts", "count:category:1", 10)
        service.set("contacts", "count:category:2", 5)  # Not associated
        service.set("contacts", "count:category:3", 8)
        
        # Simulate contact deletion from categories 1 and 3
        service.invalidate_contact_related(category_ids=[1, 3])
        
        # Verify associated category counts are invalidated
        assert service.get("contacts", "count:category:1") is None, \
            "Category 1 count should be invalidated"
        assert service.get("contacts", "count:category:3") is None, \
            "Category 3 count should be invalidated"
        
        # Category 2 should NOT be invalidated
        assert service.get("contacts", "count:category:2") == 5, \
            "Category 2 count should NOT be invalidated"


class TestInvalidationUtilityFunctions:
    """
    Checkpoint validation: Utility functions for cache invalidation.
    
    These tests validate the helper functions used by routers.
    """

    def test_invalidate_cache_on_contact_change_function(self):
        """
        Validate the invalidate_cache_on_contact_change utility function.
        
        Requirements: 1.3, 4.1, 4.2
        """
        from app.services.cache_service import invalidate_cache_on_contact_change
        
        # This should not raise any exceptions even if Redis is unavailable
        # The function handles errors gracefully
        try:
            invalidate_cache_on_contact_change(category_ids=[1, 2, 3])
            invalidate_cache_on_contact_change()  # Without category_ids
        except Exception as e:
            # Function should handle errors gracefully
            pytest.fail(f"invalidate_cache_on_contact_change raised exception: {e}")

    def test_invalidate_cache_on_category_change_function(self):
        """
        Validate the invalidate_cache_on_category_change utility function.
        
        Requirements: 1.4, 4.3
        """
        from app.services.cache_service import invalidate_cache_on_category_change
        
        # This should not raise any exceptions even if Redis is unavailable
        try:
            invalidate_cache_on_category_change(category_id=1)
            invalidate_cache_on_category_change()  # Without category_id
        except Exception as e:
            pytest.fail(f"invalidate_cache_on_category_change raised exception: {e}")


class TestCacheConsistencyAfterMutations:
    """
    Checkpoint validation: Cache consistency after mutations.
    
    These tests validate that after invalidation, fresh data is fetched.
    """

    def test_cache_miss_after_invalidation_triggers_db_fetch(self):
        """
        Validate that cache miss after invalidation would trigger DB fetch.
        
        This simulates the complete flow:
        1. Data is cached
        2. Mutation occurs
        3. Cache is invalidated
        4. Next read is a cache miss
        5. Fresh data would be fetched from DB
        
        Requirements: 3.2
        """
        from app.services.cache_service import CacheService
        
        mock_redis = MagicMock()
        storage = {}
        
        def mock_get(key):
            return storage.get(key)
        
        def mock_setex(key, ttl, value):
            storage[key] = value
        
        def mock_delete(*keys):
            for k in keys:
                if k in storage:
                    del storage[k]
            return len(keys)
        
        def mock_scan_iter(match):
            prefix = match.replace("*", "")
            return iter([k for k in storage.keys() if k.startswith(prefix)])
        
        mock_redis.get = mock_get
        mock_redis.setex = mock_setex
        mock_redis.delete = mock_delete
        mock_redis.scan_iter = mock_scan_iter
        
        service = CacheService(redis_client=mock_redis)
        
        # Step 1: Cache initial data
        initial_stats = {"total_contacts": 100}
        service.set("stats", "messages_global", initial_stats)
        
        # Verify cache hit
        cached = service.get("stats", "messages_global")
        assert cached == initial_stats, "Should get cached data"
        
        # Step 2: Simulate mutation (contact created)
        # Step 3: Invalidate cache
        service.invalidate_stats()
        
        # Step 4: Next read is cache miss
        cached = service.get("stats", "messages_global")
        assert cached is None, "Should be cache miss after invalidation"
        
        # Step 5: Simulate DB fetch and re-cache with updated data
        updated_stats = {"total_contacts": 101}  # One more contact
        service.set("stats", "messages_global", updated_stats)
        
        # Verify updated data is now cached
        cached = service.get("stats", "messages_global")
        assert cached == updated_stats, "Should get updated cached data"

    def test_multiple_mutations_all_trigger_invalidation(self):
        """
        Validate that multiple mutations all trigger proper invalidation.
        
        Requirements: 1.3, 1.4, 4.1, 4.2, 4.3
        """
        from app.services.cache_service import CacheService
        
        mock_redis = MagicMock()
        storage = {}
        
        def mock_get(key):
            return storage.get(key)
        
        def mock_setex(key, ttl, value):
            storage[key] = value
        
        def mock_delete(*keys):
            for k in keys:
                if k in storage:
                    del storage[k]
            return len(keys)
        
        def mock_scan_iter(match):
            prefix = match.replace("*", "")
            return iter([k for k in storage.keys() if k.startswith(prefix)])
        
        mock_redis.get = mock_get
        mock_redis.setex = mock_setex
        mock_redis.delete = mock_delete
        mock_redis.scan_iter = mock_scan_iter
        
        service = CacheService(redis_client=mock_redis)
        
        # Simulate multiple mutations
        for i in range(5):
            # Cache data
            service.set("stats", "messages_global", {"count": i})
            assert service.get("stats", "messages_global") is not None
            
            # Mutation occurs - invalidate
            service.invalidate_stats()
            
            # Verify invalidation
            assert service.get("stats", "messages_global") is None, \
                f"Stats should be invalidated after mutation {i+1}"


class TestRouterIntegrationWithInvalidation:
    """
    Checkpoint validation: Router integration with cache invalidation.
    
    These tests validate that routers correctly call invalidation functions.
    """

    def test_contacts_router_imports_invalidation_function(self):
        """
        Validate that contacts router imports the invalidation function.
        """
        from app.routers.contacts import invalidate_cache_on_contact_change
        
        # Function should be imported and callable
        assert callable(invalidate_cache_on_contact_change)

    def test_categories_router_imports_invalidation_function(self):
        """
        Validate that categories router imports the invalidation function.
        """
        from app.routers.categories import invalidate_cache_on_category_change
        
        # Function should be imported and callable
        assert callable(invalidate_cache_on_category_change)

    def test_cache_service_has_required_invalidation_methods(self):
        """
        Validate that CacheService has all required invalidation methods.
        """
        from app.services.cache_service import CacheService
        
        # Check that all required methods exist
        assert hasattr(CacheService, 'invalidate_stats')
        assert hasattr(CacheService, 'invalidate_categories')
        assert hasattr(CacheService, 'invalidate_category')
        assert hasattr(CacheService, 'invalidate_contact_related')
        assert hasattr(CacheService, 'invalidate_pattern')
        
        # All should be callable
        service = CacheService.__new__(CacheService)
        assert callable(service.invalidate_stats)
        assert callable(service.invalidate_categories)
        assert callable(service.invalidate_category)
        assert callable(service.invalidate_contact_related)
        assert callable(service.invalidate_pattern)
