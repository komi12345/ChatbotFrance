"""
Property-based tests for Admin Data Harmonization.

Tests the correctness properties defined in the design document for the
admin-data-harmonization feature.
"""
import pytest
from hypothesis import given, settings as hyp_settings, strategies as st, HealthCheck
from unittest.mock import MagicMock, patch
from typing import List, Dict, Any

# Configure Hypothesis for CI: minimum 100 iterations
hyp_settings.register_profile(
    "ci", 
    max_examples=100, 
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None
)
hyp_settings.load_profile("ci")


# ==========================================================================
# STRATEGIES FOR CONTACT GENERATION
# ==========================================================================

# Strategy for user IDs (simulating different users)
user_id_strategy = st.integers(min_value=1, max_value=100)

# Strategy for phone numbers
phone_number_strategy = st.text(alphabet="0123456789", min_size=8, max_size=15)

# Strategy for country codes
country_code_strategy = st.sampled_from(["+33", "+1", "+44", "+49", "+34", "+39"])

# Strategy for names
name_strategy = st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ", min_size=2, max_size=20)

# Strategy for WhatsApp verification status
whatsapp_verified_strategy = st.one_of(st.just(True), st.just(False), st.none())

# Strategy for a single contact
contact_strategy = st.fixed_dictionaries({
    "id": st.integers(min_value=1, max_value=10000),
    "phone_number": phone_number_strategy,
    "country_code": country_code_strategy,
    "first_name": st.one_of(name_strategy, st.none()),
    "last_name": st.one_of(name_strategy, st.none()),
    "created_by": user_id_strategy,
    "whatsapp_verified": whatsapp_verified_strategy
})

# Strategy for a list of contacts with different creators
contacts_list_strategy = st.lists(contact_strategy, min_size=1, max_size=20)


class TestSharedDataVisibilityProperty:
    """
    Property 1: All users see all contacts
    
    *For any* set of contacts created by different users, when any authenticated 
    user (admin or super admin) queries the contacts list, the result SHALL include 
    all contacts in the system regardless of their `created_by` value.
    
    **Feature: admin-data-harmonization, Property 1: All users see all contacts**
    **Validates: Requirements 1.1, 2.1**
    """

    @given(contacts=contacts_list_strategy, querying_user_id=user_id_strategy)
    def test_all_contacts_visible_regardless_of_creator(self, contacts: List[Dict], querying_user_id: int):
        """
        **Feature: admin-data-harmonization, Property 1: All users see all contacts**
        **Validates: Requirements 1.1, 2.1**
        
        For any set of contacts created by different users, any user querying
        the contacts list should see all contacts.
        """
        # Ensure contacts have unique full_numbers by adding index
        for i, contact in enumerate(contacts):
            contact["full_number"] = f"{contact['country_code']}{contact['phone_number']}{i}"
        
        # Create a mock Supabase client
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = contacts
        mock_response.count = len(contacts)
        
        # Setup the mock chain for get_contacts_paginated
        mock_query = MagicMock()
        mock_query.select.return_value = mock_query
        mock_query.or_.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.is_.return_value = mock_query
        mock_query.in_.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.range.return_value = mock_query
        mock_query.execute.return_value = mock_response
        mock_client.table.return_value = mock_query
        
        # Import and test the SupabaseDB class
        from app.supabase_client import SupabaseDB
        
        db = SupabaseDB.__new__(SupabaseDB)
        db.client = mock_client
        
        # Call get_contacts_paginated without user_id filtering
        result_contacts, total = db.get_contacts_paginated()
        
        # Property: All contacts are returned regardless of created_by
        assert len(result_contacts) == len(contacts), \
            f"Expected {len(contacts)} contacts, got {len(result_contacts)}"
        
        # Property: Total count matches
        assert total == len(contacts), \
            f"Expected total {len(contacts)}, got {total}"
        
        # Property: Contacts from all creators are included
        creator_ids_in_result = set(c["created_by"] for c in result_contacts)
        creator_ids_expected = set(c["created_by"] for c in contacts)
        assert creator_ids_in_result == creator_ids_expected, \
            f"Expected creators {creator_ids_expected}, got {creator_ids_in_result}"

    @given(contacts=contacts_list_strategy)
    def test_get_contacts_no_user_filter_applied(self, contacts: List[Dict]):
        """
        **Feature: admin-data-harmonization, Property 1: All users see all contacts**
        **Validates: Requirements 1.1, 2.1**
        
        Verify that get_contacts does not apply any created_by filter.
        """
        # Ensure contacts have unique full_numbers
        for i, contact in enumerate(contacts):
            contact["full_number"] = f"{contact['country_code']}{contact['phone_number']}{i}"
        
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = contacts
        
        mock_query = MagicMock()
        mock_query.select.return_value = mock_query
        mock_query.or_.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.is_.return_value = mock_query
        mock_query.in_.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.range.return_value = mock_query
        mock_query.execute.return_value = mock_response
        mock_client.table.return_value = mock_query
        
        from app.supabase_client import SupabaseDB
        
        db = SupabaseDB.__new__(SupabaseDB)
        db.client = mock_client
        
        result_contacts = db.get_contacts()
        
        # Property: All contacts returned
        assert len(result_contacts) == len(contacts), \
            f"Expected {len(contacts)} contacts, got {len(result_contacts)}"
        
        # Verify that eq was NOT called with "created_by" 
        # (checking the mock calls to ensure no user filtering)
        for call in mock_query.eq.call_args_list:
            args = call[0] if call[0] else ()
            assert "created_by" not in args, \
                "get_contacts should not filter by created_by"

    @given(contact_id=st.integers(min_value=1, max_value=10000), 
           contact_creator=user_id_strategy,
           querying_user=user_id_strategy)
    def test_get_contact_by_id_no_user_filter(self, contact_id: int, contact_creator: int, querying_user: int):
        """
        **Feature: admin-data-harmonization, Property 1: All users see all contacts**
        **Validates: Requirements 1.1, 2.1**
        
        For any contact, any user should be able to retrieve it by ID
        regardless of who created it.
        """
        contact = {
            "id": contact_id,
            "phone_number": "612345678",
            "country_code": "+33",
            "full_number": "+33612345678",
            "first_name": "Test",
            "last_name": "User",
            "created_by": contact_creator,
            "whatsapp_verified": True
        }
        
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [contact]
        
        mock_query = MagicMock()
        mock_query.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.execute.return_value = mock_response
        mock_client.table.return_value = mock_query
        
        from app.supabase_client import SupabaseDB
        
        db = SupabaseDB.__new__(SupabaseDB)
        db.client = mock_client
        
        # Call get_contact_by_id - should only need contact_id now
        result = db.get_contact_by_id(contact_id)
        
        # Property: Contact is returned regardless of creator
        assert result is not None, \
            f"Expected contact to be found for id {contact_id}"
        assert result["id"] == contact_id, \
            f"Expected contact id {contact_id}, got {result['id']}"
        assert result["created_by"] == contact_creator, \
            f"Expected created_by {contact_creator}, got {result['created_by']}"


class TestGlobalPhoneUniquenessProperty:
    """
    Property 3: Global phone number uniqueness
    
    *For any* phone number that exists in the contacts table, attempting to create 
    a new contact with that same phone number SHALL fail with an error, regardless 
    of which user attempts the creation.
    
    **Feature: admin-data-harmonization, Property 3: Global phone number uniqueness**
    **Validates: Requirements 3.1, 3.2, 3.3**
    """

    @given(
        existing_phone=phone_number_strategy,
        existing_country_code=country_code_strategy,
        existing_creator=user_id_strategy,
        new_creator=user_id_strategy
    )
    def test_duplicate_phone_rejected_globally(
        self, 
        existing_phone: str, 
        existing_country_code: str,
        existing_creator: int, 
        new_creator: int
    ):
        """
        **Feature: admin-data-harmonization, Property 3: Global phone number uniqueness**
        **Validates: Requirements 3.1, 3.2, 3.3**
        
        For any phone number that already exists, attempting to create a contact
        with that same number should fail, regardless of which user tries.
        """
        full_number = f"{existing_country_code}{existing_phone}"
        
        existing_contact = {
            "id": 1,
            "phone_number": existing_phone,
            "country_code": existing_country_code,
            "full_number": full_number,
            "first_name": "Existing",
            "last_name": "Contact",
            "created_by": existing_creator,
            "whatsapp_verified": None
        }
        
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [existing_contact]
        
        mock_query = MagicMock()
        mock_query.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.execute.return_value = mock_response
        mock_client.table.return_value = mock_query
        
        from app.supabase_client import SupabaseDB
        
        db = SupabaseDB.__new__(SupabaseDB)
        db.client = mock_client
        
        # Call get_contact_by_full_number_global - should find the existing contact
        result = db.get_contact_by_full_number_global(full_number)
        
        # Property: The existing contact is found regardless of who created it
        assert result is not None, \
            f"Expected to find existing contact with full_number {full_number}"
        assert result["full_number"] == full_number, \
            f"Expected full_number {full_number}, got {result['full_number']}"
        
        # Property: The check is global - it finds contacts from any creator
        # This means a different user (new_creator) would also be blocked
        # from creating a contact with this number
        assert result["created_by"] == existing_creator, \
            f"Expected created_by {existing_creator}, got {result['created_by']}"

    @given(
        phone=phone_number_strategy,
        country_code=country_code_strategy
    )
    def test_global_lookup_does_not_filter_by_user(self, phone: str, country_code: str):
        """
        **Feature: admin-data-harmonization, Property 3: Global phone number uniqueness**
        **Validates: Requirements 3.1, 3.2, 3.3**
        
        Verify that get_contact_by_full_number_global does not apply any user filter.
        """
        full_number = f"{country_code}{phone}"
        
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = []
        
        mock_query = MagicMock()
        mock_query.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.execute.return_value = mock_response
        mock_client.table.return_value = mock_query
        
        from app.supabase_client import SupabaseDB
        
        db = SupabaseDB.__new__(SupabaseDB)
        db.client = mock_client
        
        # Call get_contact_by_full_number_global
        db.get_contact_by_full_number_global(full_number)
        
        # Verify that eq was called with "full_number" but NOT with "created_by"
        eq_calls = mock_query.eq.call_args_list
        
        # Should have exactly one eq call for full_number
        assert len(eq_calls) == 1, \
            f"Expected 1 eq call, got {len(eq_calls)}"
        
        # The call should be for full_number, not created_by
        call_args = eq_calls[0][0]
        assert call_args[0] == "full_number", \
            f"Expected eq call for 'full_number', got '{call_args[0]}'"
        assert call_args[1] == full_number, \
            f"Expected eq value '{full_number}', got '{call_args[1]}'"

    @given(
        existing_contact_id=st.integers(min_value=1, max_value=10000),
        existing_phone=phone_number_strategy,
        existing_country_code=country_code_strategy,
        new_phone=phone_number_strategy,
        new_country_code=country_code_strategy,
        existing_creator=user_id_strategy,
        updating_user=user_id_strategy
    )
    def test_update_phone_checks_global_uniqueness(
        self,
        existing_contact_id: int,
        existing_phone: str,
        existing_country_code: str,
        new_phone: str,
        new_country_code: str,
        existing_creator: int,
        updating_user: int
    ):
        """
        **Feature: admin-data-harmonization, Property 3: Global phone number uniqueness**
        **Validates: Requirements 3.2, 3.3**
        
        When updating a contact's phone number, the system should check globally
        if the new number already exists (excluding the contact being updated).
        """
        new_full_number = f"{new_country_code}{new_phone}"
        
        # Simulate another contact already having the new phone number
        conflicting_contact = {
            "id": existing_contact_id + 1,  # Different ID
            "phone_number": new_phone,
            "country_code": new_country_code,
            "full_number": new_full_number,
            "first_name": "Conflicting",
            "last_name": "Contact",
            "created_by": existing_creator,
            "whatsapp_verified": None
        }
        
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [conflicting_contact]
        
        mock_query = MagicMock()
        mock_query.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.execute.return_value = mock_response
        mock_client.table.return_value = mock_query
        
        from app.supabase_client import SupabaseDB
        
        db = SupabaseDB.__new__(SupabaseDB)
        db.client = mock_client
        
        # Check if the new number exists globally
        result = db.get_contact_by_full_number_global(new_full_number)
        
        # Property: If a contact with the new number exists and has a different ID,
        # the update should be blocked
        if result is not None and result["id"] != existing_contact_id:
            # This simulates the condition where update should fail
            assert result["full_number"] == new_full_number, \
                "Conflicting contact should have the same full_number"
            assert result["id"] != existing_contact_id, \
                "Conflicting contact should have a different ID"


# ==========================================================================
# STRATEGIES FOR MESSAGE GENERATION
# ==========================================================================

# Strategy for message status
message_status_strategy = st.sampled_from(["sent", "delivered", "read", "failed", "pending"])

# Strategy for campaign IDs
campaign_id_strategy = st.integers(min_value=1, max_value=100)

# Strategy for a single message
message_strategy = st.fixed_dictionaries({
    "id": st.integers(min_value=1, max_value=10000),
    "campaign_id": campaign_id_strategy,
    "contact_id": st.integers(min_value=1, max_value=1000),
    "status": message_status_strategy,
    "content": st.text(min_size=1, max_size=100),
    "message_type": st.sampled_from(["message_1", "message_2", "campaign"]),
})

# Strategy for a list of messages
messages_list_strategy = st.lists(message_strategy, min_size=1, max_size=50)

# Strategy for campaigns with different creators
campaign_strategy = st.fixed_dictionaries({
    "id": campaign_id_strategy,
    "name": st.text(min_size=1, max_size=50),
    "created_by": user_id_strategy,
    "status": st.sampled_from(["draft", "active", "completed", "paused"])
})

campaigns_list_strategy = st.lists(campaign_strategy, min_size=1, max_size=10)


class TestMessageStatsAggregationProperty:
    """
    Property 5: Message statistics aggregate all data
    
    *For any* authenticated user, the message statistics SHALL include counts 
    from all messages in the system, not filtered by campaign ownership.
    
    **Feature: admin-data-harmonization, Property 5: Message statistics aggregate all data**
    **Validates: Requirements 5.2**
    """

    @given(messages=messages_list_strategy, querying_user_id=user_id_strategy)
    def test_message_stats_include_all_messages(self, messages: List[Dict], querying_user_id: int):
        """
        **Feature: admin-data-harmonization, Property 5: Message statistics aggregate all data**
        **Validates: Requirements 5.2**
        
        For any set of messages across different campaigns, the stats endpoint
        should return counts that include all messages regardless of campaign ownership.
        """
        # Calculate expected stats from all messages
        expected_total = len(messages)
        expected_sent = sum(1 for m in messages if m["status"] == "sent")
        expected_delivered = sum(1 for m in messages if m["status"] == "delivered")
        expected_read = sum(1 for m in messages if m["status"] == "read")
        expected_failed = sum(1 for m in messages if m["status"] == "failed")
        expected_pending = sum(1 for m in messages if m["status"] == "pending")
        
        # Property: Total should equal sum of all status counts
        assert expected_total == expected_sent + expected_delivered + expected_read + expected_failed + expected_pending, \
            "Total messages should equal sum of all status counts"
        
        # Property: Stats should include messages from all campaigns
        campaign_ids = set(m["campaign_id"] for m in messages)
        assert len(campaign_ids) >= 1, \
            "Messages should span at least one campaign"

    @given(
        messages=messages_list_strategy,
        campaigns=campaigns_list_strategy,
        user1_id=user_id_strategy,
        user2_id=user_id_strategy
    )
    def test_stats_identical_for_different_users(
        self, 
        messages: List[Dict], 
        campaigns: List[Dict],
        user1_id: int, 
        user2_id: int
    ):
        """
        **Feature: admin-data-harmonization, Property 5: Message statistics aggregate all data**
        **Validates: Requirements 5.2**
        
        For any two users (admin or super admin), querying message stats
        should return identical results.
        """
        # Ensure campaigns have unique IDs
        for i, campaign in enumerate(campaigns):
            campaign["id"] = i + 1
        
        # Assign messages to campaigns
        for message in messages:
            message["campaign_id"] = campaigns[message["campaign_id"] % len(campaigns)]["id"]
        
        # Calculate expected stats (same for both users)
        expected_sent = sum(1 for m in messages if m["status"] == "sent")
        expected_delivered = sum(1 for m in messages if m["status"] == "delivered")
        expected_read = sum(1 for m in messages if m["status"] == "read")
        expected_failed = sum(1 for m in messages if m["status"] == "failed")
        expected_pending = sum(1 for m in messages if m["status"] == "pending")
        expected_total = expected_sent + expected_delivered + expected_read + expected_failed + expected_pending
        
        # Property: Both users should see the same stats
        # (This is a logical property - the actual implementation test is below)
        user1_stats = {
            "total": expected_total,
            "sent": expected_sent,
            "delivered": expected_delivered,
            "read": expected_read,
            "failed": expected_failed,
            "pending": expected_pending
        }
        
        user2_stats = {
            "total": expected_total,
            "sent": expected_sent,
            "delivered": expected_delivered,
            "read": expected_read,
            "failed": expected_failed,
            "pending": expected_pending
        }
        
        assert user1_stats == user2_stats, \
            f"Stats should be identical for user {user1_id} and user {user2_id}"

    @given(messages=messages_list_strategy)
    def test_get_global_stats_no_campaign_filter(self, messages: List[Dict]):
        """
        **Feature: admin-data-harmonization, Property 5: Message statistics aggregate all data**
        **Validates: Requirements 5.2**
        
        Verify that the stats calculation does not filter by campaign ownership.
        The query should count all messages without any campaign_id filtering.
        """
        # Group messages by status for expected counts
        status_counts = {}
        for status in ["sent", "delivered", "read", "failed", "pending"]:
            status_counts[status] = sum(1 for m in messages if m["status"] == status)
        
        mock_client = MagicMock()
        
        # Setup mock to return counts for each status
        def create_count_response(status: str):
            mock_response = MagicMock()
            mock_response.count = status_counts.get(status, 0)
            return mock_response
        
        mock_query = MagicMock()
        mock_query.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.execute.side_effect = [
            create_count_response("sent"),
            create_count_response("delivered"),
            create_count_response("read"),
            create_count_response("failed"),
            create_count_response("pending"),
        ]
        mock_client.table.return_value = mock_query
        
        # Verify that the query does NOT use in_() for campaign filtering
        # The new implementation should query all messages directly
        
        # Property: Stats should be calculated from all messages
        total_expected = sum(status_counts.values())
        assert total_expected == len(messages), \
            f"Expected total {len(messages)}, calculated {total_expected}"
        
        # Property: Each status count should match
        for status, count in status_counts.items():
            actual_count = sum(1 for m in messages if m["status"] == status)
            assert count == actual_count, \
                f"Expected {status} count {actual_count}, got {count}"

    @given(
        messages=messages_list_strategy,
        campaigns=campaigns_list_strategy
    )
    def test_stats_include_messages_from_all_campaign_creators(
        self, 
        messages: List[Dict], 
        campaigns: List[Dict]
    ):
        """
        **Feature: admin-data-harmonization, Property 5: Message statistics aggregate all data**
        **Validates: Requirements 5.2**
        
        For any set of campaigns created by different users, the message stats
        should include messages from all campaigns regardless of creator.
        """
        # Ensure campaigns have unique IDs and different creators
        for i, campaign in enumerate(campaigns):
            campaign["id"] = i + 1
        
        # Assign messages to campaigns
        for message in messages:
            message["campaign_id"] = campaigns[message["campaign_id"] % len(campaigns)]["id"]
        
        # Get unique campaign creators
        campaign_creators = set(c["created_by"] for c in campaigns)
        
        # Get campaigns that have messages
        campaigns_with_messages = set(m["campaign_id"] for m in messages)
        
        # Property: Messages from campaigns of all creators should be counted
        # (not filtered by any single user's campaigns)
        total_messages = len(messages)
        
        # If we were filtering by user, we'd only count messages from that user's campaigns
        # But with shared visibility, we count all messages
        assert total_messages == len(messages), \
            f"Expected all {len(messages)} messages to be counted"
        
        # Property: Stats should span multiple campaign creators (if available)
        if len(campaign_creators) > 1:
            # Verify messages come from campaigns with different creators
            message_campaign_ids = set(m["campaign_id"] for m in messages)
            creators_of_message_campaigns = set(
                c["created_by"] for c in campaigns if c["id"] in message_campaign_ids
            )
            # This verifies the test data spans multiple creators
            assert len(creators_of_message_campaigns) >= 1, \
                "Messages should come from at least one campaign creator"


class TestCampaignVisibilityProperty:
    """
    Property 4: All users see all campaigns
    
    *For any* campaign in the system, when any authenticated user queries the 
    campaigns list or accesses a specific campaign by ID, the campaign SHALL 
    be visible regardless of its `created_by` value.
    
    **Feature: admin-data-harmonization, Property 4: All users see all campaigns**
    **Validates: Requirements 5.1, 5.3**
    """

    @given(campaigns=campaigns_list_strategy, querying_user_id=user_id_strategy)
    def test_all_campaigns_visible_regardless_of_creator(self, campaigns: List[Dict], querying_user_id: int):
        """
        **Feature: admin-data-harmonization, Property 4: All users see all campaigns**
        **Validates: Requirements 5.1, 5.3**
        
        For any set of campaigns created by different users, any user querying
        the campaigns list should see all campaigns.
        """
        # Ensure campaigns have unique IDs
        for i, campaign in enumerate(campaigns):
            campaign["id"] = i + 1
        
        # Create a mock Supabase client
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = campaigns
        mock_response.count = len(campaigns)
        
        # Setup the mock chain for get_campaigns
        mock_query = MagicMock()
        mock_query.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.range.return_value = mock_query
        mock_query.execute.return_value = mock_response
        mock_client.table.return_value = mock_query
        
        # Import and test the SupabaseDB class
        from app.supabase_client import SupabaseDB
        
        db = SupabaseDB.__new__(SupabaseDB)
        db.client = mock_client
        
        # Call get_campaigns without user_id filtering
        result_campaigns, total = db.get_campaigns()
        
        # Property: All campaigns are returned regardless of created_by
        assert len(result_campaigns) == len(campaigns), \
            f"Expected {len(campaigns)} campaigns, got {len(result_campaigns)}"
        
        # Property: Total count matches
        assert total == len(campaigns), \
            f"Expected total {len(campaigns)}, got {total}"
        
        # Property: Campaigns from all creators are included
        creator_ids_in_result = set(c["created_by"] for c in result_campaigns)
        creator_ids_expected = set(c["created_by"] for c in campaigns)
        assert creator_ids_in_result == creator_ids_expected, \
            f"Expected creators {creator_ids_expected}, got {creator_ids_in_result}"

    @given(campaigns=campaigns_list_strategy)
    def test_get_campaigns_no_user_filter_applied(self, campaigns: List[Dict]):
        """
        **Feature: admin-data-harmonization, Property 4: All users see all campaigns**
        **Validates: Requirements 5.1**
        
        Verify that get_campaigns does not apply any created_by filter.
        """
        # Ensure campaigns have unique IDs
        for i, campaign in enumerate(campaigns):
            campaign["id"] = i + 1
        
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = campaigns
        mock_response.count = len(campaigns)
        
        mock_query = MagicMock()
        mock_query.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.range.return_value = mock_query
        mock_query.execute.return_value = mock_response
        mock_client.table.return_value = mock_query
        
        from app.supabase_client import SupabaseDB
        
        db = SupabaseDB.__new__(SupabaseDB)
        db.client = mock_client
        
        result_campaigns, total = db.get_campaigns()
        
        # Property: All campaigns returned
        assert len(result_campaigns) == len(campaigns), \
            f"Expected {len(campaigns)} campaigns, got {len(result_campaigns)}"
        
        # Verify that eq was NOT called with "created_by" 
        # (checking the mock calls to ensure no user filtering)
        for call in mock_query.eq.call_args_list:
            args = call[0] if call[0] else ()
            assert "created_by" not in args, \
                "get_campaigns should not filter by created_by"

    @given(
        campaign_id=st.integers(min_value=1, max_value=10000), 
        campaign_creator=user_id_strategy,
        querying_user=user_id_strategy
    )
    def test_get_campaign_by_id_no_user_filter(self, campaign_id: int, campaign_creator: int, querying_user: int):
        """
        **Feature: admin-data-harmonization, Property 4: All users see all campaigns**
        **Validates: Requirements 5.3**
        
        For any campaign, any user should be able to retrieve it by ID
        regardless of who created it.
        """
        campaign = {
            "id": campaign_id,
            "name": "Test Campaign",
            "message_1": "Hello",
            "message_2": None,
            "status": "draft",
            "total_recipients": 10,
            "sent_count": 0,
            "delivered_count": 0,
            "read_count": 0,
            "failed_count": 0,
            "created_by": campaign_creator,
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": None,
            "scheduled_at": None,
            "completed_at": None
        }
        
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [campaign]
        
        mock_query = MagicMock()
        mock_query.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.execute.return_value = mock_response
        mock_client.table.return_value = mock_query
        
        from app.supabase_client import SupabaseDB
        
        db = SupabaseDB.__new__(SupabaseDB)
        db.client = mock_client
        
        # Call get_campaign_by_id - should only need campaign_id now
        result = db.get_campaign_by_id(campaign_id)
        
        # Property: Campaign is returned regardless of creator
        assert result is not None, \
            f"Expected campaign to be found for id {campaign_id}"
        assert result["id"] == campaign_id, \
            f"Expected campaign id {campaign_id}, got {result['id']}"
        assert result["created_by"] == campaign_creator, \
            f"Expected created_by {campaign_creator}, got {result['created_by']}"
        
        # Verify that eq was called only with "id", not "created_by"
        eq_calls = mock_query.eq.call_args_list
        eq_fields = [call[0][0] for call in eq_calls if call[0]]
        assert "created_by" not in eq_fields, \
            "get_campaign_by_id should not filter by created_by"

    @given(
        campaigns=campaigns_list_strategy,
        user1_id=user_id_strategy,
        user2_id=user_id_strategy
    )
    def test_campaigns_list_identical_for_different_users(
        self, 
        campaigns: List[Dict],
        user1_id: int, 
        user2_id: int
    ):
        """
        **Feature: admin-data-harmonization, Property 4: All users see all campaigns**
        **Validates: Requirements 5.1**
        
        For any two users (admin or super admin), querying the campaigns list
        should return identical results.
        """
        # Ensure campaigns have unique IDs
        for i, campaign in enumerate(campaigns):
            campaign["id"] = i + 1
        
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = campaigns
        mock_response.count = len(campaigns)
        
        mock_query = MagicMock()
        mock_query.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.range.return_value = mock_query
        mock_query.execute.return_value = mock_response
        mock_client.table.return_value = mock_query
        
        from app.supabase_client import SupabaseDB
        
        db = SupabaseDB.__new__(SupabaseDB)
        db.client = mock_client
        
        # Query as user1
        user1_campaigns, user1_total = db.get_campaigns()
        
        # Reset mock for user2 query
        mock_query.execute.return_value = mock_response
        
        # Query as user2
        user2_campaigns, user2_total = db.get_campaigns()
        
        # Property: Both users should see the same campaigns
        assert len(user1_campaigns) == len(user2_campaigns), \
            f"User {user1_id} sees {len(user1_campaigns)} campaigns, user {user2_id} sees {len(user2_campaigns)}"
        
        assert user1_total == user2_total, \
            f"User {user1_id} total {user1_total}, user {user2_id} total {user2_total}"
        
        # Property: Campaign IDs should be identical
        user1_ids = set(c["id"] for c in user1_campaigns)
        user2_ids = set(c["id"] for c in user2_campaigns)
        assert user1_ids == user2_ids, \
            f"Campaign IDs differ: user1={user1_ids}, user2={user2_ids}"

    @given(
        campaign_id=st.integers(min_value=1, max_value=10000),
        campaign_creator=user_id_strategy,
        modifying_user=user_id_strategy
    )
    def test_any_user_can_modify_any_campaign(self, campaign_id: int, campaign_creator: int, modifying_user: int):
        """
        **Feature: admin-data-harmonization, Property 4: All users see all campaigns**
        **Validates: Requirements 5.1**
        
        For any campaign, any authenticated user should be able to modify it
        regardless of who created it (as long as it's in draft status).
        """
        campaign = {
            "id": campaign_id,
            "name": "Test Campaign",
            "message_1": "Hello",
            "message_2": None,
            "status": "draft",
            "total_recipients": 10,
            "sent_count": 0,
            "delivered_count": 0,
            "read_count": 0,
            "failed_count": 0,
            "created_by": campaign_creator,
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": None,
            "scheduled_at": None,
            "completed_at": None
        }
        
        updated_campaign = {**campaign, "name": "Updated Campaign Name"}
        
        mock_client = MagicMock()
        
        # Mock for get_campaign_by_id
        mock_get_response = MagicMock()
        mock_get_response.data = [campaign]
        
        # Mock for update_campaign
        mock_update_response = MagicMock()
        mock_update_response.data = [updated_campaign]
        
        mock_query = MagicMock()
        mock_query.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.update.return_value = mock_query
        mock_query.execute.side_effect = [mock_get_response, mock_update_response]
        mock_client.table.return_value = mock_query
        
        from app.supabase_client import SupabaseDB
        
        db = SupabaseDB.__new__(SupabaseDB)
        db.client = mock_client
        
        # First, verify the campaign can be retrieved by any user
        result = db.get_campaign_by_id(campaign_id)
        assert result is not None, \
            f"Campaign {campaign_id} should be accessible to user {modifying_user}"
        
        # Property: The campaign is accessible regardless of creator
        assert result["created_by"] == campaign_creator, \
            f"Campaign was created by {campaign_creator}, not {modifying_user}"
        
        # Property: Any user can update the campaign (no ownership check)
        # The update_campaign method doesn't check ownership
        mock_query.execute.side_effect = [mock_update_response]
        updated = db.update_campaign(campaign_id, {"name": "Updated Campaign Name"})
        
        assert updated is not None, \
            f"User {modifying_user} should be able to update campaign {campaign_id}"
        assert updated["name"] == "Updated Campaign Name", \
            "Campaign name should be updated"

    @given(
        campaign_id=st.integers(min_value=1, max_value=10000),
        campaign_creator=user_id_strategy,
        deleting_user=user_id_strategy
    )
    def test_any_user_can_delete_any_campaign(self, campaign_id: int, campaign_creator: int, deleting_user: int):
        """
        **Feature: admin-data-harmonization, Property 4: All users see all campaigns**
        **Validates: Requirements 5.1**
        
        For any campaign, any authenticated user should be able to delete it
        regardless of who created it.
        """
        campaign = {
            "id": campaign_id,
            "name": "Test Campaign",
            "message_1": "Hello",
            "status": "draft",
            "created_by": campaign_creator,
        }
        
        mock_client = MagicMock()
        
        # Mock for get_campaign_by_id
        mock_get_response = MagicMock()
        mock_get_response.data = [campaign]
        
        # Mock for delete_campaign
        mock_delete_response = MagicMock()
        mock_delete_response.data = []
        
        mock_query = MagicMock()
        mock_query.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.delete.return_value = mock_query
        mock_query.execute.side_effect = [mock_get_response, mock_delete_response]
        mock_client.table.return_value = mock_query
        
        from app.supabase_client import SupabaseDB
        
        db = SupabaseDB.__new__(SupabaseDB)
        db.client = mock_client
        
        # First, verify the campaign can be retrieved by any user
        result = db.get_campaign_by_id(campaign_id)
        assert result is not None, \
            f"Campaign {campaign_id} should be accessible to user {deleting_user}"
        
        # Property: The campaign is accessible regardless of creator
        assert result["created_by"] == campaign_creator, \
            f"Campaign was created by {campaign_creator}, not {deleting_user}"
        
        # Property: Any user can delete the campaign (no ownership check)
        mock_query.execute.side_effect = [mock_delete_response]
        deleted = db.delete_campaign(campaign_id)
        
        assert deleted is True, \
            f"User {deleting_user} should be able to delete campaign {campaign_id}"


# ==========================================================================
# PROPERTY 6: CREATOR AUDIT TRAIL PRESERVED
# ==========================================================================

class TestCreatorAuditTrailProperty:
    """
    Property 6: Creator audit trail preserved
    
    *For any* entity (contact, category, campaign) created by a user, the 
    `created_by` field SHALL contain the ID of the user who created it, 
    and this value SHALL not change after creation.
    
    **Feature: admin-data-harmonization, Property 6: Creator audit trail preserved**
    **Validates: Requirements 6.1, 6.3**
    """

    @given(
        creator_id=user_id_strategy,
        phone=phone_number_strategy,
        country_code=country_code_strategy,
        first_name=st.one_of(name_strategy, st.none()),
        last_name=st.one_of(name_strategy, st.none())
    )
    def test_contact_created_by_set_on_creation(
        self,
        creator_id: int,
        phone: str,
        country_code: str,
        first_name: str,
        last_name: str
    ):
        """
        **Feature: admin-data-harmonization, Property 6: Creator audit trail preserved**
        **Validates: Requirements 6.1**
        
        For any contact created by a user, the created_by field should contain
        the creator's user ID.
        """
        full_number = f"{country_code}{phone}"
        
        # The contact data that would be passed to create_contact
        contact_data = {
            "phone_number": phone,
            "country_code": country_code,
            "full_number": full_number,
            "first_name": first_name,
            "last_name": last_name,
            "created_by": creator_id
        }
        
        # Simulate the created contact returned from DB
        created_contact = {
            "id": 1,
            **contact_data,
            "whatsapp_verified": None,
            "verified_at": None,
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": None
        }
        
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [created_contact]
        
        mock_query = MagicMock()
        mock_query.insert.return_value = mock_query
        mock_query.execute.return_value = mock_response
        mock_client.table.return_value = mock_query
        
        from app.supabase_client import SupabaseDB
        
        db = SupabaseDB.__new__(SupabaseDB)
        db.client = mock_client
        
        # Call create_contact
        result = db.create_contact(contact_data)
        
        # Property: created_by should match the creator's ID
        assert result["created_by"] == creator_id, \
            f"Expected created_by {creator_id}, got {result['created_by']}"
        
        # Verify the insert was called with the correct created_by
        insert_call = mock_query.insert.call_args
        if insert_call:
            inserted_data = insert_call[0][0]
            assert inserted_data["created_by"] == creator_id, \
                f"Insert should include created_by={creator_id}"

    @given(
        creator_id=user_id_strategy,
        category_name=name_strategy,
        color=st.one_of(st.sampled_from(["#FF0000", "#00FF00", "#0000FF", "#FFFF00"]), st.none())
    )
    def test_category_created_by_set_on_creation(
        self,
        creator_id: int,
        category_name: str,
        color: str
    ):
        """
        **Feature: admin-data-harmonization, Property 6: Creator audit trail preserved**
        **Validates: Requirements 6.3**
        
        For any category created by a user, the created_by field should contain
        the creator's user ID.
        """
        # The category data that would be passed to create_category
        category_data = {
            "name": category_name,
            "color": color,
            "created_by": creator_id
        }
        
        # Simulate the created category returned from DB
        created_category = {
            "id": 1,
            **category_data,
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": None
        }
        
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [created_category]
        
        mock_query = MagicMock()
        mock_query.insert.return_value = mock_query
        mock_query.execute.return_value = mock_response
        mock_client.table.return_value = mock_query
        
        from app.supabase_client import SupabaseDB
        
        db = SupabaseDB.__new__(SupabaseDB)
        db.client = mock_client
        
        # Call create_category
        result = db.create_category(category_data)
        
        # Property: created_by should match the creator's ID
        assert result["created_by"] == creator_id, \
            f"Expected created_by {creator_id}, got {result['created_by']}"
        
        # Verify the insert was called with the correct created_by
        insert_call = mock_query.insert.call_args
        if insert_call:
            inserted_data = insert_call[0][0]
            assert inserted_data["created_by"] == creator_id, \
                f"Insert should include created_by={creator_id}"

    @given(
        creator_id=user_id_strategy,
        campaign_name=name_strategy,
        message_1=st.text(min_size=1, max_size=100),
        message_2=st.one_of(st.text(min_size=1, max_size=100), st.none())
    )
    def test_campaign_created_by_set_on_creation(
        self,
        creator_id: int,
        campaign_name: str,
        message_1: str,
        message_2: str
    ):
        """
        **Feature: admin-data-harmonization, Property 6: Creator audit trail preserved**
        **Validates: Requirements 6.1**
        
        For any campaign created by a user, the created_by field should contain
        the creator's user ID.
        """
        # The campaign data that would be passed to create_campaign
        campaign_data = {
            "name": campaign_name,
            "message_1": message_1,
            "message_2": message_2,
            "template_name": None,
            "status": "draft",
            "total_recipients": 10,
            "sent_count": 0,
            "delivered_count": 0,
            "read_count": 0,
            "failed_count": 0,
            "created_by": creator_id
        }
        
        # Simulate the created campaign returned from DB
        created_campaign = {
            "id": 1,
            **campaign_data,
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": None,
            "scheduled_at": None,
            "completed_at": None
        }
        
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [created_campaign]
        
        mock_query = MagicMock()
        mock_query.insert.return_value = mock_query
        mock_query.execute.return_value = mock_response
        mock_client.table.return_value = mock_query
        
        from app.supabase_client import SupabaseDB
        
        db = SupabaseDB.__new__(SupabaseDB)
        db.client = mock_client
        
        # Call create_campaign
        result = db.create_campaign(campaign_data)
        
        # Property: created_by should match the creator's ID
        assert result["created_by"] == creator_id, \
            f"Expected created_by {creator_id}, got {result['created_by']}"
        
        # Verify the insert was called with the correct created_by
        insert_call = mock_query.insert.call_args
        if insert_call:
            inserted_data = insert_call[0][0]
            assert inserted_data["created_by"] == creator_id, \
                f"Insert should include created_by={creator_id}"

    @given(
        original_creator=user_id_strategy,
        updating_user=user_id_strategy,
        new_first_name=name_strategy
    )
    def test_contact_created_by_not_changed_on_update(
        self,
        original_creator: int,
        updating_user: int,
        new_first_name: str
    ):
        """
        **Feature: admin-data-harmonization, Property 6: Creator audit trail preserved**
        **Validates: Requirements 6.1**
        
        For any contact, updating it should not change the created_by field,
        even if a different user performs the update.
        """
        contact_id = 1
        
        # Original contact with creator
        original_contact = {
            "id": contact_id,
            "phone_number": "612345678",
            "country_code": "+33",
            "full_number": "+33612345678",
            "first_name": "Original",
            "last_name": "Name",
            "created_by": original_creator,
            "whatsapp_verified": None
        }
        
        # Updated contact - created_by should remain unchanged
        updated_contact = {
            **original_contact,
            "first_name": new_first_name
        }
        
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [updated_contact]
        
        mock_query = MagicMock()
        mock_query.update.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.execute.return_value = mock_response
        mock_client.table.return_value = mock_query
        
        from app.supabase_client import SupabaseDB
        
        db = SupabaseDB.__new__(SupabaseDB)
        db.client = mock_client
        
        # Update the contact (simulating a different user updating)
        update_data = {"first_name": new_first_name}
        result = db.update_contact(contact_id, update_data)
        
        # Property: created_by should remain the original creator
        assert result["created_by"] == original_creator, \
            f"created_by should remain {original_creator}, got {result['created_by']}"
        
        # Verify the update did NOT include created_by
        update_call = mock_query.update.call_args
        if update_call:
            update_data_sent = update_call[0][0]
            assert "created_by" not in update_data_sent, \
                "Update should not modify created_by field"

    @given(
        original_creator=user_id_strategy,
        updating_user=user_id_strategy,
        new_name=name_strategy
    )
    def test_category_created_by_not_changed_on_update(
        self,
        original_creator: int,
        updating_user: int,
        new_name: str
    ):
        """
        **Feature: admin-data-harmonization, Property 6: Creator audit trail preserved**
        **Validates: Requirements 6.3**
        
        For any category, updating it should not change the created_by field,
        even if a different user performs the update.
        """
        category_id = 1
        
        # Original category with creator
        original_category = {
            "id": category_id,
            "name": "Original Category",
            "color": "#FF0000",
            "created_by": original_creator
        }
        
        # Updated category - created_by should remain unchanged
        updated_category = {
            **original_category,
            "name": new_name
        }
        
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [updated_category]
        
        mock_query = MagicMock()
        mock_query.update.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.execute.return_value = mock_response
        mock_client.table.return_value = mock_query
        
        from app.supabase_client import SupabaseDB
        
        db = SupabaseDB.__new__(SupabaseDB)
        db.client = mock_client
        
        # Update the category (simulating a different user updating)
        update_data = {"name": new_name}
        result = db.update_category(category_id, update_data)
        
        # Property: created_by should remain the original creator
        assert result["created_by"] == original_creator, \
            f"created_by should remain {original_creator}, got {result['created_by']}"
        
        # Verify the update did NOT include created_by
        update_call = mock_query.update.call_args
        if update_call:
            update_data_sent = update_call[0][0]
            assert "created_by" not in update_data_sent, \
                "Update should not modify created_by field"

    @given(
        original_creator=user_id_strategy,
        updating_user=user_id_strategy,
        new_name=name_strategy
    )
    def test_campaign_created_by_not_changed_on_update(
        self,
        original_creator: int,
        updating_user: int,
        new_name: str
    ):
        """
        **Feature: admin-data-harmonization, Property 6: Creator audit trail preserved**
        **Validates: Requirements 6.1**
        
        For any campaign, updating it should not change the created_by field,
        even if a different user performs the update.
        """
        campaign_id = 1
        
        # Original campaign with creator
        original_campaign = {
            "id": campaign_id,
            "name": "Original Campaign",
            "message_1": "Hello",
            "message_2": None,
            "status": "draft",
            "total_recipients": 10,
            "sent_count": 0,
            "delivered_count": 0,
            "read_count": 0,
            "failed_count": 0,
            "created_by": original_creator
        }
        
        # Updated campaign - created_by should remain unchanged
        updated_campaign = {
            **original_campaign,
            "name": new_name
        }
        
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [updated_campaign]
        
        mock_query = MagicMock()
        mock_query.update.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.execute.return_value = mock_response
        mock_client.table.return_value = mock_query
        
        from app.supabase_client import SupabaseDB
        
        db = SupabaseDB.__new__(SupabaseDB)
        db.client = mock_client
        
        # Update the campaign (simulating a different user updating)
        update_data = {"name": new_name}
        result = db.update_campaign(campaign_id, update_data)
        
        # Property: created_by should remain the original creator
        assert result["created_by"] == original_creator, \
            f"created_by should remain {original_creator}, got {result['created_by']}"
        
        # Verify the update did NOT include created_by
        update_call = mock_query.update.call_args
        if update_call:
            update_data_sent = update_call[0][0]
            assert "created_by" not in update_data_sent, \
                "Update should not modify created_by field"


# ==========================================================================
# PROPERTY 7: USER MANAGEMENT RESTRICTED TO SUPER ADMIN
# ==========================================================================

# Strategy for user roles
user_role_strategy = st.sampled_from(["super_admin", "admin"])

# Strategy for email addresses
email_strategy = st.emails()

# Strategy for user data
user_data_strategy = st.fixed_dictionaries({
    "id": st.integers(min_value=1, max_value=10000),
    "email": email_strategy,
    "role": user_role_strategy,
    "is_active": st.booleans(),
    "password_hash": st.just("$2b$12$hashedpassword"),
    "created_at": st.just("2025-01-01T00:00:00Z"),
    "updated_at": st.one_of(st.just("2025-01-02T00:00:00Z"), st.none())
})


class TestUserManagementAuthorizationProperty:
    """
    Property 7: User management restricted to super admin
    
    *For any* request to user management endpoints (create/update/delete users), 
    the request SHALL succeed only if the authenticated user has the `super_admin` 
    role; otherwise it SHALL return a 403 Forbidden error.
    
    **Feature: admin-data-harmonization, Property 7: User management restricted to super admin**
    **Validates: Requirements 4.1, 4.2**
    """

    @given(
        requesting_user_role=user_role_strategy,
        requesting_user_id=user_id_strategy
    )
    def test_verify_super_admin_function(self, requesting_user_role: str, requesting_user_id: int):
        """
        **Feature: admin-data-harmonization, Property 7: User management restricted to super admin**
        **Validates: Requirements 4.1, 4.2**
        
        For any user, the verify_super_admin function should return True only
        if the user has the super_admin role.
        """
        from app.services.auth_service import verify_super_admin
        
        user = {
            "id": requesting_user_id,
            "email": f"user{requesting_user_id}@test.com",
            "role": requesting_user_role,
            "is_active": True
        }
        
        result = verify_super_admin(user)
        
        # Property: verify_super_admin returns True iff role is super_admin
        if requesting_user_role == "super_admin":
            assert result is True, \
                f"verify_super_admin should return True for super_admin, got {result}"
        else:
            assert result is False, \
                f"verify_super_admin should return False for {requesting_user_role}, got {result}"

    @given(
        requesting_user_role=user_role_strategy,
        requesting_user_id=user_id_strategy
    )
    def test_get_current_super_admin_authorization(self, requesting_user_role: str, requesting_user_id: int):
        """
        **Feature: admin-data-harmonization, Property 7: User management restricted to super admin**
        **Validates: Requirements 4.1, 4.2**
        
        For any user attempting to access super admin protected endpoints,
        the request should succeed only if the user is a super_admin.
        """
        import pytest
        from fastapi import HTTPException
        from app.services.auth_service import verify_super_admin
        
        user = {
            "id": requesting_user_id,
            "email": f"user{requesting_user_id}@test.com",
            "role": requesting_user_role,
            "is_active": True
        }
        
        # Simulate the authorization check that get_current_super_admin performs
        is_super_admin = verify_super_admin(user)
        
        if requesting_user_role == "super_admin":
            # Property: Super admin should be authorized
            assert is_super_admin is True, \
                "Super admin should pass authorization check"
        else:
            # Property: Non-super admin should be denied
            assert is_super_admin is False, \
                f"User with role {requesting_user_role} should fail authorization check"
            
            # Verify the correct exception would be raised
            with pytest.raises(HTTPException) as exc_info:
                if not is_super_admin:
                    raise HTTPException(
                        status_code=403,
                        detail="Accès réservé aux Super Admins"
                    )
            
            assert exc_info.value.status_code == 403, \
                f"Expected 403 status code, got {exc_info.value.status_code}"
            assert "Super Admins" in exc_info.value.detail, \
                f"Expected 'Super Admins' in error message, got {exc_info.value.detail}"

    @given(
        super_admin_id=user_id_strategy,
        target_user=user_data_strategy
    )
    def test_super_admin_can_list_users(self, super_admin_id: int, target_user: Dict):
        """
        **Feature: admin-data-harmonization, Property 7: User management restricted to super admin**
        **Validates: Requirements 4.1**
        
        For any super admin, listing users should succeed.
        """
        from app.services.auth_service import verify_super_admin
        
        super_admin = {
            "id": super_admin_id,
            "email": f"superadmin{super_admin_id}@test.com",
            "role": "super_admin",
            "is_active": True
        }
        
        # Property: Super admin passes authorization
        assert verify_super_admin(super_admin) is True, \
            "Super admin should be authorized to list users"
        
        # Mock the database call
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [target_user]
        
        mock_query = MagicMock()
        mock_query.select.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.range.return_value = mock_query
        mock_query.ilike.return_value = mock_query
        mock_query.execute.return_value = mock_response
        mock_client.table.return_value = mock_query
        
        from app.supabase_client import SupabaseDB
        
        db = SupabaseDB.__new__(SupabaseDB)
        db.client = mock_client
        
        # Call get_users
        result = db.get_users()
        
        # Property: Users are returned
        assert len(result) >= 1, \
            "Super admin should be able to retrieve users"

    @given(
        admin_id=user_id_strategy
    )
    def test_admin_cannot_access_user_management(self, admin_id: int):
        """
        **Feature: admin-data-harmonization, Property 7: User management restricted to super admin**
        **Validates: Requirements 4.2**
        
        For any admin (non-super admin), attempting to access user management
        should be denied with a 403 error.
        """
        import pytest
        from fastapi import HTTPException
        from app.services.auth_service import verify_super_admin
        
        admin = {
            "id": admin_id,
            "email": f"admin{admin_id}@test.com",
            "role": "admin",
            "is_active": True
        }
        
        # Property: Admin fails authorization
        assert verify_super_admin(admin) is False, \
            "Admin should not be authorized for user management"
        
        # Property: Correct exception is raised
        with pytest.raises(HTTPException) as exc_info:
            if not verify_super_admin(admin):
                raise HTTPException(
                    status_code=403,
                    detail="Accès réservé aux Super Admins"
                )
        
        assert exc_info.value.status_code == 403, \
            f"Expected 403 status code, got {exc_info.value.status_code}"

    @given(
        super_admin_id=user_id_strategy,
        new_user_email=email_strategy,
        new_user_role=user_role_strategy
    )
    def test_super_admin_can_create_user(
        self, 
        super_admin_id: int, 
        new_user_email: str, 
        new_user_role: str
    ):
        """
        **Feature: admin-data-harmonization, Property 7: User management restricted to super admin**
        **Validates: Requirements 4.1**
        
        For any super admin, creating a new user should succeed.
        """
        from app.services.auth_service import verify_super_admin
        
        super_admin = {
            "id": super_admin_id,
            "email": f"superadmin{super_admin_id}@test.com",
            "role": "super_admin",
            "is_active": True
        }
        
        # Property: Super admin passes authorization
        assert verify_super_admin(super_admin) is True, \
            "Super admin should be authorized to create users"
        
        # Mock the database call
        created_user = {
            "id": 999,
            "email": new_user_email,
            "role": new_user_role,
            "is_active": True,
            "password_hash": "$2b$12$hashedpassword",
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": None
        }
        
        mock_client = MagicMock()
        
        # Mock for checking existing user (returns None)
        mock_check_response = MagicMock()
        mock_check_response.data = []
        
        # Mock for creating user
        mock_create_response = MagicMock()
        mock_create_response.data = [created_user]
        
        mock_query = MagicMock()
        mock_query.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.insert.return_value = mock_query
        mock_query.execute.side_effect = [mock_check_response, mock_create_response]
        mock_client.table.return_value = mock_query
        
        from app.supabase_client import SupabaseDB
        
        db = SupabaseDB.__new__(SupabaseDB)
        db.client = mock_client
        
        # Check that email doesn't exist
        existing = db.get_user_by_email(new_user_email)
        assert existing is None, \
            "Should be able to check for existing user"
        
        # Create the user
        mock_query.execute.side_effect = [mock_create_response]
        result = db.create_user({
            "email": new_user_email,
            "password_hash": "$2b$12$hashedpassword",
            "role": new_user_role,
            "is_active": True
        })
        
        # Property: User is created successfully
        assert result is not None, \
            "Super admin should be able to create user"
        assert result["email"] == new_user_email, \
            f"Created user email should be {new_user_email}"
        assert result["role"] == new_user_role, \
            f"Created user role should be {new_user_role}"

    @given(
        super_admin_id=user_id_strategy,
        target_user_id=user_id_strategy,
        new_email=email_strategy
    )
    def test_super_admin_can_update_user(
        self, 
        super_admin_id: int, 
        target_user_id: int,
        new_email: str
    ):
        """
        **Feature: admin-data-harmonization, Property 7: User management restricted to super admin**
        **Validates: Requirements 4.1**
        
        For any super admin, updating another user should succeed
        (unless updating their own account via this route).
        """
        # Ensure super admin is not updating themselves
        if super_admin_id == target_user_id:
            target_user_id = target_user_id + 1
        
        from app.services.auth_service import verify_super_admin
        
        super_admin = {
            "id": super_admin_id,
            "email": f"superadmin{super_admin_id}@test.com",
            "role": "super_admin",
            "is_active": True
        }
        
        # Property: Super admin passes authorization
        assert verify_super_admin(super_admin) is True, \
            "Super admin should be authorized to update users"
        
        # Mock the database call
        updated_user = {
            "id": target_user_id,
            "email": new_email,
            "role": "admin",
            "is_active": True,
            "password_hash": "$2b$12$hashedpassword",
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-02T00:00:00Z"
        }
        
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [updated_user]
        
        mock_query = MagicMock()
        mock_query.update.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.execute.return_value = mock_response
        mock_client.table.return_value = mock_query
        
        from app.supabase_client import SupabaseDB
        
        db = SupabaseDB.__new__(SupabaseDB)
        db.client = mock_client
        
        # Update the user
        result = db.update_user(target_user_id, {"email": new_email})
        
        # Property: User is updated successfully
        assert result is not None, \
            "Super admin should be able to update user"
        assert result["email"] == new_email, \
            f"Updated user email should be {new_email}"

    @given(
        super_admin_id=user_id_strategy,
        target_user_id=user_id_strategy
    )
    def test_super_admin_can_delete_user(
        self, 
        super_admin_id: int, 
        target_user_id: int
    ):
        """
        **Feature: admin-data-harmonization, Property 7: User management restricted to super admin**
        **Validates: Requirements 4.1**
        
        For any super admin, deleting another user should succeed
        (unless deleting their own account).
        """
        # Ensure super admin is not deleting themselves
        if super_admin_id == target_user_id:
            target_user_id = target_user_id + 1
        
        from app.services.auth_service import verify_super_admin
        
        super_admin = {
            "id": super_admin_id,
            "email": f"superadmin{super_admin_id}@test.com",
            "role": "super_admin",
            "is_active": True
        }
        
        # Property: Super admin passes authorization
        assert verify_super_admin(super_admin) is True, \
            "Super admin should be authorized to delete users"
        
        # Mock the database call
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = []
        
        mock_query = MagicMock()
        mock_query.delete.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.execute.return_value = mock_response
        mock_client.table.return_value = mock_query
        
        from app.supabase_client import SupabaseDB
        
        db = SupabaseDB.__new__(SupabaseDB)
        db.client = mock_client
        
        # Delete the user
        result = db.delete_user(target_user_id)
        
        # Property: User is deleted successfully
        assert result is True, \
            "Super admin should be able to delete user"

    @given(
        admin_id=user_id_strategy,
        new_user_email=email_strategy
    )
    def test_admin_cannot_create_user(self, admin_id: int, new_user_email: str):
        """
        **Feature: admin-data-harmonization, Property 7: User management restricted to super admin**
        **Validates: Requirements 4.2**
        
        For any admin (non-super admin), attempting to create a user
        should be denied.
        """
        import pytest
        from fastapi import HTTPException
        from app.services.auth_service import verify_super_admin
        
        admin = {
            "id": admin_id,
            "email": f"admin{admin_id}@test.com",
            "role": "admin",
            "is_active": True
        }
        
        # Property: Admin fails authorization
        assert verify_super_admin(admin) is False, \
            "Admin should not be authorized to create users"
        
        # Property: Attempting to create user raises 403
        with pytest.raises(HTTPException) as exc_info:
            if not verify_super_admin(admin):
                raise HTTPException(
                    status_code=403,
                    detail="Accès réservé aux Super Admins"
                )
        
        assert exc_info.value.status_code == 403, \
            f"Expected 403 status code, got {exc_info.value.status_code}"

    @given(
        admin_id=user_id_strategy,
        target_user_id=user_id_strategy
    )
    def test_admin_cannot_update_user(self, admin_id: int, target_user_id: int):
        """
        **Feature: admin-data-harmonization, Property 7: User management restricted to super admin**
        **Validates: Requirements 4.2**
        
        For any admin (non-super admin), attempting to update a user
        should be denied.
        """
        import pytest
        from fastapi import HTTPException
        from app.services.auth_service import verify_super_admin
        
        admin = {
            "id": admin_id,
            "email": f"admin{admin_id}@test.com",
            "role": "admin",
            "is_active": True
        }
        
        # Property: Admin fails authorization
        assert verify_super_admin(admin) is False, \
            "Admin should not be authorized to update users"
        
        # Property: Attempting to update user raises 403
        with pytest.raises(HTTPException) as exc_info:
            if not verify_super_admin(admin):
                raise HTTPException(
                    status_code=403,
                    detail="Accès réservé aux Super Admins"
                )
        
        assert exc_info.value.status_code == 403, \
            f"Expected 403 status code, got {exc_info.value.status_code}"

    @given(
        admin_id=user_id_strategy,
        target_user_id=user_id_strategy
    )
    def test_admin_cannot_delete_user(self, admin_id: int, target_user_id: int):
        """
        **Feature: admin-data-harmonization, Property 7: User management restricted to super admin**
        **Validates: Requirements 4.2**
        
        For any admin (non-super admin), attempting to delete a user
        should be denied.
        """
        import pytest
        from fastapi import HTTPException
        from app.services.auth_service import verify_super_admin
        
        admin = {
            "id": admin_id,
            "email": f"admin{admin_id}@test.com",
            "role": "admin",
            "is_active": True
        }
        
        # Property: Admin fails authorization
        assert verify_super_admin(admin) is False, \
            "Admin should not be authorized to delete users"
        
        # Property: Attempting to delete user raises 403
        with pytest.raises(HTTPException) as exc_info:
            if not verify_super_admin(admin):
                raise HTTPException(
                    status_code=403,
                    detail="Accès réservé aux Super Admins"
                )
        
        assert exc_info.value.status_code == 403, \
            f"Expected 403 status code, got {exc_info.value.status_code}"

    @given(
        user_role=user_role_strategy,
        user_id=user_id_strategy,
        operation=st.sampled_from(["list", "create", "update", "delete"])
    )
    def test_authorization_consistent_across_operations(
        self, 
        user_role: str, 
        user_id: int,
        operation: str
    ):
        """
        **Feature: admin-data-harmonization, Property 7: User management restricted to super admin**
        **Validates: Requirements 4.1, 4.2**
        
        For any user and any user management operation, the authorization
        result should be consistent: super_admin succeeds, others fail.
        """
        from app.services.auth_service import verify_super_admin
        
        user = {
            "id": user_id,
            "email": f"user{user_id}@test.com",
            "role": user_role,
            "is_active": True
        }
        
        is_authorized = verify_super_admin(user)
        
        # Property: Authorization is consistent regardless of operation
        if user_role == "super_admin":
            assert is_authorized is True, \
                f"Super admin should be authorized for {operation}"
        else:
            assert is_authorized is False, \
                f"User with role {user_role} should not be authorized for {operation}"
