# Implementation Plan

## Migration Twilio Sandbox → Wassenger 2025

- [x] 1. Mettre à jour la configuration et les variables d'environnement






  - [x] 1.1 Ajouter les variables Wassenger dans config.py

    - Ajouter WASSENGER_API_KEY, WASSENGER_DEVICE_ID, WASSENGER_WEBHOOK_URL dans la classe Settings
    - Créer la méthode validate_wassenger_config() pour valider les variables obligatoires
    - Mettre à jour validate_config_on_startup() pour appeler la nouvelle validation
    - _Requirements: 1.1, 1.2, 5.1, 5.4_
  - [x] 1.2 Write property test for configuration validation






    - **Property 6: Configuration Validation**
    - **Validates: Requirements 1.1, 1.2, 5.4**

  - [x] 1.3 Mettre à jour le fichier .env.example

    - Ajouter les variables WASSENGER_* avec commentaires explicatifs en français
    - Conserver les anciennes variables TWILIO_* commentées pour référence
    - _Requirements: 5.2, 5.3_

- [x] 2. Créer le service WassengerService



  - [x] 2.1 Créer les dataclasses WassengerResponse et WassengerWebhookInteraction


    - Créer backend/app/services/wassenger_service.py
    - Définir WassengerResponse avec success, message_id, error_code, error_message, raw_response
    - Définir WassengerWebhookInteraction avec contact_phone, interaction_type, content, wassenger_message_id, timestamp, error_message
    - _Requirements: 2.3, 2.4, 3.1_

  - [x] 2.2 Implémenter la méthode format_phone_number()
    - Retirer le préfixe + si présent
    - Retirer les espaces et caractères non numériques
    - Retourner uniquement les chiffres (format: 22890123456)
    - _Requirements: 2.2_
  - [x] 2.3 Write property test for phone number formatting






    - **Property 1: Phone Number Formatting**

    - **Validates: Requirements 2.2**
  - [x] 2.4 Implémenter la méthode send_message()
    - Configurer httpx.AsyncClient avec header Authorization Bearer
    - Appeler POST https://api.wassenger.com/v1/messages
    - Inclure phone, message et device dans le payload
    - Parser la réponse et retourner WassengerResponse
    - _Requirements: 2.1, 2.3, 2.4, 2.5_
  - [x] 2.5 Write property test for API response parsing






    - **Property 7: API Response Parsing - Success**
    - **Property 8: API Response Parsing - Error**
    - **Validates: Requirements 2.3, 2.4**
  - [x] 2.6 Write property test for Device ID inclusion


    - **Property 9: Device ID Inclusion in Requests**
    - **Validates: Requirements 1.4, 2.1**
  - [x] 2.7 Implémenter la gestion des erreurs Wassenger

    - Créer le dictionnaire WASSENGER_ERROR_MESSAGES avec messages en français
    - Implémenter get_error_details() pour retourner les détails d'erreur
    - Gérer les codes: device_not_connected, invalid_phone_number, rate_limit_exceeded, session_expired
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_
  - [x] 2.8 Write property test for error message mapping






    - **Property 4: Error Message Mapping**
    - **Validates: Requirements 7.1, 7.2, 7.4**

- [x] 3. Implémenter le parsing des webhooks Wassenger





  - [x] 3.1 Implémenter parse_webhook_payload()


    - Parser l'événement (event) et les données (data)
    - Extraire fromNumber, body, id pour message:in:new
    - Extraire status, id pour les événements de statut
    - Retourner une liste de WassengerWebhookInteraction
    - _Requirements: 3.1, 3.2_
  - [x] 3.2 Write property test for webhook payload parsing






    - **Property 2: Webhook Payload Parsing**
    - **Validates: Requirements 3.1, 3.2**

  - [x] 3.3 Implémenter le mapping des statuts webhook

    - Mapper message:out:sent → sent
    - Mapper message:out:delivered → delivered
    - Mapper message:out:read → read
    - Mapper message:out:failed → failed
    - _Requirements: 3.3, 3.4, 3.5, 3.6_
  - [x] 3.4 Write property test for webhook status mapping






    - **Property 3: Webhook Status Mapping**
    - **Validates: Requirements 3.3, 3.4, 3.5, 3.6**

- [x] 4. Checkpoint - Vérifier que tous les tests passent









  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Créer l'endpoint webhook Wassenger





  - [x] 5.1 Ajouter l'endpoint POST /api/webhooks/wassenger


    - Créer la route dans backend/app/routers/webhooks.py
    - Parser le payload JSON
    - Retourner 200 OK immédiatement
    - Traiter le webhook en background task
    - _Requirements: 3.7_

  - [x] 5.2 Implémenter process_wassenger_message()












    - Rechercher le contact par numéro de téléphone
    - Vérifier si un Message 1 récent existe (24h)
    - Vérifier si un Message 2 a déjà été envoyé
    - Créer et programmer le Message 2 si nécessaire
    - Enregistrer l'interaction dans la base de données

    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_
  - [x] 5.3 Implémenter process_wassenger_status()








    - Rechercher le message par wassenger_message_id
    - Mettre à jour le statut avec horodatage
    - Mettre à jour les compteurs de la campagne
    - _Requirements: 3.3, 3.4, 3.5, 3.6_

- [x] 6. Mettre à jour les tâches Celery





  - [x] 6.1 Modifier send_single_message() pour utiliser WassengerService


    - Remplacer twilio_service par wassenger_service
    - Adapter le format de réponse (message_id au lieu de message_sid)
    - Conserver la logique de retry avec délai exponentiel
    - _Requirements: 6.1, 6.2, 6.4_
  - [x] 6.2 Write property test for exponential retry delay






    - **Property 5: Exponential Retry Delay Calculation**
    - **Validates: Requirements 2.6, 6.4**

  - [x] 6.3 Mettre à jour send_campaign_messages()

    - Utiliser wassenger_service pour l'envoi
    - Adapter le rate limiting (2 secondes au lieu de 3)
    - _Requirements: 6.1_

  - [x] 6.4 Mettre à jour retry_failed_message()

    - Utiliser wassenger_service pour les retries
    - _Requirements: 6.4_

- [x] 7. Checkpoint - Vérifier que tous les tests passent





  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Archiver le code Twilio et nettoyer





  - [x] 8.1 Archiver twilio_service.py


    - Déplacer backend/app/services/twilio_service.py vers backend/app/services/archive/
    - _Requirements: 9.1_

  - [x] 8.2 Mettre à jour les imports

    - Remplacer les imports de twilio_service par wassenger_service dans webhooks.py
    - Remplacer les imports dans message_tasks.py
    - _Requirements: 9.3_

  - [x] 8.3 Mettre à jour requirements.txt

    - Ajouter httpx si non présent
    - Commenter ou supprimer la dépendance twilio
    - _Requirements: 9.4_

- [x] 9. Créer la documentation






  - [x] 9.1 Créer GUIDE_LANCEMENT_PROJET_WASSENGER_2025.md

    - Section 1: Prérequis (Python, Node.js, ngrok)
    - Section 2: Configuration Supabase
    - Section 3: Configuration Backend (.env)
    - Section 4: Configuration Frontend (.env.local)
    - Section 5: Lancement Local
    - Section 6: Configuration ngrok
    - Section 7: Configuration Webhook Wassenger
    - Section 8: Tests du Workflow
    - Section 9: Dépannage
    - _Requirements: 8.1_

  - [x] 9.2 Créer GUIDE_CONFIGURATION_WASSENGER_2025.md

    - Section 1: Création du Compte Wassenger
    - Section 2: Connexion WhatsApp à Wassenger
    - Section 3: Obtenir l'API Key Wassenger
    - Section 4: Obtenir le Device ID
    - Section 5: Configuration des Webhooks
    - Section 6: Test de la Configuration
    - Section 7: Intégration au Projet
    - _Requirements: 8.2_

  - [x] 9.3 Créer GUIDE_CONFIGURATION_PROFIL_BUSINESS_WHATSAPP.md

    - Section 1: Comprendre le Profil WhatsApp Business
    - Section 2: Vérifier le Type de Compte WhatsApp
    - Section 3: Configuration du Profil Business dans WhatsApp
    - Section 4: Configuration dans Wassenger Dashboard
    - Section 5: Demande de Vérification WhatsApp Business
    - Section 6: Utilisation de l'API WhatsApp Business
    - Section 7: Configuration des Messages avec Nom du Chatbot
    - Section 8: Tests et Vérification
    - Section 9: Limitations et Contraintes
    - Section 10: Bonnes Pratiques
    - Section 11: Dépannage
    - _Requirements: 8.3, 10.1, 10.2, 10.3, 10.4_

- [x] 10. Créer les tests du service Wassenger





  - [x] 10.1 Créer test_wassenger_service.py avec tests unitaires






    - Tests d'initialisation du service
    - Tests de formatage des numéros
    - Tests de parsing des webhooks
    - Tests des dataclasses
    - Tests de gestion des erreurs
    - _Requirements: 9.2_

- [x] 11. Final Checkpoint - Vérifier que tous les tests passent





  - Ensure all tests pass, ask the user if questions arise.
