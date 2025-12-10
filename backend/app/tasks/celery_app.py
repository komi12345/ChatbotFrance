"""
Configuration Celery - Gestion des tâches asynchrones
Utilise Redis comme message broker pour l'envoi massif de messages WhatsApp

Exigences: 16.1, 16.3
"""
import logging
from celery import Celery
from celery.schedules import crontab
from kombu import Queue, Exchange
from datetime import timedelta

from app.config import settings

# Configuration du logger
logger = logging.getLogger(__name__)

# Création de l'application Celery
celery_app = Celery(
    "whatsapp_chatbot",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.message_tasks"]
)

# Configuration Celery
celery_app.conf.update(
    # Sérialisation
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # Timezone
    timezone="Europe/Paris",
    enable_utc=True,
    
    # Résultats des tâches
    result_expires=timedelta(hours=24),
    task_track_started=True,
    
    # Retry configuration
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Concurrence - limiter pour respecter le rate limiting WhatsApp
    worker_concurrency=2,
    worker_prefetch_multiplier=1,
    
    # Rate limiting global (25 messages par minute = ~0.42 msg/sec)
    task_default_rate_limit=f"{settings.WHATSAPP_RATE_LIMIT_PER_MINUTE}/m",
    
    # Queues et routing
    task_queues=(
        Queue("default", Exchange("default"), routing_key="default"),
        Queue("messages", Exchange("messages"), routing_key="messages.#"),
        Queue("retry", Exchange("retry"), routing_key="retry.#"),
    ),
    
    task_default_queue="default",
    task_default_exchange="default",
    task_default_routing_key="default",
    
    # Routing des tâches vers les queues appropriées
    task_routes={
        "app.tasks.message_tasks.send_single_message": {
            "queue": "messages",
            "routing_key": "messages.single",
        },
        "app.tasks.message_tasks.send_campaign_messages": {
            "queue": "messages",
            "routing_key": "messages.campaign",
        },
        "app.tasks.message_tasks.retry_failed_message": {
            "queue": "retry",
            "routing_key": "retry.message",
        },
        "app.tasks.message_tasks.verify_whatsapp_task": {
            "queue": "default",
            "routing_key": "verify.single",
        },
        "app.tasks.message_tasks.bulk_verify_task": {
            "queue": "default",
            "routing_key": "verify.bulk",
        },
    },
    
    # Beat scheduler pour les tâches périodiques
    # Requirements: 7.2 (sync horaire), 1.3, 2.5 (reset quotidien)
    beat_schedule={
        # Tâche de synchronisation horaire vers Supabase
        # Requirements: 7.2
        "sync-monitoring-to-supabase-hourly": {
            "task": "app.tasks.celery_app.sync_monitoring_to_supabase",
            "schedule": timedelta(hours=1),
            "options": {"queue": "default"},
        },
        # Tâche de reset quotidien à 00:00 UTC
        # Requirements: 1.3, 2.5
        "reset-daily-monitoring-midnight": {
            "task": "app.tasks.celery_app.reset_daily_monitoring",
            "schedule": crontab(hour=0, minute=0),
            "options": {"queue": "default"},
        },
    },
    
    # Configuration pour le scheduler crontab
    beat_schedule_filename="celerybeat-schedule",
)


class RateLimiter:
    """
    Rate limiter pour respecter la limite de 25 messages par minute de WhatsApp.
    Utilise Redis pour le comptage distribué.
    
    Exigences: 4.8, 16.3
    """
    
    def __init__(self, redis_url: str, limit: int = 25, window: int = 60):
        """
        Initialise le rate limiter.
        
        Args:
            redis_url: URL de connexion Redis
            limit: Nombre maximum de messages par fenêtre
            window: Durée de la fenêtre en secondes
        """
        self.redis_url = redis_url
        self.limit = limit
        self.window = window
        self._redis = None
    
    @property
    def redis(self):
        """Connexion Redis lazy-loaded"""
        if self._redis is None:
            import redis
            self._redis = redis.from_url(self.redis_url)
        return self._redis
    
    def can_send(self, key: str = "whatsapp_messages") -> bool:
        """
        Vérifie si un message peut être envoyé sans dépasser la limite.
        
        Args:
            key: Clé Redis pour le compteur
        
        Returns:
            True si l'envoi est autorisé, False sinon
        """
        try:
            current = self.redis.get(key)
            if current is None:
                return True
            return int(current) < self.limit
        except Exception as e:
            logger.error(f"Erreur vérification rate limit: {e}")
            # En cas d'erreur, on autorise par défaut
            return True
    
    def increment(self, key: str = "whatsapp_messages") -> int:
        """
        Incrémente le compteur de messages envoyés.
        
        Args:
            key: Clé Redis pour le compteur
        
        Returns:
            Nouvelle valeur du compteur
        """
        try:
            pipe = self.redis.pipeline()
            pipe.incr(key)
            pipe.expire(key, self.window)
            results = pipe.execute()
            return results[0]
        except Exception as e:
            logger.error(f"Erreur incrémentation rate limit: {e}")
            return 0
    
    def get_remaining(self, key: str = "whatsapp_messages") -> int:
        """
        Retourne le nombre de messages restants dans la fenêtre actuelle.
        
        Args:
            key: Clé Redis pour le compteur
        
        Returns:
            Nombre de messages restants
        """
        try:
            current = self.redis.get(key)
            if current is None:
                return self.limit
            return max(0, self.limit - int(current))
        except Exception as e:
            logger.error(f"Erreur lecture rate limit: {e}")
            return 0
    
    def get_wait_time(self, key: str = "whatsapp_messages") -> int:
        """
        Retourne le temps d'attente avant de pouvoir envoyer un nouveau message.
        
        Args:
            key: Clé Redis pour le compteur
        
        Returns:
            Temps d'attente en secondes (0 si envoi possible immédiatement)
        """
        try:
            if self.can_send(key):
                return 0
            ttl = self.redis.ttl(key)
            return max(0, ttl) if ttl > 0 else 0
        except Exception as e:
            logger.error(f"Erreur lecture TTL rate limit: {e}")
            return 0


# Instance globale du rate limiter
rate_limiter = RateLimiter(
    redis_url=settings.REDIS_URL,
    limit=settings.WHATSAPP_RATE_LIMIT_PER_MINUTE,
    window=60
)


# Instance globale du service de monitoring
# Réutilise la même connexion Redis que Celery
# Requirements: 1.1
from app.services.monitoring_service import MonitoringService
monitoring_service = MonitoringService(redis_url=settings.REDIS_URL)


def get_celery_app() -> Celery:
    """Retourne l'instance Celery"""
    return celery_app


def get_monitoring_service() -> MonitoringService:
    """Retourne l'instance du service de monitoring"""
    return monitoring_service


# =============================================================================
# Tâches périodiques de monitoring
# =============================================================================

@celery_app.task(name="app.tasks.celery_app.sync_monitoring_to_supabase")
def sync_monitoring_to_supabase():
    """
    Tâche périodique de synchronisation des compteurs vers Supabase.
    
    Exécutée toutes les heures pour persister les statistiques Redis
    dans Supabase, garantissant la survie des données aux redémarrages.
    
    Requirements: 7.2
    """
    try:
        logger.info("Démarrage de la synchronisation monitoring vers Supabase")
        monitoring_service.sync_to_supabase()
        logger.info("Synchronisation monitoring vers Supabase terminée avec succès")
        return {"status": "success", "message": "Sync completed"}
    except Exception as e:
        logger.error(f"Erreur lors de la synchronisation monitoring: {e}")
        return {"status": "error", "message": str(e)}


@celery_app.task(name="app.tasks.celery_app.reset_daily_monitoring")
def reset_daily_monitoring():
    """
    Tâche périodique de reset des compteurs quotidiens.
    
    Exécutée à 00:00 UTC pour:
    1. Persister les statistiques du jour précédent dans Supabase
    2. Réinitialiser les compteurs Redis à zéro
    3. Débloquer automatiquement l'envoi de messages
    
    Requirements: 1.3, 2.5
    """
    try:
        logger.info("Démarrage du reset quotidien des compteurs monitoring")
        monitoring_service.reset_daily_counters()
        logger.info("Reset quotidien des compteurs monitoring terminé avec succès")
        return {"status": "success", "message": "Daily reset completed"}
    except Exception as e:
        logger.error(f"Erreur lors du reset quotidien monitoring: {e}")
        return {"status": "error", "message": str(e)}
