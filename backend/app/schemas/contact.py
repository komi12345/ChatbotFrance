"""
Schémas Pydantic pour les contacts
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class ContactBase(BaseModel):
    """Schéma de base pour les contacts"""
    phone_number: str = Field(..., min_length=1, max_length=20)
    country_code: str = Field(..., pattern=r"^\+\d{1,4}$")
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)


class ContactCreate(ContactBase):
    """Schéma pour la création d'un contact"""
    category_ids: Optional[List[int]] = []
    
    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        """Valide que le numéro ne contient que des chiffres"""
        cleaned = v.replace(" ", "").replace("-", "")
        if not cleaned.isdigit():
            raise ValueError("Le numéro de téléphone ne doit contenir que des chiffres")
        return cleaned


class ContactUpdate(BaseModel):
    """Schéma pour la mise à jour d'un contact"""
    phone_number: Optional[str] = Field(None, min_length=1, max_length=20)
    country_code: Optional[str] = Field(None, pattern=r"^\+\d{1,4}$")
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    category_ids: Optional[List[int]] = None


class ContactResponse(BaseModel):
    """Schéma de réponse pour un contact"""
    id: int
    phone_number: str
    country_code: str
    full_number: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    whatsapp_verified: Optional[bool] = None  # True=verified, False=not WhatsApp, None=pending
    verified_at: Optional[datetime] = None  # Timestamp of last verification
    
    class Config:
        from_attributes = True


class ContactWithCategories(ContactResponse):
    """Schéma de contact avec ses catégories"""
    categories: List["CategoryBrief"] = []


class CategoryBrief(BaseModel):
    """Schéma bref pour une catégorie (utilisé dans les relations)"""
    id: int
    name: str
    color: Optional[str] = None
    
    class Config:
        from_attributes = True


class ContactImport(BaseModel):
    """Schéma pour l'import CSV de contacts"""
    phone_number: str
    country_code: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class ContactImportResult(BaseModel):
    """Schéma pour le résultat d'import CSV"""
    total: int
    success: int
    failed: int
    skipped: int = 0  # Nombre de doublons ignorés
    errors: List[str] = []


# Mise à jour des références forward
ContactWithCategories.model_rebuild()
