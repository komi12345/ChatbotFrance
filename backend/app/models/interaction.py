"""
Modèle Interaction - Enregistrement des webhooks WhatsApp reçus
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Interaction(Base):
    """
    Modèle interaction pour enregistrer les webhooks WhatsApp.
    Capture les réponses, réactions et statuts de lecture des contacts.
    """
    __tablename__ = "interactions"
    
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="CASCADE"))
    contact_id = Column(Integer, ForeignKey("contacts.id", ondelete="CASCADE"))
    message_id = Column(Integer, ForeignKey("messages.id", ondelete="SET NULL"), nullable=True)
    interaction_type = Column(String(50))  # 'reply', 'reaction', 'read', 'delivered'
    content = Column(Text)  # Contenu de la réponse si applicable
    whatsapp_message_id = Column(String(255))  # ID du message WhatsApp
    received_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    campaign = relationship("Campaign", back_populates="interactions")
    contact = relationship("Contact", back_populates="interactions")
    message = relationship("Message", back_populates="interactions")
    
    def __repr__(self):
        return f"<Interaction(id={self.id}, type='{self.interaction_type}')>"
    
    @property
    def is_reply(self) -> bool:
        """Vérifie si c'est une réponse du contact"""
        return self.interaction_type == "reply"
    
    @property
    def is_reaction(self) -> bool:
        """Vérifie si c'est une réaction"""
        return self.interaction_type == "reaction"
    
    @property
    def triggers_message_2(self) -> bool:
        """Vérifie si cette interaction doit déclencher le Message 2"""
        return self.interaction_type in ["reply", "reaction"]
