"""
Schémas Pydantic pour les catégories
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class CategoryBase(BaseModel):
    """Schéma de base pour les catégories"""
    name: str = Field(..., min_length=1, max_length=255)
    color: Optional[str] = Field(None, max_length=50)


class CategoryCreate(CategoryBase):
    """Schéma pour la création d'une catégorie"""
    pass


class CategoryUpdate(BaseModel):
    """Schéma pour la mise à jour d'une catégorie"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    color: Optional[str] = Field(None, max_length=50)


class CategoryResponse(CategoryBase):
    """Schéma de réponse pour une catégorie"""
    id: int
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    contact_count: int = 0
    
    class Config:
        from_attributes = True


class CategoryWithContacts(CategoryResponse):
    """Schéma de catégorie avec la liste des contacts"""
    contacts: List["ContactBrief"] = []


class ContactBrief(BaseModel):
    """Schéma bref pour un contact (utilisé dans les relations)"""
    id: int
    full_number: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    whatsapp_verified: Optional[bool] = None
    
    class Config:
        from_attributes = True


# Mise à jour des références forward
CategoryWithContacts.model_rebuild()
