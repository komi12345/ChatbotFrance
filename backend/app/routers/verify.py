"""
Routes pour la vérification WhatsApp des contacts
Permet de vérifier si un numéro est enregistré sur WhatsApp via Wassenger API

Requirements: 3.1, 3.2, 6.1
"""
import logging
from datetime import datetime
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.supabase_client import SupabaseDB, get_supabase_db
from app.services.wassenger_service import WassengerService
from app.services.auth_service import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/verify", tags=["WhatsApp Verification"])


# ==================== SCHEMAS ====================

class WhatsAppVerificationResult(BaseModel):
    """Résultat de vérification WhatsApp pour un contact"""
    contact_id: int
    whatsapp_verified: bool | None
    verified_at: datetime | None
    error_message: str | None = None


class BulkVerificationRequest(BaseModel):
    """Requête de vérification en masse"""
    contact_ids: List[int]


class BulkVerificationResponse(BaseModel):
    """Réponse de vérification en masse"""
    queued_count: int
    message: str


class WhatsAppVerificationStats(BaseModel):
    """Statistiques de vérification WhatsApp - Requirements 5.1"""
    verified_count: int
    not_whatsapp_count: int
    pending_count: int
    total_count: int


# ==================== ENDPOINTS ====================

@router.get("/stats", response_model=WhatsAppVerificationStats)
async def get_verification_stats(
    db: SupabaseDB = Depends(get_supabase_db),
    current_user: Dict = Depends(get_current_user)
) -> WhatsAppVerificationStats:
    """
    Récupère les statistiques de vérification WhatsApp pour tous les contacts.
    
    Retourne:
    - verified_count: Nombre de contacts avec WhatsApp vérifié
    - not_whatsapp_count: Nombre de contacts sans WhatsApp
    - pending_count: Nombre de contacts non vérifiés
    - total_count: Nombre total de contacts
    
    Requirements: 1.2, 2.2 - Aggregated stats for all users
    """
    stats = db.get_whatsapp_verification_stats()
    
    return WhatsAppVerificationStats(
        verified_count=stats["verified_count"],
        not_whatsapp_count=stats["not_whatsapp_count"],
        pending_count=stats["pending_count"],
        total_count=stats["total_count"]
    )

@router.post("/{contact_id}", response_model=WhatsAppVerificationResult)
async def verify_contact(
    contact_id: int,
    db: SupabaseDB = Depends(get_supabase_db),
    current_user: Dict = Depends(get_current_user)
) -> WhatsAppVerificationResult:
    """
    Vérifie si le numéro d'un contact est enregistré sur WhatsApp.
    
    - Appelle l'API Wassenger pour vérifier l'existence du numéro
    - Met à jour le contact avec le résultat de la vérification
    - Retourne le résultat de la vérification
    
    Requirements: 1.1, 2.1 - Allow verification of any contact regardless of creator
    """
    # Récupérer le contact (partagé entre tous les utilisateurs)
    contact = db.get_contact_by_id(contact_id)
    
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact non trouvé"
        )
    
    # Initialiser le service Wassenger
    wassenger_service = WassengerService()
    
    # Vérifier le numéro via Wassenger API
    verification_result = await wassenger_service.check_whatsapp_exists(contact["full_number"])
    
    # Préparer les données de mise à jour
    verified_at = datetime.utcnow()
    
    # Déterminer le statut de vérification
    # Si erreur (error_code présent), on met whatsapp_verified à null
    # Sinon, on utilise le résultat de l'API
    if verification_result.error_code:
        whatsapp_verified = None
        error_message = verification_result.error_message
        logger.warning(
            f"Erreur lors de la vérification WhatsApp pour contact {contact_id}: "
            f"{verification_result.error_code} - {verification_result.error_message}"
        )
    else:
        whatsapp_verified = verification_result.exists
        error_message = None
        logger.info(
            f"Vérification WhatsApp réussie pour contact {contact_id}: "
            f"exists={verification_result.exists}"
        )
    
    # Mettre à jour le contact avec le résultat
    update_data = {
        "whatsapp_verified": whatsapp_verified,
        "verified_at": verified_at.isoformat()
    }
    
    db.update_contact(contact_id, update_data)
    
    return WhatsAppVerificationResult(
        contact_id=contact_id,
        whatsapp_verified=whatsapp_verified,
        verified_at=verified_at,
        error_message=error_message
    )


@router.post("/bulk", response_model=BulkVerificationResponse)
async def bulk_verify_contacts(
    request: BulkVerificationRequest,
    db: SupabaseDB = Depends(get_supabase_db),
    current_user: Dict = Depends(get_current_user)
) -> BulkVerificationResponse:
    """
    Met en file d'attente la vérification WhatsApp pour plusieurs contacts.
    
    - Valide que tous les contacts existent (partagés entre tous les utilisateurs)
    - Queue les vérifications avec des délais pour respecter les rate limits
    - Retourne le nombre de vérifications mises en file d'attente
    
    Requirements: 1.1, 2.1 - Allow verification of any contact regardless of creator
    """
    # Valider les contacts (partagés entre tous les utilisateurs)
    valid_contact_ids = []
    
    for contact_id in request.contact_ids:
        contact = db.get_contact_by_id(contact_id)
        if contact:
            valid_contact_ids.append(contact_id)
        else:
            logger.warning(f"Contact {contact_id} non trouvé")
    
    if not valid_contact_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Aucun contact valide trouvé dans la liste"
        )
    
    # Queue les vérifications via Celery (sera implémenté dans la tâche 5)
    # Pour l'instant, on retourne juste le nombre de contacts à vérifier
    # La tâche Celery bulk_verify_task sera appelée ici une fois implémentée
    
    # Import conditionnel pour éviter les erreurs si Celery n'est pas configuré
    try:
        from app.tasks.message_tasks import bulk_verify_task
        bulk_verify_task.delay(valid_contact_ids, current_user["id"])
        message = f"{len(valid_contact_ids)} vérifications mises en file d'attente"
    except ImportError:
        # Celery task not yet implemented
        message = f"{len(valid_contact_ids)} contacts prêts pour vérification (tâche Celery non implémentée)"
        logger.warning("bulk_verify_task not yet implemented in Celery")
    except Exception as e:
        logger.error(f"Erreur lors de la mise en file d'attente: {e}")
        message = f"{len(valid_contact_ids)} contacts identifiés, mais erreur lors de la mise en file d'attente"
    
    logger.info(f"Bulk verification queued: {len(valid_contact_ids)} contacts pour utilisateur {current_user['id']}")
    
    return BulkVerificationResponse(
        queued_count=len(valid_contact_ids),
        message=message
    )
