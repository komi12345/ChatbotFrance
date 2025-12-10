# Plan d'Implémentation - Migration WhatsApp Meta Cloud API vers Gupshup 2025

## Vue d'Ensemble

Ce plan détaille les tâches d'implémentation pour migrer l'intégration WhatsApp de Meta Cloud API vers Gupshup API 2025. Les tâches sont organisées de manière incrémentale pour permettre une validation continue.

## Tâches

- [x] 1. Configuration Gupshup






- [x] 1.1 Mettre à jour config.py avec les variables Gupshup


  - Ajouter GUPSHUP_API_KEY, GUPSHUP_APP_NAME, GUPSHUP_PHONE_NUMBER, GUPSHUP_API_URL, GUPSHUP_CUSTOMER_ID
  - Conserver les anciennes variables Meta pour rétrocompatibilité
  - Ajouter validation des variables obligatoires au démarrage
  - _Exigences : 1.1, 1.2, 1.3, 1.4_


- [x] 1.2 Mettre à jour les fichiers .env

  - Mettre à jour backend/.env.example avec les nouvelles variables Gupshup
  - Documenter chaque variable avec des commentaires en français
  - _Exigences : 1.5_

- [x] 2. Service Gupshup








- [x] 2.1 Créer le service gupshup_service.py


  - Créer backend/app/services/gupshup_service.py
  - Implémenter les dataclasses GupshupResponse et GupshupWebhookInteraction
  - Implémenter la classe GupshupService avec les propriétés (template_url, message_url, headers)
  - Implémenter la méthode format_phone_number (retirer le +)
  - _Exigences : 2.3, 8.1_

- [x] 2.2 Écrire le test property pour le formatage des numéros






  - **Property 1: Formatage des numéros de téléphone**
  - **Valide : Exigences 2.3, 7.2**
  - Utiliser Hypothesis pour générer des numéros avec +
  - Vérifier que le résultat ne commence jamais par +


- [x] 2.3 Implémenter send_template_message

  - Construire le payload x-www-form-urlencoded avec channel, source, destination, template, src.name
  - Encoder les paramètres du template en JSON
  - Appeler l'endpoint POST /template/msg
  - Parser la réponse et retourner GupshupResponse
  - _Exigences : 2.1, 2.2, 2.4, 2.5, 2.6_

- [ ]* 2.4 Écrire les tests property pour les requêtes template
  - **Property 2: Format des requêtes template**
  - **Valide : Exigences 2.2**
  - **Property 3: Encodage JSON des paramètres template**
  - **Valide : Exigences 2.4**
  - Vérifier que tous les champs obligatoires sont présents
  - Vérifier que le JSON des paramètres est valide



- [x] 2.5 Implémenter send_text_message
  - Construire le payload x-www-form-urlencoded avec channel, source, destination, message, src.name
  - Appeler l'endpoint POST /msg
  - Parser la réponse et retourner GupshupResponse
  - _Exigences : 3.1, 3.2, 3.3, 3.5, 3.6_

- [ ]* 2.6 Écrire les tests property pour les requêtes message
  - **Property 4: Format des requêtes message texte**
  - **Valide : Exigences 3.2**
  - **Property 5: Encodage des caractères spéciaux**
  - **Valide : Exigences 3.4**
  - Vérifier que tous les champs obligatoires sont présents

  - Vérifier que les caractères spéciaux sont préservés


- [x] 2.7 Implémenter _send_request avec gestion d'erreurs
  - Utiliser httpx pour les requêtes async
  - Gérer les timeouts (30 secondes)
  - Parser les réponses success/error de Gupshup
  - Logger toutes les requêtes et erreurs
  - _Exigences : 2.5, 2.6, 3.5, 3.6_

- [x] 2.8 Mettre à jour services/__init__.py

  - Exporter gupshup_service depuis le module services
  - _Exigences : 8.2_

- [x] 3. Checkpoint - Vérifier le service Gupshup








  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Webhooks Gupshup









- [x] 4.1 Implémenter parse_webhook_payload dans gupshup_service.py

  - Parser les webhooks de type "message" (mobile, text, messageId, timestamp, name)
  - Parser les webhooks de type "message-event" (eventType, externalId, messageId)
  - Retourner une liste de GupshupWebhookInteraction
  - _Exigences : 4.1, 5.1_

- [x] 4.2 Écrire les tests property pour le parsing des webhooks






  - **Property 6: Parsing des webhooks message**
  - **Valide : Exigences 4.1**
  - **Property 7: Parsing des webhooks message-event**
  - **Valide : Exigences 5.1**
  - Générer des payloads webhook valides et vérifier l'extraction des champs


- [x] 4.3 Créer l'endpoint POST /webhooks/gupshup

  - Ajouter la route dans routers/webhooks.py
  - Parser le payload JSON
  - Détecter le type de webhook (message vs message-event)
  - Traiter en arrière-plan avec BackgroundTasks
  - Retourner 200 OK immédiatement
  - _Exigences : 4.6, 8.5_

- [x] 4.4 Écrire le test property pour le temps de réponse webhook






  - **Property 8: Temps de réponse webhook**
  - **Valide : Exigences 4.6**
  - Mesurer le temps de réponse et vérifier < 20 secondes


- [x] 4.5 Implémenter process_gupshup_message





  - Extraire le numéro mobile et ajouter le + pour la recherche en DB
  - Rechercher le contact dans la base de données
  - Vérifier si un Message 1 récent existe
  - Vérifier si le Message 2 doit être envoyé
  - Créer une tâche Celery pour l'envoi du Message 2
  - Enregistrer l'interaction dans la table interactions
  - _Exigences : 4.2, 4.3, 4.4, 4.5_


- [x] 4.6 Implémenter process_gupshup_status





  - Extraire le eventType (delivered, read, failed)
  - Rechercher le message par externalId ou messageId
  - Mettre à jour le statut du message avec horodatage
  - Incrémenter les compteurs de la campagne
  - _Exigences : 5.2, 5.3, 5.4, 5.5, 5.6_

- [x] 5. Checkpoint - Vérifier les webhooks





  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Adaptation des tâches Celery







- [x] 6.1 Mettre à jour message_tasks.py pour utiliser gupshup_service

  - Remplacer l'import whatsapp_service par gupshup_service
  - Adapter send_campaign_messages_task pour utiliser gupshup_service.send_template_message
  - Adapter send_single_message_task pour utiliser gupshup_service.send_text_message
  - Stocker le gupshup_message_id dans le champ whatsapp_message_id
  - _Exigences : 6.1, 6.5_

- [x] 6.2 Écrire le test property pour le rate limiting






  - **Property 9: Respect du rate limiting**
  - **Valide : Exigences 6.2**
  - Simuler un envoi massif et vérifier que le taux ne dépasse pas 25/min


- [x] 6.3 Adapter retry_failed_message_task

  - Utiliser gupshup_service pour les retries
  - Implémenter le délai exponentiel (60s, 120s, 240s)
  - Marquer comme échoué après 3 tentatives
  - _Exigences : 6.3, 6.4_

- [x] 6.4 Écrire le test property pour le délai de retry






  - **Property 10: Calcul du délai de retry exponentiel**
  - **Valide : Exigences 6.3**
  - Vérifier que délai = 60 × 2^(tentative-1) pour tentatives 1, 2, 3

- [x] 7. Adaptation des routes campagnes






- [x] 7.1 Mettre à jour routers/campaigns.py


  - Remplacer l'import whatsapp_service par gupshup_service (si utilisé directement)
  - Vérifier que les appels passent par les tâches Celery
  - _Exigences : 7.1, 7.4_


- [x] 7.2 Vérifier la cohérence des statistiques

  - S'assurer que les formules de calcul restent identiques
  - Vérifier que les compteurs sont mis à jour correctement
  - _Exigences : 7.5_

- [x] 7.3 Écrire les tests property pour la cohérence






  - **Property 11: Cohérence des formats de réponse API**
  - **Valide : Exigences 8.5**
  - **Property 12: Cohérence du calcul des statistiques**
  - **Valide : Exigences 7.5**
  - Comparer les formats de réponse avant/après migration
  - Vérifier que les statistiques sont calculées de la même manière

- [ ] 8. Checkpoint - Vérifier l'intégration complète
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Documentation







- [x] 9.1 Créer le guide de migration docs/MIGRATION-GUPSHUP.md

  - Documenter les étapes de migration
  - Expliquer les différences Meta vs Gupshup
  - Fournir les instructions de configuration webhook
  - Expliquer comment créer des templates sur Gupshup Dashboard
  - Lister les erreurs communes et solutions
  - _Exigences : 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ] 10. Tests d'intégration finaux

- [ ] 10.1 Créer le fichier de tests backend/tests/test_gupshup_integration.py
  - Test d'envoi de template (mock ou sandbox)
  - Test d'envoi de message texte
  - Test de réception webhook message (simulé)
  - Test de réception webhook message-event (simulé)
  - Test de formatage des numéros
  - _Exigences : 10.1, 10.2, 10.3, 10.4, 10.5_

- [x] 11. Nettoyage et finalisation

- [x] 11.1 Archiver l'ancien service whatsapp_service.py
  - Renommer en whatsapp_service.py.bak ou déplacer dans un dossier archive
  - Supprimer les imports inutilisés
  - _Exigences : 8.1_

- [x] 11.2 Vérifier tous les imports dans le projet


  - S'assurer qu'aucun fichier n'importe encore whatsapp_service
  - Vérifier que gupshup_service est correctement importé partout
  - _Exigences : 8.2_

- [x] 12. Checkpoint Final





  - Ensure all tests pass, ask the user if questions arise.
  - Vérifier que toutes les fonctionnalités sont opérationnelles
  - Tester le flux complet : Campagne → Envoi → Webhook → Message 2
  - Vérifier les statistiques et le dashboard
