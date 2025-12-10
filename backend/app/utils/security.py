"""
Utilitaires de sécurité - JWT, hashage de mots de passe, validation
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from jose import JWTError, jwt
import bcrypt

from app.config import settings


def hash_password(password: str) -> str:
    """
    Hash un mot de passe avec bcrypt.
    
    Args:
        password: Le mot de passe en clair
        
    Returns:
        Le hash bcrypt du mot de passe
    """
    # Encoder le mot de passe en bytes et générer le hash
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Vérifie si un mot de passe correspond à son hash.
    
    Args:
        plain_password: Le mot de passe en clair
        hashed_password: Le hash bcrypt à vérifier
        
    Returns:
        True si le mot de passe correspond, False sinon
    """
    try:
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Crée un token JWT d'accès.
    
    Args:
        data: Les données à encoder dans le token (user_id, email, role)
        expires_delta: Durée de validité optionnelle (défaut: 30 minutes)
        
    Returns:
        Le token JWT encodé
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Crée un token JWT de rafraîchissement.
    
    Args:
        data: Les données à encoder dans le token
        expires_delta: Durée de validité optionnelle (défaut: 7 jours)
        
    Returns:
        Le token JWT de rafraîchissement encodé
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Décode et valide un token JWT.
    
    Args:
        token: Le token JWT à décoder
        
    Returns:
        Les données du token si valide, None sinon
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def decode_refresh_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Décode et valide un token de rafraîchissement.
    
    Args:
        token: Le token de rafraîchissement à décoder
        
    Returns:
        Les données du token si valide et de type refresh, None sinon
    """
    payload = decode_token(token)
    
    if payload is None:
        return None
    
    # Vérifier que c'est bien un token de rafraîchissement
    if payload.get("type") != "refresh":
        return None
    
    return payload
