"""
Routes CRUD pour les contacts - Gestion des contacts WhatsApp
Utilise le client Supabase pour les opérations de base de données

Requirements: 1.3, 4.1, 4.2 - Cache invalidation après mutations
"""
import csv
import io
import logging
from typing import List, Optional, Dict, Literal

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse

from app.supabase_client import SupabaseDB, get_supabase_db
from app.schemas.contact import (
    ContactCreate,
    ContactUpdate,
    ContactResponse,
    ContactWithCategories,
    ContactImportResult,
)
from app.services.auth_service import get_current_user
from app.services.cache_service import invalidate_cache_on_contact_change
from app.utils.validators import (
    validate_full_phone_number,
    clean_phone_number,
)
from app.utils.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from app.tasks.message_tasks import verify_whatsapp_task

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/contacts", tags=["Contacts"])


def contact_to_response(contact: Dict, categories: List[Dict] = None) -> ContactWithCategories:
    """Convertit un dict contact en ContactWithCategories"""
    return ContactWithCategories(
        id=contact["id"],
        phone_number=contact["phone_number"],
        country_code=contact["country_code"],
        full_number=contact["full_number"],
        first_name=contact.get("first_name"),
        last_name=contact.get("last_name"),
        created_by=contact["created_by"],
        created_at=contact.get("created_at"),
        updated_at=contact.get("updated_at"),
        whatsapp_verified=contact.get("whatsapp_verified"),
        verified_at=contact.get("verified_at"),
        categories=categories or []
    )


@router.get("")
async def list_contacts(
    page: int = Query(1, ge=1, description="Numéro de page"),
    size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="Nombre d'éléments par page"),
    search: Optional[str] = Query(None, description="Recherche par nom ou numéro"),
    category_id: Optional[int] = Query(None, description="Filtrer par catégorie"),
    whatsapp_status: Optional[Literal["all", "verified", "not_whatsapp", "pending"]] = Query(
        None, 
        description="Filtrer par statut WhatsApp: all (tous), verified (WhatsApp vérifié), not_whatsapp (non-WhatsApp), pending (non vérifié)"
    ),
    db: SupabaseDB = Depends(get_supabase_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Liste tous les contacts de l'utilisateur avec pagination et recherche.
    
    Filtres disponibles:
    - search: Recherche par nom ou numéro
    - category_id: Filtrer par catégorie
    - whatsapp_status: Filtrer par statut WhatsApp (all, verified, not_whatsapp, pending)
    
    Requirements: 4.1, 4.2
    """
    skip = (page - 1) * size
    
    # Convert "all" to None for the database query (no filter)
    db_whatsapp_status = None if whatsapp_status == "all" else whatsapp_status
    
    # Requirements: 1.1, 2.1 - All users see all contacts
    contacts, total = db.get_contacts_paginated(
        skip=skip,
        limit=size,
        search=search,
        category_id=category_id,
        whatsapp_status=db_whatsapp_status
    )
    
    pages = (total + size - 1) // size if total > 0 else 1
    
    # Ajouter les catégories pour chaque contact
    items = []
    for contact in contacts:
        categories = db.get_contact_categories(contact["id"])
        items.append(contact_to_response(contact, categories))
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }


@router.post("", response_model=ContactWithCategories, status_code=status.HTTP_201_CREATED)
async def create_contact(
    contact_data: ContactCreate,
    db: SupabaseDB = Depends(get_supabase_db),
    current_user: Dict = Depends(get_current_user)
) -> ContactWithCategories:
    """
    Crée un nouveau contact avec validation du numéro.
    
    Après la création, une tâche de vérification WhatsApp est automatiquement
    mise en file d'attente. La création du contact n'est pas bloquée par
    le résultat de la vérification.
    
    Requirements: 1.1, 1.4
    """
    # Valider le numéro complet
    is_valid, error_msg, full_number = validate_full_phone_number(
        contact_data.country_code,
        contact_data.phone_number
    )
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Vérifier si le numéro existe déjà (vérification globale)
    # Requirements: 3.1, 3.3 - Global phone number uniqueness
    existing = db.get_contact_by_full_number_global(full_number)
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Un contact avec le numéro '{full_number}' existe déjà"
        )
    
    # Nettoyer le numéro de téléphone
    cleaned_phone = clean_phone_number(contact_data.phone_number)
    
    # Créer le contact
    contact = db.create_contact({
        "phone_number": cleaned_phone,
        "country_code": contact_data.country_code,
        "full_number": full_number,
        "first_name": contact_data.first_name,
        "last_name": contact_data.last_name,
        "created_by": current_user["id"]
    })
    
    # Ajouter les catégories si spécifiées
    categories = []
    if contact_data.category_ids:
        for cat_id in contact_data.category_ids:
            category = db.get_category_by_id(cat_id, current_user["id"])
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Catégorie {cat_id} non trouvée"
                )
            db.add_contact_to_category(contact["id"], cat_id)
            categories.append(category)
    
    logger.info(f"Contact créé: {contact['full_number']} (ID: {contact['id']}) par utilisateur {current_user['id']}")
    
    # Invalider le cache des stats et catégories associées
    # Requirements: 1.3, 4.1 - Invalidation après création de contact
    category_ids_list = [cat["id"] for cat in categories] if categories else None
    invalidate_cache_on_contact_change(category_ids_list)
    
    # Queue WhatsApp verification task asynchronously
    # Requirements: 1.1 - Automatically trigger verification on contact creation
    # Requirements: 1.4 - Do not block contact creation on verification result
    try:
        verify_whatsapp_task.delay(contact["id"])
        logger.info(f"Vérification WhatsApp mise en file d'attente pour contact {contact['id']}")
    except Exception as e:
        # Log the error but don't fail the contact creation
        # Requirements: 1.4 - Contact creation must succeed regardless of verification
        logger.warning(f"Impossible de mettre en file d'attente la vérification WhatsApp pour contact {contact['id']}: {e}")
    
    return contact_to_response(contact, categories)


@router.get("/{contact_id}", response_model=ContactWithCategories)
async def get_contact(
    contact_id: int,
    db: SupabaseDB = Depends(get_supabase_db),
    current_user: Dict = Depends(get_current_user)
) -> ContactWithCategories:
    """
    Récupère les détails d'un contact avec ses catégories.
    Requirements: 1.1, 2.1 - All users can access any contact
    """
    contact = db.get_contact_by_id(contact_id)
    
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact non trouvé"
        )
    
    categories = db.get_contact_categories(contact_id)
    
    return contact_to_response(contact, categories)


@router.put("/{contact_id}", response_model=ContactWithCategories)
async def update_contact(
    contact_id: int,
    contact_data: ContactUpdate,
    db: SupabaseDB = Depends(get_supabase_db),
    current_user: Dict = Depends(get_current_user)
) -> ContactWithCategories:
    """
    Met à jour un contact existant.
    Requirements: 1.1, 2.1 - All users can update any contact
    """
    contact = db.get_contact_by_id(contact_id)
    
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact non trouvé"
        )
    
    update_data = {}
    
    # Log des données reçues pour debug
    logger.info(f"Update contact {contact_id}: received phone='{contact_data.phone_number}', code='{contact_data.country_code}', existing phone='{contact['phone_number']}', existing code='{contact['country_code']}'")
    
    # Vérifier si le numéro ou l'indicatif doit être mis à jour
    # On ne met à jour que si les valeurs sont explicitement fournies ET différentes
    phone_provided = contact_data.phone_number is not None
    code_provided = contact_data.country_code is not None
    
    if phone_provided or code_provided:
        # Utiliser les nouvelles valeurs ou garder les existantes
        new_phone = contact_data.phone_number if phone_provided else contact["phone_number"]
        new_code = contact_data.country_code if code_provided else contact["country_code"]
        
        # Nettoyer le numéro
        cleaned_new_phone = clean_phone_number(new_phone)
        
        # Calculer le nouveau full_number
        is_valid, error_msg, new_full_number = validate_full_phone_number(new_code, cleaned_new_phone)
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # Vérifier si le full_number a vraiment changé
        current_full_number = contact["full_number"]
        full_number_changed = new_full_number != current_full_number
        
        logger.info(f"Update contact {contact_id}: new_full='{new_full_number}', current_full='{current_full_number}', changed={full_number_changed}")
        
        if full_number_changed:
            # Vérifier si le nouveau numéro existe déjà (pour un autre contact)
            existing = db.get_contact_by_full_number_global(new_full_number)
            if existing and int(existing["id"]) != int(contact_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Un contact avec le numéro '{new_full_number}' existe déjà"
                )
            
            update_data["phone_number"] = cleaned_new_phone
            update_data["country_code"] = new_code
            update_data["full_number"] = new_full_number
    
    # Mettre à jour les autres champs
    if contact_data.first_name is not None:
        update_data["first_name"] = contact_data.first_name
    if contact_data.last_name is not None:
        update_data["last_name"] = contact_data.last_name
    
    if update_data:
        contact = db.update_contact(contact_id, update_data)
    
    # Mettre à jour les catégories si spécifiées
    if contact_data.category_ids is not None:
        # Vérifier que toutes les catégories existent
        for cat_id in contact_data.category_ids:
            category = db.get_category_by_id(cat_id, current_user["id"])
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Catégorie {cat_id} non trouvée"
                )
        
        db.set_contact_categories(contact_id, contact_data.category_ids)
    
    categories = db.get_contact_categories(contact_id)
    
    logger.info(f"Contact mis à jour: {contact['full_number']} (ID: {contact['id']})")
    
    # Invalider le cache des stats et catégories associées
    # Requirements: 1.3, 4.1 - Invalidation après modification de contact
    category_ids_list = [cat["id"] for cat in categories] if categories else None
    invalidate_cache_on_contact_change(category_ids_list)
    
    return contact_to_response(contact, categories)


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: int,
    db: SupabaseDB = Depends(get_supabase_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Supprime un contact et toutes ses associations.
    Requirements: 1.1, 2.1 - All users can delete any contact
    Requirements: 1.3, 4.2 - Invalidation après suppression de contact
    """
    contact = db.get_contact_by_id(contact_id)
    
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact non trouvé"
        )
    
    # Récupérer les catégories AVANT suppression pour invalidation du cache
    categories = db.get_contact_categories(contact_id)
    category_ids_list = [cat["id"] for cat in categories] if categories else None
    
    contact_number = contact["full_number"]
    db.delete_contact(contact_id)
    
    logger.info(f"Contact supprimé: {contact_number} (ID: {contact_id}) par utilisateur {current_user['id']}")
    
    # Invalider le cache des stats et catégories associées
    # Requirements: 1.3, 4.2 - Invalidation après suppression de contact
    invalidate_cache_on_contact_change(category_ids_list)
    
    return None


@router.post("/import", response_model=ContactImportResult)
async def import_contacts_csv(
    file: UploadFile = File(..., description="Fichier CSV à importer"),
    category_id: Optional[int] = Query(None, description="ID de catégorie pour associer les contacts importés"),
    db: SupabaseDB = Depends(get_supabase_db),
    current_user: Dict = Depends(get_current_user)
) -> ContactImportResult:
    """
    Importe des contacts depuis un fichier CSV.
    """
    # Vérifier le type de fichier
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le fichier doit être au format CSV"
        )
    
    # Vérifier la catégorie si spécifiée
    if category_id:
        category = db.get_category_by_id(category_id, current_user["id"])
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Catégorie non trouvée"
            )
    
    # Lire le contenu du fichier
    try:
        content = await file.read()
        decoded_content = content.decode('utf-8')
    except UnicodeDecodeError:
        try:
            decoded_content = content.decode('latin-1')
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Impossible de décoder le fichier. Utilisez l'encodage UTF-8."
            )
    
    # Parser le CSV
    csv_reader = csv.DictReader(io.StringIO(decoded_content))
    
    # Vérifier les colonnes requises
    required_columns = {'phone_number', 'country_code'}
    if not csv_reader.fieldnames:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le fichier CSV est vide ou mal formaté"
        )
    
    csv_columns = set(csv_reader.fieldnames)
    missing_columns = required_columns - csv_columns
    
    if missing_columns:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Colonnes manquantes dans le CSV: {', '.join(missing_columns)}"
        )
    
    # Traiter chaque ligne
    total = 0
    success = 0
    failed = 0
    errors = []
    
    for row_num, row in enumerate(csv_reader, start=2):
        total += 1
        
        phone_number = row.get('phone_number', '').strip()
        country_code = row.get('country_code', '').strip()
        first_name = row.get('first_name', '').strip() or None
        last_name = row.get('last_name', '').strip() or None
        
        # Valider le numéro
        is_valid, error_msg, full_number = validate_full_phone_number(country_code, phone_number)
        
        if not is_valid:
            failed += 1
            errors.append(f"Ligne {row_num}: {error_msg}")
            continue
        
        # Vérifier si le numéro existe déjà (vérification globale)
        # Requirements: 3.1, 3.3 - Global phone number uniqueness
        existing = db.get_contact_by_full_number_global(full_number)
        
        if existing:
            failed += 1
            errors.append(f"Ligne {row_num}: Le numéro '{full_number}' existe déjà")
            continue
        
        # Créer le contact
        try:
            contact = db.create_contact({
                "phone_number": clean_phone_number(phone_number),
                "country_code": country_code,
                "full_number": full_number,
                "first_name": first_name,
                "last_name": last_name,
                "created_by": current_user["id"]
            })
            
            # Associer à la catégorie si spécifiée
            if category_id:
                db.add_contact_to_category(contact["id"], category_id)
            
            success += 1
            
        except Exception as e:
            failed += 1
            errors.append(f"Ligne {row_num}: Erreur lors de la création - {str(e)}")
            continue
    
    logger.info(
        f"Import CSV terminé par utilisateur {current_user['id']}: "
        f"{success} succès, {failed} échecs sur {total} lignes"
    )
    
    # Invalider le cache si des contacts ont été créés
    # Requirements: 1.3, 4.1 - Invalidation après création de contacts
    if success > 0:
        # Invalider les stats et la catégorie associée si spécifiée
        category_ids_list = [category_id] if category_id else None
        invalidate_cache_on_contact_change(category_ids_list)
    
    return ContactImportResult(
        total=total,
        success=success,
        failed=failed,
        errors=errors[:50]
    )


@router.get("/export", response_class=StreamingResponse)
async def export_contacts_csv(
    category_id: Optional[int] = Query(None, description="Filtrer par catégorie"),
    db: SupabaseDB = Depends(get_supabase_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Exporte les contacts au format CSV.
    """
    # Requirements: 1.1, 2.1 - All users see all contacts
    contacts = db.get_contacts(
        skip=0,
        limit=10000,  # Limite haute pour l'export
        category_id=category_id
    )
    
    # Créer le CSV en mémoire
    output = io.StringIO()
    writer = csv.writer(output)
    
    # En-têtes
    writer.writerow(['phone_number', 'country_code', 'full_number', 'first_name', 'last_name', 'created_at'])
    
    # Données
    for contact in contacts:
        writer.writerow([
            contact["phone_number"],
            contact["country_code"],
            contact["full_number"],
            contact.get("first_name") or '',
            contact.get("last_name") or '',
            contact.get("created_at") or ''
        ])
    
    output.seek(0)
    
    logger.info(f"Export CSV de {len(contacts)} contacts par utilisateur {current_user['id']}")
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=contacts_export.csv"
        }
    )
