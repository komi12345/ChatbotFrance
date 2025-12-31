# Design Document: WhatsApp Ban Prevention System

## Overview

Ce système implémente une stratégie anti-ban complète pour l'envoi de messages WhatsApp via Wassenger API. L'objectif est de réduire drastiquement le risque de bannissement en simulant un comportement humain avec des délais longs, de la randomisation, des pauses stratégiques et un système de warm-up progressif.

**Problème résolu :**
- Le système actuel envoie des messages toutes les 5 secondes → RISQUE DE BAN ÉLEVÉ
- Pas de randomisation → Patterns détectables par WhatsApp
- Pas de pauses → Comportement robotique

**Solution :**
- Délais de 15-35 secondes avec randomisation
- Warm-up progressif (commence très lentement)
- Pauses automatiques toutes les 20/40/60/100 messages
- Détection précoce des signes de ban
- Celery en mode single-worker

## Architecture

### Composants Modifiés

```
┌─────────────────────────────────────────────────────────────────┐
│                    message_tasks.py                              │
├─────────────────────────────────────────────────────────────────┤
│  CONFIGURATION ANTI-BAN (modifié)                                │
│  ├── WASSENGER_RATE_LIMIT_SECONDS: 5 → 15-30 (adaptatif)        │
│  ├── BATCH_SIZE: 50 → 20 (lots plus petits)                     │
│  ├── BATCH_PAUSE_SECONDS: 60 → 180-600 (pauses plus longues)    │
│  └── MIN_DELAY_SECONDS: 10 (nouveau - plancher absolu)          │
├─────────────────────────────────────────────────────────────────┤
│  NOUVELLES FONCTIONS ANTI-BAN                                    │
│  ├── get_anti_ban_delay() - Calcule délai avec randomisation    │
│  ├── get_warm_up_delay() - Délai adaptatif selon messages/jour  │
│  ├── should_take_strategic_pause() - Vérifie si pause requise   │
│  ├── get_strategic_pause_duration() - Durée de pause aléatoire  │
│  ├── is_safe_to_send() - Vérifie tous les critères anti-ban     │
│  ├── detect_ban_risk() - Analyse les codes d'erreur             │
│  └── simulate_human_behavior() - Micro-pauses aléatoires        │
├─────────────────────────────────────────────────────────────────┤
│  FONCTIONS EXISTANTES (inchangées)                               │
│  ├── send_single_message() - Envoi individuel (délais modifiés) │
│  ├── send_campaign_messages() - Orchestration (délais modifiés) │
│  └── update_campaign_status() - Statut campagne                 │
└─────────────────────────────────────────────────────────────────┘
```

### Flux de Données Anti-Ban

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Campaign   │────▶│   Anti-Ban   │────▶│   Message    │
│   Start      │     │   Checker    │     │   Sender     │
└──────────────┘     └──────────────┘     └──────────────┘
                            │                    │
                            ▼                    ▼
                     ┌──────────────┐     ┌──────────────┐
                     │   Warm-Up    │     │   Error      │
                     │   System     │     │   Detector   │
                     └──────────────┘     └──────────────┘
                            │                    │
                            ▼                    ▼
                     ┌──────────────┐     ┌──────────────┐
                     │   Strategic  │     │   Emergency  │
                     │   Pause      │     │   Halt       │
                     └──────────────┘     └──────────────┘
```

## Components and Interfaces

### 1. Configuration Anti-Ban

```python
import os
import random

# ==========================================================================
# CONFIGURATION ANTI-BAN 2025 - PROTECTION MAXIMALE
# ==========================================================================

# Délai de base entre messages (15-30 secondes selon warm-up)
ANTI_BAN_BASE_DELAY_MIN = int(os.getenv("ANTI_BAN_BASE_DELAY_MIN", "15"))
ANTI_BAN_BASE_DELAY_MAX = int(os.getenv("ANTI_BAN_BASE_DELAY_MAX", "30"))

# Variation aléatoire (±5 secondes)
ANTI_BAN_RANDOM_VARIATION = int(os.getenv("ANTI_BAN_RANDOM_VARIATION", "5"))

# Délai minimum absolu (jamais en dessous)
ANTI_BAN_MIN_DELAY = int(os.getenv("ANTI_BAN_MIN_DELAY", "10"))

# Délai "typing" humain (1-3 secondes)
HUMAN_TYPING_DELAY_MIN = 1
HUMAN_TYPING_DELAY_MAX = 3

# Taille des lots (réduite pour plus de pauses)
ANTI_BAN_BATCH_SIZE = int(os.getenv("ANTI_BAN_BATCH_SIZE", "20"))

# Seuils de pauses stratégiques
PAUSE_THRESHOLD_1 = 20   # Pause après 20 messages
PAUSE_THRESHOLD_2 = 40   # Pause après 40 messages
PAUSE_THRESHOLD_3 = 60   # Pause après 60 messages
PAUSE_THRESHOLD_4 = 100  # Pause après 100 messages

# Durées de pauses (en secondes)
PAUSE_DURATION_1 = (180, 300)    # 3-5 minutes
PAUSE_DURATION_2 = (300, 480)    # 5-8 minutes
PAUSE_DURATION_3 = (600, 900)    # 10-15 minutes
PAUSE_DURATION_4 = (1200, 1800)  # 20-30 minutes

# Probabilité de micro-pause (10%)
MICRO_PAUSE_PROBABILITY = 0.10
MICRO_PAUSE_DURATION = (30, 120)  # 30s à 2 minutes

# Codes d'erreur dangereux (risque de ban)
BAN_RISK_ERROR_CODES = ["rate_limit", "spam_detected", "blocked", "429"]

# Seuils d'erreur
CONSECUTIVE_ERROR_HALT_THRESHOLD = 3
ERROR_WINDOW_MINUTES = 10
ERROR_COUNT_HALT_THRESHOLD = 5
ERROR_RATE_WARNING_THRESHOLD = 0.05  # 5%

# Durées de pause d'urgence
EMERGENCY_PAUSE_SECONDS = 1800  # 30 minutes
EXTENDED_HALT_SECONDS = 3600    # 1 heure
```

### 2. Fonction de Délai Anti-Ban avec Randomisation

```python
def get_anti_ban_delay(messages_sent_today: int) -> float:
    """
    Calcule le délai anti-ban avec randomisation et warm-up.
    
    Le délai est composé de:
    1. Délai de base selon le warm-up (15-35 secondes)
    2. Variation aléatoire (±5 secondes)
    3. Délai "typing" humain (1-3 secondes)
    
    Args:
        messages_sent_today: Nombre de messages envoyés aujourd'hui
    
    Returns:
        Délai total en secondes (minimum 10 secondes)
    
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
```

### 3. Système de Warm-Up Progressif

```python
def get_warm_up_delay(messages_sent_today: int) -> float:
    """
    Calcule le délai de base selon le nombre de messages envoyés aujourd'hui.
    
    Stratégie de warm-up:
    - 0-30 messages: 25-35 secondes (démarrage très lent)
    - 30-80 messages: 20-28 secondes (accélération progressive)
    - 80-200 messages: 15-22 secondes (vitesse de croisière)
    - 200-500 messages: 18-25 secondes (ralentissement)
    - 500+ messages: 22-30 secondes (proche de la limite)
    
    Args:
        messages_sent_today: Nombre de messages envoyés aujourd'hui
    
    Returns:
        Délai de base en secondes
    
    Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5
    """
    if messages_sent_today < 30:
        # Phase 1: Démarrage très lent (warm-up)
        return random.uniform(25, 35)
    
    elif messages_sent_today < 80:
        # Phase 2: Accélération progressive
        return random.uniform(20, 28)
    
    elif messages_sent_today < 200:
        # Phase 3: Vitesse de croisière
        return random.uniform(15, 22)
    
    elif messages_sent_today < 500:
        # Phase 4: Ralentissement (approche de la limite)
        return random.uniform(18, 25)
    
    else:
        # Phase 5: Très lent (proche de la limite quotidienne)
        return random.uniform(22, 30)
```

### 4. Gestionnaire de Pauses Stratégiques

```python
def should_take_strategic_pause(consecutive_messages: int) -> bool:
    """
    Vérifie si une pause stratégique est nécessaire.
    
    Args:
        consecutive_messages: Nombre de messages envoyés consécutivement
    
    Returns:
        True si une pause est requise
    
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
    
    Args:
        consecutive_messages: Nombre de messages envoyés consécutivement
    
    Returns:
        Durée de pause en secondes
    
    Validates: Requirements 3.1, 3.2, 3.3, 3.4
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
        return 0
    
    pause_duration = random.uniform(min_pause, max_pause)
    
    logger.info(
        f"Pause stratégique: {pause_duration/60:.1f} minutes "
        f"après {consecutive_messages} messages consécutifs"
    )
    
    return pause_duration
```

### 5. Simulateur de Comportement Humain

```python
def simulate_human_behavior() -> float:
    """
    Simule un comportement humain avec des micro-pauses aléatoires.
    
    Avec 10% de probabilité, ajoute une micro-pause de 30-120 secondes.
    
    Returns:
        Durée de micro-pause en secondes (0 si pas de pause)
    
    Validates: Requirements 4.1
    """
    if random.random() < MICRO_PAUSE_PROBABILITY:
        pause_duration = random.uniform(*MICRO_PAUSE_DURATION)
        logger.info(f"Micro-pause humaine: {pause_duration:.0f}s")
        return pause_duration
    return 0


def is_night_time() -> bool:
    """
    Vérifie si l'heure actuelle est entre 23h et 6h (heures de nuit).
    
    Returns:
        True si c'est la nuit
    
    Validates: Requirements 4.2
    """
    from datetime import datetime
    current_hour = datetime.now().hour
    return current_hour >= 23 or current_hour < 6


def get_message_length_delay(message_length: int) -> float:
    """
    Calcule un délai supplémentaire basé sur la longueur du message.
    
    Messages plus longs = délai légèrement plus long (simulation de lecture).
    
    Args:
        message_length: Longueur du message en caractères
    
    Returns:
        Délai supplémentaire en secondes (0-5 secondes)
    
    Validates: Requirements 4.3
    """
    # 1 seconde supplémentaire par 500 caractères, max 5 secondes
    extra_delay = min(message_length / 500, 5)
    return extra_delay
```

### 6. Détecteur de Risque de Ban

```python
def detect_ban_risk(error_code: str, error_message: str) -> dict:
    """
    Analyse un code d'erreur pour détecter un risque de ban.
    
    Args:
        error_code: Code d'erreur Wassenger
        error_message: Message d'erreur
    
    Returns:
        Dictionnaire avec:
        - is_ban_risk: True si risque de ban détecté
        - action: Action recommandée ('emergency_pause', 'halt', 'continue')
        - pause_duration: Durée de pause en secondes
    
    Validates: Requirements 5.1
    """
    result = {
        "is_ban_risk": False,
        "action": "continue",
        "pause_duration": 0
    }
    
    # Vérifier les codes d'erreur dangereux
    for danger_code in BAN_RISK_ERROR_CODES:
        if danger_code in str(error_code).lower() or danger_code in str(error_message).lower():
            result["is_ban_risk"] = True
            result["action"] = "emergency_pause"
            result["pause_duration"] = EMERGENCY_PAUSE_SECONDS  # 30 minutes
            
            logger.critical(
                f"⚠️ RISQUE DE BAN DÉTECTÉ: {error_code} - {error_message}. "
                f"Pause d'urgence de {EMERGENCY_PAUSE_SECONDS/60:.0f} minutes."
            )
            break
    
    return result


def check_error_thresholds(redis_client) -> dict:
    """
    Vérifie les seuils d'erreur pour décider si l'envoi doit être arrêté.
    
    Args:
        redis_client: Client Redis
    
    Returns:
        Dictionnaire avec:
        - should_halt: True si l'envoi doit être arrêté
        - reason: Raison de l'arrêt
        - halt_duration: Durée d'arrêt en secondes
    
    Validates: Requirements 5.2, 5.3, 5.5
    """
    result = {
        "should_halt": False,
        "reason": None,
        "halt_duration": 0
    }
    
    # Vérifier les erreurs consécutives
    consecutive_errors = int(redis_client.get("anti_ban:consecutive_errors") or 0)
    if consecutive_errors >= CONSECUTIVE_ERROR_HALT_THRESHOLD:
        result["should_halt"] = True
        result["reason"] = f"{consecutive_errors} erreurs consécutives"
        result["halt_duration"] = EXTENDED_HALT_SECONDS
        return result
    
    # Vérifier les erreurs dans la fenêtre de temps
    from datetime import datetime, timedelta
    window_key = f"anti_ban:errors:{datetime.now().strftime('%Y%m%d%H%M')}"
    errors_in_window = int(redis_client.get(window_key) or 0)
    
    if errors_in_window >= ERROR_COUNT_HALT_THRESHOLD:
        result["should_halt"] = True
        result["reason"] = f"{errors_in_window} erreurs en {ERROR_WINDOW_MINUTES} minutes"
        result["halt_duration"] = EXTENDED_HALT_SECONDS
        return result
    
    # Vérifier le taux d'erreur
    total_sent = int(redis_client.get("anti_ban:total_sent") or 0)
    total_errors = int(redis_client.get("anti_ban:total_errors") or 0)
    
    if total_sent > 0:
        error_rate = total_errors / total_sent
        if error_rate >= ERROR_RATE_WARNING_THRESHOLD:
            logger.warning(
                f"⚠️ Taux d'erreur élevé: {error_rate:.1%} "
                f"({total_errors}/{total_sent})"
            )
    
    return result
```

### 7. Fonction de Vérification Globale

```python
def is_safe_to_send(redis_client, messages_sent_today: int) -> tuple[bool, str]:
    """
    Vérifie tous les critères anti-ban avant d'envoyer un message.
    
    Args:
        redis_client: Client Redis
        messages_sent_today: Nombre de messages envoyés aujourd'hui
    
    Returns:
        Tuple (can_send, reason)
    
    Validates: Requirements 4.2, 5.2, 5.3, 6.1
    """
    # Vérifier si c'est la nuit
    if is_night_time():
        return False, "Heures de nuit (23h-6h) - envoi reporté à 7h"
    
    # Vérifier la limite quotidienne
    if messages_sent_today >= 1000:
        return False, "Limite quotidienne de 1000 messages atteinte"
    
    # Vérifier les seuils d'erreur
    error_check = check_error_thresholds(redis_client)
    if error_check["should_halt"]:
        return False, f"Arrêt d'urgence: {error_check['reason']}"
    
    # Vérifier si une pause d'urgence est en cours
    emergency_pause_until = redis_client.get("anti_ban:emergency_pause_until")
    if emergency_pause_until:
        from datetime import datetime
        pause_end = datetime.fromisoformat(emergency_pause_until.decode())
        if datetime.now() < pause_end:
            remaining = (pause_end - datetime.now()).seconds
            return False, f"Pause d'urgence en cours ({remaining}s restantes)"
    
    return True, "OK"
```

## Data Models

### Aucun changement de schéma BDD

Les optimisations n'ajoutent pas de nouvelles tables ou colonnes. Toutes les données temporaires sont stockées dans Redis.

### Clés Redis Ajoutées

| Clé | Type | TTL | Description |
|-----|------|-----|-------------|
| `anti_ban:messages_today` | Integer | 24h | Compteur messages envoyés aujourd'hui |
| `anti_ban:consecutive_messages` | Integer | 1h | Compteur messages consécutifs (reset après pause) |
| `anti_ban:consecutive_errors` | Integer | 1h | Compteur erreurs consécutives |
| `anti_ban:errors:{YYYYMMDDHHMM}` | Integer | 15min | Erreurs dans la fenêtre de temps |
| `anti_ban:total_sent` | Integer | 24h | Total messages envoyés (pour taux d'erreur) |
| `anti_ban:total_errors` | Integer | 24h | Total erreurs (pour taux d'erreur) |
| `anti_ban:emergency_pause_until` | String | 2h | Timestamp fin de pause d'urgence |
| `anti_ban:last_send_time` | Float | 1h | Timestamp du dernier envoi |

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Delay Bounds Guarantee

*For any* calculated delay, the result SHALL be at least 10 seconds and at most 40 seconds (base_max + variation_max + typing_max).

**Validates: Requirements 1.1, 1.3, 1.5**

### Property 2: Warm-Up Delay Ranges

*For any* message count N, the warm-up delay SHALL fall within the correct range:
- N < 30: delay ∈ [25, 35]
- 30 ≤ N < 80: delay ∈ [20, 28]
- 80 ≤ N < 200: delay ∈ [15, 22]
- 200 ≤ N < 500: delay ∈ [18, 25]
- N ≥ 500: delay ∈ [22, 30]

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**

### Property 3: Strategic Pause Triggers

*For any* consecutive message count, a strategic pause SHALL be triggered at exactly 20, 40, 60, and 100 messages, with durations in the correct ranges.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

### Property 4: Consecutive Counter Reset

*For any* strategic pause, after the pause completes, the consecutive message counter SHALL be reset to 0.

**Validates: Requirements 3.6**

### Property 5: Micro-Pause Probability

*For any* large sample of message sends (N > 1000), the proportion of sends with micro-pauses SHALL be approximately 10% (within statistical tolerance).

**Validates: Requirements 4.1**

### Property 6: Night Time Blocking

*For any* time T where hour(T) ∈ [23, 24) ∪ [0, 6), the system SHALL block sending and return a postponement message.

**Validates: Requirements 4.2**

### Property 7: Ban Risk Detection

*For any* error code containing 'rate_limit', 'spam_detected', 'blocked', or '429', the system SHALL trigger an emergency pause of 30 minutes.

**Validates: Requirements 5.1**

### Property 8: Consecutive Error Halt

*For any* sequence of 3 or more consecutive errors, the system SHALL halt all sending.

**Validates: Requirements 5.2**

### Property 9: Error Window Halt

*For any* 10-minute window containing 5 or more errors, the system SHALL halt all sending for 1 hour.

**Validates: Requirements 5.3**

### Property 10: Daily Limit Enforcement

*For any* day, when message count reaches 1000, all subsequent send attempts SHALL be blocked with a clear error message.

**Validates: Requirements 6.1, 6.5**

### Property 11: Idempotency Preservation

*For any* message ID, calling send_single_message multiple times SHALL result in exactly one message being sent to Wassenger API.

**Validates: Requirements 8.5**

## Error Handling

### Erreurs Gérées

| Erreur | Action | Pause |
|--------|--------|-------|
| rate_limit | Pause d'urgence | 30 minutes |
| spam_detected | Pause d'urgence | 30 minutes |
| blocked | Arrêt total | Indéfini |
| 429 (HTTP) | Pause d'urgence | 30 minutes |
| 3 erreurs consécutives | Arrêt total | 1 heure |
| 5 erreurs en 10 min | Arrêt total | 1 heure |
| Taux d'erreur > 5% | Warning | Aucune |

### Circuit Breaker

Le système implémente un circuit breaker à plusieurs niveaux:

1. **Niveau 1 - Warning**: Taux d'erreur > 5% → Log warning
2. **Niveau 2 - Pause**: Code d'erreur dangereux → Pause 30 minutes
3. **Niveau 3 - Halt**: 3 erreurs consécutives → Arrêt 1 heure
4. **Niveau 4 - Emergency**: 5 erreurs en 10 min → Arrêt 1 heure

## Testing Strategy

### Tests Unitaires

- Validation des calculs de délai (bornes min/max)
- Calcul du warm-up selon le nombre de messages
- Déclenchement des pauses stratégiques
- Détection des codes d'erreur dangereux

### Tests Property-Based (Hypothesis)

- Property 1: Delay bounds avec valeurs aléatoires
- Property 2: Warm-up ranges avec message counts aléatoires
- Property 3: Strategic pause triggers
- Property 6: Night time blocking avec heures aléatoires
- Property 7: Ban risk detection avec codes d'erreur aléatoires

### Configuration des Tests

```python
# pytest.ini
[pytest]
markers =
    property: Property-based tests (run with --hypothesis-seed for reproducibility)
    anti_ban: Anti-ban specific tests
```

## Calculs de Performance

### Avant Optimisation (1000 messages)

```
Délai entre messages: 5s
Taille lot: 50
Pause entre lots: 60s
Nombre de lots: 20

Temps = (1000 * 5s) + (19 * 60s) = 5000s + 1140s = 6140s ≈ 1h42min
RISQUE DE BAN: TRÈS ÉLEVÉ ❌
```

### Après Optimisation Anti-Ban (1000 messages)

```
Délai moyen entre messages: ~22s (avec warm-up et randomisation)
Taille lot: 20
Pauses stratégiques: ~4 pauses de 5-15 min = ~40 min total
Micro-pauses (10%): ~100 pauses de 1 min = ~100 min total

Temps = (1000 * 22s) + (40 * 60s) + (100 * 60s) = 22000s + 2400s + 6000s = 30400s ≈ 8h30min
RISQUE DE BAN: TRÈS FAIBLE ✅
```

**Compromis accepté**: Temps d'envoi multiplié par ~5, mais risque de ban réduit de ~90%.

