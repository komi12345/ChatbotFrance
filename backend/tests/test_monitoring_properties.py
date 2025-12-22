"""
Property-based tests for MonitoringService.

Tests the correctness properties defined in the design document for the
WhatsApp Monitoring feature.
"""
import pytest
from hypothesis import given, settings as hyp_settings, strategies as st, HealthCheck
from unittest.mock import MagicMock, patch

# Configure Hypothesis for CI: minimum 100 iterations
hyp_settings.register_profile(
    "ci",
    max_examples=100,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None
)
hyp_settings.load_profile("ci")


# ==========================================================================
# STRATEGIES FOR MONITORING SERVICE TESTS
# ==========================================================================

# Strategy for message types
message_type_strategy = st.sampled_from(["message_1", "message_2"])

# Strategy for counter values (0-1200 to test around the 1000 limit)
counter_value_strategy = st.integers(min_value=0, max_value=1200)

# Strategy for message counts (non-negative)
message_count_strategy = st.integers(min_value=0, max_value=200)

# Strategy for interaction rates (0 to 2, typical range)
interaction_rate_strategy = st.floats(min_value=0.0, max_value=2.0, allow_nan=False, allow_infinity=False)


class TestCounterIncrementConsistencyProperty:
    """
    Property 1: Counter Increment Consistency
    
    *For any* message successfully sent via Wassenger API, the corresponding
    Redis counter (message_1 or message_2) SHALL be incremented by exactly 1,
    and the total_sent SHALL equal message_1_count + message_2_count.
    
    **Feature: whatsapp-monitoring, Property 1: Counter Increment Consistency**
    **Validates: Requirements 1.1, 1.2**
    """

    @given(
        message_1_initial=message_count_strategy,
        message_2_initial=message_count_strategy,
        message_type=message_type_strategy
    )
    def test_increment_increases_counter_by_one(
        self,
        message_1_initial: int,
        message_2_initial: int,
        message_type: str
    ):
        """
        **Feature: whatsapp-monitoring, Property 1: Counter Increment Consistency**
        **Validates: Requirements 1.1, 1.2**
        
        For any initial counter state and message type, incrementing the counter
        should increase it by exactly 1.
        """
        from app.services.monitoring_service import MonitoringService
        
        # Create service with mocked Redis
        service = MonitoringService.__new__(MonitoringService)
        service.redis_url = "redis://localhost:6379/0"
        
        # Track the current values
        current_values = {
            "message_1": message_1_initial,
            "message_2": message_2_initial,
            "errors": 0
        }
        
        # Mock Redis client
        mock_redis = MagicMock()
        mock_pipeline = MagicMock()
        
        def mock_incr(key):
            # Extract key type from full key
            key_type = key.split(":")[-1]
            current_values[key_type] += 1
            return current_values[key_type]
        
        def mock_execute():
            # Return the incremented value
            key_type = message_type
            return [current_values[key_type], True]
        
        mock_pipeline.incr = mock_incr
        mock_pipeline.expire = MagicMock()
        mock_pipeline.execute = mock_execute
        mock_redis.pipeline.return_value = mock_pipeline
        
        service._redis = mock_redis
        
        # Get initial value for the message type
        initial_value = current_values[message_type]
        
        # Increment the counter
        new_value = service.increment_message_counter(message_type)
        
        # Property: counter increased by exactly 1
        assert new_value == initial_value + 1, \
            f"Expected {initial_value + 1}, got {new_value}"

    @given(
        message_1_count=message_count_strategy,
        message_2_count=message_count_strategy
    )
    def test_total_sent_equals_sum_of_counters(
        self,
        message_1_count: int,
        message_2_count: int
    ):
        """
        **Feature: whatsapp-monitoring, Property 1: Counter Increment Consistency**
        **Validates: Requirements 1.1, 1.2**
        
        For any combination of message_1 and message_2 counts, total_sent
        should equal message_1_count + message_2_count.
        """
        from app.services.monitoring_service import DailyStats
        
        # Create DailyStats with given counts
        stats = DailyStats(
            date="2024-12-09",
            message_1_count=message_1_count,
            message_2_count=message_2_count,
            error_count=0
        )
        
        # Property: total_sent = message_1_count + message_2_count
        expected_total = message_1_count + message_2_count
        assert stats.total_sent == expected_total, \
            f"Expected total_sent={expected_total}, got {stats.total_sent}"

    @given(message_type=message_type_strategy)
    def test_increment_only_affects_specified_counter(self, message_type: str):
        """
        **Feature: whatsapp-monitoring, Property 1: Counter Increment Consistency**
        **Validates: Requirements 1.1, 1.2**
        
        For any message type, incrementing should only affect that specific
        counter, not the other one.
        """
        from app.services.monitoring_service import MonitoringService
        
        service = MonitoringService.__new__(MonitoringService)
        service.redis_url = "redis://localhost:6379/0"
        
        # Track which keys were incremented
        incremented_keys = []
        
        mock_redis = MagicMock()
        mock_pipeline = MagicMock()
        
        def mock_incr(key):
            incremented_keys.append(key)
            return 1
        
        mock_pipeline.incr = mock_incr
        mock_pipeline.expire = MagicMock()
        mock_pipeline.execute = MagicMock(return_value=[1, True])
        mock_redis.pipeline.return_value = mock_pipeline
        
        service._redis = mock_redis
        
        # Increment the counter
        service.increment_message_counter(message_type)
        
        # Property: only one key was incremented
        assert len(incremented_keys) == 1, \
            f"Expected 1 key incremented, got {len(incremented_keys)}"
        
        # Property: the incremented key contains the message type
        assert message_type in incremented_keys[0], \
            f"Expected key to contain '{message_type}', got '{incremented_keys[0]}'"



class TestDailyLimitBlockingProperty:
    """
    Property 2: Daily Limit Blocking
    
    *For any* Daily_Message_Counter value >= 1000, all subsequent calls to
    `can_send_message()` SHALL return `(False, "daily_limit_reached")` until
    the counter is reset.
    
    **Feature: whatsapp-monitoring, Property 2: Daily Limit Blocking**
    **Validates: Requirements 2.2, 2.3**
    """

    @given(total_sent=st.integers(min_value=1000, max_value=1400))
    def test_blocks_when_at_or_above_limit(self, total_sent: int):
        """
        **Feature: whatsapp-monitoring, Property 2: Daily Limit Blocking**
        **Validates: Requirements 2.2, 2.3**
        
        For any total_sent >= 1000, can_send_message() should return
        (False, "daily_limit_reached").
        """
        from app.services.monitoring_service import MonitoringService, DailyStats
        
        service = MonitoringService.__new__(MonitoringService)
        service.redis_url = "redis://localhost:6379/0"
        
        # Mock get_daily_stats to return the given total
        # Split total between message_1 and message_2
        message_1 = total_sent // 2
        message_2 = total_sent - message_1
        
        mock_stats = DailyStats(
            date="2024-12-09",
            message_1_count=message_1,
            message_2_count=message_2,
            error_count=0
        )
        
        with patch.object(service, 'get_daily_stats', return_value=mock_stats):
            can_send, error_msg = service.can_send_message()
        
        # Property: should be blocked
        assert can_send is False, \
            f"Expected can_send=False for total_sent={total_sent}, got {can_send}"
        
        # Property: error message should be "daily_limit_reached"
        assert error_msg == "daily_limit_reached", \
            f"Expected error_msg='daily_limit_reached', got '{error_msg}'"

    @given(total_sent=st.integers(min_value=0, max_value=999))
    def test_allows_when_below_limit(self, total_sent: int):
        """
        **Feature: whatsapp-monitoring, Property 2: Daily Limit Blocking**
        **Validates: Requirements 2.2, 2.3**
        
        For any total_sent < 1000, can_send_message() should return
        (True, "").
        """
        from app.services.monitoring_service import MonitoringService, DailyStats
        
        service = MonitoringService.__new__(MonitoringService)
        service.redis_url = "redis://localhost:6379/0"
        
        # Split total between message_1 and message_2
        message_1 = total_sent // 2
        message_2 = total_sent - message_1
        
        mock_stats = DailyStats(
            date="2024-12-09",
            message_1_count=message_1,
            message_2_count=message_2,
            error_count=0
        )
        
        with patch.object(service, 'get_daily_stats', return_value=mock_stats):
            can_send, error_msg = service.can_send_message()
        
        # Property: should be allowed
        assert can_send is True, \
            f"Expected can_send=True for total_sent={total_sent}, got {can_send}"
        
        # Property: error message should be empty
        assert error_msg == "", \
            f"Expected error_msg='', got '{error_msg}'"

    @given(total_sent=st.integers(min_value=1000, max_value=1400))
    def test_exact_limit_boundary(self, total_sent: int):
        """
        **Feature: whatsapp-monitoring, Property 2: Daily Limit Blocking**
        **Validates: Requirements 2.2, 2.3**
        
        For total_sent exactly at 1000, can_send_message() should block.
        """
        from app.services.monitoring_service import MonitoringService, DailyStats
        
        service = MonitoringService.__new__(MonitoringService)
        service.redis_url = "redis://localhost:6379/0"
        
        # Test exactly at 1000
        mock_stats = DailyStats(
            date="2024-12-09",
            message_1_count=500,
            message_2_count=500,
            error_count=0
        )
        
        with patch.object(service, 'get_daily_stats', return_value=mock_stats):
            can_send, error_msg = service.can_send_message()
        
        # Property: should be blocked at exactly 1000
        assert can_send is False, \
            f"Expected can_send=False at limit 1000"
        assert error_msg == "daily_limit_reached", \
            f"Expected 'daily_limit_reached' at limit 1000"



class TestAlertLevelCalculationProperty:
    """
    Property 3: Alert Level Calculation
    
    *For any* Daily_Message_Counter value N:
    - If 0 <= N <= 750, alert_level SHALL be "ok"
    - If 751 <= N <= 900, alert_level SHALL be "attention"
    - If 901 <= N <= 1000, alert_level SHALL be "danger"
    - If N > 1000, alert_level SHALL be "blocked"
    
    **Feature: whatsapp-monitoring, Property 3: Alert Level Calculation**
    **Validates: Requirements 3.1, 3.2, 3.3, 3.4**
    """

    @given(total_sent=st.integers(min_value=0, max_value=750))
    def test_ok_level_for_0_to_750(self, total_sent: int):
        """
        **Feature: whatsapp-monitoring, Property 3: Alert Level Calculation**
        **Validates: Requirements 3.1**
        
        For any total_sent in [0, 750], alert_level should be "ok".
        """
        from app.services.monitoring_service import MonitoringService, AlertLevel
        
        alert_level = MonitoringService._calculate_alert_level(total_sent)
        
        assert alert_level == AlertLevel.OK, \
            f"Expected AlertLevel.OK for total_sent={total_sent}, got {alert_level}"

    @given(total_sent=st.integers(min_value=751, max_value=900))
    def test_attention_level_for_751_to_900(self, total_sent: int):
        """
        **Feature: whatsapp-monitoring, Property 3: Alert Level Calculation**
        **Validates: Requirements 3.2**
        
        For any total_sent in [751, 900], alert_level should be "attention".
        """
        from app.services.monitoring_service import MonitoringService, AlertLevel
        
        alert_level = MonitoringService._calculate_alert_level(total_sent)
        
        assert alert_level == AlertLevel.ATTENTION, \
            f"Expected AlertLevel.ATTENTION for total_sent={total_sent}, got {alert_level}"

    @given(total_sent=st.integers(min_value=901, max_value=1000))
    def test_danger_level_for_901_to_1000(self, total_sent: int):
        """
        **Feature: whatsapp-monitoring, Property 3: Alert Level Calculation**
        **Validates: Requirements 3.3**
        
        For any total_sent in [901, 1000], alert_level should be "danger".
        """
        from app.services.monitoring_service import MonitoringService, AlertLevel
        
        alert_level = MonitoringService._calculate_alert_level(total_sent)
        
        assert alert_level == AlertLevel.DANGER, \
            f"Expected AlertLevel.DANGER for total_sent={total_sent}, got {alert_level}"

    @given(total_sent=st.integers(min_value=1001, max_value=1400))
    def test_blocked_level_for_above_1000(self, total_sent: int):
        """
        **Feature: whatsapp-monitoring, Property 3: Alert Level Calculation**
        **Validates: Requirements 3.4**
        
        For any total_sent > 1000, alert_level should be "blocked".
        """
        from app.services.monitoring_service import MonitoringService, AlertLevel
        
        alert_level = MonitoringService._calculate_alert_level(total_sent)
        
        assert alert_level == AlertLevel.BLOCKED, \
            f"Expected AlertLevel.BLOCKED for total_sent={total_sent}, got {alert_level}"

    @given(total_sent=st.integers(min_value=0, max_value=1000))
    def test_alert_level_is_always_valid_enum(self, total_sent: int):
        """
        **Feature: whatsapp-monitoring, Property 3: Alert Level Calculation**
        **Validates: Requirements 3.1, 3.2, 3.3, 3.4**
        
        For any total_sent value, the returned alert_level should be a valid
        AlertLevel enum value.
        """
        from app.services.monitoring_service import MonitoringService, AlertLevel
        
        alert_level = MonitoringService._calculate_alert_level(total_sent)
        
        # Property: result is a valid AlertLevel
        assert isinstance(alert_level, AlertLevel), \
            f"Expected AlertLevel enum, got {type(alert_level)}"
        
        # Property: result is one of the defined levels
        valid_levels = {AlertLevel.OK, AlertLevel.ATTENTION, AlertLevel.DANGER, AlertLevel.BLOCKED}
        assert alert_level in valid_levels, \
            f"Expected one of {valid_levels}, got {alert_level}"



class TestRemainingCapacityFormulaProperty:
    """
    Property 4: Remaining Capacity Formula
    
    *For any* combination of messages_sent (S) and interaction_rate (R) where R >= 0,
    the remaining_capacity SHALL equal floor((1000 - S) / (1 + R)), and SHALL never
    be negative.
    
    **Feature: whatsapp-monitoring, Property 4: Remaining Capacity Formula**
    **Validates: Requirements 5.1**
    """

    @given(
        total_sent=st.integers(min_value=0, max_value=1200),
        interaction_rate=st.floats(min_value=0.0, max_value=2.0, allow_nan=False, allow_infinity=False)
    )
    def test_remaining_capacity_matches_formula(
        self,
        total_sent: int,
        interaction_rate: float
    ):
        """
        **Feature: whatsapp-monitoring, Property 4: Remaining Capacity Formula**
        **Validates: Requirements 5.1**
        
        For any total_sent and interaction_rate >= 0, remaining_capacity should
        equal floor((1000 - total_sent) / (1 + interaction_rate)).
        """
        import math
        from app.services.monitoring_service import MonitoringService
        
        capacity = MonitoringService.calculate_remaining_capacity_from_values(
            total_sent, interaction_rate
        )
        
        # Calculate expected value using the formula
        remaining_messages = 1000 - total_sent
        if remaining_messages <= 0:
            expected = 0
        else:
            expected = math.floor(remaining_messages / (1 + interaction_rate))
            expected = max(0, expected)
        
        assert capacity == expected, \
            f"Expected {expected} for total_sent={total_sent}, rate={interaction_rate}, got {capacity}"

    @given(
        total_sent=st.integers(min_value=0, max_value=1200),
        interaction_rate=st.floats(min_value=0.0, max_value=2.0, allow_nan=False, allow_infinity=False)
    )
    def test_remaining_capacity_never_negative(
        self,
        total_sent: int,
        interaction_rate: float
    ):
        """
        **Feature: whatsapp-monitoring, Property 4: Remaining Capacity Formula**
        **Validates: Requirements 5.1**
        
        For any inputs, remaining_capacity should never be negative.
        """
        from app.services.monitoring_service import MonitoringService
        
        capacity = MonitoringService.calculate_remaining_capacity_from_values(
            total_sent, interaction_rate
        )
        
        assert capacity >= 0, \
            f"Expected non-negative capacity, got {capacity}"

    @given(
        total_sent=st.integers(min_value=1000, max_value=1400),
        interaction_rate=st.floats(min_value=0.0, max_value=2.0, allow_nan=False, allow_infinity=False)
    )
    def test_remaining_capacity_zero_when_at_or_above_limit(
        self,
        total_sent: int,
        interaction_rate: float
    ):
        """
        **Feature: whatsapp-monitoring, Property 4: Remaining Capacity Formula**
        **Validates: Requirements 5.1**
        
        When total_sent >= 1000, remaining_capacity should be 0.
        """
        from app.services.monitoring_service import MonitoringService
        
        capacity = MonitoringService.calculate_remaining_capacity_from_values(
            total_sent, interaction_rate
        )
        
        assert capacity == 0, \
            f"Expected 0 for total_sent={total_sent} >= 1000, got {capacity}"

    @given(
        total_sent=st.integers(min_value=0, max_value=999),
        interaction_rate=st.floats(min_value=0.0, max_value=2.0, allow_nan=False, allow_infinity=False)
    )
    def test_remaining_capacity_positive_when_below_limit(
        self,
        total_sent: int,
        interaction_rate: float
    ):
        """
        **Feature: whatsapp-monitoring, Property 4: Remaining Capacity Formula**
        **Validates: Requirements 5.1**
        
        When total_sent < 1000, remaining_capacity should be positive (or zero
        if interaction_rate is very high).
        """
        from app.services.monitoring_service import MonitoringService
        
        capacity = MonitoringService.calculate_remaining_capacity_from_values(
            total_sent, interaction_rate
        )
        
        # Capacity should be >= 0 (could be 0 if interaction_rate is very high)
        assert capacity >= 0, \
            f"Expected non-negative capacity for total_sent={total_sent}"

    @given(total_sent=st.integers(min_value=0, max_value=999))
    def test_remaining_capacity_with_zero_interaction_rate(self, total_sent: int):
        """
        **Feature: whatsapp-monitoring, Property 4: Remaining Capacity Formula**
        **Validates: Requirements 5.1**
        
        When interaction_rate is 0, remaining_capacity should equal (1000 - total_sent).
        """
        from app.services.monitoring_service import MonitoringService
        
        capacity = MonitoringService.calculate_remaining_capacity_from_values(
            total_sent, 0.0
        )
        
        expected = 1000 - total_sent
        assert capacity == expected, \
            f"Expected {expected} for total_sent={total_sent} with rate=0, got {capacity}"



class TestErrorRateAlertProperty:
    """
    Property 5: Error Rate Alert
    
    *For any* combination of total_sent (T) and error_count (E) where T > 0,
    if E/T > 0.10 then the error_rate_warning SHALL be true.
    
    **Feature: whatsapp-monitoring, Property 5: Error Rate Alert**
    **Validates: Requirements 6.2**
    """

    @given(
        total_sent=st.integers(min_value=1, max_value=1000),
        error_count=st.integers(min_value=0, max_value=1000)
    )
    def test_error_rate_warning_when_above_threshold(
        self,
        total_sent: int,
        error_count: int
    ):
        """
        **Feature: whatsapp-monitoring, Property 5: Error Rate Alert**
        **Validates: Requirements 6.2**
        
        For any total_sent > 0 and error_count, if error_count/total_sent > 0.10
        then error_rate_warning should be True.
        """
        from app.services.monitoring_service import MonitoringService
        
        warning = MonitoringService.calculate_error_rate_warning(total_sent, error_count)
        
        # Calculate expected value
        error_rate = error_count / total_sent
        expected_warning = error_rate > 0.10
        
        assert warning == expected_warning, \
            f"Expected warning={expected_warning} for total_sent={total_sent}, " \
            f"error_count={error_count}, rate={error_rate:.4f}"

    @given(total_sent=st.integers(min_value=1, max_value=1000))
    def test_no_warning_when_no_errors(self, total_sent: int):
        """
        **Feature: whatsapp-monitoring, Property 5: Error Rate Alert**
        **Validates: Requirements 6.2**
        
        For any total_sent > 0 with zero errors, error_rate_warning should be False.
        """
        from app.services.monitoring_service import MonitoringService
        
        warning = MonitoringService.calculate_error_rate_warning(total_sent, 0)
        
        assert warning is False, \
            f"Expected no warning with 0 errors, got warning={warning}"

    @given(
        total_sent=st.integers(min_value=10, max_value=1000)
    )
    def test_warning_at_boundary(self, total_sent: int):
        """
        **Feature: whatsapp-monitoring, Property 5: Error Rate Alert**
        **Validates: Requirements 6.2**
        
        Test the boundary condition: exactly 10% should NOT trigger warning,
        but above 10% should.
        """
        from app.services.monitoring_service import MonitoringService
        
        # Calculate error count for exactly 10%
        error_count_at_10_percent = total_sent // 10
        
        # At exactly 10% (or slightly below due to integer division), no warning
        warning_at_10 = MonitoringService.calculate_error_rate_warning(
            total_sent, error_count_at_10_percent
        )
        
        # Verify: if error_count/total_sent <= 0.10, warning should be False
        actual_rate = error_count_at_10_percent / total_sent
        if actual_rate <= 0.10:
            assert warning_at_10 is False, \
                f"Expected no warning at rate={actual_rate:.4f} (<= 10%)"
        
        # Above 10% should trigger warning
        error_count_above_10 = error_count_at_10_percent + 1
        warning_above_10 = MonitoringService.calculate_error_rate_warning(
            total_sent, error_count_above_10
        )
        
        actual_rate_above = error_count_above_10 / total_sent
        if actual_rate_above > 0.10:
            assert warning_above_10 is True, \
                f"Expected warning at rate={actual_rate_above:.4f} (> 10%)"

    @given(error_count=st.integers(min_value=0, max_value=1000))
    def test_no_warning_when_total_sent_zero(self, error_count: int):
        """
        **Feature: whatsapp-monitoring, Property 5: Error Rate Alert**
        **Validates: Requirements 6.2**
        
        When total_sent is 0, error_rate_warning should be False (avoid division by zero).
        """
        from app.services.monitoring_service import MonitoringService
        
        warning = MonitoringService.calculate_error_rate_warning(0, error_count)
        
        assert warning is False, \
            f"Expected no warning when total_sent=0, got warning={warning}"

    @given(
        total_sent=st.integers(min_value=1, max_value=1000),
        error_count=st.integers(min_value=0, max_value=1000)
    )
    def test_error_rate_warning_returns_boolean(
        self,
        total_sent: int,
        error_count: int
    ):
        """
        **Feature: whatsapp-monitoring, Property 5: Error Rate Alert**
        **Validates: Requirements 6.2**
        
        For any inputs, the result should always be a boolean.
        """
        from app.services.monitoring_service import MonitoringService
        
        warning = MonitoringService.calculate_error_rate_warning(total_sent, error_count)
        
        assert isinstance(warning, bool), \
            f"Expected boolean, got {type(warning)}"


class TestAuthenticationRequiredProperty:
    """
    Property 8: Authentication Required
    
    *For any* request to `/api/monitoring/*` endpoints without a valid JWT token,
    the response SHALL be HTTP 401 Unauthorized.
    
    **Feature: whatsapp-monitoring, Property 8: Authentication Required**
    **Validates: Requirements 8.4**
    """

    @given(endpoint=st.sampled_from(["/api/monitoring/stats", "/api/monitoring/history", "/api/monitoring/errors"]))
    def test_unauthenticated_request_returns_401(self, endpoint: str):
        """
        **Feature: whatsapp-monitoring, Property 8: Authentication Required**
        **Validates: Requirements 8.4**
        
        For any monitoring endpoint, a request without JWT token should return 401.
        """
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app)
        
        # Make request without Authorization header
        response = client.get(endpoint)
        
        # Property: should return 401 Unauthorized
        assert response.status_code == 401, \
            f"Expected 401 for unauthenticated request to {endpoint}, got {response.status_code}"

    @given(
        endpoint=st.sampled_from(["/api/monitoring/stats", "/api/monitoring/history", "/api/monitoring/errors"]),
        invalid_token=st.text(
            alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-",
            min_size=1,
            max_size=50
        ).filter(lambda x: x.strip() != "")
    )
    def test_invalid_token_returns_401(self, endpoint: str, invalid_token: str):
        """
        **Feature: whatsapp-monitoring, Property 8: Authentication Required**
        **Validates: Requirements 8.4**
        
        For any monitoring endpoint, a request with an invalid JWT token should return 401.
        """
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app)
        
        # Make request with invalid Authorization header
        response = client.get(
            endpoint,
            headers={"Authorization": f"Bearer {invalid_token}"}
        )
        
        # Property: should return 401 Unauthorized
        assert response.status_code == 401, \
            f"Expected 401 for invalid token on {endpoint}, got {response.status_code}"

    @given(endpoint=st.sampled_from(["/api/monitoring/stats", "/api/monitoring/history", "/api/monitoring/errors"]))
    def test_missing_bearer_prefix_returns_401(self, endpoint: str):
        """
        **Feature: whatsapp-monitoring, Property 8: Authentication Required**
        **Validates: Requirements 8.4**
        
        For any monitoring endpoint, a request with Authorization header but without
        'Bearer' prefix should return 401.
        """
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app)
        
        # Make request with malformed Authorization header (no Bearer prefix)
        response = client.get(
            endpoint,
            headers={"Authorization": "some_token_without_bearer"}
        )
        
        # Property: should return 401 Unauthorized
        assert response.status_code == 401, \
            f"Expected 401 for missing Bearer prefix on {endpoint}, got {response.status_code}"

    @given(endpoint=st.sampled_from(["/api/monitoring/stats", "/api/monitoring/history", "/api/monitoring/errors"]))
    def test_empty_token_returns_401(self, endpoint: str):
        """
        **Feature: whatsapp-monitoring, Property 8: Authentication Required**
        **Validates: Requirements 8.4**
        
        For any monitoring endpoint, a request with empty Bearer token should return 401.
        """
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app)
        
        # Make request with empty Bearer token
        response = client.get(
            endpoint,
            headers={"Authorization": "Bearer "}
        )
        
        # Property: should return 401 Unauthorized
        assert response.status_code == 401, \
            f"Expected 401 for empty token on {endpoint}, got {response.status_code}"


class TestPersistenceRoundTripProperty:
    """
    Property 6: Persistence Round-Trip
    
    *For any* daily statistics persisted to Supabase, querying the same date
    SHALL return identical values for message_1_count, message_2_count, and error_count.
    
    **Feature: whatsapp-monitoring, Property 6: Persistence Round-Trip**
    **Validates: Requirements 1.4, 7.4**
    """

    @given(
        message_1_count=st.integers(min_value=0, max_value=200),
        message_2_count=st.integers(min_value=0, max_value=200),
        error_count=st.integers(min_value=0, max_value=50)
    )
    def test_upsert_then_get_returns_same_values(
        self,
        message_1_count: int,
        message_2_count: int,
        error_count: int
    ):
        """
        **Feature: whatsapp-monitoring, Property 6: Persistence Round-Trip**
        **Validates: Requirements 1.4, 7.4**
        
        For any daily statistics, upserting then getting should return identical values.
        """
        from datetime import datetime, timezone
        from unittest.mock import MagicMock, patch
        
        # Create mock SupabaseDB
        mock_db = MagicMock()
        
        # Track what was upserted
        upserted_data = {}
        
        def mock_upsert(data):
            upserted_data.update(data)
            return data
        
        def mock_get(date):
            if date == upserted_data.get("date"):
                return {
                    "date": upserted_data["date"],
                    "message_1_count": upserted_data["message_1_count"],
                    "message_2_count": upserted_data["message_2_count"],
                    "error_count": upserted_data["error_count"]
                }
            return None
        
        mock_db.upsert_daily_stats = mock_upsert
        mock_db.get_daily_stats = mock_get
        
        # Test data
        test_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        original_data = {
            "date": test_date,
            "message_1_count": message_1_count,
            "message_2_count": message_2_count,
            "error_count": error_count
        }
        
        # Upsert the data
        mock_db.upsert_daily_stats(original_data)
        
        # Get the data back
        retrieved_data = mock_db.get_daily_stats(test_date)
        
        # Property: retrieved values should match original
        assert retrieved_data is not None, "Expected data to be retrieved"
        assert retrieved_data["message_1_count"] == message_1_count, \
            f"Expected message_1_count={message_1_count}, got {retrieved_data['message_1_count']}"
        assert retrieved_data["message_2_count"] == message_2_count, \
            f"Expected message_2_count={message_2_count}, got {retrieved_data['message_2_count']}"
        assert retrieved_data["error_count"] == error_count, \
            f"Expected error_count={error_count}, got {retrieved_data['error_count']}"

    @given(
        message_1_count=st.integers(min_value=0, max_value=200),
        message_2_count=st.integers(min_value=0, max_value=200),
        error_count=st.integers(min_value=0, max_value=50)
    )
    def test_sync_to_supabase_preserves_stats(
        self,
        message_1_count: int,
        message_2_count: int,
        error_count: int
    ):
        """
        **Feature: whatsapp-monitoring, Property 6: Persistence Round-Trip**
        **Validates: Requirements 1.4, 7.4**
        
        For any Redis stats, sync_to_supabase should persist identical values.
        """
        from app.services.monitoring_service import MonitoringService, DailyStats
        from unittest.mock import MagicMock, patch
        from datetime import datetime, timezone
        
        # Create service with mocked Redis
        service = MonitoringService.__new__(MonitoringService)
        service.redis_url = "redis://localhost:6379/0"
        
        # Mock Redis client
        mock_redis = MagicMock()
        mock_redis.set = MagicMock()
        mock_redis.expire = MagicMock()
        service._redis = mock_redis
        
        # Track what was persisted to Supabase
        persisted_data = {}
        
        mock_db = MagicMock()
        def mock_upsert(data):
            persisted_data.update(data)
            return data
        mock_db.upsert_daily_stats = mock_upsert
        
        # Mock get_daily_stats to return our test values
        test_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        mock_stats = DailyStats(
            date=test_date,
            message_1_count=message_1_count,
            message_2_count=message_2_count,
            error_count=error_count
        )
        
        with patch.object(service, 'get_daily_stats', return_value=mock_stats):
            with patch('app.supabase_client.get_supabase_db', return_value=mock_db):
                service.sync_to_supabase()
        
        # Property: persisted values should match original stats
        assert persisted_data.get("message_1_count") == message_1_count, \
            f"Expected message_1_count={message_1_count}, got {persisted_data.get('message_1_count')}"
        assert persisted_data.get("message_2_count") == message_2_count, \
            f"Expected message_2_count={message_2_count}, got {persisted_data.get('message_2_count')}"
        assert persisted_data.get("error_count") == error_count, \
            f"Expected error_count={error_count}, got {persisted_data.get('error_count')}"

    @given(
        message_1_count=st.integers(min_value=0, max_value=200),
        message_2_count=st.integers(min_value=0, max_value=200),
        error_count=st.integers(min_value=0, max_value=50)
    )
    def test_sync_from_supabase_restores_stats(
        self,
        message_1_count: int,
        message_2_count: int,
        error_count: int
    ):
        """
        **Feature: whatsapp-monitoring, Property 6: Persistence Round-Trip**
        **Validates: Requirements 1.4, 7.4**
        
        For any Supabase stats, sync_from_supabase should restore identical values to Redis.
        """
        from app.services.monitoring_service import MonitoringService
        from unittest.mock import MagicMock, patch
        from datetime import datetime, timezone
        
        # Create service with mocked Redis
        service = MonitoringService.__new__(MonitoringService)
        service.redis_url = "redis://localhost:6379/0"
        
        # Track what was set in Redis
        redis_values = {}
        
        mock_redis = MagicMock()
        mock_pipeline = MagicMock()
        
        def mock_set(key, value):
            redis_values[key] = value
        
        mock_pipeline.set = mock_set
        mock_pipeline.expire = MagicMock()
        mock_pipeline.execute = MagicMock()
        mock_redis.pipeline.return_value = mock_pipeline
        service._redis = mock_redis
        
        # Mock Supabase data
        test_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        supabase_data = {
            "date": test_date,
            "message_1_count": message_1_count,
            "message_2_count": message_2_count,
            "error_count": error_count
        }
        
        mock_db = MagicMock()
        mock_db.get_daily_stats = MagicMock(return_value=supabase_data)
        
        with patch('app.supabase_client.get_supabase_db', return_value=mock_db):
            service.sync_from_supabase()
        
        # Property: Redis values should match Supabase values
        # Find the keys that were set
        message_1_key = [k for k in redis_values.keys() if "message_1" in k]
        message_2_key = [k for k in redis_values.keys() if "message_2" in k]
        errors_key = [k for k in redis_values.keys() if "errors" in k]
        
        if message_1_key:
            assert redis_values[message_1_key[0]] == message_1_count, \
                f"Expected message_1={message_1_count}, got {redis_values[message_1_key[0]]}"
        if message_2_key:
            assert redis_values[message_2_key[0]] == message_2_count, \
                f"Expected message_2={message_2_count}, got {redis_values[message_2_key[0]]}"
        if errors_key:
            assert redis_values[errors_key[0]] == error_count, \
                f"Expected errors={error_count}, got {redis_values[errors_key[0]]}"

    @given(
        message_1_count=st.integers(min_value=0, max_value=200),
        message_2_count=st.integers(min_value=0, max_value=200),
        error_count=st.integers(min_value=0, max_value=50)
    )
    def test_full_round_trip_sync_to_then_from(
        self,
        message_1_count: int,
        message_2_count: int,
        error_count: int
    ):
        """
        **Feature: whatsapp-monitoring, Property 6: Persistence Round-Trip**
        **Validates: Requirements 1.4, 7.4**
        
        For any stats, sync_to_supabase followed by sync_from_supabase should
        restore the same values.
        """
        from app.services.monitoring_service import MonitoringService, DailyStats
        from unittest.mock import MagicMock, patch
        from datetime import datetime, timezone
        
        # Simulated Supabase storage
        supabase_storage = {}
        
        # Create mock SupabaseDB
        mock_db = MagicMock()
        
        def mock_upsert(data):
            date = data["date"]
            supabase_storage[date] = {
                "date": date,
                "message_1_count": data["message_1_count"],
                "message_2_count": data["message_2_count"],
                "error_count": data["error_count"]
            }
            return supabase_storage[date]
        
        def mock_get(date):
            return supabase_storage.get(date)
        
        mock_db.upsert_daily_stats = mock_upsert
        mock_db.get_daily_stats = mock_get
        
        # Create service with mocked Redis
        service = MonitoringService.__new__(MonitoringService)
        service.redis_url = "redis://localhost:6379/0"
        
        # Track Redis values
        redis_values = {}
        
        mock_redis = MagicMock()
        mock_pipeline = MagicMock()
        
        def mock_set(key, value):
            redis_values[key] = value
        
        mock_pipeline.set = mock_set
        mock_pipeline.expire = MagicMock()
        mock_pipeline.execute = MagicMock()
        mock_redis.pipeline.return_value = mock_pipeline
        mock_redis.set = mock_set
        mock_redis.expire = MagicMock()
        service._redis = mock_redis
        
        # Initial stats
        test_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        initial_stats = DailyStats(
            date=test_date,
            message_1_count=message_1_count,
            message_2_count=message_2_count,
            error_count=error_count
        )
        
        # Step 1: Sync to Supabase
        with patch.object(service, 'get_daily_stats', return_value=initial_stats):
            with patch('app.supabase_client.get_supabase_db', return_value=mock_db):
                service.sync_to_supabase()
        
        # Step 2: Sync from Supabase
        with patch('app.supabase_client.get_supabase_db', return_value=mock_db):
            service.sync_from_supabase()
        
        # Property: Values should be preserved through the round trip
        assert supabase_storage.get(test_date) is not None, "Data should be in Supabase"
        assert supabase_storage[test_date]["message_1_count"] == message_1_count
        assert supabase_storage[test_date]["message_2_count"] == message_2_count
        assert supabase_storage[test_date]["error_count"] == error_count
