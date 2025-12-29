# Message 2 - Envoi Immédiat sur Interaction

## Vue d'ensemble

Cette fonctionnalité permet d'envoyer automatiquement un Message 2 (message de suivi) **immédiatement** quand un contact répond au Message 1, dans une fenêtre de 24 heures. Si le contact ne répond pas dans les 24h, le Message 2 n'est jamais envoyé et la campagne se termine pour ce contact.

## Logique Métier

```
Message 1 envoyé au contact
        │
        ├── Contact répond dans les 24h ──► Message 2 envoyé IMMÉDIATEMENT
        │
        └── Contact ne répond pas dans les 24h ──► Message 2 N'EST PAS envoyé
                                                   (campagne terminée pour ce contact)
```

**Avantages de cette approche :**
- Les campagnes se terminent après 24h maximum
- On ne relance que les contacts qui ont montré de l'intérêt
- Réponse rapide aux contacts engagés

## User Stories

### US-1: Envoi immédiat du Message 2 sur interaction
**En tant qu'** administrateur de campagne  
**Je veux** que le Message 2 soit envoyé immédiatement quand un contact répond  
**Afin de** maintenir l'engagement avec les contacts intéressés

**Critères d'acceptation:**
- [x] Quand un webhook de réponse est reçu, le système vérifie si un Message 1 récent existe (24h)
- [x] Si un Message 1 existe et qu'aucun Message 2 n'a été envoyé, le Message 2 est créé et envoyé
- [x] Le Message 2 est envoyé avec un délai de 2 secondes (rate limit Wassenger)
- [x] L'interaction est enregistrée dans la table `interactions`

### US-2: Pas de Message 2 si pas d'interaction
**En tant que** système  
**Je veux** ne pas envoyer de Message 2 si le contact n'a pas répondu dans les 24h  
**Afin de** terminer les campagnes dans un délai raisonnable

**Critères d'acceptation:**
- [x] Aucune tâche planifiée n'est créée après l'envoi du Message 1
- [x] Si le contact ne répond pas, le Message 2 n'est jamais créé
- [x] La campagne peut se terminer après 24h sans messages en attente

### US-3: Vérification du Message 1 récent
**En tant que** système  
**Je veux** vérifier qu'un Message 1 a été envoyé dans les dernières 24h  
**Afin de** ne pas envoyer de Message 2 pour des campagnes anciennes

**Critères d'acceptation:**
- [x] La recherche du Message 1 filtre sur `sent_at >= (now - 24h)`
- [x] Seuls les Message 1 avec statut `sent`, `delivered` ou `read` sont considérés
- [x] Si aucun Message 1 récent n'est trouvé, le Message 2 n'est pas envoyé

### US-4: Éviter les doublons de Message 2
**En tant que** système  
**Je veux** vérifier qu'un Message 2 n'a pas déjà été envoyé  
**Afin de** ne pas envoyer plusieurs fois le même message

**Critères d'acceptation:**
- [x] Avant de créer un Message 2, vérifier si un existe déjà pour ce contact/campagne
- [x] Si un Message 2 existe (quel que soit son statut), ne pas en créer un nouveau
- [x] Logger l'information pour traçabilité

### US-5: Campagnes multiples simultanées
**En tant qu'** administrateur  
**Je veux** pouvoir lancer plusieurs campagnes en même temps  
**Afin de** cibler différents segments de contacts simultanément

**Critères d'acceptation:**
- [x] Chaque campagne a ses propres tâches Celery indépendantes
- [x] Les Messages 2 de différentes campagnes sont gérés indépendamment
- [x] Le rate limiting (1 msg/seconde) est respecté globalement
- [x] Les statistiques de chaque campagne sont mises à jour indépendamment

## Architecture Technique

### Flux de données - Envoi Message 2

```
Webhook réponse reçu (message:in:new)
        │
        ▼
process_wassenger_message()
        │
        ▼
┌───────────────────────────────────────┐
│ 1. Rechercher contact par numéro      │
│ 2. Rechercher Message 1 récent (24h)  │
│ 3. Vérifier si Message 2 existe déjà  │
└───────────────────────────────────────┘
        │
        ├── Pas de Message 1 récent ──► Enregistrer interaction, pas de Message 2
        │
        ├── Message 2 déjà envoyé ──► Enregistrer interaction, pas de nouveau Message 2
        │
        └── Message 1 récent + pas de Message 2 ──► _schedule_message_2_wassenger()
                                                            │
                                                            ▼
                                                   Créer Message 2 en BDD
                                                            │
                                                            ▼
                                                   send_single_message.apply_async()
                                                   (countdown=2s pour rate limit)
```

### Flux de données - Pas d'interaction

```
Message 1 envoyé
        │
        ▼
Aucune tâche planifiée (pas de countdown 24h)
        │
        ▼
Si contact ne répond pas ──► Rien ne se passe
        │
        ▼
Campagne terminée pour ce contact après 24h
```

## Fichiers impactés

- `backend/app/routers/webhooks.py` - Fonction `_schedule_message_2_wassenger` modifiée pour envoyer immédiatement
- `backend/app/tasks/message_tasks.py` - Suppression de la planification automatique après Message 1

## Configuration

| Constante | Valeur | Description |
|-----------|--------|-------------|
| `WASSENGER_RATE_LIMIT_SECONDS` | 1 | Délai entre chaque message (rate limit) |
| Fenêtre de réponse | 24h | Durée pendant laquelle une réponse déclenche le Message 2 |

## Statut d'implémentation

- [x] Modification de `_schedule_message_2_wassenger` pour envoi immédiat
- [x] Suppression de la planification automatique dans `send_single_message`
- [x] Suppression des tâches `schedule_message_2_for_contact` et `cancel_pending_message_2`
- [x] Mise à jour des docstrings et commentaires
- [x] Vérification syntaxe Python ✓
- [x] Build frontend ✓
- [ ] Tests en environnement de staging
