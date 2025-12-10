"""
Routes CRUD pour les catégories - Gestion des catégories de contacts
Utilise le client Supabase pour les opérations de base de données
"""
import logging
from typing import List, Optional, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.supabase_client import SupabaseDB, get_supabase_db
from app.schemas.category import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    CategoryWithContacts,
)
from app.services.auth_service import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/categories", tags=["Catégories"])


@router.get("")
async def list_categories(
    page: int = Query(1, ge=1, description="Numéro de page"),
    size: int = Query(50, ge=1, le=100, description="Nombre d'éléments par page"),
    search: Optional[str] = Query(None, description="Recherche par nom"),
    db: SupabaseDB = Depends(get_supabase_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Liste toutes les catégories avec pagination (partagées entre tous les utilisateurs).
    Requirements: 1.3, 2.3 - All users see all categories regardless of creator
    """
    skip = (page - 1) * size
    categories, total = db.get_categories_paginated(
        skip=skip,
        limit=size,
        search=search
    )
    
    pages = (total + size - 1) // size if total > 0 else 1
    
    # Ajouter le contact_count pour chaque catégorie
    items = []
    for cat in categories:
        contact_count = db.get_category_contact_count(cat["id"])
        items.append(CategoryResponse(
            id=cat["id"],
            name=cat["name"],
            color=cat.get("color"),
            created_by=cat["created_by"],
            created_at=cat.get("created_at"),
            updated_at=cat.get("updated_at"),
            contact_count=contact_count
        ))
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: CategoryCreate,
    db: SupabaseDB = Depends(get_supabase_db),
    current_user: Dict = Depends(get_current_user)
) -> CategoryResponse:
    """
    Crée une nouvelle catégorie (accessible à tout utilisateur authentifié).
    Requirements: 1.3, 2.3 - Any authenticated user can create categories
    """
    # Vérifier si une catégorie avec ce nom existe déjà (recherche globale)
    existing = db.get_category_by_name(category_data.name)
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Une catégorie avec le nom '{category_data.name}' existe déjà"
        )
    
    # Créer la catégorie
    category = db.create_category({
        "name": category_data.name,
        "color": category_data.color,
        "created_by": current_user["id"]
    })
    
    logger.info(f"Catégorie créée: {category['name']} (ID: {category['id']}) par utilisateur {current_user['id']}")
    
    return CategoryResponse(
        id=category["id"],
        name=category["name"],
        color=category.get("color"),
        created_by=category["created_by"],
        created_at=category.get("created_at"),
        updated_at=category.get("updated_at"),
        contact_count=0
    )


@router.get("/{category_id}", response_model=CategoryWithContacts)
async def get_category(
    category_id: int,
    db: SupabaseDB = Depends(get_supabase_db),
    current_user: Dict = Depends(get_current_user)
) -> CategoryWithContacts:
    """
    Récupère les détails d'une catégorie avec ses contacts (accessible à tout utilisateur).
    Requirements: 1.3, 2.3 - Any authenticated user can access any category
    """
    category = db.get_category_by_id(category_id)
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Catégorie non trouvée"
        )
    
    # Récupérer les contacts de la catégorie (tous les contacts, partagés)
    contacts = db.get_contacts_by_category(category_id)
    
    return CategoryWithContacts(
        id=category["id"],
        name=category["name"],
        color=category.get("color"),
        created_by=category["created_by"],
        created_at=category.get("created_at"),
        updated_at=category.get("updated_at"),
        contact_count=len(contacts),
        contacts=contacts
    )


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    db: SupabaseDB = Depends(get_supabase_db),
    current_user: Dict = Depends(get_current_user)
) -> CategoryResponse:
    """
    Met à jour une catégorie existante (accessible à tout utilisateur authentifié).
    Requirements: 1.3, 2.3 - Any authenticated user can update any category
    """
    category = db.get_category_by_id(category_id)
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Catégorie non trouvée"
        )
    
    # Vérifier si le nouveau nom existe déjà (recherche globale)
    if category_data.name and category_data.name != category["name"]:
        existing = db.get_category_by_name(category_data.name)
        if existing and existing["id"] != category_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Une catégorie avec le nom '{category_data.name}' existe déjà"
            )
    
    # Préparer les données de mise à jour
    update_data = {}
    if category_data.name is not None:
        update_data["name"] = category_data.name
    if category_data.color is not None:
        update_data["color"] = category_data.color
    
    if update_data:
        category = db.update_category(category_id, update_data)
    
    logger.info(f"Catégorie mise à jour: {category['name']} (ID: {category['id']})")
    
    contact_count = db.get_category_contact_count(category_id)
    
    return CategoryResponse(
        id=category["id"],
        name=category["name"],
        color=category.get("color"),
        created_by=category["created_by"],
        created_at=category.get("created_at"),
        updated_at=category.get("updated_at"),
        contact_count=contact_count
    )


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    db: SupabaseDB = Depends(get_supabase_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Supprime une catégorie (accessible à tout utilisateur authentifié).
    Requirements: 1.3, 2.3 - Any authenticated user can delete any category
    """
    category = db.get_category_by_id(category_id)
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Catégorie non trouvée"
        )
    
    category_name = category["name"]
    db.delete_category(category_id)
    
    logger.info(f"Catégorie supprimée: {category_name} (ID: {category_id}) par utilisateur {current_user['id']}")
    
    return None


class AddContactsRequest(BaseModel):
    """Schéma pour ajouter des contacts à une catégorie"""
    contact_ids: List[int] = Field(..., min_length=1, description="Liste des IDs de contacts à ajouter")


@router.post("/{category_id}/contacts", response_model=CategoryWithContacts)
async def add_contacts_to_category(
    category_id: int,
    request: AddContactsRequest,
    db: SupabaseDB = Depends(get_supabase_db),
    current_user: Dict = Depends(get_current_user)
) -> CategoryWithContacts:
    """
    Ajoute des contacts à une catégorie (accessible à tout utilisateur authentifié).
    Requirements: 1.3, 2.3 - Any authenticated user can manage category contacts
    """
    category = db.get_category_by_id(category_id)
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Catégorie non trouvée"
        )
    
    # Vérifier que tous les contacts existent (recherche globale)
    for contact_id in request.contact_ids:
        contact = db.get_contact_by_id(contact_id)
        if not contact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Contact {contact_id} non trouvé"
            )
        db.add_contact_to_category(contact_id, category_id)
    
    # Récupérer les contacts mis à jour (tous les contacts de la catégorie)
    contacts = db.get_contacts_by_category(category_id)
    
    logger.info(f"{len(request.contact_ids)} contact(s) ajouté(s) à la catégorie {category['name']} (ID: {category_id})")
    
    return CategoryWithContacts(
        id=category["id"],
        name=category["name"],
        color=category.get("color"),
        created_by=category["created_by"],
        created_at=category.get("created_at"),
        updated_at=category.get("updated_at"),
        contact_count=len(contacts),
        contacts=contacts
    )


@router.delete("/{category_id}/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_contact_from_category(
    category_id: int,
    contact_id: int,
    db: SupabaseDB = Depends(get_supabase_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Retire un contact d'une catégorie (accessible à tout utilisateur authentifié).
    Requirements: 1.3, 2.3 - Any authenticated user can manage category contacts
    """
    category = db.get_category_by_id(category_id)
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Catégorie non trouvée"
        )
    
    contact = db.get_contact_by_id(contact_id)
    
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact non trouvé"
        )
    
    db.remove_contact_from_category(contact_id, category_id)
    
    logger.info(f"Contact {contact_id} retiré de la catégorie {category['name']} (ID: {category_id})")
    
    return None
