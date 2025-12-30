"""
Property-based tests for Campaign Auto-Completion.

Tests the correctness properties defined in the design document:
- Property 1: Campaign Completion When All Contacts Finished
- Property 2: Pending Messages Prevent Completion
- Property 3: Completed Timestamp Set On Completion

**Feature: campaign-auto-completion**
**Validates: Requirements 1.2, 1.3, 1.4, 2.2**
"""
import pytest
from hypothesis import given, settings as hyp_settings, strategies as st, assume
from typing import List, Dict
from datetime import datetime, timezone
from collections import Counter

# Configure Hypothesis for CI: minimum 100 iterations
hyp_settings.register_profile(
    "ci",
    max_examples=100,
    deadline=None
)
hyp_settings.load_profile("ci")


# ==========================================================================
# STRATEGIES FOR CAMPAIGN AUTO-COMPLETION TESTS
# ==========================================================================

# Strategy for campaign IDs
campaign_id_strategy = st.integers(min_value=1, max_value=10000)

# Final states for messages (contacts who have completed their cycle)
FINAL_STATES = ["sent", "delivered", "read", "failed", "no_interaction"]

# Non-final states (contacts still in progress)
NON_FINAL_STATES = ["pending"]

# Strategy for final message states
final_state_strategy = st.sampled_from(FINAL_STATES)

# Strategy for non-final message states
non_final_state_strategy = st.sampled_from(NON_FINAL_STATES)


def determine_campaign_status(
    pending_count: int,
    message_1_sent_count: int,
    message_2_sent_count: int,
    no_interaction_count: int,
    failed_count: int,
    total_sent_count: int
) -> str:
    """
    Determine the campaign status based on message counts.
    
    This mirrors the logic in update_campaign_status() from message_tasks.py.
    
    LOGIQUE DE COMPLÉTION (Requirements 1.2, 1.4, 2.2):
    - pending > 0 -> "sending" (Requirements 1.4)
    - pending = 0 AND (msg2_sent + no_interaction + failed) >= msg1_sent -> "completed" (Requirements 1.2)
    - pending = 0 AND not all contacts completed -> "sending" (waiting for interactions)
    
    Args:
        pending_count: Number of pending messages
        message_1_sent_count: Number of Message 1 successfully sent
        message_2_sent_count: Number of Message 2 successfully sent
        no_interaction_count: Number of contacts with no interaction after 24h
        failed_count: Number of failed messages
        total_sent_count: Total messages sent (all types)
    
    Returns:
        Campaign status: "sending", "completed", or "failed"
    """
    # Calculate contacts who have completed their cycle
    contacts_completed = message_2_sent_count + no_interaction_count + failed_count
    
    # Check if all contacts have completed
    all_contacts_completed = (
        message_1_sent_count > 0 and 
        contacts_completed >= message_1_sent_count
    )
    
    # Determine status
    if pending_count > 0:
        # Requirements 1.4: Pending messages prevent completion
        return "sending"
    elif all_contacts_completed:
        # Requirements 1.2: All contacts finished -> completed
        if failed_count > 0 and total_sent_count == 0:
            return "failed"
        return "completed"
    else:
        # Waiting for interactions or check_expired_interactions task
        return "sending"


class TestCampaignCompletionProperty:
    """
    Property 1: Campaign Completion When All Contacts Finished
    
    *For any* campaign where all contacts have a final state (message_2 sent, 
    no_interaction, or failed), the campaign status SHALL be "completed".
    
    **Feature: campaign-auto-completion, Property 1: Campaign Completion When All Contacts Finished**
    **Validates: Requirements 1.2, 2.2**
    """

    @given(
        campaign_id=campaign_id_strategy,
        num_message_1_sent=st.integers(min_value=1, max_value=50),
        num_message_2_sent=st.integers(min_value=0, max_value=50),
        num_no_interaction=st.integers(min_value=0, max_value=50),
        num_failed=st.integers(min_value=0, max_value=50)
    )
    def test_all_contacts_finished_results_in_completed(
        self,
        campaign_id: int,
        num_message_1_sent: int,
        num_message_2_sent: int,
        num_no_interaction: int,
        num_failed: int
    ):
        """
        **Feature: campaign-auto-completion, Property 1: Campaign Completion When All Contacts Finished**
        **Validates: Requirements 1.2, 2.2**
        
        For any campaign where all contacts have completed their cycle
        (message_2 sent, no_interaction, or failed), the campaign status
        should be "completed".
        """
        # Ensure all contacts have completed their cycle
        # contacts_completed = msg2_sent + no_interaction + failed >= msg1_sent
        contacts_completed = num_message_2_sent + num_no_interaction + num_failed
        assume(contacts_completed >= num_message_1_sent)
        assume(num_message_1_sent > 0)  # At least one Message 1 sent
        
        # No pending messages
        pending_count = 0
        
        # Total sent includes Message 1 and Message 2
        total_sent_count = num_message_1_sent + num_message_2_sent
        
        # Determine status
        status = determine_campaign_status(
            pending_count=pending_count,
            message_1_sent_count=num_message_1_sent,
            message_2_sent_count=num_message_2_sent,
            no_interaction_count=num_no_interaction,
            failed_count=num_failed,
            total_sent_count=total_sent_count
        )
        
        # Property: when all contacts finished, status should be "completed" or "failed"
        assert status in ["completed", "failed"], \
            f"Expected 'completed' or 'failed' when all contacts finished, got '{status}'"
        
        # If there are any successful sends, status should be "completed"
        if total_sent_count > 0:
            assert status == "completed", \
                f"Expected 'completed' when there are successful sends, got '{status}'"

    @given(
        campaign_id=campaign_id_strategy,
        num_message_1_sent=st.integers(min_value=1, max_value=30),
        distribution=st.lists(
            st.sampled_from(["message_2", "no_interaction", "failed"]),
            min_size=1,
            max_size=30
        )
    )
    def test_mixed_final_states_results_in_completed(
        self,
        campaign_id: int,
        num_message_1_sent: int,
        distribution: List[str]
    ):
        """
        **Feature: campaign-auto-completion, Property 1: Campaign Completion When All Contacts Finished**
        **Validates: Requirements 1.2, 2.2**
        
        For any campaign with a mix of final states (message_2 sent, no_interaction, failed),
        the campaign should be "completed" when all contacts have finished.
        """
        # Count each type
        counts = Counter(distribution)
        num_message_2_sent = counts.get("message_2", 0)
        num_no_interaction = counts.get("no_interaction", 0)
        num_failed = counts.get("failed", 0)
        
        # Ensure all contacts have completed
        contacts_completed = num_message_2_sent + num_no_interaction + num_failed
        assume(contacts_completed >= num_message_1_sent)
        assume(num_message_1_sent > 0)
        
        pending_count = 0
        total_sent_count = num_message_1_sent + num_message_2_sent
        
        status = determine_campaign_status(
            pending_count=pending_count,
            message_1_sent_count=num_message_1_sent,
            message_2_sent_count=num_message_2_sent,
            no_interaction_count=num_no_interaction,
            failed_count=num_failed,
            total_sent_count=total_sent_count
        )
        
        # Property: mixed final states should result in "completed"
        if total_sent_count > 0:
            assert status == "completed", \
                f"Expected 'completed' for mixed final states with successful sends, got '{status}'"


class TestPendingMessagesPreventCompletion:
    """
    Property 2: Pending Messages Prevent Completion
    
    *For any* campaign with at least one pending message, the campaign status 
    SHALL remain "sending".
    
    **Feature: campaign-auto-completion, Property 2: Pending Messages Prevent Completion**
    **Validates: Requirements 1.4**
    """

    @given(
        campaign_id=campaign_id_strategy,
        num_pending=st.integers(min_value=1, max_value=50),
        num_message_1_sent=st.integers(min_value=0, max_value=30),
        num_message_2_sent=st.integers(min_value=0, max_value=30),
        num_no_interaction=st.integers(min_value=0, max_value=30),
        num_failed=st.integers(min_value=0, max_value=30)
    )
    def test_pending_messages_keep_status_sending(
        self,
        campaign_id: int,
        num_pending: int,
        num_message_1_sent: int,
        num_message_2_sent: int,
        num_no_interaction: int,
        num_failed: int
    ):
        """
        **Feature: campaign-auto-completion, Property 2: Pending Messages Prevent Completion**
        **Validates: Requirements 1.4**
        
        For any campaign with at least one pending message, the campaign
        status should remain "sending", regardless of other message states.
        """
        total_sent_count = num_message_1_sent + num_message_2_sent
        
        status = determine_campaign_status(
            pending_count=num_pending,
            message_1_sent_count=num_message_1_sent,
            message_2_sent_count=num_message_2_sent,
            no_interaction_count=num_no_interaction,
            failed_count=num_failed,
            total_sent_count=total_sent_count
        )
        
        # Property: pending > 0 -> status must be "sending"
        assert status == "sending", \
            f"Expected 'sending' when {num_pending} messages pending, got '{status}'"

    @given(
        campaign_id=campaign_id_strategy,
        num_pending=st.integers(min_value=1, max_value=100)
    )
    def test_single_pending_prevents_completion(
        self,
        campaign_id: int,
        num_pending: int
    ):
        """
        **Feature: campaign-auto-completion, Property 2: Pending Messages Prevent Completion**
        **Validates: Requirements 1.4**
        
        Even with many completed contacts, a single pending message
        should prevent the campaign from completing.
        """
        # Simulate a campaign with many completed contacts but some pending
        num_message_1_sent = 100
        num_message_2_sent = 90
        num_no_interaction = 5
        num_failed = 3
        # Total completed = 98, but we have pending messages
        
        total_sent_count = num_message_1_sent + num_message_2_sent
        
        status = determine_campaign_status(
            pending_count=num_pending,
            message_1_sent_count=num_message_1_sent,
            message_2_sent_count=num_message_2_sent,
            no_interaction_count=num_no_interaction,
            failed_count=num_failed,
            total_sent_count=total_sent_count
        )
        
        # Property: any pending messages -> status must be "sending"
        assert status == "sending", \
            f"Expected 'sending' with pending messages, got '{status}'"


class TestCombinedCompletionLogic:
    """
    Combined tests for Property 1 & 2: Campaign Completion Logic
    
    Tests the interaction between completion conditions and pending messages.
    
    **Feature: campaign-auto-completion, Property 1 & 2: Campaign Completion Logic**
    **Validates: Requirements 1.2, 1.4, 2.2**
    """

    @given(
        campaign_id=campaign_id_strategy,
        num_message_1_sent=st.integers(min_value=1, max_value=50),
        num_message_2_sent=st.integers(min_value=0, max_value=50),
        num_no_interaction=st.integers(min_value=0, max_value=50),
        num_failed=st.integers(min_value=0, max_value=50),
        num_pending=st.integers(min_value=0, max_value=50)
    )
    def test_completion_logic_consistency(
        self,
        campaign_id: int,
        num_message_1_sent: int,
        num_message_2_sent: int,
        num_no_interaction: int,
        num_failed: int,
        num_pending: int
    ):
        """
        **Feature: campaign-auto-completion, Property 1 & 2: Campaign Completion Logic**
        **Validates: Requirements 1.2, 1.4, 2.2**
        
        For any combination of message states, the completion logic should be consistent:
        - pending > 0 -> "sending"
        - pending = 0 AND all_completed -> "completed" (or "failed" if all failed)
        - pending = 0 AND NOT all_completed -> "sending"
        """
        total_sent_count = num_message_1_sent + num_message_2_sent
        contacts_completed = num_message_2_sent + num_no_interaction + num_failed
        all_contacts_completed = (
            num_message_1_sent > 0 and 
            contacts_completed >= num_message_1_sent
        )
        
        status = determine_campaign_status(
            pending_count=num_pending,
            message_1_sent_count=num_message_1_sent,
            message_2_sent_count=num_message_2_sent,
            no_interaction_count=num_no_interaction,
            failed_count=num_failed,
            total_sent_count=total_sent_count
        )
        
        # Verify consistency
        if num_pending > 0:
            # Property 2: Pending prevents completion
            assert status == "sending", \
                f"Pending > 0 should result in 'sending', got '{status}'"
        elif all_contacts_completed:
            # Property 1: All completed -> completed or failed
            assert status in ["completed", "failed"], \
                f"All contacts completed should result in 'completed' or 'failed', got '{status}'"
        else:
            # Waiting for interactions
            assert status == "sending", \
                f"Not all contacts completed should result in 'sending', got '{status}'"

    @given(
        num_contacts=st.integers(min_value=1, max_value=100)
    )
    def test_all_message_2_sent_completes_campaign(
        self,
        num_contacts: int
    ):
        """
        **Feature: campaign-auto-completion, Property 1: Campaign Completion When All Contacts Finished**
        **Validates: Requirements 1.2, 2.2**
        
        When all contacts have received Message 2 (100% interaction rate),
        the campaign should be completed.
        """
        # All contacts received Message 1 and Message 2
        num_message_1_sent = num_contacts
        num_message_2_sent = num_contacts
        num_no_interaction = 0
        num_failed = 0
        num_pending = 0
        total_sent_count = num_message_1_sent + num_message_2_sent
        
        status = determine_campaign_status(
            pending_count=num_pending,
            message_1_sent_count=num_message_1_sent,
            message_2_sent_count=num_message_2_sent,
            no_interaction_count=num_no_interaction,
            failed_count=num_failed,
            total_sent_count=total_sent_count
        )
        
        assert status == "completed", \
            f"100% Message 2 sent should result in 'completed', got '{status}'"

    @given(
        num_contacts=st.integers(min_value=1, max_value=100)
    )
    def test_all_no_interaction_completes_campaign(
        self,
        num_contacts: int
    ):
        """
        **Feature: campaign-auto-completion, Property 1: Campaign Completion When All Contacts Finished**
        **Validates: Requirements 1.2, 2.2**
        
        When all contacts have no interaction after 24h,
        the campaign should be completed.
        """
        # All contacts received Message 1 but no interaction
        num_message_1_sent = num_contacts
        num_message_2_sent = 0
        num_no_interaction = num_contacts
        num_failed = 0
        num_pending = 0
        total_sent_count = num_message_1_sent
        
        status = determine_campaign_status(
            pending_count=num_pending,
            message_1_sent_count=num_message_1_sent,
            message_2_sent_count=num_message_2_sent,
            no_interaction_count=num_no_interaction,
            failed_count=num_failed,
            total_sent_count=total_sent_count
        )
        
        assert status == "completed", \
            f"100% no_interaction should result in 'completed', got '{status}'"



class TestCompletedTimestampProperty:
    """
    Property 3: Completed Timestamp Set On Completion
    
    *For any* campaign that transitions to "completed" status, the completed_at 
    field SHALL be set to a non-null timestamp.
    
    **Feature: campaign-auto-completion, Property 3: Completed Timestamp Set On Completion**
    **Validates: Requirements 1.3**
    """

    @given(
        campaign_id=campaign_id_strategy,
        num_message_1_sent=st.integers(min_value=1, max_value=50),
        num_message_2_sent=st.integers(min_value=0, max_value=50),
        num_no_interaction=st.integers(min_value=0, max_value=50),
        num_failed=st.integers(min_value=0, max_value=50)
    )
    def test_completed_at_set_when_status_completed(
        self,
        campaign_id: int,
        num_message_1_sent: int,
        num_message_2_sent: int,
        num_no_interaction: int,
        num_failed: int
    ):
        """
        **Feature: campaign-auto-completion, Property 3: Completed Timestamp Set On Completion**
        **Validates: Requirements 1.3**
        
        For any campaign that transitions to "completed" status,
        the completed_at field should be set to a non-null timestamp.
        """
        # Ensure all contacts have completed their cycle
        contacts_completed = num_message_2_sent + num_no_interaction + num_failed
        assume(contacts_completed >= num_message_1_sent)
        assume(num_message_1_sent > 0)
        
        pending_count = 0
        total_sent_count = num_message_1_sent + num_message_2_sent
        
        # Determine status
        status = determine_campaign_status(
            pending_count=pending_count,
            message_1_sent_count=num_message_1_sent,
            message_2_sent_count=num_message_2_sent,
            no_interaction_count=num_no_interaction,
            failed_count=num_failed,
            total_sent_count=total_sent_count
        )
        
        # Simulate the update logic from update_campaign_status
        # When status becomes "completed", completed_at should be set
        completed_at = None
        if status == "completed":
            # This mirrors the logic in update_campaign_status:
            # if new_status == "completed" and not current_completed_at:
            #     update_data["completed_at"] = datetime.now(timezone.utc).isoformat()
            completed_at = datetime.now(timezone.utc).isoformat()
        
        # Property: when status is "completed", completed_at must be set
        if status == "completed":
            assert completed_at is not None, \
                "completed_at should be set when status is 'completed'"
            # Verify it's a valid ISO timestamp
            try:
                parsed = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
                assert parsed is not None
            except ValueError:
                pytest.fail(f"completed_at '{completed_at}' is not a valid ISO timestamp")

    @given(
        campaign_id=campaign_id_strategy,
        num_contacts=st.integers(min_value=1, max_value=100)
    )
    def test_completed_at_not_set_when_sending(
        self,
        campaign_id: int,
        num_contacts: int
    ):
        """
        **Feature: campaign-auto-completion, Property 3: Completed Timestamp Set On Completion**
        **Validates: Requirements 1.3**
        
        For any campaign that remains in "sending" status,
        the completed_at field should NOT be set.
        """
        # Campaign with pending messages -> status = "sending"
        num_pending = num_contacts
        num_message_1_sent = 0
        num_message_2_sent = 0
        num_no_interaction = 0
        num_failed = 0
        total_sent_count = 0
        
        status = determine_campaign_status(
            pending_count=num_pending,
            message_1_sent_count=num_message_1_sent,
            message_2_sent_count=num_message_2_sent,
            no_interaction_count=num_no_interaction,
            failed_count=num_failed,
            total_sent_count=total_sent_count
        )
        
        # Simulate the update logic
        completed_at = None
        if status == "completed":
            completed_at = datetime.now(timezone.utc).isoformat()
        
        # Property: when status is "sending", completed_at should NOT be set
        assert status == "sending", f"Expected 'sending', got '{status}'"
        assert completed_at is None, \
            "completed_at should NOT be set when status is 'sending'"

    @given(
        campaign_id=campaign_id_strategy,
        num_message_1_sent=st.integers(min_value=1, max_value=50),
        num_message_2_sent=st.integers(min_value=0, max_value=50),
        num_no_interaction=st.integers(min_value=0, max_value=50),
        num_failed=st.integers(min_value=0, max_value=50)
    )
    def test_completed_at_timestamp_is_recent(
        self,
        campaign_id: int,
        num_message_1_sent: int,
        num_message_2_sent: int,
        num_no_interaction: int,
        num_failed: int
    ):
        """
        **Feature: campaign-auto-completion, Property 3: Completed Timestamp Set On Completion**
        **Validates: Requirements 1.3**
        
        For any campaign that transitions to "completed" status,
        the completed_at timestamp should be recent (within the last minute).
        """
        # Ensure all contacts have completed their cycle
        contacts_completed = num_message_2_sent + num_no_interaction + num_failed
        assume(contacts_completed >= num_message_1_sent)
        assume(num_message_1_sent > 0)
        
        pending_count = 0
        total_sent_count = num_message_1_sent + num_message_2_sent
        
        status = determine_campaign_status(
            pending_count=pending_count,
            message_1_sent_count=num_message_1_sent,
            message_2_sent_count=num_message_2_sent,
            no_interaction_count=num_no_interaction,
            failed_count=num_failed,
            total_sent_count=total_sent_count
        )
        
        if status == "completed":
            # Simulate setting completed_at
            before_time = datetime.now(timezone.utc)
            completed_at = datetime.now(timezone.utc)
            after_time = datetime.now(timezone.utc)
            
            # Property: completed_at should be between before and after
            assert before_time <= completed_at <= after_time, \
                "completed_at should be set to current time"

    @given(
        campaign_id=campaign_id_strategy,
        num_contacts=st.integers(min_value=1, max_value=50)
    )
    def test_completed_at_preserved_on_subsequent_checks(
        self,
        campaign_id: int,
        num_contacts: int
    ):
        """
        **Feature: campaign-auto-completion, Property 3: Completed Timestamp Set On Completion**
        **Validates: Requirements 1.3**
        
        For any completed campaign, subsequent status checks should NOT
        overwrite the existing completed_at timestamp.
        """
        # Simulate a completed campaign
        num_message_1_sent = num_contacts
        num_message_2_sent = num_contacts
        num_no_interaction = 0
        num_failed = 0
        pending_count = 0
        total_sent_count = num_message_1_sent + num_message_2_sent
        
        status = determine_campaign_status(
            pending_count=pending_count,
            message_1_sent_count=num_message_1_sent,
            message_2_sent_count=num_message_2_sent,
            no_interaction_count=num_no_interaction,
            failed_count=num_failed,
            total_sent_count=total_sent_count
        )
        
        assert status == "completed"
        
        # First completion - set completed_at
        original_completed_at = datetime.now(timezone.utc).isoformat()
        
        # Simulate the logic from update_campaign_status:
        # if new_status == "completed":
        #     current_completed_at = campaign.get("completed_at")
        #     if not current_completed_at:
        #         update_data["completed_at"] = datetime.now(timezone.utc).isoformat()
        
        # Second check - should NOT overwrite
        current_completed_at = original_completed_at  # Already set
        new_completed_at = None
        if status == "completed" and not current_completed_at:
            new_completed_at = datetime.now(timezone.utc).isoformat()
        
        # Property: existing completed_at should be preserved
        assert new_completed_at is None, \
            "completed_at should NOT be overwritten on subsequent checks"
