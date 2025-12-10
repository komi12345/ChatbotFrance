# Plan d'Implémentation - Migration Gupshup vers Twilio WhatsApp Sandbox 2025

- [x] 1. Configuration et dépendances Twilio
  - [x] 1.1 Ajouter la bibliothèque twilio au requirements.txt
    - Ajouter `twilio>=9.0.0` au fichier requirements.txt
    - _Requirements: 2.1_
  - [x] 1.2 Mettre à jour config.py avec les variables Twilio

    - Ajouter TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_SANDBOX_NUMBER
    - Supprimer les variables GUPSHUP_* obsolètes
    - Implémenter validate_twilio_config()
    - _Requirements: 1.1, 1.2, 1.4, 8.3_
  - [x] 1.3 Mettre à jour les fichiers .env et .env.example



    - Ajouter les nouvelles variables Twilio avec commentaires en français
    - Retirer les variables Gupshup
    - _Requirements: 1.5_

- [x] 2. Créer le service Twilio



  - [x] 2.1 Créer le fichier twilio_service.py avec les classes de base


    - Créer TwilioResponse et TwilioWebhookInteraction dataclasses
    - Créer la classe TwilioService avec initialisation du client
    - _Requirements: 1.4, 2.1_
  - [ ]* 2.2 Écrire le test property pour le formatage des numéros
    - **Property 1: Formatage des numéros WhatsApp**
    - **Validates: Requirements 2.2**

  - [x] 2.3 Implémenter format_whatsapp_number et extract_phone_from_whatsapp
    - Formater au format whatsapp:+XXXXXXXXXXX
    - Extraire le numéro sans le préfixe whatsapp:
    - _Requirements: 2.2_
  - [ ]* 2.4 Écrire le test property pour le numéro source Sandbox
    - **Property 2: Numéro source Sandbox constant**

    - **Validates: Requirements 2.3**
  - [x] 2.5 Implémenter send_message avec gestion des erreurs

    - Utiliser client.messages.create()
    - Retourner TwilioResponse avec success/error
    - _Requirements: 2.3, 2.4, 2.5, 2.6_
  - [ ]* 2.6 Écrire le test property pour la gestion des erreurs
    - **Property 3: Gestion des erreurs Twilio**
    - **Validates: Requirements 2.5**

- [x] 3. Implémenter l'envoi de templates





  - [x] 3.1 Implémenter send_template_message


    - Utiliser Content SID pour les templates pré-approuvés
    - Encoder ContentVariables en JSON
    - _Requirements: 3.1, 3.2, 3.3_
  - [ ]* 3.2 Écrire le test property pour l'encodage JSON des paramètres
    - **Property 4: Encodage JSON des paramètres template**
    - **Validates: Requirements 3.2**
  - [ ]* 3.3 Écrire le test property pour la validation des paramètres
    - **Property 5: Validation des paramètres template**
    - **Validates: Requirements 3.4**

  - [x] 3.4 Implémenter la validation des paramètres template

    - Vérifier que tous les paramètres requis sont fournis
    - _Requirements: 3.4, 3.5_

- [x] 4. Checkpoint - Vérifier les tests du service Twilio








  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implémenter les webhooks Twilio





  - [x] 5.1 Implémenter validate_webhook_signature

    - Utiliser RequestValidator de Twilio
    - _Requirements: 4.1_
  - [ ]* 5.2 Écrire le test property pour la validation de signature
    - **Property 6: Validation de signature webhook**
    - **Validates: Requirements 4.1**

  - [x] 5.3 Implémenter parse_webhook_payload pour les messages entrants
    - Extraire From, Body, MessageSid
    - Créer TwilioWebhookInteraction
    - _Requirements: 4.2, 4.3_
  - [ ]* 5.4 Écrire le test property pour l'extraction des champs webhook
    - **Property 7: Extraction des champs webhook message**

    - **Validates: Requirements 4.2**
  - [x] 5.5 Implémenter parse_webhook_payload pour les statuts de livraison
    - Extraire MessageStatus (queued, sent, delivered, read, failed)
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_
  - [ ]* 5.6 Écrire le test property pour l'extraction du MessageStatus
    - **Property 9: Extraction du MessageStatus**
    - **Validates: Requirements 5.1**
  - [ ]* 5.7 Écrire le test property pour la gestion des erreurs de livraison
    - **Property 10: Gestion des erreurs de livraison**
    - **Validates: Requirements 5.4**

- [x] 6. Modifier le router webhooks.py





  - [x] 6.1 Créer l'endpoint POST /api/webhooks/twilio


    - Valider la signature Twilio
    - Parser le payload
    - Retourner TwiML vide
    - _Requirements: 4.1, 4.6_
  - [ ]* 6.2 Écrire le test property pour la réponse TwiML
    - **Property 8: Réponse webhook TwiML**
    - **Validates: Requirements 4.6**

  - [x] 6.3 Implémenter process_twilio_message pour les messages entrants
    - Rechercher le contact correspondant
    - Vérifier si Message 2 doit être envoyé
    - Créer tâche Celery si nécessaire

    - _Requirements: 4.3, 4.4, 4.5_
  - [x] 6.4 Implémenter process_twilio_status pour les statuts
    - Mettre à jour le statut du message
    - Incrémenter les compteurs de campagne
    - _Requirements: 5.2, 5.3, 5.4, 5.5, 5.6_
  - [x] 6.5 Supprimer l'ancien endpoint webhook Gupshup


    - _Requirements: 8.5_

- [x] 7. Checkpoint - Vérifier les tests des webhooks





  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Adapter les tâches Celery





  - [x] 8.1 Modifier message_tasks.py pour utiliser twilio_service


    - Remplacer import gupshup_service par twilio_service
    - Adapter les appels de fonction
    - _Requirements: 6.1_

  - [x] 8.2 Implémenter le rate limiting Sandbox (1 msg/3s)

    - Ajouter délai de 3 secondes entre les envois
    - _Requirements: 6.2, 7.2_
  - [ ]* 8.3 Écrire le test property pour le rate limiting
    - **Property 11: Respect du rate limiting Sandbox**
    - **Validates: Requirements 6.2**


  - [x] 8.4 Implémenter le retry avec délai exponentiel
    - Formule: délai = 60 × 2^(tentative-1) secondes
    - Maximum 3 tentatives
    - _Requirements: 6.3, 6.4_
  - [-]* 8.5 Écrire le test property pour le calcul du délai de retry

    - **Property 12: Calcul du délai de retry exponentiel**
    - **Validates: Requirements 6.3**
  - [x] 8.6 Stocker le twilio_message_sid dans whatsapp_message_id

    - _Requirements: 6.5_

  - [x] 8.7 Mettre à jour les statistiques de campagne

    - _Requirements: 6.6_

- [x] 9. Gestion des limitations Sandbox





  - [x] 9.1 Implémenter la détection de l'erreur 63007 (non-inscrit)


    - Retourner message explicite avec instructions de join
    - _Requirements: 7.1, 7.5_
  - [ ]* 9.2 Écrire le test property pour l'erreur Sandbox non-inscrit
    - **Property 13: Gestion de l'erreur Sandbox non-inscrit**
    - **Validates: Requirements 7.1, 7.5**

  - [x] 9.3 Implémenter la gestion de l'expiration de session (24h)

    - _Requirements: 7.3_

- [x] 10. Checkpoint - Vérifier les tests des tâches Celery





  - Ensure all tests pass, ask the user if questions arise.

- [x] 11. Suppression de l'intégration Gupshup






  - [x] 11.1 Archiver gupshup_service.py

    - Déplacer vers backend/app/services/archive/
    - _Requirements: 8.1_
  - [x] 11.2 Mettre à jour les imports dans tous les fichiers


    - Remplacer gupshup_service par twilio_service
    - _Requirements: 8.2_

  - [x] 11.3 Supprimer les fichiers de test Gupshup

    - Supprimer test_gupshup_*.py
    - _Requirements: 8.4_

  - [x] 11.4 Nettoyer les références Gupshup dans la documentation

    - _Requirements: 8.3_

- [x] 12. Modifications Frontend - Interface Sandbox





  - [x] 12.1 Créer le composant SandboxInfoBanner


    - Afficher les informations du mode Sandbox
    - Montrer le numéro Sandbox et le code de join
    - _Requirements: 9.1, 9.2_

  - [x] 12.2 Ajouter les indicateurs de contacts inscrits au Sandbox

    - Afficher un badge pour les contacts inscrits
    - Afficher un avertissement pour les contacts non inscrits
    - _Requirements: 9.3, 9.4_

  - [x] 12.3 Afficher les messages d'erreur explicatifs

    - Afficher les instructions de join en cas d'échec
    - Afficher les limitations (1 msg/3s, session 24h)
    - _Requirements: 9.4, 9.5_

- [ ] 13. Créer les tests d'intégration Twilio
  - [ ] 13.1 Créer test_twilio_connection.py
    - Valider la connexion avec les credentials
    - _Requirements: 12.1_
  - [ ] 13.2 Créer test_twilio_send.py
    - Valider le format de la requête d'envoi
    - _Requirements: 12.2_
  - [ ] 13.3 Créer test_twilio_webhook.py
    - Valider le parsing des webhooks entrants et statuts
    - _Requirements: 12.3, 12.4_
  - [ ] 13.4 Créer test_twilio_signature.py
    - Vérifier la validation de signature
    - _Requirements: 12.5_

- [ ] 14. Checkpoint - Vérifier tous les tests
  - Ensure all tests pass, ask the user if questions arise.

- [x] 15. Documentation - Configuration Twilio
  - [x] 15.1 Créer Configuration_Twilio_WhatsApp_Sandbox_2025.md
    - Introduction au Twilio WhatsApp Sandbox
    - Guide de création de compte Twilio
    - Navigation dans le dashboard Twilio 2025
    - _Requirements: 10.1_
  - [x] 15.2 Documenter la récupération des credentials
    - Account SID, Auth Token, Sandbox Number
    - Captures d'écran et emplacements exacts
    - _Requirements: 10.2_
  - [x] 15.3 Documenter la configuration du Sandbox
    - Activation, code de join, test d'adhésion
    - Gestion de plusieurs utilisateurs de test
    - _Requirements: 10.3_
  - [x] 15.4 Documenter la configuration des webhooks
    - URLs webhook, ngrok, vérification
    - _Requirements: 10.4_
  - [x] 15.5 Documenter les templates et limitations
    - Templates pré-approuvés, restrictions Sandbox
    - _Requirements: 10.5_
  - [x] 15.6 Ajouter la section troubleshooting
    - Erreurs courantes (63007, 21608, etc.)
    - Solutions et bonnes pratiques
    - _Requirements: 10.5_

- [x] 16. Documentation - Guide de lancement local






  - [x] 16.1 Créer Guide_Configuration_Projet_Local_2025.md

    - Prérequis système (Python, Node.js, versions)
    - Architecture du projet
    - _Requirements: 11.1_

  - [ ] 16.2 Documenter l'installation des dépendances
    - Commandes backend et frontend
    - Problèmes de compatibilité
    - _Requirements: 11.2_
  - [x] 16.3 Documenter la configuration des variables d'environnement

    - Exemples de fichiers .env complets

    - _Requirements: 11.3_
  - [x] 16.4 Documenter la configuration de ngrok

    - Installation, démarrage, configuration webhooks
    - _Requirements: 11.4_
  - [x] 16.5 Documenter le démarrage du projet

    - Ordre de démarrage, commandes exactes
    - Vérification du fonctionnement

    - _Requirements: 11.5_
  - [x] 16.6 Documenter les tests d'envoi de messages





    - Préparation numéro de test, envoi, vérification
    - _Requirements: 11.6_
  - [x] 16.7 Ajouter la section troubleshooting








    - Erreurs courantes et solutions
    - Problèmes CORS, réseau, webhooks
    - _Requirements: 11.6_

- [ ] 17. Checkpoint final - Validation complète
  - Ensure all tests pass, ask the user if questions arise.
