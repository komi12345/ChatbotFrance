# Implementation Plan: Performance Optimization

## Overview

Plan d'implémentation progressif et sécurisé pour l'optimisation des performances. Chaque étape est conçue pour être réversible et testée avant de passer à la suivante.

**Principe de sécurité** : Toutes les modifications sont additives (pas de suppression de code existant) et incluent des fallbacks en cas d'erreur.

## Tasks

- [x] 1. Créer le CacheService avec isolation des clés
  - [x] 1.1 Créer le fichier `backend/app/services/cache_service.py` avec la classe CacheService
    - Implémenter les méthodes get, set, delete avec gestion d'erreurs silencieuse
    - Ajouter la protection des clés existantes (whatsapp:*, campaign:*, celery*)
    - Utiliser la connexion Redis existante du MonitoringService
    - _Requirements: 3.1, 3.2, 3.4, 3.5, 3.6_

  - [x]* 1.2 Écrire les tests unitaires pour CacheService
    - Tester la génération des clés avec préfixe correct
    - Tester la protection des clés existantes
    - Tester le comportement en cas d'erreur Redis
    - _Requirements: 3.1, 3.5_

  - [x]* 1.3 Écrire le test property-based pour l'isolation des clés
    - **Property 1: Cache Key Isolation**
    - **Validates: Requirements 3.1, 3.5**

- [x] 2. Checkpoint - Valider le CacheService isolément
  - Exécuter les tests unitaires
  - Vérifier que le service démarre sans erreur
  - Vérifier que les clés existantes ne sont pas affectées

- [x] 3. Intégrer le cache dans l'endpoint /messages/stats
  - [x] 3.1 Ajouter la dépendance CacheService dans `backend/app/routers/messages.py`
    - Créer la fonction `get_cache_service()` dans cache_service.py
    - Modifier `get_global_stats()` pour utiliser le cache avec fallback DB
    - Garder le code existant comme fallback en cas d'erreur cache
    - _Requirements: 1.1, 1.5_

  - [x] 3.2 Écrire le test property-based pour le round-trip cache

    - **Property 2: Cache Round-Trip Consistency**
    - **Validates: Requirements 3.2**

- [x] 4. Checkpoint - Valider l'endpoint /messages/stats
  - Tester manuellement l'endpoint avec et sans cache
  - Vérifier les temps de réponse
  - Vérifier que le fallback DB fonctionne si Redis est lent

- [x] 5. Intégrer le cache dans l'endpoint /categories
  - [x] 5.1 Modifier `backend/app/routers/categories.py` pour utiliser le cache
    - Cacher la liste des catégories avec contact_count
    - Cacher les détails de catégorie individuelle
    - Garder le code existant comme fallback
    - _Requirements: 1.2_

  - [x] 5.2 Optimiser la requête de comptage contacts par catégorie
    - Utiliser une seule requête avec COUNT au lieu de boucle
    - _Requirements: 5.2_

- [x] 6. Checkpoint - Valider les endpoints catégories
  - Tester la liste des catégories
  - Tester le détail d'une catégorie
  - Vérifier que les comptages sont corrects

- [x] 7. Implémenter l'invalidation du cache après mutations
  - [x] 7.1 Ajouter l'invalidation dans `backend/app/routers/contacts.py`
    - Invalider cache stats après create/update/delete contact
    - Invalider cache catégories si contact associé à des catégories
    - _Requirements: 1.3, 4.1, 4.2_

  - [x] 7.2 Ajouter l'invalidation dans `backend/app/routers/categories.py`
    - Invalider cache catégories après create/update/delete catégorie
    - _Requirements: 1.4, 4.3_

  - [x] 7.3 Écrire le test property-based pour l'invalidation

    - **Property 4: Invalidation After Mutation**
    - **Validates: Requirements 1.3, 1.4, 4.1, 4.2, 4.3, 4.4**

- [x] 8. Checkpoint - Valider l'invalidation du cache
  - Créer un contact et vérifier que les stats se mettent à jour
  - Modifier une catégorie et vérifier la mise à jour
  - Supprimer un contact et vérifier les comptages

- [x] 9. Optimiser la configuration frontend TanStack Query
  - [x] 9.1 Mettre à jour `frontend/src/lib/query-client.ts`
    - Augmenter staleTime par défaut à 2 minutes
    - Configurer gcTime à 10 minutes
    - _Requirements: 2.3_

  - [x] 9.2 Mettre à jour `frontend/src/hooks/useStats.ts`
    - Augmenter staleTime à 5 minutes pour les stats
    - _Requirements: 2.2_

  - [x] 9.3 Mettre à jour `frontend/src/hooks/useContacts.ts` et `useCategories.ts`
    - Augmenter staleTime à 2 minutes
    - _Requirements: 2.3_

- [x] 10. Checkpoint - Valider la configuration frontend
  - Vérifier que les données ne sont pas refetch trop souvent
  - Vérifier que l'UI reste réactive

- [x] 11. Implémenter les mises à jour optimistes
  - [x] 11.1 Ajouter l'optimistic update dans `useCreateContact`
    - Mettre à jour le compteur de contacts immédiatement
    - Implémenter le rollback en cas d'erreur
    - _Requirements: 2.1_

  - [x] 11.2 Ajouter l'optimistic update dans `useCreateCategory`
    - Mettre à jour le compteur de catégories immédiatement
    - _Requirements: 2.1_

- [x] 12. Checkpoint - Valider les mises à jour optimistes
  - Créer un contact et vérifier la mise à jour immédiate des stats
  - Simuler une erreur et vérifier le rollback

- [x] 13. Ajouter l'endpoint de métriques cache (optionnel)
  - [x] 13.1 Créer l'endpoint `/api/cache/stats` dans un nouveau router
    - Retourner hits, misses, hit_rate
    - _Requirements: 6.1_

  - [x] 13.2 Écrire le test pour l'alerte de miss rate élevé


    - **Property 6: Cache Miss Rate Warning**
    - **Validates: Requirements 6.3**

- [x] 14. Implémenter la tâche de gestion des 24h sans interaction
  - [x] 14.1 Créer la tâche `check_expired_interactions` dans `celery_app.py`
    - Trouver les Message 1 envoyés il y a plus de 24h sans interaction
    - Marquer ces messages comme "no_interaction"
    - Incrémenter le compteur failed_count de la campagne
    - Logger chaque contact marqué
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.6_

  - [x] 14.2 Ajouter la tâche au beat_schedule (exécution toutes les heures)
    - Configurer la tâche périodique dans celery_app.py
    - _Requirements: 7.1_

  - [x] 14.3 Mettre à jour la logique de statut de campagne
    - Inclure "no_interaction" dans le calcul du statut "completed"
    - _Requirements: 7.5_

- [x] 15. Checkpoint - Valider la gestion des 24h
  - Vérifier que la tâche s'exécute correctement
  - Tester avec des messages de plus de 24h
  - Vérifier les statistiques de campagne

- [x] 16. Checkpoint final - Validation complète
  - Exécuter tous les tests backend
  - Exécuter tous les tests frontend
  - Tester le workflow complet : création contact → stats mises à jour
  - Tester le workflow 24h : Message 1 → pas d'interaction → marqué échec
  - Vérifier les logs pour absence d'erreurs

## Notes

- Les tâches marquées avec `*` sont optionnelles (tests property-based)
- Chaque checkpoint permet de valider avant de continuer
- En cas de problème, chaque modification peut être revertée indépendamment
- Le code existant est préservé comme fallback dans tous les cas
