# Design Document: Message Sending Optimization

## Overview

Cette optimisation vise à réduire le temps d'envoi de campagnes de 500-1000 messages de ~1.5 heures à ~50-60 minutes, tout en préservant la logique existante de Message 1/Message 2 et en évitant les bans WhatsApp.

**Principes clés :**
1. Réduire les délais conservateurs sans compromettre la sécurité
2. Ajouter un système adaptatif qui réagit aux erreurs
3. Préserver 100% de la logique métier existante
4. Améliorer le monitoring et la récupération après crash

## Architecture

### Composants Modifiés

```
┌─────────────────────────────────────────────────────────────────┐
│                    message_tasks.py                              │
├─────────────────────────────────────────────────────────────────┤
│  CONFIGURATION (modifié)                                         │
│  ├── WASSENGER_RATE_LIMIT_SECONDS: 5 → 3 (configurable)         │
│  ├── BATCH_SIZE: 50 → 75 (configurable)                         │
│  └── BATCH_PAUSE_SECONDS: 60 → 30 (configurable)                │
├─────────────────────────────────────────────────────────────────┤
│  NOUVELLES FONCTIONS                                             │
│  ├── get_adaptive_delay() - Calcule le délai adaptatif          │
│  ├── get_campaign_error_rate() - Récupère le taux d'erreur      │
│  └── update_campaign_progress() - Met à jour la progression     │
├─────────────────────────────────────────────────────────────────┤
│  FONCTIONS EXISTANTES (inchangées)                               │
│  ├── send_single_message() - Envoi individuel                   │
│  ├── send_campaign_messages() - Orchestration (délais modifiés) │
│  └── update_campaign_status() - Statut campagne                 │
└─────────────────────────────────────────────────────────────────┘
```

### Flux de Données

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Campaign   │────▶│    Batch     │────▶│   Message    │
│   Start      │     │  Processor   │     │   Sender     │
└──────────────┘     └──────────────┘     └──────────────┘
                            │                    │
                            ▼                    ▼
                     ┌──────────────┐     ┌──────────────┐
                     │   Adaptive   │◀────│   Error      │
                     │   Delay      │     │   Tracker    │
                     └──────────────┘     └──────────────┘
```

## Components and Interfaces

### 1. Configuration Optimisée

```python
# Configuration par défaut (optimisée pour comptes matures)
WASSENGER_RATE_LIMIT_SECONDS = int(os.getenv("WASSENGER_RATE_LIMIT_SECONDS", "3"))
BATCH_SIZE = int(os.getenv("WASSENGER_BATCH_SIZE", "75"))
BATCH_PAUSE_SECONDS = int(os.getenv("WASSENGER_BATCH_PAUSE_SECONDS", "30"))

# Seuils adaptatifs
ERROR_RATE_THRESHOLD = 0.05  # 5%
DELAY_INCREASE_FACTOR = 1.5  # +50% si erreurs
MIN_DELAY_SECONDS = 2
MAX_DELAY_SECONDS = 10
```

### 2. Fonction de Délai Adaptatif

```python
def get_adaptive_delay(campaign_id: int, base_delay: int = WASSENGER_RATE_LIMIT_SECONDS) -> int:
    """
    Calcule le délai adaptatif basé sur le taux d'erreur de la campagne.
    
    Si le taux d'erreur dépasse 5%, augmente le délai de 50%.
    Le délai reste dans les limites MIN_DELAY_SECONDS et MAX_DELAY_SECONDS.
    
    Args:
        campaign_id: ID de la campagne
        base_delay: Délai de base en secondes
    
    Returns:
        Délai adapté en secondes
    """
    error_rate = get_campaign_error_rate(campaign_id)
    
    if error_rate > ERROR_RATE_THRESHOLD:
        adjusted_delay = int(base_delay * DELAY_INCREASE_FACTOR)
        logger.warning(
            f"Campagne {campaign_id}: taux d'erreur {error_rate:.1%} > {ERROR_RATE_THRESHOLD:.1%}, "
            f"délai augmenté de {base_delay}s à {adjusted_delay}s"
        )
        return min(adjusted_delay, MAX_DELAY_SECONDS)
    
    return max(base_delay, MIN_DELAY_SECONDS)
```

### 3. Suivi du Taux d'Erreur

```python
def get_campaign_error_rate(campaign_id: int) -> float:
    """
    Calcule le taux d'erreur actuel d'une campagne.
    
    Taux = failed_count / (sent_count + failed_count)
    
    Args:
        campaign_id: ID de la campagne
    
    Returns:
        Taux d'erreur entre 0.0 et 1.0
    """
    try:
        redis_client = monitoring_service.redis_client
        
        # Récupérer les compteurs depuis Redis (plus rapide que BDD)
        sent_key = f"campaign:{campaign_id}:sent"
        failed_key = f"campaign:{campaign_id}:failed"
        
        sent = int(redis_client.get(sent_key) or 0)
        failed = int(redis_client.get(failed_key) or 0)
        
        total = sent + failed
        if total == 0:
            return 0.0
        
        return failed / total
    except Exception as e:
        logger.error(f"Erreur calcul taux d'erreur campagne {campaign_id}: {e}")
        return 0.0  # En cas d'erreur, pas d'ajustement
```

### 4. Mise à Jour de la Progression

```python
def update_campaign_progress(campaign_id: int, message_id: int, success: bool) -> None:
    """
    Met à jour la progression de la campagne dans Redis.
    
    Utilisé pour:
    - Calcul du taux d'erreur adaptatif
    - Récupération après crash
    - Affichage temps réel
    
    Args:
        campaign_id: ID de la campagne
        message_id: ID du message traité
        success: True si envoi réussi
    """
    try:
        redis_client = monitoring_service.redis_client
        
        if success:
            redis_client.incr(f"campaign:{campaign_id}:sent")
        else:
            redis_client.incr(f"campaign:{campaign_id}:failed")
        
        # Stocker le dernier message traité pour récupération
        redis_client.set(f"campaign:{campaign_id}:last_message", message_id)
        
        # TTL de 24h pour nettoyage automatique
        redis_client.expire(f"campaign:{campaign_id}:sent", 86400)
        redis_client.expire(f"campaign:{campaign_id}:failed", 86400)
        redis_client.expire(f"campaign:{campaign_id}:last_message", 86400)
        
    except Exception as e:
        logger.error(f"Erreur mise à jour progression campagne {campaign_id}: {e}")
```

## Data Models

### Aucun changement de schéma BDD

Les optimisations n'ajoutent pas de nouvelles tables ou colonnes. Toutes les données temporaires sont stockées dans Redis.

### Clés Redis Ajoutées

| Clé | Type | TTL | Description |
|-----|------|-----|-------------|
| `campaign:{id}:sent` | Integer | 24h | Compteur messages envoyés |
| `campaign:{id}:failed` | Integer | 24h | Compteur messages échoués |
| `campaign:{id}:last_message` | Integer | 24h | ID du dernier message traité |

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Configuration Validation

*For any* rate limit delay value, the system SHALL accept values between 2 and 10 seconds, and reject values outside this range.

**Validates: Requirements 1.1, 2.1**

### Property 2: Adaptive Rate Limiting

*For any* campaign with error rate > 5%, the calculated delay SHALL be exactly 50% higher than the base delay, capped at MAX_DELAY_SECONDS.

**Validates: Requirements 1.3, 1.4**

### Property 3: Completion Time Estimation

*For any* campaign with N messages, batch size B, delay D, and pause P, the estimated completion time SHALL be within 10% of: `(N * D) + ((N / B) * P)`.

**Validates: Requirements 2.3, 6.4**

### Property 4: Campaign Resume After Interruption

*For any* interrupted campaign, when resumed, only messages with status "pending" SHALL be processed, and no message SHALL be sent twice.

**Validates: Requirements 2.5, 3.5**

### Property 5: Message 1/Message 2 Logic Preservation

*For any* campaign execution, the Message 2 scheduling logic SHALL remain unchanged: Message 2 is sent immediately when contact replies within 24h, never otherwise.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

### Property 6: Idempotency Guarantee

*For any* message ID, calling send_single_message multiple times SHALL result in exactly one message being sent to Wassenger API.

**Validates: Requirements 3.5, 4.3**

### Property 7: Exponential Backoff Retry

*For any* failed message with retry count N, the retry delay SHALL be `base_delay * 2^(N-1)` seconds.

**Validates: Requirements 4.2**

### Property 8: Progress Tracking Consistency

*For any* campaign, the sum of (sent + failed + pending) messages SHALL always equal total_recipients.

**Validates: Requirements 4.3, 6.1**

## Error Handling

### Erreurs Gérées

| Erreur | Action | Impact sur Délai |
|--------|--------|------------------|
| Rate limit Wassenger (429) | Retry après 60s | +50% délai |
| Timeout réseau | Retry avec backoff | Aucun |
| Device not connected (503) | Retry après 20s | Aucun |
| Message failed | Compteur erreur +1 | Adaptatif |

### Circuit Breaker

Si le taux d'erreur dépasse 20%, la campagne est mise en pause automatiquement avec notification à l'administrateur.

```python
CIRCUIT_BREAKER_THRESHOLD = 0.20  # 20%

def check_circuit_breaker(campaign_id: int) -> bool:
    """Vérifie si le circuit breaker doit être activé."""
    error_rate = get_campaign_error_rate(campaign_id)
    if error_rate > CIRCUIT_BREAKER_THRESHOLD:
        logger.error(f"Circuit breaker activé pour campagne {campaign_id}: {error_rate:.1%} erreurs")
        return True
    return False
```

## Testing Strategy

### Tests Unitaires

- Validation des configurations (limites min/max)
- Calcul du délai adaptatif
- Calcul du taux d'erreur
- Estimation du temps de complétion

### Tests Property-Based (Hypothesis)

- Property 1: Configuration validation avec valeurs aléatoires
- Property 2: Adaptive delay avec taux d'erreur aléatoires
- Property 3: Time estimation avec paramètres aléatoires
- Property 6: Idempotency avec appels multiples

### Tests d'Intégration

- Envoi de 100 messages avec délai réduit
- Récupération après interruption simulée
- Vérification de la logique Message 2

### Configuration des Tests

```python
# pytest.ini
[pytest]
markers =
    property: Property-based tests (run with --hypothesis-seed for reproducibility)
    integration: Integration tests (require Redis and Supabase)
```

## Calculs de Performance

### Avant Optimisation (1000 messages)

```
Délai entre messages: 5s
Taille lot: 50
Pause entre lots: 60s
Nombre de lots: 20

Temps = (1000 * 5s) + (19 * 60s) = 5000s + 1140s = 6140s ≈ 1h42min
```

### Après Optimisation (1000 messages)

```
Délai entre messages: 3s
Taille lot: 75
Pause entre lots: 30s
Nombre de lots: 14

Temps = (1000 * 3s) + (13 * 30s) = 3000s + 390s = 3390s ≈ 56min
```

**Gain: ~46 minutes (45% plus rapide)**
