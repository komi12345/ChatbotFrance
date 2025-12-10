"""
Tests pour la validation des credentials Gupshup.

Ce fichier contient des tests pytest pour vérifier:
- La présence des variables d'environnement requises
- La validité de l'API key Gupshup
- La connexion à l'API Gupshup
"""
import os
import pytest
import httpx
from unittest.mock import patch, MagicMock

# Import du service et config
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.config import settings


class TestGupshupEnvironmentVariables:
    """Tests pour vérifier la présence des variables d'environnement Gupshup."""
    
    def test_gupshup_api_key_is_set(self):
        """Vérifie que GUPSHUP_API_KEY est définie et non vide."""
        api_key = os.getenv("GUPSHUP_API_KEY") or settings.GUPSHUP_API_KEY
        assert api_key is not None, "GUPSHUP_API_KEY n'est pas définie"
        assert len(api_key) > 0, "GUPSHUP_API_KEY est vide"
        assert api_key != "your_api_key", "GUPSHUP_API_KEY contient la valeur par défaut"
    
    def test_gupshup_app_name_is_set(self):
        """Vérifie que GUPSHUP_APP_NAME est définie et non vide."""
        app_name = os.getenv("GUPSHUP_APP_NAME") or settings.GUPSHUP_APP_NAME
        assert app_name is not None, "GUPSHUP_APP_NAME n'est pas définie"
        assert len(app_name) > 0, "GUPSHUP_APP_NAME est vide"
    
    def test_gupshup_phone_number_is_set(self):
        """Vérifie que GUPSHUP_PHONE_NUMBER est définie et valide."""
        phone = os.getenv("GUPSHUP_PHONE_NUMBER") or settings.GUPSHUP_PHONE_NUMBER
        assert phone is not None, "GUPSHUP_PHONE_NUMBER n'est pas définie"
        assert len(phone) >= 8, "GUPSHUP_PHONE_NUMBER semble trop court"
        # Le numéro ne doit pas contenir de +
        assert not phone.startswith("+"), \
            "GUPSHUP_PHONE_NUMBER ne doit pas commencer par +"
    
    def test_gupshup_api_url_is_valid(self):
        """Vérifie que GUPSHUP_API_URL est une URL valide."""
        api_url = os.getenv("GUPSHUP_API_URL") or settings.GUPSHUP_API_URL
        assert api_url is not None, "GUPSHUP_API_URL n'est pas définie"
        assert api_url.startswith("https://"), \
            "GUPSHUP_API_URL doit commencer par https://"
        assert "gupshup.io" in api_url, \
            "GUPSHUP_API_URL doit pointer vers gupshup.io"


class TestGupshupServiceConfiguration:
    """Tests pour vérifier la configuration du service Gupshup."""
    
    def test_service_initializes_with_config(self):
        """Vérifie que le service s'initialise correctement avec la config."""
        from app.services.gupshup_service import GupshupService
        
        service = GupshupService()
        
        assert service.api_key is not None, "api_key non initialisée"
        assert service.app_name is not None, "app_name non initialisée"
        assert service.phone_number is not None, "phone_number non initialisée"
        assert service.base_url is not None, "base_url non initialisée"
    
    def test_service_headers_contain_apikey(self):
        """Vérifie que les headers contiennent l'apikey."""
        from app.services.gupshup_service import GupshupService
        
        service = GupshupService()
        headers = service.headers
        
        assert "apikey" in headers, "Header 'apikey' manquant"
        assert headers["apikey"] == service.api_key, \
            "Header 'apikey' ne correspond pas à l'API key configurée"
    
    def test_service_headers_content_type(self):
        """Vérifie que le Content-Type est x-www-form-urlencoded."""
        from app.services.gupshup_service import GupshupService
        
        service = GupshupService()
        headers = service.headers
        
        assert "Content-Type" in headers, "Header 'Content-Type' manquant"
        assert headers["Content-Type"] == "application/x-www-form-urlencoded", \
            "Content-Type doit être application/x-www-form-urlencoded"
    
    def test_template_url_is_correct(self):
        """Vérifie que l'URL des templates est correcte."""
        from app.services.gupshup_service import GupshupService
        
        service = GupshupService()
        
        assert "/template/msg" in service.template_url, \
            "L'URL template doit contenir /template/msg"
    
    def test_message_url_is_correct(self):
        """Vérifie que l'URL des messages est correcte."""
        from app.services.gupshup_service import GupshupService
        
        service = GupshupService()
        
        assert "/msg" in service.message_url, \
            "L'URL message doit contenir /msg"


class TestGupshupApiKeyValidation:
    """Tests pour valider l'API key Gupshup avec l'API réelle."""
    
    @pytest.mark.asyncio
    async def test_api_key_format_is_valid(self):
        """Vérifie que le format de l'API key semble valide."""
        api_key = os.getenv("GUPSHUP_API_KEY") or settings.GUPSHUP_API_KEY
        
        # Les API keys Gupshup commencent généralement par "sk_"
        # ou sont des chaînes alphanumériques
        assert len(api_key) >= 20, \
            f"L'API key semble trop courte ({len(api_key)} caractères)"
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_api_connection_with_templates_endpoint(self):
        """
        Test d'intégration: vérifie la connexion à l'API Gupshup.
        
        Ce test fait un appel réel à l'API Gupshup pour vérifier
        que les credentials sont valides.
        
        Marqué comme 'integration' pour pouvoir être exclu des tests unitaires.
        """
        api_key = os.getenv("GUPSHUP_API_KEY") or settings.GUPSHUP_API_KEY
        app_name = os.getenv("GUPSHUP_APP_NAME") or settings.GUPSHUP_APP_NAME
        
        templates_url = f"https://api.gupshup.io/sm/api/v1/template/list/{app_name}"
        headers = {"apikey": api_key}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(templates_url, headers=headers)
            
            # 200 = succès, 401 = API key invalide, 403 = accès refusé
            assert response.status_code != 401, \
                "API Key invalide ou expirée (HTTP 401)"
            assert response.status_code != 403, \
                "Accès refusé - vérifiez les permissions (HTTP 403)"
            
            # On accepte 200 (succès) ou 404 (app non trouvée mais credentials OK)
            assert response.status_code in [200, 404], \
                f"Réponse inattendue de l'API: HTTP {response.status_code}"


class TestGupshupCredentialsMocked:
    """Tests avec mocks pour valider la logique sans appels API réels."""
    
    @pytest.mark.asyncio
    async def test_send_template_with_valid_credentials(self):
        """Test l'envoi de template avec des credentials valides (mocké)."""
        from app.services.gupshup_service import GupshupService
        from unittest.mock import AsyncMock
        
        service = GupshupService()
        
        # Mock de la réponse HTTP
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "submitted",
            "messageId": "test_msg_123"
        }
        
        with patch('app.services.gupshup_service.httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_client.return_value.__aexit__.return_value = None
            
            result = await service.send_template_message(
                phone="+33612345678",
                template_name="test_template",
                params=["param1"]
            )
            
            assert result.success is True, "L'envoi devrait réussir"
            assert result.message_id == "test_msg_123", \
                "Le message_id devrait être extrait"
    
    @pytest.mark.asyncio
    async def test_send_template_with_invalid_credentials(self):
        """Test l'envoi de template avec des credentials invalides (mocké)."""
        from app.services.gupshup_service import GupshupService
        from unittest.mock import AsyncMock
        
        service = GupshupService()
        
        # Mock d'une réponse d'erreur 401
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "status": "error",
            "message": "Invalid API key"
        }
        
        with patch('app.services.gupshup_service.httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_client.return_value.__aexit__.return_value = None
            
            result = await service.send_template_message(
                phone="+33612345678",
                template_name="test_template"
            )
            
            assert result.success is False, \
                "L'envoi devrait échouer avec credentials invalides"
            assert result.error_code == "401", \
                "Le code d'erreur devrait être 401"
    
    @pytest.mark.asyncio
    async def test_send_text_with_valid_credentials(self):
        """Test l'envoi de message texte avec des credentials valides (mocké)."""
        from app.services.gupshup_service import GupshupService
        from unittest.mock import AsyncMock
        
        service = GupshupService()
        
        # Mock de la réponse HTTP
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "submitted",
            "messageId": "text_msg_456"
        }
        
        with patch('app.services.gupshup_service.httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_client.return_value.__aexit__.return_value = None
            
            result = await service.send_text_message(
                phone="+33612345678",
                text="Test message"
            )
            
            assert result.success is True, "L'envoi devrait réussir"
            assert result.message_id == "text_msg_456", \
                "Le message_id devrait être extrait"


class TestGupshupCredentialsErrorHandling:
    """Tests pour la gestion des erreurs de credentials."""
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test la gestion du timeout lors de la validation."""
        from app.services.gupshup_service import GupshupService
        from unittest.mock import AsyncMock
        
        service = GupshupService()
        
        with patch('app.services.gupshup_service.httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post = AsyncMock(
                side_effect=httpx.TimeoutException("Connection timeout")
            )
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_client.return_value.__aexit__.return_value = None
            
            result = await service.send_template_message(
                phone="+33612345678",
                template_name="test_template"
            )
            
            assert result.success is False, \
                "L'envoi devrait échouer en cas de timeout"
            assert result.error_code == "timeout", \
                "Le code d'erreur devrait être 'timeout'"
    
    @pytest.mark.asyncio
    async def test_network_error_handling(self):
        """Test la gestion des erreurs réseau."""
        from app.services.gupshup_service import GupshupService
        from unittest.mock import AsyncMock
        
        service = GupshupService()
        
        with patch('app.services.gupshup_service.httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post = AsyncMock(
                side_effect=httpx.RequestError("Network error")
            )
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_client.return_value.__aexit__.return_value = None
            
            result = await service.send_template_message(
                phone="+33612345678",
                template_name="test_template"
            )
            
            assert result.success is False, \
                "L'envoi devrait échouer en cas d'erreur réseau"
            assert result.error_code == "network_error", \
                "Le code d'erreur devrait être 'network_error'"
