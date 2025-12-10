"""
Modèle User - Gestion des utilisateurs (Super Admin et Admin)
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    """
    Modèle utilisateur avec deux rôles possibles:
    - super_admin: Accès complet incluant la gestion des Admins
    - admin: Accès au dashboard sans gestion d'autres utilisateurs
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)  # 'super_admin' ou 'admin'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    categories = relationship("Category", back_populates="creator")
    contacts = relationship("Contact", back_populates="creator")
    campaigns = relationship("Campaign", back_populates="creator")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"
    
    @property
    def is_super_admin(self) -> bool:
        """Vérifie si l'utilisateur est Super Admin"""
        return self.role == "super_admin"
    
    @property
    def is_admin(self) -> bool:
        """Vérifie si l'utilisateur est Admin"""
        return self.role == "admin"
