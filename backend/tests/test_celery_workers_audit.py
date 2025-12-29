"""
Tests d'audit des Workers Celery - Phase 7
Vérifie le fonctionnement autonome du système sans admin connecté

Requirements: 8.1, 8.2, 8.3, 8.4, 8.5
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta


class TestCeleryConfiguration:
    """Tests de la configuration Celery (Requirement 8.4, 8.5)"""
    
    def test_celery_app_configuration(self):
        """Vérifie que la configuration Celery est correcte"""
        from app.tasks.celery_app import celery_app
        
        # Vérifier les paramètres de robustesse
        assert celery_app.conf.task_acks_late is True, "task_acks_late doit être True"
        assert celery_app.conf.task_reject_on_worker_lost is True, "task_reject_on_worker_lost doit être True"
        assert celery_app.conf.broker_connection_retry_on_startup is True, "broker_connection_retry_on_startup doit être True"
        
        # Vérifier la concurrence
        assert celery_app.conf.worker_concurrency >= 1, "worker_concurrency doit être >= 1"
        assert celery_app.conf.worker_prefetch_multiplier >= 1, "worker_prefetch_multiplier doit être >= 1"
    
    def test_celery_queues_configured(self):
        """Vérifie que les queues sont correctement configurées"""
        from app.tasks.celery_app import celery_app
        
        queues = celery_app.conf.task_queues
        queue_names = [q.name for q in queues]
        
        # Vérifier les queues requises
        assert "default" in queue_names, "Queue 'default' manquante"
        assert "messages" in queue_names, "Queue 'messages' manquante"
        assert "retry" in queue_names, "Queue 'retry' manquante"
        assert "verification" in queue_names, "Queue 'verification' manquante"
    
    def test_beat_schedule_configured(self):
        """Vérifie que les tâches périodiques sont configurées"""
        from app.tasks.celery_app import celery_app
        
        beat_schedule = celery_app.conf.beat_schedule
        
        # Vérifier les tâches périodiques requises
        required_tasks = [
            "sync-monitoring-to-supabase-hourly",
            "reset-daily-monitoring-midnight",
            "cleanup-expired-locks",
            "recover-interrupted-campaigns",
            "health-check",
            "check-expired-interactions-hourly",
        ]
        
        for task_name in required_tasks:
            assert task_name in beat_schedule, f"Tâche périodique '{task_name}' manquante"


class TestAutonomousMessageSending:
    """Tests d'envoi de messages sans admin connecté (Requirement 8.1)"""
    
    def test_send_single_message_no_user_dependency(self):
        """Vérifie que send_single_message n'a pas de dépendance utilisateur"""
        import inspect
        from app.tasks.message_tasks import send_single_message
        
        # Récupérer la signature de la fonction
        sig = inspect.signature(send_single_message)
        params = list(sig.parameters.keys())
        
        # Vérifier qu'il n'y a pas de paramètre user_id ou current_user
        assert "user_id" not in params, "send_single_message ne doit pas avoir de paramètre user_id"
        assert "current_user" not in params, "send_single_message ne doit pas avoir de paramètre current_user"
    
    def test_send_campaign_messages_no_user_dependency(self):
        """Vérifie que send_campaign_messages n'a pas de dépendance utilisateur"""
        import inspect
        from app.tasks.message_tasks import send_campaign_messages
        
        sig = inspect.signature(send_campaign_messages)
        params = list(sig.parameters.keys())
        
        assert "user_id" not in params, "send_campaign_messages ne doit pas avoir de paramètre user_id"
        assert "current_user" not in params, "send_campaign_messages ne doit pas avoir de paramètre current_user"


class TestAutonomousWebhookProcessing:
    """Tests de traitement des webhooks sans admin connecté (Requirement 8.2)"""
    
    def test_webhook_endpoint_no_auth_dependency(self):
        """Vérifie que l'endpoint webhook n'a pas de dépendance d'authentification"""
        import inspect
        from app.routers.webhooks import receive_wassenger_webhook
        
        sig = inspect.signature(receive_wassenger_webhook)
        params = list(sig.parameters.keys())
        
        # Vérifier qu'il n'y a pas de paramètre d'authentification
        assert "current_user" not in params, "receive_wassenger_webhook ne doit pas avoir de paramètre current_user"
        assert "token" not in params, "receive_wassenger_webhook ne doit pas avoir de paramètre token"
    
    def test_process_wassenger_message_no_user_dependency(self):
        """Vérifie que process_wassenger_message n'a pas de dépendance utilisateur"""
        import inspect
        from app.routers.webhooks import process_wassenger_message
        
        sig = inspect.signature(process_wassenger_message)
        params = list(sig.parameters.keys())
        
        assert "user_id" not in params, "process_wassenger_message ne doit pas avoir de paramètre user_id"
        assert "current_user" not in params, "process_wassenger_message ne doit pas avoir de paramètre current_user"


class TestAutonomousMessage2Sending:
    """Tests d'envoi Message 2 sur interaction sans admin (Requirement 8.3)"""
    
    def test_schedule_message_2_no_user_dependency(self):
        """Vérifie que _schedule_message_2_wassenger n'a pas de dépendance utilisateur"""
        import inspect
        from app.routers.webhooks import _schedule_message_2_wassenger
        
        sig = inspect.signature(_schedule_message_2_wassenger)
        params = list(sig.parameters.keys())
        
        # Vérifier les paramètres attendus
        assert "campaign_id" in params, "_schedule_message_2_wassenger doit avoir campaign_id"
        assert "contact_id" in params, "_schedule_message_2_wassenger doit avoir contact_id"
        
        # Vérifier qu'il n'y a pas de dépendance utilisateur
        assert "user_id" not in params, "_schedule_message_2_wassenger ne doit pas avoir de paramètre user_id"
        assert "current_user" not in params, "_schedule_message_2_wassenger ne doit pas avoir de paramètre current_user"


class TestWorkerRobustness:
    """Tests de robustesse des workers (Requirement 8.4)"""
    
    def test_idempotency_lock_functions_exist(self):
        """Vérifie que les fonctions d'idempotence existent"""
        from app.tasks.message_tasks import (
            acquire_idempotency_lock,
            release_idempotency_lock,
            get_idempotency_key,
        )
        
        # Vérifier que les fonctions sont appelables
        assert callable(acquire_idempotency_lock)
        assert callable(release_idempotency_lock)
        assert callable(get_idempotency_key)
    
    def test_idempotency_key_format(self):
        """Vérifie le format des clés d'idempotence"""
        from app.tasks.message_tasks import get_idempotency_key
        
        key = get_idempotency_key(123, "send")
        assert key == "idempotency:send:123", f"Format de clé incorrect: {key}"
        
        key = get_idempotency_key(456, "retry")
        assert key == "idempotency:retry:456", f"Format de clé incorrect: {key}"
    
    def test_validate_message_data_function(self):
        """Vérifie la fonction de validation des messages"""
        from app.tasks.message_tasks import validate_message_data
        
        # Message valide
        valid_message = {
            "id": 1,
            "contact_id": 2,
            "campaign_id": 3,
            "content": "Test message"
        }
        is_valid, error = validate_message_data(valid_message)
        assert is_valid is True, f"Message valide rejeté: {error}"
        
        # Message invalide - champ manquant
        invalid_message = {"id": 1, "contact_id": 2}
        is_valid, error = validate_message_data(invalid_message)
        assert is_valid is False, "Message invalide accepté"
        assert "campaign_id" in error or "content" in error
        
        # Message invalide - contenu vide
        empty_content = {
            "id": 1,
            "contact_id": 2,
            "campaign_id": 3,
            "content": ""
        }
        is_valid, error = validate_message_data(empty_content)
        assert is_valid is False, "Message avec contenu vide accepté"
    
    def test_validate_contact_data_function(self):
        """Vérifie la fonction de validation des contacts"""
        from app.tasks.message_tasks import validate_contact_data
        
        # Contact valide
        valid_contact = {"full_number": "+22990123456"}
        is_valid, error = validate_contact_data(valid_contact)
        assert is_valid is True, f"Contact valide rejeté: {error}"
        
        # Contact invalide - pas de numéro
        invalid_contact = {"name": "Test"}
        is_valid, error = validate_contact_data(invalid_contact)
        assert is_valid is False, "Contact sans numéro accepté"
        
        # Contact None
        is_valid, error = validate_contact_data(None)
        assert is_valid is False, "Contact None accepté"


class TestHealthCheckTask:
    """Tests de la tâche de health check (Requirement 8.4)"""
    
    def test_health_check_task_exists(self):
        """Vérifie que la tâche de health check existe"""
        from app.tasks.celery_app import system_health_check
        
        assert callable(system_health_check)
    
    def test_recover_interrupted_campaigns_task_exists(self):
        """Vérifie que la tâche de récupération existe"""
        from app.tasks.celery_app import recover_interrupted_campaigns
        
        assert callable(recover_interrupted_campaigns)
    
    def test_check_expired_interactions_task_exists(self):
        """Vérifie que la tâche de vérification 24h existe"""
        from app.tasks.celery_app import check_expired_interactions
        
        assert callable(check_expired_interactions)


class TestRetryMechanism:
    """Tests du mécanisme de retry (Requirement 8.5)"""
    
    def test_calculate_retry_delay(self):
        """Vérifie le calcul du délai de retry avec backoff exponentiel"""
        from app.tasks.message_tasks import calculate_retry_delay
        
        # Tentative 1: 60s
        delay1 = calculate_retry_delay(1)
        assert delay1 == 60, f"Délai tentative 1 incorrect: {delay1}"
        
        # Tentative 2: 120s
        delay2 = calculate_retry_delay(2)
        assert delay2 == 120, f"Délai tentative 2 incorrect: {delay2}"
        
        # Tentative 3: 240s
        delay3 = calculate_retry_delay(3)
        assert delay3 == 240, f"Délai tentative 3 incorrect: {delay3}"
    
    def test_max_retry_attempts_configured(self):
        """Vérifie que le nombre max de retries est configuré"""
        from app.config import settings
        
        assert settings.MAX_RETRY_ATTEMPTS == 3, "MAX_RETRY_ATTEMPTS doit être 3"
    
    def test_retry_base_delay_configured(self):
        """Vérifie que le délai de base est configuré"""
        from app.config import settings
        
        assert settings.RETRY_BASE_DELAY_SECONDS == 60, "RETRY_BASE_DELAY_SECONDS doit être 60"


class TestMonitoringService:
    """Tests du service de monitoring pour les workers"""
    
    def test_monitoring_service_initialization(self):
        """Vérifie que le service de monitoring s'initialise correctement"""
        from app.services.monitoring_service import MonitoringService
        
        # Créer une instance avec une URL Redis fictive
        service = MonitoringService(redis_url="redis://localhost:6379/0")
        
        assert service is not None
        assert service.redis_url == "redis://localhost:6379/0"
    
    def test_ssl_url_transformation(self):
        """Vérifie la transformation des URLs Redis SSL"""
        from app.services.monitoring_service import get_redis_url_with_ssl
        
        # URL sans SSL - pas de changement
        url1 = "redis://localhost:6379/0"
        assert get_redis_url_with_ssl(url1) == url1
        
        # URL avec SSL - ajout du paramètre
        url2 = "rediss://host:6379/0"
        result = get_redis_url_with_ssl(url2)
        assert "ssl_cert_reqs=none" in result
        
        # URL avec SSL et paramètres existants
        url3 = "rediss://host:6379/0?param=value"
        result = get_redis_url_with_ssl(url3)
        assert "ssl_cert_reqs=none" in result
        assert "&ssl_cert_reqs=none" in result


class TestCampaignLocking:
    """Tests du verrouillage des campagnes"""
    
    def test_campaign_lock_key_format(self):
        """Vérifie le format des clés de verrouillage"""
        # Le format attendu est "campaign:lock:{campaign_id}"
        campaign_id = 123
        expected_key = f"campaign:lock:{campaign_id}"
        
        # Vérifier que le format est utilisé dans le code
        from app.services.monitoring_service import MonitoringService
        import inspect
        
        source = inspect.getsource(MonitoringService.acquire_campaign_lock)
        assert "campaign:lock:" in source, "Format de clé de verrouillage incorrect"


# Exécution des tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
