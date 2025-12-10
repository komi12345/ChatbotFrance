"""
Service d'automatisation des messages
Gère la logique de déclenchement du Message 2 et l'enregistrement des interactions

Exigences: 4.5, 4.6, 4.7, 8.3, 8.4
"""
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.campaign import Campaign
from app.models.message import Message
from app.models.contact import Contact
from app.models.interaction import Interaction
from app.tasks.message_tasks import send_single_message

# Configuration du logger
logger = logging.getLogger(__name__)


class AutomationService:
    """
    Service pour l'automatisation des messages.
    Gère le déclenchement du Message 2 après interaction et l'enregistrement des interactions.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def should_send_message_2(
        self,
        contact_id: int,
        campaign_id: int
    ) -> bool:
        """
        Vérifie si le Message 2 doit être envoyé à un contact pour une campagne.
        
        Conditions:
        - Le contact a reçu le Message 1 avec succès
        - Le contact a interagi (reply ou reaction)
        - La campagne a un Message 2 configuré
        
        Args:
            contact_id: ID du contact
            campaign_id: ID de la campagne
        
        Returns:
            True si le Message 2 doit être envoyé
        
        Exigences: 4.5, 4.6, 8.3
        """
        # Vérifier que la campagne a un Message 2
        campaign = self.db.query(Campaign).filter(
            Campaign.id == campaign_id
        ).first()
        
        if not campaign or not campaign.message_2:
            logger.debug(f"Campagne {campaign_id}: pas de Message 2 configuré")
            return False
        
        # Vérifier que le Message 1 a été envoyé avec succès
        message_1 = self.db.query(Message).filter(
            Message.campaign_id == campaign_id,
            Message.contact_id == contact_id,
            Message.message_type == "message_1",
            Message.status.in_(["sent", "delivered", "read"])
        ).first()
        
        if not message_1:
            logger.debug(
                f"Contact {contact_id}, Campagne {campaign_id}: Message 1 non envoyé"
            )
            return False
        
        # Vérifier qu'il y a une interaction (reply ou reaction)
        has_interaction = self.db.query(Interaction).filter(
            Interaction.campaign_id == campaign_id,
            Interaction.contact_id == contact_id,
            Interaction.interaction_type.in_(["reply", "reaction"])
        ).first() is not None
        
        if not has_interaction:
            logger.debug(
                f"Contact {contact_id}, Campagne {campaign_id}: pas d'interaction"
            )
            return False
        
        return True
    
    def trigger_message_2(
        self,
        contact_id: int,
        campaign_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Déclenche l'envoi du Message 2 à un contact.
        
        Args:
            contact_id: ID du contact
            campaign_id: ID de la campagne
        
        Returns:
            Dictionnaire avec les informations de l'envoi ou None si échec
        
        Exigences: 4.5, 4.6, 8.4
        """
        # Vérifier les conditions
        if not self.should_send_message_2(contact_id, campaign_id):
            logger.info(
                f"Message 2 non déclenché pour contact {contact_id}, campagne {campaign_id}"
            )
            return None
        
        # Récupérer la campagne
        campaign = self.db.query(Campaign).filter(
            Campaign.id == campaign_id
        ).first()
        
        if not campaign:
            return None
        
        # Vérifier si un Message 2 n'a pas déjà été envoyé récemment
        # (pour éviter les doublons en cas de multiples interactions rapides)
        existing_message_2 = self.db.query(Message).filter(
            Message.campaign_id == campaign_id,
            Message.contact_id == contact_id,
            Message.message_type == "message_2"
        ).first()
        
        # Si un Message 2 existe déjà et est en cours ou réussi, ne pas en créer un nouveau
        # Sauf si l'exigence 4.6 demande d'envoyer à chaque interaction
        # Dans ce cas, on crée un nouveau message à chaque fois
        
        # Créer le message
        message = Message(
            campaign_id=campaign_id,
            contact_id=contact_id,
            message_type="message_2",
            content=campaign.message_2,
            status="pending"
        )
        
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        
        # Déclencher l'envoi via Celery (Message 2 = texte libre, pas template)
        task = send_single_message.apply_async(
            args=[message.id],
            kwargs={
                "is_template": False,
                "template_name": None
            }
        )
        
        logger.info(
            f"Message 2 déclenché pour contact {contact_id}, campagne {campaign_id}, "
            f"message_id: {message.id}, task_id: {task.id}"
        )
        
        return {
            "message_id": message.id,
            "task_id": task.id,
            "contact_id": contact_id,
            "campaign_id": campaign_id
        }
    
    def reset_automation_sequence(
        self,
        contact_id: int,
        campaign_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Réinitialise la séquence d'automatisation pour un contact.
        Utilisé quand un nouveau Message 1 est envoyé.
        
        Args:
            contact_id: ID du contact
            campaign_id: ID de la campagne (optionnel, si None réinitialise toutes)
        
        Returns:
            Dictionnaire avec les informations de la réinitialisation
        
        Exigences: 4.7
        """
        # Construire la requête de base
        query = self.db.query(Message).filter(
            Message.contact_id == contact_id,
            Message.message_type == "message_2",
            Message.status == "pending"
        )
        
        if campaign_id:
            query = query.filter(Message.campaign_id == campaign_id)
        
        # Annuler les Message 2 en attente
        pending_messages = query.all()
        cancelled_count = 0
        
        for message in pending_messages:
            message.status = "cancelled"
            cancelled_count += 1
        
        self.db.commit()
        
        logger.info(
            f"Séquence réinitialisée pour contact {contact_id}: "
            f"{cancelled_count} Message 2 annulé(s)"
        )
        
        return {
            "contact_id": contact_id,
            "campaign_id": campaign_id,
            "cancelled_count": cancelled_count
        }
    
    def log_interaction(
        self,
        contact_id: int,
        campaign_id: int,
        interaction_type: str,
        content: Optional[str] = None,
        whatsapp_message_id: Optional[str] = None,
        message_id: Optional[int] = None
    ) -> Interaction:
        """
        Enregistre une interaction dans la base de données.
        
        Args:
            contact_id: ID du contact
            campaign_id: ID de la campagne
            interaction_type: Type d'interaction (reply, reaction, read, delivered)
            content: Contenu de l'interaction (optionnel)
            whatsapp_message_id: ID du message WhatsApp (optionnel)
            message_id: ID du message local associé (optionnel)
        
        Returns:
            Interaction créée
        
        Exigences: 8.2, 8.3
        """
        interaction = Interaction(
            campaign_id=campaign_id,
            contact_id=contact_id,
            message_id=message_id,
            interaction_type=interaction_type,
            content=content,
            whatsapp_message_id=whatsapp_message_id,
            received_at=datetime.utcnow()
        )
        
        self.db.add(interaction)
        
        # Mettre à jour le compteur d'interactions de la campagne
        campaign = self.db.query(Campaign).filter(
            Campaign.id == campaign_id
        ).first()
        
        if campaign:
            campaign.interaction_count += 1
        
        self.db.commit()
        self.db.refresh(interaction)
        
        logger.info(
            f"Interaction enregistrée: type={interaction_type}, "
            f"contact={contact_id}, campagne={campaign_id}"
        )
        
        return interaction
    
    def process_webhook_interaction(
        self,
        contact_phone: str,
        interaction_type: str,
        content: Optional[str] = None,
        whatsapp_message_id: Optional[str] = None,
        original_message_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Traite une interaction reçue via webhook.
        Identifie le contact et la campagne, enregistre l'interaction,
        et déclenche le Message 2 si nécessaire.
        
        Args:
            contact_phone: Numéro de téléphone du contact (format WhatsApp)
            interaction_type: Type d'interaction
            content: Contenu de l'interaction
            whatsapp_message_id: ID du message WhatsApp
            original_message_id: ID du message original (pour les réponses)
        
        Returns:
            Dictionnaire avec les résultats du traitement
        
        Exigences: 8.3, 8.4
        """
        # Trouver le contact par son numéro WhatsApp
        # Le numéro WhatsApp est sans le +, donc on cherche avec le full_number
        contact = self.db.query(Contact).filter(
            Contact.full_number.like(f"%{contact_phone}")
        ).first()
        
        if not contact:
            # Essayer avec le format +
            contact = self.db.query(Contact).filter(
                Contact.full_number == f"+{contact_phone}"
            ).first()
        
        if not contact:
            logger.warning(f"Contact non trouvé pour le numéro: {contact_phone}")
            return None
        
        # Trouver le message original si on a l'ID WhatsApp
        message = None
        campaign_id = None
        
        if original_message_id:
            message = self.db.query(Message).filter(
                Message.whatsapp_message_id == original_message_id
            ).first()
            
            if message:
                campaign_id = message.campaign_id
        
        # Si pas de message trouvé, chercher la dernière campagne active pour ce contact
        if not campaign_id:
            latest_message = self.db.query(Message).filter(
                Message.contact_id == contact.id,
                Message.message_type == "message_1",
                Message.status.in_(["sent", "delivered", "read"])
            ).order_by(Message.sent_at.desc()).first()
            
            if latest_message:
                campaign_id = latest_message.campaign_id
                message = latest_message
        
        if not campaign_id:
            logger.warning(
                f"Aucune campagne trouvée pour le contact {contact.id}"
            )
            return None
        
        # Enregistrer l'interaction
        interaction = self.log_interaction(
            contact_id=contact.id,
            campaign_id=campaign_id,
            interaction_type=interaction_type,
            content=content,
            whatsapp_message_id=whatsapp_message_id,
            message_id=message.id if message else None
        )
        
        result = {
            "interaction_id": interaction.id,
            "contact_id": contact.id,
            "campaign_id": campaign_id,
            "interaction_type": interaction_type,
            "message_2_triggered": False
        }
        
        # Déclencher le Message 2 si c'est une interaction qui le justifie
        if interaction_type in ["reply", "reaction"]:
            message_2_result = self.trigger_message_2(contact.id, campaign_id)
            if message_2_result:
                result["message_2_triggered"] = True
                result["message_2_id"] = message_2_result["message_id"]
        
        return result
    
    def update_message_status_from_webhook(
        self,
        whatsapp_message_id: str,
        new_status: str
    ) -> Optional[Message]:
        """
        Met à jour le statut d'un message à partir d'un webhook de statut.
        
        Args:
            whatsapp_message_id: ID du message WhatsApp
            new_status: Nouveau statut (delivered, read)
        
        Returns:
            Message mis à jour ou None
        """
        message = self.db.query(Message).filter(
            Message.whatsapp_message_id == whatsapp_message_id
        ).first()
        
        if not message:
            logger.debug(f"Message WhatsApp {whatsapp_message_id} non trouvé")
            return None
        
        # Mettre à jour le statut et les timestamps
        now = datetime.utcnow()
        
        if new_status == "delivered" and message.status in ["sent", "pending"]:
            message.status = "delivered"
            message.delivered_at = now
        elif new_status == "read" and message.status in ["sent", "delivered", "pending"]:
            message.status = "read"
            message.read_at = now
            if not message.delivered_at:
                message.delivered_at = now
        
        self.db.commit()
        self.db.refresh(message)
        
        logger.info(
            f"Message {message.id} mis à jour: status={message.status}"
        )
        
        return message


def get_automation_service(db: Session) -> AutomationService:
    """Factory function pour créer une instance du service"""
    return AutomationService(db)
