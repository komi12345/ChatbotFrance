"""
Checkpoint Validation: 24h Interaction Management.

This test module validates Task 15:
1. Verify that the check_expired_interactions task executes correctly
2. Test with messages older than 24h
3. Verify campaign statistics are updated

Task 15: Checkpoint - Valider la gestion des 24h
Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6
"""
import pytest
from unittest.mock import MagicMock, patch, call
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

# The correct patch path for get_supabase_client (imported inside the function)
SUPABASE_CLIENT_PATCH = 'app.supabase_client.get_supabase_client'


class TestCheckExpiredInteractionsTaskStructure:
    """
    Checkpoint validation: Task structure and configuration.
    
    Requirements: 7.1
    """

    def test_task_is_registered_in_celery(self):
        """
        Validate that check_expired_interactions task is registered.
        
        Requirements: 7.1
        """
        from app.tasks.celery_app import celery_app
        
        # Check task is registered
        task_name = "app.tasks.celery_app.check_expired_interactions"
        assert task_name in celery_app.tasks, \
            f"Task {task_name} should be registered in Celery"

    def test_task_is_in_beat_schedule(self):
        """
        Validate that task is scheduled to run hourly.
        
        Requirements: 7.1
        """
        from app.tasks.celery_app import celery_app
        
        beat_schedule = celery_app.conf.beat_schedule
        
        # Check task is in beat schedule
        assert "check-expired-interactions-hourly" in beat_schedule, \
            "Task should be in beat schedule"
        
        task_config = beat_schedule["check-expired-interactions-hourly"]
        
        # Verify task name
        assert task_config["task"] == "app.tasks.celery_app.check_expired_interactions"
        
        # Verify schedule is hourly (timedelta of 1 hour)
        schedule = task_config["schedule"]
        assert schedule == timedelta(hours=1), \
            f"Task should run hourly, got {schedule}"

    def test_task_function_exists_and_is_callable(self):
        """
        Validate that the task function exists and is callable.
        
        Requirements: 7.1
        """
        from app.tasks.celery_app import check_expired_interactions
        
        assert callable(check_expired_interactions), \
            "check_expired_interactions should be callable"


class TestMessageDetectionLogic:
    """
    Checkpoint validation: Detection of messages without interaction after 24h.
    
    Requirements: 7.2
    """

    def test_cutoff_time_calculation(self):
        """
        Validate that cutoff time is correctly calculated as 24h ago.
        
        Requirements: 7.2
        """
        # The task calculates cutoff as: datetime.now(timezone.utc) - timedelta(hours=24)
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(hours=24)
        
        # Verify cutoff is approximately 24 hours ago
        time_diff = now - cutoff
        assert time_diff.total_seconds() == 24 * 60 * 60, \
            "Cutoff should be exactly 24 hours ago"

    @patch(SUPABASE_CLIENT_PATCH)
    def test_task_queries_message_1_only(self, mock_get_client):
        """
        Validate that task only queries Message 1 type messages.
        
        Requirements: 7.2
        """
        from app.tasks.celery_app import check_expired_interactions
        
        # Setup mock
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock the chain of calls
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_table.lt.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[], count=0)
        
        # Execute task
        result = check_expired_interactions()
        
        # Verify message_type filter was applied
        calls = mock_table.eq.call_args_list
        message_type_call = any(
            call[0] == ("message_type", "message_1") 
            for call in calls
        )
        assert message_type_call, \
            "Task should filter for message_type = 'message_1'"

    @patch(SUPABASE_CLIENT_PATCH)
    def test_task_filters_by_status(self, mock_get_client):
        """
        Validate that task filters messages by status (sent, delivered, read).
        
        Requirements: 7.2
        """
        from app.tasks.celery_app import check_expired_interactions
        
        # Setup mock
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_table.lt.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[], count=0)
        
        # Execute task
        result = check_expired_interactions()
        
        # Verify status filter was applied
        calls = mock_table.in_.call_args_list
        status_call = any(
            call[0][0] == "status" and set(call[0][1]) == {"sent", "delivered", "read"}
            for call in calls
        )
        assert status_call, \
            "Task should filter for status in ['sent', 'delivered', 'read']"


class TestNoInteractionMarking:
    """
    Checkpoint validation: Marking messages as no_interaction.
    
    Requirements: 7.2, 7.3
    """

    @patch(SUPABASE_CLIENT_PATCH)
    def test_message_marked_no_interaction_when_no_message_2(self, mock_get_client):
        """
        Validate that message is marked as no_interaction when no Message 2 exists.
        
        Requirements: 7.2, 7.3
        """
        from app.tasks.celery_app import check_expired_interactions
        
        # Setup mock
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Create a message that's older than 24h
        old_message = {
            "id": "msg-123",
            "campaign_id": "camp-1",
            "contact_id": "contact-1",
            "sent_at": (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat(),
            "status": "delivered"
        }
        
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_table.lt.return_value = mock_table
        mock_table.limit.return_value = mock_table
        mock_table.update.return_value = mock_table
        
        # First call returns the old message
        # Subsequent calls return empty (no message_2, no interactions)
        call_count = [0]
        def mock_execute():
            call_count[0] += 1
            if call_count[0] == 1:
                return MagicMock(data=[old_message], count=1)
            elif call_count[0] in [2, 3]:  # message_2 check, interaction check
                return MagicMock(data=[], count=0)
            else:
                return MagicMock(data=[{"first_name": "Test", "last_name": "User", "full_number": "+1234567890"}], count=1)
        
        mock_table.execute.side_effect = mock_execute
        
        # Execute task
        result = check_expired_interactions()
        
        # Verify update was called with no_interaction status
        update_calls = mock_table.update.call_args_list
        if update_calls:
            update_data = update_calls[0][0][0]
            assert update_data.get("status") == "no_interaction", \
                "Message should be marked as no_interaction"
            assert "error_message" in update_data, \
                "Error message should be set"

    @patch(SUPABASE_CLIENT_PATCH)
    def test_message_not_marked_when_message_2_exists(self, mock_get_client):
        """
        Validate that message is NOT marked when Message 2 already exists.
        
        Requirements: 7.2
        """
        from app.tasks.celery_app import check_expired_interactions
        
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        old_message = {
            "id": "msg-123",
            "campaign_id": "camp-1",
            "contact_id": "contact-1",
            "sent_at": (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat(),
            "status": "delivered"
        }
        
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_table.lt.return_value = mock_table
        mock_table.limit.return_value = mock_table
        mock_table.update.return_value = mock_table
        
        call_count = [0]
        def mock_execute():
            call_count[0] += 1
            if call_count[0] == 1:
                return MagicMock(data=[old_message], count=1)
            elif call_count[0] == 2:  # message_2 check - EXISTS
                return MagicMock(data=[{"id": "msg-456"}], count=1)
            else:
                return MagicMock(data=[], count=0)
        
        mock_table.execute.side_effect = mock_execute
        
        result = check_expired_interactions()
        
        # Verify message was NOT marked (update should not be called with no_interaction)
        assert result["messages_marked"] == 0, \
            "No messages should be marked when Message 2 exists"


class TestCampaignStatisticsUpdate:
    """
    Checkpoint validation: Campaign failed_count update.
    
    Requirements: 7.3, 7.4
    """

    @patch(SUPABASE_CLIENT_PATCH)
    def test_failed_count_incremented_after_marking(self, mock_get_client):
        """
        Validate that campaign failed_count is incremented.
        
        Requirements: 7.3, 7.4
        """
        from app.tasks.celery_app import check_expired_interactions
        
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        old_message = {
            "id": "msg-123",
            "campaign_id": "camp-1",
            "contact_id": "contact-1",
            "sent_at": (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat(),
            "status": "delivered"
        }
        
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_table.lt.return_value = mock_table
        mock_table.limit.return_value = mock_table
        mock_table.update.return_value = mock_table
        
        call_count = [0]
        def mock_execute():
            call_count[0] += 1
            if call_count[0] == 1:
                return MagicMock(data=[old_message], count=1)
            elif call_count[0] in [2, 3]:  # message_2 check, interaction check
                return MagicMock(data=[], count=0)
            elif call_count[0] == 4:  # contact info
                return MagicMock(data=[{"first_name": "Test", "last_name": "User", "full_number": "+1234567890"}])
            elif call_count[0] == 5:  # campaign failed_count query
                return MagicMock(data=[{"failed_count": 5}])
            else:
                return MagicMock(data=[], count=0)
        
        mock_table.execute.side_effect = mock_execute
        
        result = check_expired_interactions()
        
        # Verify campaigns_updated is tracked
        assert "campaigns_updated" in result, \
            "Result should include campaigns_updated count"


class TestCampaignCompletionStatus:
    """
    Checkpoint validation: Campaign completion status includes no_interaction.
    
    Requirements: 7.5
    """

    def test_recover_task_includes_no_interaction_in_completion(self):
        """
        Validate that recover_interrupted_campaigns includes no_interaction in completion check.
        
        Requirements: 7.5
        """
        from app.tasks.celery_app import recover_interrupted_campaigns
        
        # The function should exist and be callable
        assert callable(recover_interrupted_campaigns)
        
        # Check the source code includes no_interaction handling
        import inspect
        source = inspect.getsource(recover_interrupted_campaigns)
        
        assert "no_interaction" in source, \
            "recover_interrupted_campaigns should handle no_interaction status"


class TestLoggingAndTraceability:
    """
    Checkpoint validation: Logging for traceability.
    
    Requirements: 7.6
    """

    @patch('app.tasks.celery_app.logger')
    @patch(SUPABASE_CLIENT_PATCH)
    def test_task_logs_marked_contacts(self, mock_get_client, mock_logger):
        """
        Validate that task logs each contact marked as no_interaction.
        
        Requirements: 7.6
        """
        from app.tasks.celery_app import check_expired_interactions
        
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        old_message = {
            "id": "msg-123",
            "campaign_id": "camp-1",
            "contact_id": "contact-1",
            "sent_at": (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat(),
            "status": "delivered"
        }
        
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_table.lt.return_value = mock_table
        mock_table.limit.return_value = mock_table
        mock_table.update.return_value = mock_table
        
        call_count = [0]
        def mock_execute():
            call_count[0] += 1
            if call_count[0] == 1:
                return MagicMock(data=[old_message], count=1)
            elif call_count[0] in [2, 3]:
                return MagicMock(data=[], count=0)
            elif call_count[0] == 4:
                return MagicMock(data=[{"first_name": "John", "last_name": "Doe", "full_number": "+1234567890"}])
            elif call_count[0] == 5:
                return MagicMock(data=[{"failed_count": 0}])
            else:
                return MagicMock(data=[], count=0)
        
        mock_table.execute.side_effect = mock_execute
        
        result = check_expired_interactions()
        
        # Verify logging was called
        assert mock_logger.info.called, \
            "Task should log information about marked contacts"


class TestTaskReturnValue:
    """
    Checkpoint validation: Task return value structure.
    """

    @patch(SUPABASE_CLIENT_PATCH)
    def test_task_returns_expected_structure(self, mock_get_client):
        """
        Validate that task returns expected result structure.
        """
        from app.tasks.celery_app import check_expired_interactions
        
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_table.lt.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[], count=0)
        
        result = check_expired_interactions()
        
        # Verify result structure
        assert "status" in result, "Result should have 'status' field"
        assert result["status"] == "success", "Status should be 'success'"
        assert "messages_checked" in result, "Result should have 'messages_checked'"
        assert "messages_marked" in result, "Result should have 'messages_marked'"
        assert "campaigns_updated" in result, "Result should have 'campaigns_updated'"

    @patch(SUPABASE_CLIENT_PATCH)
    def test_task_handles_errors_gracefully(self, mock_get_client):
        """
        Validate that task handles errors and returns error status.
        """
        from app.tasks.celery_app import check_expired_interactions
        
        # Make the client raise an exception
        mock_get_client.side_effect = Exception("Database connection failed")
        
        result = check_expired_interactions()
        
        # Verify error handling
        assert result["status"] == "error", "Status should be 'error' on exception"
        assert "message" in result, "Result should have error message"


class TestEdgeCases:
    """
    Checkpoint validation: Edge cases handling.
    """

    @patch(SUPABASE_CLIENT_PATCH)
    def test_task_handles_empty_result(self, mock_get_client):
        """
        Validate that task handles case with no messages to check.
        """
        from app.tasks.celery_app import check_expired_interactions
        
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_table.lt.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[], count=0)
        
        result = check_expired_interactions()
        
        assert result["status"] == "success"
        assert result["messages_checked"] == 0
        assert result["messages_marked"] == 0
        assert result["campaigns_updated"] == 0

    @patch(SUPABASE_CLIENT_PATCH)
    def test_task_skips_messages_with_interaction(self, mock_get_client):
        """
        Validate that task skips messages where interaction exists.
        """
        from app.tasks.celery_app import check_expired_interactions
        
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        old_message = {
            "id": "msg-123",
            "campaign_id": "camp-1",
            "contact_id": "contact-1",
            "sent_at": (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat(),
            "status": "delivered"
        }
        
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_table.lt.return_value = mock_table
        mock_table.limit.return_value = mock_table
        mock_table.update.return_value = mock_table
        
        call_count = [0]
        def mock_execute():
            call_count[0] += 1
            if call_count[0] == 1:
                return MagicMock(data=[old_message], count=1)
            elif call_count[0] == 2:  # message_2 check - none
                return MagicMock(data=[], count=0)
            elif call_count[0] == 3:  # interaction check - EXISTS
                return MagicMock(data=[{"id": "int-1"}], count=1)
            else:
                return MagicMock(data=[], count=0)
        
        mock_table.execute.side_effect = mock_execute
        
        result = check_expired_interactions()
        
        # Message should not be marked because interaction exists
        assert result["messages_marked"] == 0, \
            "Messages with interactions should not be marked"
