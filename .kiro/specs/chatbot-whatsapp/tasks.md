# Plan d'Implémentation - Chatbot WhatsApp

## Vue d'Ensemble

Ce plan détaille les tâches d'implémentation pour le système de chatbot WhatsApp. Les tâches sont organisées de manière incrémentale pour permettre une validation continue du système.

## Tâches

- [x] 1. Configuration de la base de données Supabase





  - Créer le projet Supabase
  - Exécuter le script schema.sql pour créer toutes les tables
  - Configurer les Row Level Security (RLS) policies
  - Exécuter seed_superadmin.sql pour créer le compte Super Admin
  - Exécuter seed_admin.sql pour créer un compte Admin de test
  - Vérifier la connectivité et les permissions
  - _Exigences : 18.1, 18.2, 18.3, 18.4, 18.5, 18.6_

- [x] 2. Setup du backend FastAPI






- [x] 2.1 Créer la structure de base du projet backend

  - Créer l'arborescence des dossiers (app/, models/, schemas/, routers/, services/, tasks/, utils/)
  - Configurer main.py avec FastAPI et middleware CORS
  - Créer config.py pour charger les variables d'environnement
  - Créer database.py pour la connexion Supabase/PostgreSQL
  - Créer requirements.txt avec toutes les dépendances
  - _Exigences : 15.1, 15.2_


- [x] 2.2 Implémenter les modèles SQLAlchemy

  - Créer models/user.py (User avec rôles super_admin/admin)
  - Créer models/category.py (Category avec relations)
  - Créer models/contact.py (Contact avec indicatif pays)
  - Créer models/campaign.py (Campaign avec statuts)
  - Créer models/message.py (Message avec tracking)
  - Créer models/interaction.py (Interaction pour webhooks)
  - _Exigences : 18.2, 18.3_


- [x] 2.3 Créer les schémas Pydantic

  - Créer schemas/user.py (UserCreate, UserResponse, UserUpdate)
  - Créer schemas/category.py (CategoryCreate, CategoryResponse)
  - Créer schemas/contact.py (ContactCreate, ContactResponse, ContactImport)
  - Créer schemas/campaign.py (CampaignCreate, CampaignResponse, CampaignStats)
  - Créer schemas/message.py (MessageResponse, MessageStats)
  - Créer schemas/auth.py (Token, LoginRequest)
  - _Exigences : 10.1_

- [x] 3. Implémentation de l'authentification et sécurité






- [x] 3.1 Créer le service d'authentification

  - Implémenter utils/security.py (hash_password, verify_password, create_access_token, decode_token)
  - Implémenter services/auth_service.py (authenticate_user, get_current_user, verify_super_admin)
  - Configurer JWT avec expiration 30 minutes
  - _Exigences : 1.1, 1.4, 10.3_



- [x] 3.2 Créer les routes d'authentification







  - Implémenter routers/auth.py
  - POST /api/auth/login (connexion avec génération JWT)
  - POST /api/auth/refresh (rafraîchir le token)
  - GET /api/auth/me (obtenir l'utilisateur courant)
  - _Exigences : 1.1, 1.5_

- [ ]* 3.3 Écrire les tests pour l'authentification
  - Test unitaire : hashage et vérification des mots de passe
  - Test unitaire : génération et validation JWT
  - Test d'intégration : flux de login complet
  - **Property 10: Hashage des mots de passe** - Valide : Exigences 1.4, 10.3
  - **Property 9: Validation JWT** - Valide : Exigences 1.5, 10.4
  - _Exigences : 1.1, 1.4, 1.5_

- [x] 4. Gestion des catégories






- [x] 4.1 Implémenter le CRUD des catégories

  - Créer routers/categories.py
  - GET /api/categories (liste avec pagination)
  - POST /api/categories (créer une catégorie)
  - GET /api/categories/{id} (détails d'une catégorie)
  - PUT /api/categories/{id} (modifier une catégorie)
  - DELETE /api/categories/{id} (supprimer une catégorie)
  - POST /api/categories/{id}/contacts (ajouter des contacts)
  - DELETE /api/categories/{id}/contacts/{contact_id} (retirer un contact)
  - _Exigences : 3.1, 3.2, 3.4, 3.5_

- [ ]* 4.2 Écrire les tests pour les catégories
  - Test unitaire : création de catégorie
  - Test unitaire : association contact-catégorie
  - **Property 2: Intégrité des associations** - Valide : Exigences 3.2, 3.3
  - **Property 3: Conservation des contacts** - Valide : Exigences 3.5
  - _Exigences : 3.1, 3.2, 3.5_

- [x] 5. Gestion des contacts





- [x] 5.1 Créer le service de validation des contacts


  - Implémenter utils/validators.py (validate_phone_number, validate_country_code)
  - Créer la liste des indicatifs pays dans utils/constants.py
  - Implémenter la validation du format international
  - _Exigences : 2.1, 2.2, 10.6_


- [x] 5.2 Implémenter le CRUD des contacts

  - Créer routers/contacts.py
  - GET /api/contacts (liste avec pagination et recherche)
  - POST /api/contacts (créer un contact avec validation)
  - GET /api/contacts/{id} (détails d'un contact)
  - PUT /api/contacts/{id} (modifier un contact)
  - DELETE /api/contacts/{id} (supprimer un contact et ses associations)
  - _Exigences : 2.1, 2.4, 2.5, 2.6_



- [x] 5.3 Implémenter l'import CSV de contacts

  - POST /api/contacts/import (upload et traitement CSV)
  - Valider chaque ligne du CSV
  - Créer les contacts valides et logger les erreurs
  - Retourner un rapport d'import (succès/échecs)
  - _Exigences : 2.3_

- [ ]* 5.4 Écrire les tests pour les contacts
  - Test unitaire : validation format numéro
  - Test unitaire : import CSV avec données valides/invalides
  - **Property 1: Validation du format des numéros** - Valide : Exigences 2.1, 2.4, 10.6
  - _Exigences : 2.1, 2.3_

- [x] 6. Intégration WhatsApp Business API






- [x] 6.1 Créer le service WhatsApp

  - Implémenter services/whatsapp_service.py
  - Fonction send_template_message (Message 1 avec template Meta)
  - Fonction send_text_message (Message 2 en texte libre)
  - Fonction verify_webhook (validation token Meta)
  - Fonction parse_webhook_payload (parser les webhooks reçus)
  - Gestion des erreurs API WhatsApp avec logging
  - _Exigences : 17.1, 17.2, 17.3, 17.4_


- [x] 6.2 Implémenter les routes webhook

  - Créer routers/webhooks.py
  - GET /api/webhooks/whatsapp (vérification webhook Meta)
  - POST /api/webhooks/whatsapp (réception des webhooks)
  - Parser le payload et enregistrer dans la table interactions
  - Retourner 200 OK dans les 20 secondes
  - _Exigences : 8.1, 8.2, 8.5, 17.5, 17.6_

- [ ]* 6.3 Écrire les tests pour WhatsApp API
  - Test unitaire : formatage requête template
  - Test unitaire : parsing webhook payload
  - Test d'intégration : vérification webhook
  - **Property 15: Réponse webhook** - Valide : Exigences 8.5
  - _Exigences : 17.3, 17.6, 8.5_

- [x] 7. Configuration Celery et Redis





- [x] 7.1 Setup Celery et Redis


  - Créer tasks/celery_app.py (configuration Celery)
  - Configurer Redis comme message broker
  - Configurer les queues et routing
  - Implémenter le rate limiting (25 msg/min)
  - _Exigences : 16.1, 16.3_


- [x] 7.2 Créer les tâches Celery pour l'envoi de messages

  - Créer tasks/message_tasks.py
  - Tâche send_campaign_messages (envoi massif par lots)
  - Tâche send_single_message (envoi individuel)
  - Tâche retry_failed_message (retry avec backoff exponentiel)
  - Respecter la limite de 25 messages par minute
  - _Exigences : 4.4, 4.8, 7.1, 7.2, 16.3_

- [ ]* 7.3 Écrire les tests pour Celery
  - Test unitaire : création tâche Celery
  - Test unitaire : rate limiting 25 msg/min
  - **Property 4: Respect du rate limiting** - Valide : Exigences 4.8
  - **Property 8: Délai exponentiel retry** - Valide : Exigences 7.2
  - _Exigences : 4.8, 7.2, 16.3_

- [x] 8. Système de messages et automatisation





- [x] 8.1 Créer le service de messages


  - Implémenter services/message_service.py
  - Fonction create_campaign (créer campagne et messages)
  - Fonction send_campaign_messages (déclencher envoi Celery)
  - Fonction get_campaign_stats (calculer statistiques)
  - Fonction retry_failed_messages (réessayer les échecs)
  - Fonction calculate_success_rate (calcul taux de réussite)
  - _Exigences : 4.4, 6.2, 6.5, 7.1_


- [x] 8.2 Créer le service d'automatisation

  - Implémenter services/automation_service.py
  - Fonction should_send_message_2 (vérifier si Message 2 doit être envoyé)
  - Fonction trigger_message_2 (déclencher envoi Message 2)
  - Fonction reset_automation_sequence (réinitialiser séquence)
  - Fonction log_interaction (enregistrer interaction)
  - _Exigences : 4.5, 4.6, 4.7, 8.3, 8.4_


- [x] 8.3 Implémenter les routes de campagnes

  - Créer routers/campaigns.py
  - GET /api/campaigns (liste avec pagination)
  - POST /api/campaigns (créer et lancer une campagne)
  - GET /api/campaigns/{id} (détails d'une campagne)
  - GET /api/campaigns/{id}/stats (statistiques détaillées)
  - POST /api/campaigns/{id}/retry (réessayer les échecs)
  - _Exigences : 20.1, 20.2, 20.3, 20.4, 20.5_


- [x] 8.4 Implémenter les routes de messages

  - Créer routers/messages.py
  - GET /api/messages (liste avec filtres et pagination)
  - GET /api/messages/{id} (détails d'un message)
  - GET /api/messages/stats (statistiques globales)
  - _Exigences : 6.1, 6.3, 6.4_

- [ ]* 8.5 Écrire les tests pour messages et automatisation
  - Test unitaire : calcul taux de réussite
  - Test unitaire : logique déclenchement Message 2
  - Test d'intégration : flux complet campagne
  - **Property 5: Déclenchement Message 2** - Valide : Exigences 4.5, 4.6
  - **Property 6: Calcul taux de réussite** - Valide : Exigences 6.5
  - **Property 7: Limite retry** - Valide : Exigences 7.3
  - _Exigences : 4.5, 4.6, 6.5, 7.3_

- [x] 9. Gestion des utilisateurs (Super Admin)







- [x] 9.1 Implémenter les routes de gestion des utilisateurs

  - Créer routers/users.py (accessible uniquement Super Admin)
  - GET /api/users (liste des Admins)
  - POST /api/users (créer un Admin)
  - PUT /api/users/{id} (modifier un Admin)
  - DELETE /api/users/{id} (supprimer un Admin)
  - Vérifier le rôle Super Admin pour chaque endpoint
  - _Exigences : 1.2, 1.3, 1.4_

- [ ]* 9.2 Écrire les tests pour la gestion des utilisateurs
  - Test unitaire : vérification rôle Super Admin
  - Test d'intégration : création Admin par Super Admin
  - Test d'intégration : Admin ne peut pas créer d'autres utilisateurs
  - **Property 11: Isolation des données RLS** - Valide : Exigences 1.6
  - _Exigences : 1.2, 1.3, 1.6_




- [ ] 10. Checkpoint Backend - Vérification complète
  - Lancer tous les tests unitaires et d'intégration
  - Vérifier que tous les endpoints fonctionnent
  - Tester l'authentification et les permissions
  - Tester l'envoi de messages via WhatsApp API
  - Vérifier les webhooks avec ngrok
  - Vérifier les tâches Celery et Redis
  - Corriger les bugs identifiés
  - Demander à l'utilisateur si des questions se posent

- [x] 11. Setup du frontend Next.js







- [x] 11.1 Créer la structure de base du projet frontend

  - Initialiser Next.js 14+ avec App Router et TypeScript
  - Configurer Tailwind CSS
  - Installer shadcn/ui et initialiser les composants de base
  - Créer l'arborescence (app/, components/, lib/, hooks/, types/)
  - Configurer .env.local avec les variables d'environnement
  - _Exigences : 15.3_


- [x] 11.2 Configurer les clients API et Supabase

  - Créer lib/api.ts (client Axios avec intercepteurs JWT)
  - Créer lib/supabase.ts (client Supabase)
  - Créer lib/utils.ts (fonctions utilitaires)
  - Créer lib/constants.ts (constantes, indicatifs pays)
  - Configurer React Query avec QueryClient
  - _Exigences : 11.5_


- [x] 11.3 Créer les types TypeScript

  - Créer types/auth.ts (User, LoginRequest, Token)
  - Créer types/category.ts (Category, CategoryCreate)
  - Créer types/contact.ts (Contact, ContactCreate)
  - Créer types/campaign.ts (Campaign, CampaignCreate, CampaignStats)
  - Créer types/message.ts (Message, MessageStats)
  - _Exigences : 10.2_

- [x] 12. Authentification et layout frontend






- [x] 12.1 Créer le système d'authentification frontend

  - Créer hooks/useAuth.ts (gestion authentification, JWT, localStorage)
  - Créer app/login/page.tsx (page de connexion)
  - Créer components/layout/ProtectedRoute.tsx (HOC pour routes protégées)
  - Implémenter la validation des formulaires avec React Hook Form
  - _Exigences : 1.1, 10.2_


- [x] 12.2 Créer le layout principal

  - Créer app/layout.tsx (layout racine avec providers)
  - Créer components/layout/Sidebar.tsx (navigation avec rôles)
  - Créer components/layout/Header.tsx (en-tête avec profil utilisateur)
  - Implémenter l'affichage conditionnel selon le rôle (Super Admin vs Admin)
  - Créer app/page.tsx (redirection vers /dashboard)
  - _Exigences : 1.2, 1.3, 13.1, 13.2, 13.3_

- [ ]* 12.3 Écrire les tests pour l'authentification frontend
  - Test composant : formulaire de connexion
  - Test hook : useAuth avec localStorage
  - Test intégration : flux de login complet
  - _Exigences : 1.1, 10.2_

- [x] 13. Pages de gestion des catégories









- [x] 13.1 Créer les composants de catégories


  - Créer components/categories/CategoryCard.tsx (carte avec gradient)
  - Créer components/categories/CategoryForm.tsx (formulaire création/édition)
  - Créer components/categories/CategoryList.tsx (liste avec recherche)
  - Créer hooks/useCategories.ts (React Query hooks)
  - _Exigences : 3.1, 3.6_


- [x] 13.2 Créer les pages de catégories

  - Créer app/categories/page.tsx (liste des catégories)
  - Créer app/categories/[id]/page.tsx (détails d'une catégorie)
  - Implémenter la recherche et le filtrage
  - Implémenter les actions (créer, modifier, supprimer)
  - _Exigences : 3.1, 3.4, 3.5, 3.6_

- [ ]* 13.3 Écrire les tests pour les catégories frontend
  - Test composant : CategoryCard affichage
  - Test composant : CategoryForm validation
  - Test intégration : création de catégorie
  - _Exigences : 3.1, 3.6_

- [x] 14. Pages de gestion des contacts






- [x] 14.1 Créer les composants de contacts

  - Créer components/contacts/ContactForm.tsx (formulaire avec indicatif pays)
  - Créer components/contacts/ContactTable.tsx (table avec pagination)
  - Créer components/contacts/ContactImport.tsx (import CSV)
  - Créer hooks/useContacts.ts (React Query hooks)
  - _Exigences : 2.1, 2.2, 2.3, 11.1_


- [x] 14.2 Créer les pages de contacts

  - Créer app/contacts/page.tsx (liste des contacts)
  - Créer app/contacts/import/page.tsx (import CSV)
  - Implémenter la pagination (50 éléments par page)
  - Implémenter la recherche et le filtrage
  - _Exigences : 2.1, 2.3, 2.5, 2.6, 11.1_

- [ ]* 14.3 Écrire les tests pour les contacts frontend
  - Test composant : ContactForm validation numéro
  - Test composant : ContactImport upload CSV
  - Test intégration : création de contact
  - **Property 12: Pagination des listes** - Valide : Exigences 11.1
  - _Exigences : 2.1, 2.3, 11.1_

- [x] 15. Pages de campagnes et messages






- [x] 15.1 Créer les composants de campagnes

  - Créer components/campaigns/CampaignForm.tsx (configuration campagne)
  - Créer components/campaigns/MessageEditor.tsx (éditeur Message 1 & 2)
  - Créer components/campaigns/MessagePreview.tsx (prévisualisation WhatsApp)
  - Créer components/campaigns/CampaignStats.tsx (statistiques détaillées)
  - Créer hooks/useCampaigns.ts (React Query hooks)
  - _Exigences : 4.1, 4.2, 4.3, 5.1, 5.2, 5.3, 6.3_


- [x] 15.2 Créer les pages de campagnes

  - Créer app/campaigns/page.tsx (liste des campagnes)
  - Créer app/campaigns/new/page.tsx (nouvelle campagne)
  - Créer app/campaigns/[id]/page.tsx (détails et statistiques)
  - Implémenter la prévisualisation en temps réel
  - Implémenter l'insertion de liens (web, wa.me)
  - Implémenter le bouton retry pour les échecs
  - _Exigences : 4.1, 4.2, 4.3, 5.1, 5.2, 5.3, 20.1, 20.2, 20.3_

- [ ]* 15.3 Écrire les tests pour les campagnes frontend
  - Test composant : MessageEditor validation
  - Test composant : MessagePreview affichage
  - Test intégration : création et envoi campagne
  - **Property 13: Validation des URLs** - Valide : Exigences 4.3, 10.7
  - _Exigences : 4.1, 4.3, 5.1, 10.7_

- [x] 16. Dashboard statistiques







- [x] 16.1 Créer les composants de statistiques

  - Créer components/dashboard/StatsCard.tsx (carte métrique)
  - Créer components/dashboard/LineChart.tsx (graphique évolution Recharts)
  - Créer components/dashboard/PieChart.tsx (graphique répartition Recharts)
  - Créer components/dashboard/RecentMessages.tsx (historique récent)
  - Créer hooks/useStats.ts (React Query hooks)
  - _Exigences : 6.7, 9.1, 9.2, 9.5, 9.6_


- [x] 16.2 Créer les pages de statistiques

  - Créer app/dashboard/page.tsx (dashboard principal)
  - Créer app/statistics/page.tsx (statistiques détaillées)
  - Afficher les métriques clés (envoyés, taux réussite, utilisateurs actifs, coût)
  - Afficher le graphique d'évolution (7 derniers jours)
  - Afficher le graphique de répartition des statuts
  - Implémenter la recherche et le filtrage de l'historique
  - Implémenter l'export CSV
  - _Exigences : 6.7, 6.8, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8_

- [ ]* 16.3 Écrire les tests pour le dashboard frontend
  - Test composant : StatsCard affichage
  - Test composant : LineChart avec données
  - Test intégration : chargement dashboard complet
  - _Exigences : 9.1, 9.2, 9.5, 9.6_

- [x] 17. Gestion des utilisateurs (Super Admin uniquement)






- [x] 17.1 Créer les composants de gestion des utilisateurs

  - Créer components/users/UserForm.tsx (formulaire Admin)
  - Créer components/users/UserTable.tsx (table des Admins)
  - Vérifier le rôle Super Admin avant affichage
  - _Exigences : 1.2, 1.3, 1.4_


- [x] 17.2 Créer la page de gestion des utilisateurs

  - Créer app/admin-users/page.tsx (accessible Super Admin uniquement)
  - Implémenter CRUD des Admins
  - Afficher la liste des Admins avec statuts
  - _Exigences : 1.2, 1.3, 1.4_

- [ ]* 17.3 Écrire les tests pour la gestion des utilisateurs frontend
  - Test composant : UserForm validation
  - Test intégration : Super Admin crée un Admin
  - Test intégration : Admin ne voit pas la page
  - _Exigences : 1.2, 1.3_

- [x] 18. Composants communs et UX






- [x] 18.1 Créer les composants communs

  - Créer components/common/LoadingSpinner.tsx
  - Créer components/common/ErrorMessage.tsx
  - Créer components/common/ConfirmDialog.tsx
  - Créer components/common/Toast.tsx (notifications)
  - Implémenter les skeleton loaders
  - _Exigences : 14.1, 14.2, 14.3, 14.5_


- [x] 18.2 Implémenter les indicateurs de chargement

  - Ajouter les spinners pendant les requêtes API
  - Ajouter les messages de succès/erreur
  - Ajouter les barres de progression pour envois massifs
  - Ajouter les skeleton loaders pendant le chargement
  - _Exigences : 14.1, 14.2, 14.3, 14.4, 14.5_

- [ ]* 18.3 Écrire les tests pour les composants communs
  - Test composant : LoadingSpinner
  - Test composant : ErrorMessage
  - Test composant : Toast notifications
  - _Exigences : 14.1, 14.2, 14.3_

- [x] 19. Responsive design et accessibilité







- [x] 19.1 Optimiser pour mobile et tablette

  - Adapter le layout avec Tailwind responsive classes
  - Tester sur mobile (320px, 375px, 414px)
  - Tester sur tablette (768px, 1024px)
  - Ajuster les graphiques Recharts pour petits écrans
  - Optimiser les formulaires pour le tactile
  - _Exigences : 13.1, 13.2, 13.3, 13.4, 13.5_

- [ ]* 19.2 Tester l'accessibilité
  - Vérifier les labels de formulaires
  - Vérifier la navigation au clavier
  - Vérifier les contrastes de couleurs
  - Tester avec un lecteur d'écran
  - _Exigences : 13.4_

- [ ] 20. Checkpoint Frontend - Vérification complète
  - Lancer tous les tests frontend
  - Tester toutes les pages et fonctionnalités
  - Vérifier le responsive sur différents appareils
  - Vérifier les performances (Lighthouse)
  - Tester l'intégration complète avec le backend
  - Corriger les bugs identifiés
  - Demander à l'utilisateur si des questions se posent

- [x] 21. Documentation complète








- [x] 21.1 Créer le guide de configuration

  - Créer docs/01-CONFIGURATION.md
  - Instructions d'installation des dépendances (Python, Node.js, Redis)
  - Instructions de configuration Supabase
  - Instructions de configuration des variables d'environnement
  - Instructions d'installation des packages frontend et backend
  - _Exigences : 19.1_


- [x] 21.2 Créer le guide WhatsApp









  - Créer docs/02-WHATSAPP-SETUP.md
  - Guide de création compte Meta Business
  - Guide de configuration WhatsApp Business API
  - Instructions pour obtenir Phone Number ID et Access Token
  - Instructions pour créer et approuver des templates
  - Instructions pour configurer les webhooks
  - _Exigences : 19.2_


- [x] 21.3 Créer le guide de lancement local

  - Créer docs/03-LANCEMENT-LOCAL.md
  - Instructions pour lancer Redis
  - Instructions pour lancer Celery worker
  - Instructions pour lancer le backend FastAPI
  - Instructions pour lancer le frontend Next.js
  - Instructions pour tester l'authentification
  - Instructions pour tester l'envoi de messages
  - Instructions pour vérifier les webhooks avec ngrok
  - _Exigences : 19.3_


- [x] 21.4 Créer le guide de déploiement

  - Créer docs/04-DEPLOIEMENT-GRATUIT.md
  - Guide de déploiement backend sur Railway/Render
  - Guide de déploiement frontend sur Vercel
  - Guide de configuration Redis sur Upstash
  - Configuration des webhooks en production
  - Tests de bout en bout en production
  - _Exigences : 19.4_



- [ ] 21.5 Créer les fichiers .env.example
  - Créer backend/.env.example avec toutes les variables
  - Créer frontend/.env.local.example avec toutes les variables
  - Documenter chaque variable d'environnement
  - _Exigences : 19.5_

- [ ] 22. Tests finaux et déploiement
- [ ] 22.1 Tests end-to-end complets
  - Configurer Playwright pour les tests E2E
  - Tester le flux complet : Login → Créer catégorie → Ajouter contact → Créer campagne → Envoyer
  - Tester le flux webhook : Recevoir interaction → Déclencher Message 2
  - Tester le flux retry : Message échoue → Retry automatique
  - Tester tous les rôles (Super Admin vs Admin)
  - _Exigences : Toutes_

- [ ] 22.2 Préparation au déploiement
  - Vérifier que tous les tests passent
  - Configurer les variables d'environnement de production
  - Créer le Super Admin en production
  - Configurer les webhooks WhatsApp pour la production
  - Vérifier la sécurité (CORS, JWT, RLS)
  - _Exigences : 15.4, 15.5_

- [ ] 22.3 Déploiement et validation
  - Déployer le backend sur Railway/Render
  - Déployer le frontend sur Vercel
  - Configurer Redis sur Upstash
  - Tester l'authentification en production
  - Tester l'envoi de messages en production
  - Vérifier les webhooks en production
  - Vérifier les statistiques et le dashboard
  - _Exigences : Toutes_

- [ ] 23. Checkpoint Final
  - Vérifier que toutes les fonctionnalités sont opérationnelles
  - Vérifier que la documentation est complète
  - Vérifier que le système est déployé et accessible
  - Effectuer une démonstration complète du système
  - Demander à l'utilisateur si le projet répond à ses attentes
