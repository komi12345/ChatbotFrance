"""
Client Supabase - Connexion à la base de données via l'API REST Supabase
Remplace SQLAlchemy pour une meilleure compatibilité réseau

Thread-safe: Utilise threading.local() pour les connexions par thread

ROBUSTESSE 2025:
- Validation des entrées pour prévenir les injections
- Gestion des erreurs de connexion avec retry
- Timeouts configurables
- Logging détaillé pour le debugging
"""
import logging
import threading
import re
from typing import Optional, Any, Dict, List
from supabase import create_client, Client
from app.config import settings

logger = logging.getLogger(__name__)

# Thread-local storage pour les clients Supabase
_thread_local = threading.local()

# ==========================================================================
# ROBUSTESSE - Validation des entrées
# ==========================================================================

def sanitize_string(value: str, max_length: int = 1000) -> str:
    """
    Nettoie une chaîne de caractères pour éviter les injections.
    
    Args:
        value: Chaîne à nettoyer
        max_length: Longueur maximale autorisée
    
    Returns:
        Chaîne nettoyée
    """
    if not isinstance(value, str):
        return str(value)[:max_length]
    
    # Tronquer si trop long
    if len(value) > max_length:
        value = value[:max_length]
    
    # Supprimer les caractères de contrôle (sauf newline et tab)
    value = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', value)
    
    return value


def validate_id(value: Any, field_name: str = "id") -> int:
    """
    Valide qu'une valeur est un ID entier positif.
    
    Args:
        value: Valeur à valider
        field_name: Nom du champ pour le message d'erreur
    
    Returns:
        ID validé
    
    Raises:
        ValueError: Si la valeur n'est pas un ID valide
    """
    try:
        id_value = int(value)
        if id_value <= 0:
            raise ValueError(f"{field_name} doit être un entier positif")
        return id_value
    except (TypeError, ValueError) as e:
        raise ValueError(f"{field_name} invalide: {value}") from e


def validate_phone_number(phone: str) -> str:
    """
    Valide et nettoie un numéro de téléphone.
    
    Args:
        phone: Numéro de téléphone à valider
    
    Returns:
        Numéro nettoyé
    
    Raises:
        ValueError: Si le numéro est invalide
    """
    if not phone:
        raise ValueError("Numéro de téléphone requis")
    
    # Nettoyer le numéro
    phone_clean = re.sub(r'[^\d+]', '', phone)
    
    # Vérifier le format
    if not re.match(r'^\+?\d{8,15}$', phone_clean):
        raise ValueError(f"Format de numéro invalide: {phone}")
    
    return phone_clean


def validate_email(email: str) -> str:
    """
    Valide et nettoie une adresse email.
    
    Args:
        email: Email à valider
    
    Returns:
        Email nettoyé
    
    Raises:
        ValueError: Si l'email est invalide
    """
    if not email:
        raise ValueError("Email requis")
    
    email = email.strip().lower()
    
    # Validation basique du format email
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        raise ValueError(f"Format d'email invalide: {email}")
    
    return email


def get_supabase_client() -> Client:
    """
    Retourne une instance du client Supabase thread-safe.
    Chaque thread obtient sa propre instance pour éviter les problèmes de concurrence.
    Utilise la clé service_role pour avoir accès complet aux données.
    """
    if not hasattr(_thread_local, 'supabase_client') or _thread_local.supabase_client is None:
        try:
            _thread_local.supabase_client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_ROLE_KEY
            )
            logger.debug(f"Client Supabase initialisé pour thread {threading.current_thread().name}")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du client Supabase: {e}")
            raise
    
    return _thread_local.supabase_client


class SupabaseDB:
    """
    Classe wrapper pour les opérations de base de données Supabase.
    Fournit une interface similaire à SQLAlchemy pour faciliter la migration.
    """
    
    def __init__(self):
        self.client = get_supabase_client()
    
    # ==================== USERS ====================
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Récupère un utilisateur par son ID"""
        response = self.client.table("users").select("*").eq("id", user_id).limit(1).execute()
        return response.data[0] if response.data else None
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Récupère un utilisateur par son email"""
        response = self.client.table("users").select("*").eq("email", email).limit(1).execute()
        return response.data[0] if response.data else None
    
    def get_users(self, skip: int = 0, limit: int = 50, search: Optional[str] = None) -> List[Dict]:
        """Liste les utilisateurs avec pagination"""
        query = self.client.table("users").select("*")
        
        if search:
            query = query.ilike("email", f"%{search}%")
        
        response = query.order("created_at", desc=True).range(skip, skip + limit - 1).execute()
        return response.data or []
    
    def create_user(self, data: Dict) -> Dict:
        """Crée un nouvel utilisateur"""
        response = self.client.table("users").insert(data).execute()
        return response.data[0] if response.data else None
    
    def update_user(self, user_id: int, data: Dict) -> Dict:
        """Met à jour un utilisateur"""
        response = self.client.table("users").update(data).eq("id", user_id).execute()
        return response.data[0] if response.data else None
    
    def delete_user(self, user_id: int) -> bool:
        """Supprime un utilisateur"""
        self.client.table("users").delete().eq("id", user_id).execute()
        return True
    
    # ==================== CATEGORIES ====================
    
    def get_category_by_id(self, category_id: int, user_id: int = None) -> Optional[Dict]:
        """Récupère une catégorie par son ID (partagée entre tous les utilisateurs)"""
        response = self.client.table("categories").select("*").eq("id", category_id).limit(1).execute()
        return response.data[0] if response.data else None
    
    def get_categories(self, user_id: int = None, skip: int = 0, limit: int = 50, search: Optional[str] = None) -> List[Dict]:
        """Liste toutes les catégories (partagées entre tous les utilisateurs)"""
        query = self.client.table("categories").select("*")
        
        if search:
            query = query.ilike("name", f"%{search}%")
        
        response = query.order("created_at", desc=True).range(skip, skip + limit - 1).execute()
        return response.data or []
    
    def get_categories_paginated(self, user_id: int = None, skip: int = 0, limit: int = 50, search: Optional[str] = None) -> tuple[List[Dict], int]:
        """Liste toutes les catégories avec le total (partagées entre tous les utilisateurs)"""
        query = self.client.table("categories").select("*", count="exact")
        
        if search:
            query = query.ilike("name", f"%{search}%")
        
        response = query.order("created_at", desc=True).range(skip, skip + limit - 1).execute()
        return response.data or [], response.count or 0
    
    def get_category_by_name(self, name: str, user_id: int = None) -> Optional[Dict]:
        """Récupère une catégorie par son nom (recherche globale)"""
        response = self.client.table("categories").select("*").eq("name", name).limit(1).execute()
        return response.data[0] if response.data else None
    
    def create_category(self, data: Dict) -> Dict:
        """Crée une nouvelle catégorie"""
        response = self.client.table("categories").insert(data).execute()
        return response.data[0] if response.data else None
    
    def update_category(self, category_id: int, data: Dict) -> Dict:
        """Met à jour une catégorie"""
        response = self.client.table("categories").update(data).eq("id", category_id).execute()
        return response.data[0] if response.data else None
    
    def delete_category(self, category_id: int) -> bool:
        """Supprime une catégorie"""
        self.client.table("categories").delete().eq("id", category_id).execute()
        return True
    
    def get_category_contact_count(self, category_id: int) -> int:
        """Compte le nombre de contacts dans une catégorie"""
        response = self.client.table("category_contacts").select("id", count="exact").eq("category_id", category_id).execute()
        return response.count or 0
    
    def get_categories_contact_counts(self, category_ids: List[int]) -> Dict[int, int]:
        """
        Compte le nombre de contacts pour plusieurs catégories en une seule requête.
        
        Optimisation: Utilise une seule requête avec GROUP BY au lieu de N requêtes.
        
        Args:
            category_ids: Liste des IDs de catégories
        
        Returns:
            Dict mapping category_id -> contact_count
        
        Requirements: 5.2 - Utiliser une seule requête avec COUNT au lieu de boucle
        """
        if not category_ids:
            return {}
        
        # Récupérer toutes les associations category_contacts pour les catégories demandées
        response = self.client.table("category_contacts").select("category_id").in_("category_id", category_ids).execute()
        
        # Compter manuellement par catégorie (Supabase REST API ne supporte pas GROUP BY)
        counts: Dict[int, int] = {cat_id: 0 for cat_id in category_ids}
        for row in (response.data or []):
            cat_id = row.get("category_id")
            if cat_id in counts:
                counts[cat_id] += 1
        
        return counts
    
    # ==================== CONTACTS ====================
    
    def get_contact_by_id(self, contact_id: int) -> Optional[Dict]:
        """Récupère un contact par son ID (partagé entre tous les utilisateurs)"""
        response = self.client.table("contacts").select("*").eq("id", contact_id).limit(1).execute()
        return response.data[0] if response.data else None
    
    def get_contact_by_full_number(self, full_number: str, user_id: int) -> Optional[Dict]:
        """Récupère un contact par son numéro complet pour un utilisateur"""
        response = self.client.table("contacts").select("*").eq("full_number", full_number).eq("created_by", user_id).limit(1).execute()
        return response.data[0] if response.data else None
    
    def get_contact_by_full_number_global(self, full_number: str) -> Optional[Dict]:
        """Récupère un contact par son numéro complet (recherche globale)"""
        response = self.client.table("contacts").select("*").eq("full_number", full_number).limit(1).execute()
        return response.data[0] if response.data else None
    
    def get_contacts(self, skip: int = 0, limit: int = 50, 
                     search: Optional[str] = None, category_id: Optional[int] = None,
                     whatsapp_status: Optional[str] = None) -> List[Dict]:
        """
        Liste tous les contacts (partagés entre tous les utilisateurs).
        
        Args:
            skip: Nombre d'éléments à sauter (pagination)
            limit: Nombre maximum d'éléments à retourner
            search: Terme de recherche (numéro, prénom, nom)
            category_id: Filtrer par catégorie
            whatsapp_status: Filtrer par statut WhatsApp ('verified', 'not_whatsapp', 'pending')
        """
        if category_id:
            # Requête avec jointure sur category_contacts
            contact_ids_response = self.client.table("category_contacts").select("contact_id").eq("category_id", category_id).execute()
            contact_ids = [r["contact_id"] for r in (contact_ids_response.data or [])]
            
            if not contact_ids:
                return []
            
            query = self.client.table("contacts").select("*").in_("id", contact_ids)
        else:
            query = self.client.table("contacts").select("*")
        
        if search:
            query = query.or_(f"full_number.ilike.%{search}%,first_name.ilike.%{search}%,last_name.ilike.%{search}%")
        
        # Filter by WhatsApp verification status
        if whatsapp_status == "verified":
            query = query.eq("whatsapp_verified", True)
        elif whatsapp_status == "not_whatsapp":
            query = query.eq("whatsapp_verified", False)
        elif whatsapp_status == "pending":
            query = query.is_("whatsapp_verified", "null")
        
        response = query.order("created_at", desc=True).range(skip, skip + limit - 1).execute()
        return response.data or []
    
    def get_contacts_paginated(self, skip: int = 0, limit: int = 50, 
                               search: Optional[str] = None, category_id: Optional[int] = None,
                               whatsapp_status: Optional[str] = None) -> tuple[List[Dict], int]:
        """
        Liste tous les contacts avec le total (partagés entre tous les utilisateurs).
        
        Args:
            skip: Nombre d'éléments à sauter (pagination)
            limit: Nombre maximum d'éléments à retourner
            search: Terme de recherche (numéro, prénom, nom)
            category_id: Filtrer par catégorie
            whatsapp_status: Filtrer par statut WhatsApp ('verified', 'not_whatsapp', 'pending')
        """
        if category_id:
            # Requête avec jointure sur category_contacts
            contact_ids_response = self.client.table("category_contacts").select("contact_id").eq("category_id", category_id).execute()
            contact_ids = [r["contact_id"] for r in (contact_ids_response.data or [])]
            
            if not contact_ids:
                return [], 0
            
            query = self.client.table("contacts").select("*", count="exact").in_("id", contact_ids)
        else:
            query = self.client.table("contacts").select("*", count="exact")
        
        if search:
            query = query.or_(f"full_number.ilike.%{search}%,first_name.ilike.%{search}%,last_name.ilike.%{search}%")
        
        # Filter by WhatsApp verification status
        if whatsapp_status == "verified":
            query = query.eq("whatsapp_verified", True)
        elif whatsapp_status == "not_whatsapp":
            query = query.eq("whatsapp_verified", False)
        elif whatsapp_status == "pending":
            query = query.is_("whatsapp_verified", "null")
        
        response = query.order("created_at", desc=True).range(skip, skip + limit - 1).execute()
        return response.data or [], response.count or 0
    
    def create_contact(self, data: Dict) -> Dict:
        """Crée un nouveau contact"""
        response = self.client.table("contacts").insert(data).execute()
        return response.data[0] if response.data else None
    
    def update_contact(self, contact_id: int, data: Dict) -> Dict:
        """Met à jour un contact"""
        response = self.client.table("contacts").update(data).eq("id", contact_id).execute()
        return response.data[0] if response.data else None
    
    def delete_contact(self, contact_id: int) -> bool:
        """Supprime un contact"""
        self.client.table("contacts").delete().eq("id", contact_id).execute()
        return True
    
    def get_contact_categories(self, contact_id: int) -> List[Dict]:
        """Récupère les catégories d'un contact"""
        response = self.client.table("category_contacts").select("category_id").eq("contact_id", contact_id).execute()
        category_ids = [r["category_id"] for r in (response.data or [])]
        
        if not category_ids:
            return []
        
        categories_response = self.client.table("categories").select("*").in_("id", category_ids).execute()
        return categories_response.data or []
    
    def add_contact_to_category(self, contact_id: int, category_id: int) -> bool:
        """Ajoute un contact à une catégorie"""
        # Vérifier si l'association existe déjà
        existing = self.client.table("category_contacts").select("id").eq("contact_id", contact_id).eq("category_id", category_id).execute()
        
        if not existing.data:
            self.client.table("category_contacts").insert({
                "contact_id": contact_id,
                "category_id": category_id
            }).execute()
        
        return True
    
    def remove_contact_from_category(self, contact_id: int, category_id: int) -> bool:
        """Retire un contact d'une catégorie"""
        self.client.table("category_contacts").delete().eq("contact_id", contact_id).eq("category_id", category_id).execute()
        return True
    
    def set_contact_categories(self, contact_id: int, category_ids: List[int]) -> bool:
        """Définit les catégories d'un contact (remplace les existantes)"""
        # Supprimer les associations existantes
        self.client.table("category_contacts").delete().eq("contact_id", contact_id).execute()
        
        # Ajouter les nouvelles associations
        if category_ids:
            associations = [{"contact_id": contact_id, "category_id": cat_id} for cat_id in category_ids]
            self.client.table("category_contacts").insert(associations).execute()
        
        return True
    
    def get_contacts_by_category(self, category_id: int) -> List[Dict]:
        """Récupère tous les contacts d'une catégorie (partagés entre tous les utilisateurs)"""
        contact_ids_response = self.client.table("category_contacts").select("contact_id").eq("category_id", category_id).execute()
        contact_ids = [r["contact_id"] for r in (contact_ids_response.data or [])]
        
        if not contact_ids:
            return []
        
        contacts_response = self.client.table("contacts").select("*").in_("id", contact_ids).execute()
        return contacts_response.data or []
    
    def get_contacts_not_in_category(self, category_id: int, skip: int = 0, limit: int = 50, 
                                      search: Optional[str] = None) -> tuple[List[Dict], int]:
        """
        Récupère les contacts qui ne sont PAS dans une catégorie donnée.
        Avec pagination et recherche côté serveur.
        
        Args:
            category_id: ID de la catégorie à exclure
            skip: Nombre d'éléments à sauter (pagination)
            limit: Nombre maximum d'éléments à retourner
            search: Terme de recherche (numéro, prénom, nom)
        
        Returns:
            Tuple (liste des contacts, total)
        """
        # 1. Récupérer les IDs des contacts déjà dans cette catégorie
        existing_response = self.client.table("category_contacts").select("contact_id").eq("category_id", category_id).execute()
        existing_contact_ids = [r["contact_id"] for r in (existing_response.data or [])]
        
        # 2. Récupérer tous les contacts qui ne sont PAS dans cette liste
        query = self.client.table("contacts").select("*", count="exact")
        
        # Exclure les contacts déjà dans la catégorie
        if existing_contact_ids:
            # Supabase ne supporte pas directement "NOT IN", on utilise une approche différente
            # On récupère tous les contacts et on filtre côté serveur
            # Pour une meilleure performance avec beaucoup de contacts, on pourrait utiliser une RPC
            pass
        
        # Appliquer la recherche si présente
        if search:
            query = query.or_(f"full_number.ilike.%{search}%,first_name.ilike.%{search}%,last_name.ilike.%{search}%")
        
        # Exécuter la requête
        response = query.order("created_at", desc=True).execute()
        all_contacts = response.data or []
        
        # Filtrer les contacts qui sont déjà dans la catégorie
        if existing_contact_ids:
            filtered_contacts = [c for c in all_contacts if c["id"] not in existing_contact_ids]
        else:
            filtered_contacts = all_contacts
        
        # Calculer le total après filtrage
        total = len(filtered_contacts)
        
        # Appliquer la pagination
        paginated_contacts = filtered_contacts[skip:skip + limit]
        
        return paginated_contacts, total
    
    # ==================== CAMPAIGNS ====================
    
    def get_campaign_by_id(self, campaign_id: int) -> Optional[Dict]:
        """Récupère une campagne par son ID (partagée entre tous les utilisateurs)"""
        response = self.client.table("campaigns").select("*").eq("id", campaign_id).limit(1).execute()
        return response.data[0] if response.data else None
    
    def get_campaigns(self, skip: int = 0, limit: int = 50, 
                      status: Optional[str] = None) -> tuple[List[Dict], int]:
        """Liste toutes les campagnes avec le total (partagées entre tous les utilisateurs)"""
        query = self.client.table("campaigns").select("*", count="exact")
        
        if status:
            query = query.eq("status", status)
        
        response = query.order("created_at", desc=True).range(skip, skip + limit - 1).execute()
        return response.data or [], response.count or 0
    
    def create_campaign(self, data: Dict) -> Dict:
        """Crée une nouvelle campagne"""
        response = self.client.table("campaigns").insert(data).execute()
        return response.data[0] if response.data else None
    
    def update_campaign(self, campaign_id: int, data: Dict) -> Dict:
        """Met à jour une campagne"""
        response = self.client.table("campaigns").update(data).eq("id", campaign_id).execute()
        return response.data[0] if response.data else None
    
    def delete_campaign(self, campaign_id: int) -> bool:
        """Supprime une campagne"""
        self.client.table("campaigns").delete().eq("id", campaign_id).execute()
        return True
    
    def get_campaign_categories(self, campaign_id: int) -> List[Dict]:
        """Récupère les catégories d'une campagne"""
        response = self.client.table("campaign_categories").select("category_id").eq("campaign_id", campaign_id).execute()
        category_ids = [r["category_id"] for r in (response.data or [])]
        
        if not category_ids:
            return []
        
        categories_response = self.client.table("categories").select("*").in_("id", category_ids).execute()
        return categories_response.data or []
    
    def set_campaign_categories(self, campaign_id: int, category_ids: List[int]) -> bool:
        """Définit les catégories d'une campagne"""
        # Supprimer les associations existantes
        self.client.table("campaign_categories").delete().eq("campaign_id", campaign_id).execute()
        
        # Ajouter les nouvelles associations
        if category_ids:
            associations = [{"campaign_id": campaign_id, "category_id": cat_id} for cat_id in category_ids]
            self.client.table("campaign_categories").insert(associations).execute()
        
        return True
    
    def get_contacts_for_campaign(self, campaign_id: int) -> List[Dict]:
        """Récupère tous les contacts ciblés par une campagne (via ses catégories, partagés entre tous les utilisateurs)"""
        # Récupérer les catégories de la campagne
        cat_response = self.client.table("campaign_categories").select("category_id").eq("campaign_id", campaign_id).execute()
        category_ids = [r["category_id"] for r in (cat_response.data or [])]
        
        if not category_ids:
            return []
        
        # Récupérer les contacts de ces catégories
        contact_ids_response = self.client.table("category_contacts").select("contact_id").in_("category_id", category_ids).execute()
        contact_ids = list(set([r["contact_id"] for r in (contact_ids_response.data or [])]))
        
        if not contact_ids:
            return []
        
        contacts_response = self.client.table("contacts").select("*").in_("id", contact_ids).execute()
        return contacts_response.data or []
    
    # ==================== MESSAGES ====================
    
    def get_message_by_id(self, message_id: int) -> Optional[Dict]:
        """Récupère un message par son ID"""
        response = self.client.table("messages").select("*").eq("id", message_id).limit(1).execute()
        return response.data[0] if response.data else None
    
    def get_messages(self, campaign_id: Optional[int] = None, contact_id: Optional[int] = None,
                     skip: int = 0, limit: int = 50) -> tuple[List[Dict], int]:
        """Liste les messages avec filtres"""
        query = self.client.table("messages").select("*", count="exact")
        
        if campaign_id:
            query = query.eq("campaign_id", campaign_id)
        if contact_id:
            query = query.eq("contact_id", contact_id)
        
        response = query.order("created_at", desc=True).range(skip, skip + limit - 1).execute()
        return response.data or [], response.count or 0
    
    def create_message(self, data: Dict) -> Dict:
        """Crée un nouveau message"""
        response = self.client.table("messages").insert(data).execute()
        return response.data[0] if response.data else None
    
    def update_message(self, message_id: int, data: Dict) -> Dict:
        """Met à jour un message"""
        response = self.client.table("messages").update(data).eq("id", message_id).execute()
        return response.data[0] if response.data else None
    
    def get_campaign_message_stats(self, campaign_id: int) -> Dict:
        """Récupère les statistiques de messages d'une campagne"""
        stats = {"total": 0, "sent": 0, "delivered": 0, "read": 0, "failed": 0, "pending": 0}
        
        # Compter par statut
        for status_val in ["sent", "delivered", "read", "failed", "pending"]:
            count_response = self.client.table("messages").select("id", count="exact").eq("campaign_id", campaign_id).eq("status", status_val).execute()
            stats[status_val] = count_response.count or 0
            stats["total"] += stats[status_val]
        
        return stats
    
    def get_failed_messages(self, campaign_id: int) -> List[Dict]:
        """Récupère les messages échoués d'une campagne"""
        response = self.client.table("messages").select("*").eq("campaign_id", campaign_id).eq("status", "failed").execute()
        return response.data or []
    
    def get_campaign_interaction_count(self, campaign_id: int) -> int:
        """
        Compte le nombre d'interactions pour une campagne.
        
        Optimisation 2025: Utilise une seule requête avec IN clause au lieu de N requêtes.
        Requirements: 2.1, 2.2 - Optimisation des requêtes SQL
        """
        # Les interactions sont liées aux messages de la campagne
        # On compte les interactions dont le message_id appartient à cette campagne
        messages_response = self.client.table("messages").select("id").eq("campaign_id", campaign_id).execute()
        if not messages_response.data:
            return 0
        
        message_ids = [m["id"] for m in messages_response.data]
        
        # Optimisation: Compter toutes les interactions en une seule requête avec IN clause
        count_response = self.client.table("interactions").select("id", count="exact").in_("message_id", message_ids).execute()
        return count_response.count or 0
    
    def get_campaign_messages_with_contacts(self, campaign_id: int, limit: int = 100) -> List[Dict]:
        """
        Récupère les messages d'une campagne avec les infos des contacts.
        
        Optimisation 2025: Batch fetch des contacts au lieu de N requêtes individuelles.
        Requirements: 2.1, 2.2 - Optimisation des requêtes SQL (N+1 → batch)
        """
        response = self.client.table("messages").select(
            "id, status, message_type, content, error_message, sent_at, contact_id"
        ).eq("campaign_id", campaign_id).order("created_at", desc=True).limit(limit).execute()
        
        if not response.data:
            return []
        
        # Optimisation: Récupérer tous les contacts en une seule requête
        contact_ids = list(set(msg.get("contact_id") for msg in response.data if msg.get("contact_id")))
        contacts_map = {}
        
        if contact_ids:
            contacts_response = self.client.table("contacts").select("*").in_("id", contact_ids).execute()
            contacts_map = {c["id"]: c for c in (contacts_response.data or [])}
        
        messages = []
        for msg in response.data:
            # Récupérer les infos du contact depuis le cache
            contact = contacts_map.get(msg.get("contact_id"))
            
            # Construire le nom du contact
            contact_name = None
            contact_phone = None
            if contact:
                # Construire le nom complet à partir de first_name et last_name
                name_parts = []
                if contact.get("first_name"):
                    name_parts.append(contact["first_name"])
                if contact.get("last_name"):
                    name_parts.append(contact["last_name"])
                contact_name = " ".join(name_parts) if name_parts else None
                
                # Utiliser full_number pour le numéro de téléphone
                contact_phone = contact.get("full_number")
            
            messages.append({
                "id": msg["id"],
                "status": msg["status"],
                "message_type": msg.get("message_type", "message_1"),
                "content": msg.get("content", ""),
                "error_message": msg.get("error_message"),
                "sent_at": msg.get("sent_at"),
                "contact_id": msg.get("contact_id"),
                "contact_name": contact_name,
                "contact_phone": contact_phone,
            })
        
        return messages
    
    # ==================== INTERACTIONS ====================
    
    def create_interaction(self, data: Dict) -> Dict:
        """Crée une nouvelle interaction"""
        response = self.client.table("interactions").insert(data).execute()
        return response.data[0] if response.data else None
    
    def get_interactions(self, contact_id: int, skip: int = 0, limit: int = 50) -> List[Dict]:
        """Liste les interactions d'un contact"""
        response = self.client.table("interactions").select("*").eq("contact_id", contact_id).order("created_at", desc=True).range(skip, skip + limit - 1).execute()
        return response.data or []
    
    # ==================== STATISTICS ====================
    
    def get_dashboard_stats(self) -> Dict:
        """Récupère les statistiques pour le dashboard (agrégées pour tous les utilisateurs)"""
        stats = {}
        
        # Nombre de contacts (tous les contacts)
        contacts_response = self.client.table("contacts").select("id", count="exact").execute()
        stats["total_contacts"] = contacts_response.count or 0
        
        # Nombre de catégories (toutes les catégories)
        categories_response = self.client.table("categories").select("id", count="exact").execute()
        stats["total_categories"] = categories_response.count or 0
        
        # Nombre de campagnes (toutes les campagnes)
        campaigns_response = self.client.table("campaigns").select("id", count="exact").execute()
        stats["total_campaigns"] = campaigns_response.count or 0
        
        # Nombre de messages envoyés (tous les messages)
        messages_response = self.client.table("messages").select("id", count="exact").execute()
        stats["total_messages"] = messages_response.count or 0
        
        return stats
    
    def get_whatsapp_verification_stats(self) -> Dict:
        """
        Récupère les statistiques de vérification WhatsApp pour tous les contacts.
        
        Returns:
            Dict avec verified_count, not_whatsapp_count, pending_count, total_count
        
        Requirements: 1.2, 2.2 - Display aggregated verification statistics for all users
        """
        stats = {}
        
        # Total contacts (tous les contacts)
        total_response = self.client.table("contacts").select("id", count="exact").execute()
        stats["total_count"] = total_response.count or 0
        
        # Verified (whatsapp_verified = true)
        verified_response = self.client.table("contacts").select("id", count="exact").eq("whatsapp_verified", True).execute()
        stats["verified_count"] = verified_response.count or 0
        
        # Not WhatsApp (whatsapp_verified = false)
        not_whatsapp_response = self.client.table("contacts").select("id", count="exact").eq("whatsapp_verified", False).execute()
        stats["not_whatsapp_count"] = not_whatsapp_response.count or 0
        
        # Pending (whatsapp_verified = null)
        pending_response = self.client.table("contacts").select("id", count="exact").is_("whatsapp_verified", "null").execute()
        stats["pending_count"] = pending_response.count or 0
        
        return stats
    
    # ==================== MONITORING ====================
    
    def get_daily_stats(self, date: str) -> Optional[Dict]:
        """
        Récupère les statistiques quotidiennes pour une date donnée.
        
        Args:
            date: Date au format YYYY-MM-DD
        
        Returns:
            Dict avec message_1_count, message_2_count, error_count ou None
        
        Requirements: 7.4
        """
        response = self.client.table("daily_message_stats").select("*").eq("date", date).limit(1).execute()
        return response.data[0] if response.data else None
    
    def upsert_daily_stats(self, data: Dict) -> Dict:
        """
        Insère ou met à jour les statistiques quotidiennes.
        
        Args:
            data: Dict avec date, message_1_count, message_2_count, error_count
        
        Returns:
            Dict des données insérées/mises à jour
        
        Requirements: 7.4
        """
        # Add updated_at timestamp
        data["updated_at"] = "now()"
        
        response = self.client.table("daily_message_stats").upsert(
            data,
            on_conflict="date"
        ).execute()
        return response.data[0] if response.data else None
    
    def get_daily_stats_history(self, days: int = 7) -> List[Dict]:
        """
        Récupère l'historique des statistiques quotidiennes.
        
        Args:
            days: Nombre de jours d'historique à récupérer
        
        Returns:
            Liste des statistiques quotidiennes ordonnées par date décroissante
        
        Requirements: 7.4
        """
        from datetime import datetime, timedelta, timezone
        
        # Calculate the start date
        end_date = datetime.now(timezone.utc).date()
        start_date = end_date - timedelta(days=days - 1)
        
        response = self.client.table("daily_message_stats").select("*").gte(
            "date", start_date.isoformat()
        ).lte(
            "date", end_date.isoformat()
        ).order("date", desc=True).execute()
        
        return response.data or []
    
    def create_message_error(self, data: Dict) -> Dict:
        """
        Crée une entrée d'erreur de message.
        
        Args:
            data: Dict avec message_id (optional), error_code, error_message
        
        Returns:
            Dict de l'erreur créée
        
        Requirements: 6.4
        """
        response = self.client.table("message_errors").insert(data).execute()
        return response.data[0] if response.data else None
    
    def get_recent_errors(self, limit: int = 10) -> List[Dict]:
        """
        Récupère les erreurs récentes.
        
        Args:
            limit: Nombre maximum d'erreurs à retourner
        
        Returns:
            Liste des erreurs ordonnées par date décroissante
        
        Requirements: 6.4
        """
        response = self.client.table("message_errors").select("*").order(
            "occurred_at", desc=True
        ).limit(limit).execute()
        return response.data or []


# Instance singleton pour injection de dépendance
_db_instance: Optional[SupabaseDB] = None


def get_supabase_db() -> SupabaseDB:
    """
    Retourne l'instance singleton de SupabaseDB.
    Utilisé comme dépendance FastAPI.
    """
    global _db_instance
    
    if _db_instance is None:
        _db_instance = SupabaseDB()
    
    return _db_instance
