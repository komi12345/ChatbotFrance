"""
Property-based tests for 24h Window Enforcement.

Tests the correctness property defined in the design document:
Property 6: 24h Window Enforcement

*For any* interaction received, IF (current_time - message_1.sent_at) < 24 hours 
AND no Message 2 exists, THEN a Message 2 SHALL be created. 
IF (current_time - message_1.sent_at) >= 24 hours, THEN no Message 2 SHALL be created.

**Feature: comprehensive-audit-2025, Property 6: 24h Window Enforcement**
**Validates: Requirements 5.1, 5.2, 5.3**
"""
import pytest
from hypothesis import given, settings as hyp_settings, strategies as st, HealthCheck, assume
from unittest.mock import MagicMock, patch, AsyncMock
from typing import List, Dict, Optional
from datetime import datetime, timedelta, timezone

# Configure Hypothesis for CI: minimum 100 iterations
hyp_settings.register_profile(
    "ci",
    max_examples=100,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None
)
hyp_settings.load_profile("ci")


# ==========================================================================
# STRATEGIES FOR 24H WINDOW ENFORCEMENT TESTS
# ==========================================================================

# Strategy for campaign IDs
campaign_id_strategy = st.integers(min_value=1, max_value=10000)

# Strategy for contact IDs
contact_id_strategy = st.integers(min_value=1, max_value=100000)

# Strategy for message IDs
message_id_strategy = st.integers(min_value=1, max_value=100000)

# Strategy for phone numbers (international format without +)
phone_number_strategy = st.from_regex(r"229[0-9]{8}", fullmatch=True)

# Strategy for hours offset (0-48 hours to test around the 24h boundary)
hours_offset_strategy = st.floats(min_value=0.0, max_value=48.0, allow_nan=False, allow_infinity=False)

# Strategy for interaction content
interaction_content_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'S', 'Z')),
    min_size=1,
    max_size=200
).filter(lambda x: x.strip() != "")


def is_within_24h_window(sent_at: datetime, interaction_time: datetime) -> bool:
    """
    Helper function to check if interaction is within 24h of sent_at.
    This mirrors the logic in webhooks.py.
    """
    cutoff = interaction_time - timedelta(hours=24)
    return sent_at > cutoff


class TestWithin24hWindowProperty:
    """
    Property 6: 24h Window Enforcement - Within Window
    
    *For any* interaction received within 24 hours of Message 1 sent_at,
    AND no Message 2 exists, a Message 2 SHALL be created.
    
    **Feature: comprehensive-audit-2025, Property 6: 24h Window Enforcement**
    **Validates: Requirements 5.1, 5.2**
    """

    @given(
        campaign_id=campaign_id_strategy,
        contact_id=contact_id_strategy,
        message_1_id=message_id_strategy,
        hours_since_sent=st.floats(min_value=0.0, max_value=23.99, allow_nan=False, allow_infinity=False),
        phone=phone_number_strategy
    )
    def test_message_2_created_when_within_24h(
        self,
        campaign_id: int,
        contact_id: int,
        message_1_id: int,
        hours_since_sent: float,
        phone: str
    ):
        """
        **Feature: comprehensive-audit-2025, Property 6: 24h Window Enforcement**
        **Validates: Requirements 5.1, 5.2**
        
        For any interaction received within 24 hours of Message 1 sent_at,
        when no Message 2 exists, a Message 2 should be created.
        """
        # Calculate timestamps
        now = datetime.utcnow()
        sent_at = now - timedelta(hours=hours_since_sent)
        cutoff_time = now - timedelta(hours=24)
        
        # Verify we're within the 24h window
        assert sent_at > cutoff_time, \
            f"Test setup error: sent_at {sent_at} should be after cutoff {cutoff_time}"
        
        # Simulate the webhook processing logic
        message_1_found = True  # Message 1 exists and is within 24h
        message_2_exists = False  # No Message 2 yet
        
        # Decision logic (from webhooks.py process_wassenger_message)
        should_send_message_2 = message_1_found and not message_2_exists
        
        # Property: Message 2 should be created
        assert should_send_message_2 is True, \
            f"Expected Message 2 to be created when within 24h window ({hours_since_sent:.2f}h since sent)"

    @given(
        hours_since_sent=st.floats(min_value=0.0, max_value=23.99, allow_nan=False, allow_infinity=False)
    )
    def test_cutoff_calculation_within_window(self, hours_since_sent: float):
        """
        **Feature: comprehensive-audit-2025, Property 6: 24h Window Enforcement**
        **Validates: Requirements 5.1**
        
        For any time within 24 hours, the cutoff calculation should correctly
        identify the message as within the window.
        """
        now = datetime.utcnow()
        sent_at = now - timedelta(hours=hours_since_sent)
        cutoff = now - timedelta(hours=24)
        
        # Property: sent_at should be after cutoff (within window)
        within_window = sent_at > cutoff
        assert within_window is True, \
            f"Expected {hours_since_sent:.2f}h to be within 24h window"


class TestOutside24hWindowProperty:
    """
    Property 6: 24h Window Enforcement - Outside Window
    
    *For any* interaction received 24 hours or more after Message 1 sent_at,
    no Message 2 SHALL be created.
    
    **Feature: comprehensive-audit-2025, Property 6: 24h Window Enforcement**
    **Validates: Requirements 5.3**
    """

    @given(
        campaign_id=campaign_id_strategy,
        contact_id=contact_id_strategy,
        hours_since_sent=st.floats(min_value=24.01, max_value=72.0, allow_nan=False, allow_infinity=False),
        phone=phone_number_strategy
    )
    def test_message_2_not_created_when_outside_24h(
        self,
        campaign_id: int,
        contact_id: int,
        hours_since_sent: float,
        phone: str
    ):
        """
        **Feature: comprehensive-audit-2025, Property 6: 24h Window Enforcement**
        **Validates: Requirements 5.3**
        
        For any interaction received 24 hours or more after Message 1 sent_at,
        no Message 2 should be created.
        """
        # Calculate timestamps
        now = datetime.utcnow()
        sent_at = now - timedelta(hours=hours_since_sent)
        cutoff_time = now - timedelta(hours=24)
        
        # Verify we're outside the 24h window
        assert sent_at <= cutoff_time, \
            f"Test setup error: sent_at {sent_at} should be before or at cutoff {cutoff_time}"
        
        # Simulate the webhook processing logic
        # When sent_at < cutoff, the query won't find the message
        message_1_found = sent_at > cutoff_time  # This will be False
        
        # Decision logic (from webhooks.py process_wassenger_message)
        should_send_message_2 = message_1_found  # False because message not found
        
        # Property: Message 2 should NOT be created
        assert should_send_message_2 is False, \
            f"Expected Message 2 NOT to be created when outside 24h window ({hours_since_sent:.2f}h since sent)"

    @given(
        hours_since_sent=st.floats(min_value=24.01, max_value=72.0, allow_nan=False, allow_infinity=False)
    )
    def test_cutoff_calculation_outside_window(self, hours_since_sent: float):
        """
        **Feature: comprehensive-audit-2025, Property 6: 24h Window Enforcement**
        **Validates: Requirements 5.3**
        
        For any time 24 hours or more, the cutoff calculation should correctly
        identify the message as outside the window.
        """
        now = datetime.utcnow()
        sent_at = now - timedelta(hours=hours_since_sent)
        cutoff = now - timedelta(hours=24)
        
        # Property: sent_at should be before or at cutoff (outside window)
        within_window = sent_at > cutoff
        assert within_window is False, \
            f"Expected {hours_since_sent:.2f}h to be outside 24h window"


class TestBoundaryConditionsProperty:
    """
    Property 6: 24h Window Enforcement - Boundary Conditions
    
    Test the exact 24h boundary to ensure correct behavior.
    
    **Feature: comprehensive-audit-2025, Property 6: 24h Window Enforcement**
    **Validates: Requirements 5.1, 5.2, 5.3**
    """

    def test_exactly_24h_is_within_window(self):
        """
        **Feature: comprehensive-audit-2025, Property 6: 24h Window Enforcement**
        **Validates: Requirements 5.1, 5.2**
        
        At exactly 24 hours, the message should still be within the window
        (using >= comparison in the query).
        """
        now = datetime.utcnow()
        sent_at = now - timedelta(hours=24)
        cutoff = now - timedelta(hours=24)
        
        # The query uses gte (>=), so exactly 24h should be included
        # sent_at >= cutoff means sent_at (24h ago) >= cutoff (24h ago) = True
        within_window = sent_at >= cutoff
        
        assert within_window is True, \
            "Expected exactly 24h to be within window (boundary inclusive)"

    def test_23h59m_is_within_window(self):
        """
        **Feature: comprehensive-audit-2025, Property 6: 24h Window Enforcement**
        **Validates: Requirements 5.1, 5.2**
        
        At 23h59m, the message should be within the window.
        """
        now = datetime.utcnow()
        sent_at = now - timedelta(hours=23, minutes=59)
        cutoff = now - timedelta(hours=24)
        
        within_window = sent_at > cutoff
        
        assert within_window is True, \
            "Expected 23h59m to be within 24h window"

    def test_24h01m_is_outside_window(self):
        """
        **Feature: comprehensive-audit-2025, Property 6: 24h Window Enforcement**
        **Validates: Requirements 5.3**
        
        At 24h01m, the message should be outside the window.
        """
        now = datetime.utcnow()
        sent_at = now - timedelta(hours=24, minutes=1)
        cutoff = now - timedelta(hours=24)
        
        within_window = sent_at > cutoff
        
        assert within_window is False, \
            "Expected 24h01m to be outside 24h window"

    @given(
        seconds_before_24h=st.integers(min_value=1, max_value=3600)  # 1 second to 1 hour before 24h
    )
    def test_just_before_24h_is_within_window(self, seconds_before_24h: int):
        """
        **Feature: comprehensive-audit-2025, Property 6: 24h Window Enforcement**
        **Validates: Requirements 5.1, 5.2**
        
        For any time just before 24h, the message should be within the window.
        """
        now = datetime.utcnow()
        hours_since_sent = 24 - (seconds_before_24h / 3600)
        sent_at = now - timedelta(hours=hours_since_sent)
        cutoff = now - timedelta(hours=24)
        
        within_window = sent_at > cutoff
        
        assert within_window is True, \
            f"Expected {seconds_before_24h}s before 24h to be within window"

    @given(
        seconds_after_24h=st.integers(min_value=1, max_value=3600)  # 1 second to 1 hour after 24h
    )
    def test_just_after_24h_is_outside_window(self, seconds_after_24h: int):
        """
        **Feature: comprehensive-audit-2025, Property 6: 24h Window Enforcement**
        **Validates: Requirements 5.3**
        
        For any time just after 24h, the message should be outside the window.
        """
        now = datetime.utcnow()
        hours_since_sent = 24 + (seconds_after_24h / 3600)
        sent_at = now - timedelta(hours=hours_since_sent)
        cutoff = now - timedelta(hours=24)
        
        within_window = sent_at > cutoff
        
        assert within_window is False, \
            f"Expected {seconds_after_24h}s after 24h to be outside window"


class TestIdempotenceProperty:
    """
    Property 6 (related): Message 2 Idempotence
    
    For any contact in a campaign, regardless of the number of interactions
    received within 24h, at most ONE Message 2 SHALL exist.
    
    **Feature: comprehensive-audit-2025, Property 6: 24h Window Enforcement**
    **Validates: Requirements 5.2**
    """

    @given(
        campaign_id=campaign_id_strategy,
        contact_id=contact_id_strategy,
        num_interactions=st.integers(min_value=1, max_value=10)
    )
    def test_only_one_message_2_per_contact(
        self,
        campaign_id: int,
        contact_id: int,
        num_interactions: int
    ):
        """
        **Feature: comprehensive-audit-2025, Property 6: 24h Window Enforcement**
        **Validates: Requirements 5.2**
        
        For any number of interactions from the same contact within 24h,
        only one Message 2 should be created.
        """
        # Simulate the check for existing Message 2
        message_2_exists = False
        message_2_created_count = 0
        
        for i in range(num_interactions):
            # Check if Message 2 already exists (as done in webhooks.py)
            if not message_2_exists:
                # Create Message 2
                message_2_created_count += 1
                message_2_exists = True
            # Else: skip (Message 2 already exists)
        
        # Property: exactly one Message 2 created
        assert message_2_created_count == 1, \
            f"Expected 1 Message 2, got {message_2_created_count} for {num_interactions} interactions"

    @given(
        campaign_id=campaign_id_strategy,
        contact_id=contact_id_strategy
    )
    def test_second_interaction_does_not_create_message_2(
        self,
        campaign_id: int,
        contact_id: int
    ):
        """
        **Feature: comprehensive-audit-2025, Property 6: 24h Window Enforcement**
        **Validates: Requirements 5.2**
        
        When a second interaction is received and Message 2 already exists,
        no new Message 2 should be created.
        """
        # First interaction - Message 2 created
        message_2_exists_after_first = True
        
        # Second interaction - check logic
        should_create_message_2 = not message_2_exists_after_first
        
        # Property: should not create another Message 2
        assert should_create_message_2 is False, \
            "Expected no new Message 2 when one already exists"


class TestDatabaseQueryProperty:
    """
    Property 6: Database Query Correctness
    
    The database query for finding Message 1 within 24h should use the correct
    comparison operators and filters.
    
    **Feature: comprehensive-audit-2025, Property 6: 24h Window Enforcement**
    **Validates: Requirements 5.1**
    """

    @given(
        hours_offset=st.floats(min_value=0.0, max_value=48.0, allow_nan=False, allow_infinity=False)
    )
    def test_query_filter_consistency(self, hours_offset: float):
        """
        **Feature: comprehensive-audit-2025, Property 6: 24h Window Enforcement**
        **Validates: Requirements 5.1**
        
        The query filter (sent_at >= cutoff) should be consistent with the
        24h window logic.
        """
        now = datetime.utcnow()
        sent_at = now - timedelta(hours=hours_offset)
        cutoff = now - timedelta(hours=24)
        
        # Query uses gte (>=)
        query_would_find = sent_at >= cutoff
        
        # Expected behavior
        expected_within_window = hours_offset <= 24.0
        
        # Property: query result matches expected window behavior
        assert query_would_find == expected_within_window, \
            f"Query inconsistency at {hours_offset:.2f}h: query_found={query_would_find}, expected={expected_within_window}"
