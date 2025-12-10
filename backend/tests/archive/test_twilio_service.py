"""
Tests unitaires pour le service Twilio WhatsApp Sandbox.

Ce fichier contient des tests de base pour vérifier que le service Twilio
fonctionne correctement après la migration depuis Gupshup.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.twilio_service import (
    TwilioService,
    TwilioResponse,
    TwilioWebhookInteraction,
    SANDBOX_NOT_JOINED_ERROR_CODES,
    SESSION_EXPIRED_ERROR_CODES,
    SANDBOX_JOIN_INSTRUCTIONS,
    SESSION_EXPIRED_INSTRUCTIONS,
)


class TestTwilioServiceInitialization:
    """Tests pour l'initialisation du service Twilio."""
    
    def test_service_initializes(self):
        """Vérifie que le service s'initialise correctement."""
        service = TwilioService()
        assert service is not None
        assert service.sandbox_number == "+14155238886"
    
    def test_service_has_client(self):
        """Vérifie que le client Twilio est initialisé."""
        service = TwilioService()
        assert service.client is not None
    
    def test_service_has_validator(self):
        """Vérifie que le validateur de signature est initialisé."""
        service = TwilioService()
        assert service.validator is not None


class TestPhoneNumberFormatting:
    """Tests pour le formatage des numéros de téléphone."""
    
    def test_format_number_without_plus(self):
        """Teste le formatage d'un numéro sans +."""
        service = TwilioService()
        result = service.format_whatsapp_number("33612345678")
        assert result == "whatsapp:+33612345678"
    
    def test_format_number_with_plus(self):
        """Teste le formatage d'un numéro avec +."""
        service = TwilioService()
        result = service.format_whatsapp_number("+33612345678")
        assert result == "whatsapp:+33612345678"
    
    def test_format_number_already_whatsapp_format(self):
        """Teste le formatage d'un numéro déjà au format whatsapp:."""
        service = TwilioService()
        result = service.format_whatsapp_number("whatsapp:+33612345678")
        assert result == "whatsapp:+33612345678"
    
    def test_format_number_with_spaces(self):
        """Teste le formatage d'un numéro avec espaces."""
        service = TwilioService()
        result = service.format_whatsapp_number("  +33612345678  ")
        assert result == "whatsapp:+33612345678"


class TestPhoneNumberExtraction:
    """Tests pour l'extraction des numéros de téléphone."""
    
    def test_extract_from_whatsapp_format(self):
        """Teste l'extraction d'un numéro au format whatsapp:."""
        service = TwilioService()
        result = service.extract_phone_from_whatsapp("whatsapp:+33612345678")
        assert result == "+33612345678"
    
    def test_extract_from_plain_number(self):
        """Teste l'extraction d'un numéro sans préfixe."""
        service = TwilioService()
        result = service.extract_phone_from_whatsapp("+33612345678")
        assert result == "+33612345678"


class TestContentVariablesEncoding:
    """Tests pour l'encodage des variables de template."""
    
    def test_encode_empty_list(self):
        """Teste l'encodage d'une liste vide."""
        service = TwilioService()
        result = service.encode_content_variables([])
        assert result == "{}"
    
    def test_encode_single_param(self):
        """Teste l'encodage d'un seul paramètre."""
        service = TwilioService()
        result = service.encode_content_variables(["value1"])
        assert result == '{"1": "value1"}'
    
    def test_encode_multiple_params(self):
        """Teste l'encodage de plusieurs paramètres."""
        service = TwilioService()
        result = service.encode_content_variables(["a", "b", "c"])
        assert result == '{"1": "a", "2": "b", "3": "c"}'


class TestTemplateParameterValidation:
    """Tests pour la validation des paramètres de template."""
    
    def test_validate_sufficient_params(self):
        """Teste la validation avec suffisamment de paramètres."""
        service = TwilioService()
        is_valid, error = service.validate_template_parameters(
            "HXtest", ["a", "b"], 2
        )
        assert is_valid is True
        assert error is None
    
    def test_validate_insufficient_params(self):
        """Teste la validation avec paramètres insuffisants."""
        service = TwilioService()
        is_valid, error = service.validate_template_parameters(
            "HXtest", ["a"], 2
        )
        assert is_valid is False
        assert error is not None
        assert "2" in error  # Doit mentionner le nombre requis
    
    def test_validate_none_params(self):
        """Teste la validation avec paramètres None."""
        service = TwilioService()
        is_valid, error = service.validate_template_parameters(
            "HXtest", None, 2
        )
        assert is_valid is False
        assert error is not None


class TestWebhookParsing:
    """Tests pour le parsing des webhooks Twilio."""
    
    def test_parse_incoming_message(self):
        """Teste le parsing d'un message entrant."""
        service = TwilioService()
        payload = {
            "From": "whatsapp:+33612345678",
            "Body": "Hello world",
            "MessageSid": "SM1234567890abcdef"
        }
        interactions = service.parse_webhook_payload(payload)
        
        assert len(interactions) == 1
        assert interactions[0].contact_phone == "+33612345678"
        assert interactions[0].content == "Hello world"
        assert interactions[0].twilio_message_sid == "SM1234567890abcdef"
        assert interactions[0].interaction_type == "reply"
    
    def test_parse_delivery_status_delivered(self):
        """Teste le parsing d'un statut de livraison 'delivered'."""
        service = TwilioService()
        payload = {
            "MessageSid": "SM1234567890abcdef",
            "MessageStatus": "delivered",
            "To": "whatsapp:+33612345678"
        }
        interactions = service.parse_webhook_payload(payload)
        
        assert len(interactions) == 1
        assert interactions[0].interaction_type == "delivered"
        assert interactions[0].contact_phone == "+33612345678"
    
    def test_parse_delivery_status_failed(self):
        """Teste le parsing d'un statut de livraison 'failed'."""
        service = TwilioService()
        payload = {
            "MessageSid": "SM1234567890abcdef",
            "MessageStatus": "failed",
            "To": "whatsapp:+33612345678",
            "ErrorCode": "63007"
        }
        interactions = service.parse_webhook_payload(payload)
        
        assert len(interactions) == 1
        assert interactions[0].interaction_type == "failed"
        assert interactions[0].error_code == 63007


class TestTwilioDataClasses:
    """Tests pour les dataclasses Twilio."""
    
    def test_twilio_response_success(self):
        """Teste la création d'une TwilioResponse de succès."""
        response = TwilioResponse(
            success=True,
            message_sid="SM123"
        )
        assert response.success is True
        assert response.message_sid == "SM123"
        assert response.error_code is None
    
    def test_twilio_response_failure(self):
        """Teste la création d'une TwilioResponse d'échec."""
        response = TwilioResponse(
            success=False,
            error_code=63007,
            error_message="Recipient not in sandbox"
        )
        assert response.success is False
        assert response.error_code == 63007
        assert response.message_sid is None
    
    def test_twilio_webhook_interaction(self):
        """Teste la création d'une TwilioWebhookInteraction."""
        interaction = TwilioWebhookInteraction(
            contact_phone="+33612345678",
            interaction_type="reply",
            content="Test message"
        )
        assert interaction.contact_phone == "+33612345678"
        assert interaction.interaction_type == "reply"
        assert interaction.content == "Test message"


class TestSandboxErrorHandling:
    """Tests pour la gestion des erreurs Sandbox (Requirements 7.1, 7.3, 7.5)."""
    
    def test_is_sandbox_not_joined_error_63007(self):
        """Teste la détection de l'erreur 63007 (non-inscrit au Sandbox)."""
        service = TwilioService()
        assert service.is_sandbox_not_joined_error(63007) is True
    
    def test_is_sandbox_not_joined_error_21608(self):
        """Teste la détection de l'erreur 21608 (numéro non vérifié)."""
        service = TwilioService()
        assert service.is_sandbox_not_joined_error(21608) is True
    
    def test_is_sandbox_not_joined_error_other_code(self):
        """Teste qu'un autre code d'erreur n'est pas détecté comme non-inscrit."""
        service = TwilioService()
        assert service.is_sandbox_not_joined_error(30006) is False
        assert service.is_sandbox_not_joined_error(20003) is False
    
    def test_is_sandbox_not_joined_error_none(self):
        """Teste la gestion de None comme code d'erreur."""
        service = TwilioService()
        assert service.is_sandbox_not_joined_error(None) is False
    
    def test_is_session_expired_error_63003(self):
        """Teste la détection de l'erreur 63003 (session expirée)."""
        service = TwilioService()
        assert service.is_session_expired_error(63003) is True
    
    def test_is_session_expired_error_63001(self):
        """Teste la détection de l'erreur 63001 (fenêtre 24h dépassée)."""
        service = TwilioService()
        assert service.is_session_expired_error(63001) is True
    
    def test_is_session_expired_error_other_code(self):
        """Teste qu'un autre code d'erreur n'est pas détecté comme session expirée."""
        service = TwilioService()
        assert service.is_session_expired_error(63007) is False
        assert service.is_session_expired_error(30006) is False
    
    def test_is_session_expired_error_none(self):
        """Teste la gestion de None comme code d'erreur."""
        service = TwilioService()
        assert service.is_session_expired_error(None) is False


class TestSandboxErrorDetails:
    """Tests pour les détails d'erreur Sandbox avec instructions."""
    
    def test_get_sandbox_error_details_not_joined(self):
        """Teste les détails pour une erreur non-inscrit (63007)."""
        service = TwilioService()
        details = service.get_sandbox_error_details(63007)
        
        assert details["error_type"] == "not_joined"
        assert details["is_sandbox_error"] is True
        assert details["instructions"] == SANDBOX_JOIN_INSTRUCTIONS
        assert "join" in details["message"].lower()
    
    def test_get_sandbox_error_details_session_expired(self):
        """Teste les détails pour une erreur session expirée (63003)."""
        service = TwilioService()
        details = service.get_sandbox_error_details(63003)
        
        assert details["error_type"] == "session_expired"
        assert details["is_sandbox_error"] is True
        assert details["instructions"] == SESSION_EXPIRED_INSTRUCTIONS
        assert "24h" in details["message"]
    
    def test_get_sandbox_error_details_other_error(self):
        """Teste les détails pour une erreur non-Sandbox."""
        service = TwilioService()
        details = service.get_sandbox_error_details(30006)
        
        assert details["error_type"] == "other"
        assert details["is_sandbox_error"] is False
        assert details["instructions"] is None
    
    def test_get_sandbox_error_details_unknown_code(self):
        """Teste les détails pour un code d'erreur inconnu."""
        service = TwilioService()
        details = service.get_sandbox_error_details(99999)
        
        assert details["error_type"] == "other"
        assert details["is_sandbox_error"] is False
        assert "99999" in details["message"]
    
    def test_get_sandbox_error_details_none(self):
        """Teste les détails pour un code d'erreur None."""
        service = TwilioService()
        details = service.get_sandbox_error_details(None)
        
        assert details["error_type"] == "other"
        assert details["is_sandbox_error"] is False


class TestSandboxErrorConstants:
    """Tests pour les constantes d'erreur Sandbox."""
    
    def test_sandbox_not_joined_codes_contains_63007(self):
        """Vérifie que 63007 est dans les codes non-inscrit."""
        assert 63007 in SANDBOX_NOT_JOINED_ERROR_CODES
    
    def test_sandbox_not_joined_codes_contains_21608(self):
        """Vérifie que 21608 est dans les codes non-inscrit."""
        assert 21608 in SANDBOX_NOT_JOINED_ERROR_CODES
    
    def test_session_expired_codes_contains_63003(self):
        """Vérifie que 63003 est dans les codes session expirée."""
        assert 63003 in SESSION_EXPIRED_ERROR_CODES
    
    def test_session_expired_codes_contains_63001(self):
        """Vérifie que 63001 est dans les codes session expirée."""
        assert 63001 in SESSION_EXPIRED_ERROR_CODES
    
    def test_join_instructions_not_empty(self):
        """Vérifie que les instructions de join ne sont pas vides."""
        assert len(SANDBOX_JOIN_INSTRUCTIONS) > 0
        assert "join" in SANDBOX_JOIN_INSTRUCTIONS.lower()
    
    def test_session_expired_instructions_not_empty(self):
        """Vérifie que les instructions session expirée ne sont pas vides."""
        assert len(SESSION_EXPIRED_INSTRUCTIONS) > 0
        assert "24h" in SESSION_EXPIRED_INSTRUCTIONS
