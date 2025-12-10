"""
Routes d'authentification - Login, refresh token, profil utilisateur
Utilise le client Supabase pour les opérations de base de données
"""
from datetime import timedelta
from typing import Annotated, Optional, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from app.config import settings
from app.supabase_client import SupabaseDB, get_supabase_db
from app.schemas.auth import Token, LoginRequest, RefreshTokenRequest
from app.schemas.user import UserResponse
from app.services.auth_service import get_current_user
from app.utils.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    verify_password,
)


class LoginResponse(BaseModel):
    """Réponse de connexion avec token et utilisateur"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


router = APIRouter(prefix="/auth", tags=["Authentification"])


def authenticate_user(db: SupabaseDB, email: str, password: str) -> Optional[Dict]:
    """
    Authentifie un utilisateur avec son email et mot de passe.
    """
    user = db.get_user_by_email(email)
    
    if not user:
        return None
    
    if not user.get("is_active", True):
        return None
    
    if not verify_password(password, user.get("password_hash", "")):
        return None
    
    return user


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    db: SupabaseDB = Depends(get_supabase_db)
) -> LoginResponse:
    """
    Authentifie un utilisateur et retourne un token JWT avec les infos utilisateur.
    """
    user = authenticate_user(db, login_data.email, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Créer le token d'accès
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "user_id": user["id"],
            "email": user["email"],
            "role": user["role"],
        },
        expires_delta=access_token_expires
    )
    
    # Créer le token de rafraîchissement
    refresh_token = create_refresh_token(
        data={
            "user_id": user["id"],
            "email": user["email"],
            "role": user["role"],
        }
    )
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse(
            id=user["id"],
            email=user["email"],
            role=user["role"],
            is_active=user.get("is_active", True),
            created_at=user.get("created_at"),
            updated_at=user.get("updated_at")
        )
    )


@router.post("/login/form", response_model=Token)
async def login_form(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: SupabaseDB = Depends(get_supabase_db)
) -> Token:
    """
    Authentifie un utilisateur via formulaire OAuth2 (pour Swagger UI).
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "user_id": user["id"],
            "email": user["email"],
            "role": user["role"],
        },
        expires_delta=access_token_expires
    )
    
    refresh_token = create_refresh_token(
        data={
            "user_id": user["id"],
            "email": user["email"],
            "role": user["role"],
        }
    )
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: SupabaseDB = Depends(get_supabase_db)
) -> Token:
    """
    Rafraîchit un token JWT expiré.
    """
    payload = decode_refresh_token(refresh_data.refresh_token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de rafraîchissement invalide ou expiré",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("user_id")
    user = db.get_user_by_id(user_id)
    
    if not user or not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur non trouvé ou inactif",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "user_id": user["id"],
            "email": user["email"],
            "role": user["role"],
        },
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: Dict = Depends(get_current_user)
) -> UserResponse:
    """
    Retourne les informations de l'utilisateur connecté.
    """
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        role=current_user["role"],
        is_active=current_user.get("is_active", True),
        created_at=current_user.get("created_at"),
        updated_at=current_user.get("updated_at")
    )
