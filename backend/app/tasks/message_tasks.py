"""
Tâches Celery pour l'envoi de messages WhatsApp via Wassenger API 2025
Gère l'envoi massif par lots, l'envoi individuel et les retries avec backoff exponentiel

Migration: Twilio Sandbox -> Wassenger 2025
Exigences: 6.1, 6.2, 6.4
"""
import logging
import asyncio
import time
from datetime import datetime
from typing import Optional, List
from celery import shared_task
from celery.exceptions import MaxRetriesExceededError

from app.config import settings
from app.supabase_client import SupabaseDB, get_supabase_client
from app.tasks.celery_app import celery_app, rate_limiter, monitoring_service
from app.services.wassenger_service import wassenger_service, WassengerResponse

# Configuration du logger
logger = logging.getLogger(__name__)

# ==========================================================================
# CONFIGURATION WASSENGER
# ==========================================================================
# Rate limit Wassenger: 1 message par seconde (optimisé pour la réactivité)
# Note: Wassenger supporte jusqu'à 1 msg/s, on utilise 1s pour être safe
WASSENGER_RATE_LIMIT_SECONDS = 1

# Timestamp du dernier envoi pour le rate limiting Sandbox
_last_send_timestamp: float = 0.0


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
    
    Intègre le monitoring pour:
    - Vérifier la limite quotidienne avant envoi (180 messages/jour)
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
                "error_message": "Limite quotidienne de 180 messages atteinte. Réessayez demain."
            })
            return {
                "success": False,
                "message_id": message_id,
                "error": error_code,
                "error_message": "Limite quotidienne de 180 messages atteinte. Réessayez demain.",
                "blocked": True
            }
        
        # Récupérer le message
        message = db.get_message_by_id(message_id)
        if not message:
            logger.error(f"Message {message_id} non trouvé")
            return {"success": False, "error": "Message non trouvé"}
        
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
        # Note: "cancelled" n'existe pas en BDD, on utilise "failed" avec un message d'erreur spécifique
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
        if not contact:
            logger.error(f"Contact {message['contact_id']} non trouvé pour message {message_id}")
            return {"success": False, "error": "Contact non trouvé"}
        
        # Vérifier si la campagne est toujours active
        # Note: "failed" est utilisé pour les campagnes arrêtées manuellement (pas de statut "stopped" en BDD)
        # IMPORTANT: Les messages de type "message_2" (réponses automatiques) doivent être envoyés
        # même si la campagne est "completed", car ils sont déclenchés par l'interaction du contact.
        # Seuls les messages de type "message_1" sont bloqués quand la campagne est terminée.
        message_type = message.get("message_type", "message_1")
        campaign_response = client.table("campaigns").select("status").eq("id", message["campaign_id"]).limit(1).execute()
        if campaign_response.data:
            campaign_status = campaign_response.data[0].get("status")
            # Bloquer seulement si:
            # - La campagne est "failed" (arrêtée manuellement) -> bloquer tous les messages
            # - La campagne est "completed" ET c'est un message_1 -> bloquer
            # - NE PAS bloquer les message_2 quand la campagne est "completed"
            should_block = False
            if campaign_status == "failed":
                should_block = True
            elif campaign_status == "completed" and message_type != "message_2":
                should_block = True
            
            if should_block:
                logger.info(f"Campagne {message['campaign_id']} terminée/arrêtée (status={campaign_status}), skip message {message_id} (type={message_type})")
                db.update_message(message_id, {
                    "status": "failed",
                    "error_message": "Campagne arrêtée ou terminée"
                })
                return {
                    "success": False,
                    "message_id": message_id,
                    "skipped": True,
                    "reason": f"Campagne {campaign_status}"
                }
            elif campaign_status == "completed" and message_type == "message_2":
                logger.info(f"Campagne {message['campaign_id']} completed mais message_2 autorisé pour message {message_id}")
        
        # Respecter le rate limit Wassenger (1 msg/2s) - Exigence 2.5
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
            # Stocker le message_id Wassenger dans whatsapp_message_id
            db.update_message(message_id, {
                "status": "sent",
                "whatsapp_message_id": response.message_id,  # ID Wassenger
                "sent_at": datetime.utcnow().isoformat(),
                "error_message": None
            })
            
            # Incrémenter le compteur de monitoring - Requirements: 1.1
            # Utiliser le message_type du message (déjà récupéré plus haut)
            # message_type est soit "message_1" soit "message_2" selon le type de message en BDD
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
                "status": "pending" if can_retry else "failed",  # Garder pending si retry prévu
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
        # Incrémenter le compteur d'erreurs - Requirements: 6.1
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
            # Incrémenter le compteur d'erreurs - Requirements: 6.1
            monitoring_service.increment_error_counter()
            db.update_message(message_id, {
                "status": "failed",
                "error_message": f"Erreur après {current_retries} tentatives: {error_msg}"
            })
            return {"success": False, "error": error_msg}



@celery_app.task(
    bind=True,
    name="app.tasks.message_tasks.send_campaign_messages",
    acks_late=True,
)
def send_campaign_messages(
    self,
    campaign_id: int,
    batch_size: int = 20
) -> dict:
    """
    Envoie les messages d'une campagne par lots via Wassenger API.
    Respecte la limite de 1 message toutes les 2 secondes de Wassenger.
    
    Args:
        campaign_id: ID de la campagne
        batch_size: Taille des lots (défaut: 20)
    
    Returns:
        Dictionnaire avec les statistiques d'envoi
    
    Exigences: 6.1
    """
    db = get_db()
    client = get_supabase_client()
    
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
        
        # Créer les tâches d'envoi pour chaque message
        # Avec délai de 2 secondes entre chaque envoi pour respecter le rate limit Wassenger
        tasks_created = 0
        
        for message in pending_messages:
            # Créer une tâche d'envoi individuel avec délai de 2s entre chaque
            # Exigence 2.5: 1 message toutes les 2 secondes
            send_single_message.apply_async(
                args=[message["id"]],
                kwargs={
                    "is_template": is_template,
                    "template_name": template_name,
                    "content_sid": content_sid
                },
                countdown=tasks_created * WASSENGER_RATE_LIMIT_SECONDS
            )
            tasks_created += 1
        
        logger.info(f"Campagne {campaign_id}: {tasks_created} tâches d'envoi créées (délai {WASSENGER_RATE_LIMIT_SECONDS}s entre chaque)")
        
        # Programmer une tâche pour mettre à jour le statut final de la campagne
        # après que tous les messages aient été traités
        estimated_completion_time = tasks_created * WASSENGER_RATE_LIMIT_SECONDS + 30  # +30s de marge
        update_campaign_status.apply_async(
            args=[campaign_id],
            countdown=estimated_completion_time
        )
        
        return {
            "success": True,
            "campaign_id": campaign_id,
            "total_messages": total_messages,
            "tasks_created": tasks_created
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
