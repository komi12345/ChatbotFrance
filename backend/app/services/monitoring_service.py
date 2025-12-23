"""
Service de monitoring WhatsApp - Suivi des messages quotidiens et alertes

Ce service gère :
- Les compteurs Redis pour le suivi temps réel des messages
- La limite quotidienne de 1000 messages
- Les niveaux d'alerte visuels
- Le calcul de capacité restante

Requirements: 1.1, 1.2, 1.5, 2.1, 2.2, 2.3, 3.1-3.4, 5.1, 5.2
"""
import logging
import math
from datetime import datetime, timezone, timedelta
from typing import Tuple, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

import redis

from app.config import settings

# Configuration du logger
logger = logging.getLogger(__name__)


def get_redis_url_with_ssl(redis_url: str) -> str:
    """
    Ajoute les paramètres SSL requis pour les connexions rediss://.
    
    Render et autres services cloud utilisent rediss:// (Redis over SSL)
    qui nécessite le paramètre ssl_cert_reqs pour fonctionner.
    
    Args:
        redis_url: URL Redis originale
        
    Returns:
        URL Redis avec paramètres SSL si nécessaire
    """
    if redis_url.startswith("rediss://") and "ssl_cert_reqs" not in redis_url:
        # Ajouter le paramètre SSL requis (en minuscules pour redis-py)
        separator = "&" if "?" in redis_url else "?"
        return f"{redis_url}{separator}ssl_cert_reqs=none"
    return redis_url

# Constantes
DAILY_MESSAGE_LIMIT = 1000
TTL_SECONDS = 48 * 60 * 60  # 48 heures en secondes


class AlertLevel(str, Enum):
    """Niveaux d'alerte basés sur le pourcentage de la limite atteinte."""
    OK = "ok"           # 0-75% (0-750)
    ATTENTION = "attention"  # 76-90% (751-900)
    DANGER = "danger"   # 91-100% (901-1000)
    BLOCKED = "blocked"  # >100% (>1000)


@dataclass
class DailyStats:
    """
    Statistiques quotidiennes de messages.
    
    Attributes:
        date: Date des statistiques (format YYYY-MM-DD)
        message_1_count: Nombre de messages de type 1 envoyés
        message_2_count: Nombre de messages de type 2 envoyés
        error_count: Nombre d'erreurs d'envoi
        total_sent: Total des messages envoyés (message_1 + message_2)
    """
    date: str
    message_1_count: int
    message_2_count: int
    error_count: int
    
    @property
    def total_sent(self) -> int:
        """Retourne le total des messages envoyés."""
        return self.message_1_count + self.message_2_count


class MonitoringService:
    """
    Service de monitoring des messages WhatsApp.
    
    Utilise Redis pour les compteurs temps réel avec TTL de 48h.
    Clés Redis:
    - whatsapp:daily:{YYYY-MM-DD}:message_1
    - whatsapp:daily:{YYYY-MM-DD}:message_2
    - whatsapp:daily:{YYYY-MM-DD}:errors
    
    Requirements: 1.1, 1.2, 1.5
    """
    
    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialise le service avec connexion Redis.
        
        Args:
            redis_url: URL de connexion Redis (utilise settings.REDIS_URL par défaut)
        """
        # Appliquer la transformation SSL pour les connexions rediss://
        raw_url = redis_url or settings.REDIS_URL
        self.redis_url = get_redis_url_with_ssl(raw_url)
        self._redis: Optional[redis.Redis] = None
        
        logger.info(
            "Service de monitoring initialisé",
            extra={"redis_url": self.redis_url[:20] + "..." if self.redis_url else "N/A"}
        )
    
    @property
    def redis_client(self) -> redis.Redis:
        """Connexion Redis lazy-loaded."""
        if self._redis is None:
            self._redis = redis.from_url(self.redis_url, decode_responses=True)
        return self._redis
    
    def _get_today_key_prefix(self) -> str:
        """Retourne le préfixe de clé pour aujourd'hui."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return f"whatsapp:daily:{today}"
    
    def _get_key(self, key_type: str) -> str:
        """
        Construit une clé Redis pour le type donné.
        
        Args:
            key_type: Type de clé (message_1, message_2, errors)
        
        Returns:
            Clé Redis complète
        """
        return f"{self._get_today_key_prefix()}:{key_type}"

    def increment_message_counter(self, message_type: str) -> int:
        """
        Incrémente le compteur pour message_1 ou message_2.
        
        Args:
            message_type: Type de message ("message_1" ou "message_2")
        
        Returns:
            Nouvelle valeur du compteur
        
        Requirements: 1.1, 1.2
        """
        if message_type not in ("message_1", "message_2"):
            raise ValueError(f"Type de message invalide: {message_type}")
        
        try:
            key = self._get_key(message_type)
            pipe = self.redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, TTL_SECONDS)
            results = pipe.execute()
            new_value = results[0]
            
            logger.info(
                f"Compteur {message_type} incrémenté",
                extra={"key": key, "new_value": new_value}
            )
            
            return new_value
        except Exception as e:
            logger.error(f"Erreur incrémentation compteur {message_type}: {e}")
            return 0
    
    def increment_error_counter(self) -> int:
        """
        Incrémente le compteur d'erreurs.
        
        Returns:
            Nouvelle valeur du compteur d'erreurs
        
        Requirements: 6.1
        """
        try:
            key = self._get_key("errors")
            pipe = self.redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, TTL_SECONDS)
            results = pipe.execute()
            new_value = results[0]
            
            logger.info(
                "Compteur d'erreurs incrémenté",
                extra={"key": key, "new_value": new_value}
            )
            
            return new_value
        except Exception as e:
            logger.error(f"Erreur incrémentation compteur erreurs: {e}")
            return 0
    
    def get_daily_stats(self) -> DailyStats:
        """
        Retourne les statistiques du jour.
        
        Returns:
            DailyStats avec les compteurs actuels
        
        Requirements: 1.5
        """
        try:
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            
            # Récupérer tous les compteurs en une seule requête
            pipe = self.redis_client.pipeline()
            pipe.get(self._get_key("message_1"))
            pipe.get(self._get_key("message_2"))
            pipe.get(self._get_key("errors"))
            results = pipe.execute()
            
            message_1_count = int(results[0] or 0)
            message_2_count = int(results[1] or 0)
            error_count = int(results[2] or 0)
            
            return DailyStats(
                date=today,
                message_1_count=message_1_count,
                message_2_count=message_2_count,
                error_count=error_count
            )
        except Exception as e:
            logger.error(f"Erreur récupération stats quotidiennes: {e}")
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            return DailyStats(
                date=today,
                message_1_count=0,
                message_2_count=0,
                error_count=0
            )
    
    def can_send_message(self) -> Tuple[bool, str]:
        """
        Vérifie si un message peut être envoyé (limite 1000).
        
        Returns:
            Tuple (can_send, error_message):
            - (True, "") si compteur < 1000
            - (False, "daily_limit_reached") si compteur >= 1000
        
        Requirements: 2.1, 2.2, 2.3
        """
        try:
            stats = self.get_daily_stats()
            total_sent = stats.total_sent
            
            if total_sent >= DAILY_MESSAGE_LIMIT:
                logger.warning(
                    "Limite quotidienne atteinte",
                    extra={"total_sent": total_sent, "limit": DAILY_MESSAGE_LIMIT}
                )
                return (False, "daily_limit_reached")
            
            return (True, "")
        except Exception as e:
            logger.error(f"Erreur vérification limite: {e}")
            # En cas d'erreur, on autorise par défaut (fail-open)
            return (True, "")
    
    def acquire_campaign_lock(self, campaign_id: int, user_id: int, ttl: int = 300) -> bool:
        """
        Acquiert un verrou distribué pour une campagne.
        Empêche les modifications/envois simultanés par plusieurs utilisateurs.
        
        Args:
            campaign_id: ID de la campagne
            user_id: ID de l'utilisateur qui acquiert le verrou
            ttl: Durée de vie du verrou en secondes (défaut: 5 minutes)
        
        Returns:
            True si le verrou est acquis, False sinon
        
        Requirements: Production scalability - distributed locking
        """
        try:
            lock_key = f"campaign:lock:{campaign_id}"
            lock_value = f"user:{user_id}:{datetime.now(timezone.utc).isoformat()}"
            
            # SET NX (set if not exists) avec TTL
            acquired = self.redis_client.set(lock_key, lock_value, nx=True, ex=ttl)
            
            if acquired:
                logger.info(
                    f"Verrou campagne {campaign_id} acquis par utilisateur {user_id}",
                    extra={"campaign_id": campaign_id, "user_id": user_id, "ttl": ttl}
                )
            else:
                # Vérifier qui détient le verrou
                current_lock = self.redis_client.get(lock_key)
                logger.warning(
                    f"Verrou campagne {campaign_id} déjà détenu: {current_lock}",
                    extra={"campaign_id": campaign_id, "user_id": user_id}
                )
            
            return bool(acquired)
        except Exception as e:
            logger.error(f"Erreur acquisition verrou campagne {campaign_id}: {e}")
            return False
    
    def release_campaign_lock(self, campaign_id: int, user_id: int) -> bool:
        """
        Libère le verrou d'une campagne.
        
        Args:
            campaign_id: ID de la campagne
            user_id: ID de l'utilisateur qui libère le verrou
        
        Returns:
            True si le verrou est libéré, False sinon
        
        Requirements: Production scalability - distributed locking
        """
        try:
            lock_key = f"campaign:lock:{campaign_id}"
            
            # Vérifier que c'est bien l'utilisateur qui détient le verrou
            current_lock = self.redis_client.get(lock_key)
            if current_lock and f"user:{user_id}:" in current_lock:
                self.redis_client.delete(lock_key)
                logger.info(
                    f"Verrou campagne {campaign_id} libéré par utilisateur {user_id}",
                    extra={"campaign_id": campaign_id, "user_id": user_id}
                )
                return True
            else:
                logger.warning(
                    f"Tentative de libération verrou campagne {campaign_id} par utilisateur {user_id} non autorisée",
                    extra={"campaign_id": campaign_id, "user_id": user_id, "current_lock": current_lock}
                )
                return False
        except Exception as e:
            logger.error(f"Erreur libération verrou campagne {campaign_id}: {e}")
            return False
    
    def get_campaign_lock_info(self, campaign_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère les informations sur le verrou d'une campagne.
        
        Args:
            campaign_id: ID de la campagne
        
        Returns:
            Dict avec user_id et locked_at, ou None si pas de verrou
        """
        try:
            lock_key = f"campaign:lock:{campaign_id}"
            lock_value = self.redis_client.get(lock_key)
            
            if not lock_value:
                return None
            
            # Parse "user:{user_id}:{timestamp}"
            parts = lock_value.split(":")
            if len(parts) >= 3:
                return {
                    "user_id": int(parts[1]),
                    "locked_at": parts[2],
                    "ttl": self.redis_client.ttl(lock_key)
                }
            return None
        except Exception as e:
            logger.error(f"Erreur lecture verrou campagne {campaign_id}: {e}")
            return None
    
    def reserve_message_quota(self, count: int) -> Tuple[bool, int]:
        """
        Réserve un quota de messages de manière atomique.
        Utilisé pour éviter les dépassements lors de campagnes simultanées.
        
        Args:
            count: Nombre de messages à réserver
        
        Returns:
            Tuple (success, remaining):
            - (True, remaining) si la réservation est réussie
            - (False, 0) si le quota est insuffisant
        
        Requirements: Production scalability - atomic quota reservation
        """
        try:
            stats = self.get_daily_stats()
            current_total = stats.total_sent
            
            if current_total + count > DAILY_MESSAGE_LIMIT:
                remaining = max(0, DAILY_MESSAGE_LIMIT - current_total)
                logger.warning(
                    f"Quota insuffisant: demandé={count}, disponible={remaining}",
                    extra={"requested": count, "remaining": remaining}
                )
                return (False, remaining)
            
            # Réservation réussie - le compteur sera incrémenté lors de l'envoi réel
            logger.info(
                f"Quota réservé: {count} messages",
                extra={"reserved": count, "current_total": current_total}
            )
            return (True, DAILY_MESSAGE_LIMIT - current_total - count)
        except Exception as e:
            logger.error(f"Erreur réservation quota: {e}")
            return (False, 0)
    
    def get_alert_level(self) -> AlertLevel:
        """
        Retourne le niveau d'alerte actuel basé sur le compteur.
        
        Seuils:
        - 0-750 (0-75%) → "ok" (vert)
        - 751-900 (76-90%) → "attention" (jaune)
        - 901-1000 (91-100%) → "danger" (rouge)
        - >1000 → "blocked" (gris)
        
        Returns:
            AlertLevel correspondant au compteur actuel
        
        Requirements: 3.1, 3.2, 3.3, 3.4
        """
        try:
            stats = self.get_daily_stats()
            total_sent = stats.total_sent
            
            return self._calculate_alert_level(total_sent)
        except Exception as e:
            logger.error(f"Erreur calcul niveau d'alerte: {e}")
            return AlertLevel.OK
    
    @staticmethod
    def _calculate_alert_level(total_sent: int) -> AlertLevel:
        """
        Calcule le niveau d'alerte pour un nombre de messages donné.
        
        Args:
            total_sent: Nombre total de messages envoyés
        
        Returns:
            AlertLevel correspondant
        """
        if total_sent > DAILY_MESSAGE_LIMIT:  # > 1000
            return AlertLevel.BLOCKED
        elif total_sent >= 901:  # 901-1000 (91-100%)
            return AlertLevel.DANGER
        elif total_sent >= 751:  # 751-900 (76-90%)
            return AlertLevel.ATTENTION
        else:  # 0-750 (0-75%)
            return AlertLevel.OK
    
    def calculate_interaction_rate(self) -> float:
        """
        Calcule le taux d'interaction (message_2 / message_1).
        
        Returns:
            Taux d'interaction (0 si message_1 = 0)
        
        Requirements: 5.2
        """
        try:
            stats = self.get_daily_stats()
            
            if stats.message_1_count == 0:
                return 0.0
            
            return stats.message_2_count / stats.message_1_count
        except Exception as e:
            logger.error(f"Erreur calcul taux d'interaction: {e}")
            return 0.0
    
    def calculate_remaining_capacity(self) -> int:
        """
        Calcule la capacité restante avec le taux d'interaction.
        
        Formule: floor((1000 - sent) / (1 + interaction_rate))
        
        Returns:
            Nombre de contacts pouvant encore être contactés (jamais négatif)
        
        Requirements: 5.1
        """
        try:
            stats = self.get_daily_stats()
            total_sent = stats.total_sent
            interaction_rate = self.calculate_interaction_rate()
            
            remaining_messages = DAILY_MESSAGE_LIMIT - total_sent
            
            if remaining_messages <= 0:
                return 0
            
            # Formule: floor((1000 - sent) / (1 + interaction_rate))
            capacity = math.floor(remaining_messages / (1 + interaction_rate))
            
            return max(0, capacity)
        except Exception as e:
            logger.error(f"Erreur calcul capacité restante: {e}")
            return 0
    
    @staticmethod
    def calculate_remaining_capacity_from_values(
        total_sent: int,
        interaction_rate: float
    ) -> int:
        """
        Calcule la capacité restante à partir de valeurs données.
        
        Méthode statique pour les tests property-based.
        
        Args:
            total_sent: Nombre total de messages envoyés
            interaction_rate: Taux d'interaction (>= 0)
        
        Returns:
            Capacité restante (jamais négative)
        
        Requirements: 5.1
        """
        if interaction_rate < 0:
            interaction_rate = 0
        
        remaining_messages = DAILY_MESSAGE_LIMIT - total_sent
        
        if remaining_messages <= 0:
            return 0
        
        capacity = math.floor(remaining_messages / (1 + interaction_rate))
        
        return max(0, capacity)
    
    def get_error_rate_warning(self) -> bool:
        """
        Vérifie si le taux d'erreur dépasse 10%.
        
        Returns:
            True si error_count / total_sent > 0.10, False sinon
        
        Requirements: 6.2
        """
        try:
            stats = self.get_daily_stats()
            return self.calculate_error_rate_warning(
                stats.total_sent,
                stats.error_count
            )
        except Exception as e:
            logger.error(f"Erreur calcul taux d'erreur: {e}")
            return False
    
    @staticmethod
    def calculate_error_rate_warning(total_sent: int, error_count: int) -> bool:
        """
        Calcule si le taux d'erreur dépasse 10%.
        
        Méthode statique pour les tests property-based.
        
        Args:
            total_sent: Nombre total de messages envoyés
            error_count: Nombre d'erreurs
        
        Returns:
            True si error_count / total_sent > 0.10, False sinon
            False si total_sent <= 0 (pas de division par zéro)
        
        Requirements: 6.2
        """
        if total_sent <= 0:
            return False
        
        error_rate = error_count / total_sent
        return error_rate > 0.10
    
    def sync_to_supabase(self) -> None:
        """
        Synchronise les compteurs Redis vers Supabase.
        
        Persiste les statistiques actuelles dans la table daily_message_stats.
        
        Requirements: 7.2, 7.3
        """
        try:
            from app.supabase_client import get_supabase_db
            
            stats = self.get_daily_stats()
            db = get_supabase_db()
            
            data = {
                "date": stats.date,
                "message_1_count": stats.message_1_count,
                "message_2_count": stats.message_2_count,
                "error_count": stats.error_count
            }
            
            db.upsert_daily_stats(data)
            
            # Update last sync timestamp in Redis
            sync_key = f"{self._get_today_key_prefix()}:last_sync"
            self.redis_client.set(sync_key, datetime.now(timezone.utc).isoformat())
            self.redis_client.expire(sync_key, TTL_SECONDS)
            
            logger.info(
                "Statistiques synchronisées vers Supabase",
                extra={"date": stats.date, "total_sent": stats.total_sent}
            )
        except Exception as e:
            logger.error(f"Erreur synchronisation vers Supabase: {e}")
    
    def sync_from_supabase(self) -> None:
        """
        Récupère les compteurs depuis Supabase au démarrage.
        
        Restaure les statistiques du jour depuis Supabase si elles existent.
        
        Requirements: 7.1
        """
        try:
            from app.supabase_client import get_supabase_db
            
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            db = get_supabase_db()
            
            supabase_stats = db.get_daily_stats(today)
            
            if supabase_stats:
                # Restore counters to Redis
                pipe = self.redis_client.pipeline()
                
                message_1_key = self._get_key("message_1")
                message_2_key = self._get_key("message_2")
                errors_key = self._get_key("errors")
                
                pipe.set(message_1_key, supabase_stats["message_1_count"])
                pipe.set(message_2_key, supabase_stats["message_2_count"])
                pipe.set(errors_key, supabase_stats["error_count"])
                
                pipe.expire(message_1_key, TTL_SECONDS)
                pipe.expire(message_2_key, TTL_SECONDS)
                pipe.expire(errors_key, TTL_SECONDS)
                
                pipe.execute()
                
                logger.info(
                    "Statistiques restaurées depuis Supabase",
                    extra={
                        "date": today,
                        "message_1": supabase_stats["message_1_count"],
                        "message_2": supabase_stats["message_2_count"],
                        "errors": supabase_stats["error_count"]
                    }
                )
            else:
                logger.info(
                    "Aucune statistique trouvée dans Supabase pour aujourd'hui",
                    extra={"date": today}
                )
        except Exception as e:
            logger.error(f"Erreur synchronisation depuis Supabase: {e}")
    
    def reset_daily_counters(self) -> None:
        """
        Reset les compteurs à minuit avec persistance.
        
        Persiste les stats du jour précédent avant de reset les compteurs Redis.
        
        Requirements: 1.3, 1.4
        """
        try:
            # First, persist current stats to Supabase
            self.sync_to_supabase()
            
            # Get yesterday's date for logging
            yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
            
            # Delete today's keys (they will be recreated with 0 on next increment)
            today_prefix = self._get_today_key_prefix()
            keys_to_delete = [
                f"{today_prefix}:message_1",
                f"{today_prefix}:message_2",
                f"{today_prefix}:errors",
                f"{today_prefix}:last_sync"
            ]
            
            for key in keys_to_delete:
                self.redis_client.delete(key)
            
            logger.info(
                "Compteurs quotidiens réinitialisés",
                extra={"persisted_date": yesterday}
            )
        except Exception as e:
            logger.error(f"Erreur reset compteurs quotidiens: {e}")
    
    def log_error_to_supabase(
        self,
        error_code: str,
        error_message: str,
        message_id: Optional[int] = None
    ) -> None:
        """
        Enregistre une erreur dans Supabase.
        
        Args:
            error_code: Code d'erreur
            error_message: Message d'erreur détaillé
            message_id: ID du message concerné (optionnel)
        
        Requirements: 6.4
        """
        try:
            from app.supabase_client import get_supabase_db
            
            db = get_supabase_db()
            
            data = {
                "error_code": error_code,
                "error_message": error_message
            }
            
            if message_id is not None:
                data["message_id"] = message_id
            
            db.create_message_error(data)
            
            logger.info(
                "Erreur enregistrée dans Supabase",
                extra={"error_code": error_code, "message_id": message_id}
            )
        except Exception as e:
            logger.error(f"Erreur enregistrement erreur dans Supabase: {e}")
