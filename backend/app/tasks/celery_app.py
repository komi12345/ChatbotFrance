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


# URL Redis avec support SSL pour les services cloud (Render, etc.)
REDIS_URL_WITH_SSL = get_redis_url_with_ssl(settings.REDIS_URL)

# Création de l'application Celery
celery_app = Celery(
    "whatsapp_chatbot",
    broker=REDIS_URL_WITH_SSL,
    backend=REDIS_URL_WITH_SSL,
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
    
    # Concurrence - optimisé pour production à grande échelle
    # Note: Augmenté pour supporter plusieurs campagnes simultanées
    # Le rate limiting est géré au niveau de l'envoi, pas du worker
    worker_concurrency=4,  # Augmenté de 2 à 4 pour meilleure scalabilité
    worker_prefetch_multiplier=2,  # Augmenté pour meilleure utilisation des workers
    
    # Rate limiting global (25 messages par minute = ~0.42 msg/sec)
    task_default_rate_limit=f"{settings.WHATSAPP_RATE_LIMIT_PER_MINUTE}/m",
    
    # Queues et routing avec priorités
    task_queues=(
        Queue("default", Exchange("default"), routing_key="default"),
        Queue("messages", Exchange("messages"), routing_key="messages.#"),
        Queue("messages_high", Exchange("messages_high"), routing_key="messages.high.#"),  # Queue prioritaire
        Queue("retry", Exchange("retry"), routing_key="retry.#"),
        Queue("verification", Exchange("verification"), routing_key="verify.#"),  # Queue dédiée vérification
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
            "queue": "verification",
            "routing_key": "verify.single",
        },
        "app.tasks.message_tasks.bulk_verify_task": {
            "queue": "verification",
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
        # Tâche de nettoyage des verrous expirés (toutes les 10 minutes)
        "cleanup-expired-locks": {
            "task": "app.tasks.celery_app.cleanup_expired_locks",
            "schedule": timedelta(minutes=10),
            "options": {"queue": "default"},
        },
        # Tâche de récupération des campagnes interrompues (toutes les 5 minutes)
        # ROBUSTESSE: Reprend les campagnes qui ont été interrompues brutalement
        "recover-interrupted-campaigns": {
            "task": "app.tasks.celery_app.recover_interrupted_campaigns",
            "schedule": timedelta(minutes=5),
            "options": {"queue": "default"},
        },
        # Tâche de vérification de santé du système (toutes les 2 minutes)
        "health-check": {
            "task": "app.tasks.celery_app.system_health_check",
            "schedule": timedelta(minutes=2),
            "options": {"queue": "default"},
        },
    },
    
    # Configuration pour le scheduler crontab
    beat_schedule_filename="celerybeat-schedule",
    
    # Configuration pour la production
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=10,
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
    redis_url=REDIS_URL_WITH_SSL,
    limit=settings.WHATSAPP_RATE_LIMIT_PER_MINUTE,
    window=60
)


# Instance globale du service de monitoring
# Réutilise la même connexion Redis que Celery
# Requirements: 1.1
from app.services.monitoring_service import MonitoringService
monitoring_service = MonitoringService(redis_url=REDIS_URL_WITH_SSL)


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


@celery_app.task(name="app.tasks.celery_app.cleanup_expired_locks")
def cleanup_expired_locks():
    """
    Tâche périodique de nettoyage des verrous expirés.
    
    Exécutée toutes les 10 minutes pour nettoyer les verrous
    qui auraient pu rester bloqués suite à un crash.
    
    Requirements: Production scalability - lock cleanup
    """
    try:
        logger.info("Démarrage du nettoyage des verrous expirés")
        
        # Les verrous Redis ont un TTL automatique, donc ils expirent naturellement
        # Cette tâche est principalement pour le logging et la surveillance
        
        # Compter les verrous actifs (pattern: campaign:lock:*)
        redis_client = monitoring_service.redis_client
        lock_keys = list(redis_client.scan_iter(match="campaign:lock:*"))
        
        active_locks = []
        for key in lock_keys:
            ttl = redis_client.ttl(key)
            if ttl > 0:
                value = redis_client.get(key)
                active_locks.append({
                    "key": key,
                    "value": value,
                    "ttl": ttl
                })
        
        logger.info(
            f"Nettoyage verrous terminé: {len(active_locks)} verrous actifs",
            extra={"active_locks": len(active_locks)}
        )
        
        return {
            "status": "success",
            "active_locks": len(active_locks),
            "locks": active_locks
        }
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage des verrous: {e}")
        return {"status": "error", "message": str(e)}


@celery_app.task(name="app.tasks.celery_app.recover_interrupted_campaigns")
def recover_interrupted_campaigns():
    """
    Tâche périodique de récupération des campagnes interrompues.
    
    Détecte les campagnes en statut "sending" qui ont des messages "pending"
    mais aucune tâche Celery active, et relance l'envoi.
    
    ROBUSTESSE: Permet de reprendre automatiquement après un crash serveur
    ou une interruption de connexion.
    
    Requirements: Production robustness - automatic recovery
    """
    try:
        from app.supabase_client import get_supabase_client
        from datetime import datetime, timezone, timedelta
        
        logger.info("Démarrage de la récupération des campagnes interrompues")
        
        client = get_supabase_client()
        
        # Trouver les campagnes en statut "sending"
        campaigns_response = client.table("campaigns").select("id, name, created_at").eq("status", "sending").execute()
        sending_campaigns = campaigns_response.data or []
        
        recovered_count = 0
        
        for campaign in sending_campaigns:
            campaign_id = campaign["id"]
            
            # Vérifier s'il y a des messages pending pour cette campagne
            pending_response = client.table("messages").select("id", count="exact").eq(
                "campaign_id", campaign_id
            ).eq("status", "pending").execute()
            
            pending_count = pending_response.count or 0
            
            if pending_count == 0:
                # Pas de messages pending, la campagne devrait être terminée
                # Mettre à jour le statut
                client.table("campaigns").update({"status": "completed"}).eq("id", campaign_id).execute()
                logger.info(f"Campagne {campaign_id} marquée comme terminée (aucun message pending)")
                continue
            
            # Vérifier si des messages ont été envoyés récemment (dernières 10 minutes)
            # Si oui, la campagne est probablement encore active
            ten_minutes_ago = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
            
            recent_sent_response = client.table("messages").select("id", count="exact").eq(
                "campaign_id", campaign_id
            ).in_("status", ["sent", "delivered", "read"]).gte("sent_at", ten_minutes_ago).execute()
            
            recent_sent_count = recent_sent_response.count or 0
            
            if recent_sent_count > 0:
                # Des messages ont été envoyés récemment, la campagne est active
                logger.debug(f"Campagne {campaign_id} active ({recent_sent_count} messages envoyés récemment)")
                continue
            
            # La campagne semble interrompue - relancer l'envoi
            logger.warning(
                f"Campagne {campaign_id} ({campaign['name']}) semble interrompue: "
                f"{pending_count} messages pending, aucun envoi récent. Relance..."
            )
            
            # Importer et relancer la tâche d'envoi
            from app.tasks.message_tasks import send_campaign_messages
            send_campaign_messages.delay(campaign_id)
            
            recovered_count += 1
        
        logger.info(
            f"Récupération terminée: {recovered_count} campagne(s) relancée(s) sur {len(sending_campaigns)} en cours"
        )
        
        return {
            "status": "success",
            "sending_campaigns": len(sending_campaigns),
            "recovered_count": recovered_count
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des campagnes: {e}")
        return {"status": "error", "message": str(e)}


@celery_app.task(name="app.tasks.celery_app.system_health_check")
def system_health_check():
    """
    Tâche périodique de vérification de santé du système.
    
    Vérifie:
    - Connexion Redis
    - Connexion Supabase
    - État des workers Celery
    - Taux d'erreur des messages
    
    ROBUSTESSE: Permet de détecter les problèmes avant qu'ils ne deviennent critiques.
    
    Requirements: Production monitoring - health checks
    """
    try:
        from app.supabase_client import get_supabase_client
        
        health_status = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "redis": "unknown",
            "supabase": "unknown",
            "error_rate": "unknown",
            "daily_stats": None
        }
        
        # Vérifier Redis
        try:
            redis_client = monitoring_service.redis_client
            redis_client.ping()
            health_status["redis"] = "healthy"
        except Exception as e:
            health_status["redis"] = f"unhealthy: {str(e)}"
            logger.error(f"Health check Redis failed: {e}")
        
        # Vérifier Supabase
        try:
            client = get_supabase_client()
            # Simple query pour vérifier la connexion
            client.table("campaigns").select("id").limit(1).execute()
            health_status["supabase"] = "healthy"
        except Exception as e:
            health_status["supabase"] = f"unhealthy: {str(e)}"
            logger.error(f"Health check Supabase failed: {e}")
        
        # Vérifier le taux d'erreur
        try:
            stats = monitoring_service.get_daily_stats()
            health_status["daily_stats"] = {
                "date": stats.date,
                "message_1_count": stats.message_1_count,
                "message_2_count": stats.message_2_count,
                "error_count": stats.error_count,
                "total_sent": stats.total_sent
            }
            
            # Calculer le taux d'erreur
            if stats.total_sent > 0:
                error_rate = stats.error_count / stats.total_sent
                if error_rate > 0.10:
                    health_status["error_rate"] = f"warning: {error_rate:.1%}"
                    logger.warning(f"Taux d'erreur élevé: {error_rate:.1%}")
                else:
                    health_status["error_rate"] = f"healthy: {error_rate:.1%}"
            else:
                health_status["error_rate"] = "healthy: no messages sent"
                
        except Exception as e:
            health_status["error_rate"] = f"unknown: {str(e)}"
            logger.error(f"Health check error rate failed: {e}")
        
        # Déterminer le statut global
        is_healthy = (
            health_status["redis"] == "healthy" and
            health_status["supabase"] == "healthy" and
            not health_status["error_rate"].startswith("warning")
        )
        
        health_status["overall"] = "healthy" if is_healthy else "degraded"
        
        if not is_healthy:
            logger.warning(f"System health degraded: {health_status}")
        else:
            logger.info(f"System health check passed: {health_status['overall']}")
        
        return health_status
        
    except Exception as e:
        logger.error(f"Erreur lors du health check: {e}")
        return {
            "status": "error",
            "message": str(e),
            "overall": "unhealthy"
        }


# Import datetime pour les nouvelles tâches
from datetime import datetime, timezone
