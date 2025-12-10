"""
Modèle Campaign - Gestion des campagnes d'envoi de messages
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.category import campaign_categories


class Campaign(Base):
    """
    Modèle campagne représentant un envoi de messages à une ou plusieurs catégories.
    Gère le Message 1 (template) et le Message 2 (suivi automatique).
    """
    __tablename__ = "campaigns"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    message_1 = Column(Text, nullable=False)  # Message initial (template WhatsApp)
    message_2 = Column(Text)  # Message de suivi automatique
    template_name = Column(String(100))  # Nom du template Meta approuvé
    status = Column(String(50), default="draft")  # draft, sending, completed, failed
    total_recipients = Column(Integer, default=0)
    sent_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    interaction_count = Column(Integer, default=0)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    creator = relationship("User", back_populates="campaigns")
    categories = relationship(
        "Category",
        secondary=campaign_categories,
        back_populates="campaigns"
    )
    messages = relationship("Message", back_populates="campaign")
    interactions = relationship("Interaction", back_populates="campaign")
    
    def __repr__(self):
        return f"<Campaign(id={self.id}, name='{self.name}', status='{self.status}')>"
    
    @property
    def success_rate(self) -> float:
        """Calcule le taux de réussite de la campagne"""
        if self.total_recipients == 0:
            return 0.0
        return (self.success_count / self.total_recipients) * 100
    
    @property
    def is_completed(self) -> bool:
        """Vérifie si la campagne est terminée"""
        return self.status == "completed"
    
    @property
    def is_sending(self) -> bool:
        """Vérifie si la campagne est en cours d'envoi"""
        return self.status == "sending"
