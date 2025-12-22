"""
Tâches Celery pour l'envoi de messages WhatsApp via Wassenger API 2025
Gère l'envoi massif par lots, l'envoi individuel et les retries avec backoff exponentiel

Migration: Twilio Sandbox -> Wassenger 2025
Exigences: 6.1, 6.2, 6.4

Logique Message 2:
- Message 1 est envoyé au contact
- Si le contact répond (interaction) dans les 24h -> Message 2 envoyé IMMÉDIATEMENT
- Si le contact ne répond pas dans les 24h -> Message 2 N'EST PAS envoyé (campagne terminée pour ce contact)
- Cela permet aux campagnes de se terminer après 24h maximum

ROBUSTESSE 2025:
- Gestion des interruptions brutales (connexion perdue, crash serveur)
- Protection contre les doublons d'envoi
- Idempotence des tâches (réexécution sûre)
- Validation des données avant traitement
- Timeouts et circuit breakers
"""
import logging
import asyncio
import time
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List
from celery import shared_task
from celery.exceptions import MaxRetriesExceededError, SoftTimeLimitExceeded
from contextlib import contextmanager

from app.config import settings
from app.supabase_client import SupabaseDB, get_supabase_client
from app.tasks.celery_app import celery_app, rate_limiter, monitoring_service
from app.services.wassenger_service import wassenger_service, WassengerResponse

# Configuration du logger
logger = logging.getLogger(__name__)

# ==========================================================================
# CONFIGURATION WASSENGER - ANTI-BAN SETTINGS 2025
# ==========================================================================
# Rate limit Wassenger: 25 secondes entre chaque message
# IMPORTANT: WhatsApp peut bannir les numéros qui envoient trop vite !
# 
# Recommandations 2025 pour éviter les bans:
# - Nouveaux comptes: 30-60 secondes entre messages
# - Comptes matures (>6 mois): 20-30 secondes entre messages
# - Messages identiques: risque de ban après 20-30 envois
# - Messages personnalisés: permet d'envoyer 500+ messages en sécurité
#
# Configuration actuelle: 25 secondes (sécuritaire pour la plupart des comptes)
# Pour 1000 messages: ~7 heures d'envoi (1000 * 25s = 25000s ≈ 6.9h)
WASSENGER_RATE_LIMIT_SECONDS = 25

# Batch configuration pour envois massifs
# Envoyer par lots de 25 messages, puis pause de 5 minutes
BATCH_SIZE = 25
BATCH_PAUSE_SECONDS = 300  # 5 minutes de pause entre les lots

# Délai avant l'envoi du Message 2 (24 heures en secondes)
MESSAGE_2_DELAY_SECONDS = 24 * 60 * 60  # 86400 secondes = 24h

# Timestamp du dernier envoi pour le rate limiting Sandbox
_last_send_timestamp: float = 0.0

# ==========================================================================
# ROBUSTESSE - PROTECTION CONTRE LES DOUBLONS ET INTERRUPTIONS
# ==========================================================================
# TTL pour les verrous d'idempotence (5 minutes)
IDEMPOTENCY_LOCK_TTL = 300

# Timeout pour les opérations d'envoi (30 secondes)
SEND_OPERATION_TIMEOUT = 30

# Nombre maximum de vérifications de statut avant abandon
MAX_STATUS_CHECKS = 3


def get_idempotency_key(message_id: int, operation: str = "send") -> str:
    """
    Génère une clé d'idempotence unique pour une opération sur un message.
    Permet d'éviter les doublons en cas de réexécution de tâche.
    
    Args:
        message_id: ID du message
        operation: Type d'opération (send, retry, etc.)
    
    Returns:
        Clé d'idempotence unique
    """
    return f"idempotency:{operation}:{message_id}"


def acquire_idempotency_lock(message_id: int, operation: str = "send") -> bool:
    """
    Acquiert un verrou d'idempotence pour éviter les doublons.
    
    Args:
        message_id: ID du message
        operation: Type d'opération
    
    Returns:
        True si le verrou est acquis, False si déjà verrouillé
    """
    try:
        key = get_idempotency_key(message_id, operation)
        redis_client = monitoring_service.redis_client
        
        # SET NX avec TTL - retourne True si la clé n'existait pas
        acquired = redis_client.set(key, datetime.utcnow().isoformat(), nx=True, ex=IDEMPOTENCY_LOCK_TTL)
        
        if acquired:
            logger.debug(f"Verrou d'idempotence acquis: {key}")
        else:
            logger.warning(f"Verrou d'idempotence déjà existant: {key} - opération ignorée")
        
        return bool(acquired)
    except Exception as e:
        logger.error(f"Erreur acquisition verrou idempotence: {e}")
        # En cas d'erreur Redis, on autorise l'opération (fail-open)
        return True


def release_idempotency_lock(message_id: int, operation: str = "send") -> None:
    """
    Libère un verrou d'idempotence.
    
    Args:
        message_id: ID du message
        operation: Type d'opération
    """
    try:
        key = get_idempotency_key(message_id, operation)
        redis_client = monitoring_service.redis_client
        redis_client.delete(key)
        logger.debug(f"Verrou d'idempotence libéré: {key}")
    except Exception as e:
        logger.error(f"Erreur libération verrou idempotence: {e}")


@contextmanager
def idempotency_guard(message_id: int, operation: str = "send"):
    """
    Context manager pour garantir l'idempotence d'une opération.
    
    Usage:
        with idempotency_guard(message_id, "send") as can_proceed:
            if can_proceed:
                # Effectuer l'opération
    """
    can_proceed = acquire_idempotency_lock(message_id, operation)
    try:
        yield can_proceed
    finally:
        if can_proceed:
            release_idempotency_lock(message_id, operation)


def validate_message_data(message: dict) -> tuple[bool, str]:
    """
    Valide les données d'un message avant envoi.
    
    Args:
        message: Dictionnaire du message
    
    Returns:
        Tuple (is_valid, error_message)
    """
    if not message:
        return False, "Message non trouvé"
    
    required_fields = ["id", "contact_id", "campaign_id", "content"]
    for field in required_fields:
        if field not in message or message[field] is None:
            return False, f"Champ requis manquant: {field}"
    
    if not message.get("content", "").strip():
        return False, "Contenu du message vide"
    
    return True, ""


def validate_contact_data(contact: dict) -> tuple[bool, str]:
    """
    Valide les données d'un contact avant envoi.
    
    Args:
        contact: Dictionnaire du contact
    
    Returns:
        Tuple (is_valid, error_message)
    """
    if not contact:
        return False, "Contact non trouvé"
    
    phone = contact.get("whatsapp_id") or contact.get("full_number")
    if not phone:
        return False, "Numéro de téléphone manquant"
    
    # Validation basique du format de numéro
    phone_clean = phone.replace("+", "").replace(" ", "")
    if not phone_clean.isdigit() or len(phone_clean) < 8:
        return False, f"Format de numéro invalide: {phone}"
    
    return True, ""


def is_campaign_active(client, campaign_id: int, message_type: str = "message_1") -> tuple[bool, str]:
    """
    Vérifie si une campagne est active et peut recevoir des envois.
    
    Args:
        client: Client Supabase
        campaign_id: ID de la campagne
        message_type: Type de message (message_1 ou message_2)
    
    Returns:
        Tuple (is_active, reason)
    """
    try:
        campaign_response = client.table("campaigns").select("status").eq("id", campaign_id).limit(1).execute()
        
        if not campaign_response.data:
            return False, "Campagne non trouvée"
        
        campaign_status = campaign_response.data[0].get("status")
        
        # Bloquer si campagne arrêtée manuellement
        if campaign_status == "failed":
            return False, "Campagne arrêtée manuellement"
        
        # Pour message_1, bloquer si campagne terminée
        if campaign_status == "completed" and message_type != "message_2":
            return False, "Campagne terminée"
        
        return True, ""
        
    except Exception as e:
        logger.error(f"Erreur vérification statut campagne {campaign_id}: {e}")
        # En cas d'erreur, on autorise (fail-open) pour ne pas bloquer les envois
        return True, ""


def get_db() -> SupabaseDB:
    """Crée une nouvelle instance de base de données Supabase pour les tâches Celery"""
    return SupabaseDB()


def run_async(coro):
    """Exécute une coroutine de manière synchrone pour Celery"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def calculate_retry_delay(attempt: int) -> int:
    """
    Calcule le délai avant le prochain retry avec backoff exponentiel.
    
    Formule: délai = 60 × 2^(tentative-1) secondes
    - Tentative 1: 60s
    - Tentative 2: 120s
    - Tentative 3: 240s
    
    Args:
        attempt: Numéro de la tentative (1, 2, 3)
    
    Returns:
        Délai en secondes
    
    Exigences: 6.3
    """
    base_delay = settings.RETRY_BASE_DELAY_SECONDS  # 60 secondes
    return base_delay * (2 ** (attempt - 1))


def wait_for_wassenger_rate_limit() -> None:
    """
    Attend le délai nécessaire pour respecter le rate limit Wassenger (1 msg/2s).
    
    Cette fonction est appelée avant chaque envoi de message pour s'assurer
    qu'au moins 2 secondes se sont écoulées depuis le dernier envoi.
    
    Exigences: 2.5
    """
    global _last_send_timestamp
    
    if _last_send_timestamp > 0:
        elapsed = time.time() - _last_send_timestamp
        if elapsed < WASSENGER_RATE_LIMIT_SECONDS:
            wait_time = WASSENGER_RATE_LIMIT_SECONDS - elapsed
            logger.debug(f"Rate limit Wassenger: attente de {wait_time:.2f}s")
            time.sleep(wait_time)
    
    # Mettre à jour le timestamp après l'attente
    _last_send_timestamp = time.time()


def has_contact_interacted(client, campaign_id: int, contact_id: int, since_timestamp: str = None) -> bool:
    """
    Vérifie si un contact a eu une interaction (réponse) pour une campagne donnée.
    
    Cette fonction est utilisée pour décider si le Message 2 doit être envoyé.
    Si le contact a répondu au Message 1, on n'envoie pas le Message 2.
    
    Args:
        client: Client Supabase
        campaign_id: ID de la campagne
        contact_id: ID du contact
        since_timestamp: Timestamp ISO (optionnel, pour filtrer les interactions après cette date)
    
    Returns:
        True si le contact a eu une interaction, False sinon
    """
    try:
        query = client.table("interactions").select("id", count="exact").eq(
            "campaign_id", campaign_id
        ).eq(
            "contact_id", contact_id
        ).in_(
            "interaction_type", ["reply", "reaction"]  # Seules les réponses et réactions comptent
        )
        
        if since_timestamp:
            query = query.gte("received_at", since_timestamp)
        
        response = query.execute()
        interaction_count = response.count or 0
        
        return interaction_count > 0
        
    except Exception as e:
        logger.error(f"Erreur vérification interaction contact {contact_id}: {e}")
        return False  # En cas d'erreur, on considère qu'il n'y a pas d'interaction (sécurité)


def update_campaign_statistics(client, campaign_id: int, success: bool) -> None:
    """
    Met à jour les statistiques de la campagne après l'envoi d'un message.
    
    Args:
        client: Client Supabase
        campaign_id: ID de la campagne
        success: True si l'envoi a réussi, False sinon
    
    Exigences: 6.6
    """
    try:
        # Récupérer la campagne
        campaign_response = client.table("campaigns").select("*").eq("id", campaign_id).limit(1).execute()
        if not campaign_response.data:
            logger.warning(f"Campagne {campaign_id} non trouvée pour mise à jour des statistiques")
            return
        
        campaign = campaign_response.data[0]
        
        if success:
            # Incrémenter les compteurs de succès
            client.table("campaigns").update({
                "sent_count": (campaign.get("sent_count") or 0) + 1,
                "success_count": (campaign.get("success_count") or 0) + 1
            }).eq("id", campaign_id).execute()
        else:
            # Incrémenter le compteur d'échecs
            client.table("campaigns").update({
                "failed_count": (campaign.get("failed_count") or 0) + 1
            }).eq("id", campaign_id).execute()
        
        logger.debug(f"Statistiques campagne {campaign_id} mises à jour (success={success})")
        
    except Exception as e:
        logger.error(f"Erreur mise à jour statistiques campagne {campaign_id}: {e}")


@celery_app.task(
    bind=True,
    name="app.tasks.message_tasks.send_single_message",
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
    soft_time_limit=60,  # Timeout souple de 60 secondes
    time_limit=90,  # Timeout dur de 90 secondes
)
def send_single_message(
    self,
    message_id: int,
    is_template: bool = True,
    template_name: Optional[str] = None,
    content_sid: Optional[str] = None
) -> dict:
    """
    Envoie un message individuel via Wassenger WhatsApp API.
    
    ROBUSTESSE:
    - Verrou d'idempotence pour éviter les doublons
    - Validation des données avant envoi
    - Vérification du statut de la campagne
    - Gestion des timeouts
    - Protection contre les interruptions
    
    Intègre le monitoring pour:
    - Vérifier la limite quotidienne avant envoi (1000 messages/jour)
    - Incrémenter les compteurs de messages envoyés
    - Incrémenter les compteurs d'erreurs en cas d'échec
    
    Args:
        message_id: ID du message dans la base de données
        is_template: True pour Message 1 (template), False pour Message 2 (texte)
        template_name: Nom du template WhatsApp (pour référence, non utilisé avec Wassenger)
        content_sid: SID du template (non utilisé avec Wassenger, conservé pour compatibilité)
    
    Returns:
        Dictionnaire avec le résultat de l'envoi
    
    Exigences: 1.1, 2.1, 2.2, 6.1, 6.2, 6.4
    """
    db = get_db()
    client = get_supabase_client()
    
    # Vérifier l'idempotence - éviter les doublons en cas de réexécution
    if not acquire_idempotency_lock(message_id, "send"):
        logger.info(f"Message {message_id} déjà en cours de traitement (idempotence), skip")
        return {
            "success": True,
            "message_id": message_id,
            "skipped": True,
            "reason": "Opération déjà en cours (idempotence)"
        }
    
    try:
        # Vérifier la limite quotidienne avant envoi - Requirements: 2.1, 2.2
        can_send, error_code = monitoring_service.can_send_message()
        if not can_send:
            logger.warning(
                f"Message {message_id} bloqué: limite quotidienne atteinte",
                extra={"error_code": error_code}
            )
            # Mettre à jour le message avec l'erreur
            db.update_message(message_id, {
                "status": "failed",
                "error_message": "Limite quotidienne de 1000 messages atteinte. Réessayez demain."
            })
            return {
                "success": False,
                "message_id": message_id,
                "error": error_code,
                "error_message": "Limite quotidienne de 1000 messages atteinte. Réessayez demain.",
                "blocked": True
            }
        
        # Récupérer le message
        message = db.get_message_by_id(message_id)
        
        # Validation des données du message
        is_valid, error_msg = validate_message_data(message)
        if not is_valid:
            logger.error(f"Message {message_id} invalide: {error_msg}")
            return {"success": False, "error": error_msg}
        
        # IMPORTANT: Vérifier si le message a déjà été envoyé (évite les doublons)
        current_status = message.get("status")
        if current_status in ("sent", "delivered", "read"):
            logger.info(f"Message {message_id} déjà envoyé (status={current_status}), skip")
            return {
                "success": True,
                "message_id": message_id,
                "skipped": True,
                "reason": f"Message déjà envoyé (status={current_status})"
            }
        
        # Vérifier si le message a été annulé/échoué manuellement
        if current_status == "failed" and message.get("error_message") == "Campagne arrêtée par l'utilisateur":
            logger.info(f"Message {message_id} annulé par l'utilisateur, skip")
            return {
                "success": False,
                "message_id": message_id,
                "skipped": True,
                "reason": "Message annulé par l'utilisateur"
            }
        
        # Récupérer le contact via requête directe
        contact_response = client.table("contacts").select("*").eq("id", message["contact_id"]).limit(1).execute()
        contact = contact_response.data[0] if contact_response.data else None
        
        # Validation des données du contact
        is_valid, error_msg = validate_contact_data(contact)
        if not is_valid:
            logger.error(f"Contact invalide pour message {message_id}: {error_msg}")
            db.update_message(message_id, {
                "status": "failed",
                "error_message": error_msg
            })
            return {"success": False, "error": error_msg}
        
        # Vérifier si la campagne est toujours active
        message_type = message.get("message_type", "message_1")
        is_active, reason = is_campaign_active(client, message["campaign_id"], message_type)
        
        if not is_active:
            logger.info(f"Campagne {message['campaign_id']} inactive ({reason}), skip message {message_id}")
            db.update_message(message_id, {
                "status": "failed",
                "error_message": reason
            })
            return {
                "success": False,
                "message_id": message_id,
                "skipped": True,
                "reason": reason
            }
        
        # Respecter le rate limit Wassenger (25s entre messages) - Exigence 2.5
        wait_for_wassenger_rate_limit()
        
        # Envoyer le message via Wassenger API
        phone = contact.get("whatsapp_id") or contact.get("full_number")
        
        # Wassenger utilise uniquement des messages texte (pas de templates Twilio)
        # Le contenu du message est toujours dans message["content"]
        response = run_async(
            wassenger_service.send_message(
                phone=phone,
                text=message["content"]
            )
        )
        
        # Mettre à jour le statut du message
        if response.success:
            sent_at_timestamp = datetime.utcnow().isoformat()
            
            # Stocker le message_id Wassenger dans whatsapp_message_id
            db.update_message(message_id, {
                "status": "sent",
                "whatsapp_message_id": response.message_id,  # ID Wassenger
                "sent_at": sent_at_timestamp,
                "error_message": None
            })
            
            # Incrémenter le compteur de monitoring - Requirements: 1.1
            logger.info(f"Compteur {message_type} incrémenté")
            monitoring_service.increment_message_counter(message_type)
            
            # Mettre à jour les statistiques de la campagne
            update_campaign_statistics(client, message["campaign_id"], success=True)
            
            logger.info(f"Message {message_id} envoyé avec succès via Wassenger, ID: {response.message_id}")
            
            return {
                "success": True,
                "message_id": message_id,
                "wassenger_message_id": response.message_id
            }
        else:
            # Échec de l'envoi - Incrémenter le compteur d'erreurs - Requirements: 6.1
            monitoring_service.increment_error_counter()
            
            retry_count = (message.get("retry_count") or 0) + 1
            
            # Vérifier si on peut encore réessayer
            can_retry = retry_count < settings.MAX_RETRY_ATTEMPTS
            
            db.update_message(message_id, {
                "status": "pending" if can_retry else "failed",
                "error_message": response.error_message,
                "retry_count": retry_count
            })
            
            # Mettre à jour les statistiques seulement si échec définitif
            if not can_retry:
                update_campaign_statistics(client, message["campaign_id"], success=False)
            
            logger.error(
                f"Échec envoi message {message_id}: {response.error_code} - {response.error_message}"
            )
            
            # Programmer un retry si possible (max 3 tentatives - Exigence 6.4)
            if can_retry:
                # Délai exponentiel: 30s, 60s, 120s (réduit pour réactivité)
                delay = 30 * (2 ** (retry_count - 1))
                logger.info(f"Message {message_id}: retry programmé dans {delay}s (tentative {retry_count})")
                raise self.retry(countdown=delay)
            
            return {
                "success": False,
                "message_id": message_id,
                "error": response.error_message,
                "retry_count": retry_count
            }
    
    except SoftTimeLimitExceeded:
        # Timeout atteint - marquer comme pending pour retry automatique
        logger.warning(f"Message {message_id}: timeout atteint, sera réessayé")
        db.update_message(message_id, {
            "status": "pending",
            "error_message": "Timeout - sera réessayé automatiquement"
        })
        return {"success": False, "error": "Timeout", "will_retry": True}
            
    except MaxRetriesExceededError:
        logger.error(f"Message {message_id}: nombre maximum de retries atteint")
        # Incrémenter le compteur d'erreurs - Requirements: 6.1
        monitoring_service.increment_error_counter()
        # Marquer définitivement comme échoué
        db.update_message(message_id, {
            "status": "failed",
            "error_message": "Nombre maximum de tentatives atteint"
        })
        update_campaign_statistics(client, message["campaign_id"], success=False)
        return {"success": False, "error": "Max retries exceeded"}
        
    except self.MaxRetriesExceededError:
        # Alias pour compatibilité
        logger.error(f"Message {message_id}: nombre maximum de retries atteint")
        monitoring_service.increment_error_counter()
        db.update_message(message_id, {
            "status": "failed",
            "error_message": "Nombre maximum de tentatives atteint"
        })
        return {"success": False, "error": "Max retries exceeded"}
        
    except Exception as e:
        error_msg = str(e)
        logger.exception(f"Erreur inattendue lors de l'envoi du message {message_id}: {error_msg}")
        
        # Vérifier le nombre de retries avant de réessayer
        current_retries = self.request.retries
        if current_retries < self.max_retries:
            delay = 30 * (2 ** current_retries)
            raise self.retry(exc=e, countdown=delay)
        else:
            # Max retries atteint, marquer comme échoué
            monitoring_service.increment_error_counter()
            db.update_message(message_id, {
                "status": "failed",
                "error_message": f"Erreur après {current_retries} tentatives: {error_msg}"
            })
            return {"success": False, "error": error_msg}
    
    finally:
        # Toujours libérer le verrou d'idempotence
        release_idempotency_lock(message_id, "send")



@celery_app.task(
    bind=True,
    name="app.tasks.message_tasks.send_campaign_messages",
    acks_late=True,
)
def send_campaign_messages(
    self,
    campaign_id: int,
    batch_size: int = None
) -> dict:
    """
    Envoie les messages d'une campagne par lots via Wassenger API.
    
    ANTI-BAN STRATEGY 2025:
    - Délai de 25 secondes entre chaque message
    - Envoi par lots de 25 messages avec pause de 5 minutes entre les lots
    - Pour 1000 messages: ~7-8 heures d'envoi total
    
    Args:
        campaign_id: ID de la campagne
        batch_size: Taille des lots (défaut: BATCH_SIZE = 25)
    
    Returns:
        Dictionnaire avec les statistiques d'envoi
    
    Exigences: 6.1
    """
    db = get_db()
    client = get_supabase_client()
    
    # Utiliser la taille de lot par défaut si non spécifiée
    if batch_size is None:
        batch_size = BATCH_SIZE
    
    try:
        # Récupérer la campagne directement (sans filtre user_id pour les tâches Celery)
        campaign_response = client.table("campaigns").select("*").eq("id", campaign_id).limit(1).execute()
        campaign = campaign_response.data[0] if campaign_response.data else None
        if not campaign:
            logger.error(f"Campagne {campaign_id} non trouvée")
            return {"success": False, "error": "Campagne non trouvée"}
        
        # Mettre à jour le statut de la campagne
        db.update_campaign(campaign_id, {"status": "sending"})
        
        logger.info(f"Démarrage envoi campagne {campaign_id}: {campaign.get('name')}")
        
        # Récupérer tous les messages en attente pour cette campagne
        messages_response = client.table("messages").select("*").eq("campaign_id", campaign_id).eq("status", "pending").execute()
        pending_messages = messages_response.data or []
        
        total_messages = len(pending_messages)
        logger.info(f"Campagne {campaign_id}: {total_messages} messages à envoyer")
        
        # Wassenger utilise uniquement des messages texte (pas de templates Twilio)
        # Ces paramètres sont conservés pour compatibilité mais non utilisés
        is_template = False
        content_sid = None
        template_name = campaign.get("template_name")
        
        # ==========================================================================
        # ANTI-BAN BATCH LOGIC 2025
        # ==========================================================================
        # Stratégie: Envoyer par lots avec pauses pour éviter les bans WhatsApp
        # - Lot de 25 messages avec 25s entre chaque message
        # - Pause de 5 minutes entre chaque lot
        # - Temps par lot: 25 * 25s = 625s (~10 min)
        # - Pour 1000 messages (40 lots): ~7-8 heures
        # ==========================================================================
        
        tasks_created = 0
        current_batch = 0
        
        for i, message in enumerate(pending_messages):
            # Calculer le numéro de lot actuel
            batch_number = i // batch_size
            position_in_batch = i % batch_size
            
            # Calculer le délai total:
            # - Délai de base: position dans le lot * rate limit
            # - Délai de pause: nombre de lots précédents * pause entre lots
            base_delay = position_in_batch * WASSENGER_RATE_LIMIT_SECONDS
            batch_pause_delay = batch_number * BATCH_PAUSE_SECONDS
            
            # Ajouter aussi le temps des lots précédents (messages déjà envoyés)
            previous_batches_time = batch_number * batch_size * WASSENGER_RATE_LIMIT_SECONDS
            
            total_delay = base_delay + batch_pause_delay + previous_batches_time
            
            # Log pour le premier message de chaque lot
            if position_in_batch == 0:
                logger.info(
                    f"Campagne {campaign_id}: Lot {batch_number + 1} programmé "
                    f"(messages {i + 1}-{min(i + batch_size, total_messages)}) "
                    f"démarrage dans {total_delay}s"
                )
            
            # Créer une tâche d'envoi individuel avec le délai calculé
            send_single_message.apply_async(
                args=[message["id"]],
                kwargs={
                    "is_template": is_template,
                    "template_name": template_name,
                    "content_sid": content_sid
                },
                countdown=total_delay
            )
            tasks_created += 1
        
        # Calculer le temps estimé de complétion
        num_batches = (total_messages + batch_size - 1) // batch_size  # Arrondi supérieur
        estimated_completion_time = (
            total_messages * WASSENGER_RATE_LIMIT_SECONDS +  # Temps d'envoi
            (num_batches - 1) * BATCH_PAUSE_SECONDS +  # Pauses entre lots
            60  # Marge de sécurité
        )
        
        # Convertir en heures/minutes pour le log
        hours = estimated_completion_time // 3600
        minutes = (estimated_completion_time % 3600) // 60
        
        logger.info(
            f"Campagne {campaign_id}: {tasks_created} tâches créées en {num_batches} lots. "
            f"Délai entre messages: {WASSENGER_RATE_LIMIT_SECONDS}s, "
            f"Pause entre lots: {BATCH_PAUSE_SECONDS}s. "
            f"Temps estimé: {hours}h{minutes}min"
        )
        
        # Programmer une tâche pour mettre à jour le statut final de la campagne
        update_campaign_status.apply_async(
            args=[campaign_id],
            countdown=estimated_completion_time
        )
        
        return {
            "success": True,
            "campaign_id": campaign_id,
            "total_messages": total_messages,
            "tasks_created": tasks_created,
            "num_batches": num_batches,
            "estimated_completion_seconds": estimated_completion_time,
            "estimated_completion_hours": round(estimated_completion_time / 3600, 1)
        }
        
    except Exception as e:
        logger.exception(f"Erreur lors de l'envoi de la campagne {campaign_id}: {e}")
        
        # Marquer la campagne comme échouée
        client.table("campaigns").update({"status": "failed"}).eq("id", campaign_id).execute()
        
        return {"success": False, "error": str(e)}


@celery_app.task(
    bind=True,
    name="app.tasks.message_tasks.retry_failed_message",
    max_retries=3,
    acks_late=True,
)
def retry_failed_message(
    self,
    message_id: int
) -> dict:
    """
    Réessaie l'envoi d'un message échoué via Wassenger avec backoff exponentiel.
    
    Utilise wassenger_service pour les retries.
    Délai exponentiel: 60s, 120s, 240s (formule: 60 × 2^(tentative-1))
    Marque comme échoué après 3 tentatives.
    
    Args:
        message_id: ID du message à réessayer
    
    Returns:
        Dictionnaire avec le résultat du retry
    
    Exigences: 6.4
    """
    db = get_db()
    client = get_supabase_client()
    
    try:
        # Récupérer le message
        message = db.get_message_by_id(message_id)
        if not message:
            logger.error(f"Message {message_id} non trouvé pour retry")
            return {"success": False, "error": "Message non trouvé"}
        
        retry_count = message.get("retry_count") or 0
        
        # Vérifier si le message peut être réessayé (max 3 tentatives - Exigence 6.4)
        if retry_count >= settings.MAX_RETRY_ATTEMPTS:
            # Marquer définitivement comme échoué après 3 tentatives
            db.update_message(message_id, {
                "status": "failed",
                "error_message": "Nombre maximum de tentatives atteint (3)"
            })
            
            logger.warning(
                f"Message {message_id} marqué comme échoué définitivement "
                f"(retry_count={retry_count})"
            )
            return {
                "success": False,
                "error": "Nombre maximum de tentatives atteint",
                "retry_count": retry_count
            }
        
        # Récupérer la campagne pour référence
        campaign_response = client.table("campaigns").select("*").eq("id", message["campaign_id"]).limit(1).execute()
        if not campaign_response.data:
            logger.error(f"Campagne {message['campaign_id']} non trouvée pour retry message {message_id}")
            return {"success": False, "error": "Campagne non trouvée"}
        
        campaign = campaign_response.data[0]
        
        # Réinitialiser le statut pour le retry
        db.update_message(message_id, {"status": "pending"})
        
        # Calculer le délai exponentiel (Exigence 2.6)
        # Formule: délai = 60 × 2^(tentative-1) -> 60s, 120s, 240s
        next_attempt = retry_count + 1
        delay = calculate_retry_delay(next_attempt)
        
        logger.info(
            f"Programmation retry message {message_id} via Wassenger dans {delay}s "
            f"(tentative {next_attempt}/{settings.MAX_RETRY_ATTEMPTS})"
        )
        
        # Programmer la tâche d'envoi avec délai via wassenger_service
        # Wassenger n'utilise pas de templates, mais on conserve les paramètres pour compatibilité
        send_single_message.apply_async(
            args=[message_id],
            kwargs={
                "is_template": False,
                "template_name": campaign.get("template_name"),
                "content_sid": None
            },
            countdown=delay
        )
        
        return {
            "success": True,
            "message_id": message_id,
            "retry_count": next_attempt,
            "delay_seconds": delay
        }
        
    except Exception as e:
        logger.exception(f"Erreur lors du retry du message {message_id}: {e}")
        return {"success": False, "error": str(e)}


@celery_app.task(
    bind=True,
    name="app.tasks.message_tasks.retry_campaign_failed_messages",
    acks_late=True,
)
def retry_campaign_failed_messages(
    self,
    campaign_id: int
) -> dict:
    """
    Réessaie tous les messages échoués d'une campagne via Wassenger.
    
    Args:
        campaign_id: ID de la campagne
    
    Returns:
        Dictionnaire avec les statistiques de retry
    """
    client = get_supabase_client()
    
    try:
        # Récupérer tous les messages échoués de la campagne qui peuvent être réessayés
        messages_response = client.table("messages").select("*").eq("campaign_id", campaign_id).eq("status", "failed").lt("retry_count", settings.MAX_RETRY_ATTEMPTS).execute()
        failed_messages = messages_response.data or []
        
        total_failed = len(failed_messages)
        logger.info(f"Campagne {campaign_id}: {total_failed} messages échoués à réessayer")
        
        if total_failed == 0:
            return {
                "success": True,
                "campaign_id": campaign_id,
                "retried_count": 0,
                "message": "Aucun message à réessayer"
            }
        
        # Programmer les retries avec délai de 2s entre chaque (rate limit Wassenger)
        retried_count = 0
        for message in failed_messages:
            retry_failed_message.apply_async(
                args=[message["id"]],
                countdown=retried_count * WASSENGER_RATE_LIMIT_SECONDS
            )
            retried_count += 1
        
        logger.info(f"Campagne {campaign_id}: {retried_count} retries programmés")
        
        return {
            "success": True,
            "campaign_id": campaign_id,
            "retried_count": retried_count
        }
        
    except Exception as e:
        logger.exception(f"Erreur lors du retry des messages de la campagne {campaign_id}: {e}")
        return {"success": False, "error": str(e)}


# ==========================================================================
# WHATSAPP VERIFICATION TASKS
# ==========================================================================
# Rate limit for WhatsApp verification: 2 seconds between calls
# Requirements: 6.1, 6.2
VERIFICATION_RATE_LIMIT_SECONDS = 2

# Minimum delay for rate limit retry (60 seconds)
# Requirements: 6.2
RATE_LIMIT_RETRY_DELAY_SECONDS = 60


@celery_app.task(
    bind=True,
    name="app.tasks.message_tasks.verify_whatsapp_task",
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
)
def verify_whatsapp_task(self, contact_id: int) -> dict:
    """
    Tâche asynchrone pour vérifier si un numéro de téléphone est enregistré sur WhatsApp.
    
    Utilise l'API Wassenger pour vérifier l'existence du numéro sur WhatsApp.
    Gère le rate limiting avec backoff exponentiel.
    Met à jour le contact avec le résultat de la vérification.
    
    Args:
        contact_id: ID du contact à vérifier
    
    Returns:
        Dictionnaire avec le résultat de la vérification:
        - success: True si la vérification a réussi
        - contact_id: ID du contact
        - whatsapp_verified: True/False/None selon le résultat
        - error: Message d'erreur si échec
    
    Requirements: 1.1, 6.2
    """
    db = get_db()
    client = get_supabase_client()
    
    try:
        # Récupérer le contact directement (sans filtre user_id pour les tâches Celery)
        contact_response = client.table("contacts").select("*").eq("id", contact_id).limit(1).execute()
        contact = contact_response.data[0] if contact_response.data else None
        
        if not contact:
            logger.error(f"Contact {contact_id} non trouvé pour vérification WhatsApp")
            return {"success": False, "error": "Contact non trouvé", "contact_id": contact_id}
        
        # Récupérer le numéro de téléphone
        phone = contact.get("whatsapp_id") or contact.get("full_number")
        if not phone:
            logger.error(f"Contact {contact_id} n'a pas de numéro de téléphone")
            # Marquer comme non vérifié (null) car pas de numéro
            db.update_contact(contact_id, {
                "whatsapp_verified": None,
                "verified_at": datetime.utcnow().isoformat()
            })
            return {"success": False, "error": "Numéro de téléphone manquant", "contact_id": contact_id}
        
        logger.info(f"Vérification WhatsApp pour contact {contact_id}, numéro: {phone}")
        
        # Appeler l'API Wassenger pour vérifier l'existence
        response = run_async(
            wassenger_service.check_whatsapp_exists(phone)
        )
        
        # Traiter le résultat
        if response.error_code:
            # Gérer les erreurs spécifiques
            if response.error_code == "rate_limit_exceeded":
                # Rate limit atteint - programmer un retry avec délai
                retry_count = self.request.retries
                # Backoff exponentiel: 60s, 120s, 240s
                delay = RATE_LIMIT_RETRY_DELAY_SECONDS * (2 ** retry_count)
                
                logger.warning(
                    f"Rate limit atteint pour contact {contact_id}, "
                    f"retry dans {delay}s (tentative {retry_count + 1}/{self.max_retries})"
                )
                
                raise self.retry(countdown=delay)
            
            elif response.error_code in ("timeout", "network_error", "unexpected_error"):
                # Erreur réseau/API - marquer comme null et programmer retry
                # Requirements: 1.3
                retry_count = self.request.retries
                
                if retry_count < self.max_retries:
                    # Backoff exponentiel: 60s, 120s, 240s
                    delay = settings.RETRY_BASE_DELAY_SECONDS * (2 ** retry_count)
                    
                    logger.warning(
                        f"Erreur {response.error_code} pour contact {contact_id}, "
                        f"retry dans {delay}s (tentative {retry_count + 1}/{self.max_retries})"
                    )
                    
                    raise self.retry(countdown=delay)
                else:
                    # Max retries atteint - marquer comme null
                    db.update_contact(contact_id, {
                        "whatsapp_verified": None,
                        "verified_at": datetime.utcnow().isoformat()
                    })
                    
                    logger.error(
                        f"Vérification WhatsApp échouée pour contact {contact_id} "
                        f"après {retry_count} tentatives: {response.error_message}"
                    )
                    
                    return {
                        "success": False,
                        "contact_id": contact_id,
                        "whatsapp_verified": None,
                        "error": response.error_message
                    }
            
            else:
                # Autre erreur (invalid_phone_number, etc.) - marquer comme null
                db.update_contact(contact_id, {
                    "whatsapp_verified": None,
                    "verified_at": datetime.utcnow().isoformat()
                })
                
                logger.error(
                    f"Erreur vérification WhatsApp pour contact {contact_id}: "
                    f"{response.error_code} - {response.error_message}"
                )
                
                return {
                    "success": False,
                    "contact_id": contact_id,
                    "whatsapp_verified": None,
                    "error": response.error_message
                }
        
        # Vérification réussie - mettre à jour le contact
        whatsapp_verified = response.exists
        
        db.update_contact(contact_id, {
            "whatsapp_verified": whatsapp_verified,
            "verified_at": datetime.utcnow().isoformat()
        })
        
        logger.info(
            f"Vérification WhatsApp terminée pour contact {contact_id}: "
            f"whatsapp_verified={whatsapp_verified}"
        )
        
        return {
            "success": True,
            "contact_id": contact_id,
            "whatsapp_verified": whatsapp_verified
        }
        
    except self.MaxRetriesExceededError:
        # Max retries atteint via Celery
        logger.error(f"Contact {contact_id}: nombre maximum de retries atteint")
        
        db.update_contact(contact_id, {
            "whatsapp_verified": None,
            "verified_at": datetime.utcnow().isoformat()
        })
        
        return {
            "success": False,
            "contact_id": contact_id,
            "whatsapp_verified": None,
            "error": "Nombre maximum de tentatives atteint"
        }
        
    except Exception as e:
        error_msg = str(e)
        logger.exception(f"Erreur inattendue lors de la vérification du contact {contact_id}: {error_msg}")
        
        # Vérifier le nombre de retries avant de réessayer
        current_retries = self.request.retries
        if current_retries < self.max_retries:
            delay = settings.RETRY_BASE_DELAY_SECONDS * (2 ** current_retries)
            raise self.retry(exc=e, countdown=delay)
        else:
            # Max retries atteint - marquer comme null
            db.update_contact(contact_id, {
                "whatsapp_verified": None,
                "verified_at": datetime.utcnow().isoformat()
            })
            
            return {
                "success": False,
                "contact_id": contact_id,
                "whatsapp_verified": None,
                "error": error_msg
            }


@celery_app.task(
    bind=True,
    name="app.tasks.message_tasks.bulk_verify_task",
    acks_late=True,
)
def bulk_verify_task(self, contact_ids: List[int]) -> dict:
    """
    Tâche pour vérifier plusieurs contacts en masse.
    
    Queue les vérifications individuelles avec des délais pour respecter
    le rate limit de l'API Wassenger (2 secondes entre chaque appel).
    
    Args:
        contact_ids: Liste des IDs de contacts à vérifier
    
    Returns:
        Dictionnaire avec les statistiques de la vérification en masse:
        - success: True si les tâches ont été créées
        - queued_count: Nombre de vérifications mises en file d'attente
        - total_contacts: Nombre total de contacts à vérifier
        - estimated_completion_seconds: Temps estimé pour terminer
    
    Requirements: 6.1, 6.2
    """
    try:
        total_contacts = len(contact_ids)
        
        if total_contacts == 0:
            logger.info("Aucun contact à vérifier")
            return {
                "success": True,
                "queued_count": 0,
                "total_contacts": 0,
                "message": "Aucun contact à vérifier"
            }
        
        logger.info(f"Démarrage vérification en masse de {total_contacts} contacts")
        
        # Queue les vérifications individuelles avec délai de 2s entre chaque
        # Requirements: 6.1 - respecter le rate limit API
        queued_count = 0
        
        for i, contact_id in enumerate(contact_ids):
            # Délai = index * 2 secondes pour respecter le rate limit
            delay = i * VERIFICATION_RATE_LIMIT_SECONDS
            
            verify_whatsapp_task.apply_async(
                args=[contact_id],
                countdown=delay
            )
            queued_count += 1
        
        # Calculer le temps estimé de complétion
        estimated_completion_seconds = total_contacts * VERIFICATION_RATE_LIMIT_SECONDS
        
        logger.info(
            f"Vérification en masse: {queued_count} tâches créées, "
            f"temps estimé: {estimated_completion_seconds}s"
        )
        
        return {
            "success": True,
            "queued_count": queued_count,
            "total_contacts": total_contacts,
            "estimated_completion_seconds": estimated_completion_seconds,
            "message": f"{queued_count} vérifications mises en file d'attente"
        }
        
    except Exception as e:
        logger.exception(f"Erreur lors de la vérification en masse: {e}")
        return {
            "success": False,
            "error": str(e),
            "queued_count": 0,
            "total_contacts": len(contact_ids)
        }


@celery_app.task(
    bind=True,
    name="app.tasks.message_tasks.update_campaign_status",
    acks_late=True,
)
def update_campaign_status(self, campaign_id: int) -> dict:
    """
    Met à jour le statut d'une campagne en fonction des messages envoyés.
    
    Args:
        campaign_id: ID de la campagne
    
    Returns:
        Dictionnaire avec le nouveau statut
    
    Exigences: 6.6
    """
    client = get_supabase_client()
    
    try:
        # Récupérer la campagne directement (sans filtre user_id pour les tâches Celery)
        campaign_response = client.table("campaigns").select("*").eq("id", campaign_id).limit(1).execute()
        campaign = campaign_response.data[0] if campaign_response.data else None
        if not campaign:
            return {"success": False, "error": "Campagne non trouvée"}
        
        # Compter les messages par statut
        pending_response = client.table("messages").select("id", count="exact").eq("campaign_id", campaign_id).eq("status", "pending").execute()
        pending_count = pending_response.count or 0
        
        sent_response = client.table("messages").select("id", count="exact").eq("campaign_id", campaign_id).in_("status", ["sent", "delivered", "read"]).execute()
        sent_count = sent_response.count or 0
        
        failed_response = client.table("messages").select("id", count="exact").eq("campaign_id", campaign_id).eq("status", "failed").execute()
        failed_count = failed_response.count or 0
        
        # Déterminer le statut de la campagne
        if pending_count == 0:
            if failed_count > 0 and sent_count == 0:
                new_status = "failed"
            else:
                new_status = "completed"
        else:
            new_status = "sending"
        
        # Mettre à jour la campagne - Exigence 6.6
        client.table("campaigns").update({
            "status": new_status,
            "sent_count": sent_count,
            "success_count": sent_count,
            "failed_count": failed_count
        }).eq("id", campaign_id).execute()
        
        logger.info(
            f"Campagne {campaign_id} mise à jour: status={new_status}, "
            f"sent={sent_count}, failed={failed_count}, pending={pending_count}"
        )
        
        return {
            "success": True,
            "campaign_id": campaign_id,
            "status": new_status,
            "sent_count": sent_count,
            "failed_count": failed_count,
            "pending_count": pending_count
        }
        
    except Exception as e:
        logger.exception(f"Erreur mise à jour statut campagne {campaign_id}: {e}")
        return {"success": False, "error": str(e)}


# ==========================================================================
# NOTE: MESSAGE 2 LOGIC
# ==========================================================================
# Le Message 2 est envoyé IMMÉDIATEMENT quand le contact répond au Message 1.
# Cette logique est gérée dans webhooks.py -> process_wassenger_message -> _schedule_message_2_wassenger
# 
# Si le contact ne répond pas dans les 24h, le Message 2 n'est JAMAIS envoyé.
# Cela permet aux campagnes de se terminer après 24h maximum.
# ==========================================================================
