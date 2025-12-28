"""
Property-based tests for Cache Invalidation After Mutation.

Tests Property 4 from the design document:
*For any* mutation operation (create/update/delete) on contacts or categories,
the relevant cache entries SHALL be invalidated (cache miss on next read).

**Feature: performance-optimization, Property 4: Invalidation After Mutation**
**Validates: Requirements 1.3, 1.4, 4.1, 4.2, 4.3, 4.4**
"""
import pytest
from hypothesis import given, settings as hyp_settings, strategies as st, HealthCheck
from unittest.mock import MagicMock, patch
from datetime import timedelta
from typing import List, Optional

# Configure Hypothesis for CI: minimum 100 iterations
hyp_settings.register_profile(
    "ci",
    max_examples=100,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None
)
hyp_settings.load_profile("ci")


# ==========================================================================
# STRATEGIES FOR INVALIDATION TESTS
# ==========================================================================

# Strategy for category IDs
category_id_strategy = st.integers(min_value=1, max_value=10000)

# Strategy for lists of category IDs
category_ids_list_strategy = st.lists(
    category_id_strategy,
    min_size=0,
    max_size=10
)

# Strategy for contact data
contact_data_strategy = st.fixed_dictionaries({
    "id": st.integers(min_value=1, max_value=10000),
    "phone_number": st.text(
        alphabet="0123456789",
        min_size=8,
        max_size=10
    ),
    "country_code": st.sampled_from(["+229", "+33", "+1", "+44"]),
    "first_name": st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    "last_name": st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
})

# Strategy for category data
category_data_strategy = st.fixed_dictionaries({
    "id": st.integers(min_value=1, max_value=10000),
    "name": st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    "color": st.sampled_from(["#FF0000", "#00FF00", "#0000FF", "#FFFF00", None]),
})


class MockCacheService:
    """
    Mock CacheService that tracks cache operations for testing invalidation.
    
    This mock simulates the real CacheService behavior while tracking:
    - Which keys have been set (cached)
    - Which keys have been invalidated (deleted)
    - Cache hits and misses
    """
    
    CACHE_PREFIX = "cache:"
    PROTECTED_PREFIXES = ("whatsapp:", "campaign:", "celery")
    DEFAULT_TTL = timedelta(seconds=60)
    STATS_TTL = timedelta(seconds=60)
    CATEGORIES_TTL = timedelta(seconds=120)
    CONTACTS_COUNT_TTL = timedelta(seconds=60)
    
    def __init__(self):
        self._storage = {}
        self._invalidated_keys = set()
        self._hits = 0
        self._misses = 0
    
    def _make_key(self, namespace: str, key: str) -> str:
        return f"{self.CACHE_PREFIX}{namespace}:{key}"
    
    def _is_protected_key(self, key: str) -> bool:
        return any(key.startswith(prefix) for prefix in self.PROTECTED_PREFIXES)
    
    def get(self, namespace: str, key: str):
        cache_key = self._make_key(namespace, key)
        if cache_key in self._storage:
            self._hits += 1
            return self._storage[cache_key]
        self._misses += 1
        return None
    
    def set(self, namespace: str, key: str, value, ttl=None) -> bool:
        cache_key = self._make_key(namespace, key)
        if self._is_protected_key(cache_key):
            return False
        self._storage[cache_key] = value
        return True
    
    def delete(self, namespace: str, key: str) -> bool:
        cache_key = self._make_key(namespace, key)
        self._invalidated_keys.add(cache_key)
        if cache_key in self._storage:
            del self._storage[cache_key]
        return True
    
    def invalidate_pattern(self, pattern: str) -> int:
        full_pattern = f"{self.CACHE_PREFIX}{pattern}"
        # Simple pattern matching (just prefix matching for tests)
        prefix = full_pattern.replace("*", "")
        keys_to_delete = [k for k in self._storage.keys() if k.startswith(prefix)]
        for key in keys_to_delete:
            self._invalidated_keys.add(key)
            del self._storage[key]
        return len(keys_to_delete)
    
    def invalidate_stats(self) -> int:
        return self.invalidate_pattern("stats:*")
    
    def invalidate_categories(self) -> int:
        return self.invalidate_pattern("categories:*")
    
    def invalidate_category(self, category_id: int) -> int:
        count = 0
        count += self.delete("categories", f"detail:{category_id}") and 1 or 0
        count += self.delete("contacts", f"count:category:{category_id}") and 1 or 0
        return count
    
    def invalidate_contact_related(self, category_ids: Optional[List[int]] = None) -> int:
        count = 0
        count += self.invalidate_stats()
        if category_ids:
            for cat_id in category_ids:
                count += self.invalidate_category(cat_id)
        return count
    
    def was_key_invalidated(self, namespace: str, key: str) -> bool:
        """Check if a specific key was invalidated."""
        cache_key = self._make_key(namespace, key)
        return cache_key in self._invalidated_keys
    
    def was_pattern_invalidated(self, pattern: str) -> bool:
        """Check if any key matching the pattern was invalidated."""
        prefix = f"{self.CACHE_PREFIX}{pattern}".replace("*", "")
        return any(k.startswith(prefix) for k in self._invalidated_keys)
    
    def get_invalidated_keys(self) -> set:
        """Return all invalidated keys."""
        return self._invalidated_keys.copy()
    
    def reset(self):
        """Reset the mock state."""
        self._storage.clear()
        self._invalidated_keys.clear()
        self._hits = 0
        self._misses = 0


class TestInvalidationAfterMutationProperty:
    """
    Property 4: Invalidation After Mutation
    
    *For any* mutation operation (create/update/delete) on contacts or categories,
    the relevant cache entries SHALL be invalidated (cache miss on next read).
    
    **Feature: performance-optimization, Property 4: Invalidation After Mutation**
    **Validates: Requirements 1.3, 1.4, 4.1, 4.2, 4.3, 4.4**
    """

    @given(category_ids=category_ids_list_strategy)
    def test_contact_creation_invalidates_stats_cache(
        self,
        category_ids: List[int]
    ):
        """
        **Feature: performance-optimization, Property 4: Invalidation After Mutation**
        **Validates: Requirements 1.3, 4.1**
        
        For any contact creation with any set of category associations,
        the stats cache should be invalidated.
        """
        cache = MockCacheService()
        
        # Pre-populate cache with stats data
        cache.set("stats", "messages_global", {"total": 100})
        cache.set("stats", "dashboard", {"contacts": 50})
        
        # Verify cache is populated
        assert cache.get("stats", "messages_global") is not None
        assert cache.get("stats", "dashboard") is not None
        
        # Simulate contact creation invalidation
        cache.invalidate_contact_related(category_ids if category_ids else None)
        
        # Property: stats cache should be invalidated (cache miss on next read)
        assert cache.get("stats", "messages_global") is None, \
            "Stats cache should be invalidated after contact creation"
        assert cache.get("stats", "dashboard") is None, \
            "Dashboard stats cache should be invalidated after contact creation"

    @given(category_ids=st.lists(category_id_strategy, min_size=1, max_size=5))
    def test_contact_creation_invalidates_associated_category_caches(
        self,
        category_ids: List[int]
    ):
        """
        **Feature: performance-optimization, Property 4: Invalidation After Mutation**
        **Validates: Requirements 4.1**
        
        For any contact creation with category associations,
        the cache for each associated category should be invalidated.
        """
        cache = MockCacheService()
        
        # Pre-populate cache with category data for each category
        for cat_id in category_ids:
            cache.set("categories", f"detail:{cat_id}", {"id": cat_id, "name": f"Cat {cat_id}"})
            cache.set("contacts", f"count:category:{cat_id}", 10)
        
        # Verify cache is populated
        for cat_id in category_ids:
            assert cache.get("categories", f"detail:{cat_id}") is not None
            assert cache.get("contacts", f"count:category:{cat_id}") is not None
        
        # Simulate contact creation invalidation
        cache.invalidate_contact_related(category_ids)
        
        # Property: each associated category cache should be invalidated
        for cat_id in category_ids:
            assert cache.get("categories", f"detail:{cat_id}") is None, \
                f"Category {cat_id} detail cache should be invalidated"
            assert cache.get("contacts", f"count:category:{cat_id}") is None, \
                f"Category {cat_id} contact count cache should be invalidated"

    @given(category_ids=category_ids_list_strategy)
    def test_contact_deletion_invalidates_stats_cache(
        self,
        category_ids: List[int]
    ):
        """
        **Feature: performance-optimization, Property 4: Invalidation After Mutation**
        **Validates: Requirements 1.3, 4.2**
        
        For any contact deletion with any set of category associations,
        the stats cache should be invalidated.
        """
        cache = MockCacheService()
        
        # Pre-populate cache with stats data
        cache.set("stats", "messages_global", {"total": 100})
        cache.set("stats", "dashboard", {"contacts": 50})
        
        # Simulate contact deletion invalidation (same as creation)
        cache.invalidate_contact_related(category_ids if category_ids else None)
        
        # Property: stats cache should be invalidated after contact deletion
        assert cache.get("stats", "messages_global") is None, \
            "Stats cache should be invalidated after contact deletion"
        assert cache.get("stats", "dashboard") is None, \
            "Dashboard stats cache should be invalidated after contact deletion"

    @given(category_ids=st.lists(category_id_strategy, min_size=1, max_size=5))
    def test_contact_deletion_invalidates_associated_category_caches(
        self,
        category_ids: List[int]
    ):
        """
        **Feature: performance-optimization, Property 4: Invalidation After Mutation**
        **Validates: Requirements 4.2**
        
        For any contact deletion with category associations,
        the cache for each associated category should be invalidated.
        """
        cache = MockCacheService()
        
        # Pre-populate cache with category data
        for cat_id in category_ids:
            cache.set("categories", f"detail:{cat_id}", {"id": cat_id})
            cache.set("contacts", f"count:category:{cat_id}", 10)
        
        # Simulate contact deletion invalidation
        cache.invalidate_contact_related(category_ids)
        
        # Property: each associated category cache should be invalidated
        for cat_id in category_ids:
            assert cache.get("categories", f"detail:{cat_id}") is None, \
                f"Category {cat_id} detail cache should be invalidated after contact deletion"
            assert cache.get("contacts", f"count:category:{cat_id}") is None, \
                f"Category {cat_id} contact count cache should be invalidated after contact deletion"

    @given(category_id=category_id_strategy)
    def test_category_creation_invalidates_categories_list_cache(
        self,
        category_id: int
    ):
        """
        **Feature: performance-optimization, Property 4: Invalidation After Mutation**
        **Validates: Requirements 1.4, 4.3**
        
        For any category creation, the categories list cache should be invalidated.
        """
        cache = MockCacheService()
        
        # Pre-populate cache with categories list
        cache.set("categories", "list:page_1:size_50", {"items": [], "total": 0})
        cache.set("categories", "list:page_2:size_50", {"items": [], "total": 0})
        
        # Verify cache is populated
        assert cache.get("categories", "list:page_1:size_50") is not None
        
        # Simulate category creation invalidation
        cache.invalidate_categories()
        
        # Property: categories list cache should be invalidated
        assert cache.get("categories", "list:page_1:size_50") is None, \
            "Categories list cache should be invalidated after category creation"
        assert cache.get("categories", "list:page_2:size_50") is None, \
            "All categories list pages should be invalidated"

    @given(category_id=category_id_strategy)
    def test_category_update_invalidates_category_detail_cache(
        self,
        category_id: int
    ):
        """
        **Feature: performance-optimization, Property 4: Invalidation After Mutation**
        **Validates: Requirements 1.4, 4.3**
        
        For any category update, the specific category detail cache should be invalidated.
        """
        cache = MockCacheService()
        
        # Pre-populate cache with category detail
        cache.set("categories", f"detail:{category_id}", {"id": category_id, "name": "Test"})
        cache.set("contacts", f"count:category:{category_id}", 5)
        
        # Verify cache is populated
        assert cache.get("categories", f"detail:{category_id}") is not None
        
        # Simulate category update invalidation
        cache.invalidate_category(category_id)
        cache.invalidate_categories()
        
        # Property: category detail cache should be invalidated
        assert cache.get("categories", f"detail:{category_id}") is None, \
            "Category detail cache should be invalidated after update"
        assert cache.get("contacts", f"count:category:{category_id}") is None, \
            "Category contact count cache should be invalidated after update"

    @given(category_id=category_id_strategy)
    def test_category_deletion_invalidates_all_related_caches(
        self,
        category_id: int
    ):
        """
        **Feature: performance-optimization, Property 4: Invalidation After Mutation**
        **Validates: Requirements 1.4, 4.3**
        
        For any category deletion, all related caches should be invalidated.
        """
        cache = MockCacheService()
        
        # Pre-populate cache with category data
        cache.set("categories", f"detail:{category_id}", {"id": category_id})
        cache.set("categories", "list:page_1:size_50", {"items": []})
        cache.set("contacts", f"count:category:{category_id}", 10)
        
        # Simulate category deletion invalidation
        cache.invalidate_category(category_id)
        cache.invalidate_categories()
        
        # Property: all related caches should be invalidated
        assert cache.get("categories", f"detail:{category_id}") is None, \
            "Category detail cache should be invalidated after deletion"
        assert cache.get("categories", "list:page_1:size_50") is None, \
            "Categories list cache should be invalidated after deletion"
        assert cache.get("contacts", f"count:category:{category_id}") is None, \
            "Category contact count cache should be invalidated after deletion"

    @given(
        category_ids=st.lists(category_id_strategy, min_size=1, max_size=5),
        other_category_id=category_id_strategy
    )
    def test_invalidation_does_not_affect_unrelated_caches(
        self,
        category_ids: List[int],
        other_category_id: int
    ):
        """
        **Feature: performance-optimization, Property 4: Invalidation After Mutation**
        **Validates: Requirements 4.1, 4.2, 4.3**
        
        For any mutation, only the relevant caches should be invalidated,
        not unrelated caches.
        """
        # Ensure other_category_id is not in category_ids
        if other_category_id in category_ids:
            other_category_id = max(category_ids) + 1
        
        cache = MockCacheService()
        
        # Pre-populate cache with data for both related and unrelated categories
        for cat_id in category_ids:
            cache.set("categories", f"detail:{cat_id}", {"id": cat_id})
            cache.set("contacts", f"count:category:{cat_id}", 10)
        
        # Pre-populate unrelated category cache
        cache.set("categories", f"detail:{other_category_id}", {"id": other_category_id})
        cache.set("contacts", f"count:category:{other_category_id}", 20)
        
        # Simulate contact mutation invalidation for specific categories
        cache.invalidate_contact_related(category_ids)
        
        # Property: unrelated category caches should NOT be invalidated
        # Note: The current implementation invalidates all stats but only specific categories
        assert cache.get("categories", f"detail:{other_category_id}") is not None, \
            f"Unrelated category {other_category_id} detail cache should NOT be invalidated"
        assert cache.get("contacts", f"count:category:{other_category_id}") is not None, \
            f"Unrelated category {other_category_id} contact count should NOT be invalidated"

    @given(category_ids=category_ids_list_strategy)
    def test_invalidation_results_in_cache_miss(
        self,
        category_ids: List[int]
    ):
        """
        **Feature: performance-optimization, Property 4: Invalidation After Mutation**
        **Validates: Requirements 1.3, 1.4, 4.1, 4.2, 4.3, 4.4**
        
        For any invalidation operation, subsequent reads should result in cache misses.
        """
        cache = MockCacheService()
        
        # Pre-populate cache
        cache.set("stats", "messages_global", {"total": 100})
        for cat_id in category_ids:
            cache.set("categories", f"detail:{cat_id}", {"id": cat_id})
        
        # Record initial hits
        initial_misses = cache._misses
        
        # Invalidate
        cache.invalidate_contact_related(category_ids if category_ids else None)
        
        # Read invalidated keys
        cache.get("stats", "messages_global")
        for cat_id in category_ids:
            cache.get("categories", f"detail:{cat_id}")
        
        # Property: all reads after invalidation should be misses
        expected_misses = initial_misses + 1 + len(category_ids)  # stats + categories
        assert cache._misses == expected_misses, \
            f"Expected {expected_misses} misses after invalidation, got {cache._misses}"

    @given(
        num_mutations=st.integers(min_value=1, max_value=10),
        category_id=category_id_strategy
    )
    def test_multiple_mutations_all_trigger_invalidation(
        self,
        num_mutations: int,
        category_id: int
    ):
        """
        **Feature: performance-optimization, Property 4: Invalidation After Mutation**
        **Validates: Requirements 1.3, 1.4, 4.1, 4.2, 4.3, 4.4**
        
        For any sequence of mutations, each mutation should trigger invalidation.
        """
        cache = MockCacheService()
        
        for i in range(num_mutations):
            # Re-populate cache (simulating data being cached again)
            cache.set("stats", "messages_global", {"total": 100 + i})
            cache.set("categories", f"detail:{category_id}", {"id": category_id})
            
            # Verify cache is populated
            assert cache.get("stats", "messages_global") is not None
            
            # Simulate mutation invalidation
            cache.invalidate_contact_related([category_id])
            
            # Property: cache should be invalidated after each mutation
            assert cache.get("stats", "messages_global") is None, \
                f"Stats cache should be invalidated after mutation {i+1}"
            assert cache.get("categories", f"detail:{category_id}") is None, \
                f"Category cache should be invalidated after mutation {i+1}"


class TestInvalidationWithRealCacheService:
    """
    Integration tests using the real CacheService with mocked Redis.
    
    These tests verify that the actual CacheService implementation
    correctly invalidates caches after mutations.
    
    **Feature: performance-optimization, Property 4: Invalidation After Mutation**
    **Validates: Requirements 1.3, 1.4, 4.1, 4.2, 4.3, 4.4**
    """

    @given(category_ids=st.lists(category_id_strategy, min_size=0, max_size=5))
    def test_invalidate_contact_related_clears_stats(
        self,
        category_ids: List[int]
    ):
        """
        **Feature: performance-optimization, Property 4: Invalidation After Mutation**
        **Validates: Requirements 4.1, 4.2**
        
        For any contact mutation, invalidate_contact_related should clear stats cache.
        """
        from app.services.cache_service import CacheService
        
        # Create service with mocked Redis
        service = CacheService.__new__(CacheService)
        service.CACHE_PREFIX = "cache:"
        service.PROTECTED_PREFIXES = ("whatsapp:", "campaign:", "celery")
        service.DEFAULT_TTL = timedelta(seconds=60)
        service._hits = 0
        service._misses = 0
        
        # Track deleted keys
        deleted_patterns = []
        
        def mock_scan_iter(match):
            # Return keys matching the pattern
            if "stats:*" in match:
                return iter(["cache:stats:messages_global", "cache:stats:dashboard"])
            elif "categories:*" in match:
                return iter([])
            return iter([])
        
        def mock_delete(*keys):
            deleted_patterns.extend(keys)
            return len(keys)
        
        mock_redis = MagicMock()
        mock_redis.scan_iter = mock_scan_iter
        mock_redis.delete = mock_delete
        service._redis = mock_redis
        
        # Call invalidate_contact_related
        service.invalidate_contact_related(category_ids if category_ids else None)
        
        # Property: stats keys should be deleted
        assert any("stats" in str(k) for k in deleted_patterns), \
            "Stats cache keys should be deleted after contact mutation"

    @given(category_id=category_id_strategy)
    def test_invalidate_category_clears_specific_category(
        self,
        category_id: int
    ):
        """
        **Feature: performance-optimization, Property 4: Invalidation After Mutation**
        **Validates: Requirements 4.3**
        
        For any category mutation, invalidate_category should clear that category's cache.
        """
        from app.services.cache_service import CacheService
        
        service = CacheService.__new__(CacheService)
        service.CACHE_PREFIX = "cache:"
        service.PROTECTED_PREFIXES = ("whatsapp:", "campaign:", "celery")
        
        deleted_keys = []
        
        def mock_delete(key):
            deleted_keys.append(key)
            return 1
        
        mock_redis = MagicMock()
        mock_redis.delete = mock_delete
        service._redis = mock_redis
        
        # Call invalidate_category
        service.invalidate_category(category_id)
        
        # Property: specific category keys should be deleted
        expected_detail_key = f"cache:categories:detail:{category_id}"
        expected_count_key = f"cache:contacts:count:category:{category_id}"
        
        assert expected_detail_key in deleted_keys, \
            f"Category detail key {expected_detail_key} should be deleted"
        assert expected_count_key in deleted_keys, \
            f"Category count key {expected_count_key} should be deleted"
