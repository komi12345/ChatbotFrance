"""
Unit tests for WassengerService.

Tests the core functionality of the Wassenger service including:
- Service initialization
- Phone number formatting
- Webhook payload parsing
- Dataclasses (WassengerResponse, WassengerWebhookInteraction)
- Error handling and error message mapping

Requirements: 9.2
"""
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from app.services.wassenger_service import (
    WassengerService,
    WassengerResponse,
    WassengerWebhookInteraction,
    WASSENGER_ERROR_MESSAGES,
    DEVICE_RECONNECT_INSTRUCTIONS,
)


# ==========================================================================
# TESTS: DATACLASSES
# ==========================================================================

class TestWassengerResponseDataclass:
    """Tests for WassengerResponse dataclass."""

    def test_success_response_creation(self):
        """Test creating a successful response."""
        response = WassengerResponse(
            success=True,
            message_id="msg_abc123",
            raw_response={"id": "msg_abc123", "status": "queued"}
        )
        
        assert response.success is True
        assert response.message_id == "msg_abc123"
        assert response.error_code is None
        assert response.error_message is None
        assert response.raw_response == {"id": "msg_abc123", "status": "queued"}

    def test_error_response_creation(self):
        """Test creating an error response."""
        response = WassengerResponse(
            success=False,
            error_code="device_not_connected",
            error_message="L'appareil WhatsApp doit être reconnecté",
            raw_response={"error": "device_not_connected"}
        )
        
        assert response.success is False
        assert response.message_id is None
        assert response.error_code == "device_not_connected"
        assert response.error_message == "L'appareil WhatsApp doit être reconnecté"

    def test_minimal_response_creation(self):
        """Test creating a response with only required field."""
        response = WassengerResponse(success=True)
        
        assert response.success is True
        assert response.message_id is None
        assert response.error_code is None
        assert response.error_message is None
        assert response.raw_response is None


class TestWassengerWebhookInteractionDataclass:
    """Tests for WassengerWebhookInteraction dataclass."""

    def test_reply_interaction_creation(self):
        """Test creating a reply interaction."""
        timestamp = datetime(2025, 1, 15, 10, 30, 0)
        interaction = WassengerWebhookInteraction(
            contact_phone="22890123456",
            interaction_type="reply",
            content="Bonjour!",
            wassenger_message_id="msg_xyz789",
            timestamp=timestamp
        )
        
        assert interaction.contact_phone == "22890123456"
        assert interaction.interaction_type == "reply"
        assert interaction.content == "Bonjour!"
        assert interaction.wassenger_message_id == "msg_xyz789"
        assert interaction.timestamp == timestamp
        assert interaction.error_message is None

    def test_status_interaction_creation(self):
        """Test creating a status update interaction."""
        interaction = WassengerWebhookInteraction(
            contact_phone="22890123456",
            interaction_type="delivered",
            wassenger_message_id="msg_abc123"
        )
        
        assert interaction.contact_phone == "22890123456"
        assert interaction.interaction_type == "delivered"
        assert interaction.content is None
        assert interaction.wassenger_message_id == "msg_abc123"

    def test_failed_interaction_with_error(self):
        """Test creating a failed interaction with error message."""
        interaction = WassengerWebhookInteraction(
            contact_phone="22890123456",
            interaction_type="failed",
            wassenger_message_id="msg_abc123",
            error_message="Invalid phone number"
        )
        
        assert interaction.interaction_type == "failed"
        assert interaction.error_message == "Invalid phone number"


# ==========================================================================
# TESTS: SERVICE INITIALIZATION
# ==========================================================================

class TestWassengerServiceInitialization:
    """Tests for WassengerService initialization."""

    @patch('app.services.wassenger_service.settings')
    def test_service_initialization_with_valid_config(self, mock_settings):
        """Test service initializes correctly with valid configuration."""
        mock_settings.WASSENGER_API_KEY = "wsp_live_test_key_123"
        mock_settings.WASSENGER_DEVICE_ID = "device_abc123"
        
        service = WassengerService()
        
        assert service.api_key == "wsp_live_test_key_123"
        assert service.device_id == "device_abc123"
        assert service._client is None  # Client is created on-demand now
        assert service.BASE_URL == "https://api.wassenger.com/v1"

    @patch('app.services.wassenger_service.settings')
    def test_service_has_correct_headers(self, mock_settings):
        """Test service client factory creates client with correct authorization headers."""
        mock_settings.WASSENGER_API_KEY = "wsp_live_test_key_123"
        mock_settings.WASSENGER_DEVICE_ID = "device_abc123"
        
        service = WassengerService()
        
        # Get a client instance to check headers
        client = service._get_client()
        
        # Check that Authorization header is set correctly
        assert "Authorization" in client.headers
        assert client.headers["Authorization"] == "Bearer wsp_live_test_key_123"


# ==========================================================================
# TESTS: PHONE NUMBER FORMATTING
# ==========================================================================

class TestPhoneNumberFormatting:
    """Tests for phone number formatting."""

    def setup_method(self):
        """Create a service instance for testing."""
        self.service = WassengerService.__new__(WassengerService)

    def test_format_phone_with_plus_prefix(self):
        """Test formatting phone number with + prefix."""
        result = self.service.format_phone_number("+22890123456")
        assert result == "22890123456"

    def test_format_phone_without_plus_prefix(self):
        """Test formatting phone number without + prefix."""
        result = self.service.format_phone_number("22890123456")
        assert result == "22890123456"

    def test_format_phone_with_spaces(self):
        """Test formatting phone number with spaces."""
        result = self.service.format_phone_number("228 90 12 34 56")
        assert result == "22890123456"

    def test_format_phone_with_plus_and_spaces(self):
        """Test formatting phone number with + and spaces."""
        result = self.service.format_phone_number("+228 90 12 34 56")
        assert result == "22890123456"

    def test_format_phone_with_dashes(self):
        """Test formatting phone number with dashes."""
        result = self.service.format_phone_number("228-90-12-34-56")
        assert result == "22890123456"

    def test_format_phone_with_parentheses(self):
        """Test formatting phone number with parentheses (US format)."""
        result = self.service.format_phone_number("(228) 901-2345")
        assert result == "2289012345"

    def test_format_phone_with_dots(self):
        """Test formatting phone number with dots."""
        result = self.service.format_phone_number("228.90.12.34.56")
        assert result == "22890123456"

    def test_format_empty_phone(self):
        """Test formatting empty phone number."""
        result = self.service.format_phone_number("")
        assert result == ""

    def test_format_phone_only_special_chars(self):
        """Test formatting phone with only special characters."""
        result = self.service.format_phone_number("+-() ")
        assert result == ""


# ==========================================================================
# TESTS: WEBHOOK PAYLOAD PARSING
# ==========================================================================

class TestWebhookPayloadParsing:
    """Tests for webhook payload parsing."""

    def setup_method(self):
        """Create a service instance for testing."""
        self.service = WassengerService.__new__(WassengerService)

    def test_parse_incoming_message_webhook(self):
        """Test parsing message:in:new webhook."""
        payload = {
            "event": "message:in:new",
            "data": {
                "id": "msg_xyz789",
                "fromNumber": "22890123456",
                "body": "Bonjour, je suis intéressé",
                "timestamp": "2025-01-15T10:35:00Z",
                "device": "device_abc123"
            }
        }
        
        interactions = self.service.parse_webhook_payload(payload)
        
        assert len(interactions) == 1
        interaction = interactions[0]
        assert interaction.contact_phone == "22890123456"
        assert interaction.interaction_type == "reply"
        assert interaction.content == "Bonjour, je suis intéressé"
        assert interaction.wassenger_message_id == "msg_xyz789"
        assert interaction.timestamp is not None

    def test_parse_message_sent_webhook(self):
        """Test parsing message:out:sent webhook."""
        payload = {
            "event": "message:out:sent",
            "data": {
                "id": "msg_abc123",
                "phone": "22890123456",
                "timestamp": "2025-01-15T10:30:00Z"
            }
        }
        
        interactions = self.service.parse_webhook_payload(payload)
        
        assert len(interactions) == 1
        interaction = interactions[0]
        assert interaction.interaction_type == "sent"
        assert interaction.wassenger_message_id == "msg_abc123"

    def test_parse_message_delivered_webhook(self):
        """Test parsing message:out:delivered webhook."""
        payload = {
            "event": "message:out:delivered",
            "data": {
                "id": "msg_abc123",
                "phone": "22890123456",
                "timestamp": "2025-01-15T10:31:00Z"
            }
        }
        
        interactions = self.service.parse_webhook_payload(payload)
        
        assert len(interactions) == 1
        interaction = interactions[0]
        assert interaction.interaction_type == "delivered"

    def test_parse_message_read_webhook(self):
        """Test parsing message:out:read webhook."""
        payload = {
            "event": "message:out:read",
            "data": {
                "id": "msg_abc123",
                "phone": "22890123456",
                "timestamp": "2025-01-15T10:32:00Z"
            }
        }
        
        interactions = self.service.parse_webhook_payload(payload)
        
        assert len(interactions) == 1
        interaction = interactions[0]
        assert interaction.interaction_type == "read"

    def test_parse_message_failed_webhook(self):
        """Test parsing message:out:failed webhook with error."""
        payload = {
            "event": "message:out:failed",
            "data": {
                "id": "msg_abc123",
                "phone": "22890123456",
                "timestamp": "2025-01-15T10:30:00Z",
                "error": "Invalid phone number format"
            }
        }
        
        interactions = self.service.parse_webhook_payload(payload)
        
        assert len(interactions) == 1
        interaction = interactions[0]
        assert interaction.interaction_type == "failed"
        assert interaction.error_message == "Invalid phone number format"

    def test_parse_message_update_webhook(self):
        """Test parsing message:update webhook (Wassenger 2025 format)."""
        payload = {
            "event": "message:update",
            "data": {
                "id": "msg_abc123",
                "phone": "22890123456",
                "status": "delivered",
                "timestamp": "2025-01-15T10:31:00Z"
            }
        }
        
        interactions = self.service.parse_webhook_payload(payload)
        
        assert len(interactions) == 1
        interaction = interactions[0]
        assert interaction.interaction_type == "delivered"
        assert interaction.wassenger_message_id == "msg_abc123"

    def test_parse_unknown_event_returns_empty(self):
        """Test parsing unknown event type returns empty list."""
        payload = {
            "event": "unknown:event:type",
            "data": {"id": "msg_abc123"}
        }
        
        interactions = self.service.parse_webhook_payload(payload)
        
        assert len(interactions) == 0

    def test_parse_empty_payload_returns_empty(self):
        """Test parsing empty payload returns empty list."""
        payload = {}
        
        interactions = self.service.parse_webhook_payload(payload)
        
        assert len(interactions) == 0

    def test_parse_reaction_webhook(self):
        """Test parsing message:reaction webhook."""
        payload = {
            "event": "message:reaction",
            "data": {
                "fromNumber": "22890123456",
                "messageId": "msg_abc123",
                "reaction": "👍",
                "timestamp": "2025-01-15T10:32:00Z"
            }
        }
        
        interactions = self.service.parse_webhook_payload(payload)
        
        assert len(interactions) == 1
        interaction = interactions[0]
        assert interaction.interaction_type == "reaction"
        assert interaction.content == "👍"


# ==========================================================================
# TESTS: ERROR HANDLING
# ==========================================================================

class TestErrorHandling:
    """Tests for error handling and error message mapping."""

    def test_get_error_details_device_not_connected(self):
        """Test error details for device_not_connected."""
        details = WassengerService.get_error_details("device_not_connected")
        
        assert details["error_type"] == "device_not_connected"
        assert "reconnecté" in details["message"].lower() or "qr code" in details["message"].lower()
        assert details["requires_reconnect"] is True
        assert details["instructions"] is not None

    def test_get_error_details_invalid_phone_number(self):
        """Test error details for invalid_phone_number."""
        details = WassengerService.get_error_details("invalid_phone_number")
        
        assert details["error_type"] == "invalid_phone_number"
        assert "numéro" in details["message"].lower() or "format" in details["message"].lower()
        assert details["requires_reconnect"] is False

    def test_get_error_details_rate_limit_exceeded(self):
        """Test error details for rate_limit_exceeded."""
        details = WassengerService.get_error_details("rate_limit_exceeded")
        
        assert details["error_type"] == "rate_limit_exceeded"
        assert details["retry_delay_seconds"] == 60
        assert "limite" in details["message"].lower() or "débit" in details["message"].lower()

    def test_get_error_details_session_expired(self):
        """Test error details for session_expired."""
        details = WassengerService.get_error_details("session_expired")
        
        assert details["error_type"] == "session_expired"
        assert details["requires_reconnect"] is True
        assert "expiré" in details["message"].lower() or "session" in details["message"].lower()

    def test_get_error_details_unknown_error(self):
        """Test error details for unknown error code."""
        details = WassengerService.get_error_details("some_unknown_error_code")
        
        assert details["error_type"] == "some_unknown_error_code"
        assert "some_unknown_error_code" in details["message"]
        assert details["requires_reconnect"] is False

    def test_all_known_error_codes_have_messages(self):
        """Test that all known error codes have French messages."""
        known_codes = [
            "device_not_connected",
            "invalid_phone_number",
            "rate_limit_exceeded",
            "session_expired",
            "message_too_long",
            "unauthorized",
            "device_not_found",
            "insufficient_credits"
        ]
        
        for code in known_codes:
            assert code in WASSENGER_ERROR_MESSAGES, f"Missing message for {code}"
            assert len(WASSENGER_ERROR_MESSAGES[code]) > 0, f"Empty message for {code}"

    def test_device_reconnect_instructions_exist(self):
        """Test that device reconnect instructions are defined."""
        assert DEVICE_RECONNECT_INSTRUCTIONS is not None
        assert len(DEVICE_RECONNECT_INSTRUCTIONS) > 0
        assert "wassenger" in DEVICE_RECONNECT_INSTRUCTIONS.lower()


# ==========================================================================
# TESTS: TIMESTAMP PARSING
# ==========================================================================

class TestTimestampParsing:
    """Tests for timestamp parsing."""

    def setup_method(self):
        """Create a service instance for testing."""
        self.service = WassengerService.__new__(WassengerService)

    def test_parse_valid_iso_timestamp(self):
        """Test parsing valid ISO 8601 timestamp."""
        result = self.service._parse_timestamp("2025-01-15T10:30:00Z")
        
        assert result is not None
        assert isinstance(result, datetime)
        assert result.year == 2025
        assert result.month == 1
        assert result.day == 15

    def test_parse_none_timestamp_returns_current(self):
        """Test parsing None timestamp returns current time."""
        result = self.service._parse_timestamp(None)
        
        assert result is not None
        assert isinstance(result, datetime)

    def test_parse_empty_timestamp_returns_current(self):
        """Test parsing empty timestamp returns current time."""
        result = self.service._parse_timestamp("")
        
        assert result is not None
        assert isinstance(result, datetime)

    def test_parse_invalid_timestamp_returns_current(self):
        """Test parsing invalid timestamp returns current time."""
        result = self.service._parse_timestamp("not-a-timestamp")
        
        assert result is not None
        assert isinstance(result, datetime)
