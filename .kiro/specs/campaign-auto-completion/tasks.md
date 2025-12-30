# Implementation Plan: Campaign Auto-Completion

## Overview

Ce plan implémente la correction de l'auto-terminaison des campagnes en ajoutant une vérification du statut après chaque envoi de Message 2 et une tâche périodique de vérification.

## Tasks

- [x] 1. Modifier send_single_message pour déclencher la vérification après Message 2
  - [x] 1.1 Ajouter la détection du message_type="message_2" après envoi réussi
    - Après `update_campaign_statistics()`, vérifier si c'est un Message 2
    - Déclencher `update_campaign_status.apply_async()` avec countdown=5
    - _Requirements: 1.1, 3.4_

- [x] 2. Créer la tâche périodique check_sending_campaigns
  - [x] 2.1 Ajouter la tâche dans celery_app.py
    - Récupérer toutes les campagnes en statut "sending"
    - Pour chaque campagne, appeler `update_campaign_status.delay()`
    - _Requirements: 2.1, 2.2_
  
  - [x] 2.2 Configurer Celery Beat pour exécuter la tâche toutes les 2 minutes
    - Ajouter l'entrée dans `celery_app.conf.beat_schedule`
    - _Requirements: 2.1_

- [x] 3. Améliorer la logique de update_campaign_status
  - [x] 3.1 Simplifier la condition de complétion
    - Compter message_1_sent, message_2_sent, no_interaction, failed
    - Campagne complète si: pending=0 ET (msg2_sent + no_interaction + failed) >= msg1_sent
    - _Requirements: 1.2, 2.3_
  
  - [x] 3.2 S'assurer que completed_at est toujours défini lors de la complétion
    - Vérifier que le timestamp est défini quand status passe à "completed"
    - _Requirements: 1.3_

- [x] 4. Checkpoint - Tester manuellement
  - Créer une campagne de test avec 2-3 contacts
  - Envoyer Message 1, simuler une interaction, vérifier que Message 2 est envoyé
  - Vérifier que la campagne passe en "completed" automatiquement
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 5. Écrire les tests property-based
  - [x] 5.1 Test Property 1 & 2: Campaign completion logic
    - **Property 1: Campaign Completion When All Contacts Finished**
    - **Property 2: Pending Messages Prevent Completion**
    - **Validates: Requirements 1.2, 1.4, 2.2**
  
  - [x] 5.2 Test Property 3: Completed timestamp
    - **Property 3: Completed Timestamp Set On Completion**
    - **Validates: Requirements 1.3**

- [x] 6. Final checkpoint
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Toutes les tâches sont obligatoires
- La tâche périodique est un filet de sécurité en cas de webhook manqué
- Le délai de 5 secondes avant la vérification permet à la BDD de se synchroniser
