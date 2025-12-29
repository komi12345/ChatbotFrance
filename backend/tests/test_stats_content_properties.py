"""
Property-Based Tests for Stats Content Completeness

Property 14: Stats Content Completeness
*For any* stats response, the response SHALL include: total_messages, sent_count,
delivered_count, read_count, failed_count, pending_count.

**Validates: Requirements 9.2**

Task 15.4: Écrire le test property-based pour Stats Content
"""
import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from app.schemas.message import MessageStats


# =============================================================================
# Strategies for generating valid stats data
# =============================================================================

@st.composite
def valid_message_counts(draw):
    """
    Generate valid message counts where all values are non-negative integers.
    
    The total should equal the sum of all status counts.
    """
    sent = draw(st.integers(min_value=0, max_value=10000))
    delivered = draw(st.integers(min_value=0, max_value=10000))
    read = draw(st.integers(min_value=0, max_value=10000))
    failed = draw(st.integers(min_value=0, max_value=10000))
    pending = draw(st.integers(min_value=0, max_value=10000))
    
    total = sent + delivered + read + failed + pending
    
    return {
        "total_messages": total,
        "sent_count": sent,
        "delivered_count": delivered,
        "read_count": read,
        "failed_count": failed,
        "pending_count": pending
    }


@st.composite
def valid_stats_data(draw):
    """
    Generate complete valid stats data including rates.
    
    Rates are calculated based on counts and are valid percentages (0-100).
    """
    counts = draw(valid_message_counts())
    total = counts["total_messages"]
    
    # Calculate rates (avoid division by zero)
    if total > 0:
        success_rate = (counts["sent_count"] + counts["delivered_count"] + counts["read_count"]) / total * 100
        delivery_rate = (counts["delivered_count"] + counts["read_count"]) / total * 100
        read_rate = counts["read_count"] / total * 100
    else:
        success_rate = 0.0
        delivery_rate = 0.0
        read_rate = 0.0
    
    return {
        **counts,
        "success_rate": success_rate,
        "delivery_rate": delivery_rate,
        "read_rate": read_rate
    }


# =============================================================================
# Property 14: Stats Content Completeness
# =============================================================================

class TestStatsContentCompletenessProperty:
    """
    Property 14: Stats Content Completeness
    
    *For any* stats response, the response SHALL include: total_messages, sent_count,
    delivered_count, read_count, failed_count, pending_count.
    
    **Validates: Requirements 9.2**
    """

    @given(stats_data=valid_stats_data())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_property_14_stats_contains_all_required_fields(self, stats_data):
        """
        Property 14: Stats Content Completeness
        
        For any valid stats data, the MessageStats model SHALL contain all required fields:
        - total_messages
        - sent_count
        - delivered_count
        - read_count
        - failed_count
        - pending_count
        
        **Validates: Requirements 9.2**
        """
        # Create MessageStats from generated data
        stats = MessageStats(**stats_data)
        
        # Required fields per Requirements 9.2
        required_fields = [
            "total_messages",
            "sent_count",
            "delivered_count",
            "read_count",
            "failed_count",
            "pending_count"
        ]
        
        # Verify all required fields are present and accessible
        for field in required_fields:
            assert hasattr(stats, field), f"Stats should have field '{field}'"
            value = getattr(stats, field)
            assert value is not None, f"Field '{field}' should not be None"
            assert isinstance(value, int), f"Field '{field}' should be an integer"
            assert value >= 0, f"Field '{field}' should be non-negative"

    @given(stats_data=valid_stats_data())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_property_14_stats_total_equals_sum_of_counts(self, stats_data):
        """
        Property 14 (Invariant): Total messages equals sum of all status counts
        
        For any valid stats, total_messages SHALL equal the sum of:
        sent_count + delivered_count + read_count + failed_count + pending_count
        
        **Validates: Requirements 9.2**
        """
        stats = MessageStats(**stats_data)
        
        expected_total = (
            stats.sent_count +
            stats.delivered_count +
            stats.read_count +
            stats.failed_count +
            stats.pending_count
        )
        
        assert stats.total_messages == expected_total, \
            f"Total ({stats.total_messages}) should equal sum of counts ({expected_total})"

    @given(stats_data=valid_stats_data())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_property_14_stats_rates_are_valid_percentages(self, stats_data):
        """
        Property 14 (Invariant): Rate fields are valid percentages
        
        For any valid stats, success_rate, delivery_rate, and read_rate
        SHALL be between 0 and 100 (inclusive).
        
        **Validates: Requirements 9.2**
        """
        stats = MessageStats(**stats_data)
        
        # Verify rates are valid percentages
        assert 0 <= stats.success_rate <= 100, \
            f"success_rate ({stats.success_rate}) should be 0-100"
        assert 0 <= stats.delivery_rate <= 100, \
            f"delivery_rate ({stats.delivery_rate}) should be 0-100"
        assert 0 <= stats.read_rate <= 100, \
            f"read_rate ({stats.read_rate}) should be 0-100"

    @given(stats_data=valid_stats_data())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_property_14_stats_rates_are_consistent(self, stats_data):
        """
        Property 14 (Invariant): Rate calculations are consistent
        
        For any valid stats:
        - read_rate <= delivery_rate (read implies delivered)
        - delivery_rate <= success_rate (delivered implies sent)
        
        **Validates: Requirements 9.2**
        """
        stats = MessageStats(**stats_data)
        
        # Read rate should be <= delivery rate
        # (you can't read a message that wasn't delivered)
        assert stats.read_rate <= stats.delivery_rate + 0.01, \
            f"read_rate ({stats.read_rate}) should be <= delivery_rate ({stats.delivery_rate})"
        
        # Delivery rate should be <= success rate
        # (you can't deliver a message that wasn't sent)
        assert stats.delivery_rate <= stats.success_rate + 0.01, \
            f"delivery_rate ({stats.delivery_rate}) should be <= success_rate ({stats.success_rate})"


class TestStatsContentEdgeCases:
    """
    Edge case tests for stats content.
    """

    @given(st.integers(min_value=0, max_value=1000000))
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_property_14_stats_handles_large_counts(self, total):
        """
        Property 14 (Edge Case): Stats handles large message counts
        
        For any large total count, the stats model SHALL handle it correctly.
        
        **Validates: Requirements 9.2**
        """
        # Distribute total across statuses
        sent = total // 5
        delivered = total // 5
        read = total // 5
        failed = total // 10
        pending = total - sent - delivered - read - failed
        
        stats = MessageStats(
            total_messages=total,
            sent_count=sent,
            delivered_count=delivered,
            read_count=read,
            failed_count=failed,
            pending_count=pending,
            success_rate=60.0 if total > 0 else 0.0,
            delivery_rate=40.0 if total > 0 else 0.0,
            read_rate=20.0 if total > 0 else 0.0
        )
        
        assert stats.total_messages == total
        assert stats.sent_count + stats.delivered_count + stats.read_count + \
               stats.failed_count + stats.pending_count == total

    def test_property_14_stats_handles_zero_messages(self):
        """
        Property 14 (Edge Case): Stats handles zero messages
        
        When total_messages is 0, all counts and rates SHALL be 0.
        
        **Validates: Requirements 9.2**
        """
        stats = MessageStats(
            total_messages=0,
            sent_count=0,
            delivered_count=0,
            read_count=0,
            failed_count=0,
            pending_count=0,
            success_rate=0.0,
            delivery_rate=0.0,
            read_rate=0.0
        )
        
        assert stats.total_messages == 0
        assert stats.sent_count == 0
        assert stats.delivered_count == 0
        assert stats.read_count == 0
        assert stats.failed_count == 0
        assert stats.pending_count == 0
        assert stats.success_rate == 0.0
        assert stats.delivery_rate == 0.0
        assert stats.read_rate == 0.0

    def test_property_14_stats_handles_all_failed(self):
        """
        Property 14 (Edge Case): Stats handles all failed messages
        
        When all messages have failed, success_rate SHALL be 0.
        
        **Validates: Requirements 9.2**
        """
        stats = MessageStats(
            total_messages=100,
            sent_count=0,
            delivered_count=0,
            read_count=0,
            failed_count=100,
            pending_count=0,
            success_rate=0.0,
            delivery_rate=0.0,
            read_rate=0.0
        )
        
        assert stats.total_messages == 100
        assert stats.failed_count == 100
        assert stats.success_rate == 0.0

    def test_property_14_stats_handles_all_read(self):
        """
        Property 14 (Edge Case): Stats handles all read messages
        
        When all messages are read, all rates SHALL be 100%.
        
        **Validates: Requirements 9.2**
        """
        stats = MessageStats(
            total_messages=100,
            sent_count=0,
            delivered_count=0,
            read_count=100,
            failed_count=0,
            pending_count=0,
            success_rate=100.0,
            delivery_rate=100.0,
            read_rate=100.0
        )
        
        assert stats.total_messages == 100
        assert stats.read_count == 100
        assert stats.success_rate == 100.0
        assert stats.delivery_rate == 100.0
        assert stats.read_rate == 100.0


class TestStatsContentSerialization:
    """
    Tests for stats serialization (round-trip property).
    """

    @given(stats_data=valid_stats_data())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_property_14_stats_serialization_round_trip(self, stats_data):
        """
        Property 14 (Round Trip): Stats serialization is consistent
        
        For any valid stats, serializing to dict and back SHALL produce
        equivalent stats.
        
        **Validates: Requirements 9.2**
        """
        # Create original stats
        original = MessageStats(**stats_data)
        
        # Serialize to dict
        serialized = original.model_dump()
        
        # Deserialize back
        restored = MessageStats(**serialized)
        
        # Verify equivalence
        assert original.total_messages == restored.total_messages
        assert original.sent_count == restored.sent_count
        assert original.delivered_count == restored.delivered_count
        assert original.read_count == restored.read_count
        assert original.failed_count == restored.failed_count
        assert original.pending_count == restored.pending_count
        assert abs(original.success_rate - restored.success_rate) < 0.01
        assert abs(original.delivery_rate - restored.delivery_rate) < 0.01
        assert abs(original.read_rate - restored.read_rate) < 0.01
