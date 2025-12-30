"""
Routes CRUD pour les catégories - Gestion des catégories de contacts
Utilise le client Supabase pour les opérations de base de données

Performance Optimization:
- Endpoints GET utilisent le cache Redis pour améliorer les temps de réponse
- Fallback automatique sur la DB si le cache est indisponible
- Invalidation du cache après mutations (create/update/delete)
- Requirements: 1.2, 1.4, 3.2, 3.4, 4.3, 5.2
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
from app.services.cache_service import (
    CacheService,
    get_cache_service,
    invalidate_cache_on_category_change,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/categories", tags=["Catégories"])


@router.get("")
async def list_categories(
    page: int = Query(1, ge=1, description="Numéro de page"),
    size: int = Query(50, ge=1, le=100, description="Nombre d'éléments par page"),
    search: Optional[str] = Query(None, description="Recherche par nom"),
    db: SupabaseDB = Depends(get_supabase_db),
    cache: CacheService = Depends(get_cache_service),
    current_user: Dict = Depends(get_current_user)
):
    """
    Liste toutes les catégories avec pagination (partagées entre tous les utilisateurs).
    
    Performance: Utilise le cache Redis avec TTL de 120s pour les listes sans recherche.
    Fallback automatique sur la DB si le cache est indisponible.
    
    Requirements: 
    - 1.2: Cache les comptages de contacts par catégorie avec TTL de 60s
    - 1.3, 2.3: All users see all categories regardless of creator
    - 3.2: Stratégie cache-aside (lecture cache, fallback DB)
    - 3.4: Mode dégradé si cache indisponible
    - 5.2: Inclure contact_count dans la requête principale (optimisé avec une seule requête)
    """
    skip = (page - 1) * size
    
    # Clé de cache pour la liste des catégories (uniquement si pas de recherche)
    cache_key = f"list:page_{page}:size_{size}" if not search else None
    
    # Essayer de récupérer depuis le cache d'abord (seulement si pas de recherche)
    if cache_key:
        cached_result = cache.get("categories", cache_key)
        if cached_result is not None:
            logger.debug(f"Categories list récupérée depuis le cache (page={page})")
            return cached_result
    
    # Fallback sur la DB
    logger.debug("Cache miss - récupération des catégories depuis la DB")
    categories, total = db.get_categories_paginated(
        skip=skip,
        limit=size,
        search=search
    )
    
    pages = (total + size - 1) // size if total > 0 else 1
    
    # Optimisation: récupérer tous les comptages en une seule requête
    # Requirements: 5.2 - Utiliser une seule requête avec COUNT au lieu de boucle
    category_ids = [cat["id"] for cat in categories]
    
    # Essayer de récupérer les comptages depuis le cache d'abord
    cached_counts = {}
    uncached_category_ids = []
    
    for cat_id in category_ids:
        count_cache_key = f"count:category:{cat_id}"
        cached_count = cache.get("contacts", count_cache_key)
        if cached_count is not None:
            cached_counts[cat_id] = cached_count
        else:
            uncached_category_ids.append(cat_id)
    
    # Récupérer les comptages manquants en une seule requête
    if uncached_category_ids:
        db_counts = db.get_categories_contact_counts(uncached_category_ids)
        # Mettre en cache les comptages récupérés
        for cat_id, count in db_counts.items():
            count_cache_key = f"count:category:{cat_id}"
            cache.set("contacts", count_cache_key, count, CacheService.CONTACTS_COUNT_TTL)
            cached_counts[cat_id] = count
    
    # Construire la liste des catégories avec les comptages
    items = []
    for cat in categories:
        contact_count = cached_counts.get(cat["id"], 0)
        items.append(CategoryResponse(
            id=cat["id"],
            name=cat["name"],
            color=cat.get("color"),
            created_by=cat["created_by"],
            created_at=cat.get("created_at"),
            updated_at=cat.get("updated_at"),
            contact_count=contact_count
        ))
    
    result = {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }
    
    # Mettre en cache le résultat (seulement si pas de recherche)
    if cache_key:
        # Convertir les items en dict pour la sérialisation JSON
        cache_result = {
            "items": [item.model_dump() for item in items],
            "total": total,
            "page": page,
            "size": size,
            "pages": pages
        }
        cache.set("categories", cache_key, cache_result, CacheService.CATEGORIES_TTL)
    
    return result


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: CategoryCreate,
    db: SupabaseDB = Depends(get_supabase_db),
    cache: CacheService = Depends(get_cache_service),
    current_user: Dict = Depends(get_current_user)
) -> CategoryResponse:
    """
    Crée une nouvelle catégorie (accessible à tout utilisateur authentifié).
    
    Invalidation du cache après création.
    
    Requirements: 
    - 1.3, 2.3: Any authenticated user can create categories
    - 1.4, 4.3: Invalider le cache des catégories après création
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
    
    # Invalider le cache des catégories après création
    invalidate_cache_on_category_change()
    
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
    cache: CacheService = Depends(get_cache_service),
    current_user: Dict = Depends(get_current_user)
) -> CategoryWithContacts:
    """
    Récupère les détails d'une catégorie avec ses contacts (accessible à tout utilisateur).
    
    Performance: Utilise le cache Redis avec TTL de 120s pour les détails de catégorie.
    Fallback automatique sur la DB si le cache est indisponible.
    
    Requirements: 
    - 1.2: Cache les détails de catégorie avec TTL de 120s
    - 1.3, 2.3: Any authenticated user can access any category
    - 3.2: Stratégie cache-aside (lecture cache, fallback DB)
    - 3.4: Mode dégradé si cache indisponible
    """
    # Clé de cache pour les détails de catégorie
    cache_key = f"detail:{category_id}"
    
    # Essayer de récupérer depuis le cache d'abord
    cached_result = cache.get("categories", cache_key)
    if cached_result is not None:
        logger.debug(f"Category detail récupérée depuis le cache (id={category_id})")
        return CategoryWithContacts(**cached_result)
    
    # Fallback sur la DB
    logger.debug(f"Cache miss - récupération de la catégorie {category_id} depuis la DB")
    category = db.get_category_by_id(category_id)
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Catégorie non trouvée"
        )
    
    # Récupérer les contacts de la catégorie (tous les contacts, partagés)
    contacts = db.get_contacts_by_category(category_id)
    
    result = CategoryWithContacts(
        id=category["id"],
        name=category["name"],
        color=category.get("color"),
        created_by=category["created_by"],
        created_at=category.get("created_at"),
        updated_at=category.get("updated_at"),
        contact_count=len(contacts),
        contacts=contacts
    )
    
    # Mettre en cache le résultat (TTL 120s)
    cache.set("categories", cache_key, result.model_dump(), CacheService.CATEGORIES_TTL)
    
    return result


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    db: SupabaseDB = Depends(get_supabase_db),
    cache: CacheService = Depends(get_cache_service),
    current_user: Dict = Depends(get_current_user)
) -> CategoryResponse:
    """
    Met à jour une catégorie existante (accessible à tout utilisateur authentifié).
    
    Invalidation du cache après mise à jour.
    
    Requirements: 
    - 1.3, 2.3: Any authenticated user can update any category
    - 1.4, 4.3: Invalider le cache des catégories après modification
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
    
    # Invalider le cache de cette catégorie et la liste des catégories
    invalidate_cache_on_category_change(category_id)
    
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
    cache: CacheService = Depends(get_cache_service),
    current_user: Dict = Depends(get_current_user)
):
    """
    Supprime une catégorie (accessible à tout utilisateur authentifié).
    
    Invalidation du cache après suppression.
    
    Requirements: 
    - 1.3, 2.3: Any authenticated user can delete any category
    - 1.4, 4.3: Invalider le cache des catégories après suppression
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
    
    # Invalider le cache de cette catégorie et la liste des catégories
    invalidate_cache_on_category_change(category_id)
    
    return None


class AddContactsRequest(BaseModel):
    """Schéma pour ajouter des contacts à une catégorie"""
    contact_ids: List[int] = Field(..., min_length=1, description="Liste des IDs de contacts à ajouter")


@router.post("/{category_id}/contacts", response_model=CategoryWithContacts)
async def add_contacts_to_category(
    category_id: int,
    request: AddContactsRequest,
    db: SupabaseDB = Depends(get_supabase_db),
    cache: CacheService = Depends(get_cache_service),
    current_user: Dict = Depends(get_current_user)
) -> CategoryWithContacts:
    """
    Ajoute des contacts à une catégorie (accessible à tout utilisateur authentifié).
    
    Invalidation du cache après ajout de contacts.
    
    Requirements: 
    - 1.3, 2.3: Any authenticated user can manage category contacts
    - 1.4, 4.3: Invalider le cache des catégories après modification
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
    
    # Invalider le cache de cette catégorie (comptage et détails)
    invalidate_cache_on_category_change(category_id)
    
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
    cache: CacheService = Depends(get_cache_service),
    current_user: Dict = Depends(get_current_user)
):
    """
    Retire un contact d'une catégorie (accessible à tout utilisateur authentifié).
    
    Invalidation du cache après retrait de contact.
    
    Requirements: 
    - 1.3, 2.3: Any authenticated user can manage category contacts
    - 1.4, 4.3: Invalider le cache des catégories après modification
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
    
    # Invalider le cache de cette catégorie (comptage et détails)
    invalidate_cache_on_category_change(category_id)
    
    return None


@router.get("/{category_id}/available-contacts")
async def get_available_contacts_for_category(
    category_id: int,
    page: int = Query(1, ge=1, description="Numéro de page"),
    size: int = Query(50, ge=1, le=500, description="Nombre d'éléments par page (max 500)"),
    search: Optional[str] = Query(None, description="Recherche par nom ou numéro"),
    db: SupabaseDB = Depends(get_supabase_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Récupère les contacts qui ne sont PAS dans une catégorie donnée.
    Avec pagination et recherche côté serveur.
    
    Retourne uniquement les contacts disponibles pour être ajoutés à cette catégorie.
    """
    # Vérifier que la catégorie existe
    category = db.get_category_by_id(category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Catégorie non trouvée"
        )
    
    skip = (page - 1) * size
    
    # Récupérer les contacts qui ne sont pas dans cette catégorie
    contacts, total = db.get_contacts_not_in_category(
        category_id=category_id,
        skip=skip,
        limit=size,
        search=search
    )
    
    pages = (total + size - 1) // size if total > 0 else 1
    
    return {
        "items": contacts,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }
