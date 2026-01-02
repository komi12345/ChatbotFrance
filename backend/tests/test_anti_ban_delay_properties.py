"""
Property-based tests for Anti-Ban Delay System.

Tests the correctness properties defined in the design document for the
WhatsApp Ban Prevention feature.

**Feature: whatsapp-ban-prevention**
"""
import pytest
from hypothesis import given, settings as hyp_settings, strategies as st, HealthCheck

# Configure Hypothesis for CI: minimum 100 iterations
hyp_settings.register_profile(
    "ci",
    max_examples=100,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None
)
hyp_settings.load_profile("ci")


# ==========================================================================
# STRATEGIES FOR ANTI-BAN DELAY TESTS
# ==========================================================================

# Strategy for messages sent today (0-1200 to test all warm-up phases)
messages_sent_today_strategy = st.integers(min_value=0, max_value=1200)

# Strategy for phase 1: 0-29 messages
phase_1_strategy = st.integers(min_value=0, max_value=29)

# Strategy for phase 2: 30-79 messages
phase_2_strategy = st.integers(min_value=30, max_value=79)

# Strategy for phase 3: 80-199 messages
phase_3_strategy = st.integers(min_value=80, max_value=199)

# Strategy for phase 4: 200-499 messages
phase_4_strategy = st.integers(min_value=200, max_value=499)

# Strategy for phase 5: 500+ messages
phase_5_strategy = st.integers(min_value=500, max_value=1200)


class TestDelayBoundsGuaranteeProperty:
    """
    Property 1: Delay Bounds Guarantee
    
    *For any* calculated delay, the result SHALL be at least 10 seconds
    and at most 40 seconds (base_max + variation_max + typing_max).
    
    **Feature: whatsapp-ban-prevention, Property 1: Delay Bounds Guarantee**
    **Validates: Requirements 1.1, 1.3, 1.5**
    """

    @given(messages_sent_today=messages_sent_today_strategy)
    def test_delay_never_below_minimum(self, messages_sent_today: int):
        """
        **Feature: whatsapp-ban-prevention, Property 1: Delay Bounds Guarantee**
        **Validates: Requirements 1.1, 1.5**
        
        For any messages_sent_today value, the calculated delay should never
        be below the minimum of 10 seconds.
        """
        from app.tasks.message_tasks import get_anti_ban_delay, ANTI_BAN_MIN_DELAY
        
        delay = get_anti_ban_delay(messages_sent_today)
        
        # Property: delay >= ANTI_BAN_MIN_DELAY (10 seconds)
        assert delay >= ANTI_BAN_MIN_DELAY, \
            f"Expected delay >= {ANTI_BAN_MIN_DELAY}s, got {delay:.2f}s for messages_sent_today={messages_sent_today}"

    @given(messages_sent_today=messages_sent_today_strategy)
    def test_delay_never_above_maximum(self, messages_sent_today: int):
        """
        **Feature: whatsapp-ban-prevention, Property 1: Delay Bounds Guarantee**
        **Validates: Requirements 1.3**
        
        For any messages_sent_today value, the calculated delay should never
        exceed the theoretical maximum of 43 seconds (35 + 5 + 3).
        """
        from app.tasks.message_tasks import (
            get_anti_ban_delay,
            ANTI_BAN_RANDOM_VARIATION,
            HUMAN_TYPING_DELAY_MAX
        )
        
        delay = get_anti_ban_delay(messages_sent_today)
        
        # Maximum possible delay:
        # - Max base delay (phase 1): 35 seconds
        # - Max random variation: +5 seconds
        # - Max typing delay: 3 seconds
        # Total max: 35 + 5 + 3 = 43 seconds
        max_delay = 35 + ANTI_BAN_RANDOM_VARIATION + HUMAN_TYPING_DELAY_MAX
        
        # Property: delay <= max_delay
        assert delay <= max_delay, \
            f"Expected delay <= {max_delay}s, got {delay:.2f}s for messages_sent_today={messages_sent_today}"

    @given(messages_sent_today=messages_sent_today_strategy)
    def test_delay_is_positive_float(self, messages_sent_today: int):
        """
        **Feature: whatsapp-ban-prevention, Property 1: Delay Bounds Guarantee**
        **Validates: Requirements 1.1, 1.3, 1.5**
        
        For any messages_sent_today value, the calculated delay should be
        a positive float.
        """
        from app.tasks.message_tasks import get_anti_ban_delay
        
        delay = get_anti_ban_delay(messages_sent_today)
        
        # Property: delay is a float
        assert isinstance(delay, float), \
            f"Expected float, got {type(delay)}"
        
        # Property: delay is positive
        assert delay > 0, \
            f"Expected positive delay, got {delay}"

    @given(messages_sent_today=messages_sent_today_strategy)
    def test_delay_within_valid_range(self, messages_sent_today: int):
        """
        **Feature: whatsapp-ban-prevention, Property 1: Delay Bounds Guarantee**
        **Validates: Requirements 1.1, 1.3, 1.5**
        
        For any messages_sent_today value, the calculated delay should be
        within the valid range [10, 43] seconds.
        """
        from app.tasks.message_tasks import get_anti_ban_delay, ANTI_BAN_MIN_DELAY
        
        delay = get_anti_ban_delay(messages_sent_today)
        
        # Property: delay is within valid range
        min_delay = ANTI_BAN_MIN_DELAY  # 10 seconds
        max_delay = 43  # 35 + 5 + 3 seconds
        
        assert min_delay <= delay <= max_delay, \
            f"Expected delay in [{min_delay}, {max_delay}], got {delay:.2f}s"



class TestWarmUpDelayRangesProperty:
    """
    Property 2: Warm-Up Delay Ranges
    
    *For any* message count N, the warm-up delay SHALL fall within the correct range:
    - N < 30: delay ∈ [25, 35]
    - 30 ≤ N < 80: delay ∈ [20, 28]
    - 80 ≤ N < 200: delay ∈ [15, 22]
    - 200 ≤ N < 500: delay ∈ [18, 25]
    - N ≥ 500: delay ∈ [22, 30]
    
    **Feature: whatsapp-ban-prevention, Property 2: Warm-Up Delay Ranges**
    **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**
    """

    @given(messages_sent_today=phase_1_strategy)
    def test_phase_1_delay_range(self, messages_sent_today: int):
        """
        **Feature: whatsapp-ban-prevention, Property 2: Warm-Up Delay Ranges**
        **Validates: Requirements 2.1**
        
        For messages_sent_today < 30 (Phase 1), warm-up delay should be
        in range [25, 35] seconds.
        """
        from app.tasks.message_tasks import get_warm_up_delay
        
        delay = get_warm_up_delay(messages_sent_today)
        
        # Property: delay in [25, 35] for phase 1
        assert 25 <= delay <= 35, \
            f"Expected delay in [25, 35] for phase 1 (N={messages_sent_today}), got {delay:.2f}s"

    @given(messages_sent_today=phase_2_strategy)
    def test_phase_2_delay_range(self, messages_sent_today: int):
        """
        **Feature: whatsapp-ban-prevention, Property 2: Warm-Up Delay Ranges**
        **Validates: Requirements 2.2**
        
        For 30 <= messages_sent_today < 80 (Phase 2), warm-up delay should be
        in range [20, 28] seconds.
        """
        from app.tasks.message_tasks import get_warm_up_delay
        
        delay = get_warm_up_delay(messages_sent_today)
        
        # Property: delay in [20, 28] for phase 2
        assert 20 <= delay <= 28, \
            f"Expected delay in [20, 28] for phase 2 (N={messages_sent_today}), got {delay:.2f}s"

    @given(messages_sent_today=phase_3_strategy)
    def test_phase_3_delay_range(self, messages_sent_today: int):
        """
        **Feature: whatsapp-ban-prevention, Property 2: Warm-Up Delay Ranges**
        **Validates: Requirements 2.3**
        
        For 80 <= messages_sent_today < 200 (Phase 3), warm-up delay should be
        in range [15, 22] seconds.
        """
        from app.tasks.message_tasks import get_warm_up_delay
        
        delay = get_warm_up_delay(messages_sent_today)
        
        # Property: delay in [15, 22] for phase 3
        assert 15 <= delay <= 22, \
            f"Expected delay in [15, 22] for phase 3 (N={messages_sent_today}), got {delay:.2f}s"

    @given(messages_sent_today=phase_4_strategy)
    def test_phase_4_delay_range(self, messages_sent_today: int):
        """
        **Feature: whatsapp-ban-prevention, Property 2: Warm-Up Delay Ranges**
        **Validates: Requirements 2.4**
        
        For 200 <= messages_sent_today < 500 (Phase 4), warm-up delay should be
        in range [18, 25] seconds.
        """
        from app.tasks.message_tasks import get_warm_up_delay
        
        delay = get_warm_up_delay(messages_sent_today)
        
        # Property: delay in [18, 25] for phase 4
        assert 18 <= delay <= 25, \
            f"Expected delay in [18, 25] for phase 4 (N={messages_sent_today}), got {delay:.2f}s"

    @given(messages_sent_today=phase_5_strategy)
    def test_phase_5_delay_range(self, messages_sent_today: int):
        """
        **Feature: whatsapp-ban-prevention, Property 2: Warm-Up Delay Ranges**
        **Validates: Requirements 2.5**
        
        For messages_sent_today >= 500 (Phase 5), warm-up delay should be
        in range [22, 30] seconds.
        """
        from app.tasks.message_tasks import get_warm_up_delay
        
        delay = get_warm_up_delay(messages_sent_today)
        
        # Property: delay in [22, 30] for phase 5
        assert 22 <= delay <= 30, \
            f"Expected delay in [22, 30] for phase 5 (N={messages_sent_today}), got {delay:.2f}s"

    @given(messages_sent_today=messages_sent_today_strategy)
    def test_warm_up_delay_is_positive_float(self, messages_sent_today: int):
        """
        **Feature: whatsapp-ban-prevention, Property 2: Warm-Up Delay Ranges**
        **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**
        
        For any messages_sent_today value, the warm-up delay should be
        a positive float.
        """
        from app.tasks.message_tasks import get_warm_up_delay
        
        delay = get_warm_up_delay(messages_sent_today)
        
        # Property: delay is a float
        assert isinstance(delay, float), \
            f"Expected float, got {type(delay)}"
        
        # Property: delay is positive
        assert delay > 0, \
            f"Expected positive delay, got {delay}"

    def test_phase_boundaries(self):
        """
        **Feature: whatsapp-ban-prevention, Property 2: Warm-Up Delay Ranges**
        **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**
        
        Test the exact boundary values between phases.
        """
        from app.tasks.message_tasks import get_warm_up_delay
        
        # Test boundary: 29 (phase 1) vs 30 (phase 2)
        delay_29 = get_warm_up_delay(29)
        delay_30 = get_warm_up_delay(30)
        
        assert 25 <= delay_29 <= 35, f"N=29 should be phase 1, got {delay_29:.2f}s"
        assert 20 <= delay_30 <= 28, f"N=30 should be phase 2, got {delay_30:.2f}s"
        
        # Test boundary: 79 (phase 2) vs 80 (phase 3)
        delay_79 = get_warm_up_delay(79)
        delay_80 = get_warm_up_delay(80)
        
        assert 20 <= delay_79 <= 28, f"N=79 should be phase 2, got {delay_79:.2f}s"
        assert 15 <= delay_80 <= 22, f"N=80 should be phase 3, got {delay_80:.2f}s"
        
        # Test boundary: 199 (phase 3) vs 200 (phase 4)
        delay_199 = get_warm_up_delay(199)
        delay_200 = get_warm_up_delay(200)
        
        assert 15 <= delay_199 <= 22, f"N=199 should be phase 3, got {delay_199:.2f}s"
        assert 18 <= delay_200 <= 25, f"N=200 should be phase 4, got {delay_200:.2f}s"
        
        # Test boundary: 499 (phase 4) vs 500 (phase 5)
        delay_499 = get_warm_up_delay(499)
        delay_500 = get_warm_up_delay(500)
        
        assert 18 <= delay_499 <= 25, f"N=499 should be phase 4, got {delay_499:.2f}s"
        assert 22 <= delay_500 <= 30, f"N=500 should be phase 5, got {delay_500:.2f}s"


# ==========================================================================
# STRATEGIES FOR STRATEGIC PAUSE TESTS
# ==========================================================================

# Strategy for consecutive messages (0-150 to test all thresholds)
consecutive_messages_strategy = st.integers(min_value=0, max_value=150)

# Strategy for exact threshold values
threshold_values_strategy = st.sampled_from([20, 40, 60, 100])

# Strategy for non-threshold values (values that should NOT trigger a pause)
non_threshold_strategy = st.integers(min_value=0, max_value=150).filter(
    lambda x: x not in [20, 40, 60, 100]
)

# Strategy for values below threshold 1 (0-19)
below_threshold_1_strategy = st.integers(min_value=0, max_value=19)

# Strategy for values between threshold 1 and 2 (21-39)
between_threshold_1_2_strategy = st.integers(min_value=21, max_value=39)

# Strategy for values between threshold 2 and 3 (41-59)
between_threshold_2_3_strategy = st.integers(min_value=41, max_value=59)

# Strategy for values between threshold 3 and 4 (61-99)
between_threshold_3_4_strategy = st.integers(min_value=61, max_value=99)

# Strategy for values above threshold 4 (101+)
above_threshold_4_strategy = st.integers(min_value=101, max_value=150)


class TestStrategicPauseTriggersProperty:
    """
    Property 3: Strategic Pause Triggers
    
    *For any* consecutive message count, a strategic pause SHALL be triggered
    at exactly 20, 40, 60, and 100 messages, with durations in the correct ranges.
    
    **Feature: whatsapp-ban-prevention, Property 3: Strategic Pause Triggers**
    **Validates: Requirements 3.1, 3.2, 3.3, 3.4**
    """

    @given(consecutive_messages=threshold_values_strategy)
    def test_pause_triggered_at_thresholds(self, consecutive_messages: int):
        """
        **Feature: whatsapp-ban-prevention, Property 3: Strategic Pause Triggers**
        **Validates: Requirements 3.1, 3.2, 3.3, 3.4**
        
        For any threshold value (20, 40, 60, 100), should_take_strategic_pause
        should return True.
        """
        from app.tasks.message_tasks import should_take_strategic_pause
        
        result = should_take_strategic_pause(consecutive_messages)
        
        # Property: pause should be triggered at threshold values
        assert result is True, \
            f"Expected pause to be triggered at {consecutive_messages} messages, got {result}"

    @given(consecutive_messages=non_threshold_strategy)
    def test_pause_not_triggered_at_non_thresholds(self, consecutive_messages: int):
        """
        **Feature: whatsapp-ban-prevention, Property 3: Strategic Pause Triggers**
        **Validates: Requirements 3.1, 3.2, 3.3, 3.4**
        
        For any non-threshold value, should_take_strategic_pause should return False.
        """
        from app.tasks.message_tasks import should_take_strategic_pause
        
        result = should_take_strategic_pause(consecutive_messages)
        
        # Property: pause should NOT be triggered at non-threshold values
        assert result is False, \
            f"Expected no pause at {consecutive_messages} messages, got {result}"

    def test_threshold_20_pause_duration_range(self):
        """
        **Feature: whatsapp-ban-prevention, Property 3: Strategic Pause Triggers**
        **Validates: Requirements 3.1**
        
        At 20 messages, pause duration should be in range [180, 300] seconds (3-5 minutes).
        """
        from app.tasks.message_tasks import (
            get_strategic_pause_duration,
            PAUSE_DURATION_1
        )
        
        # Run multiple times to test randomization
        for _ in range(100):
            duration = get_strategic_pause_duration(20)
            min_pause, max_pause = PAUSE_DURATION_1
            
            assert min_pause <= duration <= max_pause, \
                f"Expected duration in [{min_pause}, {max_pause}] for 20 messages, got {duration:.2f}s"

    def test_threshold_40_pause_duration_range(self):
        """
        **Feature: whatsapp-ban-prevention, Property 3: Strategic Pause Triggers**
        **Validates: Requirements 3.2**
        
        At 40 messages, pause duration should be in range [300, 480] seconds (5-8 minutes).
        """
        from app.tasks.message_tasks import (
            get_strategic_pause_duration,
            PAUSE_DURATION_2
        )
        
        # Run multiple times to test randomization
        for _ in range(100):
            duration = get_strategic_pause_duration(40)
            min_pause, max_pause = PAUSE_DURATION_2
            
            assert min_pause <= duration <= max_pause, \
                f"Expected duration in [{min_pause}, {max_pause}] for 40 messages, got {duration:.2f}s"

    def test_threshold_60_pause_duration_range(self):
        """
        **Feature: whatsapp-ban-prevention, Property 3: Strategic Pause Triggers**
        **Validates: Requirements 3.3**
        
        At 60 messages, pause duration should be in range [600, 900] seconds (10-15 minutes).
        """
        from app.tasks.message_tasks import (
            get_strategic_pause_duration,
            PAUSE_DURATION_3
        )
        
        # Run multiple times to test randomization
        for _ in range(100):
            duration = get_strategic_pause_duration(60)
            min_pause, max_pause = PAUSE_DURATION_3
            
            assert min_pause <= duration <= max_pause, \
                f"Expected duration in [{min_pause}, {max_pause}] for 60 messages, got {duration:.2f}s"

    def test_threshold_100_pause_duration_range(self):
        """
        **Feature: whatsapp-ban-prevention, Property 3: Strategic Pause Triggers**
        **Validates: Requirements 3.4**
        
        At 100 messages, pause duration should be in range [1200, 1800] seconds (20-30 minutes).
        """
        from app.tasks.message_tasks import (
            get_strategic_pause_duration,
            PAUSE_DURATION_4
        )
        
        # Run multiple times to test randomization
        for _ in range(100):
            duration = get_strategic_pause_duration(100)
            min_pause, max_pause = PAUSE_DURATION_4
            
            assert min_pause <= duration <= max_pause, \
                f"Expected duration in [{min_pause}, {max_pause}] for 100 messages, got {duration:.2f}s"

    @given(consecutive_messages=below_threshold_1_strategy)
    def test_no_pause_below_threshold_1(self, consecutive_messages: int):
        """
        **Feature: whatsapp-ban-prevention, Property 3: Strategic Pause Triggers**
        **Validates: Requirements 3.1**
        
        For consecutive_messages < 20, pause duration should be 0.
        """
        from app.tasks.message_tasks import get_strategic_pause_duration
        
        duration = get_strategic_pause_duration(consecutive_messages)
        
        # Property: no pause below threshold 1
        assert duration == 0.0, \
            f"Expected 0 duration for {consecutive_messages} messages, got {duration:.2f}s"

    @given(consecutive_messages=between_threshold_1_2_strategy)
    def test_threshold_1_duration_between_20_and_40(self, consecutive_messages: int):
        """
        **Feature: whatsapp-ban-prevention, Property 3: Strategic Pause Triggers**
        **Validates: Requirements 3.1**
        
        For 20 < consecutive_messages < 40, pause duration should use threshold 1 range.
        """
        from app.tasks.message_tasks import (
            get_strategic_pause_duration,
            PAUSE_DURATION_1
        )
        
        duration = get_strategic_pause_duration(consecutive_messages)
        min_pause, max_pause = PAUSE_DURATION_1
        
        # Property: duration in threshold 1 range
        assert min_pause <= duration <= max_pause, \
            f"Expected duration in [{min_pause}, {max_pause}] for {consecutive_messages} messages, got {duration:.2f}s"

    @given(consecutive_messages=between_threshold_2_3_strategy)
    def test_threshold_2_duration_between_40_and_60(self, consecutive_messages: int):
        """
        **Feature: whatsapp-ban-prevention, Property 3: Strategic Pause Triggers**
        **Validates: Requirements 3.2**
        
        For 40 < consecutive_messages < 60, pause duration should use threshold 2 range.
        """
        from app.tasks.message_tasks import (
            get_strategic_pause_duration,
            PAUSE_DURATION_2
        )
        
        duration = get_strategic_pause_duration(consecutive_messages)
        min_pause, max_pause = PAUSE_DURATION_2
        
        # Property: duration in threshold 2 range
        assert min_pause <= duration <= max_pause, \
            f"Expected duration in [{min_pause}, {max_pause}] for {consecutive_messages} messages, got {duration:.2f}s"

    @given(consecutive_messages=between_threshold_3_4_strategy)
    def test_threshold_3_duration_between_60_and_100(self, consecutive_messages: int):
        """
        **Feature: whatsapp-ban-prevention, Property 3: Strategic Pause Triggers**
        **Validates: Requirements 3.3**
        
        For 60 < consecutive_messages < 100, pause duration should use threshold 3 range.
        """
        from app.tasks.message_tasks import (
            get_strategic_pause_duration,
            PAUSE_DURATION_3
        )
        
        duration = get_strategic_pause_duration(consecutive_messages)
        min_pause, max_pause = PAUSE_DURATION_3
        
        # Property: duration in threshold 3 range
        assert min_pause <= duration <= max_pause, \
            f"Expected duration in [{min_pause}, {max_pause}] for {consecutive_messages} messages, got {duration:.2f}s"

    @given(consecutive_messages=above_threshold_4_strategy)
    def test_threshold_4_duration_above_100(self, consecutive_messages: int):
        """
        **Feature: whatsapp-ban-prevention, Property 3: Strategic Pause Triggers**
        **Validates: Requirements 3.4**
        
        For consecutive_messages > 100, pause duration should use threshold 4 range.
        """
        from app.tasks.message_tasks import (
            get_strategic_pause_duration,
            PAUSE_DURATION_4
        )
        
        duration = get_strategic_pause_duration(consecutive_messages)
        min_pause, max_pause = PAUSE_DURATION_4
        
        # Property: duration in threshold 4 range
        assert min_pause <= duration <= max_pause, \
            f"Expected duration in [{min_pause}, {max_pause}] for {consecutive_messages} messages, got {duration:.2f}s"

    @given(consecutive_messages=consecutive_messages_strategy)
    def test_pause_duration_is_non_negative_float(self, consecutive_messages: int):
        """
        **Feature: whatsapp-ban-prevention, Property 3: Strategic Pause Triggers**
        **Validates: Requirements 3.1, 3.2, 3.3, 3.4**
        
        For any consecutive_messages value, pause duration should be a non-negative float.
        """
        from app.tasks.message_tasks import get_strategic_pause_duration
        
        duration = get_strategic_pause_duration(consecutive_messages)
        
        # Property: duration is a float
        assert isinstance(duration, float), \
            f"Expected float, got {type(duration)}"
        
        # Property: duration is non-negative
        assert duration >= 0, \
            f"Expected non-negative duration, got {duration}"

    def test_should_take_strategic_pause_returns_bool(self):
        """
        **Feature: whatsapp-ban-prevention, Property 3: Strategic Pause Triggers**
        **Validates: Requirements 3.1, 3.2, 3.3, 3.4**
        
        should_take_strategic_pause should always return a boolean.
        """
        from app.tasks.message_tasks import should_take_strategic_pause
        
        # Test various values
        test_values = [0, 10, 19, 20, 21, 39, 40, 41, 59, 60, 61, 99, 100, 101, 150]
        
        for value in test_values:
            result = should_take_strategic_pause(value)
            assert isinstance(result, bool), \
                f"Expected bool for {value}, got {type(result)}"

    def test_pause_duration_increases_with_threshold(self):
        """
        **Feature: whatsapp-ban-prevention, Property 3: Strategic Pause Triggers**
        **Validates: Requirements 3.1, 3.2, 3.3, 3.4**
        
        Higher thresholds should have longer minimum pause durations.
        """
        from app.tasks.message_tasks import (
            PAUSE_DURATION_1,
            PAUSE_DURATION_2,
            PAUSE_DURATION_3,
            PAUSE_DURATION_4
        )
        
        # Verify that minimum durations increase with threshold
        assert PAUSE_DURATION_1[0] < PAUSE_DURATION_2[0], \
            "Threshold 2 min should be > Threshold 1 min"
        assert PAUSE_DURATION_2[0] < PAUSE_DURATION_3[0], \
            "Threshold 3 min should be > Threshold 2 min"
        assert PAUSE_DURATION_3[0] < PAUSE_DURATION_4[0], \
            "Threshold 4 min should be > Threshold 3 min"


# ==========================================================================
# STRATEGIES FOR HUMAN BEHAVIOR SIMULATION TESTS
# ==========================================================================

# Strategy for night time hours (23, 0, 1, 2, 3, 4, 5)
night_time_hours_strategy = st.sampled_from([23, 0, 1, 2, 3, 4, 5])

# Strategy for day time hours (6, 7, ..., 22)
day_time_hours_strategy = st.integers(min_value=6, max_value=22)

# Strategy for all hours (0-23)
all_hours_strategy = st.integers(min_value=0, max_value=23)

# Strategy for message lengths (0-5000 characters)
message_length_strategy = st.integers(min_value=0, max_value=5000)

# Strategy for positive message lengths (1-5000 characters)
positive_message_length_strategy = st.integers(min_value=1, max_value=5000)


class TestNightTimeBlockingProperty:
    """
    Property 6: Night Time Blocking (DÉSACTIVÉ)
    
    IMPORTANT: Le blocage nocturne a été DÉSACTIVÉ pour permettre l'envoi
    de messages 24h/24. La fonction is_night_time() retourne maintenant
    toujours False.
    
    Ces tests vérifient que la fonction est bien désactivée et retourne
    toujours False, quelle que soit l'heure.
    
    **Feature: whatsapp-ban-prevention, Property 6: Night Time Blocking (DISABLED)**
    **Validates: Requirements 4.2 (DÉSACTIVÉ)**
    """

    @given(hour=night_time_hours_strategy)
    def test_night_time_hours_return_false_disabled(self, hour: int):
        """
        **Feature: whatsapp-ban-prevention, Property 6: Night Time Blocking (DISABLED)**
        **Validates: Requirements 4.2 (DÉSACTIVÉ)**
        
        DÉSACTIVÉ: is_night_time retourne toujours False pour permettre
        l'envoi 24h/24. Même pendant les heures de nuit (23h-6h), la fonction
        retourne False.
        """
        from app.tasks.message_tasks import is_night_time
        
        result = is_night_time()
        
        # Property: is_night_time always returns False (disabled)
        assert result is False, \
            f"Expected False (disabled) for hour {hour}, got {result}"

    @given(hour=day_time_hours_strategy)
    def test_day_time_hours_return_false(self, hour: int):
        """
        **Feature: whatsapp-ban-prevention, Property 6: Night Time Blocking (DISABLED)**
        **Validates: Requirements 4.2 (DÉSACTIVÉ)**
        
        Pour toutes les heures de jour, is_night_time retourne False.
        """
        from app.tasks.message_tasks import is_night_time
        
        result = is_night_time()
        
        # Property: day time hours should return False
        assert result is False, \
            f"Expected False for hour {hour}, got {result}"

    def test_function_always_returns_false(self):
        """
        **Feature: whatsapp-ban-prevention, Property 6: Night Time Blocking (DISABLED)**
        **Validates: Requirements 4.2 (DÉSACTIVÉ)**
        
        Vérifie que is_night_time retourne toujours False (désactivé).
        """
        from app.tasks.message_tasks import is_night_time
        
        # Test multiple times to ensure consistency
        for _ in range(10):
            result = is_night_time()
            assert result is False, "is_night_time should always return False (disabled)"

    def test_24h_sending_enabled(self):
        """
        **Feature: whatsapp-ban-prevention, Property 6: Night Time Blocking (DISABLED)**
        **Validates: Requirements 4.2 (DÉSACTIVÉ)**
        
        Vérifie que l'envoi 24h/24 est activé (pas de blocage nocturne).
        """
        from app.tasks.message_tasks import is_night_time
        
        # The function should always return False, enabling 24/7 sending
        result = is_night_time()
        assert result is False, "24/7 sending should be enabled (is_night_time returns False)"

    @given(hour=all_hours_strategy)
    def test_is_night_time_returns_bool(self, hour: int):
        """
        **Feature: whatsapp-ban-prevention, Property 6: Night Time Blocking (DISABLED)**
        **Validates: Requirements 4.2 (DÉSACTIVÉ)**
        
        is_night_time doit toujours retourner un booléen (False).
        """
        from app.tasks.message_tasks import is_night_time
        
        result = is_night_time()
        
        # Property: result should be a boolean
        assert isinstance(result, bool), \
            f"Expected bool for hour {hour}, got {type(result)}"
        
        # Property: result should always be False (disabled)
        assert result is False, \
            f"Expected False (disabled) for hour {hour}, got {result}"


class TestSimulateHumanBehaviorProperty:
    """
    Property 5: Micro-Pause Probability
    
    *For any* large sample of message sends (N > 1000), the proportion of
    sends with micro-pauses SHALL be approximately 10% (within statistical tolerance).
    
    **Feature: whatsapp-ban-prevention, Property 5: Micro-Pause Probability**
    **Validates: Requirements 4.1**
    """

    def test_micro_pause_returns_float(self):
        """
        **Feature: whatsapp-ban-prevention, Property 5: Micro-Pause Probability**
        **Validates: Requirements 4.1**
        
        simulate_human_behavior should always return a float.
        """
        from app.tasks.message_tasks import simulate_human_behavior
        
        # Run multiple times
        for _ in range(100):
            result = simulate_human_behavior()
            assert isinstance(result, float), \
                f"Expected float, got {type(result)}"

    def test_micro_pause_is_non_negative(self):
        """
        **Feature: whatsapp-ban-prevention, Property 5: Micro-Pause Probability**
        **Validates: Requirements 4.1**
        
        simulate_human_behavior should always return a non-negative value.
        """
        from app.tasks.message_tasks import simulate_human_behavior
        
        # Run multiple times
        for _ in range(100):
            result = simulate_human_behavior()
            assert result >= 0, \
                f"Expected non-negative value, got {result}"

    def test_micro_pause_within_bounds_when_triggered(self):
        """
        **Feature: whatsapp-ban-prevention, Property 5: Micro-Pause Probability**
        **Validates: Requirements 4.1**
        
        When a micro-pause is triggered, it should be within [30, 120] seconds.
        """
        from app.tasks.message_tasks import (
            simulate_human_behavior,
            MICRO_PAUSE_DURATION
        )
        
        min_pause, max_pause = MICRO_PAUSE_DURATION
        
        # Run many times to catch triggered pauses
        triggered_pauses = []
        for _ in range(1000):
            result = simulate_human_behavior()
            if result > 0:
                triggered_pauses.append(result)
        
        # Verify all triggered pauses are within bounds
        for pause in triggered_pauses:
            assert min_pause <= pause <= max_pause, \
                f"Expected pause in [{min_pause}, {max_pause}], got {pause:.2f}s"

    def test_micro_pause_probability_approximately_10_percent(self):
        """
        **Feature: whatsapp-ban-prevention, Property 5: Micro-Pause Probability**
        **Validates: Requirements 4.1**
        
        Over a large sample, approximately 10% of calls should trigger a pause.
        Statistical tolerance: 5% to 15% (accounting for randomness).
        """
        from app.tasks.message_tasks import simulate_human_behavior
        
        # Run 1000 times
        num_samples = 1000
        triggered_count = 0
        
        for _ in range(num_samples):
            result = simulate_human_behavior()
            if result > 0:
                triggered_count += 1
        
        # Calculate percentage
        percentage = triggered_count / num_samples
        
        # Property: percentage should be approximately 10% (with tolerance)
        # Using 5% to 15% as acceptable range for statistical variation
        assert 0.05 <= percentage <= 0.15, \
            f"Expected ~10% pause rate, got {percentage:.1%} ({triggered_count}/{num_samples})"


class TestMessageLengthDelayProperty:
    """
    Property for message length delay calculation.
    
    *For any* message length, the delay should be calculated as:
    - 1 second per 500 characters
    - Maximum 5 seconds
    
    **Feature: whatsapp-ban-prevention**
    **Validates: Requirements 4.3**
    """

    @given(message_length=message_length_strategy)
    def test_message_length_delay_returns_float(self, message_length: int):
        """
        **Feature: whatsapp-ban-prevention**
        **Validates: Requirements 4.3**
        
        get_message_length_delay should always return a float.
        """
        from app.tasks.message_tasks import get_message_length_delay
        
        result = get_message_length_delay(message_length)
        
        assert isinstance(result, float), \
            f"Expected float, got {type(result)}"

    @given(message_length=message_length_strategy)
    def test_message_length_delay_is_non_negative(self, message_length: int):
        """
        **Feature: whatsapp-ban-prevention**
        **Validates: Requirements 4.3**
        
        get_message_length_delay should always return a non-negative value.
        """
        from app.tasks.message_tasks import get_message_length_delay
        
        result = get_message_length_delay(message_length)
        
        assert result >= 0, \
            f"Expected non-negative value for length {message_length}, got {result}"

    @given(message_length=message_length_strategy)
    def test_message_length_delay_max_5_seconds(self, message_length: int):
        """
        **Feature: whatsapp-ban-prevention**
        **Validates: Requirements 4.3**
        
        get_message_length_delay should never exceed 5 seconds.
        """
        from app.tasks.message_tasks import get_message_length_delay
        
        result = get_message_length_delay(message_length)
        
        assert result <= 5.0, \
            f"Expected delay <= 5.0s for length {message_length}, got {result:.2f}s"

    @given(message_length=positive_message_length_strategy)
    def test_message_length_delay_formula(self, message_length: int):
        """
        **Feature: whatsapp-ban-prevention**
        **Validates: Requirements 4.3**
        
        For positive message lengths, delay should be min(length/500, 5).
        """
        from app.tasks.message_tasks import get_message_length_delay
        
        result = get_message_length_delay(message_length)
        expected = min(message_length / 500.0, 5.0)
        
        assert abs(result - expected) < 0.001, \
            f"Expected {expected:.4f}s for length {message_length}, got {result:.4f}s"

    def test_zero_length_returns_zero(self):
        """
        **Feature: whatsapp-ban-prevention**
        **Validates: Requirements 4.3**
        
        Zero message length should return 0 delay.
        """
        from app.tasks.message_tasks import get_message_length_delay
        
        result = get_message_length_delay(0)
        
        assert result == 0.0, \
            f"Expected 0.0s for length 0, got {result:.2f}s"

    def test_negative_length_returns_zero(self):
        """
        **Feature: whatsapp-ban-prevention**
        **Validates: Requirements 4.3**
        
        Negative message length should return 0 delay.
        """
        from app.tasks.message_tasks import get_message_length_delay
        
        result = get_message_length_delay(-100)
        
        assert result == 0.0, \
            f"Expected 0.0s for negative length, got {result:.2f}s"

    def test_500_chars_returns_1_second(self):
        """
        **Feature: whatsapp-ban-prevention**
        **Validates: Requirements 4.3**
        
        500 characters should return exactly 1 second delay.
        """
        from app.tasks.message_tasks import get_message_length_delay
        
        result = get_message_length_delay(500)
        
        assert result == 1.0, \
            f"Expected 1.0s for 500 chars, got {result:.2f}s"

    def test_2500_chars_returns_5_seconds(self):
        """
        **Feature: whatsapp-ban-prevention**
        **Validates: Requirements 4.3**
        
        2500 characters should return exactly 5 seconds delay (max).
        """
        from app.tasks.message_tasks import get_message_length_delay
        
        result = get_message_length_delay(2500)
        
        assert result == 5.0, \
            f"Expected 5.0s for 2500 chars, got {result:.2f}s"

    def test_5000_chars_returns_5_seconds_max(self):
        """
        **Feature: whatsapp-ban-prevention**
        **Validates: Requirements 4.3**
        
        5000 characters should return 5 seconds (capped at max).
        """
        from app.tasks.message_tasks import get_message_length_delay
        
        result = get_message_length_delay(5000)
        
        assert result == 5.0, \
            f"Expected 5.0s (max) for 5000 chars, got {result:.2f}s"


# ==========================================================================
# STRATEGIES FOR BAN RISK DETECTION TESTS
# ==========================================================================

# Strategy for dangerous error codes
dangerous_error_codes_strategy = st.sampled_from([
    "rate_limit",
    "spam_detected",
    "blocked",
    "429",
    "RATE_LIMIT",
    "SPAM_DETECTED",
    "BLOCKED",
    "Rate_Limit",
    "rate_limit_exceeded",
    "spam_detected_warning",
    "user_blocked",
    "error_429",
])

# Strategy for safe error codes (should NOT trigger ban risk)
safe_error_codes_strategy = st.sampled_from([
    "timeout",
    "network_error",
    "invalid_phone",
    "unknown_error",
    "connection_failed",
    "server_error",
    "500",
    "503",
    "authentication_failed",
    "invalid_token",
    "",
    None,
])

# Strategy for error messages containing dangerous keywords
# Note: These must contain the exact keywords: rate_limit, spam_detected, blocked, 429
dangerous_error_messages_strategy = st.sampled_from([
    "rate_limit: too many messages",
    "spam_detected: suspicious activity",
    "Your number has been blocked",
    "HTTP 429 Too Many Requests",
    "Error code: rate_limit",
    "Warning: spam_detected on account",
    "Account blocked due to policy violation",
    "Error 429: Rate limited",
])

# Strategy for safe error messages
safe_error_messages_strategy = st.sampled_from([
    "Connection timeout",
    "Network error occurred",
    "Invalid phone number format",
    "Server unavailable",
    "Authentication failed",
    "Unknown error",
    "",
    None,
])

# Strategy for consecutive error counts
consecutive_errors_strategy = st.integers(min_value=0, max_value=10)

# Strategy for error counts below threshold
below_consecutive_threshold_strategy = st.integers(min_value=0, max_value=2)

# Strategy for error counts at or above threshold
at_or_above_consecutive_threshold_strategy = st.integers(min_value=3, max_value=10)


class TestBanRiskDetectionProperty:
    """
    Property 7: Ban Risk Detection
    
    *For any* error code containing 'rate_limit', 'spam_detected', 'blocked',
    or '429', the system SHALL trigger an emergency pause of 30 minutes.
    
    **Feature: whatsapp-ban-prevention, Property 7: Ban Risk Detection**
    **Validates: Requirements 5.1**
    """

    @given(error_code=dangerous_error_codes_strategy)
    def test_dangerous_error_codes_trigger_ban_risk(self, error_code: str):
        """
        **Feature: whatsapp-ban-prevention, Property 7: Ban Risk Detection**
        **Validates: Requirements 5.1**
        
        For any error code containing dangerous keywords, detect_ban_risk
        should return is_ban_risk=True and action='emergency_pause'.
        """
        from app.tasks.message_tasks import detect_ban_risk, EMERGENCY_PAUSE_SECONDS
        
        result = detect_ban_risk(error_code, "Some error message")
        
        # Property: dangerous error codes should trigger ban risk
        assert result["is_ban_risk"] is True, \
            f"Expected is_ban_risk=True for error_code='{error_code}', got {result['is_ban_risk']}"
        
        assert result["action"] == "emergency_pause", \
            f"Expected action='emergency_pause' for error_code='{error_code}', got {result['action']}"
        
        assert result["pause_duration"] == EMERGENCY_PAUSE_SECONDS, \
            f"Expected pause_duration={EMERGENCY_PAUSE_SECONDS} for error_code='{error_code}', got {result['pause_duration']}"

    @given(error_message=dangerous_error_messages_strategy)
    def test_dangerous_error_messages_trigger_ban_risk(self, error_message: str):
        """
        **Feature: whatsapp-ban-prevention, Property 7: Ban Risk Detection**
        **Validates: Requirements 5.1**
        
        For any error message containing dangerous keywords, detect_ban_risk
        should return is_ban_risk=True.
        """
        from app.tasks.message_tasks import detect_ban_risk, EMERGENCY_PAUSE_SECONDS
        
        result = detect_ban_risk("generic_error", error_message)
        
        # Property: dangerous error messages should trigger ban risk
        assert result["is_ban_risk"] is True, \
            f"Expected is_ban_risk=True for error_message='{error_message}', got {result['is_ban_risk']}"
        
        assert result["action"] == "emergency_pause", \
            f"Expected action='emergency_pause' for error_message='{error_message}', got {result['action']}"

    @given(error_code=safe_error_codes_strategy, error_message=safe_error_messages_strategy)
    def test_safe_errors_do_not_trigger_ban_risk(self, error_code, error_message):
        """
        **Feature: whatsapp-ban-prevention, Property 7: Ban Risk Detection**
        **Validates: Requirements 5.1**
        
        For any error code/message NOT containing dangerous keywords,
        detect_ban_risk should return is_ban_risk=False.
        """
        from app.tasks.message_tasks import detect_ban_risk
        
        result = detect_ban_risk(error_code, error_message)
        
        # Property: safe errors should NOT trigger ban risk
        assert result["is_ban_risk"] is False, \
            f"Expected is_ban_risk=False for error_code='{error_code}', error_message='{error_message}', got {result['is_ban_risk']}"
        
        assert result["action"] == "continue", \
            f"Expected action='continue' for safe error, got {result['action']}"
        
        assert result["pause_duration"] == 0, \
            f"Expected pause_duration=0 for safe error, got {result['pause_duration']}"

    def test_detect_ban_risk_returns_dict(self):
        """
        **Feature: whatsapp-ban-prevention, Property 7: Ban Risk Detection**
        **Validates: Requirements 5.1**
        
        detect_ban_risk should always return a dictionary with required keys.
        """
        from app.tasks.message_tasks import detect_ban_risk
        
        result = detect_ban_risk("test_error", "test message")
        
        # Property: result should be a dict with required keys
        assert isinstance(result, dict), \
            f"Expected dict, got {type(result)}"
        
        required_keys = ["is_ban_risk", "action", "pause_duration"]
        for key in required_keys:
            assert key in result, \
                f"Expected key '{key}' in result, got {result.keys()}"

    def test_emergency_pause_duration_is_30_minutes(self):
        """
        **Feature: whatsapp-ban-prevention, Property 7: Ban Risk Detection**
        **Validates: Requirements 5.1**
        
        Emergency pause duration should be exactly 30 minutes (1800 seconds).
        """
        from app.tasks.message_tasks import detect_ban_risk, EMERGENCY_PAUSE_SECONDS
        
        # Verify constant value
        assert EMERGENCY_PAUSE_SECONDS == 1800, \
            f"Expected EMERGENCY_PAUSE_SECONDS=1800, got {EMERGENCY_PAUSE_SECONDS}"
        
        # Verify it's used correctly
        result = detect_ban_risk("rate_limit", "Rate limit exceeded")
        
        assert result["pause_duration"] == 1800, \
            f"Expected pause_duration=1800 (30 minutes), got {result['pause_duration']}"

    def test_case_insensitive_detection(self):
        """
        **Feature: whatsapp-ban-prevention, Property 7: Ban Risk Detection**
        **Validates: Requirements 5.1**
        
        Ban risk detection should be case-insensitive.
        """
        from app.tasks.message_tasks import detect_ban_risk
        
        # Test various case combinations
        test_cases = [
            ("RATE_LIMIT", ""),
            ("Rate_Limit", ""),
            ("rate_limit", ""),
            ("SPAM_DETECTED", ""),
            ("Spam_Detected", ""),
            ("BLOCKED", ""),
            ("Blocked", ""),
            ("", "RATE_LIMIT exceeded"),
            ("", "Spam_Detected warning"),
            ("", "user BLOCKED"),
            ("", "error 429"),
        ]
        
        for error_code, error_message in test_cases:
            result = detect_ban_risk(error_code, error_message)
            assert result["is_ban_risk"] is True, \
                f"Expected is_ban_risk=True for error_code='{error_code}', error_message='{error_message}'"

    def test_none_values_handled_gracefully(self):
        """
        **Feature: whatsapp-ban-prevention, Property 7: Ban Risk Detection**
        **Validates: Requirements 5.1**
        
        detect_ban_risk should handle None values gracefully.
        """
        from app.tasks.message_tasks import detect_ban_risk
        
        # Test with None values
        result = detect_ban_risk(None, None)
        
        assert result["is_ban_risk"] is False, \
            "Expected is_ban_risk=False for None values"
        
        result = detect_ban_risk(None, "rate_limit error")
        assert result["is_ban_risk"] is True, \
            "Expected is_ban_risk=True when error_message contains dangerous keyword"
        
        result = detect_ban_risk("rate_limit", None)
        assert result["is_ban_risk"] is True, \
            "Expected is_ban_risk=True when error_code contains dangerous keyword"


class TestConsecutiveErrorHaltProperty:
    """
    Property 8: Consecutive Error Halt
    
    *For any* sequence of 3 or more consecutive errors, the system SHALL
    halt all sending.
    
    **Feature: whatsapp-ban-prevention, Property 8: Consecutive Error Halt**
    **Validates: Requirements 5.2**
    """

    def test_check_error_thresholds_returns_dict(self):
        """
        **Feature: whatsapp-ban-prevention, Property 8: Consecutive Error Halt**
        **Validates: Requirements 5.2**
        
        check_error_thresholds should always return a dictionary with required keys.
        """
        from unittest.mock import MagicMock
        from app.tasks.message_tasks import check_error_thresholds
        
        # Create mock Redis client
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        
        result = check_error_thresholds(mock_redis)
        
        # Property: result should be a dict with required keys
        assert isinstance(result, dict), \
            f"Expected dict, got {type(result)}"
        
        required_keys = ["should_halt", "reason", "halt_duration"]
        for key in required_keys:
            assert key in result, \
                f"Expected key '{key}' in result, got {result.keys()}"

    @given(consecutive_errors=below_consecutive_threshold_strategy)
    def test_below_threshold_does_not_halt(self, consecutive_errors: int):
        """
        **Feature: whatsapp-ban-prevention, Property 8: Consecutive Error Halt**
        **Validates: Requirements 5.2**
        
        For consecutive_errors < 3, should_halt should be False.
        """
        from unittest.mock import MagicMock
        from app.tasks.message_tasks import check_error_thresholds
        
        # Create mock Redis client
        mock_redis = MagicMock()
        mock_redis.get.side_effect = lambda key: {
            "anti_ban:consecutive_errors": str(consecutive_errors).encode(),
            "anti_ban:total_sent": b"100",
            "anti_ban:total_errors": b"2",
        }.get(key, None)
        
        result = check_error_thresholds(mock_redis)
        
        # Property: below threshold should NOT halt
        assert result["should_halt"] is False, \
            f"Expected should_halt=False for {consecutive_errors} consecutive errors, got {result['should_halt']}"

    @given(consecutive_errors=at_or_above_consecutive_threshold_strategy)
    def test_at_or_above_threshold_halts(self, consecutive_errors: int):
        """
        **Feature: whatsapp-ban-prevention, Property 8: Consecutive Error Halt**
        **Validates: Requirements 5.2**
        
        For consecutive_errors >= 3, should_halt should be True.
        """
        from unittest.mock import MagicMock
        from app.tasks.message_tasks import check_error_thresholds, EXTENDED_HALT_SECONDS
        
        # Create mock Redis client
        mock_redis = MagicMock()
        mock_redis.get.side_effect = lambda key: {
            "anti_ban:consecutive_errors": str(consecutive_errors).encode(),
            "anti_ban:total_sent": b"100",
            "anti_ban:total_errors": b"5",
        }.get(key, None)
        
        result = check_error_thresholds(mock_redis)
        
        # Property: at or above threshold should halt
        assert result["should_halt"] is True, \
            f"Expected should_halt=True for {consecutive_errors} consecutive errors, got {result['should_halt']}"
        
        assert result["halt_duration"] == EXTENDED_HALT_SECONDS, \
            f"Expected halt_duration={EXTENDED_HALT_SECONDS}, got {result['halt_duration']}"
        
        assert result["reason"] is not None, \
            "Expected reason to be set when halting"

    def test_exactly_3_consecutive_errors_halts(self):
        """
        **Feature: whatsapp-ban-prevention, Property 8: Consecutive Error Halt**
        **Validates: Requirements 5.2**
        
        Exactly 3 consecutive errors should trigger a halt.
        """
        from unittest.mock import MagicMock
        from app.tasks.message_tasks import check_error_thresholds, CONSECUTIVE_ERROR_HALT_THRESHOLD
        
        # Verify threshold is 3
        assert CONSECUTIVE_ERROR_HALT_THRESHOLD == 3, \
            f"Expected CONSECUTIVE_ERROR_HALT_THRESHOLD=3, got {CONSECUTIVE_ERROR_HALT_THRESHOLD}"
        
        # Create mock Redis client with exactly 3 errors
        mock_redis = MagicMock()
        mock_redis.get.side_effect = lambda key: {
            "anti_ban:consecutive_errors": b"3",
            "anti_ban:total_sent": b"100",
            "anti_ban:total_errors": b"3",
        }.get(key, None)
        
        result = check_error_thresholds(mock_redis)
        
        assert result["should_halt"] is True, \
            "Expected should_halt=True for exactly 3 consecutive errors"

    def test_exactly_2_consecutive_errors_does_not_halt(self):
        """
        **Feature: whatsapp-ban-prevention, Property 8: Consecutive Error Halt**
        **Validates: Requirements 5.2**
        
        Exactly 2 consecutive errors should NOT trigger a halt.
        """
        from unittest.mock import MagicMock
        from app.tasks.message_tasks import check_error_thresholds
        
        # Create mock Redis client with exactly 2 errors
        mock_redis = MagicMock()
        mock_redis.get.side_effect = lambda key: {
            "anti_ban:consecutive_errors": b"2",
            "anti_ban:total_sent": b"100",
            "anti_ban:total_errors": b"2",
        }.get(key, None)
        
        result = check_error_thresholds(mock_redis)
        
        assert result["should_halt"] is False, \
            "Expected should_halt=False for exactly 2 consecutive errors"

    def test_halt_duration_is_1_hour(self):
        """
        **Feature: whatsapp-ban-prevention, Property 8: Consecutive Error Halt**
        **Validates: Requirements 5.2**
        
        Halt duration should be exactly 1 hour (3600 seconds).
        """
        from app.tasks.message_tasks import EXTENDED_HALT_SECONDS
        
        assert EXTENDED_HALT_SECONDS == 3600, \
            f"Expected EXTENDED_HALT_SECONDS=3600 (1 hour), got {EXTENDED_HALT_SECONDS}"

    def test_error_rate_warning_at_5_percent(self):
        """
        **Feature: whatsapp-ban-prevention, Property 8: Consecutive Error Halt**
        **Validates: Requirements 5.5**
        
        Error rate >= 5% should trigger a warning (but not halt).
        """
        from unittest.mock import MagicMock
        from app.tasks.message_tasks import check_error_thresholds, ERROR_RATE_WARNING_THRESHOLD
        
        # Verify threshold is 5%
        assert ERROR_RATE_WARNING_THRESHOLD == 0.05, \
            f"Expected ERROR_RATE_WARNING_THRESHOLD=0.05, got {ERROR_RATE_WARNING_THRESHOLD}"
        
        # Create mock Redis client with 5% error rate (5 errors out of 100)
        mock_redis = MagicMock()
        mock_redis.get.side_effect = lambda key: {
            "anti_ban:consecutive_errors": b"0",
            "anti_ban:total_sent": b"100",
            "anti_ban:total_errors": b"5",
        }.get(key, None)
        
        result = check_error_thresholds(mock_redis)
        
        # Should NOT halt (just warning)
        assert result["should_halt"] is False, \
            "Expected should_halt=False for 5% error rate (warning only)"
        
        # Should have warning
        assert result.get("warning") is not None, \
            "Expected warning to be set for 5% error rate"

    def test_redis_error_handled_gracefully(self):
        """
        **Feature: whatsapp-ban-prevention, Property 8: Consecutive Error Halt**
        **Validates: Requirements 5.2**
        
        Redis errors should be handled gracefully (fail-open).
        """
        from unittest.mock import MagicMock
        from app.tasks.message_tasks import check_error_thresholds
        
        # Create mock Redis client that raises an exception
        mock_redis = MagicMock()
        mock_redis.get.side_effect = Exception("Redis connection failed")
        
        result = check_error_thresholds(mock_redis)
        
        # Should NOT halt on Redis error (fail-open)
        assert result["should_halt"] is False, \
            "Expected should_halt=False when Redis fails (fail-open)"

    def test_none_redis_values_handled(self):
        """
        **Feature: whatsapp-ban-prevention, Property 8: Consecutive Error Halt**
        **Validates: Requirements 5.2**
        
        None values from Redis should be handled as 0.
        """
        from unittest.mock import MagicMock
        from app.tasks.message_tasks import check_error_thresholds
        
        # Create mock Redis client that returns None for all keys
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        
        result = check_error_thresholds(mock_redis)
        
        # Should NOT halt when no data
        assert result["should_halt"] is False, \
            "Expected should_halt=False when Redis returns None"


class TestIsSafeToSendProperty:
    """
    Property for is_safe_to_send function.
    
    *For any* combination of conditions, is_safe_to_send should correctly
    determine if sending is safe.
    
    **Feature: whatsapp-ban-prevention**
    **Validates: Requirements 4.2, 5.2, 5.3, 6.1**
    """

    def test_is_safe_to_send_returns_tuple(self):
        """
        **Feature: whatsapp-ban-prevention**
        **Validates: Requirements 4.2, 5.2, 5.3, 6.1**
        
        is_safe_to_send should always return a tuple (bool, str).
        """
        from unittest.mock import MagicMock, patch
        from datetime import datetime
        from app.tasks.message_tasks import is_safe_to_send
        
        # Create mock Redis client
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        
        # Mock datetime to be during day time
        mock_datetime = datetime(2025, 1, 1, 12, 0, 0)
        
        with patch('app.tasks.message_tasks.datetime') as mock_dt:
            mock_dt.now.return_value = mock_datetime
            mock_dt.fromisoformat = datetime.fromisoformat
            
            result = is_safe_to_send(mock_redis, 100)
        
        # Property: result should be a tuple
        assert isinstance(result, tuple), \
            f"Expected tuple, got {type(result)}"
        
        assert len(result) == 2, \
            f"Expected tuple of length 2, got {len(result)}"
        
        assert isinstance(result[0], bool), \
            f"Expected first element to be bool, got {type(result[0])}"
        
        assert isinstance(result[1], str), \
            f"Expected second element to be str, got {type(result[1])}"

    def test_blocks_during_night_time(self):
        """
        **Feature: whatsapp-ban-prevention**
        **Validates: Requirements 4.2**
        
        is_safe_to_send should block during night time (23h-6h).
        """
        from unittest.mock import MagicMock, patch
        from datetime import datetime
        from app.tasks.message_tasks import is_safe_to_send
        
        # Create mock Redis client
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        
        # Test night time hours
        night_hours = [23, 0, 1, 2, 3, 4, 5]
        
        for hour in night_hours:
            mock_datetime = datetime(2025, 1, 1, hour, 30, 0)
            
            with patch('app.tasks.message_tasks.datetime') as mock_dt:
                mock_dt.now.return_value = mock_datetime
                mock_dt.fromisoformat = datetime.fromisoformat
                
                can_send, reason = is_safe_to_send(mock_redis, 100)
            
            assert can_send is False, \
                f"Expected can_send=False during night time (hour={hour})"
            
            assert "nuit" in reason.lower() or "night" in reason.lower(), \
                f"Expected reason to mention night time, got '{reason}'"

    def test_allows_during_day_time(self):
        """
        **Feature: whatsapp-ban-prevention**
        **Validates: Requirements 4.2**
        
        is_safe_to_send should allow during day time (6h-22h).
        """
        from unittest.mock import MagicMock, patch
        from datetime import datetime
        from app.tasks.message_tasks import is_safe_to_send
        
        # Create mock Redis client
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        
        # Test day time hour
        mock_datetime = datetime(2025, 1, 1, 12, 0, 0)
        
        with patch('app.tasks.message_tasks.datetime') as mock_dt:
            mock_dt.now.return_value = mock_datetime
            mock_dt.fromisoformat = datetime.fromisoformat
            
            can_send, reason = is_safe_to_send(mock_redis, 100)
        
        assert can_send is True, \
            f"Expected can_send=True during day time, got {can_send}"
        
        assert reason == "OK", \
            f"Expected reason='OK', got '{reason}'"

    def test_blocks_at_daily_limit(self):
        """
        **Feature: whatsapp-ban-prevention**
        **Validates: Requirements 6.1**
        
        is_safe_to_send should block when daily limit (1000) is reached.
        """
        from unittest.mock import MagicMock, patch
        from datetime import datetime
        from app.tasks.message_tasks import is_safe_to_send
        
        # Create mock Redis client
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        
        # Mock datetime to be during day time
        mock_datetime = datetime(2025, 1, 1, 12, 0, 0)
        
        with patch('app.tasks.message_tasks.datetime') as mock_dt:
            mock_dt.now.return_value = mock_datetime
            mock_dt.fromisoformat = datetime.fromisoformat
            
            # Test at exactly 1000 messages
            can_send, reason = is_safe_to_send(mock_redis, 1000)
        
        assert can_send is False, \
            "Expected can_send=False at daily limit (1000)"
        
        assert "1000" in reason or "limite" in reason.lower() or "limit" in reason.lower(), \
            f"Expected reason to mention daily limit, got '{reason}'"

    def test_allows_below_daily_limit(self):
        """
        **Feature: whatsapp-ban-prevention**
        **Validates: Requirements 6.1**
        
        is_safe_to_send should allow when below daily limit.
        """
        from unittest.mock import MagicMock, patch
        from datetime import datetime
        from app.tasks.message_tasks import is_safe_to_send
        
        # Create mock Redis client
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        
        # Mock datetime to be during day time
        mock_datetime = datetime(2025, 1, 1, 12, 0, 0)
        
        with patch('app.tasks.message_tasks.datetime') as mock_dt:
            mock_dt.now.return_value = mock_datetime
            mock_dt.fromisoformat = datetime.fromisoformat
            
            # Test at 999 messages (just below limit)
            can_send, reason = is_safe_to_send(mock_redis, 999)
        
        assert can_send is True, \
            "Expected can_send=True below daily limit (999)"

    def test_blocks_on_consecutive_errors(self):
        """
        **Feature: whatsapp-ban-prevention**
        **Validates: Requirements 5.2**
        
        is_safe_to_send should block when consecutive error threshold is reached.
        """
        from unittest.mock import MagicMock, patch
        from datetime import datetime
        from app.tasks.message_tasks import is_safe_to_send
        
        # Create mock Redis client with 3 consecutive errors
        mock_redis = MagicMock()
        mock_redis.get.side_effect = lambda key: {
            "anti_ban:consecutive_errors": b"3",
            "anti_ban:total_sent": b"100",
            "anti_ban:total_errors": b"3",
            "anti_ban:emergency_pause_until": None,
        }.get(key, None)
        
        # Mock datetime to be during day time
        mock_datetime = datetime(2025, 1, 1, 12, 0, 0)
        
        with patch('app.tasks.message_tasks.datetime') as mock_dt:
            mock_dt.now.return_value = mock_datetime
            mock_dt.fromisoformat = datetime.fromisoformat
            
            can_send, reason = is_safe_to_send(mock_redis, 100)
        
        assert can_send is False, \
            "Expected can_send=False when consecutive error threshold reached"
        
        assert "erreur" in reason.lower() or "error" in reason.lower() or "urgence" in reason.lower(), \
            f"Expected reason to mention errors, got '{reason}'"
