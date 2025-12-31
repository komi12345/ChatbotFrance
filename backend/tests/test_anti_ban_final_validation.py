"""
Final Validation Tests for Anti-Ban System.

This test module validates the complete anti-ban implementation by:
1. Running all property-based tests
2. Verifying delay calculations for a simulated 10-message sequence
3. Confirming that delays are correctly applied

**Feature: whatsapp-ban-prevention**
**Task: 14. Final checkpoint - Validation complète**
"""
import pytest
import time
from datetime import datetime
from unittest.mock import MagicMock, patch


class TestAntiBanDelayValidation:
    """
    Validation tests for anti-ban delay calculations.
    
    Verifies that delays are correctly calculated and applied
    for a sequence of 10 messages.
    """

    def test_10_message_delay_sequence(self):
        """
        Test that a sequence of 10 messages has correct delays applied.
        
        This simulates sending 10 messages and verifies:
        1. Each delay is within the expected bounds
        2. Total time is significantly longer than without anti-ban
        3. Delays vary (randomization is working)
        """
        from app.tasks.message_tasks import get_anti_ban_delay, ANTI_BAN_MIN_DELAY
        
        delays = []
        messages_sent_today = 0
        
        # Simulate sending 10 messages
        for i in range(10):
            delay = get_anti_ban_delay(messages_sent_today)
            delays.append(delay)
            messages_sent_today += 1
        
        # Verify all delays are within bounds
        for i, delay in enumerate(delays):
            assert delay >= ANTI_BAN_MIN_DELAY, \
                f"Message {i+1}: delay {delay:.2f}s is below minimum {ANTI_BAN_MIN_DELAY}s"
            assert delay <= 43, \
                f"Message {i+1}: delay {delay:.2f}s exceeds maximum 43s"
        
        # Verify total time is significant (at least 10 * 10s = 100s)
        total_delay = sum(delays)
        assert total_delay >= 100, \
            f"Total delay {total_delay:.2f}s is too short (expected >= 100s)"
        
        # Verify delays vary (randomization is working)
        unique_delays = len(set(round(d, 1) for d in delays))
        assert unique_delays >= 3, \
            f"Only {unique_delays} unique delays - randomization may not be working"
        
        # Log the results for verification
        print(f"\n=== 10 Message Delay Sequence ===")
        for i, delay in enumerate(delays):
            print(f"Message {i+1}: {delay:.2f}s")
        print(f"Total delay: {total_delay:.2f}s ({total_delay/60:.1f} minutes)")
        print(f"Average delay: {total_delay/10:.2f}s")
        print(f"Unique delays: {unique_delays}")

    def test_warm_up_phases_in_sequence(self):
        """
        Test that warm-up phases are correctly applied as message count increases.
        """
        from app.tasks.message_tasks import get_warm_up_delay
        
        # Test each phase boundary
        phase_tests = [
            (0, 25, 35, "Phase 1 (0-29)"),
            (29, 25, 35, "Phase 1 boundary"),
            (30, 20, 28, "Phase 2 (30-79)"),
            (79, 20, 28, "Phase 2 boundary"),
            (80, 15, 22, "Phase 3 (80-199)"),
            (199, 15, 22, "Phase 3 boundary"),
            (200, 18, 25, "Phase 4 (200-499)"),
            (499, 18, 25, "Phase 4 boundary"),
            (500, 22, 30, "Phase 5 (500+)"),
            (1000, 22, 30, "Phase 5 high"),
        ]
        
        print(f"\n=== Warm-Up Phase Validation ===")
        for messages_sent, min_expected, max_expected, phase_name in phase_tests:
            delay = get_warm_up_delay(messages_sent)
            assert min_expected <= delay <= max_expected, \
                f"{phase_name}: delay {delay:.2f}s not in [{min_expected}, {max_expected}]"
            print(f"{phase_name} (N={messages_sent}): {delay:.2f}s ✓")

    def test_strategic_pause_triggers(self):
        """
        Test that strategic pauses are triggered at correct thresholds.
        """
        from app.tasks.message_tasks import (
            should_take_strategic_pause,
            get_strategic_pause_duration,
            PAUSE_THRESHOLD_1, PAUSE_THRESHOLD_2, PAUSE_THRESHOLD_3, PAUSE_THRESHOLD_4
        )
        
        print(f"\n=== Strategic Pause Validation ===")
        
        # Test threshold triggers
        thresholds = [
            (PAUSE_THRESHOLD_1, True, "Threshold 1 (20)"),
            (PAUSE_THRESHOLD_2, True, "Threshold 2 (40)"),
            (PAUSE_THRESHOLD_3, True, "Threshold 3 (60)"),
            (PAUSE_THRESHOLD_4, True, "Threshold 4 (100)"),
            (19, False, "Below threshold 1"),
            (21, False, "Between thresholds"),
            (50, False, "Between thresholds"),
        ]
        
        for count, expected, name in thresholds:
            result = should_take_strategic_pause(count)
            assert result == expected, \
                f"{name}: expected {expected}, got {result}"
            print(f"{name} (N={count}): pause={result} ✓")
        
        # Test pause durations
        print(f"\n=== Pause Duration Validation ===")
        duration_tests = [
            (20, 180, 300, "3-5 minutes"),
            (40, 300, 480, "5-8 minutes"),
            (60, 600, 900, "10-15 minutes"),
            (100, 1200, 1800, "20-30 minutes"),
        ]
        
        for count, min_dur, max_dur, expected_range in duration_tests:
            duration = get_strategic_pause_duration(count)
            assert min_dur <= duration <= max_dur, \
                f"Threshold {count}: duration {duration:.0f}s not in [{min_dur}, {max_dur}]"
            print(f"Threshold {count}: {duration/60:.1f} minutes ({expected_range}) ✓")

    def test_human_behavior_simulation(self):
        """
        Test that human behavior simulation functions work correctly.
        """
        from app.tasks.message_tasks import (
            simulate_human_behavior,
            get_message_length_delay,
            MICRO_PAUSE_PROBABILITY,
            MICRO_PAUSE_DURATION
        )
        
        print(f"\n=== Human Behavior Simulation ===")
        
        # Test micro-pause probability (run 1000 times)
        micro_pauses = 0
        for _ in range(1000):
            pause = simulate_human_behavior()
            if pause > 0:
                micro_pauses += 1
                # Verify pause is within bounds
                assert MICRO_PAUSE_DURATION[0] <= pause <= MICRO_PAUSE_DURATION[1], \
                    f"Micro-pause {pause:.0f}s not in expected range"
        
        # Verify probability is approximately 10% (allow 5-15% range)
        actual_probability = micro_pauses / 1000
        assert 0.05 <= actual_probability <= 0.15, \
            f"Micro-pause probability {actual_probability:.1%} not near expected 10%"
        print(f"Micro-pause probability: {actual_probability:.1%} (expected ~10%) ✓")
        
        # Test message length delay
        length_tests = [
            (0, 0, 0, "Empty message"),
            (500, 1, 1, "500 chars"),
            (1000, 2, 2, "1000 chars"),
            (2500, 5, 5, "2500 chars"),
            (5000, 5, 5, "5000 chars (max)"),
        ]
        
        print(f"\n=== Message Length Delay ===")
        for length, min_delay, max_delay, name in length_tests:
            delay = get_message_length_delay(length)
            assert min_delay <= delay <= max_delay, \
                f"{name}: delay {delay:.2f}s not in [{min_delay}, {max_delay}]"
            print(f"{name} ({length} chars): {delay:.2f}s ✓")

    def test_ban_risk_detection(self):
        """
        Test that ban risk detection correctly identifies dangerous error codes.
        """
        from app.tasks.message_tasks import (
            detect_ban_risk,
            BAN_RISK_ERROR_CODES,
            EMERGENCY_PAUSE_SECONDS
        )
        
        print(f"\n=== Ban Risk Detection ===")
        
        # Test dangerous error codes
        for code in BAN_RISK_ERROR_CODES:
            result = detect_ban_risk(code, "")
            assert result["is_ban_risk"] is True, \
                f"Error code '{code}' should trigger ban risk"
            assert result["action"] == "emergency_pause", \
                f"Error code '{code}' should trigger emergency_pause"
            assert result["pause_duration"] == EMERGENCY_PAUSE_SECONDS, \
                f"Error code '{code}' should have 30-minute pause"
            print(f"Error code '{code}': detected ✓")
        
        # Test safe error codes
        safe_codes = ["network_error", "timeout", "invalid_number", "unknown"]
        for code in safe_codes:
            result = detect_ban_risk(code, "")
            assert result["is_ban_risk"] is False, \
                f"Error code '{code}' should NOT trigger ban risk"
            print(f"Safe code '{code}': not detected ✓")

    def test_is_safe_to_send_validation(self):
        """
        Test that is_safe_to_send correctly validates all conditions.
        """
        from app.tasks.message_tasks import is_safe_to_send
        
        print(f"\n=== is_safe_to_send Validation ===")
        
        # Mock Redis client
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        
        # Test daily limit enforcement
        with patch('app.tasks.message_tasks.is_night_time', return_value=False):
            with patch('app.tasks.message_tasks.check_error_thresholds', return_value={
                "should_halt": False,
                "reason": None,
                "halt_duration": 0,
                "warning": None
            }):
                # Below limit - should allow
                can_send, reason = is_safe_to_send(mock_redis, 999)
                assert can_send is True, f"Should allow at 999 messages, got: {reason}"
                print(f"999 messages: allowed ✓")
                
                # At limit - should block
                can_send, reason = is_safe_to_send(mock_redis, 1000)
                assert can_send is False, "Should block at 1000 messages"
                assert "1000" in reason or "limite" in reason.lower()
                print(f"1000 messages: blocked ✓")
                
                # Above limit - should block
                can_send, reason = is_safe_to_send(mock_redis, 1500)
                assert can_send is False, "Should block at 1500 messages"
                print(f"1500 messages: blocked ✓")

    def test_celery_configuration(self):
        """
        Test that Celery is configured correctly for anti-ban mode.
        """
        from app.tasks.celery_app import celery_app
        
        print(f"\n=== Celery Configuration Validation ===")
        
        # Verify anti-ban settings
        config = celery_app.conf
        
        # Requirements 7.1: Single worker
        assert config.worker_concurrency == 1, \
            f"worker_concurrency should be 1, got {config.worker_concurrency}"
        print(f"worker_concurrency: {config.worker_concurrency} ✓")
        
        # Requirements 7.2: No prefetching
        assert config.worker_prefetch_multiplier == 1, \
            f"worker_prefetch_multiplier should be 1, got {config.worker_prefetch_multiplier}"
        print(f"worker_prefetch_multiplier: {config.worker_prefetch_multiplier} ✓")
        
        # Requirements 7.3: Rate limit 4/m
        assert config.task_default_rate_limit == "4/m", \
            f"task_default_rate_limit should be '4/m', got {config.task_default_rate_limit}"
        print(f"task_default_rate_limit: {config.task_default_rate_limit} ✓")
        
        # Requirements 7.5: Soft time limit 300s
        assert config.task_soft_time_limit == 300, \
            f"task_soft_time_limit should be 300, got {config.task_soft_time_limit}"
        print(f"task_soft_time_limit: {config.task_soft_time_limit}s ✓")
        
        # Hard time limit 600s
        assert config.task_time_limit == 600, \
            f"task_time_limit should be 600, got {config.task_time_limit}"
        print(f"task_time_limit: {config.task_time_limit}s ✓")

    def test_estimated_send_time_calculation(self):
        """
        Calculate and verify estimated send time for different message counts.
        """
        from app.tasks.message_tasks import get_anti_ban_delay
        
        print(f"\n=== Estimated Send Time Calculation ===")
        
        test_counts = [10, 100, 500, 1000]
        
        for count in test_counts:
            # Calculate average delay for this count
            total_delay = 0
            for i in range(count):
                total_delay += get_anti_ban_delay(i)
            
            # Add strategic pauses (approximately)
            # 20 messages: 3-5 min, 40: 5-8 min, 60: 10-15 min, 100: 20-30 min
            strategic_pauses = 0
            if count >= 20:
                strategic_pauses += 240  # ~4 min
            if count >= 40:
                strategic_pauses += 390  # ~6.5 min
            if count >= 60:
                strategic_pauses += 750  # ~12.5 min
            if count >= 100:
                strategic_pauses += 1500  # ~25 min
            
            total_time = total_delay + strategic_pauses
            hours = total_time / 3600
            minutes = (total_time % 3600) / 60
            
            print(f"{count} messages: ~{hours:.1f}h {minutes:.0f}m (delays: {total_delay/60:.0f}min, pauses: {strategic_pauses/60:.0f}min)")
        
        # Verify 1000 messages takes significantly longer than before
        # Before: ~1h42min (5s per message)
        # After: ~8h (with anti-ban)
        assert total_delay > 5000, \
            f"1000 messages should take much longer than before (got {total_delay/60:.0f} min delays)"


class TestAntiBanIntegration:
    """
    Integration tests for the complete anti-ban system.
    """

    def test_idempotency_key_generation(self):
        """
        Test that idempotency keys are correctly generated.
        """
        from app.tasks.message_tasks import get_idempotency_key
        
        print(f"\n=== Idempotency Key Generation ===")
        
        # Test key format
        key1 = get_idempotency_key(123, "send")
        assert key1 == "idempotency:send:123", f"Unexpected key format: {key1}"
        print(f"Key for message 123, send: {key1} ✓")
        
        key2 = get_idempotency_key(456, "retry")
        assert key2 == "idempotency:retry:456", f"Unexpected key format: {key2}"
        print(f"Key for message 456, retry: {key2} ✓")
        
        # Test uniqueness
        assert key1 != key2, "Keys should be unique"
        print(f"Keys are unique ✓")

    def test_env_variables_documented(self):
        """
        Test that all anti-ban environment variables are documented in .env.example.
        """
        import os
        
        print(f"\n=== Environment Variables Documentation ===")
        
        env_example_path = os.path.join(os.path.dirname(__file__), '..', '.env.example')
        
        if os.path.exists(env_example_path):
            with open(env_example_path, 'r') as f:
                env_content = f.read()
            
            required_vars = [
                "ANTI_BAN_BASE_DELAY_MIN",
                "ANTI_BAN_BASE_DELAY_MAX",
                "ANTI_BAN_RANDOM_VARIATION",
                "ANTI_BAN_MIN_DELAY",
                "ANTI_BAN_BATCH_SIZE",
            ]
            
            for var in required_vars:
                assert var in env_content, \
                    f"Environment variable {var} not documented in .env.example"
                print(f"{var}: documented ✓")
        else:
            print(f"Warning: .env.example not found at {env_example_path}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
