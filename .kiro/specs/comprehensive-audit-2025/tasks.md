# Implementation Plan: Comprehensive Audit 2025

## Overview

Plan d'audit et d'optimisation complet de la plateforme WhatsApp. L'audit est divisé en phases progressives, chaque phase validant un aspect spécifique du système avant de passer à la suivante.

**Principe** : Auditer d'abord, optimiser ensuite. Chaque modification est testée avant d'être appliquée.

**Note** : Toutes les fonctionnalités s'appliquent de manière identique pour Admin et Super Admin.

## Tasks

- [x] 1. Phase 1 - Audit de Performance Frontend
  - [x] 1.1 Mesurer les métriques Lighthouse actuelles (TTI, FCP, LCP)
    - Exécuter Lighthouse sur toutes les pages principales
    - Documenter les scores actuels dans un rapport
    - Identifier les pages les plus lentes
    - _Requirements: 1.1, 1.2, 1.3_

  - [x] 1.2 Analyser la taille du bundle JavaScript
    - Utiliser Webpack Bundle Analyzer
    - Identifier les dépendances les plus lourdes
    - Documenter la taille actuelle vs objectif (< 200KB)
    - _Requirements: 1.4_

  - [x] 1.3 Auditer la configuration TanStack Query
    - Vérifier les valeurs staleTime et gcTime actuelles
    - Identifier les requêtes qui refetch trop souvent
    - Vérifier l'utilisation des optimistic updates
    - _Requirements: 2.2, 2.3, 3.1, 3.2_

- [x] 2. Checkpoint - Rapport d'audit frontend
  - Compiler les métriques mesurées
  - Lister les optimisations prioritaires
  - Valider avec l'utilisateur avant d'appliquer les changements

- [x] 3. Phase 2 - Audit de Performance Backend
  - [x] 3.1 Mesurer les temps de réponse des endpoints API
    - Tester GET /messages/stats, /categories, /contacts
    - Tester POST /contacts, /campaigns/start
    - Documenter les temps actuels vs objectifs
    - _Requirements: 2.1, 2.2_

  - [x] 3.2 Auditer l'utilisation du cache Redis
    - Vérifier le hit rate actuel
    - Identifier les endpoints sans cache
    - Vérifier la séparation des clés cache vs Celery
    - _Requirements: 2.3, 2.4_

  - [x] 3.3 Analyser les requêtes SQL lentes
    - Utiliser les logs Supabase pour identifier les requêtes > 30ms
    - Vérifier les index existants
    - Identifier les N+1 queries potentielles
    - _Requirements: 2.1, 2.2_

- [x] 4. Checkpoint - Rapport d'audit backend
  - Compiler les métriques mesurées
  - Lister les optimisations prioritaires
  - Valider avec l'utilisateur avant d'appliquer les changements

- [x] 5. Phase 3 - Audit de la Logique Message 1
  - [x] 5.1 Vérifier l'envoi de Message 1 à tous les contacts
    - Analyser le code de lancement de campagne
    - Vérifier que tous les contacts reçoivent le Message 1
    - Vérifier l'enregistrement du timestamp sent_at
    - _Requirements: 4.1, 4.2_

  - [x] 5.2 Vérifier le rate limiting
    - Analyser la configuration du rate limiting
    - Vérifier le respect de la limite de 1000 msg/jour
    - Tester le comportement quand la limite est atteinte
    - _Requirements: 4.4_

  - [x] 5.3 Vérifier la logique de retry
    - Analyser le code de retry avec backoff exponentiel
    - Vérifier le nombre max de retries (3)
    - Tester le comportement en cas d'échec
    - _Requirements: 4.6_

  - [x] 5.4 Écrire le test property-based pour Message 1 Completeness
    - **Property 4: Message 1 Completeness**
    - **Validates: Requirements 4.1, 4.2**

- [x] 6. Checkpoint - Validation logique Message 1
  - Vérifier que tous les tests passent
  - Documenter les problèmes identifiés
  - Corriger les bugs si nécessaire

- [x] 7. Phase 4 - Audit de la Logique Message 2 (24h)
  - [x] 7.1 Vérifier la détection d'interaction dans les 24h
    - Analyser le code du webhook handler
    - Vérifier le calcul de la fenêtre 24h
    - Tester avec des timestamps limites (23h59, 24h01)
    - _Requirements: 5.1, 5.2, 5.3_

  - [x] 7.2 Vérifier la détection de tous les types d'interaction
    - Analyser le code de parsing des webhooks
    - Vérifier que texte, emoji, vocal, audio, image, vidéo, document sont détectés
    - Tester chaque type d'interaction
    - _Requirements: 5.4_

  - [x] 7.3 Vérifier le temps de réponse Message 2
    - Mesurer le temps entre webhook et création Message 2
    - Vérifier que c'est < 5 secondes
    - Identifier les goulots d'étranglement
    - _Requirements: 5.5_

  - [x] 7.4 Vérifier l'enregistrement des interactions
    - Vérifier que chaque interaction est enregistrée en BDD
    - Vérifier les champs campaign_id, contact_id, interaction_type
    - _Requirements: 5.6_

  - [x] 7.5 Écrire le test property-based pour 24h Window Enforcement
    - **Property 6: 24h Window Enforcement**
    - **Validates: Requirements 5.1, 5.2, 5.3**

- [x] 8. Checkpoint - Validation logique Message 2
  - Vérifier que tous les tests passent
  - Documenter les problèmes identifiés
  - Corriger les bugs si nécessaire

- [x] 9. Phase 5 - Audit de la Prévention des Doublons
  - [x] 9.1 Vérifier le verrou distribué Redis
    - Analyser le code d'acquisition du verrou
    - Vérifier le TTL du verrou (5 min recommandé)
    - Tester les race conditions
    - _Requirements: 6.1, 6.3_

  - [x] 9.2 Vérifier l'idempotence Message 2
    - Analyser le code de vérification de Message 2 existant
    - Tester avec plusieurs interactions simultanées
    - Vérifier qu'un seul Message 2 est créé
    - _Requirements: 6.2, 6.4_

  - [x] 9.3 Écrire le test property-based pour Message 2 Idempotence
    - **Property 10: Message 2 Idempotence**
    - **Validates: Requirements 6.4**

- [x] 10. Checkpoint - Validation prévention doublons
  - Vérifier que tous les tests passent
  - Documenter les problèmes identifiés
  - Corriger les bugs si nécessaire

- [x] 11. Phase 6 - Audit de la Clôture Automatique
  - [x] 11.1 Vérifier la tâche périodique de timeout 24h
    - Analyser le code de check_expired_interactions
    - Vérifier la fréquence d'exécution (toutes les heures)
    - Vérifier le marquage des contacts sans interaction
    - _Requirements: 7.1, 7.2, 7.4_

  - [x] 11.2 Vérifier la logique de clôture de campagne
    - Analyser le code de détection des états finaux
    - Vérifier que tous les états sont considérés
    - Tester la clôture automatique
    - _Requirements: 7.1, 7.2_

  - [x] 11.3 Vérifier le calcul des statistiques finales
    - Analyser le code de calcul des stats
    - Vérifier que toutes les métriques sont calculées
    - Tester avec différents scénarios de campagne
    - _Requirements: 7.3, 9.5_

  - [x] 11.4 Vérifier le timeout de sécurité 48h
    - Analyser le code de timeout maximum
    - Vérifier que les campagnes > 48h sont clôturées
    - _Requirements: 7.5_

  - [x] 11.5 Écrire le test property-based pour Campaign Completion
    - **Property 11: Campaign Completion Logic**
    - **Validates: Requirements 7.1, 7.2**

- [x] 12. Checkpoint - Validation clôture automatique
  - Vérifier que tous les tests passent
  - Documenter les problèmes identifiés
  - Corriger les bugs si nécessaire

- [x] 13. Phase 7 - Audit des Workers Celery
  - [x] 13.1 Vérifier la configuration des workers
    - Analyser la configuration Celery
    - Vérifier le nombre de workers et la concurrency
    - Vérifier le heartbeat et la supervision
    - _Requirements: 8.4, 8.5_

  - [x] 13.2 Vérifier le fonctionnement autonome
    - Tester l'envoi de messages sans admin connecté
    - Tester le traitement des webhooks sans admin connecté
    - Vérifier les logs pour confirmer le fonctionnement
    - _Requirements: 8.1, 8.2, 8.3_

- [x] 14. Checkpoint - Validation workers Celery
  - Vérifier que les workers fonctionnent correctement
  - Documenter les problèmes identifiés
  - Corriger les bugs si nécessaire

- [x] 15. Phase 8 - Audit des Statistiques
  - [x] 15.1 Vérifier le temps d'affichage des statistiques
    - Mesurer le temps de réponse de /messages/stats
    - Vérifier l'utilisation du cache
    - Tester avec des campagnes de différentes tailles
    - _Requirements: 9.1, 3.5_

  - [x] 15.2 Vérifier le contenu des statistiques
    - Vérifier que tous les champs requis sont présents
    - Tester la cohérence des données
    - _Requirements: 9.2_

  - [x] 15.3 Vérifier la latence de mise à jour
    - Mesurer le temps entre envoi de message et mise à jour des stats
    - Vérifier que c'est < 5 secondes
    - _Requirements: 9.3_

  - [x] 15.4 Écrire le test property-based pour Stats Content
    - **Property 14: Stats Content Completeness**
    - **Validates: Requirements 9.2**

- [x] 16. Checkpoint - Validation statistiques
  - Vérifier que tous les tests passent
  - Documenter les problèmes identifiés
  - Corriger les bugs si nécessaire

- [x] 17. Phase 9 - Nettoyage du Code
  - [x] 17.1 Supprimer le code mort et les imports inutilisés
    - Analyser le code backend avec des outils de linting
    - Analyser le code frontend avec ESLint
    - Supprimer le code non utilisé
    - _Requirements: 10.1, 10.2_

  - [x] 17.2 Supprimer les console.log/print de debug
    - Rechercher les console.log dans le frontend
    - Rechercher les print dans le backend
    - Supprimer ou remplacer par des logs appropriés
    - _Requirements: 10.3_

  - [x] 17.3 Vérifier les conventions de style
    - Exécuter flake8/black sur le backend
    - Exécuter ESLint/Prettier sur le frontend
    - Corriger les violations de style
    - _Requirements: 10.6_

- [x] 18. Checkpoint - Validation nettoyage
  - Vérifier que le linting passe sans erreurs
  - Vérifier que tous les tests passent toujours
  - Documenter les changements effectués

- [x] 19. Phase 10 - Optimisations (si nécessaire)
  - [x] 19.1 Appliquer les optimisations frontend identifiées
    - Optimiser la configuration TanStack Query si nécessaire
    - Ajouter les optimistic updates manquants
    - Réduire la taille du bundle si > 200KB
    - _Requirements: 1.4, 2.2, 2.3, 3.1, 3.2_

  - [x] 19.2 Appliquer les optimisations backend identifiées
    - Ajouter du cache sur les endpoints lents
    - Optimiser les requêtes SQL lentes
    - Ajouter des index si nécessaire
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 19.3 Corriger les bugs identifiés dans la logique métier
    - Corriger les problèmes de logique Message 1/Message 2
    - Corriger les problèmes de clôture de campagne
    - Corriger les problèmes de statistiques
    - _Requirements: 4.1-4.6, 5.1-5.6, 6.1-6.5, 7.1-7.6_

- [x] 20. Checkpoint final - Validation complète
  - Exécuter tous les tests backend (pytest)
  - Exécuter tous les tests frontend (vitest)
  - Mesurer les métriques de performance finales
  - Comparer avec les métriques initiales
  - Documenter les améliorations obtenues

- [x] 21. Livraison - Rapport d'audit final
  - [x] 21.1 Créer le rapport d'audit complet
    - Métriques AVANT/APRÈS
    - Liste des problèmes identifiés et corrigés
    - Recommandations pour le futur
    - _Requirements: Tous_

## Notes

- Toutes les tâches sont obligatoires, y compris les tests property-based
- Chaque checkpoint permet de valider avant de continuer
- L'audit est non-destructif : on mesure d'abord, on optimise ensuite
- Toutes les modifications sont réversibles
- Les fonctionnalités s'appliquent de manière identique pour Admin et Super Admin

