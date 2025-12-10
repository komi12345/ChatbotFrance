"""
Service d'authentification - Logique métier pour l'authentification
Utilise le client Supabase pour les opérations de base de données
"""
from typing import Optional, Dict

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.supabase_client import SupabaseDB, get_supabase_db
from app.utils.security import verify_password, decode_token

# Configuration OAuth2 pour récupérer le token depuis le header Authorization
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login/form")


def authenticate_user(db: SupabaseDB, email: str, password: str) -> Optional[Dict]:
    """
    Authentifie un utilisateur avec son email et mot de passe.
    
    Args:
        db: Instance SupabaseDB
        email: Email de l'utilisateur
        password: Mot de passe en clair
        
    Returns:
        L'utilisateur si authentification réussie, None sinon
    """
    user = db.get_user_by_email(email)
    
    if not user:
        return None
    
    if not user.get("is_active", True):
        return None
    
    if not verify_password(password, user.get("password_hash", "")):
        return None
    
    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: SupabaseDB = Depends(get_supabase_db)
) -> Dict:
    """
    Récupère l'utilisateur courant à partir du token JWT.
    Utilisé comme dépendance FastAPI pour protéger les routes.
    
    Args:
        token: Token JWT extrait du header Authorization
        db: Instance SupabaseDB
        
    Returns:
        L'utilisateur authentifié (dict)
        
    Raises:
        HTTPException 401: Si le token est invalide ou l'utilisateur non trouvé
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Identifiants invalides",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Décoder le token
    payload = decode_token(token)
    
    if payload is None:
        raise credentials_exception
    
    # Extraire les données du token
    user_id: int = payload.get("user_id")
    email: str = payload.get("email")
    
    if user_id is None or email is None:
        raise credentials_exception
    
    # Récupérer l'utilisateur depuis la base de données
    user = db.get_user_by_id(user_id)
    
    if user is None:
        raise credentials_exception
    
    # Vérifier que l'utilisateur est toujours actif
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Compte utilisateur désactivé",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_active_user(
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    """
    Vérifie que l'utilisateur courant est actif.
    """
    if not current_user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Utilisateur inactif"
        )
    return current_user


def verify_super_admin(user: Dict) -> bool:
    """
    Vérifie si l'utilisateur est un Super Admin.
    """
    return user.get("role") == "super_admin"


async def get_current_super_admin(
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    """
    Vérifie que l'utilisateur courant est un Super Admin.
    """
    if not verify_super_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux Super Admins"
        )
    return current_user
