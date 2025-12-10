"""
Modèle Message - Tracking individuel des messages envoyés
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Message(Base):
    """
    Modèle message pour le tracking individuel de chaque envoi.
    Enregistre le statut, les timestamps et les informations de retry.
    """
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="CASCADE"))
    contact_id = Column(Integer, ForeignKey("contacts.id", ondelete="CASCADE"))
    message_type = Column(String(20))  # 'message_1' ou 'message_2'
    content = Column(Text, nullable=False)
    status = Column(String(50), default="pending")  # pending, sent, delivered, read, failed
    whatsapp_message_id = Column(String(255))  # ID retourné par WhatsApp API
    error_message = Column(Text)  # Message d'erreur en cas d'échec
    retry_count = Column(Integer, default=0)
    sent_at = Column(DateTime)
    delivered_at = Column(DateTime)
    read_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    campaign = relationship("Campaign", back_populates="messages")
    contact = relationship("Contact", back_populates="messages")
    interactions = relationship("Interaction", back_populates="message")
    
    def __repr__(self):
        return f"<Message(id={self.id}, type='{self.message_type}', status='{self.status}')>"
    
    @property
    def is_sent(self) -> bool:
        """Vérifie si le message a été envoyé"""
        return self.status in ["sent", "delivered", "read"]
    
    @property
    def is_failed(self) -> bool:
        """Vérifie si le message a échoué"""
        return self.status == "failed"
    
    @property
    def can_retry(self) -> bool:
        """Vérifie si le message peut être réessayé (max 3 tentatives)"""
        return self.is_failed and self.retry_count < 3
    
    @property
    def is_message_1(self) -> bool:
        """Vérifie si c'est un Message 1 (initial)"""
        return self.message_type == "message_1"
    
    @property
    def is_message_2(self) -> bool:
        """Vérifie si c'est un Message 2 (suivi)"""
        return self.message_type == "message_2"
