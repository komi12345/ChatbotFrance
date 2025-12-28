"""
Routes de métriques du cache - Statistiques de performance

Ce router fournit les endpoints pour :
- GET /api/cache/stats : Métriques du cache (hits, misses, hit_rate)

Tous les endpoints nécessitent une authentification JWT.

Requirements: 6.1
"""
import logging
from typing import Dict

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.services.auth_service import get_current_user
from app.services.cache_service import CacheService, get_cache_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cache", tags=["Cache"])


# ==================== SCHEMAS ====================

class CacheStatsResponse(BaseModel):
    """Réponse pour les statistiques du cache."""
    hits: int = Field(..., description="Nombre de cache hits")
    misses: int = Field(..., description="Nombre de cache misses")
    total: int = Field(..., description="Total des opérations de lecture")
    hit_rate: float = Field(..., description="Taux de hit en pourcentage (0-100)")


# ==================== ENDPOINTS ====================

@router.get("/stats", response_model=CacheStatsResponse)
async def get_cache_stats(
    current_user: Dict = Depends(get_current_user),
    cache_service: CacheService = Depends(get_cache_service)
) -> CacheStatsResponse:
    """
    Récupère les métriques de performance du cache.
    
    Retourne les compteurs de hits, misses et le taux de hit.
    Un taux de hit inférieur à 50% génère un warning dans les logs.
    
    Requirements: 6.1
    """
    logger.info(f"Récupération stats cache par utilisateur {current_user.get('id')}")
    
    metrics = cache_service.get_metrics()
    
    return CacheStatsResponse(
        hits=metrics["hits"],
        misses=metrics["misses"],
        total=metrics["total"],
        hit_rate=metrics["hit_rate"]
    )
