"""
Routes Webhook WhatsApp - Réception et traitement des webhooks Meta, Gupshup, Twilio et Wassenger
Utilise le client Supabase pour les opérations de base de données

Migration 2025: Twilio Sandbox -> Wassenger
- L'endpoint /webhooks/twilio est conservé pour rétrocompatibilité mais marqué DÉPRÉCIÉ
- L'endpoint /webhooks/wassenger est le nouvel endpoint actif
"""
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request, status, Depends
from fastapi.responses import PlainTextResponse, Response

from app.config import settings
from app.supabase_client import SupabaseDB, get_supabase_db
from app.services.wassenger_service import wassenger_service, WassengerWebhookInteraction

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.get("/whatsapp", response_class=PlainTextResponse)
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
) -> PlainTextResponse:
    """
    Endpoint de vérification du webhook WhatsApp par Meta.
    
    NOTE: Cet endpoint est conservé pour rétrocompatibilité avec Meta Cloud API.
    La migration vers Gupshup utilise l'endpoint /webhooks/gupshup.
    """
    logger.info(f"Vérification webhook Meta: mode={hub_mode}")
    
    if not hub_mode or not hub_verify_token or not hub_challenge:
        logger.warning("Paramètres de vérification manquants")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Paramètres de vérification manquants"
        )
    
    # Vérifier le token directement avec les settings
    # (Anciennement via whatsapp_service.verify_webhook)
    webhook_verify_token = settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN
    
    if hub_mode == "subscribe" and hub_verify_token == webhook_verify_token:
        logger.info("Webhook Meta vérifié avec succès")
        return PlainTextResponse(content=hub_challenge, status_code=200)
    
    logger.warning(f"Échec de la vérification du webhook Meta: mode={hub_mode}")
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Token de vérification invalide"
    )


@router.post("/whatsapp", status_code=status.HTTP_200_OK)
async def receive_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: SupabaseDB = Depends(get_supabase_db),
) -> Dict[str, str]:
    """
    Endpoint de réception des webhooks WhatsApp Meta (DÉPRÉCIÉ).
    
    NOTE: Cet endpoint est conservé pour rétrocompatibilité avec Meta Cloud API.
    La migration vers Gupshup utilise l'endpoint /webhooks/gupshup.
    Les webhooks Meta ne sont plus traités activement.
    """
    try:
        # Parser le payload JSON
        payload = await request.json()
        
        logger.warning("Webhook Meta reçu (DÉPRÉCIÉ) - Utilisez /webhooks/gupshup")
        logger.debug(f"Payload Meta: {payload}")
        
        # NOTE: Le parsing des webhooks Meta n'est plus supporté après la migration vers Gupshup.
        # Les webhooks doivent être configurés sur Gupshup Dashboard vers /webhooks/gupshup.
        
        # Retourner 200 OK immédiatement pour éviter les retries de Meta
        return {"status": "received", "note": "deprecated_endpoint"}
        
    except Exception as e:
        # Logger l'erreur mais retourner 200 OK pour éviter les retries de Meta
        logger.exception(f"Erreur lors du traitement du webhook Meta: {str(e)}")
        return {"status": "error_logged"}


# =============================================================================
# GUPSHUP WEBHOOKS (DÉPRÉCIÉ - Remplacé par Twilio)
# =============================================================================


@router.post("/gupshup", status_code=status.HTTP_200_OK)
async def receive_gupshup_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: SupabaseDB = Depends(get_supabase_db),
) -> Dict[str, str]:
    """
    Endpoint de réception des webhooks Gupshup (DÉPRÉCIÉ).
    
    NOTE: Cet endpoint est conservé pour rétrocompatibilité.
    La migration vers Twilio utilise l'endpoint /webhooks/twilio.
    Les webhooks Gupshup ne sont plus traités activement.
    
    Requirement: 8.5 - Suppression de l'ancien endpoint webhook Gupshup
    """
    try:
        # Parser le payload JSON
        payload = await request.json()
        
        logger.warning("Webhook Gupshup reçu (DÉPRÉCIÉ) - Utilisez /webhooks/twilio")
        logger.debug(f"Payload Gupshup: {payload}")
        
        # NOTE: Le parsing des webhooks Gupshup n'est plus supporté après la migration vers Twilio.
        # Les webhooks doivent être configurés sur Twilio Dashboard vers /webhooks/twilio.
        
        # Retourner 200 OK immédiatement pour éviter les retries de Gupshup
        return {"status": "received", "note": "deprecated_endpoint"}
        
    except Exception as e:
        # Logger l'erreur mais retourner 200 OK pour éviter les retries de Gupshup
        logger.exception(f"Erreur lors du traitement du webhook Gupshup: {str(e)}")
        return {"status": "error_logged"}


async def _update_campaign_counters(
    campaign_id: int,
    event_type: str,
    previous_status: str,
    db: SupabaseDB
) -> None:
    """
    Met à jour les compteurs de la campagne après un changement de statut.
    
    Args:
        campaign_id: ID de la campagne
        event_type: Type d'événement (sent, delivered, read, failed)
        previous_status: Statut précédent du message
        db: Instance de la base de données
    
    Exigence: 5.6
    """
    try:
        client = db.client
        
        # Récupérer la campagne
        campaign_response = client.table("campaigns").select("*").eq("id", campaign_id).limit(1).execute()
        campaign = campaign_response.data[0] if campaign_response.data else None
        
        if not campaign:
            logger.warning(f"Campagne {campaign_id} non trouvée pour mise à jour des compteurs")
            return
        
        update_data = {}
        
        # Incrémenter les compteurs appropriés
        if event_type == "sent" and previous_status == "pending":
            update_data["sent_count"] = (campaign.get("sent_count") or 0) + 1
            update_data["success_count"] = (campaign.get("success_count") or 0) + 1
            
        elif event_type == "failed":
            # Si le message était déjà compté comme succès, décrémenter
            if previous_status in ["sent", "delivered", "read"]:
                update_data["success_count"] = max(0, (campaign.get("success_count") or 0) - 1)
            update_data["failed_count"] = (campaign.get("failed_count") or 0) + 1
        
        # Incrémenter le compteur d'interactions pour les réponses
        # (géré dans process_gupshup_message)
        
        if update_data:
            db.update_campaign(campaign_id, update_data)
            logger.info(f"Compteurs campagne {campaign_id} mis à jour: {update_data}")
            
    except Exception as e:
        logger.exception(f"Erreur lors de la mise à jour des compteurs de campagne: {str(e)}")


# =============================================================================
# TWILIO WHATSAPP SANDBOX WEBHOOKS (DÉPRÉCIÉ - Remplacé par Wassenger 2025)
# =============================================================================


@router.post("/twilio", status_code=status.HTTP_200_OK)
async def receive_twilio_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: SupabaseDB = Depends(get_supabase_db),
) -> Response:
    """
    Endpoint de réception des webhooks Twilio WhatsApp Sandbox (DÉPRÉCIÉ).
    
    NOTE: Cet endpoint est conservé pour rétrocompatibilité.
    La migration vers Wassenger utilise l'endpoint /webhooks/wassenger.
    Les webhooks Twilio ne sont plus traités activement.
    
    Requirement: 9.3 - Migration des imports vers wassenger_service
    """
    try:
        # Parser le form data
        form_data = await request.form()
        params = {key: value for key, value in form_data.items()}
        
        logger.warning(
            f"Webhook Twilio reçu (DÉPRÉCIÉ) - Utilisez /webhooks/wassenger. "
            f"MessageSid={params.get('MessageSid', 'N/A')}"
        )
        logger.debug(f"Payload Twilio: {params}")
        
        # NOTE: Le traitement des webhooks Twilio n'est plus supporté après la migration vers Wassenger.
        # Les webhooks doivent être configurés sur Wassenger Dashboard vers /webhooks/wassenger.
        
        # Retourner TwiML vide pour éviter les retries de Twilio
        twiml_response = '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'
        return Response(
            content=twiml_response,
            media_type="application/xml",
            status_code=200
        )
        
    except Exception as e:
        # Logger l'erreur mais retourner TwiML vide pour éviter les retries de Twilio
        logger.exception(f"Erreur lors du traitement du webhook Twilio: {str(e)}")
        twiml_response = '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'
        return Response(
            content=twiml_response,
            media_type="application/xml",
            status_code=200
        )


# NOTE: process_twilio_message a été supprimé lors de la migration vers Wassenger 2025
# Utilisez process_wassenger_message à la place


# NOTE: _schedule_message_2_twilio a été supprimé lors de la migration vers Wassenger 2025
# Utilisez _schedule_message_2_wassenger à la place


# NOTE: process_twilio_status a été supprimé lors de la migration vers Wassenger 2025
# Utilisez process_wassenger_status à la place


# =============================================================================
# WASSENGER WHATSAPP WEBHOOKS (2025)
# =============================================================================


@router.post("/wassenger", status_code=status.HTTP_200_OK)
async def receive_wassenger_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: SupabaseDB = Depends(get_supabase_db),
) -> Dict[str, str]:
    """
    Endpoint de réception des webhooks Wassenger 2025.
    
    Gère les types d'événements suivants (Wassenger 2025):
    - message:in:new : Message entrant d'un contact (réponse)
    - message:out:new : Message sortant créé (en file d'attente)
    - message:update : Mise à jour de statut (sent/delivered/read/failed)
    - message:reaction : Réaction à un message (emoji)
    
    Événements legacy (rétrocompatibilité):
    - message:out:sent : Message envoyé avec succès
    - message:out:delivered : Message délivré
    - message:out:read : Message lu
    - message:out:failed : Échec d'envoi
    
    Retourne 200 OK immédiatement et traite le webhook en background task.
    
    Requirements: 3.7
    """
    try:
        # Parser le payload JSON
        payload = await request.json()
        
        event = payload.get("event", "unknown")
        logger.info(f"Webhook Wassenger reçu: event={event}")
        logger.debug(f"Payload Wassenger: {payload}")
        
        # Détecter le type d'événement et traiter en background
        if event == "message:in:new":
            # Message entrant d'un contact (réponse)
            background_tasks.add_task(
                process_wassenger_message,
                payload,
                db
            )
        elif event == "message:out:new":
            # Message sortant créé (nouveau en 2025) - statut "queued"
            background_tasks.add_task(
                process_wassenger_status,
                payload,
                db
            )
        elif event == "message:update":
            # Mise à jour de statut (NOUVEAU en 2025 - regroupe sent/delivered/read/failed)
            background_tasks.add_task(
                process_wassenger_status,
                payload,
                db
            )
        elif event == "message:reaction":
            # Réaction à un message (emoji) - traité comme une interaction
            background_tasks.add_task(
                process_wassenger_reaction,
                payload,
                db
            )
        elif event.startswith("message:out:"):
            # Anciens événements de statut (rétrocompatibilité)
            background_tasks.add_task(
                process_wassenger_status,
                payload,
                db
            )
        else:
            logger.debug(f"Événement Wassenger ignoré: {event}")
        
        # Retourner 200 OK immédiatement (Requirement 3.7)
        return {"status": "received"}
        
    except Exception as e:
        # Logger l'erreur mais retourner 200 OK pour éviter les retries de Wassenger
        logger.exception(f"Erreur lors du traitement du webhook Wassenger: {str(e)}")
        return {"status": "error_logged"}


async def process_wassenger_message(
    payload: Dict[str, Any],
    db: SupabaseDB
) -> None:
    """
    Traite un webhook Wassenger de message entrant (message:in:new).
    
    Workflow:
    1. Extraire le numéro de téléphone, le contenu et l'ID du message
    2. Rechercher le contact dans la base de données
    3. Vérifier si un Message 1 récent existe (24h)
    4. Vérifier si le Message 2 doit être envoyé
    5. Créer une tâche Celery pour l'envoi du Message 2
    6. Enregistrer l'interaction dans la table interactions
    
    Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6
    """
    try:
        # Parser le payload avec le service Wassenger
        if wassenger_service is None:
            logger.error("WassengerService non initialisé - impossible de traiter le webhook")
            return
            
        interactions = wassenger_service.parse_webhook_payload(payload)
        
        if not interactions:
            logger.warning("Aucune interaction extraite du webhook message Wassenger")
            return
        
        interaction = interactions[0]
        client = db.client
        
        # Le numéro est au format Wassenger (sans +)
        phone = interaction.contact_phone
        
        logger.info(f"Traitement message Wassenger du contact: {phone}")
        
        # Rechercher le contact par son numéro (Requirements: 4.1)
        # Essayer d'abord avec le numéro tel quel
        contact_response = client.table("contacts").select("*").eq("full_number", phone).execute()
        contact = contact_response.data[0] if contact_response.data else None
        
        if not contact:
            # Essayer avec le préfixe +
            phone_with_plus = f"+{phone}"
            contact_response = client.table("contacts").select("*").eq("full_number", phone_with_plus).execute()
            contact = contact_response.data[0] if contact_response.data else None
        
        if not contact:
            logger.warning(f"Contact non trouvé pour le numéro Wassenger: {phone}")
            return
        
        contact_id = contact["id"]
        logger.info(f"Contact trouvé: id={contact_id}")
        
        # Rechercher le dernier Message 1 envoyé au contact (dans les dernières 24h)
        # Requirements: 4.2
        cutoff_time = (datetime.utcnow() - timedelta(hours=24)).isoformat()
        
        message_1_response = client.table("messages").select("*").eq(
            "contact_id", contact_id
        ).eq(
            "message_type", "message_1"
        ).in_(
            "status", ["sent", "delivered", "read"]
        ).gte(
            "sent_at", cutoff_time
        ).order(
            "sent_at", desc=True
        ).limit(1).execute()
        
        message_1 = message_1_response.data[0] if message_1_response.data else None
        
        campaign_id = None
        should_send_message_2 = False
        
        if message_1:
            campaign_id = message_1.get("campaign_id")
            logger.info(f"Message 1 récent trouvé: id={message_1['id']}, campaign_id={campaign_id}")
            
            # Vérifier si un Message 2 a déjà été envoyé pour ce contact dans cette campagne
            # Requirements: 4.3
            message_2_response = client.table("messages").select("id").eq(
                "contact_id", contact_id
            ).eq(
                "campaign_id", campaign_id
            ).eq(
                "message_type", "message_2"
            ).execute()
            
            if not message_2_response.data:
                # Aucun Message 2 envoyé, on doit l'envoyer (Requirements: 4.4)
                should_send_message_2 = True
                logger.info(f"Message 2 doit être envoyé pour contact {contact_id}, campagne {campaign_id}")
            else:
                # Message 2 déjà envoyé, ignorer (Requirements: 4.5)
                logger.info(f"Message 2 déjà envoyé pour contact {contact_id}, campagne {campaign_id}")
        else:
            logger.info(f"Aucun Message 1 récent trouvé pour contact {contact_id}")
        
        # Enregistrer l'interaction dans la table interactions (Requirements: 4.6)
        interaction_data = {
            "campaign_id": campaign_id,
            "contact_id": contact_id,
            "message_id": message_1["id"] if message_1 else None,
            "interaction_type": interaction.interaction_type,
            "content": interaction.content,
            "whatsapp_message_id": interaction.wassenger_message_id,
            "received_at": interaction.timestamp.isoformat() if interaction.timestamp else datetime.utcnow().isoformat()
        }
        
        db.create_interaction(interaction_data)
        logger.info(f"Interaction enregistrée pour contact {contact_id}")
        
        # Incrémenter le compteur d'interactions de la campagne (Requirements: 4.6)
        if campaign_id:
            campaign_response = client.table("campaigns").select("interaction_count").eq("id", campaign_id).limit(1).execute()
            if campaign_response.data:
                current_count = campaign_response.data[0].get("interaction_count", 0) or 0
                db.update_campaign(campaign_id, {"interaction_count": current_count + 1})
                logger.info(f"Compteur d'interactions incrémenté pour campagne {campaign_id}")
        
        # Créer une tâche Celery pour l'envoi du Message 2 si nécessaire
        if should_send_message_2 and campaign_id:
            await _schedule_message_2_wassenger(campaign_id, contact_id, contact, db)
        
    except Exception as e:
        logger.exception(f"Erreur lors du traitement du message Wassenger: {str(e)}")


async def _schedule_message_2_wassenger(
    campaign_id: int,
    contact_id: int,
    contact: Dict[str, Any],
    db: SupabaseDB
) -> None:
    """
    Envoie le Message 2 IMMÉDIATEMENT suite à une interaction du contact.
    
    LOGIQUE:
    - Le contact a répondu au Message 1 dans les 24h
    - On envoie le Message 2 immédiatement pour continuer la conversation
    - Si le contact ne répond pas dans les 24h, on n'envoie PAS le Message 2
      (la campagne se termine pour ce contact)
    
    Args:
        campaign_id: ID de la campagne
        contact_id: ID du contact
        contact: Données du contact
        db: Instance de la base de données
    
    Requirements: 4.4, 4.5 - Envoyer Message 2 si interaction dans les 24h
    """
    try:
        client = db.client
        
        # Récupérer la campagne pour obtenir le contenu du Message 2
        campaign_response = client.table("campaigns").select("*").eq("id", campaign_id).limit(1).execute()
        campaign = campaign_response.data[0] if campaign_response.data else None
        
        if not campaign:
            logger.warning(f"Campagne {campaign_id} non trouvée pour Message 2")
            return
        
        # Vérifier si la campagne a un Message 2 configuré
        message_2_content = campaign.get("message_2")
        if not message_2_content:
            logger.info(f"Pas de Message 2 configuré pour campagne {campaign_id}")
            return
        
        # Créer le Message 2 dans la base de données
        message_data = {
            "campaign_id": campaign_id,
            "contact_id": contact_id,
            "message_type": "message_2",
            "content": message_2_content,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat()
        }
        
        new_message = db.create_message(message_data)
        
        if not new_message:
            logger.error(f"Échec création Message 2 pour contact {contact_id}, campagne {campaign_id}")
            return
        
        message_2_id = new_message["id"]
        logger.info(f"Message 2 créé: id={message_2_id} pour contact {contact_id}, campagne {campaign_id}")
        
        # Importer la tâche d'envoi
        from app.tasks.message_tasks import send_single_message
        
        # Envoyer le Message 2 immédiatement (avec un petit délai de 2s pour le rate limit)
        send_single_message.apply_async(
            args=[message_2_id],
            kwargs={
                "is_template": False,
                "template_name": None
            },
            countdown=2  # 2 secondes de délai pour respecter le rate limit
        )
        
        logger.info(
            f"Message 2 envoyé immédiatement pour contact {contact_id}, campagne {campaign_id} "
            f"(contact a répondu au Message 1)"
        )
            
    except Exception as e:
        logger.exception(f"Erreur lors de l'envoi du Message 2 (Wassenger): {str(e)}")


async def process_wassenger_status(
    payload: Dict[str, Any],
    db: SupabaseDB
) -> None:
    """
    Traite un webhook Wassenger de statut de livraison (2025).
    
    Gère les événements:
    - message:out:new (queued)
    - message:update (sent/delivered/read/failed/pending)
    - message:out:sent/delivered/read/failed (legacy)
    
    Workflow:
    1. Extraire le type d'événement et l'ID du message
    2. Rechercher le message par wassenger_message_id (whatsapp_message_id)
    3. Mettre à jour le statut du message avec horodatage
    4. Mettre à jour les compteurs de la campagne
    
    Requirements: 3.3, 3.4, 3.5, 3.6
    """
    try:
        # Parser le payload avec le service Wassenger
        if wassenger_service is None:
            logger.error("WassengerService non initialisé - impossible de traiter le webhook")
            return
            
        interactions = wassenger_service.parse_webhook_payload(payload)
        
        if not interactions:
            logger.debug("Aucune interaction de statut extraite du webhook Wassenger")
            return
        
        interaction = interactions[0]
        client = db.client
        
        event_type = interaction.interaction_type
        wassenger_message_id = interaction.wassenger_message_id
        
        logger.info(f"Traitement statut Wassenger: type={event_type}, message_id={wassenger_message_id}")
        
        # Ignorer les statuts inconnus
        if event_type == "unknown":
            logger.debug(f"Statut Wassenger inconnu ignoré: message_id={wassenger_message_id}")
            return
        
        # Rechercher le message par whatsapp_message_id (qui stocke l'ID Wassenger)
        message = None
        
        if wassenger_message_id:
            message_response = client.table("messages").select("*").eq(
                "whatsapp_message_id", wassenger_message_id
            ).limit(1).execute()
            message = message_response.data[0] if message_response.data else None
        
        if not message:
            logger.warning(
                f"Message non trouvé pour statut Wassenger: message_id={wassenger_message_id}"
            )
            return
        
        message_id = message["id"]
        campaign_id = message.get("campaign_id")
        current_status = message.get("status", "")
        
        logger.info(f"Message trouvé: id={message_id}, status actuel={current_status}")
        
        # Préparer les données de mise à jour selon le type d'événement
        update_data = {}
        timestamp_str = interaction.timestamp.isoformat() if interaction.timestamp else datetime.utcnow().isoformat()
        
        if event_type == "queued":
            # Message en file d'attente (nouveau en 2025)
            # Ne pas rétrograder si déjà envoyé
            if current_status in ["pending"]:
                logger.debug(f"Message {message_id} en file d'attente (queued)")
                # Pas de mise à jour nécessaire, le statut reste "pending"
                
        elif event_type == "pending":
            # Statut pending (mapping depuis queued dans message:update)
            if current_status in ["pending"]:
                logger.debug(f"Message {message_id} en attente (pending)")
                # Pas de mise à jour nécessaire
                
        elif event_type == "sent":
            # Message envoyé (Requirements: 3.3)
            if current_status in ["pending"]:
                update_data["status"] = "sent"
                update_data["sent_at"] = timestamp_str
                
        elif event_type == "delivered":
            # Message délivré (Requirements: 3.4)
            if current_status in ["pending", "sent"]:
                update_data["status"] = "delivered"
                update_data["delivered_at"] = timestamp_str
                
        elif event_type == "read":
            # Message lu (Requirements: 3.5)
            if current_status in ["pending", "sent", "delivered"]:
                update_data["status"] = "read"
                update_data["read_at"] = timestamp_str
                
        elif event_type == "failed":
            # Message échoué (Requirements: 3.6)
            error_message = interaction.error_message or "Erreur inconnue"
            
            update_data["status"] = "failed"
            update_data["error_message"] = error_message
            logger.error(f"Message {message_id} échoué (Wassenger): {error_message}")
        
        # Mettre à jour le message si nécessaire
        if update_data:
            db.update_message(message_id, update_data)
            logger.info(f"Message {message_id} mis à jour (Wassenger): {update_data}")
            
            # Mettre à jour les compteurs de la campagne
            if campaign_id:
                await _update_campaign_counters(campaign_id, event_type, current_status, db)
        
    except Exception as e:
        logger.exception(f"Erreur lors du traitement du statut Wassenger: {str(e)}")


async def process_wassenger_reaction(
    payload: Dict[str, Any],
    db: SupabaseDB
) -> None:
    """
    Traite un webhook Wassenger de réaction à un message (message:reaction).
    
    Les réactions sont traitées comme des interactions et enregistrées dans la base.
    
    Workflow:
    1. Extraire le numéro de téléphone, l'emoji et l'ID du message
    2. Rechercher le contact dans la base de données
    3. Enregistrer l'interaction de type "reaction"
    4. Incrémenter le compteur d'interactions de la campagne
    """
    try:
        # Parser le payload avec le service Wassenger
        if wassenger_service is None:
            logger.error("WassengerService non initialisé - impossible de traiter le webhook")
            return
            
        interactions = wassenger_service.parse_webhook_payload(payload)
        
        if not interactions:
            logger.debug("Aucune interaction de réaction extraite du webhook Wassenger")
            return
        
        interaction = interactions[0]
        client = db.client
        
        phone = interaction.contact_phone
        emoji = interaction.content  # L'emoji de réaction
        wassenger_message_id = interaction.wassenger_message_id
        
        logger.info(f"Traitement réaction Wassenger: emoji={emoji}, phone={phone}, message_id={wassenger_message_id}")
        
        # Rechercher le contact par son numéro
        contact_response = client.table("contacts").select("*").eq("full_number", phone).execute()
        contact = contact_response.data[0] if contact_response.data else None
        
        if not contact:
            # Essayer avec le préfixe +
            phone_with_plus = f"+{phone}"
            contact_response = client.table("contacts").select("*").eq("full_number", phone_with_plus).execute()
            contact = contact_response.data[0] if contact_response.data else None
        
        if not contact:
            logger.warning(f"Contact non trouvé pour réaction Wassenger: {phone}")
            return
        
        contact_id = contact["id"]
        
        # Rechercher le message original par son ID Wassenger
        message = None
        campaign_id = None
        
        if wassenger_message_id:
            message_response = client.table("messages").select("*").eq(
                "whatsapp_message_id", wassenger_message_id
            ).limit(1).execute()
            message = message_response.data[0] if message_response.data else None
            
            if message:
                campaign_id = message.get("campaign_id")
        
        # Enregistrer l'interaction de type "reaction"
        interaction_data = {
            "campaign_id": campaign_id,
            "contact_id": contact_id,
            "message_id": message["id"] if message else None,
            "interaction_type": "reaction",
            "content": emoji,  # L'emoji de réaction
            "whatsapp_message_id": wassenger_message_id,
            "received_at": interaction.timestamp.isoformat() if interaction.timestamp else datetime.utcnow().isoformat()
        }
        
        db.create_interaction(interaction_data)
        logger.info(f"Réaction '{emoji}' enregistrée pour contact {contact_id}")
        
        # Incrémenter le compteur d'interactions de la campagne
        if campaign_id:
            campaign_response = client.table("campaigns").select("interaction_count").eq("id", campaign_id).limit(1).execute()
            if campaign_response.data:
                current_count = campaign_response.data[0].get("interaction_count", 0) or 0
                db.update_campaign(campaign_id, {"interaction_count": current_count + 1})
                logger.info(f"Compteur d'interactions incrémenté pour campagne {campaign_id} (réaction)")
        
    except Exception as e:
        logger.exception(f"Erreur lors du traitement de la réaction Wassenger: {str(e)}")
