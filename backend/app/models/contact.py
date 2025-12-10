"""
Modèle Contact - Gestion des contacts WhatsApp
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.category import category_contacts


class Contact(Base):
    """
    Modèle contact représentant un numéro WhatsApp.
    Stocke le numéro avec l'indicatif pays pour le format international.
    """
    __tablename__ = "contacts"
    
    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(20), nullable=False)  # Numéro sans indicatif
    country_code = Column(String(5), nullable=False)   # Indicatif pays (ex: +33)
    full_number = Column(String(25), unique=True, nullable=False, index=True)  # Numéro complet
    first_name = Column(String(100))
    last_name = Column(String(100))
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # WhatsApp verification fields
    whatsapp_verified = Column(Boolean, nullable=True, default=None)  # True=verified, False=not WhatsApp, None=pending
    verified_at = Column(DateTime, nullable=True, default=None)  # Timestamp of last verification
    
    # Relations
    creator = relationship("User", back_populates="contacts")
    categories = relationship(
        "Category",
        secondary=category_contacts,
        back_populates="contacts"
    )
    messages = relationship("Message", back_populates="contact")
    interactions = relationship("Interaction", back_populates="contact")
    
    def __repr__(self):
        return f"<Contact(id={self.id}, full_number='{self.full_number}')>"
    
    @property
    def display_name(self) -> str:
        """Retourne le nom complet ou le numéro si pas de nom"""
        if self.first_name or self.last_name:
            return f"{self.first_name or ''} {self.last_name or ''}".strip()
        return self.full_number
    
    @property
    def whatsapp_id(self) -> str:
        """Retourne l'ID WhatsApp (numéro sans le +)"""
        return self.full_number.replace("+", "")
