"""
Tâches Celery pour l'envoi de messages WhatsApp via Wassenger API 2025
Gère l'envoi massif par lots, l'envoi individuel et les retries avec backoff exponentiel

Migration: Twilio Sandbox -> Wassenger 2025
Exigences: 6.1, 6.2, 6.4

Logique Message 2:
- Message 1 est envoyé au contact
- Si le contact répond (interaction) dans les 24h -> Message 2 envoyé IMMÉDIATEMENT
- Si le contact ne répond pas dans les 24h -> Message 2 N'EST PAS envoyé (campagne terminée pour ce contact)
- Cela permet aux campagnes de se terminer après 24h maximum

ROBUSTESSE 2025:
- Gestion des interruptions brutales (connexion perdue, crash serveur)
- Protection contre les doublons d'envoi
- Idempotence des tâches (réexécution sûre)
- Validation des données avant traitement
- Timeouts et circuit breakers

SYSTÈME ANTI-BAN 2025:
Ce module implémente une stratégie anti-ban complète pour éviter les bannissements WhatsApp.
Documentation complète: .kiro/specs/whatsapp-ban-prevention/design.md

Fonctions anti-ban principales:
- get_anti_ban_delay(): Calcule le délai avec randomisation (Requirements 1.1-1.6)
- get_warm_up_delay(): Délai adaptatif selon messages/jour (Requirements 2.1-2.5)
- should_take_strategic_pause(): Vérifie si pause requise (Requirements 3.1-3.4)
- get_strategic_pause_duration(): Durée de pause aléatoire (Requirements 3.1-3.5)
- simulate_human_behavior(): Micro-pauses aléatoires (Requirements 4.1)
- is_night_time(): Blocage heures de nuit (Requirements 4.2)
- get_message_length_delay(): Délai basé sur longueur (Requirements 4.3)
- detect_ban_risk(): Détection codes d'erreur dangereux (Requirements 5.1)
- check_error_thresholds(): Vérification seuils d'erreur (Requirements 5.2, 5.3, 5.5)
- is_safe_to_send(): Vérification globale avant envoi (Requirements 4.2, 5.2, 5.3, 6.1)

Variables d'environnement anti-ban (voir .env.example):
- ANTI_BAN_BASE_DELAY_MIN: Délai minimum de base (défaut: 15s)
- ANTI_BAN_BASE_DELAY_MAX: Délai maximum de base (défaut: 30s)
- ANTI_BAN_RANDOM_VARIATION: Variation aléatoire ±X secondes (défaut: 5s)
- ANTI_BAN_MIN_DELAY: Plancher absolu (défaut: 10s)
- ANTI_BAN_BATCH_SIZE: Taille des lots (défaut: 20)
"""
import logging
import asyncio
import time
import os
import random
from datetime import datetime
from typing import Optional, List
from celery.exceptions import MaxRetriesExceededError, SoftTimeLimitExceeded
from contextlib import contextmanager

from app.config import settings
from app.supabase_client import get_supabase_client, SupabaseDB
from app.tasks.celery_app import celery_app, monitoring_service
from app.services.wassenger_service import wassenger_service

# Configuration du logger
logger = logging.getLogger(__name__)

# ==========================================================================
# CONFIGURATION WASSENGER - ANTI-BAN SETTINGS 2025
# ==========================================================================
# Rate limit Wassenger: délai entre chaque message
# IMPORTANT: WhatsApp peut bannir les numéros qui envoient trop vite !
# 
# Recommandations 2025 pour éviter les bans:
# - Nouveaux comptes: 10-15 secondes entre messages
# - Comptes matures (>6 mois): 3-5 secondes entre messages
# - Messages identiques: risque de ban après 20-30 envois
# - Messages personnalisés: permet d'envoyer 500+ messages en sécurité
#
# Configuration actuelle: 5 secondes (optimisé pour comptes matures)
# Pour 100 messages: ~8 minutes d'envoi (100 * 5s = 500s ≈ 8min)
# Pour 1000 messages: ~1.5 heures d'envoi (1000 * 5s = 5000s ≈ 1.4h)
WASSENGER_RATE_LIMIT_SECONDS = 5

# Batch configuration pour envois massifs
# Envoyer par lots de 50 messages, puis pause de 60 secondes
BATCH_SIZE = 50
BATCH_PAUSE_SECONDS = 60  # 1 minute de pause entre les lots

# Délai avant l'envoi du Message 2 (24 heures en secondes)
MESSAGE_2_DELAY_SECONDS = 24 * 60 * 60  # 86400 secondes = 24h

# Timestamp du dernier envoi pour le rate limiting Sandbox
_last_send_timestamp: float = 0.0

# ==========================================================================
# CONFIGURATION ANTI-BAN 2025 - PROTECTION MAXIMALE
# ==========================================================================
# Ce système implémente une stratégie anti-ban complète pour éviter les
# bannissements WhatsApp. Les délais sont beaucoup plus longs que la config
# standard, avec randomisation et pauses stratégiques.
#
# IMPORTANT: Avec cette configuration, l'envoi de 1000 messages prendra
# environ 8 heures au lieu de 1.5 heures. C'est un compromis nécessaire
# pour éviter les bannissements.
#
# Requirements: 1.1, 1.5, 3.1, 3.2, 3.3, 3.4, 5.1
# ==========================================================================

# ---------------------------------------------------------------------------
# DÉLAIS DE BASE ANTI-BAN (Requirements: 1.1, 1.5)
# ---------------------------------------------------------------------------
# Délai de base entre messages (15-30 secondes selon warm-up)
# Ces valeurs sont adaptatives selon le nombre de messages envoyés
ANTI_BAN_BASE_DELAY_MIN = int(os.getenv("ANTI_BAN_BASE_DELAY_MIN", "15"))
ANTI_BAN_BASE_DELAY_MAX = int(os.getenv("ANTI_BAN_BASE_DELAY_MAX", "30"))

# Variation aléatoire ajoutée au délai de base (±5 secondes)
# Permet d'éviter les patterns détectables par WhatsApp
ANTI_BAN_RANDOM_VARIATION = int(os.getenv("ANTI_BAN_RANDOM_VARIATION", "5"))

# Délai minimum absolu - jamais en dessous de cette valeur
# Même avec la randomisation, le délai ne descendra pas sous 10 secondes
ANTI_BAN_MIN_DELAY = int(os.getenv("ANTI_BAN_MIN_DELAY", "10"))

# Délai "typing" humain simulé (1-3 secondes)
# Simule le temps qu'un humain mettrait à taper un message
HUMAN_TYPING_DELAY_MIN = 1
HUMAN_TYPING_DELAY_MAX = 3

# ---------------------------------------------------------------------------
# CONFIGURATION DES LOTS ANTI-BAN (Requirements: 3.1)
# ---------------------------------------------------------------------------
# Taille des lots réduite pour plus de pauses stratégiques
# 20 messages par lot au lieu de 50
ANTI_BAN_BATCH_SIZE = int(os.getenv("ANTI_BAN_BATCH_SIZE", "20"))

# ---------------------------------------------------------------------------
# SEUILS DE PAUSES STRATÉGIQUES (Requirements: 3.1, 3.2, 3.3, 3.4)
# ---------------------------------------------------------------------------
# Pauses automatiques après un certain nombre de messages consécutifs
# Ces pauses simulent le comportement d'un humain qui fait des pauses
PAUSE_THRESHOLD_1 = 20   # Pause après 20 messages consécutifs
PAUSE_THRESHOLD_2 = 40   # Pause après 40 messages consécutifs
PAUSE_THRESHOLD_3 = 60   # Pause après 60 messages consécutifs
PAUSE_THRESHOLD_4 = 100  # Pause après 100 messages consécutifs

# Durées de pauses stratégiques (en secondes)
# Les durées sont des tuples (min, max) pour randomisation
PAUSE_DURATION_1 = (180, 300)    # 3-5 minutes après 20 messages
PAUSE_DURATION_2 = (300, 480)    # 5-8 minutes après 40 messages
PAUSE_DURATION_3 = (600, 900)    # 10-15 minutes après 60 messages
PAUSE_DURATION_4 = (1200, 1800)  # 20-30 minutes après 100 messages

# ---------------------------------------------------------------------------
# SIMULATION DE COMPORTEMENT HUMAIN (Requirements: 4.1)
# ---------------------------------------------------------------------------
# Probabilité de micro-pause aléatoire (10% = 0.10)
# Avec 10% de probabilité, une micro-pause sera ajoutée
MICRO_PAUSE_PROBABILITY = 0.10

# Durée des micro-pauses (30 secondes à 2 minutes)
MICRO_PAUSE_DURATION = (30, 120)

# ---------------------------------------------------------------------------
# DÉTECTION DE RISQUE DE BAN (Requirements: 5.1)
# ---------------------------------------------------------------------------
# Codes d'erreur dangereux indiquant un risque de ban imminent
# Si l'API retourne un de ces codes, une pause d'urgence est déclenchée
BAN_RISK_ERROR_CODES = [
    "rate_limit",      # Limite de débit atteinte
    "spam_detected",   # WhatsApp a détecté du spam
    "blocked",         # Numéro bloqué
    "429",             # HTTP 429 Too Many Requests
]

# ---------------------------------------------------------------------------
# SEUILS D'ERREUR ET ARRÊT D'URGENCE (Requirements: 5.2, 5.3, 5.5)
# ---------------------------------------------------------------------------
# Nombre d'erreurs consécutives avant arrêt total
CONSECUTIVE_ERROR_HALT_THRESHOLD = 3

# Fenêtre de temps pour compter les erreurs (en minutes)
ERROR_WINDOW_MINUTES = 10

# Nombre d'erreurs dans la fenêtre avant arrêt total
ERROR_COUNT_HALT_THRESHOLD = 5

# Seuil de taux d'erreur pour déclencher un warning (5%)
ERROR_RATE_WARNING_THRESHOLD = 0.05

# ---------------------------------------------------------------------------
# DURÉES DE PAUSE D'URGENCE (Requirements: 5.1, 5.3)
# ---------------------------------------------------------------------------
# Pause d'urgence en cas de détection de risque de ban (30 minutes)
EMERGENCY_PAUSE_SECONDS = 1800

# Arrêt prolongé en cas d'erreurs multiples (1 heure)
EXTENDED_HALT_SECONDS = 3600

# ==========================================================================
# ROBUSTESSE - PROTECTION CONTRE LES DOUBLONS ET INTERRUPTIONS
# ==========================================================================
# TTL pour les verrous d'idempotence (5 minutes)
IDEMPOTENCY_LOCK_TTL = 300

# Timeout pour les opérations d'envoi (30 secondes)
SEND_OPERATION_TIMEOUT = 30

# Nombre maximum de vérifications de statut avant abandon
MAX_STATUS_CHECKS = 3


# ==========================================================================
# FONCTIONS ANTI-BAN - CALCUL DES DÉLAIS
# ==========================================================================

def get_warm_up_delay(messages_sent_today: int) -> float:
    """
    Calcule le délai de base selon le nombre de messages envoyés aujourd'hui.
    
    Stratégie de warm-up progressive:
    - 0-30 messages: 25-35 secondes (démarrage très lent)
    - 30-80 messages: 20-28 secondes (accélération progressive)
    - 80-200 messages: 15-22 secondes (vitesse de croisière)
    - 200-500 messages: 18-25 secondes (ralentissement)
    - 500+ messages: 22-30 secondes (proche de la limite)
    
    Args:
        messages_sent_today: Nombre de messages envoyés aujourd'hui
    
    Returns:
        Délai de base en secondes (randomisé dans la plage appropriée)
    
    Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5
    """
    if messages_sent_today < 30:
        # Phase 1: Démarrage très lent (warm-up initial)
        return random.uniform(25, 35)
    
    elif messages_sent_today < 80:
        # Phase 2: Accélération progressive
        return random.uniform(20, 28)
    
    elif messages_sent_today < 200:
        # Phase 3: Vitesse de croisière (optimal)
        return random.uniform(15, 22)
    
    elif messages_sent_today < 500:
        # Phase 4: Ralentissement (approche de la limite)
        return random.uniform(18, 25)
    
    else:
        # Phase 5: Très lent (proche de la limite quotidienne)
        return random.uniform(22, 30)


def get_anti_ban_delay(messages_sent_today: int) -> float:
    """
    Calcule le délai anti-ban total avec randomisation et warm-up.
    
    Le délai est composé de:
    1. Délai de base selon le warm-up (15-35 secondes selon la phase)
    2. Variation aléatoire (±5 secondes)
    3. Délai "typing" humain (1-3 secondes)
    
    Le délai final est garanti d'être au minimum ANTI_BAN_MIN_DELAY (10 secondes).
    
    Args:
        messages_sent_today: Nombre de messages envoyés aujourd'hui
    
    Returns:
        Délai total en secondes (minimum 10 secondes, maximum ~40 secondes)
    
    Validates: Requirements 1.1, 1.2, 1.3, 1.5, 1.6
    """
    # 1. Obtenir le délai de base selon le warm-up
    base_delay = get_warm_up_delay(messages_sent_today)
    
    # 2. Ajouter variation aléatoire (±5 secondes)
    random_variation = random.uniform(
        -ANTI_BAN_RANDOM_VARIATION, 
        ANTI_BAN_RANDOM_VARIATION
    )
    
    # 3. Ajouter délai "typing" humain (1-3 secondes)
    typing_delay = random.uniform(HUMAN_TYPING_DELAY_MIN, HUMAN_TYPING_DELAY_MAX)
    
    # Calculer le délai total
    total_delay = base_delay + random_variation + typing_delay
    
    # Appliquer le plancher minimum (jamais en dessous de 10 secondes)
    final_delay = max(total_delay, ANTI_BAN_MIN_DELAY)
    
    logger.info(
        f"Délai anti-ban calculé: {final_delay:.1f}s "
        f"(base={base_delay:.1f}s, variation={random_variation:.1f}s, typing={typing_delay:.1f}s)"
    )
    
    return final_delay


# ==========================================================================
# FONCTIONS ANTI-BAN - PAUSES STRATÉGIQUES
# ==========================================================================

def should_take_strategic_pause(consecutive_messages: int) -> bool:
    """
    Vérifie si une pause stratégique est nécessaire.
    
    Les pauses stratégiques sont déclenchées à des seuils spécifiques
    pour simuler un comportement humain qui fait des pauses régulières.
    
    Args:
        consecutive_messages: Nombre de messages envoyés consécutivement
    
    Returns:
        True si une pause est requise à ce seuil exact
    
    Validates: Requirements 3.1, 3.2, 3.3, 3.4
    """
    return consecutive_messages in [
        PAUSE_THRESHOLD_1,  # 20 messages
        PAUSE_THRESHOLD_2,  # 40 messages
        PAUSE_THRESHOLD_3,  # 60 messages
        PAUSE_THRESHOLD_4,  # 100 messages
    ]


def get_strategic_pause_duration(consecutive_messages: int) -> float:
    """
    Calcule la durée de pause stratégique avec randomisation.
    
    Les durées de pause augmentent avec le nombre de messages envoyés:
    - 20 messages: 3-5 minutes
    - 40 messages: 5-8 minutes
    - 60 messages: 10-15 minutes
    - 100 messages: 20-30 minutes
    
    Args:
        consecutive_messages: Nombre de messages envoyés consécutivement
    
    Returns:
        Durée de pause en secondes (0 si aucune pause requise)
    
    Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5
    """
    if consecutive_messages >= PAUSE_THRESHOLD_4:
        min_pause, max_pause = PAUSE_DURATION_4  # 20-30 minutes
    elif consecutive_messages >= PAUSE_THRESHOLD_3:
        min_pause, max_pause = PAUSE_DURATION_3  # 10-15 minutes
    elif consecutive_messages >= PAUSE_THRESHOLD_2:
        min_pause, max_pause = PAUSE_DURATION_2  # 5-8 minutes
    elif consecutive_messages >= PAUSE_THRESHOLD_1:
        min_pause, max_pause = PAUSE_DURATION_1  # 3-5 minutes
    else:
        return 0.0
    
    pause_duration = random.uniform(min_pause, max_pause)
    
    logger.info(
        f"Pause stratégique: {pause_duration/60:.1f} minutes "
        f"après {consecutive_messages} messages consécutifs"
    )
    
    return pause_duration


def reset_consecutive_counter(redis_client) -> None:
    """
    Réinitialise le compteur de messages consécutifs après une pause stratégique.
    
    Cette fonction est appelée après chaque pause stratégique pour
    recommencer le comptage à zéro.
    
    Args:
        redis_client: Client Redis pour accéder au compteur
    
    Validates: Requirements 3.6
    """
    try:
        redis_client.set("anti_ban:consecutive_messages", 0)
        logger.debug("Compteur de messages consécutifs réinitialisé à 0")
    except Exception as e:
        logger.error(f"Erreur réinitialisation compteur consécutif: {e}")


# ==========================================================================
# FONCTIONS ANTI-BAN - SIMULATION DE COMPORTEMENT HUMAIN
# ==========================================================================

def simulate_human_behavior() -> float:
    """
    Simule un comportement humain avec des micro-pauses aléatoires.
    
    Avec 10% de probabilité (MICRO_PAUSE_PROBABILITY), ajoute une micro-pause
    de 30-120 secondes (MICRO_PAUSE_DURATION) pour simuler un comportement
    humain naturel.
    
    Returns:
        Durée de micro-pause en secondes (0.0 si pas de pause)
    
    Validates: Requirements 4.1
    """
    if random.random() < MICRO_PAUSE_PROBABILITY:
        min_pause, max_pause = MICRO_PAUSE_DURATION
        pause_duration = random.uniform(min_pause, max_pause)
        logger.info(f"Micro-pause humaine: {pause_duration:.0f}s")
        return pause_duration
    return 0.0


def is_night_time() -> bool:
    """
    Vérifie si l'heure actuelle est entre 23h et 6h (heures de nuit).
    
    DÉSACTIVÉ: Cette fonction retourne toujours False pour permettre
    l'envoi de messages 24h/24. Le blocage nocturne a été désactivé
    car le serveur Render est en UTC et cela causait des problèmes
    de synchronisation avec le fuseau horaire local.
    
    Returns:
        False (toujours) - blocage nocturne désactivé
    
    Validates: Requirements 4.2 (DÉSACTIVÉ)
    """
    # DÉSACTIVÉ: Retourne toujours False pour permettre l'envoi 24h/24
    # L'ancien code vérifiait: current_hour >= 23 or current_hour < 6
    return False


def get_message_length_delay(message_length: int) -> float:
    """
    Calcule un délai supplémentaire basé sur la longueur du message.
    
    Messages plus longs = délai légèrement plus long pour simuler
    le temps qu'un humain mettrait à lire/écrire un message long.
    
    Formule: 1 seconde par 500 caractères, maximum 5 secondes.
    
    Args:
        message_length: Longueur du message en caractères
    
    Returns:
        Délai supplémentaire en secondes (0.0 à 5.0 secondes)
    
    Validates: Requirements 4.3
    """
    if message_length <= 0:
        return 0.0
    
    # 1 seconde par 500 caractères, max 5 secondes
    extra_delay = min(message_length / 500.0, 5.0)
    return extra_delay


# ==========================================================================
# FONCTIONS ANTI-BAN - DÉTECTION DE RISQUE DE BAN
# ==========================================================================

def detect_ban_risk(error_code: str, error_message: str) -> dict:
    """
    Analyse un code d'erreur pour détecter un risque de ban.
    
    Cette fonction examine les codes d'erreur retournés par l'API Wassenger
    pour identifier les signes de bannissement imminent. Si un code dangereux
    est détecté, une pause d'urgence de 30 minutes est recommandée.
    
    Codes d'erreur dangereux:
    - rate_limit: Limite de débit atteinte
    - spam_detected: WhatsApp a détecté du spam
    - blocked: Numéro bloqué
    - 429: HTTP 429 Too Many Requests
    
    Args:
        error_code: Code d'erreur retourné par l'API Wassenger
        error_message: Message d'erreur associé
    
    Returns:
        Dictionnaire avec:
        - is_ban_risk: True si risque de ban détecté
        - action: Action recommandée ('emergency_pause', 'halt', 'continue')
        - pause_duration: Durée de pause en secondes (0 si pas de pause)
    
    Validates: Requirements 5.1
    """
    result = {
        "is_ban_risk": False,
        "action": "continue",
        "pause_duration": 0
    }
    
    # Convertir en chaînes pour la comparaison (gestion des None)
    error_code_str = str(error_code).lower() if error_code else ""
    error_message_str = str(error_message).lower() if error_message else ""
    
    # Vérifier les codes d'erreur dangereux
    for danger_code in BAN_RISK_ERROR_CODES:
        danger_code_lower = danger_code.lower()
        if danger_code_lower in error_code_str or danger_code_lower in error_message_str:
            result["is_ban_risk"] = True
            result["action"] = "emergency_pause"
            result["pause_duration"] = EMERGENCY_PAUSE_SECONDS  # 30 minutes
            
            logger.critical(
                f"⚠️ RISQUE DE BAN DÉTECTÉ: {error_code} - {error_message}. "
                f"Pause d'urgence de {EMERGENCY_PAUSE_SECONDS/60:.0f} minutes recommandée."
            )
            break
    
    return result


def check_error_thresholds(redis_client) -> dict:
    """
    Vérifie les seuils d'erreur pour décider si l'envoi doit être arrêté.
    
    Cette fonction analyse les compteurs d'erreur stockés dans Redis pour
    déterminer si l'envoi de messages doit être interrompu. Les critères sont:
    
    1. Erreurs consécutives: Si 3 erreurs consécutives se produisent, arrêt total
    2. Erreurs dans la fenêtre: Si 5 erreurs en 10 minutes, arrêt pour 1 heure
    3. Taux d'erreur: Si > 5%, warning (pas d'arrêt)
    
    Args:
        redis_client: Client Redis pour accéder aux compteurs
    
    Returns:
        Dictionnaire avec:
        - should_halt: True si l'envoi doit être arrêté
        - reason: Raison de l'arrêt (None si pas d'arrêt)
        - halt_duration: Durée d'arrêt en secondes (0 si pas d'arrêt)
        - warning: Message de warning si taux d'erreur élevé (None sinon)
    
    Validates: Requirements 5.2, 5.3, 5.5
    """
    result = {
        "should_halt": False,
        "reason": None,
        "halt_duration": 0,
        "warning": None
    }
    
    try:
        # Vérifier les erreurs consécutives (Requirements 5.2)
        consecutive_errors_raw = redis_client.get("anti_ban:consecutive_errors")
        consecutive_errors = int(consecutive_errors_raw) if consecutive_errors_raw else 0
        
        if consecutive_errors >= CONSECUTIVE_ERROR_HALT_THRESHOLD:
            result["should_halt"] = True
            result["reason"] = f"{consecutive_errors} erreurs consécutives (seuil: {CONSECUTIVE_ERROR_HALT_THRESHOLD})"
            result["halt_duration"] = EXTENDED_HALT_SECONDS  # 1 heure
            
            logger.critical(
                f"⚠️ ARRÊT D'URGENCE: {consecutive_errors} erreurs consécutives. "
                f"Arrêt pour {EXTENDED_HALT_SECONDS/60:.0f} minutes."
            )
            return result
        
        # Vérifier les erreurs dans la fenêtre de temps (Requirements 5.3)
        # On utilise une clé avec le timestamp arrondi à la minute
        current_minute = datetime.now().strftime('%Y%m%d%H%M')
        
        # Compter les erreurs dans les dernières ERROR_WINDOW_MINUTES minutes
        errors_in_window = 0
        for i in range(ERROR_WINDOW_MINUTES):
            # Calculer le timestamp de chaque minute dans la fenêtre
            from datetime import timedelta
            check_time = datetime.now() - timedelta(minutes=i)
            window_key = f"anti_ban:errors:{check_time.strftime('%Y%m%d%H%M')}"
            
            errors_raw = redis_client.get(window_key)
            if errors_raw:
                errors_in_window += int(errors_raw)
        
        if errors_in_window >= ERROR_COUNT_HALT_THRESHOLD:
            result["should_halt"] = True
            result["reason"] = f"{errors_in_window} erreurs en {ERROR_WINDOW_MINUTES} minutes (seuil: {ERROR_COUNT_HALT_THRESHOLD})"
            result["halt_duration"] = EXTENDED_HALT_SECONDS  # 1 heure
            
            logger.critical(
                f"⚠️ ARRÊT D'URGENCE: {errors_in_window} erreurs en {ERROR_WINDOW_MINUTES} minutes. "
                f"Arrêt pour {EXTENDED_HALT_SECONDS/60:.0f} minutes."
            )
            return result
        
        # Vérifier le taux d'erreur (Requirements 5.5)
        total_sent_raw = redis_client.get("anti_ban:total_sent")
        total_errors_raw = redis_client.get("anti_ban:total_errors")
        
        total_sent = int(total_sent_raw) if total_sent_raw else 0
        total_errors = int(total_errors_raw) if total_errors_raw else 0
        
        if total_sent > 0:
            error_rate = total_errors / total_sent
            if error_rate >= ERROR_RATE_WARNING_THRESHOLD:
                result["warning"] = (
                    f"Taux d'erreur élevé: {error_rate:.1%} "
                    f"({total_errors}/{total_sent})"
                )
                logger.warning(f"⚠️ {result['warning']}")
        
        return result
        
    except Exception as e:
        logger.error(f"Erreur lors de la vérification des seuils d'erreur: {e}")
        # En cas d'erreur Redis, on n'arrête pas (fail-open)
        return result


def is_safe_to_send(redis_client, messages_sent_today: int) -> tuple:
    """
    Vérifie tous les critères anti-ban avant d'envoyer un message.
    
    Cette fonction combine toutes les vérifications anti-ban pour déterminer
    si l'envoi d'un message est sûr. Les vérifications incluent:
    
    1. Heures de nuit (23h-6h): Envoi bloqué
    2. Limite quotidienne (1000 messages): Envoi bloqué
    3. Seuils d'erreur: Envoi bloqué si trop d'erreurs
    4. Pause d'urgence en cours: Envoi bloqué
    
    Args:
        redis_client: Client Redis pour accéder aux compteurs
        messages_sent_today: Nombre de messages envoyés aujourd'hui
    
    Returns:
        Tuple (can_send: bool, reason: str)
        - can_send: True si l'envoi est autorisé
        - reason: "OK" si autorisé, sinon la raison du blocage
    
    Validates: Requirements 4.2, 5.2, 5.3, 6.1
    """
    # Vérifier si c'est la nuit (Requirements 4.2)
    if is_night_time():
        return False, "Heures de nuit (23h-6h) - envoi reporté à 7h"
    
    # Vérifier la limite quotidienne (Requirements 6.1)
    # Note: La limite est de 1000 messages par jour
    DAILY_LIMIT = 1000
    if messages_sent_today >= DAILY_LIMIT:
        return False, f"Limite quotidienne de {DAILY_LIMIT} messages atteinte"
    
    # Vérifier les seuils d'erreur (Requirements 5.2, 5.3)
    try:
        error_check = check_error_thresholds(redis_client)
        if error_check["should_halt"]:
            return False, f"Arrêt d'urgence: {error_check['reason']}"
    except Exception as e:
        logger.error(f"Erreur lors de la vérification des seuils d'erreur: {e}")
        # En cas d'erreur Redis, on autorise (fail-open)
    
    # Vérifier si une pause d'urgence est en cours
    try:
        emergency_pause_until = redis_client.get("anti_ban:emergency_pause_until")
        if emergency_pause_until:
            # Décoder si c'est en bytes
            if isinstance(emergency_pause_until, bytes):
                emergency_pause_until = emergency_pause_until.decode()
            
            pause_end = datetime.fromisoformat(emergency_pause_until)
            if datetime.now() < pause_end:
                remaining = (pause_end - datetime.now()).seconds
                return False, f"Pause d'urgence en cours ({remaining}s restantes)"
    except Exception as e:
        logger.error(f"Erreur lors de la vérification de la pause d'urgence: {e}")
        # En cas d'erreur, on autorise (fail-open)
    
    return True, "OK"


def get_idempotency_key(message_id: int, operation: str = "send") -> str:
    """
    Génère une clé d'idempotence unique pour une opération sur un message.
    Permet d'éviter les doublons en cas de réexécution de tâche.
    
    Args:
        message_id: ID du message
        operation: Type d'opération (send, retry, etc.)
    
    Returns:
        Clé d'idempotence unique
    """
    return f"idempotency:{operation}:{message_id}"


def acquire_idempotency_lock(message_id: int, operation: str = "send") -> bool:
    """
    Acquiert un verrou d'idempotence pour éviter les doublons.
    
    Args:
        message_id: ID du message
        operation: Type d'opération
    
    Returns:
        True si le verrou est acquis, False si déjà verrouillé
    """
    try:
        key = get_idempotency_key(message_id, operation)
        redis_client = monitoring_service.redis_client
        
        # SET NX avec TTL - retourne True si la clé n'existait pas
        acquired = redis_client.set(key, datetime.utcnow().isoformat(), nx=True, ex=IDEMPOTENCY_LOCK_TTL)
        
        if acquired:
            logger.debug(f"Verrou d'idempotence acquis: {key}")
        else:
            logger.warning(f"Verrou d'idempotence déjà existant: {key} - opération ignorée")
        
        return bool(acquired)
    except Exception as e:
        logger.error(f"Erreur acquisition verrou idempotence: {e}")
        # En cas d'erreur Redis, on autorise l'opération (fail-open)
        return True


def release_idempotency_lock(message_id: int, operation: str = "send") -> None:
    """
    Libère un verrou d'idempotence.
    
    Args:
        message_id: ID du message
        operation: Type d'opération
    """
    try:
        key = get_idempotency_key(message_id, operation)
        redis_client = monitoring_service.redis_client
        redis_client.delete(key)
        logger.debug(f"Verrou d'idempotence libéré: {key}")
    except Exception as e:
        logger.error(f"Erreur libération verrou idempotence: {e}")


@contextmanager
def idempotency_guard(message_id: int, operation: str = "send"):
    """
    Context manager pour garantir l'idempotence d'une opération.
    
    Usage:
        with idempotency_guard(message_id, "send") as can_proceed:
            if can_proceed:
                # Effectuer l'opération
    """
    can_proceed = acquire_idempotency_lock(message_id, operation)
    try:
        yield can_proceed
    finally:
        if can_proceed:
            release_idempotency_lock(message_id, operation)


def validate_message_data(message: dict) -> tuple[bool, str]:
    """
    Valide les données d'un message avant envoi.
    
    Args:
        message: Dictionnaire du message
    
    Returns:
        Tuple (is_valid, error_message)
    """
    if not message:
        return False, "Message non trouvé"
    
    required_fields = ["id", "contact_id", "campaign_id", "content"]
    for field in required_fields:
        if field not in message or message[field] is None:
            return False, f"Champ requis manquant: {field}"
    
    if not message.get("content", "").strip():
        return False, "Contenu du message vide"
    
    return True, ""


def validate_contact_data(contact: dict) -> tuple[bool, str]:
    """
    Valide les données d'un contact avant envoi.
    
    Args:
        contact: Dictionnaire du contact
    
    Returns:
        Tuple (is_valid, error_message)
    """
    if not contact:
        return False, "Contact non trouvé"
    
    phone = contact.get("whatsapp_id") or contact.get("full_number")
    if not phone:
        return False, "Numéro de téléphone manquant"
    
    # Validation basique du format de numéro
    phone_clean = phone.replace("+", "").replace(" ", "")
    if not phone_clean.isdigit() or len(phone_clean) < 8:
        return False, f"Format de numéro invalide: {phone}"
    
    return True, ""


def is_campaign_active(client, campaign_id: int, message_type: str = "message_1") -> tuple[bool, str]:
    """
    Vérifie si une campagne est active et peut recevoir des envois.
    
    Args:
        client: Client Supabase
        campaign_id: ID de la campagne
        message_type: Type de message (message_1 ou message_2)
    
    Returns:
        Tuple (is_active, reason)
    """
    try:
        campaign_response = client.table("campaigns").select("status").eq("id", campaign_id).limit(1).execute()
        
        if not campaign_response.data:
            return False, "Campagne non trouvée"
        
        campaign_status = campaign_response.data[0].get("status")
        
        # Bloquer si campagne arrêtée manuellement
        if campaign_status == "failed":
            return False, "Campagne arrêtée manuellement"
        
        # Pour message_1, bloquer si campagne terminée
        if campaign_status == "completed" and message_type != "message_2":
            return False, "Campagne terminée"
        
        return True, ""
        
    except Exception as e:
        logger.error(f"Erreur vérification statut campagne {campaign_id}: {e}")
        # En cas d'erreur, on autorise (fail-open) pour ne pas bloquer les envois
        return True, ""


def get_db() -> SupabaseDB:
    """Crée une nouvelle instance de base de données Supabase pour les tâches Celery"""
    return SupabaseDB()


def run_async(coro):
    """Exécute une coroutine de manière synchrone pour Celery"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def calculate_retry_delay(attempt: int) -> int:
    """
    Calcule le délai avant le prochain retry avec backoff exponentiel.
    
    Formule: délai = 60 × 2^(tentative-1) secondes
    - Tentative 1: 60s
    - Tentative 2: 120s
    - Tentative 3: 240s
    
    Args:
        attempt: Numéro de la tentative (1, 2, 3)
    
    Returns:
        Délai en secondes
    
    Exigences: 6.3
    """
    base_delay = settings.RETRY_BASE_DELAY_SECONDS  # 60 secondes
    return base_delay * (2 ** (attempt - 1))


def wait_for_wassenger_rate_limit() -> None:
    """
    Attend le délai nécessaire pour respecter le rate limit anti-ban Wassenger.
    
    Cette fonction implémente le système anti-ban complet avec:
    1. Vérification is_safe_to_send() avant chaque envoi (Requirements 4.2, 5.2, 5.3, 6.1)
    2. Délai adaptatif via get_anti_ban_delay() avec warm-up (Requirements 1.1, 1.2, 1.3, 2.1-2.5)
    3. Micro-pauses humaines aléatoires via simulate_human_behavior() (Requirements 4.1)
    
    Le délai est calculé dynamiquement selon:
    - Le nombre de messages envoyés aujourd'hui (warm-up progressif)
    - Une variation aléatoire (±5 secondes)
    - Un délai "typing" humain (1-3 secondes)
    - Des micro-pauses aléatoires (10% de probabilité, 30-120 secondes)
    
    Validates: Requirements 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 2.4, 2.5, 4.1, 4.2, 5.2, 5.3, 6.1
    """
    global _last_send_timestamp
    
    try:
        redis_client = monitoring_service.redis_client
        
        # =======================================================================
        # ÉTAPE 1: Récupérer le compteur de messages du jour depuis Redis
        # =======================================================================
        messages_today_raw = redis_client.get("anti_ban:messages_today")
        messages_sent_today = int(messages_today_raw) if messages_today_raw else 0
        
        # =======================================================================
        # ÉTAPE 2: Vérification is_safe_to_send() (Requirements 4.2, 5.2, 5.3, 6.1)
        # =======================================================================
        can_send, reason = is_safe_to_send(redis_client, messages_sent_today)
        if not can_send:
            logger.warning(f"⚠️ Envoi bloqué par anti-ban: {reason}")
            # Lever une exception pour que la tâche soit réessayée plus tard
            raise RuntimeError(f"Envoi bloqué: {reason}")
        
        # =======================================================================
        # ÉTAPE 3: Calculer le délai anti-ban adaptatif (Requirements 1.1-1.6, 2.1-2.5)
        # =======================================================================
        anti_ban_delay = get_anti_ban_delay(messages_sent_today)
        
        # =======================================================================
        # ÉTAPE 4: Appliquer le délai en tenant compte du temps écoulé
        # =======================================================================
        if _last_send_timestamp > 0:
            elapsed = time.time() - _last_send_timestamp
            if elapsed < anti_ban_delay:
                wait_time = anti_ban_delay - elapsed
                logger.info(
                    f"Anti-ban rate limit: attente de {wait_time:.1f}s "
                    f"(délai total: {anti_ban_delay:.1f}s, écoulé: {elapsed:.1f}s, "
                    f"messages aujourd'hui: {messages_sent_today})"
                )
                time.sleep(wait_time)
        else:
            # Premier message de la session - appliquer le délai complet
            logger.info(
                f"Anti-ban rate limit (premier message): attente de {anti_ban_delay:.1f}s "
                f"(messages aujourd'hui: {messages_sent_today})"
            )
            time.sleep(anti_ban_delay)
        
        # =======================================================================
        # ÉTAPE 5: Micro-pauses humaines aléatoires (Requirements 4.1)
        # =======================================================================
        micro_pause = simulate_human_behavior()
        if micro_pause > 0:
            logger.info(f"Micro-pause humaine appliquée: {micro_pause:.0f}s")
            time.sleep(micro_pause)
        
        # =======================================================================
        # ÉTAPE 6: Mettre à jour le timestamp après l'attente
        # =======================================================================
        _last_send_timestamp = time.time()
        
    except RuntimeError:
        # Re-lever les erreurs de blocage anti-ban
        raise
    except Exception as e:
        # En cas d'erreur Redis ou autre, fallback sur le délai fixe original
        logger.error(f"Erreur système anti-ban, fallback sur délai fixe: {e}")
        
        if _last_send_timestamp > 0:
            elapsed = time.time() - _last_send_timestamp
            if elapsed < WASSENGER_RATE_LIMIT_SECONDS:
                wait_time = WASSENGER_RATE_LIMIT_SECONDS - elapsed
                logger.debug(f"Rate limit Wassenger (fallback): attente de {wait_time:.2f}s")
                time.sleep(wait_time)
        
        _last_send_timestamp = time.time()


def has_contact_interacted(client, campaign_id: int, contact_id: int, since_timestamp: str = None) -> bool:
    """
    Vérifie si un contact a eu une interaction (réponse) pour une campagne donnée.
    
    Cette fonction est utilisée pour décider si le Message 2 doit être envoyé.
    Si le contact a répondu au Message 1, on n'envoie pas le Message 2.
    
    Args:
        client: Client Supabase
        campaign_id: ID de la campagne
        contact_id: ID du contact
        since_timestamp: Timestamp ISO (optionnel, pour filtrer les interactions après cette date)
    
    Returns:
        True si le contact a eu une interaction, False sinon
    """
    try:
        query = client.table("interactions").select("id", count="exact").eq(
            "campaign_id", campaign_id
        ).eq(
            "contact_id", contact_id
        ).in_(
            "interaction_type", ["reply", "reaction"]  # Seules les réponses et réactions comptent
        )
        
        if since_timestamp:
            query = query.gte("received_at", since_timestamp)
        
        response = query.execute()
        interaction_count = response.count or 0
        
        return interaction_count > 0
        
    except Exception as e:
        logger.error(f"Erreur vérification interaction contact {contact_id}: {e}")
        return False  # En cas d'erreur, on considère qu'il n'y a pas d'interaction (sécurité)


def update_campaign_statistics(client, campaign_id: int, success: bool) -> None:
    """
    Met à jour les statistiques de la campagne après l'envoi d'un message.
    
    Args:
        client: Client Supabase
        campaign_id: ID de la campagne
        success: True si l'envoi a réussi, False sinon
    
    Exigences: 6.6
    """
    try:
        # Récupérer la campagne
        campaign_response = client.table("campaigns").select("*").eq("id", campaign_id).limit(1).execute()
        if not campaign_response.data:
            logger.warning(f"Campagne {campaign_id} non trouvée pour mise à jour des statistiques")
            return
        
        campaign = campaign_response.data[0]
        
        if success:
            # Incrémenter les compteurs de succès
            client.table("campaigns").update({
                "sent_count": (campaign.get("sent_count") or 0) + 1,
                "success_count": (campaign.get("success_count") or 0) + 1
            }).eq("id", campaign_id).execute()
        else:
            # Incrémenter le compteur d'échecs
            client.table("campaigns").update({
                "failed_count": (campaign.get("failed_count") or 0) + 1
            }).eq("id", campaign_id).execute()
        
        logger.debug(f"Statistiques campagne {campaign_id} mises à jour (success={success})")
        
    except Exception as e:
        logger.error(f"Erreur mise à jour statistiques campagne {campaign_id}: {e}")


@celery_app.task(
    bind=True,
    name="app.tasks.message_tasks.send_single_message",
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
    soft_time_limit=60,  # Timeout souple de 60 secondes
    time_limit=90,  # Timeout dur de 90 secondes
)
def send_single_message(
    self,
    message_id: int,
    is_template: bool = True,
    template_name: Optional[str] = None,
    content_sid: Optional[str] = None
) -> dict:
    """
    Envoie un message individuel via Wassenger WhatsApp API.
    
    ROBUSTESSE:
    - Verrou d'idempotence pour éviter les doublons
    - Validation des données avant envoi
    - Vérification du statut de la campagne
    - Gestion des timeouts
    - Protection contre les interruptions
    
    Intègre le monitoring pour:
    - Vérifier la limite quotidienne avant envoi (1000 messages/jour)
    - Incrémenter les compteurs de messages envoyés
    - Incrémenter les compteurs d'erreurs en cas d'échec
    
    Args:
        message_id: ID du message dans la base de données
        is_template: True pour Message 1 (template), False pour Message 2 (texte)
        template_name: Nom du template WhatsApp (pour référence, non utilisé avec Wassenger)
        content_sid: SID du template (non utilisé avec Wassenger, conservé pour compatibilité)
    
    Returns:
        Dictionnaire avec le résultat de l'envoi
    
    Exigences: 1.1, 2.1, 2.2, 6.1, 6.2, 6.4
    """
    db = get_db()
    client = get_supabase_client()
    
    # Vérifier l'idempotence - éviter les doublons en cas de réexécution
    if not acquire_idempotency_lock(message_id, "send"):
        logger.info(f"Message {message_id} déjà en cours de traitement (idempotence), skip")
        return {
            "success": True,
            "message_id": message_id,
            "skipped": True,
            "reason": "Opération déjà en cours (idempotence)"
        }
    
    try:
        # Vérifier la limite quotidienne avant envoi - Requirements: 2.1, 2.2
        can_send, error_code = monitoring_service.can_send_message()
        if not can_send:
            logger.warning(
                f"Message {message_id} bloqué: limite quotidienne atteinte",
                extra={"error_code": error_code}
            )
            # Mettre à jour le message avec l'erreur
            db.update_message(message_id, {
                "status": "failed",
                "error_message": "Limite quotidienne de 1000 messages atteinte. Réessayez demain."
            })
            return {
                "success": False,
                "message_id": message_id,
                "error": error_code,
                "error_message": "Limite quotidienne de 1000 messages atteinte. Réessayez demain.",
                "blocked": True
            }
        
        # Récupérer le message
        message = db.get_message_by_id(message_id)
        
        # Validation des données du message
        is_valid, error_msg = validate_message_data(message)
        if not is_valid:
            logger.error(f"Message {message_id} invalide: {error_msg}")
            return {"success": False, "error": error_msg}
        
        # IMPORTANT: Vérifier si le message a déjà été envoyé (évite les doublons)
        current_status = message.get("status")
        if current_status in ("sent", "delivered", "read"):
            logger.info(f"Message {message_id} déjà envoyé (status={current_status}), skip")
            return {
                "success": True,
                "message_id": message_id,
                "skipped": True,
                "reason": f"Message déjà envoyé (status={current_status})"
            }
        
        # Vérifier si le message a été annulé/échoué manuellement
        if current_status == "failed" and message.get("error_message") == "Campagne arrêtée par l'utilisateur":
            logger.info(f"Message {message_id} annulé par l'utilisateur, skip")
            return {
                "success": False,
                "message_id": message_id,
                "skipped": True,
                "reason": "Message annulé par l'utilisateur"
            }
        
        # Récupérer le contact via requête directe
        contact_response = client.table("contacts").select("*").eq("id", message["contact_id"]).limit(1).execute()
        contact = contact_response.data[0] if contact_response.data else None
        
        # Validation des données du contact
        is_valid, error_msg = validate_contact_data(contact)
        if not is_valid:
            logger.error(f"Contact invalide pour message {message_id}: {error_msg}")
            db.update_message(message_id, {
                "status": "failed",
                "error_message": error_msg
            })
            return {"success": False, "error": error_msg}
        
        # Vérifier si la campagne est toujours active
        message_type = message.get("message_type", "message_1")
        is_active, reason = is_campaign_active(client, message["campaign_id"], message_type)
        
        if not is_active:
            logger.info(f"Campagne {message['campaign_id']} inactive ({reason}), skip message {message_id}")
            db.update_message(message_id, {
                "status": "failed",
                "error_message": reason
            })
            return {
                "success": False,
                "message_id": message_id,
                "skipped": True,
                "reason": reason
            }
        
        # Respecter le rate limit Wassenger (25s entre messages) - Exigence 2.5
        wait_for_wassenger_rate_limit()
        
        # =======================================================================
        # ANTI-BAN: Délai basé sur la longueur du message (Requirements 4.3)
        # =======================================================================
        message_content = message["content"]
        message_length_delay = get_message_length_delay(len(message_content))
        if message_length_delay > 0:
            logger.debug(
                f"Message {message_id}: délai longueur message {message_length_delay:.1f}s "
                f"(longueur: {len(message_content)} caractères)"
            )
            time.sleep(message_length_delay)
        
        # Envoyer le message via Wassenger API
        phone = contact.get("whatsapp_id") or contact.get("full_number")
        
        # Wassenger utilise uniquement des messages texte (pas de templates Twilio)
        # Le contenu du message est toujours dans message["content"]
        response = run_async(
            wassenger_service.send_message(
                phone=phone,
                text=message_content
            )
        )
        
        # Mettre à jour le statut du message
        if response.success:
            sent_at_timestamp = datetime.utcnow().isoformat()
            
            # Stocker le message_id Wassenger dans whatsapp_message_id
            db.update_message(message_id, {
                "status": "sent",
                "whatsapp_message_id": response.message_id,  # ID Wassenger
                "sent_at": sent_at_timestamp,
                "error_message": None
            })
            
            # =======================================================================
            # ANTI-BAN: Réinitialiser le compteur d'erreurs consécutives (Requirements 5.2)
            # =======================================================================
            try:
                redis_client = monitoring_service.redis_client
                redis_client.set("anti_ban:consecutive_errors", 0)
                logger.debug(f"Message {message_id}: compteur erreurs consécutives réinitialisé")
            except Exception as redis_error:
                logger.warning(f"Erreur réinitialisation compteur erreurs: {redis_error}")
            
            # Incrémenter le compteur de monitoring - Requirements: 1.1
            logger.info(f"Compteur {message_type} incrémenté")
            monitoring_service.increment_message_counter(message_type)
            
            # Mettre à jour les statistiques de la campagne
            update_campaign_statistics(client, message["campaign_id"], success=True)
            
            # CAMPAIGN AUTO-COMPLETION: Déclencher la vérification du statut après Message 2
            # Requirements: 1.1, 3.4 - Vérifier si la campagne doit être marquée comme terminée
            if message_type == "message_2":
                logger.info(
                    f"Message 2 envoyé pour campagne {message['campaign_id']}, "
                    f"déclenchement vérification statut dans 5s"
                )
                # Délai de 5 secondes pour laisser le temps à la BDD de se synchroniser
                update_campaign_status.apply_async(
                    args=[message["campaign_id"]],
                    countdown=5
                )
            
            logger.info(f"Message {message_id} envoyé avec succès via Wassenger, ID: {response.message_id}")
            
            return {
                "success": True,
                "message_id": message_id,
                "wassenger_message_id": response.message_id
            }
        else:
            # Échec de l'envoi - Incrémenter le compteur d'erreurs - Requirements: 6.1
            monitoring_service.increment_error_counter()
            
            # =======================================================================
            # ANTI-BAN: Détection de risque de ban (Requirements 5.1)
            # =======================================================================
            ban_risk = detect_ban_risk(response.error_code, response.error_message)
            if ban_risk["is_ban_risk"]:
                logger.critical(
                    f"⚠️ RISQUE DE BAN DÉTECTÉ pour message {message_id}: "
                    f"{response.error_code} - {response.error_message}"
                )
                # Déclencher pause d'urgence en stockant le timestamp de fin dans Redis
                try:
                    redis_client = monitoring_service.redis_client
                    from datetime import timedelta
                    pause_end = datetime.now() + timedelta(seconds=ban_risk["pause_duration"])
                    redis_client.set(
                        "anti_ban:emergency_pause_until",
                        pause_end.isoformat(),
                        ex=int(ban_risk["pause_duration"]) + 60  # TTL avec marge
                    )
                    logger.critical(
                        f"Pause d'urgence activée jusqu'à {pause_end.isoformat()} "
                        f"({ban_risk['pause_duration']/60:.0f} minutes)"
                    )
                except Exception as redis_error:
                    logger.error(f"Erreur activation pause d'urgence: {redis_error}")
            
            # =======================================================================
            # ANTI-BAN: Mise à jour des compteurs d'erreur dans Redis (Requirements 5.2, 5.3)
            # =======================================================================
            try:
                redis_client = monitoring_service.redis_client
                
                # Incrémenter le compteur d'erreurs consécutives (Requirements 5.2)
                consecutive_errors = redis_client.incr("anti_ban:consecutive_errors")
                redis_client.expire("anti_ban:consecutive_errors", 3600)  # TTL 1 heure
                logger.debug(f"Erreurs consécutives: {consecutive_errors}")
                
                # Incrémenter le compteur d'erreurs dans la fenêtre de temps (Requirements 5.3)
                current_minute = datetime.now().strftime('%Y%m%d%H%M')
                window_key = f"anti_ban:errors:{current_minute}"
                redis_client.incr(window_key)
                redis_client.expire(window_key, ERROR_WINDOW_MINUTES * 60 + 60)  # TTL avec marge
                
                # Incrémenter le compteur total d'erreurs (Requirements 5.5)
                redis_client.incr("anti_ban:total_errors")
                redis_client.expire("anti_ban:total_errors", 86400)  # TTL 24h
                
                logger.debug(
                    f"Message {message_id}: compteurs erreurs mis à jour "
                    f"(consécutives: {consecutive_errors})"
                )
            except Exception as redis_error:
                logger.warning(f"Erreur mise à jour compteurs erreurs Redis: {redis_error}")
            
            retry_count = (message.get("retry_count") or 0) + 1
            
            # Vérifier si on peut encore réessayer
            can_retry = retry_count < settings.MAX_RETRY_ATTEMPTS
            
            db.update_message(message_id, {
                "status": "pending" if can_retry else "failed",
                "error_message": response.error_message,
                "retry_count": retry_count
            })
            
            # Mettre à jour les statistiques seulement si échec définitif
            if not can_retry:
                update_campaign_statistics(client, message["campaign_id"], success=False)
            
            logger.error(
                f"Échec envoi message {message_id}: {response.error_code} - {response.error_message}"
            )
            
            # Programmer un retry si possible (max 3 tentatives - Exigence 6.4)
            if can_retry:
                # Délai exponentiel: 30s, 60s, 120s (réduit pour réactivité)
                delay = 30 * (2 ** (retry_count - 1))
                logger.info(f"Message {message_id}: retry programmé dans {delay}s (tentative {retry_count})")
                raise self.retry(countdown=delay)
            
            return {
                "success": False,
                "message_id": message_id,
                "error": response.error_message,
                "retry_count": retry_count
            }
    
    except SoftTimeLimitExceeded:
        # Timeout atteint - marquer comme pending pour retry automatique
        logger.warning(f"Message {message_id}: timeout atteint, sera réessayé")
        db.update_message(message_id, {
            "status": "pending",
            "error_message": "Timeout - sera réessayé automatiquement"
        })
        return {"success": False, "error": "Timeout", "will_retry": True}
            
    except MaxRetriesExceededError:
        logger.error(f"Message {message_id}: nombre maximum de retries atteint")
        # Incrémenter le compteur d'erreurs - Requirements: 6.1
        monitoring_service.increment_error_counter()
        # Marquer définitivement comme échoué
        db.update_message(message_id, {
            "status": "failed",
            "error_message": "Nombre maximum de tentatives atteint"
        })
        update_campaign_statistics(client, message["campaign_id"], success=False)
        return {"success": False, "error": "Max retries exceeded"}
        
    except self.MaxRetriesExceededError:
        # Alias pour compatibilité
        logger.error(f"Message {message_id}: nombre maximum de retries atteint")
        monitoring_service.increment_error_counter()
        db.update_message(message_id, {
            "status": "failed",
            "error_message": "Nombre maximum de tentatives atteint"
        })
        return {"success": False, "error": "Max retries exceeded"}
        
    except Exception as e:
        error_msg = str(e)
        logger.exception(f"Erreur inattendue lors de l'envoi du message {message_id}: {error_msg}")
        
        # Vérifier le nombre de retries avant de réessayer
        current_retries = self.request.retries
        if current_retries < self.max_retries:
            delay = 30 * (2 ** current_retries)
            raise self.retry(exc=e, countdown=delay)
        else:
            # Max retries atteint, marquer comme échoué
            monitoring_service.increment_error_counter()
            db.update_message(message_id, {
                "status": "failed",
                "error_message": f"Erreur après {current_retries} tentatives: {error_msg}"
            })
            return {"success": False, "error": error_msg}
    
    finally:
        # Toujours libérer le verrou d'idempotence
        release_idempotency_lock(message_id, "send")



def calculate_strategic_pause_delay(consecutive_count: int) -> float:
    """
    Calcule le délai de pause stratégique cumulé pour un nombre de messages consécutifs.
    
    Cette fonction calcule le temps total de pause stratégique qui doit être ajouté
    au délai d'un message en fonction du nombre de messages consécutifs envoyés.
    
    Les pauses stratégiques sont déclenchées aux seuils suivants:
    - 20 messages: 3-5 minutes (moyenne: 240s)
    - 40 messages: 5-8 minutes (moyenne: 390s)
    - 60 messages: 10-15 minutes (moyenne: 750s)
    - 100 messages: 20-30 minutes (moyenne: 1500s)
    
    Args:
        consecutive_count: Nombre de messages consécutifs (1-indexed)
    
    Returns:
        Délai de pause stratégique cumulé en secondes
    
    Validates: Requirements 3.1, 3.2, 3.3, 3.4
    """
    total_pause = 0.0
    
    # Utiliser les valeurs moyennes des plages pour le calcul prédictif
    # (la randomisation réelle se fait dans get_strategic_pause_duration)
    PAUSE_DURATION_1_AVG = (PAUSE_DURATION_1[0] + PAUSE_DURATION_1[1]) / 2  # 240s
    PAUSE_DURATION_2_AVG = (PAUSE_DURATION_2[0] + PAUSE_DURATION_2[1]) / 2  # 390s
    PAUSE_DURATION_3_AVG = (PAUSE_DURATION_3[0] + PAUSE_DURATION_3[1]) / 2  # 750s
    PAUSE_DURATION_4_AVG = (PAUSE_DURATION_4[0] + PAUSE_DURATION_4[1]) / 2  # 1500s
    
    # Ajouter les pauses pour chaque seuil dépassé
    if consecutive_count > PAUSE_THRESHOLD_1:  # > 20
        total_pause += PAUSE_DURATION_1_AVG
    if consecutive_count > PAUSE_THRESHOLD_2:  # > 40
        total_pause += PAUSE_DURATION_2_AVG
    if consecutive_count > PAUSE_THRESHOLD_3:  # > 60
        total_pause += PAUSE_DURATION_3_AVG
    if consecutive_count > PAUSE_THRESHOLD_4:  # > 100
        total_pause += PAUSE_DURATION_4_AVG
    
    # Pour les messages au-delà de 100, ajouter des pauses supplémentaires
    # tous les 100 messages
    if consecutive_count > PAUSE_THRESHOLD_4:
        extra_pauses = (consecutive_count - PAUSE_THRESHOLD_4) // PAUSE_THRESHOLD_4
        total_pause += extra_pauses * PAUSE_DURATION_4_AVG
    
    return total_pause


def initialize_consecutive_counter(redis_client, campaign_id: int) -> None:
    """
    Initialise le compteur de messages consécutifs pour une campagne.
    
    Cette fonction est appelée au début de l'envoi d'une campagne pour
    réinitialiser le compteur de messages consécutifs à 0.
    
    Args:
        redis_client: Client Redis
        campaign_id: ID de la campagne
    
    Validates: Requirements 3.1, 3.2, 3.3, 3.4
    """
    try:
        key = f"anti_ban:consecutive_messages:{campaign_id}"
        redis_client.set(key, 0, ex=86400)  # TTL 24h
        logger.info(f"Compteur messages consécutifs initialisé pour campagne {campaign_id}")
    except Exception as e:
        logger.error(f"Erreur initialisation compteur consécutif campagne {campaign_id}: {e}")


def increment_consecutive_counter(redis_client, campaign_id: int) -> int:
    """
    Incrémente le compteur de messages consécutifs pour une campagne.
    
    Cette fonction est appelée après chaque message envoyé pour suivre
    le nombre de messages consécutifs et déclencher les pauses stratégiques.
    
    Args:
        redis_client: Client Redis
        campaign_id: ID de la campagne
    
    Returns:
        Nouvelle valeur du compteur
    
    Validates: Requirements 3.1, 3.2, 3.3, 3.4
    """
    try:
        key = f"anti_ban:consecutive_messages:{campaign_id}"
        new_count = redis_client.incr(key)
        redis_client.expire(key, 86400)  # Renouveler TTL 24h
        return new_count
    except Exception as e:
        logger.error(f"Erreur incrémentation compteur consécutif campagne {campaign_id}: {e}")
        return 0


def get_consecutive_counter(redis_client, campaign_id: int) -> int:
    """
    Récupère la valeur actuelle du compteur de messages consécutifs.
    
    Args:
        redis_client: Client Redis
        campaign_id: ID de la campagne
    
    Returns:
        Valeur actuelle du compteur (0 si non trouvé)
    
    Validates: Requirements 3.1, 3.2, 3.3, 3.4
    """
    try:
        key = f"anti_ban:consecutive_messages:{campaign_id}"
        value = redis_client.get(key)
        return int(value) if value else 0
    except Exception as e:
        logger.error(f"Erreur lecture compteur consécutif campagne {campaign_id}: {e}")
        return 0


def reset_campaign_consecutive_counter(redis_client, campaign_id: int) -> None:
    """
    Réinitialise le compteur de messages consécutifs après une pause stratégique.
    
    Cette fonction est appelée après chaque pause stratégique pour
    recommencer le comptage à zéro.
    
    Args:
        redis_client: Client Redis
        campaign_id: ID de la campagne
    
    Validates: Requirements 3.6
    """
    try:
        key = f"anti_ban:consecutive_messages:{campaign_id}"
        redis_client.set(key, 0, ex=86400)  # TTL 24h
        logger.debug(f"Compteur messages consécutifs réinitialisé pour campagne {campaign_id}")
    except Exception as e:
        logger.error(f"Erreur réinitialisation compteur consécutif campagne {campaign_id}: {e}")


@celery_app.task(
    bind=True,
    name="app.tasks.message_tasks.send_campaign_messages",
    acks_late=True,
)
def send_campaign_messages(
    self,
    campaign_id: int,
    batch_size: int = None
) -> dict:
    """
    Envoie les messages d'une campagne par lots via Wassenger API.
    
    ANTI-BAN STRATEGY 2025:
    - Délai de 15-35 secondes entre chaque message (adaptatif selon warm-up)
    - Envoi par lots de 20 messages (ANTI_BAN_BATCH_SIZE)
    - Pauses stratégiques automatiques aux seuils 20, 40, 60, 100 messages
    - Pour 1000 messages: ~8-10 heures d'envoi total
    
    PAUSES STRATÉGIQUES (Requirements 3.1, 3.2, 3.3, 3.4):
    - Après 20 messages: pause de 3-5 minutes
    - Après 40 messages: pause de 5-8 minutes
    - Après 60 messages: pause de 10-15 minutes
    - Après 100 messages: pause de 20-30 minutes
    - Le compteur est réinitialisé après chaque pause (Requirements 3.6)
    
    Args:
        campaign_id: ID de la campagne
        batch_size: Taille des lots (défaut: ANTI_BAN_BATCH_SIZE = 20)
    
    Returns:
        Dictionnaire avec les statistiques d'envoi
    
    Exigences: 6.1
    Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.6
    """
    db = get_db()
    client = get_supabase_client()
    
    # ==========================================================================
    # ANTI-BAN: Utiliser ANTI_BAN_BATCH_SIZE (20) au lieu de BATCH_SIZE (50)
    # Requirements: 3.1
    # ==========================================================================
    if batch_size is None:
        batch_size = ANTI_BAN_BATCH_SIZE  # 20 messages par lot
    
    try:
        # =======================================================================
        # ANTI-BAN: Initialiser le compteur de messages consécutifs
        # Requirements: 3.1, 3.2, 3.3, 3.4
        # =======================================================================
        try:
            redis_client = monitoring_service.redis_client
            initialize_consecutive_counter(redis_client, campaign_id)
            logger.info(f"Campagne {campaign_id}: compteur messages consécutifs initialisé")
        except Exception as redis_error:
            logger.warning(f"Erreur initialisation compteur Redis: {redis_error}")
        
        # Récupérer la campagne directement (sans filtre user_id pour les tâches Celery)
        campaign_response = client.table("campaigns").select("*").eq("id", campaign_id).limit(1).execute()
        campaign = campaign_response.data[0] if campaign_response.data else None
        if not campaign:
            logger.error(f"Campagne {campaign_id} non trouvée")
            return {"success": False, "error": "Campagne non trouvée"}
        
        # Mettre à jour le statut de la campagne
        db.update_campaign(campaign_id, {"status": "sending"})
        
        logger.info(f"Démarrage envoi campagne {campaign_id}: {campaign.get('name')}")
        
        # Récupérer tous les messages en attente pour cette campagne
        messages_response = client.table("messages").select("*").eq("campaign_id", campaign_id).eq("status", "pending").execute()
        pending_messages = messages_response.data or []
        
        total_messages = len(pending_messages)
        logger.info(f"Campagne {campaign_id}: {total_messages} messages à envoyer")
        
        # Wassenger utilise uniquement des messages texte (pas de templates Twilio)
        # Ces paramètres sont conservés pour compatibilité mais non utilisés
        is_template = False
        content_sid = None
        template_name = campaign.get("template_name")
        
        # ==========================================================================
        # ANTI-BAN BATCH LOGIC 2025 - AVEC PAUSES STRATÉGIQUES
        # ==========================================================================
        # Stratégie: Envoyer par lots avec pauses stratégiques pour éviter les bans
        # - Lot de 20 messages (ANTI_BAN_BATCH_SIZE)
        # - Délai moyen de ~22s entre chaque message (warm-up + randomisation)
        # - Pauses stratégiques aux seuils 20, 40, 60, 100 messages
        # - Pour 1000 messages: ~8-10 heures d'envoi total
        #
        # Requirements: 3.1, 3.2, 3.3, 3.4, 3.6
        # ==========================================================================
        
        tasks_created = 0
        
        # Délai moyen estimé entre messages (pour le calcul du temps total)
        # Utilise la moyenne des délais warm-up + variation + typing
        AVERAGE_DELAY_SECONDS = 22  # Moyenne estimée des délais anti-ban
        
        # Compteur de messages consécutifs pour le calcul des pauses stratégiques
        consecutive_count = 0
        cumulative_strategic_pause = 0.0
        
        for i, message in enumerate(pending_messages):
            # =======================================================================
            # ANTI-BAN: Incrémenter le compteur de messages consécutifs
            # Requirements: 3.1, 3.2, 3.3, 3.4
            # =======================================================================
            consecutive_count += 1
            
            # Calculer le numéro de lot actuel
            batch_number = i // batch_size
            position_in_batch = i % batch_size
            
            # =======================================================================
            # ANTI-BAN: Vérifier et calculer les pauses stratégiques
            # Requirements: 3.1, 3.2, 3.3, 3.4, 3.6
            # =======================================================================
            if should_take_strategic_pause(consecutive_count):
                # Calculer la durée de pause stratégique
                pause_duration = get_strategic_pause_duration(consecutive_count)
                cumulative_strategic_pause += pause_duration
                
                logger.info(
                    f"Campagne {campaign_id}: Pause stratégique programmée après message {i + 1} "
                    f"({consecutive_count} messages consécutifs) - durée: {pause_duration/60:.1f} min"
                )
                
                # Réinitialiser le compteur après la pause (Requirements 3.6)
                # Note: Le compteur sera réinitialisé dans Redis par send_single_message
                # après l'exécution de la pause
                consecutive_count = 0
            
            # Calculer le délai total:
            # - Délai de base: position dans le lot * délai moyen anti-ban
            # - Délai de pause entre lots: nombre de lots précédents * pause entre lots
            # - Délai de pauses stratégiques cumulées
            base_delay = position_in_batch * AVERAGE_DELAY_SECONDS
            batch_pause_delay = batch_number * BATCH_PAUSE_SECONDS
            
            # Ajouter aussi le temps des lots précédents (messages déjà envoyés)
            previous_batches_time = batch_number * batch_size * AVERAGE_DELAY_SECONDS
            
            # Ajouter les pauses stratégiques cumulées
            total_delay = base_delay + batch_pause_delay + previous_batches_time + cumulative_strategic_pause
            
            # Log pour le premier message de chaque lot
            if position_in_batch == 0:
                logger.info(
                    f"Campagne {campaign_id}: Lot {batch_number + 1} programmé "
                    f"(messages {i + 1}-{min(i + batch_size, total_messages)}) "
                    f"démarrage dans {total_delay:.0f}s (pauses stratégiques: {cumulative_strategic_pause/60:.1f}min)"
                )
            
            # Créer une tâche d'envoi individuel avec le délai calculé
            send_single_message.apply_async(
                args=[message["id"]],
                kwargs={
                    "is_template": is_template,
                    "template_name": template_name,
                    "content_sid": content_sid
                },
                countdown=total_delay
            )
            tasks_created += 1
        
        # Calculer le temps estimé de complétion avec pauses stratégiques
        num_batches = (total_messages + batch_size - 1) // batch_size  # Arrondi supérieur
        
        # Calculer le nombre de pauses stratégiques attendues
        num_strategic_pauses = 0
        total_strategic_pause_time = 0.0
        
        # Pauses aux seuils 20, 40, 60, 100 (puis tous les 100)
        if total_messages > PAUSE_THRESHOLD_1:
            num_strategic_pauses += 1
            total_strategic_pause_time += (PAUSE_DURATION_1[0] + PAUSE_DURATION_1[1]) / 2
        if total_messages > PAUSE_THRESHOLD_2:
            num_strategic_pauses += 1
            total_strategic_pause_time += (PAUSE_DURATION_2[0] + PAUSE_DURATION_2[1]) / 2
        if total_messages > PAUSE_THRESHOLD_3:
            num_strategic_pauses += 1
            total_strategic_pause_time += (PAUSE_DURATION_3[0] + PAUSE_DURATION_3[1]) / 2
        if total_messages > PAUSE_THRESHOLD_4:
            num_strategic_pauses += 1
            total_strategic_pause_time += (PAUSE_DURATION_4[0] + PAUSE_DURATION_4[1]) / 2
            # Pauses supplémentaires tous les 100 messages
            extra_pauses = (total_messages - PAUSE_THRESHOLD_4) // PAUSE_THRESHOLD_4
            num_strategic_pauses += extra_pauses
            total_strategic_pause_time += extra_pauses * (PAUSE_DURATION_4[0] + PAUSE_DURATION_4[1]) / 2
        
        estimated_completion_time = (
            total_messages * AVERAGE_DELAY_SECONDS +  # Temps d'envoi avec délais anti-ban
            (num_batches - 1) * BATCH_PAUSE_SECONDS +  # Pauses entre lots
            total_strategic_pause_time +  # Pauses stratégiques
            60  # Marge de sécurité
        )
        
        # Convertir en heures/minutes pour le log
        hours = int(estimated_completion_time // 3600)
        minutes = int((estimated_completion_time % 3600) // 60)
        
        logger.info(
            f"Campagne {campaign_id}: {tasks_created} tâches créées en {num_batches} lots. "
            f"Délai moyen entre messages: {AVERAGE_DELAY_SECONDS}s, "
            f"Pause entre lots: {BATCH_PAUSE_SECONDS}s, "
            f"Pauses stratégiques: {num_strategic_pauses} ({total_strategic_pause_time/60:.0f}min). "
            f"Temps estimé: {hours}h{minutes}min"
        )
        
        # Programmer une tâche pour mettre à jour le statut final de la campagne
        update_campaign_status.apply_async(
            args=[campaign_id],
            countdown=estimated_completion_time
        )
        
        return {
            "success": True,
            "campaign_id": campaign_id,
            "total_messages": total_messages,
            "tasks_created": tasks_created,
            "num_batches": num_batches,
            "num_strategic_pauses": num_strategic_pauses,
            "total_strategic_pause_minutes": round(total_strategic_pause_time / 60, 1),
            "estimated_completion_seconds": estimated_completion_time,
            "estimated_completion_hours": round(estimated_completion_time / 3600, 1)
        }
        
    except Exception as e:
        logger.exception(f"Erreur lors de l'envoi de la campagne {campaign_id}: {e}")
        
        # Marquer la campagne comme échouée
        client.table("campaigns").update({"status": "failed"}).eq("id", campaign_id).execute()
        
        return {"success": False, "error": str(e)}


@celery_app.task(
    bind=True,
    name="app.tasks.message_tasks.retry_failed_message",
    max_retries=3,
    acks_late=True,
)
def retry_failed_message(
    self,
    message_id: int
) -> dict:
    """
    Réessaie l'envoi d'un message échoué via Wassenger avec backoff exponentiel.
    
    Utilise wassenger_service pour les retries.
    Délai exponentiel: 60s, 120s, 240s (formule: 60 × 2^(tentative-1))
    Marque comme échoué après 3 tentatives.
    
    Args:
        message_id: ID du message à réessayer
    
    Returns:
        Dictionnaire avec le résultat du retry
    
    Exigences: 6.4
    """
    db = get_db()
    client = get_supabase_client()
    
    try:
        # Récupérer le message
        message = db.get_message_by_id(message_id)
        if not message:
            logger.error(f"Message {message_id} non trouvé pour retry")
            return {"success": False, "error": "Message non trouvé"}
        
        retry_count = message.get("retry_count") or 0
        
        # Vérifier si le message peut être réessayé (max 3 tentatives - Exigence 6.4)
        if retry_count >= settings.MAX_RETRY_ATTEMPTS:
            # Marquer définitivement comme échoué après 3 tentatives
            db.update_message(message_id, {
                "status": "failed",
                "error_message": "Nombre maximum de tentatives atteint (3)"
            })
            
            logger.warning(
                f"Message {message_id} marqué comme échoué définitivement "
                f"(retry_count={retry_count})"
            )
            return {
                "success": False,
                "error": "Nombre maximum de tentatives atteint",
                "retry_count": retry_count
            }
        
        # Récupérer la campagne pour référence
        campaign_response = client.table("campaigns").select("*").eq("id", message["campaign_id"]).limit(1).execute()
        if not campaign_response.data:
            logger.error(f"Campagne {message['campaign_id']} non trouvée pour retry message {message_id}")
            return {"success": False, "error": "Campagne non trouvée"}
        
        campaign = campaign_response.data[0]
        
        # Réinitialiser le statut pour le retry
        db.update_message(message_id, {"status": "pending"})
        
        # Calculer le délai exponentiel (Exigence 2.6)
        # Formule: délai = 60 × 2^(tentative-1) -> 60s, 120s, 240s
        next_attempt = retry_count + 1
        delay = calculate_retry_delay(next_attempt)
        
        logger.info(
            f"Programmation retry message {message_id} via Wassenger dans {delay}s "
            f"(tentative {next_attempt}/{settings.MAX_RETRY_ATTEMPTS})"
        )
        
        # Programmer la tâche d'envoi avec délai via wassenger_service
        # Wassenger n'utilise pas de templates, mais on conserve les paramètres pour compatibilité
        send_single_message.apply_async(
            args=[message_id],
            kwargs={
                "is_template": False,
                "template_name": campaign.get("template_name"),
                "content_sid": None
            },
            countdown=delay
        )
        
        return {
            "success": True,
            "message_id": message_id,
            "retry_count": next_attempt,
            "delay_seconds": delay
        }
        
    except Exception as e:
        logger.exception(f"Erreur lors du retry du message {message_id}: {e}")
        return {"success": False, "error": str(e)}


@celery_app.task(
    bind=True,
    name="app.tasks.message_tasks.retry_campaign_failed_messages",
    acks_late=True,
)
def retry_campaign_failed_messages(
    self,
    campaign_id: int
) -> dict:
    """
    Réessaie tous les messages échoués d'une campagne via Wassenger.
    
    Args:
        campaign_id: ID de la campagne
    
    Returns:
        Dictionnaire avec les statistiques de retry
    """
    client = get_supabase_client()
    
    try:
        # Récupérer tous les messages échoués de la campagne qui peuvent être réessayés
        messages_response = client.table("messages").select("*").eq("campaign_id", campaign_id).eq("status", "failed").lt("retry_count", settings.MAX_RETRY_ATTEMPTS).execute()
        failed_messages = messages_response.data or []
        
        total_failed = len(failed_messages)
        logger.info(f"Campagne {campaign_id}: {total_failed} messages échoués à réessayer")
        
        if total_failed == 0:
            return {
                "success": True,
                "campaign_id": campaign_id,
                "retried_count": 0,
                "message": "Aucun message à réessayer"
            }
        
        # Programmer les retries avec délai de 2s entre chaque (rate limit Wassenger)
        retried_count = 0
        for message in failed_messages:
            retry_failed_message.apply_async(
                args=[message["id"]],
                countdown=retried_count * WASSENGER_RATE_LIMIT_SECONDS
            )
            retried_count += 1
        
        logger.info(f"Campagne {campaign_id}: {retried_count} retries programmés")
        
        return {
            "success": True,
            "campaign_id": campaign_id,
            "retried_count": retried_count
        }
        
    except Exception as e:
        logger.exception(f"Erreur lors du retry des messages de la campagne {campaign_id}: {e}")
        return {"success": False, "error": str(e)}


# ==========================================================================
# WHATSAPP VERIFICATION TASKS
# ==========================================================================
# Rate limit for WhatsApp verification: 2 seconds between calls
# Requirements: 6.1, 6.2
VERIFICATION_RATE_LIMIT_SECONDS = 2

# Minimum delay for rate limit retry (60 seconds)
# Requirements: 6.2
RATE_LIMIT_RETRY_DELAY_SECONDS = 60


@celery_app.task(
    bind=True,
    name="app.tasks.message_tasks.verify_whatsapp_task",
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
)
def verify_whatsapp_task(self, contact_id: int) -> dict:
    """
    Tâche asynchrone pour vérifier si un numéro de téléphone est enregistré sur WhatsApp.
    
    Utilise l'API Wassenger pour vérifier l'existence du numéro sur WhatsApp.
    Gère le rate limiting avec backoff exponentiel.
    Met à jour le contact avec le résultat de la vérification.
    
    Args:
        contact_id: ID du contact à vérifier
    
    Returns:
        Dictionnaire avec le résultat de la vérification:
        - success: True si la vérification a réussi
        - contact_id: ID du contact
        - whatsapp_verified: True/False/None selon le résultat
        - error: Message d'erreur si échec
    
    Requirements: 1.1, 6.2
    """
    db = get_db()
    client = get_supabase_client()
    
    try:
        # Récupérer le contact directement (sans filtre user_id pour les tâches Celery)
        contact_response = client.table("contacts").select("*").eq("id", contact_id).limit(1).execute()
        contact = contact_response.data[0] if contact_response.data else None
        
        if not contact:
            logger.error(f"Contact {contact_id} non trouvé pour vérification WhatsApp")
            return {"success": False, "error": "Contact non trouvé", "contact_id": contact_id}
        
        # Récupérer le numéro de téléphone
        phone = contact.get("whatsapp_id") or contact.get("full_number")
        if not phone:
            logger.error(f"Contact {contact_id} n'a pas de numéro de téléphone")
            # Marquer comme non vérifié (null) car pas de numéro
            db.update_contact(contact_id, {
                "whatsapp_verified": None,
                "verified_at": datetime.utcnow().isoformat()
            })
            return {"success": False, "error": "Numéro de téléphone manquant", "contact_id": contact_id}
        
        logger.info(f"Vérification WhatsApp pour contact {contact_id}, numéro: {phone}")
        
        # Appeler l'API Wassenger pour vérifier l'existence
        response = run_async(
            wassenger_service.check_whatsapp_exists(phone)
        )
        
        # Traiter le résultat
        if response.error_code:
            # Gérer les erreurs spécifiques
            if response.error_code == "rate_limit_exceeded":
                # Rate limit atteint - programmer un retry avec délai
                retry_count = self.request.retries
                # Backoff exponentiel: 60s, 120s, 240s
                delay = RATE_LIMIT_RETRY_DELAY_SECONDS * (2 ** retry_count)
                
                logger.warning(
                    f"Rate limit atteint pour contact {contact_id}, "
                    f"retry dans {delay}s (tentative {retry_count + 1}/{self.max_retries})"
                )
                
                raise self.retry(countdown=delay)
            
            elif response.error_code in ("timeout", "network_error", "unexpected_error"):
                # Erreur réseau/API - marquer comme null et programmer retry
                # Requirements: 1.3
                retry_count = self.request.retries
                
                if retry_count < self.max_retries:
                    # Backoff exponentiel: 60s, 120s, 240s
                    delay = settings.RETRY_BASE_DELAY_SECONDS * (2 ** retry_count)
                    
                    logger.warning(
                        f"Erreur {response.error_code} pour contact {contact_id}, "
                        f"retry dans {delay}s (tentative {retry_count + 1}/{self.max_retries})"
                    )
                    
                    raise self.retry(countdown=delay)
                else:
                    # Max retries atteint - marquer comme null
                    db.update_contact(contact_id, {
                        "whatsapp_verified": None,
                        "verified_at": datetime.utcnow().isoformat()
                    })
                    
                    logger.error(
                        f"Vérification WhatsApp échouée pour contact {contact_id} "
                        f"après {retry_count} tentatives: {response.error_message}"
                    )
                    
                    return {
                        "success": False,
                        "contact_id": contact_id,
                        "whatsapp_verified": None,
                        "error": response.error_message
                    }
            
            else:
                # Autre erreur (invalid_phone_number, etc.) - marquer comme null
                db.update_contact(contact_id, {
                    "whatsapp_verified": None,
                    "verified_at": datetime.utcnow().isoformat()
                })
                
                logger.error(
                    f"Erreur vérification WhatsApp pour contact {contact_id}: "
                    f"{response.error_code} - {response.error_message}"
                )
                
                return {
                    "success": False,
                    "contact_id": contact_id,
                    "whatsapp_verified": None,
                    "error": response.error_message
                }
        
        # Vérification réussie - mettre à jour le contact
        whatsapp_verified = response.exists
        
        db.update_contact(contact_id, {
            "whatsapp_verified": whatsapp_verified,
            "verified_at": datetime.utcnow().isoformat()
        })
        
        logger.info(
            f"Vérification WhatsApp terminée pour contact {contact_id}: "
            f"whatsapp_verified={whatsapp_verified}"
        )
        
        return {
            "success": True,
            "contact_id": contact_id,
            "whatsapp_verified": whatsapp_verified
        }
        
    except self.MaxRetriesExceededError:
        # Max retries atteint via Celery
        logger.error(f"Contact {contact_id}: nombre maximum de retries atteint")
        
        db.update_contact(contact_id, {
            "whatsapp_verified": None,
            "verified_at": datetime.utcnow().isoformat()
        })
        
        return {
            "success": False,
            "contact_id": contact_id,
            "whatsapp_verified": None,
            "error": "Nombre maximum de tentatives atteint"
        }
        
    except Exception as e:
        error_msg = str(e)
        logger.exception(f"Erreur inattendue lors de la vérification du contact {contact_id}: {error_msg}")
        
        # Vérifier le nombre de retries avant de réessayer
        current_retries = self.request.retries
        if current_retries < self.max_retries:
            delay = settings.RETRY_BASE_DELAY_SECONDS * (2 ** current_retries)
            raise self.retry(exc=e, countdown=delay)
        else:
            # Max retries atteint - marquer comme null
            db.update_contact(contact_id, {
                "whatsapp_verified": None,
                "verified_at": datetime.utcnow().isoformat()
            })
            
            return {
                "success": False,
                "contact_id": contact_id,
                "whatsapp_verified": None,
                "error": error_msg
            }


@celery_app.task(
    bind=True,
    name="app.tasks.message_tasks.bulk_verify_task",
    acks_late=True,
)
def bulk_verify_task(self, contact_ids: List[int]) -> dict:
    """
    Tâche pour vérifier plusieurs contacts en masse.
    
    Queue les vérifications individuelles avec des délais pour respecter
    le rate limit de l'API Wassenger (2 secondes entre chaque appel).
    
    Args:
        contact_ids: Liste des IDs de contacts à vérifier
    
    Returns:
        Dictionnaire avec les statistiques de la vérification en masse:
        - success: True si les tâches ont été créées
        - queued_count: Nombre de vérifications mises en file d'attente
        - total_contacts: Nombre total de contacts à vérifier
        - estimated_completion_seconds: Temps estimé pour terminer
    
    Requirements: 6.1, 6.2
    """
    try:
        total_contacts = len(contact_ids)
        
        if total_contacts == 0:
            logger.info("Aucun contact à vérifier")
            return {
                "success": True,
                "queued_count": 0,
                "total_contacts": 0,
                "message": "Aucun contact à vérifier"
            }
        
        logger.info(f"Démarrage vérification en masse de {total_contacts} contacts")
        
        # Queue les vérifications individuelles avec délai de 2s entre chaque
        # Requirements: 6.1 - respecter le rate limit API
        queued_count = 0
        
        for i, contact_id in enumerate(contact_ids):
            # Délai = index * 2 secondes pour respecter le rate limit
            delay = i * VERIFICATION_RATE_LIMIT_SECONDS
            
            verify_whatsapp_task.apply_async(
                args=[contact_id],
                countdown=delay
            )
            queued_count += 1
        
        # Calculer le temps estimé de complétion
        estimated_completion_seconds = total_contacts * VERIFICATION_RATE_LIMIT_SECONDS
        
        logger.info(
            f"Vérification en masse: {queued_count} tâches créées, "
            f"temps estimé: {estimated_completion_seconds}s"
        )
        
        return {
            "success": True,
            "queued_count": queued_count,
            "total_contacts": total_contacts,
            "estimated_completion_seconds": estimated_completion_seconds,
            "message": f"{queued_count} vérifications mises en file d'attente"
        }
        
    except Exception as e:
        logger.exception(f"Erreur lors de la vérification en masse: {e}")
        return {
            "success": False,
            "error": str(e),
            "queued_count": 0,
            "total_contacts": len(contact_ids)
        }


@celery_app.task(
    bind=True,
    name="app.tasks.message_tasks.update_campaign_status",
    acks_late=True,
)
def update_campaign_status(self, campaign_id: int) -> dict:
    """
    Met à jour le statut d'une campagne en fonction des messages envoyés.
    
    LOGIQUE DE CLÔTURE SIMPLIFIÉE (Requirements 1.2, 2.3):
    Une campagne passe en "completed" quand:
    - pending = 0 (tous les Message 1 sont envoyés)
    - ET (msg2_sent + no_interaction + failed) >= msg1_sent (tous les contacts ont terminé leur cycle)
    
    Un contact a terminé son cycle si:
    - Il a reçu le Message 2 (interaction complète), OU
    - Il est marqué "no_interaction" (24h sans réponse), OU
    - Son message a échoué ("failed")
    
    Args:
        campaign_id: ID de la campagne
    
    Returns:
        Dictionnaire avec le nouveau statut et les statistiques
    
    Exigences: 1.2, 1.3, 1.4, 2.2, 2.3
    """
    client = get_supabase_client()
    
    try:
        from datetime import datetime, timezone
        
        # Récupérer la campagne directement (sans filtre user_id pour les tâches Celery)
        campaign_response = client.table("campaigns").select("*").eq("id", campaign_id).limit(1).execute()
        campaign = campaign_response.data[0] if campaign_response.data else None
        if not campaign:
            return {"success": False, "error": "Campagne non trouvée"}
        
        # =================================================================
        # COMPTAGE DES MESSAGES (Requirements 2.3)
        # =================================================================
        
        # Compter les messages pending
        pending_response = client.table("messages").select("id", count="exact").eq(
            "campaign_id", campaign_id
        ).eq("status", "pending").execute()
        pending_count = pending_response.count or 0
        
        # Compter les Message 1 envoyés (sent/delivered/read)
        message_1_sent_response = client.table("messages").select("id", count="exact").eq(
            "campaign_id", campaign_id
        ).eq("message_type", "message_1").in_("status", ["sent", "delivered", "read"]).execute()
        message_1_sent_count = message_1_sent_response.count or 0
        
        # Compter les Message 2 envoyés (interactions complètes)
        message_2_sent_response = client.table("messages").select("id", count="exact").eq(
            "campaign_id", campaign_id
        ).eq("message_type", "message_2").in_("status", ["sent", "delivered", "read"]).execute()
        message_2_sent_count = message_2_sent_response.count or 0
        
        # Compter les messages "no_interaction" (24h sans réponse)
        no_interaction_response = client.table("messages").select("id", count="exact").eq(
            "campaign_id", campaign_id
        ).eq("status", "no_interaction").execute()
        no_interaction_count = no_interaction_response.count or 0
        
        # Compter les messages échoués
        failed_response = client.table("messages").select("id", count="exact").eq(
            "campaign_id", campaign_id
        ).eq("status", "failed").execute()
        failed_count = failed_response.count or 0
        
        # Total des messages envoyés (tous types)
        total_sent_response = client.table("messages").select("id", count="exact").eq(
            "campaign_id", campaign_id
        ).in_("status", ["sent", "delivered", "read"]).execute()
        total_sent_count = total_sent_response.count or 0
        
        # =================================================================
        # LOGIQUE DE COMPLÉTION SIMPLIFIÉE (Requirements 1.2, 1.4, 2.2)
        # =================================================================
        # 
        # Condition de complétion:
        # - pending = 0 (tous les Message 1 sont envoyés)
        # - ET (msg2_sent + no_interaction + failed) >= msg1_sent
        #
        # Cette condition garantit que tous les contacts ont terminé leur cycle:
        # - Soit ils ont interagi et reçu le Message 2
        # - Soit ils n'ont pas interagi dans les 24h (no_interaction)
        # - Soit leur message a échoué (failed)
        # =================================================================
        
        # Calculer le nombre de contacts qui ont terminé leur cycle
        contacts_completed = message_2_sent_count + no_interaction_count + failed_count
        
        # Vérifier si tous les contacts ont terminé
        # Note: message_1_sent_count > 0 évite la division par zéro et les campagnes vides
        all_contacts_completed = (
            message_1_sent_count > 0 and 
            contacts_completed >= message_1_sent_count
        )
        
        # Déterminer le nouveau statut
        if pending_count > 0:
            # Il reste des messages pending -> campagne en cours (Requirements 1.4)
            new_status = "sending"
            logger.debug(
                f"Campagne {campaign_id}: {pending_count} messages pending, status=sending"
            )
        elif all_contacts_completed:
            # Tous les contacts ont terminé leur cycle -> campagne complète (Requirements 1.2)
            if failed_count > 0 and total_sent_count == 0:
                # Tous les messages ont échoué
                new_status = "failed"
            else:
                new_status = "completed"
            
            logger.info(
                f"Campagne {campaign_id} complète: "
                f"msg1_sent={message_1_sent_count}, msg2_sent={message_2_sent_count}, "
                f"no_interaction={no_interaction_count}, failed={failed_count}"
            )
        else:
            # Pas de pending mais tous les contacts n'ont pas terminé
            # -> en attente d'interactions ou de la tâche check_expired_interactions
            new_status = "sending"
            logger.info(
                f"Campagne {campaign_id}: en attente d'interactions "
                f"({contacts_completed}/{message_1_sent_count} contacts terminés)"
            )
        
        # =================================================================
        # MISE À JOUR DE LA CAMPAGNE
        # =================================================================
        
        total_failed = failed_count + no_interaction_count
        
        update_data = {
            "sent_count": total_sent_count,
            "success_count": total_sent_count,
            "failed_count": total_failed
        }
        
        # Mettre à jour le statut si nécessaire
        current_status = campaign.get("status")
        if new_status != current_status:
            update_data["status"] = new_status
        
        # IMPORTANT (Requirements 1.3): Toujours définir completed_at lors de la complétion
        # Vérifier si le statut devient "completed" OU si c'est déjà "completed" sans timestamp
        if new_status == "completed":
            current_completed_at = campaign.get("completed_at")
            if not current_completed_at:
                # Définir completed_at si pas encore défini
                update_data["completed_at"] = datetime.now(timezone.utc).isoformat()
                logger.info(f"Campagne {campaign_id}: completed_at défini")
        
        client.table("campaigns").update(update_data).eq("id", campaign_id).execute()
        
        logger.info(
            f"Campagne {campaign_id} mise à jour: status={new_status}, "
            f"msg1_sent={message_1_sent_count}, msg2_sent={message_2_sent_count}, "
            f"no_interaction={no_interaction_count}, failed={failed_count}, pending={pending_count}"
        )
        
        return {
            "success": True,
            "campaign_id": campaign_id,
            "status": new_status,
            "message_1_sent": message_1_sent_count,
            "message_2_sent": message_2_sent_count,
            "no_interaction_count": no_interaction_count,
            "failed_count": failed_count,
            "pending_count": pending_count,
            "contacts_completed": contacts_completed,
            "all_contacts_completed": all_contacts_completed
        }
        
    except Exception as e:
        logger.exception(f"Erreur mise à jour statut campagne {campaign_id}: {e}")
        return {"success": False, "error": str(e)}


# ==========================================================================
# NOTE: MESSAGE 2 LOGIC
# ==========================================================================
# Le Message 2 est envoyé IMMÉDIATEMENT quand le contact répond au Message 1.
# Cette logique est gérée dans webhooks.py -> process_wassenger_message -> _schedule_message_2_wassenger
# 
# Si le contact ne répond pas dans les 24h, le Message 2 n'est JAMAIS envoyé.
# Cela permet aux campagnes de se terminer après 24h maximum.
# ==========================================================================
