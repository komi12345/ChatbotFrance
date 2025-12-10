"""
Routes CRUD pour les campagnes - Gestion des campagnes d'envoi de messages
Utilise le client Supabase pour les opérations de base de données

Migration Twilio Sandbox 2025: Les envois passent par les tâches Celery qui utilisent twilio_service
Exigences: 7.1, 7.4
"""
import logging
from typing import List, Optional, Dict
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.supabase_client import SupabaseDB, get_supabase_db
from app.schemas.campaign import (
    CampaignCreate,
    CampaignUpdate,
    CampaignResponse,
    CampaignWithCategories,
    CampaignStats,
    CampaignRetryResult,
)
from app.services.auth_service import get_current_user
from app.utils.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from app.tasks.message_tasks import (
    send_campaign_messages,
    retry_campaign_failed_messages,
)
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


def campaign_to_response(campaign: Dict, categories: List[Dict] = None) -> CampaignWithCategories:
    """Convertit un dict campagne en CampaignWithCategories"""
    return CampaignWithCategories(
        id=campaign["id"],
        name=campaign["name"],
        message_1=campaign.get("message_1", ""),
        message_2=campaign.get("message_2"),
        template_name=campaign.get("template_name"),
        status=campaign.get("status", "draft"),
        total_recipients=campaign.get("total_recipients", 0),
        sent_count=campaign.get("sent_count", 0),
        delivered_count=campaign.get("delivered_count", 0),
        read_count=campaign.get("read_count", 0),
        failed_count=campaign.get("failed_count", 0),
        created_by=campaign["created_by"],
        created_at=campaign.get("created_at"),
        updated_at=campaign.get("updated_at"),
        scheduled_at=campaign.get("scheduled_at"),
        completed_at=campaign.get("completed_at"),
        categories=categories or [],
        success_rate=0.0
    )


@router.get("")
async def list_campaigns(
    page: int = Query(1, ge=1, description="Numéro de page"),
    size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="Nombre d'éléments par page"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filtrer par statut"),
    db: SupabaseDB = Depends(get_supabase_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Liste toutes les campagnes avec pagination (partagées entre tous les utilisateurs).
    Requirements: 5.1 - All users see all campaigns regardless of creator
    """
    skip = (page - 1) * size
    campaigns, total = db.get_campaigns(
        skip=skip,
        limit=size,
        status=status_filter
    )
    
    pages = (total + size - 1) // size if total > 0 else 1
    
    items = []
    for campaign in campaigns:
        categories = db.get_campaign_categories(campaign["id"])
        campaign_response = campaign_to_response(campaign, categories)
        
        # Calculer le taux de réussite
        if campaign.get("total_recipients", 0) > 0:
            campaign_response.success_rate = (
                (campaign.get("delivered_count", 0) + campaign.get("read_count", 0)) 
                / campaign["total_recipients"] * 100
            )
        
        items.append(campaign_response)
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }


@router.post("", response_model=CampaignWithCategories, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    campaign_data: CampaignCreate,
    auto_send: bool = Query(False, description="Lancer l'envoi automatiquement après création"),
    db: SupabaseDB = Depends(get_supabase_db),
    current_user: Dict = Depends(get_current_user)
) -> CampaignWithCategories:
    """
    Crée une nouvelle campagne et optionnellement lance l'envoi.
    """
    # Vérifier que les catégories existent (partagées entre tous les utilisateurs)
    categories = []
    for cat_id in campaign_data.category_ids:
        category = db.get_category_by_id(cat_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Catégorie {cat_id} non trouvée"
            )
        categories.append(category)
    
    # Compter le nombre total de destinataires (partagés entre tous les utilisateurs)
    all_contacts = set()
    for cat_id in campaign_data.category_ids:
        contacts = db.get_contacts_by_category(cat_id)
        for contact in contacts:
            all_contacts.add(contact["id"])
    
    total_recipients = len(all_contacts)
    
    if total_recipients == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Aucun contact dans les catégories sélectionnées"
        )
    
    # Créer la campagne
    campaign = db.create_campaign({
        "name": campaign_data.name,
        "message_1": campaign_data.message_1,
        "message_2": campaign_data.message_2,
        "template_name": campaign_data.template_name,
        "status": "draft",
        "total_recipients": total_recipients,
        "sent_count": 0,
        "delivered_count": 0,
        "read_count": 0,
        "failed_count": 0,
        "created_by": current_user["id"]
    })
    
    # Associer les catégories
    db.set_campaign_categories(campaign["id"], campaign_data.category_ids)
    
    logger.info(
        f"Campagne '{campaign['name']}' créée (ID: {campaign['id']}) "
        f"par utilisateur {current_user['id']} avec {total_recipients} destinataires"
    )
    
    # Lancer l'envoi si demandé (via Celery + twilio_service - Exigence 7.1, 7.4)
    if auto_send:
        campaign = db.update_campaign(campaign["id"], {"status": "sending"})
        # Déclencher l'envoi asynchrone via Celery (utilise twilio_service)
        send_campaign_messages.delay(campaign["id"])
        logger.info(f"Tâche Celery d'envoi créée pour campagne {campaign['id']}")
    
    return campaign_to_response(campaign, categories)


@router.get("/{campaign_id}", response_model=CampaignWithCategories)
async def get_campaign(
    campaign_id: int,
    db: SupabaseDB = Depends(get_supabase_db),
    current_user: Dict = Depends(get_current_user)
) -> CampaignWithCategories:
    """
    Récupère les détails d'une campagne (partagée entre tous les utilisateurs).
    Requirements: 5.3 - Any user can access any campaign by ID
    """
    campaign = db.get_campaign_by_id(campaign_id)
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campagne non trouvée"
        )
    
    categories = db.get_campaign_categories(campaign_id)
    
    return campaign_to_response(campaign, categories)


@router.put("/{campaign_id}", response_model=CampaignWithCategories)
async def update_campaign(
    campaign_id: int,
    campaign_data: CampaignUpdate,
    db: SupabaseDB = Depends(get_supabase_db),
    current_user: Dict = Depends(get_current_user)
) -> CampaignWithCategories:
    """
    Met à jour une campagne existante (partagée entre tous les utilisateurs).
    Seules les campagnes en statut 'draft' peuvent être modifiées.
    Requirements: 5.1 - Any user can modify any campaign
    """
    campaign = db.get_campaign_by_id(campaign_id)
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campagne non trouvée"
        )
    
    if campaign.get("status") != "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Seules les campagnes en brouillon peuvent être modifiées"
        )
    
    # Préparer les données de mise à jour
    update_data = campaign_data.model_dump(exclude_unset=True)
    
    if update_data:
        campaign = db.update_campaign(campaign_id, update_data)
    
    categories = db.get_campaign_categories(campaign_id)
    
    logger.info(f"Campagne {campaign_id} mise à jour par utilisateur {current_user['id']}")
    
    return campaign_to_response(campaign, categories)


@router.post("/{campaign_id}/stop", response_model=dict)
async def stop_campaign(
    campaign_id: int,
    db: SupabaseDB = Depends(get_supabase_db),
    current_user: Dict = Depends(get_current_user)
) -> dict:
    """
    Arrête une campagne en cours d'envoi (partagée entre tous les utilisateurs).
    Marque les messages pending comme cancelled - les tâches Celery vérifieront
    le statut avant d'envoyer et s'arrêteront automatiquement.
    Requirements: 5.1 - Any user can stop any campaign
    """
    campaign = db.get_campaign_by_id(campaign_id)
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campagne non trouvée"
        )
    
    current_status = campaign.get("status")
    
    # Si la campagne est déjà terminée, retourner un succès sans rien faire
    # Note: "stopped" n'existe pas dans la BDD, on utilise "failed" pour les campagnes arrêtées
    if current_status in ("completed", "failed"):
        return {
            "success": True,
            "campaign_id": campaign_id,
            "status": current_status,
            "cancelled_messages": 0,
            "message": f"Campagne déjà {current_status}, aucune action nécessaire"
        }
    
    # Seules les campagnes en cours peuvent être arrêtées
    if current_status not in ("sending", "draft"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La campagne ne peut pas être arrêtée (statut actuel: {current_status})"
        )
    
    # Annuler les messages en attente dans la base de données
    # Les tâches Celery vérifieront le statut avant d'envoyer
    from app.supabase_client import get_supabase_client
    client = get_supabase_client()
    
    # Mettre à jour le statut de la campagne EN PREMIER à "failed" (arrêtée manuellement)
    # Note: La BDD n'a pas de statut "stopped", on utilise "failed"
    db.update_campaign(campaign_id, {"status": "failed"})
    
    # Mettre à jour les messages pending en failed (pas "cancelled" car non supporté par la BDD)
    cancelled_response = client.table("messages").update({
        "status": "failed",
        "error_message": "Campagne arrêtée par l'utilisateur"
    }).eq("campaign_id", campaign_id).eq("status", "pending").execute()
    
    cancelled_count = len(cancelled_response.data) if cancelled_response.data else 0
    
    logger.info(
        f"Campagne {campaign_id} arrêtée par utilisateur {current_user['id']}, "
        f"{cancelled_count} messages annulés"
    )
    
    return {
        "success": True,
        "campaign_id": campaign_id,
        "status": "failed",
        "cancelled_messages": cancelled_count,
        "message": f"Campagne arrêtée, {cancelled_count} message(s) annulé(s)"
    }


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(
    campaign_id: int,
    force: bool = Query(False, description="Forcer la suppression même si en cours"),
    db: SupabaseDB = Depends(get_supabase_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Supprime une campagne (partagée entre tous les utilisateurs).
    Par défaut, seules les campagnes en statut 'draft', 'failed' ou 'completed' peuvent être supprimées.
    Avec force=True, les campagnes en cours peuvent aussi être supprimées (arrête d'abord la campagne).
    Requirements: 5.1 - Any user can delete any campaign
    """
    campaign = db.get_campaign_by_id(campaign_id)
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campagne non trouvée"
        )
    
    campaign_status = campaign.get("status")
    
    # Si la campagne est en cours d'envoi
    if campaign_status == "sending":
        if not force:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La campagne est en cours d'envoi. Utilisez force=true pour forcer la suppression ou arrêtez-la d'abord."
            )
        
        # Marquer les messages pending comme failed
        from app.supabase_client import get_supabase_client
        client = get_supabase_client()
        client.table("messages").update({
            "status": "failed",
            "error_message": "Campagne supprimée par l'utilisateur"
        }).eq("campaign_id", campaign_id).eq("status", "pending").execute()
        
        logger.info(f"Messages pending marqués comme failed pour suppression campagne {campaign_id}")
    
    campaign_name = campaign["name"]
    db.delete_campaign(campaign_id)
    
    logger.info(
        f"Campagne '{campaign_name}' (ID: {campaign_id}) supprimée "
        f"par utilisateur {current_user['id']}"
    )
    
    return None


@router.post("/{campaign_id}/send", response_model=dict)
async def send_campaign(
    campaign_id: int,
    db: SupabaseDB = Depends(get_supabase_db),
    current_user: Dict = Depends(get_current_user)
) -> dict:
    """
    Lance l'envoi des messages d'une campagne (partagée entre tous les utilisateurs).
    Requirements: 5.1 - Any user can send any campaign
    """
    campaign = db.get_campaign_by_id(campaign_id)
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campagne non trouvée"
        )
    
    if campaign.get("status") != "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Seules les campagnes en brouillon peuvent être envoyées"
        )
    
    # Mettre à jour le statut
    db.update_campaign(campaign_id, {"status": "sending"})
    
    # Récupérer les contacts cibles (partagés entre tous les utilisateurs)
    contacts = db.get_contacts_for_campaign(campaign_id)
    
    # Créer les messages pour chaque contact
    for contact in contacts:
        db.create_message({
            "campaign_id": campaign_id,
            "contact_id": contact["id"],
            "content": campaign.get("message_1", ""),
            "status": "pending",
            "message_type": "message_1"
        })
    
    logger.info(
        f"Campagne {campaign_id} lancée avec {len(contacts)} messages "
        f"par utilisateur {current_user['id']}"
    )
    
    # Déclencher l'envoi asynchrone via Celery (utilise twilio_service - Exigence 7.1, 7.4)
    send_campaign_messages.delay(campaign_id)
    logger.info(f"Tâche Celery d'envoi créée pour campagne {campaign_id}")
    
    return {
        "campaign_id": campaign_id,
        "status": "sending",
        "total_messages": len(contacts),
        "message": f"Envoi lancé pour {len(contacts)} destinataires"
    }


@router.get("/{campaign_id}/stats", response_model=CampaignStats)
async def get_campaign_stats(
    campaign_id: int,
    db: SupabaseDB = Depends(get_supabase_db),
    current_user: Dict = Depends(get_current_user)
) -> CampaignStats:
    """
    Récupère les statistiques détaillées d'une campagne (partagée entre tous les utilisateurs).
    Requirements: 5.1, 5.3 - Any user can view stats for any campaign
    """
    campaign = db.get_campaign_by_id(campaign_id)
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campagne non trouvée"
        )
    
    # Récupérer les stats des messages
    message_stats = db.get_campaign_message_stats(campaign_id)
    
    total = message_stats["total"]
    success_rate = 0.0
    if total > 0:
        success_rate = (message_stats["delivered"] + message_stats["read"]) / total * 100
    
    return CampaignStats(
        campaign_id=campaign_id,
        total_recipients=campaign.get("total_recipients", 0),
        sent_count=message_stats["sent"],
        delivered_count=message_stats["delivered"],
        read_count=message_stats["read"],
        failed_count=message_stats["failed"],
        pending_count=message_stats["pending"],
        success_rate=success_rate
    )


@router.post("/{campaign_id}/retry", response_model=CampaignRetryResult)
async def retry_failed_messages(
    campaign_id: int,
    db: SupabaseDB = Depends(get_supabase_db),
    current_user: Dict = Depends(get_current_user)
) -> CampaignRetryResult:
    """
    Réessaie l'envoi des messages échoués d'une campagne (partagée entre tous les utilisateurs).
    Requirements: 5.1 - Any user can retry any campaign
    """
    campaign = db.get_campaign_by_id(campaign_id)
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campagne non trouvée"
        )
    
    # Récupérer les messages échoués
    failed_messages = db.get_failed_messages(campaign_id)
    
    if not failed_messages:
        return CampaignRetryResult(
            campaign_id=campaign_id,
            retried_count=0,
            message="Aucun message échoué à réessayer"
        )
    
    # Remettre les messages en attente
    for message in failed_messages:
        db.update_message(message["id"], {
            "status": "pending",
            "retry_count": (message.get("retry_count", 0) or 0) + 1
        })
    
    logger.info(
        f"Retry de {len(failed_messages)} messages pour la campagne {campaign_id} "
        f"par utilisateur {current_user['id']}"
    )
    
    # Déclencher le retry asynchrone via Celery (utilise twilio_service - Exigence 7.1)
    retry_campaign_failed_messages.delay(campaign_id)
    logger.info(f"Tâche Celery de retry créée pour campagne {campaign_id}")
    
    return CampaignRetryResult(
        campaign_id=campaign_id,
        retried_count=len(failed_messages),
        message=f"{len(failed_messages)} message(s) remis en file d'attente"
    )
