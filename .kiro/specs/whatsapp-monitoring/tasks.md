# Implementation Plan

## Phase 1: Backend - MonitoringService et Redis

- [x] 1. Créer le service de monitoring backend





  - [x] 1.1 Créer `backend/app/services/monitoring_service.py` avec la classe MonitoringService


    - Initialisation avec connexion Redis (réutiliser `settings.REDIS_URL`)
    - Méthodes : `increment_message_counter()`, `increment_error_counter()`, `get_daily_stats()`
    - Clés Redis : `whatsapp:daily:{YYYY-MM-DD}:message_1`, `message_2`, `errors`
    - TTL de 48h sur les clés pour éviter l'accumulation
    - _Requirements: 1.1, 1.2, 1.5_

  - [x] 1.2 Write property test for counter increment consistency


    - **Property 1: Counter Increment Consistency**
    - **Validates: Requirements 1.1, 1.2**

  - [x] 1.3 Implémenter la méthode `can_send_message()` avec vérification limite 180


    - Retourne `(True, "")` si compteur < 180
    - Retourne `(False, "daily_limit_reached")` si compteur >= 180
    - Message d'erreur en français pour l'utilisateur
    - _Requirements: 2.1, 2.2, 2.3_


  - [x] 1.4 Write property test for daily limit blocking

    - **Property 2: Daily Limit Blocking**
    - **Validates: Requirements 2.2, 2.3**

  - [x] 1.5 Implémenter la méthode `get_alert_level()` avec les seuils


    - 0-135 (75%) → "ok" (vert)
    - 136-162 (90%) → "attention" (jaune)
    - 163-180 (100%) → "danger" (rouge)
    - >180 → "blocked" (gris)
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [x] 1.6 Write property test for alert level calculation


    - **Property 3: Alert Level Calculation**
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4**

  - [x] 1.7 Implémenter `calculate_remaining_capacity()` et `calculate_interaction_rate()`


    - Formule : `floor((180 - sent) / (1 + interaction_rate))`
    - Interaction rate : `message_2_count / message_1_count` (0 si message_1 = 0)
    - _Requirements: 5.1, 5.2_

  - [x] 1.8 Write property test for remaining capacity formula


    - **Property 4: Remaining Capacity Formula**
    - **Validates: Requirements 5.1**

- [x] 2. Checkpoint - Vérifier les tests backend





  - Ensure all tests pass, ask the user if questions arise.

## Phase 2: Intégration avec Celery Tasks

- [x] 3. Intégrer le monitoring dans les tâches d'envoi de messages





  - [x] 3.1 Modifier `send_single_message()` dans `message_tasks.py`


    - Appeler `monitoring_service.can_send_message()` avant l'envoi
    - Si bloqué, retourner erreur sans envoyer
    - Si succès, appeler `monitoring_service.increment_message_counter(message_type)`
    - Si erreur, appeler `monitoring_service.increment_error_counter()`
    - _Requirements: 1.1, 2.1, 2.2, 6.1_

  - [x] 3.2 Write property test for error rate alert


    - **Property 5: Error Rate Alert**
    - **Validates: Requirements 6.2**

  - [x] 3.3 Créer une instance globale `monitoring_service` dans `celery_app.py`


    - Réutiliser la même connexion Redis que Celery
    - _Requirements: 1.1_

## Phase 3: API Endpoints

- [x] 4. Créer le router de monitoring






  - [x] 4.1 Créer `backend/app/routers/monitoring.py` avec les endpoints

    - `GET /api/monitoring/stats` : Statistiques temps réel
    - `GET /api/monitoring/history?days=7` : Historique 7 jours
    - `GET /api/monitoring/errors?limit=10` : Dernières erreurs
    - Tous les endpoints nécessitent JWT authentication
    - _Requirements: 1.5, 4.1, 4.2, 4.3, 4.4, 6.3, 8.4_


  - [x] 4.2 Write property test for authentication required

    - **Property 8: Authentication Required**
    - **Validates: Requirements 8.4**


  - [x] 4.3 Enregistrer le router dans `main.py`

    - Ajouter `app.include_router(monitoring_router, prefix="/api")`
    - _Requirements: 8.4_

- [x] 5. Checkpoint - Vérifier l'API





  - Ensure all tests pass, ask the user if questions arise.

## Phase 4: Persistance Supabase

- [x] 6. Créer les tables Supabase et la synchronisation





  - [x] 6.1 Créer la migration SQL pour `daily_message_stats`


    - Table avec colonnes : id, date, message_1_count, message_2_count, error_count
    - Index sur date
    - _Requirements: 7.4_


  - [x] 6.2 Créer la migration SQL pour `message_errors`

    - Table avec colonnes : id, message_id, error_code, error_message, occurred_at
    - Index sur occurred_at
    - _Requirements: 6.4_

  - [x] 6.3 Implémenter `sync_to_supabase()` et `sync_from_supabase()` dans MonitoringService


    - Sync vers Supabase : upsert des compteurs actuels
    - Sync depuis Supabase : récupération au démarrage
    - _Requirements: 7.1, 7.2, 7.3_

  - [x] 6.4 Write property test for persistence round-trip


    - **Property 6: Persistence Round-Trip**
    - **Validates: Requirements 1.4, 7.4**

  - [x] 6.5 Ajouter les méthodes de persistance dans `supabase_client.py`


    - `get_daily_stats(date)`, `upsert_daily_stats(data)`, `get_daily_stats_history(days)`
    - `create_message_error(data)`, `get_recent_errors(limit)`
    - _Requirements: 6.4, 7.4_

  - [x] 6.6 Implémenter `reset_daily_counters()` avec persistance

    - Persister les stats du jour précédent avant reset
    - Reset des compteurs Redis à 0
    - _Requirements: 1.3, 1.4_

- [x] 7. Checkpoint - Vérifier la persistance





  - Ensure all tests pass, ask the user if questions arise.

## Phase 5: Frontend - Page Monitoring

- [x] 8. Créer le hook et les types TypeScript





  - [x] 8.1 Créer `frontend/src/hooks/useMonitoring.ts`


    - Hook React Query avec auto-refresh 10 secondes
    - Fonctions : `useMonitoringStats()`, `useMonitoringHistory()`, `useMonitoringErrors()`
    - _Requirements: 4.5_

  - [x] 8.2 Créer `frontend/src/types/monitoring.ts`


    - Types : MonitoringStats, DailyHistory, RecentError, AlertLevel
    - _Requirements: 4.1_

- [ ] 9. Créer les composants de monitoring
  - [ ] 9.1 Créer `frontend/src/components/monitoring/AlertBadge.tsx`
    - Badge coloré selon le niveau d'alerte (ok/attention/danger/blocked)
    - Réutilisable dans la navigation et la page
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [x] 9.2 Créer `frontend/src/components/monitoring/MessageGauge.tsx`





    - Jauge circulaire affichant messages envoyés / limite (180)
    - Couleur selon le niveau d'alerte
    - _Requirements: 4.1_

  - [x] 9.3 Créer `frontend/src/components/monitoring/CapacityCard.tsx`





    - Carte affichant la capacité restante
    - Avertissement si < 10 contacts
    - _Requirements: 5.1, 5.3, 5.4_

  - [x] 9.4 Créer `frontend/src/components/monitoring/ErrorsList.tsx`





    - Liste des 10 dernières erreurs avec timestamps
    - Alerte si taux d'erreur > 10%
    - _Requirements: 6.2, 6.3_

- [x] 10. Créer la page de monitoring

  - [x] 10.1 Créer `frontend/src/app/dashboard/monitoring/page.tsx`
    - Layout avec DashboardLayout existant
    - Intégration des composants : MessageGauge, CapacityCard, StatsCards, ErrorsList
    - Graphique historique 7 jours (réutiliser LineChart existant)
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 8.3_


  - [x] 10.2 Write property test for navigation badge threshold


    - **Property 7: Navigation Badge Threshold**
    - **Validates: Requirements 8.2**

- [x] 11. Intégrer dans la navigation






  - [x] 11.1 Modifier la navigation pour ajouter le lien Monitoring

    - Ajouter lien vers `/dashboard/monitoring` dans le menu
    - Afficher badge d'alerte si compteur > 135
    - _Requirements: 8.1, 8.2_

- [x] 12. Checkpoint - Vérifier le frontend





  - Ensure all tests pass, ask the user if questions arise.

## Phase 6: Tâches périodiques et finalisation

- [x] 13. Configurer les tâches périodiques Celery Beat





  - [x] 13.1 Ajouter tâche de sync horaire dans `celery_app.py`


    - Tâche `sync_monitoring_to_supabase` toutes les heures
    - _Requirements: 7.2_


  - [x] 13.2 Ajouter tâche de reset quotidien dans `celery_app.py`

    - Tâche `reset_daily_monitoring` à 00:00 UTC
    - _Requirements: 1.3, 2.5_

- [x] 14. Final Checkpoint - Vérifier l'intégration complète





  - Ensure all tests pass, ask the user if questions arise.
