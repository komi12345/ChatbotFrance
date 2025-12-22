"""
Configuration de l'application - Chargement des variables d'environnement
"""
import os
import sys
from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    """Configuration de l'application via variables d'environnement"""
    
    # Environnement
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api"
    
    # Supabase / PostgreSQL
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    DATABASE_URL: str
    
    # ==========================================================================
    # WASSENGER API 2025 - NOUVELLE INTÉGRATION
    # ==========================================================================
    # Clé API Wassenger (obligatoire)
    # Trouvez-la dans : Wassenger Dashboard > Settings > API Keys
    WASSENGER_API_KEY: str = ""
    # ID de l'appareil WhatsApp connecté (obligatoire)
    # Trouvez-le dans : Wassenger Dashboard > Devices
    WASSENGER_DEVICE_ID: str = ""
    # URL du webhook pour recevoir les notifications Wassenger
    # En développement local avec ngrok : https://votre-url.ngrok.io/api/webhooks/wassenger
    WASSENGER_WEBHOOK_URL: str = ""
    
    # ==========================================================================
    # TWILIO WHATSAPP SANDBOX (DÉPRÉCIÉ - conservé pour rétrocompatibilité)
    # ==========================================================================
    # Account SID Twilio (déprécié)
    # Trouvez-le dans : Twilio Console > Account Info
    TWILIO_ACCOUNT_SID: str = ""
    # Auth Token Twilio (déprécié, secret)
    # Trouvez-le dans : Twilio Console > Account Info
    TWILIO_AUTH_TOKEN: str = ""
    # Numéro Sandbox Twilio (par défaut: +14155238886)
    TWILIO_SANDBOX_NUMBER: str = "+14155238886"
    # URL de base pour les webhooks (pour validation de signature)
    TWILIO_WEBHOOK_BASE_URL: str = ""
    
    # ==========================================================================
    # ANCIENNES VARIABLES META (conservées pour rétrocompatibilité)
    # ==========================================================================
    # WhatsApp Business API (Meta Cloud API) - DÉPRÉCIÉ
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_ACCESS_TOKEN: str = ""
    WHATSAPP_WEBHOOK_VERIFY_TOKEN: str = ""
    WHATSAPP_API_VERSION: str = "v18.0"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 heures - sessions longues pour admin/super_admin
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000"
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    WHATSAPP_RATE_LIMIT_PER_MINUTE: int = 25
    
    # Retry Configuration
    MAX_RETRY_ATTEMPTS: int = 3
    RETRY_BASE_DELAY_SECONDS: int = 60
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Retourne la liste des origines CORS autorisées"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    def validate_wassenger_config(self) -> None:
        """
        Valide que les variables Wassenger obligatoires sont configurées.
        Affiche une erreur explicite si une variable est manquante ou vide.
        
        Raises:
            ValueError: Si une variable obligatoire est manquante ou vide
        """
        missing_vars = []
        
        # Vérifier que les valeurs ne sont pas vides ou composées uniquement d'espaces
        if not self.WASSENGER_API_KEY or not self.WASSENGER_API_KEY.strip():
            missing_vars.append("WASSENGER_API_KEY")
        if not self.WASSENGER_DEVICE_ID or not self.WASSENGER_DEVICE_ID.strip():
            missing_vars.append("WASSENGER_DEVICE_ID")
        
        if missing_vars:
            error_msg = (
                f"\n{'='*60}\n"
                f"ERREUR DE CONFIGURATION WASSENGER\n"
                f"{'='*60}\n"
                f"Les variables d'environnement suivantes sont obligatoires :\n"
            )
            for var in missing_vars:
                error_msg += f"  - {var}\n"
            error_msg += (
                f"\nVeuillez les définir dans votre fichier .env\n"
                f"Consultez .env.example pour plus d'informations.\n"
                f"{'='*60}\n"
            )
            raise ValueError(error_msg)
    
    def validate_twilio_config(self) -> None:
        """
        Valide que les variables Twilio obligatoires sont configurées.
        DÉPRÉCIÉ : Conservé pour rétrocompatibilité.
        
        Raises:
            ValueError: Si une variable obligatoire est manquante
        """
        missing_vars = []
        
        if not self.TWILIO_ACCOUNT_SID:
            missing_vars.append("TWILIO_ACCOUNT_SID")
        if not self.TWILIO_AUTH_TOKEN:
            missing_vars.append("TWILIO_AUTH_TOKEN")
        
        if missing_vars:
            error_msg = (
                f"\n{'='*60}\n"
                f"ERREUR DE CONFIGURATION TWILIO\n"
                f"{'='*60}\n"
                f"Les variables d'environnement suivantes sont obligatoires :\n"
            )
            for var in missing_vars:
                error_msg += f"  - {var}\n"
            error_msg += (
                f"\nVeuillez les définir dans votre fichier .env\n"
                f"Consultez .env.example pour plus d'informations.\n"
                f"{'='*60}\n"
            )
            raise ValueError(error_msg)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Retourne l'instance de configuration (singleton avec cache)"""
    return Settings()


def validate_config_on_startup() -> None:
    """
    Valide la configuration au démarrage de l'application.
    Appelée depuis main.py pour vérifier les variables obligatoires.
    Utilise maintenant Wassenger au lieu de Twilio.
    """
    config = get_settings()
    config.validate_wassenger_config()


# Instance globale pour import facile
settings = get_settings()
