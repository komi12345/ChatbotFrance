# Guide de Configuration WhatsApp Business API

Ce guide détaille les étapes pour configurer WhatsApp Business API (Meta Cloud API) pour le système de chatbot.

## Table des Matières

1. [Prérequis](#prérequis)
2. [Création du Compte Meta Business](#création-du-compte-meta-business)
3. [Configuration de l'Application Meta](#configuration-de-lapplication-meta)
4. [Obtention des Identifiants API](#obtention-des-identifiants-api)
5. [Création de Templates de Messages](#création-de-templates-de-messages)
6. [Configuration des Webhooks](#configuration-des-webhooks)
7. [Test de l'Intégration](#test-de-lintégration)

---

## Prérequis

- Un compte Facebook personnel
- Un numéro de téléphone pour WhatsApp Business (différent de votre numéro personnel)
- Une entreprise vérifiable (nom, adresse, site web)
- Accès à un serveur avec HTTPS pour les webhooks (ou ngrok pour le développement)

---

## Création du Compte Meta Business

### Étape 1 : Créer un Compte Meta Business

1. Rendez-vous sur [business.facebook.com](https://business.facebook.com)
2. Cliquez sur "Créer un compte"
3. Remplissez les informations de votre entreprise :
   - Nom de l'entreprise
   - Votre nom
   - Adresse email professionnelle
4. Confirmez votre email
5. Complétez les informations de l'entreprise (adresse, site web)

### Étape 2 : Vérifier l'Entreprise (Optionnel mais Recommandé)

La vérification de l'entreprise permet d'augmenter les limites d'envoi de messages.

1. Dans Meta Business Suite, allez dans **Paramètres** > **Centre de sécurité**
2. Cliquez sur "Commencer la vérification"
3. Fournissez les documents requis :
   - Licence commerciale ou extrait Kbis
   - Facture de services publics
   - Relevé bancaire de l'entreprise
4. Attendez la validation (1-5 jours ouvrés)

---

## Configuration de l'Application Meta

### Étape 1 : Créer une Application Meta

1. Rendez-vous sur [developers.facebook.com](https://developers.facebook.com)
2. Connectez-vous avec votre compte Facebook
3. Cliquez sur "Mes applications" > "Créer une application"
4. Sélectionnez "Entreprise" comme type d'application
5. Remplissez les informations :
   - **Nom de l'application** : Chatbot WhatsApp
   - **Email de contact** : votre@email.com
   - **Compte Business** : Sélectionnez votre compte Meta Business
6. Cliquez sur "Créer l'application"

### Étape 2 : Ajouter WhatsApp à l'Application

1. Dans le dashboard de l'application, cliquez sur "Ajouter des produits"
2. Trouvez "WhatsApp" et cliquez sur "Configurer"
3. Acceptez les conditions d'utilisation de WhatsApp Business Platform

### Étape 3 : Configurer un Numéro de Téléphone

1. Dans la section WhatsApp > **Démarrage rapide**
2. Vous avez deux options :
   - **Numéro de test** : Gratuit, limité à 5 destinataires
   - **Numéro professionnel** : Votre propre numéro WhatsApp Business

#### Option A : Utiliser le Numéro de Test (Développement)

1. Meta fournit un numéro de test automatiquement
2. Ajoutez jusqu'à 5 numéros de destinataires pour les tests
3. Cliquez sur "Ajouter un numéro de téléphone" dans la section destinataires
4. Vérifiez chaque numéro par SMS

#### Option B : Ajouter Votre Propre Numéro (Production)

1. Cliquez sur "Ajouter un numéro de téléphone"
2. Entrez le numéro de téléphone (avec indicatif pays)
3. Choisissez la méthode de vérification (SMS ou appel)
4. Entrez le code de vérification
5. Configurez le profil WhatsApp Business :
   - Nom d'affichage
   - Catégorie d'entreprise
   - Description

---

## Obtention des Identifiants API

### Phone Number ID

1. Dans WhatsApp > **Configuration de l'API**
2. Trouvez la section "Numéros de téléphone"
3. Copiez le **Phone Number ID** (format : 123456789012345)

### Access Token

#### Token Temporaire (Développement)

1. Dans WhatsApp > **Configuration de l'API**
2. Cliquez sur "Générer un token d'accès temporaire"
3. Ce token expire après 24 heures

#### Token Permanent (Production)

1. Allez dans **Paramètres de l'application** > **Basique**
2. Notez l'**App ID** et le **App Secret**
3. Créez un utilisateur système :
   - Allez dans Meta Business Suite > **Paramètres** > **Utilisateurs** > **Utilisateurs système**
   - Cliquez sur "Ajouter"
   - Nommez l'utilisateur (ex: "API WhatsApp")
   - Rôle : Admin
4. Générez un token pour l'utilisateur système :
   - Cliquez sur l'utilisateur système créé
   - Cliquez sur "Générer un nouveau token"
   - Sélectionnez l'application
   - Cochez les permissions :
     - `whatsapp_business_management`
     - `whatsapp_business_messaging`
   - Cliquez sur "Générer le token"
5. **Copiez et sauvegardez ce token** - il ne sera plus affiché !

### Webhook Verify Token

C'est un token que vous définissez vous-même pour sécuriser les webhooks :

```bash
# Générez un token aléatoire
python -c "import secrets; print(secrets.token_hex(16))"
```

Exemple : `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`

---

## Création de Templates de Messages

Les templates sont obligatoires pour initier une conversation avec un contact.

### Étape 1 : Accéder au Gestionnaire de Templates

1. Dans WhatsApp > **Gestionnaire de modèles de messages**
2. Cliquez sur "Créer un modèle"

### Étape 2 : Créer un Template

1. **Catégorie** : Choisissez selon votre cas d'usage
   - Marketing : Promotions, offres
   - Utilitaire : Confirmations, rappels
   - Authentification : Codes de vérification

2. **Nom du modèle** : Utilisez des minuscules et underscores
   - Exemple : `campagne_bienvenue`

3. **Langue** : Sélectionnez les langues nécessaires
   - Français (fr)
   - Anglais (en)

4. **Contenu du message** :
   ```
   Bonjour {{1}} !
   
   Merci de votre intérêt pour nos services.
   
   Découvrez nos offres : {{2}}
   
   Répondez à ce message pour plus d'informations.
   ```
   - `{{1}}` : Variable pour le prénom
   - `{{2}}` : Variable pour le lien

5. **Exemples de variables** (requis pour l'approbation) :
   - {{1}} : Jean
   - {{2}} : https://example.com/offres

6. Cliquez sur "Soumettre"

### Étape 3 : Attendre l'Approbation

- Les templates sont examinés par Meta (généralement 24-48h)
- Statuts possibles :
  - **En attente** : En cours d'examen
  - **Approuvé** : Prêt à l'utilisation
  - **Rejeté** : Modifiez et resoumettez

### Bonnes Pratiques pour les Templates

- Évitez le langage promotionnel agressif
- Incluez une option de désabonnement
- Soyez clair sur l'identité de l'expéditeur
- N'utilisez pas de liens raccourcis (bit.ly, etc.)
- Respectez les politiques de Meta

---

## Configuration des Webhooks

Les webhooks permettent de recevoir les messages et interactions des utilisateurs.

### Étape 1 : Préparer l'Endpoint

Votre backend doit exposer un endpoint pour les webhooks :

```
GET  /api/webhooks/whatsapp  → Vérification du webhook
POST /api/webhooks/whatsapp  → Réception des événements
```

### Étape 2 : Exposer le Backend (Développement)

Pour le développement local, utilisez ngrok :

```bash
# Installer ngrok
# Windows : téléchargez depuis ngrok.com
# macOS : brew install ngrok
# Linux : snap install ngrok

# Lancer ngrok
ngrok http 8000
```

Notez l'URL HTTPS fournie (ex: `https://abc123.ngrok.io`)

### Étape 3 : Configurer le Webhook dans Meta

1. Dans WhatsApp > **Configuration**
2. Section "Webhook"
3. Cliquez sur "Modifier"
4. Remplissez :
   - **URL de rappel** : `https://votre-domaine.com/api/webhooks/whatsapp`
   - **Token de vérification** : Le token que vous avez défini dans `.env`
5. Cliquez sur "Vérifier et enregistrer"

### Étape 4 : S'abonner aux Événements

Après la vérification, abonnez-vous aux événements :

1. Cliquez sur "Gérer" à côté de "Champs webhook"
2. Cochez les événements suivants :
   - `messages` : Réception des messages
   - `message_deliveries` : Confirmations de livraison
   - `message_reads` : Confirmations de lecture
   - `message_reactions` : Réactions aux messages
3. Cliquez sur "Terminé"

---

## Test de l'Intégration

### Test 1 : Vérifier les Identifiants

```bash
# Remplacez par vos valeurs
PHONE_NUMBER_ID="votre_phone_number_id"
ACCESS_TOKEN="votre_access_token"

curl -X GET "https://graph.facebook.com/v18.0/$PHONE_NUMBER_ID" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

Réponse attendue :
```json
{
  "id": "123456789012345",
  "display_phone_number": "+33612345678",
  "verified_name": "Votre Entreprise"
}
```

### Test 2 : Envoyer un Message Template

```bash
curl -X POST "https://graph.facebook.com/v18.0/$PHONE_NUMBER_ID/messages" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "messaging_product": "whatsapp",
    "to": "33612345678",
    "type": "template",
    "template": {
      "name": "hello_world",
      "language": {
        "code": "en_US"
      }
    }
  }'
```

Réponse attendue :
```json
{
  "messaging_product": "whatsapp",
  "contacts": [{"wa_id": "33612345678"}],
  "messages": [{"id": "wamid.xxx"}]
}
```

### Test 3 : Vérifier les Webhooks

1. Envoyez un message depuis WhatsApp vers votre numéro Business
2. Vérifiez les logs de votre backend
3. L'interaction doit être enregistrée dans la base de données

---

## Configuration dans le Backend

Mettez à jour votre fichier `.env` :

```env
# WhatsApp Business API
WHATSAPP_PHONE_NUMBER_ID=123456789012345
WHATSAPP_ACCESS_TOKEN=EAAxxxxxxxxxxxxxxx
WHATSAPP_WEBHOOK_VERIFY_TOKEN=votre_token_de_verification
WHATSAPP_API_VERSION=v18.0
```

---

## Limites et Quotas

### Limites de Messages

| Niveau | Messages/24h | Condition |
|--------|-------------|-----------|
| Tier 1 | 1 000 | Nouveau compte |
| Tier 2 | 10 000 | Après vérification |
| Tier 3 | 100 000 | Bon historique |
| Tier 4 | Illimité | Entreprise vérifiée |

### Limites de l'API

- **Rate limit** : 80 requêtes/seconde par numéro
- **Taille des messages** : 4 096 caractères max
- **Médias** : 16 MB max pour les images/vidéos

---

## Dépannage

### Erreur "Invalid OAuth access token"
- Le token a expiré → Générez un nouveau token
- Permissions manquantes → Vérifiez les permissions du token

### Erreur "Phone number not registered"
- Le numéro destinataire n'a pas WhatsApp
- Format incorrect → Utilisez le format international sans "+"

### Webhook non vérifié
- Vérifiez que le token correspond exactement
- Vérifiez que l'endpoint est accessible en HTTPS
- Vérifiez les logs du backend pour les erreurs

### Template rejeté
- Relisez les politiques de Meta
- Évitez le contenu promotionnel agressif
- Ajoutez des exemples de variables clairs

---

## Ressources

- [Documentation officielle WhatsApp Business API](https://developers.facebook.com/docs/whatsapp/cloud-api)
- [Référence des messages](https://developers.facebook.com/docs/whatsapp/cloud-api/reference/messages)
- [Guide des templates](https://developers.facebook.com/docs/whatsapp/message-templates)
- [Webhooks WhatsApp](https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks)
