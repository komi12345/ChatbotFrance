# ⚙️ Guide de Configuration Wassenger 2025

Ce guide détaille les étapes pour créer et configurer votre compte Wassenger afin d'intégrer l'API WhatsApp à votre projet.

---

## 📋 Table des Matières

1. [Création du Compte Wassenger](#1-création-du-compte-wassenger)
2. [Connexion WhatsApp à Wassenger](#2-connexion-whatsapp-à-wassenger)
3. [Obtenir l'API Key Wassenger](#3-obtenir-lapi-key-wassenger)
4. [Obtenir le Device ID](#4-obtenir-le-device-id)
5. [Configuration des Webhooks](#5-configuration-des-webhooks)
6. [Test de la Configuration](#6-test-de-la-configuration)
7. [Intégration au Projet](#7-intégration-au-projet)

---

## 1. Création du Compte Wassenger

### 1.1 S'inscrire sur Wassenger

1. Rendez-vous sur [wassenger.com](https://wassenger.com/)
2. Cliquez sur **Sign Up** ou **Get Started**
3. Remplissez le formulaire d'inscription :
   - **Email** : Votre adresse email professionnelle
   - **Password** : Un mot de passe fort
   - **Company Name** : Nom de votre entreprise (optionnel)
4. Validez votre email en cliquant sur le lien reçu

### 1.2 Choisir un Plan

Wassenger propose plusieurs plans :

| Plan | Messages/mois | Prix | Recommandé pour |
|------|---------------|------|-----------------|
| **Free Trial** | 100 | Gratuit | Tests et développement |
| **Starter** | 1,000 | ~$19/mois | Petits projets |
| **Professional** | 10,000 | ~$49/mois | Projets moyens |
| **Business** | Illimité | Sur devis | Gros volumes |

💡 **Conseil** : Commencez par le Free Trial pour tester l'intégration.

### 1.3 Accéder au Dashboard

Après inscription, connectez-vous à [app.wassenger.com](https://app.wassenger.com/)

Vous verrez le dashboard principal avec :
- 📱 **Devices** : Vos appareils WhatsApp connectés
- 📊 **Analytics** : Statistiques d'utilisation
- ⚙️ **Settings** : Configuration API et webhooks

---

## 2. Connexion WhatsApp à Wassenger

### 2.1 Prérequis

Avant de connecter WhatsApp :
- ✅ Un smartphone avec WhatsApp installé
- ✅ Un numéro de téléphone actif
- ✅ WhatsApp Business App (recommandé) ou WhatsApp standard

### 2.2 Ajouter un Nouvel Appareil

1. Dans le dashboard, allez dans **Devices**
2. Cliquez sur **Add Device** ou **Connect New Device**
3. Donnez un nom à votre appareil (ex: "Chatbot Production")

### 2.3 Scanner le QR Code

1. Un QR code s'affiche à l'écran
2. Sur votre smartphone :
   - Ouvrez **WhatsApp**
   - Allez dans **Paramètres > Appareils liés**
   - Cliquez sur **Lier un appareil**
   - Scannez le QR code affiché sur Wassenger

### 2.4 Vérifier la Connexion

Après le scan :
- ✅ Le statut passe à **Connected** (vert)
- ✅ Le nom de l'appareil apparaît dans la liste
- ✅ Vous pouvez voir les informations du compte WhatsApp

⚠️ **Important** : 
- Gardez votre téléphone connecté à Internet
- Ne déconnectez pas WhatsApp Web/Desktop sur d'autres appareils
- La session reste active tant que le téléphone est en ligne

### 2.5 Résolution des Problèmes de Connexion

| Problème | Solution |
|----------|----------|
| QR code expiré | Rafraîchissez la page et rescannez |
| Connexion échouée | Vérifiez votre connexion Internet |
| Session déconnectée | Rescannez le QR code |
| "Trop d'appareils liés" | Déconnectez un appareil dans WhatsApp |

---

## 3. Obtenir l'API Key Wassenger

### 3.1 Accéder aux Paramètres API

1. Dans le dashboard, cliquez sur **Settings** (⚙️)
2. Allez dans **API Keys** ou **Developer Settings**

### 3.2 Créer une Nouvelle API Key

1. Cliquez sur **Create API Key** ou **Generate New Key**
2. Donnez un nom descriptif : "Chatbot WhatsApp Production"
3. Sélectionnez les permissions :
   - ✅ **Send Messages** : Envoyer des messages
   - ✅ **Read Messages** : Lire les messages (pour webhooks)
   - ✅ **Manage Devices** : Gérer les appareils (optionnel)
4. Cliquez sur **Create**

### 3.3 Copier l'API Key

L'API Key s'affiche une seule fois ! Copiez-la immédiatement.

Format de l'API Key :
```
wsp_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

- `wsp_live_` : Préfixe pour les clés de production
- `wsp_test_` : Préfixe pour les clés de test (sandbox)

### 3.4 Sécurité de l'API Key

⚠️ **IMPORTANT - Règles de sécurité** :

- ❌ Ne jamais commiter l'API Key dans Git
- ❌ Ne jamais l'exposer côté client (frontend)
- ✅ Stocker uniquement dans les variables d'environnement
- ✅ Utiliser des clés différentes pour dev/prod

---

## 4. Obtenir le Device ID

### 4.1 Localiser le Device ID

1. Dans le dashboard, allez dans **Devices**
2. Cliquez sur l'appareil connecté
3. Le **Device ID** est affiché dans les détails

### 4.2 Format du Device ID

Le Device ID ressemble à :
```
64a1b2c3d4e5f6g7h8i9j0k1
```

C'est un identifiant unique de 24 caractères hexadécimaux.

### 4.3 Copier le Device ID

1. Cliquez sur l'icône de copie (📋) à côté du Device ID
2. Ou sélectionnez et copiez manuellement

💡 **Conseil** : Si vous avez plusieurs appareils, notez quel Device ID correspond à quel numéro WhatsApp.

---

## 5. Configuration des Webhooks

### 5.1 Comprendre les Webhooks

Les webhooks permettent à Wassenger de notifier votre application quand :
- 📥 Un message est reçu
- ✅ Un message est envoyé
- 📬 Un message est délivré
- 👁️ Un message est lu
- ❌ Un envoi échoue

**🔴 IMPORTANT** : Sans webhooks configurés, vos statistiques "Délivrés", "Lus", "Échoués" resteront à 0 !

### 5.2 Exposer votre Backend Local avec ngrok

Pour le développement local, vous devez exposer votre backend à Internet :

#### Installation de ngrok

```bash
# Windows (avec Chocolatey)
choco install ngrok

# Ou téléchargez depuis https://ngrok.com/download
```

#### Créer un compte ngrok (gratuit)

1. Allez sur [ngrok.com](https://ngrok.com/)
2. Créez un compte gratuit
3. Récupérez votre **authtoken** dans le dashboard

#### Configurer ngrok

```bash
ngrok config add-authtoken VOTRE_AUTHTOKEN
```

#### Lancer ngrok

```bash
# Exposer le port 8000 (backend FastAPI)
ngrok http 8000
```

Vous obtiendrez une URL comme :
```
Forwarding    https://abc123def456.ngrok-free.app -> http://localhost:8000
```

**Copiez cette URL** - c'est votre URL publique pour les webhooks.

### 5.3 Créer un Webhook dans Wassenger

1. Connectez-vous à [app.wassenger.com](https://app.wassenger.com/)
2. Dans le menu de gauche, cliquez sur **Webhooks** (ou **Settings > Webhooks**)
3. Cliquez sur **+ Add Webhook** ou **Create Webhook**

### 5.4 Configurer l'URL du Webhook

Entrez l'URL de votre endpoint :

**Développement local (avec ngrok)** :
```
https://abc123def456.ngrok-free.app/api/webhooks/wassenger
```

**Production** :
```
https://votre-domaine.com/api/webhooks/wassenger
```

⚠️ **Attention** : L'URL ngrok change à chaque redémarrage (sauf avec un plan payant). Vous devrez mettre à jour le webhook dans Wassenger à chaque fois.

### 5.5 Sélectionner les Événements (CRUCIAL)

Cochez **TOUS** les événements suivants pour que les statistiques fonctionnent :

| Événement | Description | Impact sur les Stats |
|-----------|-------------|---------------------|
| `message:in:new` | Nouveau message entrant (réponse) | Déclenche Message 2 |
| `message:out:new` | Message sortant créé | - |
| `message:update` | **Mise à jour de statut** | ✅ Met à jour Délivrés/Lus/Échoués |
| `message:reaction` | Réaction à un message | Compteur interactions |

**🔴 L'événement `message:update` est OBLIGATOIRE pour les statistiques !**

C'est cet événement qui envoie les mises à jour de statut :
- `sent` → Le message a été envoyé
- `delivered` → Le message a été délivré (✅ incrémente "Délivrés")
- `read` → Le message a été lu (✅ incrémente "Lus")
- `failed` → L'envoi a échoué (✅ incrémente "Échoués")

### 5.6 Configuration Complète du Webhook

Remplissez le formulaire :

| Champ | Valeur |
|-------|--------|
| **Name** | `Chatbot WhatsApp Webhook` |
| **URL** | `https://votre-url.ngrok-free.app/api/webhooks/wassenger` |
| **Events** | ✅ Tous cochés (message:in:new, message:out:new, message:update, message:reaction) |
| **Status** | Active |

### 5.7 Options Avancées

- **Secret Token** (optionnel) : Pour valider l'authenticité des webhooks
- **Retry Policy** : 3 tentatives recommandées
- **Timeout** : 30 secondes recommandées

### 5.8 Sauvegarder et Activer

1. Cliquez sur **Save** ou **Create Webhook**
2. Vérifiez que le webhook est **Active** (vert)

### 5.9 Vérifier que le Webhook Fonctionne

#### Méthode 1 : Test depuis Wassenger

1. Dans la liste des webhooks, cliquez sur **Test** ou **Send Test**
2. Vérifiez les logs de votre backend :
   ```
   INFO: Webhook Wassenger reçu: event=test
   ```

#### Méthode 2 : Envoyer un Message de Test

1. Envoyez un message via votre application
2. Attendez quelques secondes
3. Vérifiez les logs du backend :
   ```
   INFO: Webhook Wassenger reçu: event=message:update
   INFO: Traitement statut Wassenger: type=sent, message_id=msg_xxx
   INFO: Message xxx mis à jour (Wassenger): {'status': 'sent', 'sent_at': '...'}
   ```

4. Quand le destinataire reçoit le message :
   ```
   INFO: Webhook Wassenger reçu: event=message:update
   INFO: Traitement statut Wassenger: type=delivered, message_id=msg_xxx
   INFO: Message xxx mis à jour (Wassenger): {'status': 'delivered', 'delivered_at': '...'}
   ```

### 5.10 Dépannage des Webhooks

| Problème | Cause | Solution |
|----------|-------|----------|
| Statistiques à 0 | Webhook non configuré | Configurez le webhook dans Wassenger |
| Webhook non reçu | URL incorrecte | Vérifiez l'URL ngrok et qu'elle pointe vers `/api/webhooks/wassenger` |
| Erreur 404 | Endpoint non trouvé | Vérifiez que le backend est lancé |
| Erreur 500 | Erreur serveur | Consultez les logs du backend |
| URL ngrok expirée | Session ngrok fermée | Relancez ngrok et mettez à jour l'URL dans Wassenger |
| Statuts non mis à jour | Événement `message:update` non coché | Cochez tous les événements dans Wassenger |

### 5.11 Workflow Complet des Webhooks

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Votre Backend  │────▶│   Wassenger     │────▶│   WhatsApp      │
│  (FastAPI)      │     │   API           │     │   (Destinataire)│
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        │  1. POST /messages    │                       │
        │──────────────────────▶│                       │
        │                       │  2. Envoi WhatsApp    │
        │                       │──────────────────────▶│
        │                       │                       │
        │  3. Webhook: sent     │                       │
        │◀──────────────────────│                       │
        │                       │                       │
        │                       │  4. Message délivré   │
        │                       │◀──────────────────────│
        │  5. Webhook: delivered│                       │
        │◀──────────────────────│                       │
        │                       │                       │
        │                       │  6. Message lu        │
        │                       │◀──────────────────────│
        │  7. Webhook: read     │                       │
        │◀──────────────────────│                       │
        │                       │                       │
        │  8. Mise à jour BDD   │                       │
        │  (status=delivered/   │                       │
        │   read)               │                       │
        │                       │                       │
        │  9. Stats mises à jour│                       │
        │  (Délivrés++, Lus++) │                       │
└───────┴───────────────────────┴───────────────────────┘
```

---

## 6. Test de la Configuration

### 6.1 Tester l'API Key

Utilisez curl ou Postman pour tester :

```bash
curl -X GET "https://api.wassenger.com/v1/devices" \
  -H "Authorization: Bearer wsp_live_votre_api_key"
```

**Réponse attendue** :
```json
{
  "devices": [
    {
      "id": "64a1b2c3d4e5f6g7h8i9j0k1",
      "name": "Chatbot Production",
      "status": "connected",
      "phone": "22890123456"
    }
  ]
}
```

### 6.2 Tester l'Envoi de Message

```bash
curl -X POST "https://api.wassenger.com/v1/messages" \
  -H "Authorization: Bearer wsp_live_votre_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "22890123456",
    "message": "Test depuis l API Wassenger",
    "device": "64a1b2c3d4e5f6g7h8i9j0k1"
  }'
```

**Réponse attendue** :
```json
{
  "id": "msg_abc123xyz",
  "status": "queued",
  "phone": "22890123456"
}
```

### 6.3 Tester le Webhook

1. Dans le dashboard Wassenger, allez dans **Webhooks**
2. Cliquez sur **Test** à côté de votre webhook
3. Vérifiez que votre serveur reçoit la requête

**Payload de test** :
```json
{
  "event": "message:in:new",
  "data": {
    "id": "test_msg_123",
    "fromNumber": "22890123456",
    "body": "Message de test",
    "timestamp": "2025-01-15T10:30:00Z"
  }
}
```

### 6.4 Vérifier les Logs

Dans les logs de votre backend :
```
INFO: Webhook Wassenger reçu: message:in:new
INFO: Contact trouvé: 22890123456
```

---

## 7. Intégration au Projet

### 7.1 Configurer les Variables d'Environnement

Ajoutez dans `backend/.env` :

```env
# =============================================================================
# WASSENGER API 2025
# =============================================================================
# Clé API (obligatoire)
WASSENGER_API_KEY=wsp_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Device ID (obligatoire)
WASSENGER_DEVICE_ID=64a1b2c3d4e5f6g7h8i9j0k1

# URL du webhook (pour référence)
WASSENGER_WEBHOOK_URL=https://votre-url.ngrok.io/api/webhooks/wassenger
```

### 7.2 Vérifier la Configuration

Lancez le backend et vérifiez qu'il démarre sans erreur :

```bash
cd backend
python -m uvicorn app.main:app --reload
```

Si la configuration est correcte, vous verrez :
```
INFO: Application startup complete.
```

Si une variable est manquante :
```
ERREUR DE CONFIGURATION WASSENGER
Les variables d'environnement suivantes sont obligatoires :
  - WASSENGER_API_KEY
```

### 7.3 Tester l'Intégration Complète

1. Créez une campagne dans le dashboard
2. Envoyez un Message 1
3. Vérifiez :
   - ✅ Le message est reçu sur WhatsApp
   - ✅ Le statut se met à jour (sent → delivered → read)
4. Répondez au message
5. Vérifiez :
   - ✅ L'interaction est enregistrée
   - ✅ Le Message 2 est envoyé automatiquement

### 7.4 Checklist Finale

Avant de passer en production :

- [ ] API Key de production créée
- [ ] Device ID correct configuré
- [ ] Webhook URL de production configurée
- [ ] Tous les événements webhook activés
- [ ] Tests d'envoi réussis
- [ ] Tests de réception réussis
- [ ] Workflow Message 1 → Interaction → Message 2 fonctionnel

---

## 📚 Ressources Supplémentaires

- 📖 [Documentation officielle Wassenger](https://wassenger.com/docs)
- 🔧 [API Reference](https://wassenger.com/docs/api)
- 💬 [Support Wassenger](https://wassenger.com/support)
- 📁 [Guide de lancement du projet](./GUIDE_LANCEMENT_PROJET_WASSENGER_2025.md)

---

*Guide mis à jour : Décembre 2025*
