"""
Routes de monitoring WhatsApp - Statistiques temps réel et historique

Ce router fournit les endpoints pour :
- GET /api/monitoring/stats : Statistiques temps réel
- GET /api/monitoring/history : Historique des 7 derniers jours
- GET /api/monitoring/errors : Dernières erreurs

Tous les endpoints nécessitent une authentification JWT.

Requirements: 1.5, 4.1, 4.2, 4.3, 4.4, 6.3, 8.4
"""
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.services.auth_service import get_current_user
from app.services.monitoring_service import (
    MonitoringService,
    AlertLevel,
    DAILY_MESSAGE_LIMIT,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])

# Instance globale du service de monitoring
_monitoring_service: Optional[MonitoringService] = None


def get_monitoring_service() -> MonitoringService:
    """Retourne l'instance singleton du service de monitoring."""
    global _monitoring_service
    if _monitoring_service is None:
        _monitoring_service = MonitoringService()
    return _monitoring_service


# ==================== SCHEMAS ====================

class MonitoringStatsResponse(BaseModel):
    """Réponse pour les statistiques temps réel."""
    message_1_count: int = Field(..., description="Nombre de messages de type 1 envoyés")
    message_2_count: int = Field(..., description="Nombre de messages de type 2 envoyés")
    total_sent: int = Field(..., description="Total des messages envoyés")
    error_count: int = Field(..., description="Nombre d'erreurs")
    daily_limit: int = Field(..., description="Limite quotidienne (1000)")
    remaining: int = Field(..., description="Messages restants avant limite")
    alert_level: str = Field(..., description="Niveau d'alerte (ok, attention, danger, blocked)")
    interaction_rate: float = Field(..., description="Taux d'interaction (message_2/message_1)")
    remaining_capacity: int = Field(..., description="Capacité restante en contacts")
    is_blocked: bool = Field(..., description="True si limite atteinte")
    error_rate_warning: bool = Field(..., description="True si taux d'erreur > 10%")
    last_sync: Optional[str] = Field(None, description="Timestamp dernière synchronisation")


class DailyHistoryItem(BaseModel):
    """Élément d'historique quotidien."""
    date: str = Field(..., description="Date (YYYY-MM-DD)")
    message_1: int = Field(..., description="Messages de type 1")
    message_2: int = Field(..., description="Messages de type 2")
    errors: int = Field(..., description="Nombre d'erreurs")


class RecentErrorItem(BaseModel):
    """Élément d'erreur récente."""
    timestamp: str = Field(..., description="Timestamp de l'erreur")
    message_id: Optional[int] = Field(None, description="ID du message concerné")
    error: str = Field(..., description="Message d'erreur")


# ==================== ENDPOINTS ====================

@router.get("/stats", response_model=MonitoringStatsResponse)
async def get_monitoring_stats(
    current_user: Dict = Depends(get_current_user),
    monitoring_service: MonitoringService = Depends(get_monitoring_service)
) -> MonitoringStatsResponse:
    """
    Récupère les statistiques de monitoring temps réel.
    
    Retourne les compteurs actuels, le niveau d'alerte, et la capacité restante.
    
    Requirements: 1.5, 4.1, 4.2, 4.3, 8.4
    """
    logger.info(f"Récupération stats monitoring par utilisateur {current_user.get('id')}")
    
    # Récupérer les statistiques du jour
    stats = monitoring_service.get_daily_stats()
    
    # Calculer les métriques dérivées
    alert_level = monitoring_service.get_alert_level()
    interaction_rate = monitoring_service.calculate_interaction_rate()
    remaining_capacity = monitoring_service.calculate_remaining_capacity()
    can_send, _ = monitoring_service.can_send_message()
    error_rate_warning = monitoring_service.get_error_rate_warning()
    
    return MonitoringStatsResponse(
        message_1_count=stats.message_1_count,
        message_2_count=stats.message_2_count,
        total_sent=stats.total_sent,
        error_count=stats.error_count,
        daily_limit=DAILY_MESSAGE_LIMIT,
        remaining=max(0, DAILY_MESSAGE_LIMIT - stats.total_sent),
        alert_level=alert_level.value,
        interaction_rate=round(interaction_rate, 3),
        remaining_capacity=remaining_capacity,
        is_blocked=not can_send,
        error_rate_warning=error_rate_warning,
        last_sync=datetime.now(timezone.utc).isoformat()
    )


@router.get("/history", response_model=List[DailyHistoryItem])
async def get_monitoring_history(
    days: int = Query(7, ge=1, le=30, description="Nombre de jours d'historique"),
    current_user: Dict = Depends(get_current_user),
    monitoring_service: MonitoringService = Depends(get_monitoring_service)
) -> List[DailyHistoryItem]:
    """
    Récupère l'historique des statistiques sur les derniers jours.
    
    Note: Pour l'instant, retourne uniquement les stats du jour actuel depuis Redis.
    L'historique complet sera disponible après l'implémentation de la persistance Supabase.
    
    Requirements: 4.4, 8.4
    """
    logger.info(f"Récupération historique {days} jours par utilisateur {current_user.get('id')}")
    
    # Pour l'instant, on retourne uniquement les stats du jour depuis Redis
    # L'historique complet sera implémenté dans la Phase 4 (Persistance Supabase)
    stats = monitoring_service.get_daily_stats()
    
    return [
        DailyHistoryItem(
            date=stats.date,
            message_1=stats.message_1_count,
            message_2=stats.message_2_count,
            errors=stats.error_count
        )
    ]


@router.get("/errors", response_model=List[RecentErrorItem])
async def get_monitoring_errors(
    limit: int = Query(10, ge=1, le=50, description="Nombre d'erreurs à retourner"),
    current_user: Dict = Depends(get_current_user),
    monitoring_service: MonitoringService = Depends(get_monitoring_service)
) -> List[RecentErrorItem]:
    """
    Récupère les dernières erreurs d'envoi de messages.
    
    Note: Pour l'instant, retourne une liste vide.
    Les erreurs détaillées seront disponibles après l'implémentation de la persistance Supabase.
    
    Requirements: 6.3, 8.4
    """
    logger.info(f"Récupération {limit} dernières erreurs par utilisateur {current_user.get('id')}")
    
    # Pour l'instant, on retourne une liste vide
    # Les erreurs détaillées seront implémentées dans la Phase 4 (Persistance Supabase)
    # avec la table message_errors
    return []


class SystemStatusResponse(BaseModel):
    """Réponse pour le statut système."""
    status: str = Field(..., description="Statut global (healthy, degraded, critical)")
    redis_connected: bool = Field(..., description="Connexion Redis active")
    supabase_connected: bool = Field(..., description="Connexion Supabase active")
    celery_workers: int = Field(..., description="Nombre de workers Celery actifs")
    active_campaigns: int = Field(..., description="Nombre de campagnes en cours")
    active_locks: int = Field(..., description="Nombre de verrous actifs")
    daily_quota_used: int = Field(..., description="Quota quotidien utilisé")
    daily_quota_remaining: int = Field(..., description="Quota quotidien restant")
    can_send_messages: bool = Field(..., description="Envoi de messages autorisé")
    timestamp: str = Field(..., description="Timestamp du statut")


@router.get("/system-status", response_model=SystemStatusResponse)
async def get_system_status(
    current_user: Dict = Depends(get_current_user),
    monitoring_service: MonitoringService = Depends(get_monitoring_service)
) -> SystemStatusResponse:
    """
    Récupère le statut complet du système pour le déploiement en production.
    
    Vérifie:
    - Connexion Redis
    - Connexion Supabase
    - Workers Celery
    - Campagnes actives
    - Verrous distribués
    - Quota quotidien
    
    Requirements: Production monitoring
    """
    logger.info(f"Vérification statut système par utilisateur {current_user.get('id')}")
    
    # Vérifier Redis
    redis_connected = False
    active_locks = 0
    try:
        monitoring_service.redis_client.ping()
        redis_connected = True
        # Compter les verrous actifs
        lock_keys = list(monitoring_service.redis_client.scan_iter(match="campaign:lock:*"))
        active_locks = len(lock_keys)
    except Exception as e:
        logger.error(f"Erreur connexion Redis: {e}")
    
    # Vérifier Supabase
    supabase_connected = False
    active_campaigns = 0
    try:
        from app.supabase_client import get_supabase_db
        db = get_supabase_db()
        # Test simple de connexion
        campaigns, _ = db.get_campaigns(limit=1, status="sending")
        supabase_connected = True
        # Compter les campagnes en cours
        _, active_campaigns = db.get_campaigns(status="sending")
    except Exception as e:
        logger.error(f"Erreur connexion Supabase: {e}")
    
    # Vérifier Celery (via Redis)
    celery_workers = 0
    try:
        from app.tasks.celery_app import celery_app
        inspect = celery_app.control.inspect()
        active = inspect.active()
        if active:
            celery_workers = len(active)
    except Exception as e:
        logger.warning(f"Impossible de vérifier les workers Celery: {e}")
    
    # Quota quotidien
    stats = monitoring_service.get_daily_stats()
    can_send, _ = monitoring_service.can_send_message()
    
    # Déterminer le statut global
    if not redis_connected or not supabase_connected:
        status = "critical"
    elif celery_workers == 0 or not can_send:
        status = "degraded"
    else:
        status = "healthy"
    
    return SystemStatusResponse(
        status=status,
        redis_connected=redis_connected,
        supabase_connected=supabase_connected,
        celery_workers=celery_workers,
        active_campaigns=active_campaigns,
        active_locks=active_locks,
        daily_quota_used=stats.total_sent,
        daily_quota_remaining=max(0, DAILY_MESSAGE_LIMIT - stats.total_sent),
        can_send_messages=can_send,
        timestamp=datetime.now(timezone.utc).isoformat()
    )


class CampaignLockInfo(BaseModel):
    """Information sur un verrou de campagne."""
    campaign_id: int
    user_id: int
    locked_at: str
    ttl: int


@router.get("/locks", response_model=List[CampaignLockInfo])
async def get_active_locks(
    current_user: Dict = Depends(get_current_user),
    monitoring_service: MonitoringService = Depends(get_monitoring_service)
) -> List[CampaignLockInfo]:
    """
    Récupère la liste des verrous de campagne actifs.
    
    Utile pour diagnostiquer les problèmes de campagnes bloquées.
    
    Requirements: Production monitoring
    """
    logger.info(f"Récupération verrous actifs par utilisateur {current_user.get('id')}")
    
    locks = []
    try:
        lock_keys = list(monitoring_service.redis_client.scan_iter(match="campaign:lock:*"))
        
        for key in lock_keys:
            # Extraire l'ID de campagne du nom de clé
            campaign_id = int(key.split(":")[-1])
            lock_info = monitoring_service.get_campaign_lock_info(campaign_id)
            
            if lock_info:
                locks.append(CampaignLockInfo(
                    campaign_id=campaign_id,
                    user_id=lock_info["user_id"],
                    locked_at=lock_info["locked_at"],
                    ttl=lock_info["ttl"]
                ))
    except Exception as e:
        logger.error(f"Erreur récupération verrous: {e}")
    
    return locks
