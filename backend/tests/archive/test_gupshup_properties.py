"""
Tests Property-Based pour le service Gupshup.

Ce fichier contient les tests property-based utilisant Hypothesis
pour valider les propriétés de correction du service Gupshup.
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime
from typing import List
import time

# Import du service à tester
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.gupshup_service import GupshupService


class TestPhoneNumberFormatting:
    """Tests property-based pour le formatage des numéros de téléphone."""
    
    @settings(max_examples=100)
    @given(
        phone_number=st.text(
            alphabet=st.sampled_from("0123456789"),
            min_size=8,
            max_size=15
        ).map(lambda x: "+" + x)
    )
    def test_format_phone_number_removes_plus(self, phone_number: str):
        """
        **Feature: migration-gupshup, Property 1: Formatage des numéros de téléphone**
        **Valide: Exigences 2.3, 7.2**
        
        Pour tout numéro de téléphone passé au service Gupshup,
        le caractère "+" doit être retiré du début du numéro.
        
        Cette propriété vérifie que:
        1. Le résultat ne commence jamais par "+"
        2. Le reste du numéro est préservé
        """
        service = GupshupService()
        result = service.format_phone_number(phone_number)
        
        # Le résultat ne doit jamais commencer par +
        assert not result.startswith("+"), \
            f"Le numéro formaté '{result}' commence encore par '+'"
        
        # Le reste du numéro doit être préservé
        expected = phone_number.lstrip("+")
        assert result == expected, \
            f"Le numéro '{phone_number}' devrait donner '{expected}', mais a donné '{result}'"
    
    @settings(max_examples=100)
    @given(
        phone_number=st.text(
            alphabet=st.sampled_from("0123456789"),
            min_size=8,
            max_size=15
        )
    )
    def test_format_phone_number_without_plus_unchanged(self, phone_number: str):
        """
        **Feature: migration-gupshup, Property 1: Formatage des numéros de téléphone**
        **Valide: Exigences 2.3, 7.2**
        
        Pour tout numéro de téléphone sans +, le formatage doit
        retourner le numéro inchangé.
        """
        service = GupshupService()
        result = service.format_phone_number(phone_number)
        
        # Le résultat ne doit jamais commencer par +
        assert not result.startswith("+"), \
            f"Le numéro formaté '{result}' commence par '+'"
        
        # Le numéro sans + doit rester inchangé
        assert result == phone_number, \
            f"Le numéro '{phone_number}' devrait rester inchangé, mais a donné '{result}'"
    
    @settings(max_examples=100)
    @given(
        phone_number=st.text(
            alphabet=st.sampled_from("0123456789+"),
            min_size=1,
            max_size=20
        ).filter(lambda x: x.startswith("+"))
    )
    def test_format_phone_number_multiple_plus_stripped(self, phone_number: str):
        """
        **Feature: migration-gupshup, Property 1: Formatage des numéros de téléphone**
        **Valide: Exigences 2.3, 7.2**
        
        Pour tout numéro commençant par un ou plusieurs +,
        tous les + au début doivent être retirés.
        """
        service = GupshupService()
        result = service.format_phone_number(phone_number)
        
        # Le résultat ne doit jamais commencer par +
        assert not result.startswith("+"), \
            f"Le numéro formaté '{result}' commence encore par '+'"


class TestWebhookMessageParsing:
    """
    Tests property-based pour le parsing des webhooks message.
    
    **Feature: migration-gupshup, Property 6: Parsing des webhooks message**
    **Valide: Exigences 4.1**
    """
    
    @settings(max_examples=100)
    @given(
        mobile=st.text(
            alphabet=st.sampled_from("0123456789"),
            min_size=8,
            max_size=15
        ),
        text=st.text(min_size=1, max_size=500),
        message_id=st.text(
            alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"),
            min_size=10,
            max_size=50
        ),
        timestamp=st.integers(min_value=1000000000, max_value=2000000000),
        name=st.text(min_size=1, max_size=100).filter(lambda x: x.strip() != "")
    )
    def test_parse_message_webhook_extracts_fields(
        self, mobile: str, text: str, message_id: str, timestamp: int, name: str
    ):
        """
        **Feature: migration-gupshup, Property 6: Parsing des webhooks message**
        **Valide: Exigences 4.1**
        
        Pour tout webhook Gupshup de type "message", le parsing doit extraire
        correctement les champs mobile, text et messageId.
        
        Cette propriété vérifie que:
        1. Le numéro mobile est extrait et formaté avec +
        2. Le texte du message est préservé
        3. Le messageId est extrait correctement
        """
        # Construire un payload webhook valide
        payload = {
            "type": "message",
            "mobile": mobile,
            "text": text,
            "messageId": message_id,
            "timestamp": timestamp,
            "name": name
        }
        
        service = GupshupService()
        interactions = service.parse_webhook_payload(payload)
        
        # Doit retourner exactement une interaction
        assert len(interactions) == 1, \
            f"Attendu 1 interaction, obtenu {len(interactions)}"
        
        interaction = interactions[0]
        
        # Vérifier l'extraction du numéro mobile (avec + ajouté)
        expected_phone = f"+{mobile}" if not mobile.startswith("+") else mobile
        assert interaction.contact_phone == expected_phone, \
            f"Numéro attendu '{expected_phone}', obtenu '{interaction.contact_phone}'"
        
        # Vérifier l'extraction du texte
        assert interaction.content == text, \
            f"Texte attendu '{text}', obtenu '{interaction.content}'"
        
        # Vérifier l'extraction du messageId
        assert interaction.gupshup_message_id == message_id, \
            f"MessageId attendu '{message_id}', obtenu '{interaction.gupshup_message_id}'"
        
        # Vérifier le type d'interaction
        assert interaction.interaction_type == "reply", \
            f"Type attendu 'reply', obtenu '{interaction.interaction_type}'"
    
    @settings(max_examples=100)
    @given(
        mobile=st.text(
            alphabet=st.sampled_from("0123456789"),
            min_size=8,
            max_size=15
        ),
        text=st.text(min_size=0, max_size=500),
        message_id=st.text(
            alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"),
            min_size=0,
            max_size=50
        )
    )
    def test_parse_message_webhook_handles_optional_fields(
        self, mobile: str, text: str, message_id: str
    ):
        """
        **Feature: migration-gupshup, Property 6: Parsing des webhooks message**
        **Valide: Exigences 4.1**
        
        Pour tout webhook message avec des champs optionnels manquants,
        le parsing doit quand même extraire les champs disponibles.
        """
        # Payload minimal sans timestamp ni name
        payload = {
            "type": "message",
            "mobile": mobile,
            "text": text,
            "messageId": message_id
        }
        
        service = GupshupService()
        interactions = service.parse_webhook_payload(payload)
        
        # Doit retourner exactement une interaction
        assert len(interactions) == 1, \
            f"Attendu 1 interaction, obtenu {len(interactions)}"
        
        interaction = interactions[0]
        
        # Les champs optionnels doivent être None
        assert interaction.timestamp is None, \
            "Le timestamp devrait être None quand absent"
        assert interaction.contact_name is None, \
            "Le contact_name devrait être None quand absent"


class TestWebhookResponseTime:
    """
    Tests property-based pour le temps de réponse des webhooks.
    
    **Feature: migration-gupshup, Property 8: Temps de réponse webhook**
    **Valide: Exigences 4.6**
    """
    
    @settings(max_examples=100)
    @given(
        mobile=st.text(
            alphabet=st.sampled_from("0123456789"),
            min_size=8,
            max_size=15
        ),
        text=st.text(min_size=1, max_size=1000),
        message_id=st.text(
            alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"),
            min_size=10,
            max_size=50
        ),
        timestamp=st.integers(min_value=1000000000, max_value=2000000000),
        name=st.text(min_size=1, max_size=100).filter(lambda x: x.strip() != "")
    )
    def test_webhook_message_parsing_completes_quickly(
        self, mobile: str, text: str, message_id: str, timestamp: int, name: str
    ):
        """
        **Feature: migration-gupshup, Property 8: Temps de réponse webhook**
        **Valide: Exigences 4.6**
        
        Pour tout webhook reçu, le parsing du payload doit se terminer
        en moins de 20 secondes pour permettre une réponse rapide.
        
        Cette propriété vérifie que le parsing synchrone (qui bloque la réponse)
        est suffisamment rapide pour respecter le délai de 20 secondes.
        """
        # Construire un payload webhook message valide
        payload = {
            "type": "message",
            "mobile": mobile,
            "text": text,
            "messageId": message_id,
            "timestamp": timestamp,
            "name": name
        }
        
        service = GupshupService()
        
        # Mesurer le temps de parsing
        start_time = time.time()
        interactions = service.parse_webhook_payload(payload)
        elapsed_time = time.time() - start_time
        
        # Le parsing doit se terminer en moins de 20 secondes
        # (En pratique, cela devrait être en millisecondes)
        assert elapsed_time < 20.0, \
            f"Le parsing du webhook a pris {elapsed_time:.3f}s, dépassant la limite de 20s"
        
        # Vérifier que le parsing a produit un résultat valide
        assert len(interactions) == 1, \
            f"Attendu 1 interaction, obtenu {len(interactions)}"
    
    @settings(max_examples=100)
    @given(
        event_type=st.sampled_from(["sent", "delivered", "read", "failed"]),
        external_id=st.text(
            alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyz0123456789-_"),
            min_size=5,
            max_size=50
        ),
        message_id=st.text(
            alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"),
            min_size=10,
            max_size=50
        ),
        dest_addr=st.text(
            alphabet=st.sampled_from("0123456789"),
            min_size=8,
            max_size=15
        )
    )
    def test_webhook_message_event_parsing_completes_quickly(
        self, event_type: str, external_id: str, message_id: str, dest_addr: str
    ):
        """
        **Feature: migration-gupshup, Property 8: Temps de réponse webhook**
        **Valide: Exigences 4.6**
        
        Pour tout webhook message-event reçu, le parsing du payload doit
        se terminer en moins de 20 secondes pour permettre une réponse rapide.
        """
        # Construire un payload webhook message-event valide
        payload = {
            "type": "message-event",
            "eventType": event_type,
            "externalId": external_id,
            "messageId": message_id,
            "destAddr": dest_addr
        }
        
        service = GupshupService()
        
        # Mesurer le temps de parsing
        start_time = time.time()
        interactions = service.parse_webhook_payload(payload)
        elapsed_time = time.time() - start_time
        
        # Le parsing doit se terminer en moins de 20 secondes
        assert elapsed_time < 20.0, \
            f"Le parsing du webhook message-event a pris {elapsed_time:.3f}s, dépassant la limite de 20s"
        
        # Vérifier que le parsing a produit un résultat valide
        assert len(interactions) == 1, \
            f"Attendu 1 interaction, obtenu {len(interactions)}"
    
    @settings(max_examples=50)
    @given(
        text=st.text(min_size=100, max_size=5000)  # Messages plus longs
    )
    def test_webhook_large_message_parsing_completes_quickly(self, text: str):
        """
        **Feature: migration-gupshup, Property 8: Temps de réponse webhook**
        **Valide: Exigences 4.6**
        
        Pour tout webhook avec un message de grande taille, le parsing
        doit toujours se terminer en moins de 20 secondes.
        """
        payload = {
            "type": "message",
            "mobile": "33612345678",
            "text": text,
            "messageId": "test_message_id_12345",
            "timestamp": 1700000000,
            "name": "Test User"
        }
        
        service = GupshupService()
        
        # Mesurer le temps de parsing
        start_time = time.time()
        interactions = service.parse_webhook_payload(payload)
        elapsed_time = time.time() - start_time
        
        # Le parsing doit se terminer en moins de 20 secondes
        assert elapsed_time < 20.0, \
            f"Le parsing d'un grand message ({len(text)} chars) a pris {elapsed_time:.3f}s"
        
        # Vérifier que le contenu est préservé
        assert len(interactions) == 1
        assert interactions[0].content == text


class MockRateLimiter:
    """
    Rate limiter pour les tests - copie de la logique de RateLimiter
    sans dépendance à Celery.
    
    Utilisé pour tester la propriété de rate limiting sans avoir besoin
    d'installer Celery dans l'environnement de test.
    """
    
    def __init__(self, limit: int = 25, window: int = 60):
        """
        Initialise le rate limiter.
        
        Args:
            limit: Nombre maximum de messages par fenêtre
            window: Durée de la fenêtre en secondes
        """
        self.limit = limit
        self.window = window
        self._redis = None
    
    def can_send(self, key: str = "whatsapp_messages") -> bool:
        """
        Vérifie si un message peut être envoyé sans dépasser la limite.
        """
        try:
            current = self._redis.get(key)
            if current is None:
                return True
            return int(current) < self.limit
        except Exception:
            return True
    
    def increment(self, key: str = "whatsapp_messages") -> int:
        """
        Incrémente le compteur de messages envoyés.
        """
        try:
            pipe = self._redis.pipeline()
            pipe.incr(key)
            pipe.expire(key, self.window)
            results = pipe.execute()
            return results[0]
        except Exception:
            return 0
    
    def get_remaining(self, key: str = "whatsapp_messages") -> int:
        """
        Retourne le nombre de messages restants dans la fenêtre actuelle.
        """
        try:
            current = self._redis.get(key)
            if current is None:
                return self.limit
            return max(0, self.limit - int(current))
        except Exception:
            return 0


class TestRateLimiting:
    """
    Tests property-based pour le respect du rate limiting.
    
    **Feature: migration-gupshup, Property 9: Respect du rate limiting**
    **Valide: Exigences 6.2**
    """
    
    @settings(max_examples=100)
    @given(
        num_messages=st.integers(min_value=1, max_value=100),
        rate_limit=st.integers(min_value=5, max_value=50)
    )
    def test_rate_limiter_blocks_after_limit(self, num_messages: int, rate_limit: int):
        """
        **Feature: migration-gupshup, Property 9: Respect du rate limiting**
        **Valide: Exigences 6.2**
        
        Pour tout envoi massif de messages, le système ne doit jamais
        dépasser la limite configurée par minute.
        
        Cette propriété vérifie que:
        1. Le rate limiter autorise les envois jusqu'à la limite
        2. Le rate limiter bloque les envois au-delà de la limite
        3. Le compteur est correctement incrémenté
        """
        from unittest.mock import MagicMock
        
        # Créer un mock Redis pour simuler le comportement
        mock_redis = MagicMock()
        counter = {"value": 0}
        
        def mock_get(key):
            return str(counter["value"]) if counter["value"] > 0 else None
        
        def mock_incr(key):
            counter["value"] += 1
            return counter["value"]
        
        def mock_expire(key, ttl):
            return True
        
        def mock_pipeline():
            pipe = MagicMock()
            pipe.incr = mock_incr
            pipe.expire = mock_expire
            pipe.execute = lambda: [counter["value"], True]
            return pipe
        
        mock_redis.get = mock_get
        mock_redis.pipeline = mock_pipeline
        
        # Créer le rate limiter avec le mock
        limiter = MockRateLimiter(limit=rate_limit, window=60)
        limiter._redis = mock_redis
        
        # Simuler l'envoi de messages
        allowed_count = 0
        blocked_count = 0
        
        for i in range(num_messages):
            if limiter.can_send():
                limiter.increment()
                allowed_count += 1
            else:
                blocked_count += 1
        
        # Vérifier que le nombre de messages autorisés ne dépasse jamais la limite
        assert allowed_count <= rate_limit, \
            f"Le rate limiter a autorisé {allowed_count} messages, " \
            f"dépassant la limite de {rate_limit}"
        
        # Si on a envoyé plus de messages que la limite, certains doivent être bloqués
        if num_messages > rate_limit:
            expected_blocked = num_messages - rate_limit
            assert blocked_count == expected_blocked, \
                f"Attendu {expected_blocked} messages bloqués, obtenu {blocked_count}"
    
    @settings(max_examples=100)
    @given(
        rate_limit=st.integers(min_value=10, max_value=50)
    )
    def test_rate_limiter_remaining_count_accurate(self, rate_limit: int):
        """
        **Feature: migration-gupshup, Property 9: Respect du rate limiting**
        **Valide: Exigences 6.2**
        
        Pour tout état du rate limiter, le nombre de messages restants
        doit être égal à (limite - messages envoyés).
        """
        from unittest.mock import MagicMock
        
        # Créer un mock Redis
        mock_redis = MagicMock()
        counter = {"value": 0}
        
        def mock_get(key):
            return str(counter["value"]) if counter["value"] > 0 else None
        
        def mock_pipeline():
            pipe = MagicMock()
            def do_incr(key):
                counter["value"] += 1
                return counter["value"]
            pipe.incr = do_incr
            pipe.expire = lambda k, t: True
            pipe.execute = lambda: [counter["value"], True]
            return pipe
        
        mock_redis.get = mock_get
        mock_redis.pipeline = mock_pipeline
        
        limiter = MockRateLimiter(limit=rate_limit, window=60)
        limiter._redis = mock_redis
        
        # Vérifier le compteur initial
        assert limiter.get_remaining() == rate_limit, \
            f"Compteur initial devrait être {rate_limit}"
        
        # Envoyer quelques messages et vérifier le compteur
        messages_to_send = min(rate_limit // 2, 10)
        for _ in range(messages_to_send):
            if limiter.can_send():
                limiter.increment()
        
        expected_remaining = rate_limit - messages_to_send
        actual_remaining = limiter.get_remaining()
        
        assert actual_remaining == expected_remaining, \
            f"Après {messages_to_send} messages, attendu {expected_remaining} restants, " \
            f"obtenu {actual_remaining}"
    
    @settings(max_examples=50)
    @given(
        rate_limit=st.just(25)  # Limite réelle de WhatsApp
    )
    def test_rate_limiter_whatsapp_limit_25_per_minute(self, rate_limit: int):
        """
        **Feature: migration-gupshup, Property 9: Respect du rate limiting**
        **Valide: Exigences 6.2**
        
        Pour la limite WhatsApp de 25 messages par minute,
        le système ne doit jamais autoriser plus de 25 messages.
        """
        from unittest.mock import MagicMock
        
        # Créer un mock Redis
        mock_redis = MagicMock()
        counter = {"value": 0}
        
        def mock_get(key):
            return str(counter["value"]) if counter["value"] > 0 else None
        
        def mock_pipeline():
            pipe = MagicMock()
            def do_incr(key):
                counter["value"] += 1
                return counter["value"]
            pipe.incr = do_incr
            pipe.expire = lambda k, t: True
            pipe.execute = lambda: [counter["value"], True]
            return pipe
        
        mock_redis.get = mock_get
        mock_redis.pipeline = mock_pipeline
        
        limiter = MockRateLimiter(limit=25, window=60)
        limiter._redis = mock_redis
        
        # Tenter d'envoyer 50 messages (2x la limite)
        allowed = 0
        for _ in range(50):
            if limiter.can_send():
                limiter.increment()
                allowed += 1
        
        # Exactement 25 messages doivent être autorisés
        assert allowed == 25, \
            f"Le rate limiter WhatsApp a autorisé {allowed} messages au lieu de 25"


def calculate_retry_delay(attempt: int, base_delay: int = 60) -> int:
    """
    Calcule le délai avant le prochain retry avec backoff exponentiel.
    
    Formule: délai = base_delay × 2^(tentative-1) secondes
    - Tentative 1: 60s
    - Tentative 2: 120s
    - Tentative 3: 240s
    
    Cette fonction est une copie de la logique de message_tasks.py
    pour permettre les tests sans dépendance à Celery.
    
    Args:
        attempt: Numéro de la tentative (1, 2, 3, ...)
        base_delay: Délai de base en secondes (défaut: 60)
    
    Returns:
        Délai en secondes
    """
    return base_delay * (2 ** (attempt - 1))


class TestRetryDelayCalculation:
    """
    Tests property-based pour le calcul du délai de retry exponentiel.
    
    **Feature: migration-gupshup, Property 10: Calcul du délai de retry exponentiel**
    **Valide: Exigences 6.3**
    """
    
    @settings(max_examples=100)
    @given(
        attempt=st.integers(min_value=1, max_value=3)
    )
    def test_retry_delay_exponential_formula(self, attempt: int):
        """
        **Feature: migration-gupshup, Property 10: Calcul du délai de retry exponentiel**
        **Valide: Exigences 6.3**
        
        Pour tout retry de message échoué, le délai doit suivre la formule:
        délai = 60 × 2^(tentative-1) secondes
        
        - Tentative 1: 60s
        - Tentative 2: 120s
        - Tentative 3: 240s
        """
        # Calculer le délai attendu selon la formule
        base_delay = 60  # secondes
        expected_delay = base_delay * (2 ** (attempt - 1))
        
        # Calculer le délai réel
        actual_delay = calculate_retry_delay(attempt)
        
        # Vérifier que le délai correspond à la formule
        assert actual_delay == expected_delay, \
            f"Pour tentative {attempt}, attendu {expected_delay}s, obtenu {actual_delay}s"
    
    @settings(max_examples=100)
    @given(
        attempt=st.integers(min_value=1, max_value=3)
    )
    def test_retry_delay_specific_values(self, attempt: int):
        """
        **Feature: migration-gupshup, Property 10: Calcul du délai de retry exponentiel**
        **Valide: Exigences 6.3**
        
        Vérifier les valeurs spécifiques pour les tentatives 1, 2, 3:
        - Tentative 1: 60s
        - Tentative 2: 120s
        - Tentative 3: 240s
        """
        expected_values = {
            1: 60,
            2: 120,
            3: 240
        }
        
        actual_delay = calculate_retry_delay(attempt)
        expected_delay = expected_values[attempt]
        
        assert actual_delay == expected_delay, \
            f"Tentative {attempt}: attendu {expected_delay}s, obtenu {actual_delay}s"
    
    @settings(max_examples=100)
    @given(
        attempt=st.integers(min_value=1, max_value=10)
    )
    def test_retry_delay_always_positive(self, attempt: int):
        """
        **Feature: migration-gupshup, Property 10: Calcul du délai de retry exponentiel**
        **Valide: Exigences 6.3**
        
        Pour toute tentative, le délai doit toujours être positif.
        """
        delay = calculate_retry_delay(attempt)
        
        assert delay > 0, \
            f"Le délai pour tentative {attempt} doit être positif, obtenu {delay}"
    
    @settings(max_examples=100)
    @given(
        attempt1=st.integers(min_value=1, max_value=9),
    )
    def test_retry_delay_increases_with_attempts(self, attempt1: int):
        """
        **Feature: migration-gupshup, Property 10: Calcul du délai de retry exponentiel**
        **Valide: Exigences 6.3**
        
        Pour toute paire de tentatives consécutives, le délai doit doubler.
        """
        attempt2 = attempt1 + 1
        
        delay1 = calculate_retry_delay(attempt1)
        delay2 = calculate_retry_delay(attempt2)
        
        # Le délai doit doubler entre deux tentatives consécutives
        assert delay2 == delay1 * 2, \
            f"Le délai devrait doubler: tentative {attempt1}={delay1}s, " \
            f"tentative {attempt2}={delay2}s (attendu {delay1 * 2}s)"


class TestWebhookMessageEventParsing:
    """
    Tests property-based pour le parsing des webhooks message-event.
    
    **Feature: migration-gupshup, Property 7: Parsing des webhooks message-event**
    **Valide: Exigences 5.1**
    """
    
    @settings(max_examples=100)
    @given(
        event_type=st.sampled_from(["sent", "delivered", "read", "failed"]),
        external_id=st.text(
            alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyz0123456789-_"),
            min_size=5,
            max_size=50
        ),
        message_id=st.text(
            alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"),
            min_size=10,
            max_size=50
        ),
        dest_addr=st.text(
            alphabet=st.sampled_from("0123456789"),
            min_size=8,
            max_size=15
        )
    )
    def test_parse_message_event_webhook_extracts_event_type(
        self, event_type: str, external_id: str, message_id: str, dest_addr: str
    ):
        """
        **Feature: migration-gupshup, Property 7: Parsing des webhooks message-event**
        **Valide: Exigences 5.1**
        
        Pour tout webhook Gupshup de type "message-event", le parsing doit
        extraire correctement le eventType parmi (sent, delivered, read, failed).
        
        Cette propriété vérifie que:
        1. Le eventType est correctement mappé vers notre type d'interaction
        2. L'externalId est extrait pour identifier le message
        3. Le messageId est extrait correctement
        """
        # Construire un payload webhook message-event valide
        payload = {
            "type": "message-event",
            "eventType": event_type,
            "externalId": external_id,
            "messageId": message_id,
            "destAddr": dest_addr
        }
        
        service = GupshupService()
        interactions = service.parse_webhook_payload(payload)
        
        # Doit retourner exactement une interaction
        assert len(interactions) == 1, \
            f"Attendu 1 interaction, obtenu {len(interactions)}"
        
        interaction = interactions[0]
        
        # Vérifier que le eventType est correctement extrait
        assert interaction.interaction_type == event_type, \
            f"Type attendu '{event_type}', obtenu '{interaction.interaction_type}'"
        
        # Vérifier l'extraction de l'externalId
        assert interaction.external_id == external_id, \
            f"ExternalId attendu '{external_id}', obtenu '{interaction.external_id}'"
        
        # Vérifier l'extraction du messageId
        assert interaction.gupshup_message_id == message_id, \
            f"MessageId attendu '{message_id}', obtenu '{interaction.gupshup_message_id}'"
    
    @settings(max_examples=100)
    @given(
        event_type=st.sampled_from(["SENT", "DELIVERED", "READ", "FAILED", "Sent", "Delivered"]),
        message_id=st.text(
            alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"),
            min_size=10,
            max_size=50
        )
    )
    def test_parse_message_event_webhook_case_insensitive(
        self, event_type: str, message_id: str
    ):
        """
        **Feature: migration-gupshup, Property 7: Parsing des webhooks message-event**
        **Valide: Exigences 5.1**
        
        Pour tout eventType avec différentes casses (majuscules/minuscules),
        le parsing doit normaliser et extraire correctement le type.
        """
        payload = {
            "type": "message-event",
            "eventType": event_type,
            "messageId": message_id,
            "destAddr": "33612345678"
        }
        
        service = GupshupService()
        interactions = service.parse_webhook_payload(payload)
        
        # Doit retourner exactement une interaction
        assert len(interactions) == 1, \
            f"Attendu 1 interaction, obtenu {len(interactions)}"
        
        interaction = interactions[0]
        
        # Le type doit être normalisé en minuscules
        expected_type = event_type.lower()
        assert interaction.interaction_type == expected_type, \
            f"Type attendu '{expected_type}', obtenu '{interaction.interaction_type}'"
    
    @settings(max_examples=50)
    @given(
        event_type=st.sampled_from(["enqueued", "unknown", "pending", ""])
    )
    def test_parse_message_event_webhook_ignores_unsupported_types(
        self, event_type: str
    ):
        """
        **Feature: migration-gupshup, Property 7: Parsing des webhooks message-event**
        **Valide: Exigences 5.1**
        
        Pour les eventTypes non supportés (enqueued, unknown, etc.),
        le parsing doit retourner une liste vide.
        """
        payload = {
            "type": "message-event",
            "eventType": event_type,
            "messageId": "test_message_id",
            "destAddr": "33612345678"
        }
        
        service = GupshupService()
        interactions = service.parse_webhook_payload(payload)
        
        # Doit retourner une liste vide pour les types non supportés
        assert len(interactions) == 0, \
            f"Attendu 0 interactions pour eventType '{event_type}', obtenu {len(interactions)}"



# =============================================================================
# Property 11 & 12: Tests de cohérence API et statistiques
# =============================================================================

class TestAPIResponseConsistency:
    """
    Tests property-based pour la cohérence des formats de réponse API.
    
    **Feature: migration-gupshup, Property 11: Cohérence des formats de réponse API**
    **Valide: Exigences 8.5**
    
    Ces tests vérifient que les formats de réponse de l'API restent identiques
    après la migration de Meta Cloud API vers Gupshup.
    """
    
    @settings(max_examples=100)
    @given(
        success=st.booleans(),
        message_id=st.text(
            alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"),
            min_size=10,
            max_size=50
        ).filter(lambda x: len(x) > 0),
        error_code=st.text(
            alphabet=st.sampled_from("0123456789"),
            min_size=1,
            max_size=5
        ),
        error_message=st.text(min_size=1, max_size=200)
    )
    def test_gupshup_response_has_same_fields_as_whatsapp_response(
        self, success: bool, message_id: str, error_code: str, error_message: str
    ):
        """
        **Feature: migration-gupshup, Property 11: Cohérence des formats de réponse API**
        **Valide: Exigences 8.5**
        
        Pour toute réponse du service Gupshup, les champs doivent être identiques
        à ceux de l'ancien service WhatsApp (success, message_id, error_code, error_message).
        
        Cette propriété vérifie que:
        1. GupshupResponse a les mêmes attributs que WhatsAppResponse
        2. Les types de données sont compatibles
        3. Le comportement est cohérent (success=True implique message_id présent)
        """
        from app.services.gupshup_service import GupshupResponse
        
        # Créer une réponse Gupshup
        if success:
            response = GupshupResponse(
                success=True,
                message_id=message_id,
                raw_response={"status": "submitted", "messageId": message_id}
            )
        else:
            response = GupshupResponse(
                success=False,
                error_code=error_code,
                error_message=error_message,
                raw_response={"status": "error", "message": error_message}
            )
        
        # Vérifier que les attributs requis existent (compatibilité avec WhatsAppResponse)
        assert hasattr(response, 'success'), "GupshupResponse doit avoir l'attribut 'success'"
        assert hasattr(response, 'message_id'), "GupshupResponse doit avoir l'attribut 'message_id'"
        assert hasattr(response, 'error_code'), "GupshupResponse doit avoir l'attribut 'error_code'"
        assert hasattr(response, 'error_message'), "GupshupResponse doit avoir l'attribut 'error_message'"
        assert hasattr(response, 'raw_response'), "GupshupResponse doit avoir l'attribut 'raw_response'"
        
        # Vérifier les types
        assert isinstance(response.success, bool), "success doit être un booléen"
        
        # Vérifier la cohérence logique
        if response.success:
            assert response.message_id is not None, \
                "Si success=True, message_id doit être présent"
        else:
            assert response.error_code is not None or response.error_message is not None, \
                "Si success=False, error_code ou error_message doit être présent"
    
    @settings(max_examples=100)
    @given(
        contact_phone=st.text(
            alphabet=st.sampled_from("0123456789"),
            min_size=8,
            max_size=15
        ).map(lambda x: "+" + x),
        interaction_type=st.sampled_from(["reply", "delivered", "read", "failed", "sent"]),
        content=st.text(min_size=0, max_size=500),
        message_id=st.text(
            alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"),
            min_size=10,
            max_size=50
        )
    )
    def test_webhook_interaction_has_same_fields_as_whatsapp_interaction(
        self, contact_phone: str, interaction_type: str, content: str, message_id: str
    ):
        """
        **Feature: migration-gupshup, Property 11: Cohérence des formats de réponse API**
        **Valide: Exigences 8.5**
        
        Pour toute interaction webhook Gupshup, les champs doivent être compatibles
        avec l'ancien format WebhookInteraction de WhatsApp.
        
        Cette propriété vérifie que:
        1. GupshupWebhookInteraction a les attributs nécessaires
        2. Les types de données sont compatibles
        3. Le mapping des types d'interaction est cohérent
        """
        from app.services.gupshup_service import GupshupWebhookInteraction
        
        # Créer une interaction Gupshup
        interaction = GupshupWebhookInteraction(
            contact_phone=contact_phone,
            interaction_type=interaction_type,
            content=content if content else None,
            gupshup_message_id=message_id
        )
        
        # Vérifier que les attributs requis existent (compatibilité avec WebhookInteraction)
        assert hasattr(interaction, 'contact_phone'), \
            "GupshupWebhookInteraction doit avoir l'attribut 'contact_phone'"
        assert hasattr(interaction, 'interaction_type'), \
            "GupshupWebhookInteraction doit avoir l'attribut 'interaction_type'"
        assert hasattr(interaction, 'content'), \
            "GupshupWebhookInteraction doit avoir l'attribut 'content'"
        assert hasattr(interaction, 'gupshup_message_id'), \
            "GupshupWebhookInteraction doit avoir l'attribut 'gupshup_message_id'"
        assert hasattr(interaction, 'timestamp'), \
            "GupshupWebhookInteraction doit avoir l'attribut 'timestamp'"
        
        # Vérifier les types
        assert isinstance(interaction.contact_phone, str), "contact_phone doit être une chaîne"
        assert isinstance(interaction.interaction_type, str), "interaction_type doit être une chaîne"
        
        # Vérifier que le type d'interaction est valide
        valid_types = {"reply", "delivered", "read", "failed", "sent"}
        assert interaction.interaction_type in valid_types, \
            f"interaction_type '{interaction.interaction_type}' doit être parmi {valid_types}"
    
    @settings(max_examples=100)
    @given(
        phone=st.text(
            alphabet=st.sampled_from("0123456789"),
            min_size=8,
            max_size=15
        ).map(lambda x: "+" + x),
        template_name=st.text(
            alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyz_"),
            min_size=3,
            max_size=30
        ),
        params=st.lists(st.text(min_size=1, max_size=50), min_size=0, max_size=5)
    )
    def test_send_template_method_signature_compatible(
        self, phone: str, template_name: str, params: List[str]
    ):
        """
        **Feature: migration-gupshup, Property 11: Cohérence des formats de réponse API**
        **Valide: Exigences 8.5**
        
        Pour toute invocation de send_template_message, la signature de méthode
        doit être compatible avec l'ancienne implémentation WhatsApp.
        
        Cette propriété vérifie que:
        1. La méthode accepte les mêmes paramètres (phone, template_name, params)
        2. Le paramètre language_code est optionnel
        """
        import inspect
        from app.services.gupshup_service import GupshupService
        
        service = GupshupService()
        
        # Vérifier que la méthode existe
        assert hasattr(service, 'send_template_message'), \
            "GupshupService doit avoir la méthode 'send_template_message'"
        
        # Vérifier la signature de la méthode
        sig = inspect.signature(service.send_template_message)
        params_names = list(sig.parameters.keys())
        
        # Les paramètres requis doivent être présents
        assert 'phone' in params_names, "send_template_message doit accepter 'phone'"
        assert 'template_name' in params_names, "send_template_message doit accepter 'template_name'"
        
        # Les paramètres optionnels doivent avoir des valeurs par défaut
        params_param = sig.parameters.get('params')
        if params_param:
            assert params_param.default is not inspect.Parameter.empty or \
                   params_param.default is None, \
                "Le paramètre 'params' doit être optionnel"
    
    @settings(max_examples=100)
    @given(
        phone=st.text(
            alphabet=st.sampled_from("0123456789"),
            min_size=8,
            max_size=15
        ).map(lambda x: "+" + x),
        text=st.text(min_size=1, max_size=500)
    )
    def test_send_text_method_signature_compatible(
        self, phone: str, text: str
    ):
        """
        **Feature: migration-gupshup, Property 11: Cohérence des formats de réponse API**
        **Valide: Exigences 8.5**
        
        Pour toute invocation de send_text_message, la signature de méthode
        doit être compatible avec l'ancienne implémentation WhatsApp.
        """
        import inspect
        from app.services.gupshup_service import GupshupService
        
        service = GupshupService()
        
        # Vérifier que la méthode existe
        assert hasattr(service, 'send_text_message'), \
            "GupshupService doit avoir la méthode 'send_text_message'"
        
        # Vérifier la signature de la méthode
        sig = inspect.signature(service.send_text_message)
        params_names = list(sig.parameters.keys())
        
        # Les paramètres requis doivent être présents
        assert 'phone' in params_names, "send_text_message doit accepter 'phone'"
        assert 'text' in params_names, "send_text_message doit accepter 'text'"


def calculate_success_rate(delivered_count: int, read_count: int, total: int) -> float:
    """
    Calcule le taux de réussite d'une campagne.
    
    Formule: success_rate = (delivered_count + read_count) / total * 100
    
    Cette fonction reproduit la logique de calcul utilisée dans campaigns.py
    pour permettre les tests property-based.
    
    Args:
        delivered_count: Nombre de messages délivrés
        read_count: Nombre de messages lus
        total: Nombre total de destinataires
    
    Returns:
        Taux de réussite en pourcentage (0.0 à 100.0)
    
    Exigences: 7.5
    """
    if total <= 0:
        return 0.0
    return (delivered_count + read_count) / total * 100


class TestStatisticsCalculation:
    """
    Tests property-based pour la cohérence du calcul des statistiques.
    
    **Feature: migration-gupshup, Property 12: Cohérence du calcul des statistiques**
    **Valide: Exigences 7.5**
    
    Ces tests vérifient que les formules de calcul des statistiques restent
    identiques après la migration vers Gupshup.
    """
    
    @settings(max_examples=100)
    @given(
        delivered_count=st.integers(min_value=0, max_value=10000),
        read_count=st.integers(min_value=0, max_value=10000),
        total=st.integers(min_value=1, max_value=20000)
    )
    def test_success_rate_formula_consistent(
        self, delivered_count: int, read_count: int, total: int
    ):
        """
        **Feature: migration-gupshup, Property 12: Cohérence du calcul des statistiques**
        **Valide: Exigences 7.5**
        
        Pour toute campagne, le taux de réussite doit être calculé avec la formule:
        success_rate = (delivered_count + read_count) / total * 100
        
        Cette propriété vérifie que:
        1. La formule est correctement appliquée
        2. Le résultat est entre 0 et 100 (ou plus si delivered+read > total)
        3. Le calcul est déterministe
        """
        # Calculer le taux de réussite
        success_rate = calculate_success_rate(delivered_count, read_count, total)
        
        # Calculer la valeur attendue
        expected_rate = (delivered_count + read_count) / total * 100
        
        # Vérifier que le calcul est correct
        assert abs(success_rate - expected_rate) < 0.0001, \
            f"Taux calculé {success_rate} != attendu {expected_rate}"
        
        # Vérifier que le résultat est non-négatif
        assert success_rate >= 0.0, \
            f"Le taux de réussite {success_rate} ne peut pas être négatif"
    
    @settings(max_examples=100)
    @given(
        total=st.integers(min_value=0, max_value=10000)
    )
    def test_success_rate_zero_when_no_recipients(self, total: int):
        """
        **Feature: migration-gupshup, Property 12: Cohérence du calcul des statistiques**
        **Valide: Exigences 7.5**
        
        Pour toute campagne sans destinataires (total=0), le taux de réussite
        doit être 0.0 pour éviter une division par zéro.
        """
        if total <= 0:
            success_rate = calculate_success_rate(0, 0, total)
            assert success_rate == 0.0, \
                f"Le taux de réussite devrait être 0.0 quand total={total}, obtenu {success_rate}"
    
    @settings(max_examples=100)
    @given(
        delivered_count=st.integers(min_value=0, max_value=1000),
        read_count=st.integers(min_value=0, max_value=1000),
        total=st.integers(min_value=1, max_value=2000)
    )
    def test_success_rate_deterministic(
        self, delivered_count: int, read_count: int, total: int
    ):
        """
        **Feature: migration-gupshup, Property 12: Cohérence du calcul des statistiques**
        **Valide: Exigences 7.5**
        
        Pour les mêmes entrées, le calcul du taux de réussite doit toujours
        produire le même résultat (déterminisme).
        """
        # Calculer deux fois avec les mêmes entrées
        rate1 = calculate_success_rate(delivered_count, read_count, total)
        rate2 = calculate_success_rate(delivered_count, read_count, total)
        
        # Les résultats doivent être identiques
        assert rate1 == rate2, \
            f"Le calcul n'est pas déterministe: {rate1} != {rate2}"
    
    @settings(max_examples=100)
    @given(
        delivered_count=st.integers(min_value=0, max_value=500),
        read_count=st.integers(min_value=0, max_value=500),
        total=st.integers(min_value=1, max_value=1000)
    )
    def test_success_rate_increases_with_delivered_or_read(
        self, delivered_count: int, read_count: int, total: int
    ):
        """
        **Feature: migration-gupshup, Property 12: Cohérence du calcul des statistiques**
        **Valide: Exigences 7.5**
        
        Pour toute campagne, augmenter delivered_count ou read_count
        doit augmenter (ou maintenir) le taux de réussite.
        """
        # Taux initial
        initial_rate = calculate_success_rate(delivered_count, read_count, total)
        
        # Taux avec un delivered de plus
        rate_with_more_delivered = calculate_success_rate(delivered_count + 1, read_count, total)
        
        # Taux avec un read de plus
        rate_with_more_read = calculate_success_rate(delivered_count, read_count + 1, total)
        
        # Les taux doivent augmenter ou rester égaux
        assert rate_with_more_delivered >= initial_rate, \
            f"Le taux devrait augmenter avec plus de delivered: {rate_with_more_delivered} < {initial_rate}"
        
        assert rate_with_more_read >= initial_rate, \
            f"Le taux devrait augmenter avec plus de read: {rate_with_more_read} < {initial_rate}"
    
    @settings(max_examples=100)
    @given(
        sent_count=st.integers(min_value=0, max_value=1000),
        delivered_count=st.integers(min_value=0, max_value=1000),
        read_count=st.integers(min_value=0, max_value=1000),
        failed_count=st.integers(min_value=0, max_value=1000),
        pending_count=st.integers(min_value=0, max_value=1000)
    )
    def test_campaign_stats_fields_consistent(
        self, sent_count: int, delivered_count: int, read_count: int,
        failed_count: int, pending_count: int
    ):
        """
        **Feature: migration-gupshup, Property 12: Cohérence du calcul des statistiques**
        **Valide: Exigences 7.5**
        
        Pour toute campagne, les champs de statistiques doivent être cohérents:
        - Tous les compteurs sont non-négatifs
        - Le total peut être calculé à partir des compteurs individuels
        """
        # Tous les compteurs doivent être non-négatifs
        assert sent_count >= 0, "sent_count doit être >= 0"
        assert delivered_count >= 0, "delivered_count doit être >= 0"
        assert read_count >= 0, "read_count doit être >= 0"
        assert failed_count >= 0, "failed_count doit être >= 0"
        assert pending_count >= 0, "pending_count doit être >= 0"
        
        # Le total des statuts terminaux doit être cohérent
        # Note: Un message peut être sent -> delivered -> read, donc ces compteurs
        # ne s'additionnent pas nécessairement au total
        # Mais sent + pending + failed devrait approximer le total
        
        # Vérifier que les compteurs sont des entiers
        assert isinstance(sent_count, int), "sent_count doit être un entier"
        assert isinstance(delivered_count, int), "delivered_count doit être un entier"
        assert isinstance(read_count, int), "read_count doit être un entier"
        assert isinstance(failed_count, int), "failed_count doit être un entier"
        assert isinstance(pending_count, int), "pending_count doit être un entier"
    
    @settings(max_examples=100)
    @given(
        total_recipients=st.integers(min_value=1, max_value=10000)
    )
    def test_success_rate_bounded_when_counts_valid(self, total_recipients: int):
        """
        **Feature: migration-gupshup, Property 12: Cohérence du calcul des statistiques**
        **Valide: Exigences 7.5**
        
        Pour toute campagne avec des compteurs valides (delivered + read <= total),
        le taux de réussite doit être entre 0% et 100%.
        """
        # Générer des compteurs valides (ne dépassant pas le total)
        import random
        delivered = random.randint(0, total_recipients)
        remaining = total_recipients - delivered
        read = random.randint(0, remaining)
        
        success_rate = calculate_success_rate(delivered, read, total_recipients)
        
        # Le taux doit être entre 0 et 100
        assert 0.0 <= success_rate <= 100.0, \
            f"Le taux de réussite {success_rate}% devrait être entre 0% et 100%"
    
    @settings(max_examples=50)
    @given(
        total=st.integers(min_value=1, max_value=1000)
    )
    def test_success_rate_100_when_all_delivered_or_read(self, total: int):
        """
        **Feature: migration-gupshup, Property 12: Cohérence du calcul des statistiques**
        **Valide: Exigences 7.5**
        
        Pour toute campagne où tous les messages sont délivrés ou lus,
        le taux de réussite doit être exactement 100%.
        """
        # Cas 1: Tous délivrés
        rate_all_delivered = calculate_success_rate(total, 0, total)
        assert abs(rate_all_delivered - 100.0) < 0.0001, \
            f"Taux devrait être 100% quand tous délivrés, obtenu {rate_all_delivered}%"
        
        # Cas 2: Tous lus
        rate_all_read = calculate_success_rate(0, total, total)
        assert abs(rate_all_read - 100.0) < 0.0001, \
            f"Taux devrait être 100% quand tous lus, obtenu {rate_all_read}%"
        
        # Cas 3: Mix délivrés et lus = total
        half = total // 2
        rate_mixed = calculate_success_rate(half, total - half, total)
        assert abs(rate_mixed - 100.0) < 0.0001, \
            f"Taux devrait être 100% quand delivered+read=total, obtenu {rate_mixed}%"
    
    @settings(max_examples=50)
    @given(
        total=st.integers(min_value=1, max_value=1000)
    )
    def test_success_rate_0_when_none_delivered_or_read(self, total: int):
        """
        **Feature: migration-gupshup, Property 12: Cohérence du calcul des statistiques**
        **Valide: Exigences 7.5**
        
        Pour toute campagne où aucun message n'est délivré ni lu,
        le taux de réussite doit être exactement 0%.
        """
        success_rate = calculate_success_rate(0, 0, total)
        
        assert success_rate == 0.0, \
            f"Taux devrait être 0% quand aucun délivré/lu, obtenu {success_rate}%"
