"""
Schémas Pydantic pour les utilisateurs
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator
import re


def validate_email_format(email: str) -> str:
    """Validation d'email plus permissive pour le développement"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValueError('Format d\'email invalide')
    return email.lower()


class UserBase(BaseModel):
    """Schéma de base pour les utilisateurs"""
    email: str
    role: str = Field(..., pattern="^(super_admin|admin)$")
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        return validate_email_format(v)


class UserCreate(UserBase):
    """Schéma pour la création d'un utilisateur"""
    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseModel):
    """Schéma pour la mise à jour d'un utilisateur"""
    email: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    is_active: Optional[bool] = None
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return validate_email_format(v)


class UserResponse(UserBase):
    """Schéma de réponse pour un utilisateur"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserInDB(UserResponse):
    """Schéma utilisateur avec hash du mot de passe (usage interne)"""
    password_hash: str
