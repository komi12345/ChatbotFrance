# Implementation Plan: Message Sending Optimization

## Overview

Optimisation de l'envoi de messages WhatsApp pour réduire le temps d'envoi de 1000 messages de ~1h42min à ~56min, tout en préservant la logique Message 1/Message 2 existante.

## Tasks

- [ ] 1. Ajouter la configuration optimisée et les variables d'environnement
  - Modifier les constantes dans `message_tasks.py`
  - Ajouter les variables d'environnement dans `.env.example`
  - Documenter les nouvelles configurations
  - _Requirements: 1.1, 2.1, 5.1_

- [ ] 2. Implémenter le système de délai adaptatif
  - [ ] 2.1 Créer la fonction `get_campaign_error_rate()` pour calculer le taux d'erreur depuis Redis
    - Utiliser les compteurs Redis `campaign:{id}:sent` et `campaign:{id}:failed`
    - _Requirements: 1.3_

  - [ ] 2.2 Créer la fonction `get_adaptive_delay()` pour calculer le délai adaptatif
    - Augmenter le délai de 50% si taux d'erreur > 5%
    - Respecter les limites MIN_DELAY et MAX_DELAY
    - _Requirements: 1.4_

  - [ ]* 2.3 Write property test for adaptive delay calculation
    - **Property 2: Adaptive Rate Limiting**
    - **Validates: Requirements 1.3, 1.4**

- [ ] 3. Implémenter le suivi de progression dans Redis
  - [ ] 3.1 Créer la fonction `update_campaign_progress()` pour mettre à jour les compteurs Redis
    - Incrémenter sent/failed après chaque message
    - Stocker le dernier message traité
    - _Requirements: 4.3_

  - [ ] 3.2 Modifier `send_single_message()` pour appeler `update_campaign_progress()`
    - Appeler après chaque envoi réussi ou échoué
    - _Requirements: 4.3, 6.3_

  - [ ]* 3.3 Write property test for progress tracking consistency
    - **Property 8: Progress Tracking Consistency**
    - **Validates: Requirements 4.3, 6.1**

- [ ] 4. Modifier `send_campaign_messages()` pour utiliser les nouveaux paramètres
  - [ ] 4.1 Utiliser les nouvelles constantes configurables (BATCH_SIZE, BATCH_PAUSE_SECONDS)
    - Lire depuis les variables d'environnement
    - _Requirements: 2.1, 2.2_

  - [ ] 4.2 Intégrer le délai adaptatif dans le calcul des délais
    - Appeler `get_adaptive_delay()` pour chaque lot
    - _Requirements: 1.3, 1.4_

  - [ ] 4.3 Améliorer le calcul du temps estimé de complétion
    - Utiliser la formule: `(N * D) + ((N / B) * P)`
    - _Requirements: 2.3, 6.4_

  - [ ]* 4.4 Write property test for completion time estimation
    - **Property 3: Completion Time Estimation**
    - **Validates: Requirements 2.3, 6.4**

- [ ] 5. Implémenter le circuit breaker
  - [ ] 5.1 Créer la fonction `check_circuit_breaker()` pour vérifier le seuil d'erreur
    - Activer si taux d'erreur > 20%
    - _Requirements: 4.1_

  - [ ] 5.2 Intégrer le circuit breaker dans `send_campaign_messages()`
    - Vérifier avant chaque lot
    - Mettre la campagne en pause si activé
    - _Requirements: 4.1_

- [ ] 6. Checkpoint - Vérifier que les optimisations fonctionnent
  - Ensure all tests pass, ask the user if questions arise.
  - Vérifier que la logique Message 1/Message 2 est préservée

- [ ]* 7. Write property tests for behavior preservation
  - [ ]* 7.1 Write property test for idempotency guarantee
    - **Property 6: Idempotency Guarantee**
    - **Validates: Requirements 3.5, 4.3**

  - [ ]* 7.2 Write property test for campaign resume after interruption
    - **Property 4: Campaign Resume After Interruption**
    - **Validates: Requirements 2.5, 3.5**

- [ ] 8. Mettre à jour la documentation
  - [ ] 8.1 Mettre à jour `.env.example` avec les nouvelles variables
    - WASSENGER_RATE_LIMIT_SECONDS, WASSENGER_BATCH_SIZE, WASSENGER_BATCH_PAUSE_SECONDS
    - _Requirements: 5.1_

  - [ ] 8.2 Mettre à jour la documentation technique
    - Documenter les nouveaux paramètres et leur impact
    - _Requirements: 5.4_

- [ ] 9. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
  - Vérifier les performances avec un test de 100 messages

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- La logique Message 1/Message 2 dans `webhooks.py` n'est PAS modifiée
- Les changements sont rétrocompatibles (valeurs par défaut si env vars non définies)
- Le circuit breaker est une sécurité supplémentaire, pas critique pour le MVP
