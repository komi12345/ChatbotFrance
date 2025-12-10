"""
Schémas Pydantic pour l'authentification
"""
from typing import Optional
from pydantic import BaseModel, field_validator
import re


class LoginRequest(BaseModel):
    """Schéma pour la requête de connexion"""
    email: str
    password: str
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validation d'email plus permissive pour le développement"""
        # Pattern simple pour valider le format email
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, v):
            raise ValueError('Format d\'email invalide')
        return v.lower()


class Token(BaseModel):
    """Schéma pour le token JWT"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int  # Durée en secondes


class TokenData(BaseModel):
    """Schéma pour les données contenues dans le token"""
    user_id: Optional[int] = None
    email: Optional[str] = None
    role: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    """Schéma pour la requête de rafraîchissement du token"""
    refresh_token: str
