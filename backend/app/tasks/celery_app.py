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
        # Tâche de vérification des messages sans interaction après 24h
        # Requirements: 7.1 - Exécutée toutes les heures
        "check-expired-interactions-hourly": {
            "task": "app.tasks.celery_app.check_expired_interactions",
            "schedule": timedelta(hours=1),
            "options": {"queue": "default"},
        },
        # Tâche de timeout de sécurité 48h pour clôturer les campagnes bloquées
        # Requirements: 7.5 - Exécutée toutes les 6 heures
        "check-campaign-timeout-48h": {
            "task": "app.tasks.celery_app.check_campaign_timeout_48h",
            "schedule": timedelta(hours=6),
            "options": {"queue": "default"},
        },
        # Tâche de vérification périodique des campagnes en cours
        # Requirements: 2.1, 2.2 - Exécutée toutes les 2 minutes
        "check-sending-campaigns": {
            "task": "app.tasks.celery_app.check_sending_campaigns",
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
    
    LOGIQUE DE CLÔTURE 2025:
    Une campagne reste en "sending" jusqu'à ce que:
    1. 24h se soient écoulées depuis le lancement, OU
    2. Tous les contacts aient reçu le Message 2 (interaction complète pour tous)
    
    ROBUSTESSE: Permet de reprendre automatiquement après un crash serveur
    ou une interruption de connexion.
    
    Requirements: Production robustness - automatic recovery
    Requirements 7.5: Inclure "no_interaction" dans le calcul du statut "completed"
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
        completed_count = 0
        
        for campaign in sending_campaigns:
            campaign_id = campaign["id"]
            campaign_created_at = campaign.get("created_at")
            
            # Calculer le temps écoulé depuis le lancement
            campaign_start_time = None
            if campaign_created_at:
                try:
                    # Parser le timestamp ISO et s'assurer qu'il a une timezone
                    parsed_time = datetime.fromisoformat(campaign_created_at.replace("Z", "+00:00"))
                    # Si le datetime est naive (sans timezone), ajouter UTC
                    if parsed_time.tzinfo is None:
                        campaign_start_time = parsed_time.replace(tzinfo=timezone.utc)
                    else:
                        campaign_start_time = parsed_time
                except (ValueError, AttributeError):
                    campaign_start_time = datetime.now(timezone.utc)
            else:
                campaign_start_time = datetime.now(timezone.utc)
            
            hours_since_launch = (datetime.now(timezone.utc) - campaign_start_time).total_seconds() / 3600
            is_24h_elapsed = hours_since_launch >= 24
            
            # Vérifier s'il y a des messages pending pour cette campagne
            pending_response = client.table("messages").select("id", count="exact").eq(
                "campaign_id", campaign_id
            ).eq("status", "pending").execute()
            pending_count = pending_response.count or 0
            
            # Compter les Message 1 envoyés
            message_1_sent_response = client.table("messages").select("id", count="exact").eq(
                "campaign_id", campaign_id
            ).eq("message_type", "message_1").in_("status", ["sent", "delivered", "read"]).execute()
            message_1_sent_count = message_1_sent_response.count or 0
            
            # Compter les Message 2 envoyés
            message_2_sent_response = client.table("messages").select("id", count="exact").eq(
                "campaign_id", campaign_id
            ).eq("message_type", "message_2").in_("status", ["sent", "delivered", "read"]).execute()
            message_2_sent_count = message_2_sent_response.count or 0
            
            # Compter les no_interaction et failed
            no_interaction_response = client.table("messages").select("id", count="exact").eq(
                "campaign_id", campaign_id
            ).eq("status", "no_interaction").execute()
            no_interaction_count = no_interaction_response.count or 0
            
            failed_response = client.table("messages").select("id", count="exact").eq(
                "campaign_id", campaign_id
            ).eq("status", "failed").execute()
            failed_count = failed_response.count or 0
            
            # Calculer si tous les contacts ont terminé leur cycle
            contacts_completed = message_2_sent_count + no_interaction_count + failed_count
            all_contacts_completed = (message_1_sent_count > 0 and contacts_completed >= message_1_sent_count)
            
            # LOGIQUE DE CLÔTURE:
            if pending_count == 0:
                # Tous les Message 1 sont envoyés
                if is_24h_elapsed or all_contacts_completed:
                    # Clôturer la campagne
                    total_sent_response = client.table("messages").select("id", count="exact").eq(
                        "campaign_id", campaign_id
                    ).in_("status", ["sent", "delivered", "read"]).execute()
                    total_sent_count = total_sent_response.count or 0
                    
                    if failed_count > 0 and total_sent_count == 0:
                        new_status = "failed"
                    else:
                        new_status = "completed"
                    
                    client.table("campaigns").update({
                        "status": new_status,
                        "completed_at": datetime.now(timezone.utc).isoformat()
                    }).eq("id", campaign_id).execute()
                    
                    logger.info(
                        f"Campagne {campaign_id} clôturée: status={new_status}, "
                        f"24h_elapsed={is_24h_elapsed}, all_completed={all_contacts_completed}, "
                        f"msg1={message_1_sent_count}, msg2={message_2_sent_count}, "
                        f"no_interaction={no_interaction_count}"
                    )
                    completed_count += 1
                else:
                    # Moins de 24h et pas tous les contacts ont terminé -> garder en "sending"
                    logger.debug(
                        f"Campagne {campaign_id} en attente d'interactions: "
                        f"{hours_since_launch:.1f}h écoulées, "
                        f"msg2={message_2_sent_count}/{message_1_sent_count}"
                    )
                continue
            
            # Il y a des messages pending - vérifier si la campagne est interrompue
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
            f"Récupération terminée: {recovered_count} campagne(s) relancée(s), "
            f"{completed_count} campagne(s) clôturée(s) sur {len(sending_campaigns)} en cours"
        )
        
        return {
            "status": "success",
            "sending_campaigns": len(sending_campaigns),
            "recovered_count": recovered_count,
            "completed_count": completed_count
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


@celery_app.task(name="app.tasks.celery_app.check_expired_interactions")
def check_expired_interactions():
    """
    Tâche périodique pour marquer les contacts sans interaction après 24h.
    
    Exécutée toutes les heures pour:
    1. Trouver les Message 1 envoyés il y a plus de 24h
    2. Vérifier si le contact a interagi
    3. Si pas d'interaction -> marquer comme "no_interaction"
    4. Mettre à jour les statistiques de la campagne (failed_count)
    
    Requirements: 7.1, 7.2, 7.3, 7.4, 7.6
    """
    try:
        from app.supabase_client import get_supabase_client
        
        logger.info("Démarrage de la vérification des messages sans interaction (24h)")
        
        client = get_supabase_client()
        
        # Calculer le timestamp de coupure (24h en arrière)
        cutoff_time = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
        
        # Trouver les messages Message 1 envoyés il y a plus de 24h
        # qui sont en statut "sent", "delivered" ou "read"
        # et qui ne sont pas déjà marqués comme "no_interaction" ou "failed"
        messages_response = client.table("messages").select(
            "id, campaign_id, contact_id, sent_at, status"
        ).eq(
            "message_type", "message_1"
        ).in_(
            "status", ["sent", "delivered", "read"]
        ).lt(
            "sent_at", cutoff_time
        ).execute()
        
        messages_to_check = messages_response.data or []
        
        logger.info(f"Trouvé {len(messages_to_check)} messages Message 1 de plus de 24h à vérifier")
        
        marked_count = 0
        campaigns_updated = {}  # Pour tracker les campagnes à mettre à jour
        
        for message in messages_to_check:
            message_id = message["id"]
            campaign_id = message["campaign_id"]
            contact_id = message["contact_id"]
            
            # Vérifier si un Message 2 a déjà été envoyé pour ce contact/campagne
            # Si oui, le contact a interagi et le Message 2 a été envoyé
            message_2_response = client.table("messages").select(
                "id", count="exact"
            ).eq(
                "campaign_id", campaign_id
            ).eq(
                "contact_id", contact_id
            ).eq(
                "message_type", "message_2"
            ).execute()
            
            message_2_count = message_2_response.count or 0
            
            if message_2_count > 0:
                # Message 2 déjà envoyé = interaction a eu lieu, skip
                logger.debug(
                    f"Message {message_id}: Message 2 déjà envoyé pour contact {contact_id}, skip"
                )
                continue
            
            # Vérifier s'il y a eu une interaction (reply ou reaction)
            interaction_response = client.table("interactions").select(
                "id", count="exact"
            ).eq(
                "campaign_id", campaign_id
            ).eq(
                "contact_id", contact_id
            ).in_(
                "interaction_type", ["reply", "reaction"]
            ).execute()
            
            interaction_count = interaction_response.count or 0
            
            if interaction_count > 0:
                # Interaction trouvée mais Message 2 pas encore envoyé
                # Cela peut arriver si le Message 2 est en attente
                logger.debug(
                    f"Message {message_id}: Interaction trouvée pour contact {contact_id}, skip"
                )
                continue
            
            # Pas d'interaction après 24h -> marquer comme "no_interaction"
            client.table("messages").update({
                "status": "no_interaction",
                "error_message": "Pas d'interaction dans les 24h"
            }).eq("id", message_id).execute()
            
            # Récupérer les infos du contact pour le log
            contact_response = client.table("contacts").select(
                "first_name, last_name, full_number"
            ).eq("id", contact_id).limit(1).execute()
            
            contact_info = contact_response.data[0] if contact_response.data else {}
            contact_name = f"{contact_info.get('first_name', '')} {contact_info.get('last_name', '')}".strip()
            contact_phone = contact_info.get("full_number", "N/A")
            
            logger.info(
                f"Message {message_id} marqué 'no_interaction': "
                f"Contact {contact_id} ({contact_name}, {contact_phone}), "
                f"Campagne {campaign_id}"
            )
            
            marked_count += 1
            
            # Tracker la campagne pour mise à jour du failed_count
            if campaign_id not in campaigns_updated:
                campaigns_updated[campaign_id] = 0
            campaigns_updated[campaign_id] += 1
        
        # Mettre à jour les compteurs failed_count des campagnes
        for campaign_id, count in campaigns_updated.items():
            try:
                # Récupérer le failed_count actuel
                campaign_response = client.table("campaigns").select(
                    "failed_count"
                ).eq("id", campaign_id).limit(1).execute()
                
                if campaign_response.data:
                    current_failed = campaign_response.data[0].get("failed_count") or 0
                    new_failed = current_failed + count
                    
                    client.table("campaigns").update({
                        "failed_count": new_failed
                    }).eq("id", campaign_id).execute()
                    
                    logger.info(
                        f"Campagne {campaign_id}: failed_count mis à jour "
                        f"({current_failed} -> {new_failed}, +{count} no_interaction)"
                    )
            except Exception as e:
                logger.error(f"Erreur mise à jour failed_count campagne {campaign_id}: {e}")
        
        logger.info(
            f"Vérification 24h terminée: {marked_count} message(s) marqué(s) 'no_interaction' "
            f"sur {len(messages_to_check)} vérifié(s), "
            f"{len(campaigns_updated)} campagne(s) mise(s) à jour"
        )
        
        return {
            "status": "success",
            "messages_checked": len(messages_to_check),
            "messages_marked": marked_count,
            "campaigns_updated": len(campaigns_updated),
            "details": campaigns_updated
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la vérification des interactions 24h: {e}")
        return {"status": "error", "message": str(e)}


@celery_app.task(name="app.tasks.celery_app.check_campaign_timeout_48h")
def check_campaign_timeout_48h():
    """
    Tâche périodique pour clôturer les campagnes de plus de 48h.
    
    Exécutée toutes les 6 heures pour:
    1. Trouver les campagnes en statut "sending" créées il y a plus de 48h
    2. Marquer tous les messages "pending" comme "failed" (timeout)
    3. Mettre à jour le statut de la campagne via update_campaign_status
    
    Cette tâche est un filet de sécurité pour éviter les campagnes "zombies"
    qui resteraient bloquées en statut "sending" indéfiniment.
    
    Requirements: 7.5 - Timeout de sécurité 48h
    """
    try:
        from app.supabase_client import get_supabase_client
        from app.tasks.message_tasks import update_campaign_status
        
        logger.info("Démarrage de la vérification du timeout 48h des campagnes")
        
        client = get_supabase_client()
        
        # Calculer le timestamp de coupure (48h en arrière)
        cutoff_time = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
        
        # Trouver les campagnes en statut "sending" créées il y a plus de 48h
        campaigns_response = client.table("campaigns").select(
            "id, name, created_at"
        ).eq(
            "status", "sending"
        ).lt(
            "created_at", cutoff_time
        ).execute()
        
        campaigns_to_close = campaigns_response.data or []
        
        logger.info(f"Trouvé {len(campaigns_to_close)} campagne(s) en timeout 48h")
        
        closed_count = 0
        total_messages_failed = 0
        
        for campaign in campaigns_to_close:
            campaign_id = campaign["id"]
            campaign_name = campaign["name"]
            
            try:
                # Compter les messages pending avant de les marquer
                pending_response = client.table("messages").select(
                    "id", count="exact"
                ).eq(
                    "campaign_id", campaign_id
                ).eq(
                    "status", "pending"
                ).execute()
                
                pending_count = pending_response.count or 0
                
                if pending_count > 0:
                    # Marquer tous les messages pending comme "failed" avec message de timeout
                    client.table("messages").update({
                        "status": "failed",
                        "error_message": "Timeout 48h - campagne clôturée automatiquement"
                    }).eq(
                        "campaign_id", campaign_id
                    ).eq(
                        "status", "pending"
                    ).execute()
                    
                    total_messages_failed += pending_count
                    
                    logger.info(
                        f"Campagne {campaign_id} ({campaign_name}): "
                        f"{pending_count} message(s) pending marqué(s) comme failed (timeout 48h)"
                    )
                
                # Mettre à jour le statut de la campagne
                update_campaign_status.delay(campaign_id)
                
                closed_count += 1
                
                logger.info(
                    f"Campagne {campaign_id} ({campaign_name}) clôturée (timeout 48h)"
                )
                
            except Exception as e:
                logger.error(
                    f"Erreur lors de la clôture de la campagne {campaign_id}: {e}"
                )
        
        logger.info(
            f"Vérification timeout 48h terminée: {closed_count} campagne(s) clôturée(s), "
            f"{total_messages_failed} message(s) marqué(s) comme failed"
        )
        
        return {
            "status": "success",
            "campaigns_checked": len(campaigns_to_close),
            "campaigns_closed": closed_count,
            "messages_failed": total_messages_failed
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la vérification du timeout 48h: {e}")
        return {"status": "error", "message": str(e)}


@celery_app.task(name="app.tasks.celery_app.check_sending_campaigns")
def check_sending_campaigns():
    """
    Tâche périodique de vérification des campagnes en cours d'envoi.
    
    Exécutée toutes les 2 minutes pour:
    1. Récupérer toutes les campagnes en statut "sending"
    2. Pour chaque campagne, déclencher update_campaign_status pour vérifier
       si elle doit être marquée comme "completed"
    
    Cette tâche est un filet de sécurité en cas de webhook manqué ou
    de problème lors de l'envoi du Message 2.
    
    Requirements: 2.1, 2.2
    """
    try:
        from app.supabase_client import get_supabase_client
        from app.tasks.message_tasks import update_campaign_status
        
        logger.info("Démarrage de la vérification périodique des campagnes en cours")
        
        client = get_supabase_client()
        
        # Récupérer toutes les campagnes en statut "sending"
        campaigns_response = client.table("campaigns").select(
            "id, name"
        ).eq(
            "status", "sending"
        ).execute()
        
        sending_campaigns = campaigns_response.data or []
        
        logger.info(f"Trouvé {len(sending_campaigns)} campagne(s) en statut 'sending'")
        
        triggered_count = 0
        
        for campaign in sending_campaigns:
            campaign_id = campaign["id"]
            campaign_name = campaign["name"]
            
            try:
                # Déclencher la vérification du statut de la campagne
                update_campaign_status.delay(campaign_id)
                triggered_count += 1
                
                logger.debug(
                    f"Vérification déclenchée pour campagne {campaign_id} ({campaign_name})"
                )
                
            except Exception as e:
                logger.error(
                    f"Erreur lors du déclenchement de la vérification "
                    f"pour campagne {campaign_id}: {e}"
                )
        
        logger.info(
            f"Vérification périodique terminée: {triggered_count} vérification(s) "
            f"déclenchée(s) sur {len(sending_campaigns)} campagne(s) en cours"
        )
        
        return {
            "status": "success",
            "sending_campaigns": len(sending_campaigns),
            "triggered_count": triggered_count
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la vérification périodique des campagnes: {e}")
        return {"status": "error", "message": str(e)}
