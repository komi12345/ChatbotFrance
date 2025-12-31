# Implementation Plan: WhatsApp Ban Prevention System

## Overview

Implémentation d'un système anti-ban complet pour l'envoi de messages WhatsApp. Les modifications sont concentrées dans `message_tasks.py` et `celery_app.py`, sans toucher à la structure existante du projet.

## Tasks

- [x] 1. Ajouter la configuration anti-ban dans message_tasks.py
  - Ajouter les nouvelles constantes de configuration anti-ban
  - Définir les seuils de pauses stratégiques
  - Définir les codes d'erreur dangereux
  - _Requirements: 1.1, 1.5, 3.1, 3.2, 3.3, 3.4, 5.1_

- [x] 2. Implémenter le système de délai anti-ban avec randomisation
  - [x] 2.1 Créer la fonction `get_warm_up_delay()` pour calculer le délai selon le nombre de messages du jour
    - Implémenter les 5 phases de warm-up
    - Utiliser `random.uniform()` pour la randomisation
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [x] 2.2 Créer la fonction `get_anti_ban_delay()` pour calculer le délai total
    - Combiner délai de base + variation aléatoire + délai typing
    - Appliquer le plancher minimum de 10 secondes
    - Logger chaque délai calculé
    - _Requirements: 1.1, 1.2, 1.3, 1.5, 1.6_

  - [x] 2.3 Write property test for delay bounds guarantee
    - **Property 1: Delay Bounds Guarantee**
    - **Validates: Requirements 1.1, 1.3, 1.5**

  - [x] 2.4 Write property test for warm-up delay ranges
    - **Property 2: Warm-Up Delay Ranges**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**

- [x] 3. Implémenter le gestionnaire de pauses stratégiques
  - [x] 3.1 Créer la fonction `should_take_strategic_pause()` pour vérifier si une pause est requise
    - Vérifier les seuils 20, 40, 60, 100 messages
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [x] 3.2 Créer la fonction `get_strategic_pause_duration()` pour calculer la durée de pause
    - Retourner une durée aléatoire dans la plage appropriée
    - Logger la pause avec durée et raison
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [x] 3.3 Créer la fonction `reset_consecutive_counter()` pour réinitialiser le compteur après pause
    - Réinitialiser le compteur Redis à 0
    - _Requirements: 3.6_

  - [x] 3.4 Write property test for strategic pause triggers
    - **Property 3: Strategic Pause Triggers**
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4**

- [x] 4. Implémenter le simulateur de comportement humain
  - [x] 4.1 Créer la fonction `simulate_human_behavior()` pour les micro-pauses aléatoires
    - Implémenter la probabilité de 10%
    - Durée de pause entre 30-120 secondes
    - _Requirements: 4.1_

  - [x] 4.2 Créer la fonction `is_night_time()` pour vérifier les heures de nuit
    - Bloquer entre 23h et 6h
    - _Requirements: 4.2_

  - [x] 4.3 Créer la fonction `get_message_length_delay()` pour le délai basé sur la longueur
    - 1 seconde par 500 caractères, max 5 secondes
    - _Requirements: 4.3_

  - [x] 4.4 Write property test for night time blocking
    - **Property 6: Night Time Blocking**
    - **Validates: Requirements 4.2**

- [x] 5. Implémenter le détecteur de risque de ban
  - [x] 5.1 Créer la fonction `detect_ban_risk()` pour analyser les codes d'erreur
    - Détecter rate_limit, spam_detected, blocked, 429
    - Déclencher pause d'urgence de 30 minutes
    - _Requirements: 5.1_

  - [x] 5.2 Créer la fonction `check_error_thresholds()` pour vérifier les seuils d'erreur
    - Arrêter après 3 erreurs consécutives
    - Arrêter après 5 erreurs en 10 minutes
    - Warning si taux d'erreur > 5%
    - _Requirements: 5.2, 5.3, 5.5_

  - [x] 5.3 Créer la fonction `is_safe_to_send()` pour vérification globale
    - Combiner toutes les vérifications anti-ban
    - _Requirements: 4.2, 5.2, 5.3, 6.1_

  - [x] 5.4 Write property test for ban risk detection
    - **Property 7: Ban Risk Detection**
    - **Validates: Requirements 5.1**

  - [x] 5.5 Write property test for consecutive error halt
    - **Property 8: Consecutive Error Halt**
    - **Validates: Requirements 5.2**

- [x] 6. Checkpoint - Vérifier les fonctions anti-ban
  - Ensure all tests pass, ask the user if questions arise.
  - Vérifier que les fonctions retournent les valeurs attendues

- [x] 7. Modifier `wait_for_wassenger_rate_limit()` pour utiliser le nouveau système
  - [x] 7.1 Remplacer le délai fixe par `get_anti_ban_delay()`
    - Récupérer le compteur de messages du jour depuis Redis
    - Appliquer le délai calculé
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 2.4, 2.5_

  - [x] 7.2 Ajouter la vérification `is_safe_to_send()` avant chaque envoi
    - Bloquer si conditions non remplies
    - _Requirements: 4.2, 5.2, 5.3, 6.1_

  - [x] 7.3 Ajouter les micro-pauses humaines
    - Appeler `simulate_human_behavior()` avec 10% de probabilité
    - _Requirements: 4.1_

- [x] 8. Modifier `send_single_message()` pour intégrer la détection de ban
  - [x] 8.1 Ajouter l'appel à `detect_ban_risk()` après chaque erreur
    - Déclencher pause d'urgence si code dangereux détecté
    - _Requirements: 5.1_

  - [x] 8.2 Ajouter la mise à jour des compteurs d'erreur dans Redis
    - Incrémenter consecutive_errors en cas d'échec
    - Réinitialiser en cas de succès
    - _Requirements: 5.2, 5.3_

  - [x] 8.3 Ajouter le délai basé sur la longueur du message
    - Appeler `get_message_length_delay()` avant envoi
    - _Requirements: 4.3_

- [x] 9. Modifier `send_campaign_messages()` pour intégrer les pauses stratégiques
  - [x] 9.1 Ajouter le compteur de messages consécutifs
    - Incrémenter après chaque message
    - Stocker dans Redis
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [x] 9.2 Ajouter la vérification et exécution des pauses stratégiques
    - Appeler `should_take_strategic_pause()` après chaque message
    - Exécuter la pause si nécessaire
    - Réinitialiser le compteur après pause
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.6_

  - [x] 9.3 Réduire la taille des lots de 50 à 20
    - Modifier BATCH_SIZE pour utiliser ANTI_BAN_BATCH_SIZE
    - _Requirements: 3.1_

- [x] 10. Modifier la configuration Celery pour le mode anti-ban
  - [x] 10.1 Réduire worker_concurrency à 1
    - Un seul worker = pas de parallélisme
    - _Requirements: 7.1_

  - [x] 10.2 Réduire worker_prefetch_multiplier à 1
    - Pas de prefetching
    - _Requirements: 7.2_

  - [x] 10.3 Réduire task_default_rate_limit à 4/m
    - Maximum 4 messages par minute
    - _Requirements: 7.3_

  - [x] 10.4 Augmenter soft_time_limit à 300 secondes
    - Plus de temps pour les délais longs
    - _Requirements: 7.5_

- [x] 11. Checkpoint - Tester l'intégration complète
  - Ensure all tests pass, ask the user if questions arise.
  - Vérifier que la logique Message 1/Message 2 fonctionne toujours

- [x] 12. Write property tests for behavior preservation
  - [x] 12.1 Write property test for idempotency preservation
    - **Property 11: Idempotency Preservation**
    - **Validates: Requirements 8.5**

  - [x] 12.2 Write property test for daily limit enforcement
    - **Property 10: Daily Limit Enforcement**
    - **Validates: Requirements 6.1, 6.5**

- [x] 13. Mettre à jour la documentation
  - [x] 13.1 Mettre à jour `.env.example` avec les nouvelles variables anti-ban
    - ANTI_BAN_BASE_DELAY_MIN, ANTI_BAN_BASE_DELAY_MAX, etc.
    - _Requirements: 1.1, 2.1_

  - [x] 13.2 Ajouter des commentaires explicatifs dans le code
    - Documenter chaque fonction anti-ban
    - _Requirements: 1.4, 3.5, 5.4_

- [x] 14. Final checkpoint - Validation complète
  - Ensure all tests pass, ask the user if questions arise.
  - Vérifier les temps d'envoi avec un test de 10 messages
  - Confirmer que les délais sont bien appliqués

## Notes

- Toutes les tâches sont obligatoires pour une couverture de tests complète
- La logique Message 1/Message 2 dans `webhooks.py` n'est PAS modifiée
- Les changements sont rétrocompatibles (valeurs par défaut si env vars non définies)
- Le temps d'envoi sera significativement plus long (~8h pour 1000 messages vs ~1h42 avant)
- C'est un compromis nécessaire pour éviter les bannissements

## Fichiers à Modifier

1. `backend/app/tasks/message_tasks.py` - Fonctions anti-ban et délais
2. `backend/app/tasks/celery_app.py` - Configuration Celery
3. `backend/.env.example` - Variables d'environnement

## Fichiers NON Modifiés (préservation de la logique existante)

- `backend/app/routers/webhooks.py` - Logique Message 2 inchangée
- `backend/app/services/wassenger_service.py` - Service API inchangé
- `backend/app/routers/campaigns.py` - Routes API inchangées
- `frontend/*` - Aucun changement frontend

