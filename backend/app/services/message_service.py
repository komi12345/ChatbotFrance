"""
Service de gestion des messages et campagnes
Gère la création de campagnes, l'envoi de messages et les statistiques

Exigences: 4.4, 6.2, 6.5, 7.1
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.campaign import Campaign
from app.models.message import Message
from app.models.contact import Contact
from app.models.category import Category
from app.models.interaction import Interaction
from app.tasks.message_tasks import send_campaign_messages, retry_campaign_failed_messages

# Configuration du logger
logger = logging.getLogger(__name__)


class MessageService:
    """
    Service pour la gestion des messages et campagnes.
    Fournit les fonctions de création, envoi et statistiques.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_campaign(
        self,
        name: str,
        message_1: str,
        category_ids: List[int],
        user_id: int,
        message_2: Optional[str] = None,
        template_name: Optional[str] = None
    ) -> Campaign:
        """
        Crée une nouvelle campagne avec ses messages.
        
        Args:
            name: Nom de la campagne
            message_1: Contenu du Message 1 (template)
            category_ids: Liste des IDs de catégories cibles
            user_id: ID de l'utilisateur créateur
            message_2: Contenu du Message 2 (suivi automatique)
            template_name: Nom du template WhatsApp approuvé
        
        Returns:
            Campaign créée
        
        Exigences: 4.4, 20.1, 20.2
        """
        # Récupérer les catégories
        categories = self.db.query(Category).filter(
            Category.id.in_(category_ids),
            Category.created_by == user_id
        ).all()
        
        if not categories:
            raise ValueError("Aucune catégorie valide trouvée")
        
        # Collecter tous les contacts uniques des catégories
        contact_ids = set()
        for category in categories:
            for contact in category.contacts:
                contact_ids.add(contact.id)
        
        if not contact_ids:
            raise ValueError("Aucun contact dans les catégories sélectionnées")
        
        # Créer la campagne
        campaign = Campaign(
            name=name,
            message_1=message_1,
            message_2=message_2,
            template_name=template_name,
            status="draft",
            total_recipients=len(contact_ids),
            created_by=user_id
        )
        
        # Associer les catégories
        campaign.categories = categories
        
        self.db.add(campaign)
        self.db.flush()  # Pour obtenir l'ID de la campagne
        
        # Créer les enregistrements de messages pour chaque contact
        contacts = self.db.query(Contact).filter(Contact.id.in_(contact_ids)).all()
        
        for contact in contacts:
            message = Message(
                campaign_id=campaign.id,
                contact_id=contact.id,
                message_type="message_1",
                content=message_1,
                status="pending"
            )
            self.db.add(message)
        
        self.db.commit()
        self.db.refresh(campaign)
        
        logger.info(
            f"Campagne '{name}' créée (ID: {campaign.id}) avec {len(contact_ids)} destinataires"
        )
        
        return campaign
    
    def send_campaign_messages(self, campaign_id: int, user_id: int) -> Dict[str, Any]:
        """
        Déclenche l'envoi des messages d'une campagne via Celery.
        
        Args:
            campaign_id: ID de la campagne
            user_id: ID de l'utilisateur (pour vérification)
        
        Returns:
            Dictionnaire avec les informations de la tâche
        
        Exigences: 4.4, 16.1, 16.2
        """
        # Vérifier que la campagne existe et appartient à l'utilisateur
        campaign = self.db.query(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.created_by == user_id
        ).first()
        
        if not campaign:
            raise ValueError("Campagne non trouvée")
        
        if campaign.status == "sending":
            raise ValueError("La campagne est déjà en cours d'envoi")
        
        if campaign.status == "completed":
            raise ValueError("La campagne est déjà terminée")
        
        # Mettre à jour le statut
        campaign.status = "sending"
        self.db.commit()
        
        # Déclencher la tâche Celery
        task = send_campaign_messages.apply_async(args=[campaign_id])
        
        logger.info(f"Envoi campagne {campaign_id} déclenché, task_id: {task.id}")
        
        return {
            "campaign_id": campaign_id,
            "task_id": task.id,
            "status": "sending",
            "total_recipients": campaign.total_recipients
        }
    
    def get_campaign_stats(self, campaign_id: int, user_id: int) -> Dict[str, Any]:
        """
        Calcule les statistiques détaillées d'une campagne.
        
        Args:
            campaign_id: ID de la campagne
            user_id: ID de l'utilisateur (pour vérification)
        
        Returns:
            Dictionnaire avec les statistiques
        
        Exigences: 6.2, 6.5, 20.3, 20.4
        """
        # Vérifier que la campagne existe et appartient à l'utilisateur
        campaign = self.db.query(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.created_by == user_id
        ).first()
        
        if not campaign:
            raise ValueError("Campagne non trouvée")
        
        # Compter les messages par statut
        status_counts = self.db.query(
            Message.status,
            func.count(Message.id).label("count")
        ).filter(
            Message.campaign_id == campaign_id
        ).group_by(Message.status).all()
        
        messages_by_status = {status: count for status, count in status_counts}
        
        # Calculer les statistiques quotidiennes (7 derniers jours)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        daily_stats = self.db.query(
            func.date(Message.sent_at).label("date"),
            func.count(Message.id).label("sent"),
            func.sum(
                func.case((Message.status == "delivered", 1), else_=0)
            ).label("delivered"),
            func.sum(
                func.case((Message.status == "read", 1), else_=0)
            ).label("read"),
            func.sum(
                func.case((Message.status == "failed", 1), else_=0)
            ).label("failed")
        ).filter(
            Message.campaign_id == campaign_id,
            Message.sent_at >= seven_days_ago
        ).group_by(func.date(Message.sent_at)).all()
        
        daily_stats_list = [
            {
                "date": str(stat.date) if stat.date else None,
                "sent": stat.sent or 0,
                "delivered": stat.delivered or 0,
                "read": stat.read or 0,
                "failed": stat.failed or 0
            }
            for stat in daily_stats
        ]
        
        # Calculer le taux de réussite
        success_rate = self.calculate_success_rate(campaign_id)
        
        return {
            "campaign_id": campaign_id,
            "campaign_name": campaign.name,
            "total_recipients": campaign.total_recipients,
            "sent_count": campaign.sent_count,
            "success_count": campaign.success_count,
            "failed_count": campaign.failed_count,
            "interaction_count": campaign.interaction_count,
            "success_rate": success_rate,
            "status": campaign.status,
            "messages_by_status": messages_by_status,
            "daily_stats": daily_stats_list
        }
    
    def retry_failed_messages(self, campaign_id: int, user_id: int) -> Dict[str, Any]:
        """
        Réessaie l'envoi des messages échoués d'une campagne.
        
        Args:
            campaign_id: ID de la campagne
            user_id: ID de l'utilisateur (pour vérification)
        
        Returns:
            Dictionnaire avec les informations du retry
        
        Exigences: 7.1
        """
        # Vérifier que la campagne existe et appartient à l'utilisateur
        campaign = self.db.query(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.created_by == user_id
        ).first()
        
        if not campaign:
            raise ValueError("Campagne non trouvée")
        
        # Compter les messages qui peuvent être réessayés
        retryable_count = self.db.query(Message).filter(
            Message.campaign_id == campaign_id,
            Message.status == "failed",
            Message.retry_count < 3  # Max 3 tentatives (Exigence 7.3)
        ).count()
        
        if retryable_count == 0:
            return {
                "campaign_id": campaign_id,
                "retried_count": 0,
                "message": "Aucun message à réessayer"
            }
        
        # Déclencher la tâche Celery de retry
        task = retry_campaign_failed_messages.apply_async(args=[campaign_id])
        
        logger.info(
            f"Retry campagne {campaign_id} déclenché: {retryable_count} messages, task_id: {task.id}"
        )
        
        return {
            "campaign_id": campaign_id,
            "retried_count": retryable_count,
            "task_id": task.id,
            "message": f"{retryable_count} message(s) programmé(s) pour réessai"
        }
    
    def calculate_success_rate(self, campaign_id: int) -> float:
        """
        Calcule le taux de réussite d'une campagne.
        
        Formule: (messages réussis / total messages) × 100
        
        Args:
            campaign_id: ID de la campagne
        
        Returns:
            Taux de réussite en pourcentage
        
        Exigences: 6.5
        """
        # Compter le total de messages
        total = self.db.query(Message).filter(
            Message.campaign_id == campaign_id
        ).count()
        
        if total == 0:
            return 0.0
        
        # Compter les messages réussis (sent, delivered, read)
        success = self.db.query(Message).filter(
            Message.campaign_id == campaign_id,
            Message.status.in_(["sent", "delivered", "read"])
        ).count()
        
        return round((success / total) * 100, 2)
    
    def get_messages_list(
        self,
        user_id: int,
        campaign_id: Optional[int] = None,
        contact_id: Optional[int] = None,
        status: Optional[str] = None,
        message_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[Message]:
        """
        Récupère la liste des messages avec filtres.
        
        Args:
            user_id: ID de l'utilisateur
            campaign_id: Filtre par campagne
            contact_id: Filtre par contact
            status: Filtre par statut
            message_type: Filtre par type (message_1, message_2)
            skip: Offset pour pagination
            limit: Limite de résultats
        
        Returns:
            Liste des messages
        
        Exigences: 6.1, 6.3
        """
        # Construire la requête de base avec jointure sur Campaign pour vérifier l'ownership
        query = self.db.query(Message).join(Campaign).filter(
            Campaign.created_by == user_id
        )
        
        # Appliquer les filtres
        if campaign_id:
            query = query.filter(Message.campaign_id == campaign_id)
        
        if contact_id:
            query = query.filter(Message.contact_id == contact_id)
        
        if status:
            query = query.filter(Message.status == status)
        
        if message_type:
            query = query.filter(Message.message_type == message_type)
        
        # Pagination
        messages = query.order_by(Message.created_at.desc()).offset(skip).limit(limit).all()
        
        return messages
    
    def get_global_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Calcule les statistiques globales de tous les messages de l'utilisateur.
        
        Args:
            user_id: ID de l'utilisateur
        
        Returns:
            Dictionnaire avec les statistiques globales
        
        Exigences: 6.4, 9.1, 9.2
        """
        # Requête de base avec jointure sur Campaign
        base_query = self.db.query(Message).join(Campaign).filter(
            Campaign.created_by == user_id
        )
        
        # Compter par statut
        total = base_query.count()
        sent = base_query.filter(Message.status.in_(["sent", "delivered", "read"])).count()
        delivered = base_query.filter(Message.status.in_(["delivered", "read"])).count()
        read = base_query.filter(Message.status == "read").count()
        failed = base_query.filter(Message.status == "failed").count()
        pending = base_query.filter(Message.status == "pending").count()
        
        # Calculer les taux
        success_rate = round((sent / total) * 100, 2) if total > 0 else 0.0
        delivery_rate = round((delivered / sent) * 100, 2) if sent > 0 else 0.0
        read_rate = round((read / delivered) * 100, 2) if delivered > 0 else 0.0
        
        return {
            "total_messages": total,
            "sent_count": sent,
            "delivered_count": delivered,
            "read_count": read,
            "failed_count": failed,
            "pending_count": pending,
            "success_rate": success_rate,
            "delivery_rate": delivery_rate,
            "read_rate": read_rate
        }


def get_message_service(db: Session) -> MessageService:
    """Factory function pour créer une instance du service"""
    return MessageService(db)
