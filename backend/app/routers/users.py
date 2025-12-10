"""
Routes de gestion des utilisateurs - Accessible uniquement aux Super Admins
Utilise le client Supabase pour les opérations de base de données
"""
import logging
from typing import List, Optional, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.supabase_client import SupabaseDB, get_supabase_db
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
)
from app.services.auth_service import get_current_super_admin
from app.utils.security import hash_password

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["Utilisateurs (Super Admin)"])


def user_to_response(user: Dict) -> UserResponse:
    """Convertit un dict utilisateur en UserResponse"""
    return UserResponse(
        id=user["id"],
        email=user["email"],
        role=user["role"],
        is_active=user.get("is_active", True),
        created_at=user.get("created_at"),
        updated_at=user.get("updated_at")
    )


@router.get("", response_model=List[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(50, ge=1, le=100, description="Nombre maximum d'éléments"),
    search: Optional[str] = Query(None, description="Recherche par email"),
    role: Optional[str] = Query(None, pattern="^(super_admin|admin)$", description="Filtrer par rôle"),
    is_active: Optional[bool] = Query(None, description="Filtrer par statut actif"),
    db: SupabaseDB = Depends(get_supabase_db),
    current_user: Dict = Depends(get_current_super_admin)
) -> List[UserResponse]:
    """
    Liste tous les utilisateurs (Super Admin uniquement).
    """
    users = db.get_users(skip=skip, limit=limit, search=search)
    
    # Filtrer par rôle et statut actif si nécessaire
    if role:
        users = [u for u in users if u.get("role") == role]
    if is_active is not None:
        users = [u for u in users if u.get("is_active", True) == is_active]
    
    return [user_to_response(u) for u in users]


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: SupabaseDB = Depends(get_supabase_db),
    current_user: Dict = Depends(get_current_super_admin)
) -> UserResponse:
    """
    Crée un nouvel utilisateur Admin (Super Admin uniquement).
    """
    # Vérifier si un utilisateur avec cet email existe déjà
    existing = db.get_user_by_email(user_data.email)
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Un utilisateur avec l'email '{user_data.email}' existe déjà"
        )
    
    # Hasher le mot de passe avec bcrypt
    password_hash = hash_password(user_data.password)
    
    # Créer l'utilisateur
    user = db.create_user({
        "email": user_data.email,
        "password_hash": password_hash,
        "role": user_data.role,
        "is_active": True
    })
    
    logger.info(f"Utilisateur créé: {user['email']} (ID: {user['id']}, rôle: {user['role']}) par Super Admin {current_user['id']}")
    
    return user_to_response(user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: SupabaseDB = Depends(get_supabase_db),
    current_user: Dict = Depends(get_current_super_admin)
) -> UserResponse:
    """
    Récupère les détails d'un utilisateur (Super Admin uniquement).
    """
    user = db.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )
    
    return user_to_response(user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: SupabaseDB = Depends(get_supabase_db),
    current_user: Dict = Depends(get_current_super_admin)
) -> UserResponse:
    """
    Met à jour un utilisateur existant (Super Admin uniquement).
    """
    user = db.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )
    
    # Empêcher la modification de son propre compte via cette route
    if user["id"] == current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Utilisez la route /api/auth/me pour modifier votre propre compte"
        )
    
    # Vérifier si le nouvel email existe déjà
    if user_data.email and user_data.email != user["email"]:
        existing = db.get_user_by_email(user_data.email)
        if existing and existing["id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Un utilisateur avec l'email '{user_data.email}' existe déjà"
            )
    
    # Préparer les données de mise à jour
    update_data = {}
    
    if user_data.email is not None:
        update_data["email"] = user_data.email
    
    if user_data.password is not None:
        update_data["password_hash"] = hash_password(user_data.password)
    
    if user_data.is_active is not None:
        update_data["is_active"] = user_data.is_active
    
    if update_data:
        user = db.update_user(user_id, update_data)
    
    logger.info(f"Utilisateur mis à jour: {user['email']} (ID: {user['id']}) par Super Admin {current_user['id']}")
    
    return user_to_response(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: SupabaseDB = Depends(get_supabase_db),
    current_user: Dict = Depends(get_current_super_admin)
):
    """
    Supprime un utilisateur (Super Admin uniquement).
    """
    user = db.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )
    
    # Empêcher la suppression de son propre compte
    if user["id"] == current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vous ne pouvez pas supprimer votre propre compte"
        )
    
    user_email = user["email"]
    db.delete_user(user_id)
    
    logger.info(f"Utilisateur supprimé: {user_email} (ID: {user_id}) par Super Admin {current_user['id']}")
    
    return None
