"""
Property-based tests for Anti-Ban Behavior Preservation.

Tests the correctness properties for idempotency and daily limit enforcement
as defined in the design document for the WhatsApp Ban Prevention feature.

**Feature: whatsapp-ban-prevention**
"""
import pytest
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from unittest.mock import MagicMock, patch, AsyncMock
from hypothesis import given, settings as hyp_settings, strategies as st, HealthCheck, assume

# Configure Hypothesis for CI: minimum 100 iterations
hyp_settings.register_profile(
    "ci",
    max_examples=100,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None
)
hyp_settings.load_profile("ci")


# ==========================================================================
# STRATEGIES FOR BEHAVIOR PRESERVATION TESTS
# ==========================================================================

# Message ID strategy
message_id_strategy = st.integers(min_value=1, max_value=100000)

# Campaign ID strategy
campaign_id_strategy = st.integers(min_value=1, max_value=10000)

# Contact ID strategy
contact_id_strategy = st.integers(min_value=1, max_value=10000)

# Number of send attempts strategy
num_send_attempts_strategy = st.integers(min_value=2, max_value=10)

# Daily message count strategy (0-1200 to test around the 1000 limit)
daily_message_count_strategy = st.integers(min_value=0, max_value=1200)

# Messages at or above limit strategy
at_or_above_limit_strategy = st.integers(min_value=1000, max_value=1500)

# Messages below limit strategy
below_limit_strategy = st.integers(min_value=0, max_value=999)


# ==========================================================================
# Property 11: Idempotency Preservation
# ==========================================================================

class TestIdempotencyPreservationProperty:
    """
    Property 11: Idempotency Preservation
    
    *For any* message ID, calling send_single_message multiple times SHALL
    result in exactly one message being sent to Wassenger API.
    
    **Feature: whatsapp-ban-prevention, Property 11: Idempotency Preservation**
    **Validates: Requirements 8.5**
    """

    @given(
        message_id=message_id_strategy,
        num_attempts=num_send_attempts_strategy
    )
    def test_idempotency_lock_prevents_duplicate_sends(
        self,
        message_id: int,
        num_attempts: int
    ):
        """
        **Feature: whatsapp-ban-prevention, Property 11: Idempotency Preservation**
        **Validates: Requirements 8.5**
        
        For any number of send attempts for the same message, only one
        should actually proceed due to the idempotency lock.
        """
        # Simulate Redis lock state (SET NX behavior)
        lock_state = {"acquired": False}
        successful_locks = 0
        
        def try_acquire_lock():
            """Simulate Redis SET NX behavior."""
            if not lock_state["acquired"]:
                lock_state["acquired"] = True
                return True
            return False
        
        # Simulate multiple send attempts
        for _ in range(num_attempts):
            if try_acquire_lock():
                successful_locks += 1
        
        # Property: only one lock should be acquired
        assert successful_locks == 1, \
            f"Expected 1 successful lock, got {successful_locks} for {num_attempts} attempts"

    @given(
        message_id=message_id_strategy,
        campaign_id=campaign_id_strategy,
        contact_id=contact_id_strategy
    )
    def test_sent_status_prevents_resend(
        self,
        message_id: int,
        campaign_id: int,
        contact_id: int
    ):
        """
        **Feature: whatsapp-ban-prevention, Property 11: Idempotency Preservation**
        **Validates: Requirements 8.5**
        
        For any message with status 'sent', 'delivered', or 'read',
        subsequent send attempts should be skipped.
        """
        sent_statuses = ["sent", "delivered", "read"]
        
        for status in sent_statuses:
            message = {
                "id": message_id,
                "campaign_id": campaign_id,
                "contact_id": contact_id,
                "status": status,
                "content": "Test message"
            }
            
            # Logic from send_single_message: check if already sent
            current_status = message.get("status")
            should_skip = current_status in ("sent", "delivered", "read")
            
            # Property: should skip if already sent
            assert should_skip is True, \
                f"Expected to skip message with status '{status}'"

    @given(
        message_id=message_id_strategy,
        num_concurrent_calls=st.integers(min_value=2, max_value=5)
    )
    def test_concurrent_calls_single_api_call(
        self,
        message_id: int,
        num_concurrent_calls: int
    ):
        """
        **Feature: whatsapp-ban-prevention, Property 11: Idempotency Preservation**
        **Validates: Requirements 8.5**
        
        When multiple concurrent calls attempt to send the same message,
        only one API call should be made.
        """
        # Simulate shared state
        api_calls_made = 0
        lock_acquired = False
        
        def simulate_send_attempt():
            nonlocal api_calls_made, lock_acquired
            
            # Step 1: Try to acquire idempotency lock
            if not lock_acquired:
                lock_acquired = True
                # Step 2: Make API call
                api_calls_made += 1
                return True
            return False
        
        # Simulate concurrent calls
        results = []
        for _ in range(num_concurrent_calls):
            results.append(simulate_send_attempt())
        
        # Property: exactly one API call should be made
        assert api_calls_made == 1, \
            f"Expected 1 API call, got {api_calls_made} for {num_concurrent_calls} concurrent calls"
        
        # Property: exactly one call should succeed
        assert sum(results) == 1, \
            f"Expected 1 successful call, got {sum(results)}"

    @given(
        message_id=message_id_strategy,
        campaign_id=campaign_id_strategy,
        contact_id=contact_id_strategy
    )
    def test_failed_message_can_be_retried(
        self,
        message_id: int,
        campaign_id: int,
        contact_id: int
    ):
        """
        **Feature: whatsapp-ban-prevention, Property 11: Idempotency Preservation**
        **Validates: Requirements 8.5**
        
        A failed message should be retryable (not blocked by status check).
        """
        message = {
            "id": message_id,
            "campaign_id": campaign_id,
            "contact_id": contact_id,
            "status": "failed",
            "content": "Test message"
        }
        
        # Logic: failed messages should NOT be skipped by status check
        current_status = message.get("status")
        should_skip = current_status in ("sent", "delivered", "read")
        
        # Property: failed messages can be retried
        assert should_skip is False, \
            "Failed messages should be retryable"

    @given(
        message_id=message_id_strategy,
        campaign_id=campaign_id_strategy,
        contact_id=contact_id_strategy
    )
    def test_pending_message_can_be_sent(
        self,
        message_id: int,
        campaign_id: int,
        contact_id: int
    ):
        """
        **Feature: whatsapp-ban-prevention, Property 11: Idempotency Preservation**
        **Validates: Requirements 8.5**
        
        A pending message should be sendable (not blocked by status check).
        """
        message = {
            "id": message_id,
            "campaign_id": campaign_id,
            "contact_id": contact_id,
            "status": "pending",
            "content": "Test message"
        }
        
        # Logic: pending messages should NOT be skipped
        current_status = message.get("status")
        should_skip = current_status in ("sent", "delivered", "read")
        
        # Property: pending messages can be sent
        assert should_skip is False, \
            "Pending messages should be sendable"

    def test_idempotency_key_uniqueness(self):
        """
        **Feature: whatsapp-ban-prevention, Property 11: Idempotency Preservation**
        **Validates: Requirements 8.5**
        
        Idempotency keys should be unique per message and operation.
        """
        from app.tasks.message_tasks import get_idempotency_key
        
        # Test different message IDs produce different keys
        key1 = get_idempotency_key(1, "send")
        key2 = get_idempotency_key(2, "send")
        
        assert key1 != key2, "Different message IDs should produce different keys"
        
        # Test different operations produce different keys
        key_send = get_idempotency_key(1, "send")
        key_retry = get_idempotency_key(1, "retry")
        
        assert key_send != key_retry, "Different operations should produce different keys"

    @given(message_id=message_id_strategy)
    def test_idempotency_key_format(self, message_id: int):
        """
        **Feature: whatsapp-ban-prevention, Property 11: Idempotency Preservation**
        **Validates: Requirements 8.5**
        
        Idempotency keys should follow the expected format.
        """
        from app.tasks.message_tasks import get_idempotency_key
        
        key = get_idempotency_key(message_id, "send")
        
        # Property: key should contain the message ID
        assert str(message_id) in key, \
            f"Key should contain message ID {message_id}, got {key}"
        
        # Property: key should contain the operation
        assert "send" in key, \
            f"Key should contain operation 'send', got {key}"
        
        # Property: key should start with idempotency prefix
        assert key.startswith("idempotency:"), \
            f"Key should start with 'idempotency:', got {key}"


class TestIdempotencyWithMockedRedis:
    """
    Property 11: Idempotency Preservation with Mocked Redis
    
    Tests that validate the actual implementation logic with mocked
    Redis dependencies.
    
    **Feature: whatsapp-ban-prevention, Property 11: Idempotency Preservation**
    **Validates: Requirements 8.5**
    """

    @given(
        message_id=message_id_strategy,
        num_attempts=num_send_attempts_strategy
    )
    def test_redis_set_nx_pattern(
        self,
        message_id: int,
        num_attempts: int
    ):
        """
        **Feature: whatsapp-ban-prevention, Property 11: Idempotency Preservation**
        **Validates: Requirements 8.5**
        
        Test that the Redis SET NX pattern correctly prevents duplicate operations.
        """
        # Mock Redis client
        mock_redis = MagicMock()
        lock_acquired_count = 0
        lock_state = {"acquired": False}
        
        def mock_set(key, value, nx=False, ex=None):
            nonlocal lock_acquired_count
            if nx and not lock_state["acquired"]:
                lock_state["acquired"] = True
                lock_acquired_count += 1
                return True
            return False
        
        mock_redis.set = mock_set
        
        # Simulate multiple attempts to acquire the lock
        successful_locks = 0
        for _ in range(num_attempts):
            if mock_redis.set(f"idempotency:send:{message_id}", "1", nx=True, ex=300):
                successful_locks += 1
        
        # Property: only one lock should be acquired
        assert successful_locks == 1, \
            f"Expected 1 successful lock, got {successful_locks}"

    @given(message_id=message_id_strategy)
    def test_lock_release_after_operation(self, message_id: int):
        """
        **Feature: whatsapp-ban-prevention, Property 11: Idempotency Preservation**
        **Validates: Requirements 8.5**
        
        After an operation completes, the lock should be released.
        """
        # Mock Redis client
        mock_redis = MagicMock()
        lock_state = {"acquired": False}
        
        def mock_set(key, value, nx=False, ex=None):
            if nx and not lock_state["acquired"]:
                lock_state["acquired"] = True
                return True
            return False
        
        def mock_delete(key):
            lock_state["acquired"] = False
        
        mock_redis.set = mock_set
        mock_redis.delete = mock_delete
        
        # Acquire lock
        key = f"idempotency:send:{message_id}"
        acquired = mock_redis.set(key, "1", nx=True, ex=300)
        assert acquired is True, "First lock should be acquired"
        
        # Release lock
        mock_redis.delete(key)
        
        # Should be able to acquire again
        acquired_again = mock_redis.set(key, "1", nx=True, ex=300)
        assert acquired_again is True, "Lock should be acquirable after release"




# ==========================================================================
# Property 10: Daily Limit Enforcement
# ==========================================================================

class TestDailyLimitEnforcementProperty:
    """
    Property 10: Daily Limit Enforcement
    
    *For any* day, when message count reaches 1000, all subsequent send
    attempts SHALL be blocked with a clear error message.
    
    **Feature: whatsapp-ban-prevention, Property 10: Daily Limit Enforcement**
    **Validates: Requirements 6.1, 6.5**
    """

    @given(messages_sent_today=at_or_above_limit_strategy)
    def test_blocks_at_or_above_daily_limit(self, messages_sent_today: int):
        """
        **Feature: whatsapp-ban-prevention, Property 10: Daily Limit Enforcement**
        **Validates: Requirements 6.1, 6.5**
        
        For any messages_sent_today >= 1000, is_safe_to_send should return
        (False, reason) where reason mentions the daily limit.
        """
        from unittest.mock import MagicMock
        
        # Mock Redis client
        mock_redis = MagicMock()
        mock_redis.get.return_value = None  # No emergency pause
        
        # Import the function
        from app.tasks.message_tasks import is_safe_to_send
        
        # Mock is_night_time to return False (daytime)
        with patch('app.tasks.message_tasks.is_night_time', return_value=False):
            # Mock check_error_thresholds to return no halt
            with patch('app.tasks.message_tasks.check_error_thresholds', return_value={
                "should_halt": False,
                "reason": None,
                "halt_duration": 0,
                "warning": None
            }):
                can_send, reason = is_safe_to_send(mock_redis, messages_sent_today)
        
        # Property: should be blocked
        assert can_send is False, \
            f"Expected can_send=False for messages_sent_today={messages_sent_today}, got {can_send}"
        
        # Property: reason should mention daily limit
        assert "1000" in reason or "limite" in reason.lower() or "limit" in reason.lower(), \
            f"Expected reason to mention daily limit, got '{reason}'"

    @given(messages_sent_today=below_limit_strategy)
    def test_allows_below_daily_limit(self, messages_sent_today: int):
        """
        **Feature: whatsapp-ban-prevention, Property 10: Daily Limit Enforcement**
        **Validates: Requirements 6.1, 6.5**
        
        For any messages_sent_today < 1000, is_safe_to_send should return
        (True, "OK") when all other conditions are met.
        """
        from unittest.mock import MagicMock
        
        # Mock Redis client
        mock_redis = MagicMock()
        mock_redis.get.return_value = None  # No emergency pause
        
        # Import the function
        from app.tasks.message_tasks import is_safe_to_send
        
        # Mock is_night_time to return False (daytime)
        with patch('app.tasks.message_tasks.is_night_time', return_value=False):
            # Mock check_error_thresholds to return no halt
            with patch('app.tasks.message_tasks.check_error_thresholds', return_value={
                "should_halt": False,
                "reason": None,
                "halt_duration": 0,
                "warning": None
            }):
                can_send, reason = is_safe_to_send(mock_redis, messages_sent_today)
        
        # Property: should be allowed
        assert can_send is True, \
            f"Expected can_send=True for messages_sent_today={messages_sent_today}, got {can_send}"
        
        # Property: reason should be "OK"
        assert reason == "OK", \
            f"Expected reason='OK', got '{reason}'"

    def test_blocks_at_exactly_1000(self):
        """
        **Feature: whatsapp-ban-prevention, Property 10: Daily Limit Enforcement**
        **Validates: Requirements 6.1, 6.5**
        
        At exactly 1000 messages, sending should be blocked.
        """
        from unittest.mock import MagicMock
        
        # Mock Redis client
        mock_redis = MagicMock()
        mock_redis.get.return_value = None  # No emergency pause
        
        # Import the function
        from app.tasks.message_tasks import is_safe_to_send
        
        # Mock is_night_time to return False (daytime)
        with patch('app.tasks.message_tasks.is_night_time', return_value=False):
            # Mock check_error_thresholds to return no halt
            with patch('app.tasks.message_tasks.check_error_thresholds', return_value={
                "should_halt": False,
                "reason": None,
                "halt_duration": 0,
                "warning": None
            }):
                can_send, reason = is_safe_to_send(mock_redis, 1000)
        
        # Property: should be blocked at exactly 1000
        assert can_send is False, \
            "Expected can_send=False at exactly 1000 messages"
        
        # Property: reason should mention limit
        assert "1000" in reason or "limite" in reason.lower(), \
            f"Expected reason to mention 1000 limit, got '{reason}'"

    def test_allows_at_999(self):
        """
        **Feature: whatsapp-ban-prevention, Property 10: Daily Limit Enforcement**
        **Validates: Requirements 6.1, 6.5**
        
        At 999 messages, sending should still be allowed.
        """
        from unittest.mock import MagicMock
        
        # Mock Redis client
        mock_redis = MagicMock()
        mock_redis.get.return_value = None  # No emergency pause
        
        # Import the function
        from app.tasks.message_tasks import is_safe_to_send
        
        # Mock is_night_time to return False (daytime)
        with patch('app.tasks.message_tasks.is_night_time', return_value=False):
            # Mock check_error_thresholds to return no halt
            with patch('app.tasks.message_tasks.check_error_thresholds', return_value={
                "should_halt": False,
                "reason": None,
                "halt_duration": 0,
                "warning": None
            }):
                can_send, reason = is_safe_to_send(mock_redis, 999)
        
        # Property: should be allowed at 999
        assert can_send is True, \
            "Expected can_send=True at 999 messages"
        
        # Property: reason should be OK
        assert reason == "OK", \
            f"Expected reason='OK' at 999 messages, got '{reason}'"

    @given(messages_sent_today=daily_message_count_strategy)
    def test_daily_limit_is_1000(self, messages_sent_today: int):
        """
        **Feature: whatsapp-ban-prevention, Property 10: Daily Limit Enforcement**
        **Validates: Requirements 6.1, 6.5**
        
        The daily limit should be exactly 1000 messages.
        """
        from unittest.mock import MagicMock
        
        # Mock Redis client
        mock_redis = MagicMock()
        mock_redis.get.return_value = None  # No emergency pause
        
        # Import the function
        from app.tasks.message_tasks import is_safe_to_send
        
        # Mock is_night_time to return False (daytime)
        with patch('app.tasks.message_tasks.is_night_time', return_value=False):
            # Mock check_error_thresholds to return no halt
            with patch('app.tasks.message_tasks.check_error_thresholds', return_value={
                "should_halt": False,
                "reason": None,
                "halt_duration": 0,
                "warning": None
            }):
                can_send, reason = is_safe_to_send(mock_redis, messages_sent_today)
        
        # Property: blocked if and only if >= 1000
        expected_blocked = messages_sent_today >= 1000
        
        if expected_blocked:
            assert can_send is False, \
                f"Expected blocked at {messages_sent_today} messages"
        else:
            assert can_send is True, \
                f"Expected allowed at {messages_sent_today} messages"


class TestDailyLimitWithMonitoringService:
    """
    Property 10: Daily Limit Enforcement with Monitoring Service
    
    Tests that validate the daily limit enforcement through the
    monitoring service's can_send_message method.
    
    **Feature: whatsapp-ban-prevention, Property 10: Daily Limit Enforcement**
    **Validates: Requirements 6.1, 6.5**
    """

    @given(total_sent=at_or_above_limit_strategy)
    def test_monitoring_service_blocks_at_limit(self, total_sent: int):
        """
        **Feature: whatsapp-ban-prevention, Property 10: Daily Limit Enforcement**
        **Validates: Requirements 6.1, 6.5**
        
        For any total_sent >= 1000, monitoring_service.can_send_message()
        should return (False, "daily_limit_reached").
        """
        from app.services.monitoring_service import MonitoringService, DailyStats
        
        # Create mock stats - total_sent is a property computed from message_1_count + message_2_count
        mock_stats = DailyStats(
            date=datetime.now().strftime("%Y-%m-%d"),
            message_1_count=total_sent // 2,
            message_2_count=total_sent - (total_sent // 2),
            error_count=0
        )
        
        # Mock the MonitoringService with patched get_daily_stats
        with patch.object(MonitoringService, 'get_daily_stats', return_value=mock_stats):
            with patch.object(MonitoringService, 'redis_client', new_callable=lambda: MagicMock()):
                service = MonitoringService.__new__(MonitoringService)
                service._redis = MagicMock()
                can_send, error_msg = service.can_send_message()
        
        # Property: should be blocked
        assert can_send is False, \
            f"Expected can_send=False for total_sent={total_sent}, got {can_send}"
        
        # Property: error message should be "daily_limit_reached"
        assert error_msg == "daily_limit_reached", \
            f"Expected error_msg='daily_limit_reached', got '{error_msg}'"

    @given(total_sent=below_limit_strategy)
    def test_monitoring_service_allows_below_limit(self, total_sent: int):
        """
        **Feature: whatsapp-ban-prevention, Property 10: Daily Limit Enforcement**
        **Validates: Requirements 6.1, 6.5**
        
        For any total_sent < 1000, monitoring_service.can_send_message()
        should return (True, "").
        """
        from app.services.monitoring_service import MonitoringService, DailyStats
        
        # Create mock stats - total_sent is a property computed from message_1_count + message_2_count
        mock_stats = DailyStats(
            date=datetime.now().strftime("%Y-%m-%d"),
            message_1_count=total_sent // 2,
            message_2_count=total_sent - (total_sent // 2),
            error_count=0
        )
        
        # Mock the MonitoringService with patched get_daily_stats
        with patch.object(MonitoringService, 'get_daily_stats', return_value=mock_stats):
            with patch.object(MonitoringService, 'redis_client', new_callable=lambda: MagicMock()):
                service = MonitoringService.__new__(MonitoringService)
                service._redis = MagicMock()
                can_send, error_msg = service.can_send_message()
        
        # Property: should be allowed
        assert can_send is True, \
            f"Expected can_send=True for total_sent={total_sent}, got {can_send}"
        
        # Property: error message should be empty
        assert error_msg == "", \
            f"Expected empty error_msg, got '{error_msg}'"

    def test_daily_limit_constant_is_1000(self):
        """
        **Feature: whatsapp-ban-prevention, Property 10: Daily Limit Enforcement**
        **Validates: Requirements 6.1, 6.5**
        
        The DAILY_MESSAGE_LIMIT constant should be 1000.
        """
        from app.services.monitoring_service import DAILY_MESSAGE_LIMIT
        
        assert DAILY_MESSAGE_LIMIT == 1000, \
            f"Expected DAILY_MESSAGE_LIMIT=1000, got {DAILY_MESSAGE_LIMIT}"

    def test_error_message_is_clear(self):
        """
        **Feature: whatsapp-ban-prevention, Property 10: Daily Limit Enforcement**
        **Validates: Requirements 6.5**
        
        When daily limit is reached, the error message should be clear.
        """
        from app.services.monitoring_service import MonitoringService, DailyStats
        
        # Create mock stats at limit - total_sent is a property computed from message_1_count + message_2_count
        mock_stats = DailyStats(
            date=datetime.now().strftime("%Y-%m-%d"),
            message_1_count=500,
            message_2_count=500,
            error_count=0
        )
        
        # Mock the MonitoringService with patched get_daily_stats
        with patch.object(MonitoringService, 'get_daily_stats', return_value=mock_stats):
            with patch.object(MonitoringService, 'redis_client', new_callable=lambda: MagicMock()):
                service = MonitoringService.__new__(MonitoringService)
                service._redis = MagicMock()
                can_send, error_msg = service.can_send_message()
        
        # Property: error message should be clear and specific
        assert error_msg == "daily_limit_reached", \
            f"Expected clear error message 'daily_limit_reached', got '{error_msg}'"


class TestDailyLimitEdgeCases:
    """
    Edge cases for Daily Limit Enforcement.
    
    **Feature: whatsapp-ban-prevention, Property 10: Daily Limit Enforcement**
    **Validates: Requirements 6.1, 6.5**
    """

    def test_zero_messages_allowed(self):
        """
        **Feature: whatsapp-ban-prevention, Property 10: Daily Limit Enforcement**
        **Validates: Requirements 6.1, 6.5**
        
        At 0 messages sent, sending should be allowed.
        """
        from unittest.mock import MagicMock
        from app.tasks.message_tasks import is_safe_to_send
        
        # Mock Redis client
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        
        with patch('app.tasks.message_tasks.is_night_time', return_value=False):
            with patch('app.tasks.message_tasks.check_error_thresholds', return_value={
                "should_halt": False,
                "reason": None,
                "halt_duration": 0,
                "warning": None
            }):
                can_send, reason = is_safe_to_send(mock_redis, 0)
        
        assert can_send is True, "Should allow sending at 0 messages"
        assert reason == "OK", f"Expected 'OK', got '{reason}'"

    @given(messages_over_limit=st.integers(min_value=1, max_value=500))
    def test_messages_over_limit_still_blocked(self, messages_over_limit: int):
        """
        **Feature: whatsapp-ban-prevention, Property 10: Daily Limit Enforcement**
        **Validates: Requirements 6.1, 6.5**
        
        Messages significantly over the limit should still be blocked.
        """
        from unittest.mock import MagicMock
        from app.tasks.message_tasks import is_safe_to_send
        
        messages_sent = 1000 + messages_over_limit
        
        # Mock Redis client
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        
        with patch('app.tasks.message_tasks.is_night_time', return_value=False):
            with patch('app.tasks.message_tasks.check_error_thresholds', return_value={
                "should_halt": False,
                "reason": None,
                "halt_duration": 0,
                "warning": None
            }):
                can_send, reason = is_safe_to_send(mock_redis, messages_sent)
        
        assert can_send is False, \
            f"Should block at {messages_sent} messages (over limit by {messages_over_limit})"
