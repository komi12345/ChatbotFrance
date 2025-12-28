"""
Routes pour les messages - Récupération et statistiques des messages
Utilise le client Supabase pour les opérations de base de données

Performance Optimization:
- Endpoint /stats utilise le cache Redis pour améliorer les temps de réponse
- Fallback automatique sur la DB si le cache est indisponible
- Requirements: 1.1, 1.5, 3.2, 3.4
"""
import logging
from typing import List, Optional, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.supabase_client import SupabaseDB, get_supabase_db, get_supabase_client
from app.schemas.message import (
    MessageResponse,
    MessageWithContact,
    MessageStats,
    MessageContactInfo,
    MessageCampaignInfo,
)
from app.services.auth_service import get_current_user
from app.services.cache_service import CacheService, get_cache_service
from app.utils.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/messages", tags=["Messages"])


@router.get("")
async def list_messages(
    page: int = Query(1, ge=1, description="Numéro de page"),
    size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="Nombre d'éléments par page"),
    limit: Optional[int] = Query(None, description="Alias pour size (compatibilité frontend)"),
    campaign_id: Optional[int] = Query(None, description="Filtrer par campagne"),
    contact_id: Optional[int] = Query(None, description="Filtrer par contact"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filtrer par statut"),
    message_type: Optional[str] = Query(None, description="Filtrer par type (message_1, message_2)"),
    db: SupabaseDB = Depends(get_supabase_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Liste tous les messages du système avec filtres et pagination.
    Affiche tous les messages sans filtrage par utilisateur (données partagées).
    Requirements: 5.2 - All users see all messages
    """
    # Utiliser limit si fourni (compatibilité frontend)
    if limit is not None:
        size = min(limit, MAX_PAGE_SIZE)
    
    skip = (page - 1) * size
    
    # Récupérer tous les messages directement (sans filtrage par campagne utilisateur)
    client = get_supabase_client()
    
    query = client.table("messages").select("*", count="exact")
    
    # Appliquer les filtres
    if campaign_id:
        query = query.eq("campaign_id", campaign_id)
    if contact_id:
        query = query.eq("contact_id", contact_id)
    if status_filter:
        query = query.eq("status", status_filter)
    if message_type:
        query = query.eq("message_type", message_type)
    
    # Pagination et tri
    response = query.order("created_at", desc=True).range(skip, skip + size - 1).execute()
    
    messages = response.data or []
    total = response.count or 0
    
    pages = (total + size - 1) // size if total > 0 else 1
    
    # Enrichir avec les informations du contact et de la campagne
    items = []
    
    # Cache pour les campagnes (récupérer toutes les campagnes pour le cache)
    campaigns, _ = db.get_campaigns(skip=0, limit=1000)
    campaign_cache = {c["id"]: c for c in campaigns}
    
    for message in messages:
        contact = db.get_contact_by_id(message["contact_id"]) if message.get("contact_id") else None
        campaign = campaign_cache.get(message.get("campaign_id"))
        
        contact_name = None
        contact_info = None
        if contact:
            first_name = contact.get("first_name", "") or ""
            last_name = contact.get("last_name", "") or ""
            contact_name = f"{first_name} {last_name}".strip() or None
            contact_info = MessageContactInfo(
                id=contact["id"],
                phone_number=contact.get("phone_number", ""),
                full_number=contact.get("full_number", ""),
                first_name=contact.get("first_name"),
                last_name=contact.get("last_name")
            )
        
        campaign_info = None
        if campaign:
            campaign_info = MessageCampaignInfo(
                id=campaign["id"],
                name=campaign["name"]
            )
        
        message_data = MessageWithContact(
            id=message["id"],
            campaign_id=message.get("campaign_id"),
            contact_id=message.get("contact_id"),
            message_type=message.get("message_type", "campaign"),
            content=message.get("content", ""),
            status=message.get("status", "pending"),
            whatsapp_message_id=message.get("whatsapp_message_id"),
            error_message=message.get("error_message"),
            retry_count=message.get("retry_count", 0),
            sent_at=message.get("sent_at"),
            delivered_at=message.get("delivered_at"),
            read_at=message.get("read_at"),
            created_at=message.get("created_at"),
            updated_at=message.get("updated_at"),
            contact_full_number=contact["full_number"] if contact else "",
            contact_name=contact_name,
            campaign_name=campaign["name"] if campaign else None,
            contact=contact_info,
            campaign=campaign_info
        )
        items.append(message_data)
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }


@router.get("/stats", response_model=MessageStats)
async def get_global_stats(
    db: SupabaseDB = Depends(get_supabase_db),
    cache: CacheService = Depends(get_cache_service),
    current_user: Dict = Depends(get_current_user)
) -> MessageStats:
    """
    Récupère les statistiques globales de tous les messages du système.
    Agrège les stats de tous les messages sans filtrage par utilisateur.
    
    Performance: Utilise le cache Redis avec TTL de 60s.
    Fallback automatique sur la DB si le cache est indisponible.
    
    Requirements: 
    - 1.1: Cache les résultats avec TTL de 60 secondes
    - 1.5: Retourne les données en moins de 200ms avec cache
    - 3.2: Stratégie cache-aside (lecture cache, fallback DB)
    - 3.4: Mode dégradé si cache indisponible
    - 5.2: Message statistics aggregate all data
    """
    # Clé de cache pour les stats globales
    cache_key = "messages_global"
    
    # Essayer de récupérer depuis le cache d'abord
    cached_stats = cache.get("stats", cache_key)
    if cached_stats is not None:
        logger.debug("Stats récupérées depuis le cache")
        return MessageStats(**cached_stats)
    
    # Fallback sur la DB - calcul des statistiques
    logger.debug("Cache miss - calcul des stats depuis la DB")
    stats = await _compute_message_stats_from_db()
    
    # Mettre en cache pour les prochaines requêtes (TTL 60s)
    cache.set("stats", cache_key, stats.model_dump(), CacheService.STATS_TTL)
    
    return stats


async def _compute_message_stats_from_db() -> MessageStats:
    """
    Calcule les statistiques des messages depuis la base de données.
    
    Cette fonction est appelée en cas de cache miss.
    Elle effectue les requêtes SQL nécessaires pour agréger les stats.
    
    Returns:
        MessageStats: Statistiques calculées depuis la DB
    
    Requirements: 5.1 - Agrégation en requêtes optimisées
    """
    client = get_supabase_client()
    
    # Compter les messages par statut directement depuis la BDD (tous les messages)
    total_messages = 0
    sent_count = 0
    delivered_count = 0
    read_count = 0
    failed_count = 0
    pending_count = 0
    
    for status_val in ["sent", "delivered", "read", "failed", "pending"]:
        count_response = client.table("messages").select("id", count="exact").eq("status", status_val).execute()
        count = count_response.count or 0
        total_messages += count
        
        if status_val == "sent":
            sent_count = count
        elif status_val == "delivered":
            delivered_count = count
        elif status_val == "read":
            read_count = count
        elif status_val == "failed":
            failed_count = count
        elif status_val == "pending":
            pending_count = count
    
    success_rate = 0.0
    delivery_rate = 0.0
    read_rate = 0.0
    
    if total_messages > 0:
        # Taux de réussite = (envoyés + délivrés + lus) / total
        # Note: "sent" signifie que le message a été envoyé avec succès via l'API
        # "delivered" et "read" sont des confirmations supplémentaires via webhooks
        success_rate = (sent_count + delivered_count + read_count) / total_messages * 100
        delivery_rate = (delivered_count + read_count) / total_messages * 100
        read_rate = read_count / total_messages * 100
    
    logger.info(f"Stats globales calculées: total={total_messages}, sent={sent_count}, delivered={delivered_count}, read={read_count}, failed={failed_count}, pending={pending_count}")
    
    return MessageStats(
        total_messages=total_messages,
        sent_count=sent_count,
        delivered_count=delivered_count,
        read_count=read_count,
        failed_count=failed_count,
        pending_count=pending_count,
        success_rate=success_rate,
        delivery_rate=delivery_rate,
        read_rate=read_rate
    )


@router.get("/{message_id}", response_model=MessageWithContact)
async def get_message(
    message_id: int,
    db: SupabaseDB = Depends(get_supabase_db),
    current_user: Dict = Depends(get_current_user)
) -> MessageWithContact:
    """
    Récupère les détails d'un message spécifique.
    Accessible à tous les utilisateurs authentifiés (données partagées).
    Requirements: 5.2 - All users can access any message
    """
    message = db.get_message_by_id(message_id)
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message non trouvé"
        )
    
    # Récupérer les informations de la campagne (sans vérification d'appartenance)
    campaign = None
    if message.get("campaign_id"):
        campaign = db.get_campaign_by_id(message["campaign_id"])
    
    # Récupérer les informations du contact (sans vérification d'appartenance)
    contact = db.get_contact_by_id(message["contact_id"]) if message.get("contact_id") else None
    
    contact_name = None
    contact_info = None
    if contact:
        first_name = contact.get("first_name", "") or ""
        last_name = contact.get("last_name", "") or ""
        contact_name = f"{first_name} {last_name}".strip() or None
        contact_info = MessageContactInfo(
            id=contact["id"],
            phone_number=contact.get("phone_number", ""),
            full_number=contact.get("full_number", ""),
            first_name=contact.get("first_name"),
            last_name=contact.get("last_name")
        )
    
    campaign_info = None
    if campaign:
        campaign_info = MessageCampaignInfo(
            id=campaign["id"],
            name=campaign["name"]
        )
    
    return MessageWithContact(
        id=message["id"],
        campaign_id=message.get("campaign_id"),
        contact_id=message.get("contact_id"),
        message_type=message.get("message_type", "campaign"),
        content=message.get("content", ""),
        status=message.get("status", "pending"),
        whatsapp_message_id=message.get("whatsapp_message_id"),
        error_message=message.get("error_message"),
        retry_count=message.get("retry_count", 0),
        sent_at=message.get("sent_at"),
        delivered_at=message.get("delivered_at"),
        read_at=message.get("read_at"),
        created_at=message.get("created_at"),
        updated_at=message.get("updated_at"),
        contact_full_number=contact["full_number"] if contact else "",
        contact_name=contact_name,
        campaign_name=campaign["name"] if campaign else None,
        contact=contact_info,
        campaign=campaign_info
    )
