"""
Service de Cache Applicatif - Optimisation des performances

Ce service gère le cache Redis pour les données fréquemment accédées :
- Statistiques globales (messages, contacts, campagnes)
- Listes de catégories avec comptages
- Comptages de contacts par catégorie

IMPORTANT: Ce service utilise des clés avec préfixe "cache:" pour ne PAS
interférer avec les clés existantes utilisées par Celery et le monitoring :
- whatsapp:* - Compteurs de monitoring quotidiens
- campaign:* - Verrous de campagne
- celery* - Queues et résultats Celery

Requirements: 3.1, 3.2, 3.4, 3.5, 3.6
"""
import json
import logging
from datetime import datetime, date, timedelta
from typing import Any, Callable, Optional, List

import redis


class DateTimeEncoder(json.JSONEncoder):
    """
    Encodeur JSON personnalisé pour gérer les objets datetime.
    
    Convertit les objets datetime et date en chaînes ISO 8601.
    """
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, date):
            return obj.isoformat()
        return super().default(obj)

from app.config import settings

logger = logging.getLogger(__name__)


def get_redis_url_with_ssl(redis_url: str) -> str:
    """
    Ajoute les paramètres SSL requis pour les connexions rediss://.
    Réutilise la même logique que monitoring_service.py.
    """
    if redis_url.startswith("rediss://") and "ssl_cert_reqs" not in redis_url:
        separator = "&" if "?" in redis_url else "?"
        return f"{redis_url}{separator}ssl_cert_reqs=none"
    return redis_url


class CacheService:
    """
    Service de cache applicatif utilisant Redis.
    
    Préfixes de clés:
    - cache:stats:* - Statistiques globales
    - cache:categories:* - Données de catégories
    - cache:contacts:count:* - Comptages de contacts
    
    Ne doit PAS interférer avec:
    - whatsapp:* - Compteurs monitoring
    - campaign:* - Verrous de campagne
    - celery* - Queues Celery
    
    Requirements: 3.1, 3.5
    """
    
    # Préfixes protégés - NE JAMAIS écrire sur ces clés
    PROTECTED_PREFIXES = ("whatsapp:", "campaign:", "celery")
    
    # Préfixe pour toutes les clés de cache
    CACHE_PREFIX = "cache:"
    
    # TTL par défaut et par type de données
    DEFAULT_TTL = timedelta(seconds=60)
    STATS_TTL = timedelta(seconds=60)
    CATEGORIES_TTL = timedelta(seconds=120)
    CONTACTS_COUNT_TTL = timedelta(seconds=60)
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        Initialise le service de cache.
        
        Args:
            redis_client: Client Redis existant (optionnel).
                         Si non fourni, crée une nouvelle connexion.
        
        Requirements: 3.6 - Réutiliser la connexion Redis existante
        """
        self._redis = redis_client
        self._redis_url = get_redis_url_with_ssl(settings.REDIS_URL)
        
        # Métriques de cache
        self._hits = 0
        self._misses = 0
        
        logger.info(
            "CacheService initialisé",
            extra={"redis_url": self._redis_url[:20] + "..." if self._redis_url else "N/A"}
        )
    
    @property
    def redis(self) -> redis.Redis:
        """Connexion Redis lazy-loaded."""
        if self._redis is None:
            self._redis = redis.from_url(self._redis_url, decode_responses=True)
        return self._redis

    def _make_key(self, namespace: str, key: str) -> str:
        """
        Génère une clé cache avec le préfixe approprié.
        
        Args:
            namespace: Espace de noms (stats, categories, contacts)
            key: Identifiant unique dans l'espace de noms
        
        Returns:
            Clé Redis complète avec préfixe cache:
        
        Requirements: 3.1
        """
        return f"{self.CACHE_PREFIX}{namespace}:{key}"
    
    def _is_protected_key(self, key: str) -> bool:
        """
        Vérifie si une clé est protégée (ne doit pas être modifiée).
        
        Args:
            key: Clé Redis à vérifier
        
        Returns:
            True si la clé est protégée, False sinon
        
        Requirements: 3.5
        """
        return any(key.startswith(prefix) for prefix in self.PROTECTED_PREFIXES)
    
    def get(self, namespace: str, key: str) -> Optional[Any]:
        """
        Récupère une valeur du cache.
        
        Args:
            namespace: Espace de noms
            key: Identifiant unique
        
        Returns:
            Valeur désérialisée ou None si non trouvée/erreur
        
        Requirements: 3.2, 3.4
        """
        cache_key = self._make_key(namespace, key)
        try:
            value = self.redis.get(cache_key)
            if value is not None:
                self._hits += 1
                logger.debug(f"Cache HIT: {cache_key}")
                return json.loads(value)
            self._misses += 1
            logger.debug(f"Cache MISS: {cache_key}")
            return None
        except json.JSONDecodeError as e:
            logger.warning(f"Cache JSON decode error for {cache_key}: {e}")
            self._misses += 1
            return None
        except redis.RedisError as e:
            logger.warning(f"Cache Redis error for {cache_key}: {e}")
            self._misses += 1
            return None
        except Exception as e:
            logger.warning(f"Cache unexpected error for {cache_key}: {e}")
            self._misses += 1
            return None
    
    def set(
        self,
        namespace: str,
        key: str,
        value: Any,
        ttl: Optional[timedelta] = None
    ) -> bool:
        """
        Stocke une valeur dans le cache.
        
        Args:
            namespace: Espace de noms
            key: Identifiant unique
            value: Valeur à stocker (sera sérialisée en JSON)
            ttl: Durée de vie (utilise DEFAULT_TTL si non spécifié)
        
        Returns:
            True si succès, False sinon
        
        Requirements: 3.1, 3.5
        """
        cache_key = self._make_key(namespace, key)
        
        # Vérification de sécurité - ne jamais écrire sur les clés protégées
        if self._is_protected_key(cache_key):
            logger.error(f"SECURITY: Attempted to write to protected key: {cache_key}")
            return False
        
        try:
            ttl = ttl or self.DEFAULT_TTL
            # Utiliser DateTimeEncoder pour gérer les objets datetime
            serialized = json.dumps(value, cls=DateTimeEncoder)
            self.redis.setex(cache_key, int(ttl.total_seconds()), serialized)
            logger.debug(f"Cache SET: {cache_key} (TTL: {ttl.total_seconds()}s)")
            return True
        except TypeError as e:
            logger.warning(f"Cache JSON encode error for {cache_key}: {e}")
            return False
        except redis.RedisError as e:
            logger.warning(f"Cache Redis error for {cache_key}: {e}")
            return False
        except Exception as e:
            logger.warning(f"Cache unexpected error for {cache_key}: {e}")
            return False
    
    def delete(self, namespace: str, key: str) -> bool:
        """
        Supprime une entrée du cache.
        
        Args:
            namespace: Espace de noms
            key: Identifiant unique
        
        Returns:
            True si succès, False sinon
        """
        cache_key = self._make_key(namespace, key)
        try:
            self.redis.delete(cache_key)
            logger.debug(f"Cache DELETE: {cache_key}")
            return True
        except redis.RedisError as e:
            logger.warning(f"Cache delete error for {cache_key}: {e}")
            return False
        except Exception as e:
            logger.warning(f"Cache unexpected delete error for {cache_key}: {e}")
            return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalide toutes les clés correspondant au pattern.
        
        Args:
            pattern: Pattern de clé (ex: "stats:*" pour cache:stats:*)
        
        Returns:
            Nombre de clés supprimées
        
        Requirements: 4.5
        """
        full_pattern = f"{self.CACHE_PREFIX}{pattern}"
        try:
            keys = list(self.redis.scan_iter(match=full_pattern))
            if not keys:
                return 0
            
            # Vérifier qu'aucune clé protégée n'est dans la liste
            safe_keys = [k for k in keys if not self._is_protected_key(k)]
            
            if not safe_keys:
                return 0
            
            deleted = self.redis.delete(*safe_keys)
            logger.info(f"Cache INVALIDATE pattern '{full_pattern}': {deleted} keys deleted")
            return deleted
        except redis.RedisError as e:
            logger.warning(f"Cache invalidate pattern error for {full_pattern}: {e}")
            return 0
        except Exception as e:
            logger.warning(f"Cache unexpected invalidate error for {full_pattern}: {e}")
            return 0

    # =========================================================================
    # Méthodes d'invalidation spécifiques
    # =========================================================================
    
    def invalidate_stats(self) -> int:
        """
        Invalide tous les caches de statistiques.
        
        Appelé après création/modification/suppression de contacts ou messages.
        
        Returns:
            Nombre de clés supprimées
        
        Requirements: 1.3, 4.1, 4.2
        """
        return self.invalidate_pattern("stats:*")
    
    def invalidate_categories(self) -> int:
        """
        Invalide tous les caches de catégories.
        
        Appelé après création/modification/suppression de catégories.
        
        Returns:
            Nombre de clés supprimées
        
        Requirements: 1.4, 4.3
        """
        return self.invalidate_pattern("categories:*")
    
    def invalidate_category(self, category_id: int) -> int:
        """
        Invalide le cache d'une catégorie spécifique.
        
        Args:
            category_id: ID de la catégorie
        
        Returns:
            Nombre de clés supprimées
        """
        count = 0
        count += self.delete("categories", f"detail:{category_id}") and 1 or 0
        count += self.delete("contacts", f"count:category:{category_id}") and 1 or 0
        return count
    
    def invalidate_contact_related(self, category_ids: Optional[List[int]] = None) -> int:
        """
        Invalide les caches liés aux contacts.
        
        Args:
            category_ids: Liste des IDs de catégories associées au contact
        
        Returns:
            Nombre de clés supprimées
        
        Requirements: 4.1, 4.2
        """
        count = 0
        # Invalider les stats globales
        count += self.invalidate_stats()
        
        # Invalider les comptages de catégories spécifiques
        if category_ids:
            for cat_id in category_ids:
                count += self.invalidate_category(cat_id)
        
        return count
    
    # =========================================================================
    # Méthode utilitaire avec fallback
    # =========================================================================
    
    def get_or_set(
        self,
        namespace: str,
        key: str,
        fallback_fn: Callable[[], Any],
        ttl: Optional[timedelta] = None
    ) -> Any:
        """
        Récupère du cache ou exécute le fallback et met en cache.
        
        Pattern cache-aside : lecture du cache, fallback sur fonction si miss.
        
        Args:
            namespace: Espace de noms
            key: Identifiant unique
            fallback_fn: Fonction à appeler si cache miss
            ttl: Durée de vie du cache
        
        Returns:
            Valeur du cache ou résultat du fallback
        
        Requirements: 3.2, 3.4
        """
        # Essayer le cache d'abord
        cached = self.get(namespace, key)
        if cached is not None:
            return cached
        
        # Fallback sur la fonction
        try:
            result = fallback_fn()
        except Exception as e:
            logger.error(f"Cache fallback error for {namespace}:{key}: {e}")
            raise
        
        # Mettre en cache (fail silently)
        self.set(namespace, key, result, ttl)
        
        return result
    
    # =========================================================================
    # Métriques
    # =========================================================================
    
    def get_metrics(self) -> dict:
        """
        Retourne les métriques du cache.
        
        Returns:
            Dictionnaire avec hits, misses, total, hit_rate
        
        Requirements: 6.1
        """
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0.0
        
        metrics = {
            "hits": self._hits,
            "misses": self._misses,
            "total": total,
            "hit_rate": round(hit_rate, 2)
        }
        
        # Logger un warning si le taux de miss est trop élevé
        # Requirements: 6.3
        if total > 10 and hit_rate < 50:
            logger.warning(
                f"Cache hit rate is low: {hit_rate:.1f}% ({self._hits} hits, {self._misses} misses)"
            )
        
        return metrics
    
    def reset_metrics(self) -> None:
        """Réinitialise les métriques du cache."""
        self._hits = 0
        self._misses = 0


# =========================================================================
# Instance globale et dépendance FastAPI
# =========================================================================

# Instance globale du service de cache (lazy-loaded)
_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """
    Retourne l'instance globale du service de cache.
    
    Utilisé comme dépendance FastAPI:
    ```python
    @router.get("/stats")
    async def get_stats(cache: CacheService = Depends(get_cache_service)):
        ...
    ```
    
    Returns:
        Instance CacheService
    """
    global _cache_service
    if _cache_service is None:
        # Réutiliser la connexion Redis du MonitoringService si disponible
        try:
            from app.services.monitoring_service import MonitoringService
            monitoring = MonitoringService()
            _cache_service = CacheService(redis_client=monitoring.redis_client)
            logger.info("CacheService initialized with MonitoringService Redis connection")
        except Exception as e:
            logger.warning(f"Could not reuse MonitoringService Redis: {e}")
            _cache_service = CacheService()
    return _cache_service


def invalidate_cache_on_contact_change(category_ids: Optional[List[int]] = None) -> None:
    """
    Fonction utilitaire pour invalider le cache après modification de contact.
    
    Args:
        category_ids: Liste des IDs de catégories associées au contact
    """
    try:
        cache = get_cache_service()
        cache.invalidate_contact_related(category_ids)
    except Exception as e:
        logger.warning(f"Failed to invalidate cache on contact change: {e}")


def invalidate_cache_on_category_change(category_id: Optional[int] = None) -> None:
    """
    Fonction utilitaire pour invalider le cache après modification de catégorie.
    
    Args:
        category_id: ID de la catégorie modifiée (None pour invalider toutes)
    """
    try:
        cache = get_cache_service()
        if category_id:
            cache.invalidate_category(category_id)
        cache.invalidate_categories()
    except Exception as e:
        logger.warning(f"Failed to invalidate cache on category change: {e}")
