# Design Document: Campaign Auto-Completion

## Overview

Ce document décrit la conception pour corriger le problème d'auto-terminaison des campagnes WhatsApp. Actuellement, les campagnes restent en statut "sending" même après que tous les contacts ont reçu leur Message 2, car la vérification du statut n'est déclenchée qu'une seule fois au lancement.

## Architecture

### Composants Modifiés

1. **webhooks.py** - `_schedule_message_2_wassenger()`
   - Ajouter un appel à `update_campaign_status` après l'envoi du Message 2

2. **message_tasks.py** - `send_single_message()`
   - Déclencher la vérification du statut après l'envoi réussi d'un Message 2

3. **celery_app.py** - Nouvelle tâche périodique
   - Ajouter `check_sending_campaigns` qui s'exécute toutes les 2 minutes

4. **update_campaign_status()** - Amélioration de la logique
   - Simplifier la condition de complétion

### Flux de Données

```
Message 2 envoyé
       ↓
send_single_message() détecte message_type="message_2"
       ↓
Déclenche update_campaign_status.delay(campaign_id)
       ↓
Vérifie si tous les contacts ont terminé
       ↓
Si oui → status = "completed", completed_at = now()
```

## Components and Interfaces

### Interface: Campaign Status Checker

```python
def check_campaign_completion(campaign_id: int) -> dict:
    """
    Vérifie si une campagne doit être marquée comme terminée.
    
    Returns:
        {
            "should_complete": bool,
            "message_1_sent": int,
            "message_2_sent": int,
            "no_interaction": int,
            "failed": int,
            "pending": int
        }
    """
```

### Modification: send_single_message()

Après l'envoi réussi d'un Message 2, déclencher la vérification :

```python
if message.get("message_type") == "message_2" and response.success:
    # Déclencher la vérification du statut de la campagne
    update_campaign_status.apply_async(
        args=[message["campaign_id"]],
        countdown=5  # Petit délai pour laisser le temps à la BDD
    )
```

### Nouvelle Tâche: check_sending_campaigns

```python
@celery_app.task(name="app.tasks.celery_app.check_sending_campaigns")
def check_sending_campaigns():
    """
    Vérifie toutes les campagnes en statut "sending" et les termine si nécessaire.
    Exécutée toutes les 2 minutes via Celery Beat.
    """
```

## Data Models

Aucune modification du schéma de base de données n'est nécessaire. Les champs existants sont suffisants :
- `campaigns.status` : "draft" | "sending" | "completed" | "failed"
- `campaigns.completed_at` : timestamp de fin
- `messages.status` : "pending" | "sent" | "delivered" | "read" | "failed" | "no_interaction"
- `messages.message_type` : "message_1" | "message_2"

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Campaign Completion When All Contacts Finished

*For any* campaign where all contacts have a final state (message_2 sent, no_interaction, or failed), the campaign status SHALL be "completed".

**Validates: Requirements 1.2, 2.2**

### Property 2: Pending Messages Prevent Completion

*For any* campaign with at least one pending message, the campaign status SHALL remain "sending".

**Validates: Requirements 1.4**

### Property 3: Completed Timestamp Set On Completion

*For any* campaign that transitions to "completed" status, the completed_at field SHALL be set to a non-null timestamp.

**Validates: Requirements 1.3**

### Property 4: Message 2 Triggers Status Check

*For any* successful Message 2 send, the campaign status checker SHALL be triggered within 10 seconds.

**Validates: Requirements 1.1, 3.4**

### Property 5: Correct Message Counting

*For any* campaign, the sum of (message_2_sent + no_interaction + failed) SHALL equal the total number of contacts that received Message 1 when the campaign is completed.

**Validates: Requirements 2.3**

## Error Handling

1. **Erreur lors de la vérification du statut**
   - Logger l'erreur avec le campaign_id
   - Ne pas modifier le statut de la campagne
   - La tâche périodique réessaiera dans 2 minutes

2. **Erreur lors de l'envoi du Message 2**
   - Marquer le message comme "failed"
   - Déclencher quand même la vérification du statut
   - Le contact sera compté comme "failed" dans les stats

3. **Webhook non reçu**
   - La tâche périodique détectera les campagnes bloquées
   - Après 24h, les contacts sans interaction seront marqués "no_interaction"

## Testing Strategy

### Unit Tests

1. Test de la logique de complétion avec différents états de contacts
2. Test du déclenchement de la vérification après Message 2
3. Test de la tâche périodique

### Property-Based Tests

Utiliser Hypothesis pour Python :

```python
from hypothesis import given, strategies as st

@given(
    num_message_2_sent=st.integers(min_value=0, max_value=100),
    num_no_interaction=st.integers(min_value=0, max_value=100),
    num_failed=st.integers(min_value=0, max_value=100),
    num_pending=st.integers(min_value=0, max_value=100)
)
def test_campaign_completion_property(num_message_2_sent, num_no_interaction, num_failed, num_pending):
    """
    Property 1 & 2: Campaign completion logic
    """
    # Si pending > 0, status doit être "sending"
    # Si pending == 0 et tous les contacts ont terminé, status doit être "completed"
```

Configuration : minimum 100 itérations par test.
