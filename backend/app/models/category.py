"""
Modèle Category - Gestion des catégories de contacts
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.database import Base


# Table de jonction pour la relation many-to-many entre Category et Contact
category_contacts = Table(
    "category_contacts",
    Base.metadata,
    Column("id", Integer, primary_key=True),
    Column("category_id", Integer, ForeignKey("categories.id", ondelete="CASCADE")),
    Column("contact_id", Integer, ForeignKey("contacts.id", ondelete="CASCADE")),
    Column("added_at", DateTime, default=datetime.utcnow),
)

# Table de jonction pour la relation many-to-many entre Campaign et Category
campaign_categories = Table(
    "campaign_categories",
    Base.metadata,
    Column("id", Integer, primary_key=True),
    Column("campaign_id", Integer, ForeignKey("campaigns.id", ondelete="CASCADE")),
    Column("category_id", Integer, ForeignKey("categories.id", ondelete="CASCADE")),
)


class Category(Base):
    """
    Modèle catégorie pour regrouper les contacts.
    Chaque catégorie peut contenir plusieurs contacts et être utilisée dans plusieurs campagnes.
    """
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    color = Column(String(50))  # Couleur pour l'affichage avec gradient
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    creator = relationship("User", back_populates="categories")
    contacts = relationship(
        "Contact",
        secondary=category_contacts,
        back_populates="categories"
    )
    campaigns = relationship(
        "Campaign",
        secondary=campaign_categories,
        back_populates="categories"
    )
    
    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}')>"
    
    @property
    def contact_count(self) -> int:
        """Retourne le nombre de contacts dans la catégorie"""
        return len(self.contacts) if self.contacts else 0
