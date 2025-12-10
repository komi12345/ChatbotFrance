# Guide de Migration - WhatsApp Meta Cloud API vers Gupshup 2025

> ⚠️ **OBSOLÈTE** : Ce guide est obsolète. L'intégration Gupshup a été remplacée par Twilio WhatsApp Sandbox.
> Consultez la documentation de configuration Twilio pour la nouvelle intégration.
> Date de migration : Décembre 2025

Ce guide détaille les étapes pour migrer l'intégration WhatsApp de Meta Cloud API vers Gupshup API (version 2025).

## Table des Matières

1. [Vue d'Ensemble](#vue-densemble)
2. [Différences Meta vs Gupshup](#différences-meta-vs-gupshup)
3. [Prérequis](#prérequis)
4. [Configuration des Variables d'Environnement](#configuration-des-variables-denvironnement)
5. [Configuration du Webhook Gupshup](#configuration-du-webhook-gupshup)
6. [Création de Templates sur Gupshup Dashboard](#création-de-templates-sur-gupshup-dashboard)
7. [Test de l'Intégration](#test-de-lintégration)
8. [Erreurs Communes et Solutions](#erreurs-communes-et-solutions)
9. [Référence API Gupshup](#référence-api-gupshup)

---

## Vue d'Ensemble

### Pourquoi Migrer vers Gupshup ?

Gupshup est un fournisseur officiel de WhatsApp Business API qui offre :
- Une interface simplifiée pour l'envoi de messages
- Un dashboard intuitif pour la gestion des templates
- Un support technique dédié
- Des tarifs compétitifs

### Architecture Après Migration

```
Dashboard Admin (Next.js 14+)
         ↕
API REST Backend Python (FastAPI)
         ↕
Gupshup API (2025) ← NOUVELLE INTÉGRATION
         ↕
WhatsApp Business Platform
         ↕
Base de données Supabase (PostgreSQL)
```

### Informations du Compte Gupshup

- **Application Name** : newsteck
- **WhatsApp Phone Number** : +33 7 53 11 72 15 (33753117215)
- **Customer ID** : 4000322028
- **API Endpoint** : https://api.gupshup.io/sm/api/v1
- **Status** : Live (Actif)
- **Tier** : BM Level (250 Customers/24 Hrs)

---

## Différences Meta vs Gupshup

### Tableau Comparatif

| Aspect | Meta Cloud API | Gupshup API 2025 |
|--------|---------------|------------------|
| **Authentification** | Bearer Token (`Authorization: Bearer xxx`) | Header apikey (`apikey: xxx`) |
| **Format requête** | JSON (`application/json`) | x-www-form-urlencoded |
| **Format numéro** | Avec + (`+33612345678`) | Sans + (`33612345678`) |
| **Endpoint template** | `POST /messages` | `POST /template/msg` |
| **Endpoint texte** | `POST /messages` | `POST /msg` |
| **Webhook format** | Nested (`entry.changes.value`) | Flat (`type`, `mobile`, `text`) |
| **Réponse succès** | `{"messages": [{"id": "..."}]}` | `{"status": "submitted", "messageId": "..."}` |

### Exemples de Requêtes

#### Envoi de Template - Meta (Ancien)

```bash
curl -X POST "https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages" \
  -H "Authorization: Bearer {ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "messaging_product": "whatsapp",
    "to": "33612345678",
    "type": "template",
    "template": {
      "name": "hello_world",
      "language": {"code": "fr"}
    }
  }'
```

#### Envoi de Template - Gupshup (Nouveau)

```bash
curl -X POST "https://api.gupshup.io/sm/api/v1/template/msg" \
  -H "apikey: {GUPSHUP_API_KEY}" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "channel=whatsapp&source=33753117215&destination=33612345678&template={\"id\":\"hello_world\",\"params\":[]}&src.name=newsteck"
```

### Format des Webhooks

#### Webhook Message - Meta (Ancien)

```json
{
  "object": "whatsapp_business_account",
  "entry": [{
    "changes": [{
      "value": {
        "messages": [{
          "from": "33612345678",
          "text": {"body": "Bonjour"},
          "id": "wamid.xxx"
        }]
      }
    }]
  }]
}
```

#### Webhook Message - Gupshup (Nouveau)

```json
{
  "type": "message",
  "mobile": "33612345678",
  "text": "Bonjour",
  "messageId": "gBEGVzU...",
  "timestamp": 1234567890,
  "name": "Jean Dupont"
}
```

#### Webhook Statut - Gupshup

```json
{
  "type": "message-event",
  "eventType": "delivered",
  "externalId": "msg_123",
  "messageId": "gBEGVzU...",
  "destAddr": "33612345678"
}
```

---

## Prérequis

Avant de commencer la migration, assurez-vous d'avoir :

1. **Compte Gupshup actif** avec accès au dashboard
2. **Application WhatsApp** créée et approuvée sur Gupshup
3. **Numéro WhatsApp Business** vérifié et actif
4. **API Key Gupshup** générée depuis le dashboard
5. **Templates** créés et approuvés sur Gupshup Dashboard

### Obtenir vos Identifiants Gupshup

1. Connectez-vous à [Gupshup Dashboard](https://www.gupshup.io/developer/home)
2. Allez dans **Settings** > **API Keys**
3. Copiez votre **API Key**
4. Allez dans **WhatsApp** > **App Settings**
5. Notez le **App Name** et le **Phone Number**

---

## Configuration des Variables d'Environnement

### Étape 1 : Mettre à jour le fichier .env

Ouvrez `backend/.env` et ajoutez/modifiez les variables suivantes :

```env
# =============================================================================
# GUPSHUP API (2025) - NOUVELLE INTÉGRATION
# =============================================================================

# Clé API Gupshup (OBLIGATOIRE)
# Trouvez-la dans : Gupshup Dashboard > Settings > API Keys
GUPSHUP_API_KEY=votre_cle_api_gupshup

# Nom de l'application Gupshup (OBLIGATOIRE)
# Trouvez-le dans : Gupshup Dashboard > WhatsApp > App Settings
GUPSHUP_APP_NAME=newsteck

# Numéro de téléphone WhatsApp (OBLIGATOIRE)
# Format : sans le caractère "+" (ex: 33753117215)
GUPSHUP_PHONE_NUMBER=33753117215

# URL de base de l'API Gupshup
GUPSHUP_API_URL=https://api.gupshup.io/sm/api/v1

# ID Client Gupshup (optionnel)
GUPSHUP_CUSTOMER_ID=4000322028
```

### Étape 2 : Vérifier la Configuration

Exécutez le script de vérification :

```bash
cd backend
python -c "
from app.config import settings
print('=== Configuration Gupshup ===')
print(f'API Key: {settings.GUPSHUP_API_KEY[:10]}...' if settings.GUPSHUP_API_KEY else 'NON CONFIGURÉ')
print(f'App Name: {settings.GUPSHUP_APP_NAME}')
print(f'Phone Number: {settings.GUPSHUP_PHONE_NUMBER}')
print(f'API URL: {settings.GUPSHUP_API_URL}')
print('Configuration OK!' if settings.GUPSHUP_API_KEY else 'ERREUR: API Key manquante')
"
```

### Variables Anciennes (Meta)

Les anciennes variables Meta peuvent être conservées pour référence mais ne sont plus utilisées :

```env
# DÉPRÉCIÉ - Anciennes variables Meta (peuvent être supprimées)
# WHATSAPP_PHONE_NUMBER_ID=...
# WHATSAPP_ACCESS_TOKEN=...
# WHATSAPP_WEBHOOK_VERIFY_TOKEN=...
```

---

## Configuration du Webhook Gupshup

### Étape 1 : Préparer l'URL du Webhook

Le backend expose un endpoint pour recevoir les webhooks Gupshup :

```
POST /api/webhooks/gupshup
```

#### URL en Développement (avec ngrok)

```bash
# Lancer ngrok
ngrok http 8000

# Exemple d'URL générée
https://abc123.ngrok.io/api/webhooks/gupshup
```

#### URL en Production

```
https://votre-api.com/api/webhooks/gupshup
```

### Étape 2 : Configurer le Webhook sur Gupshup Dashboard

1. Connectez-vous à [Gupshup Dashboard](https://www.gupshup.io/developer/home)
2. Allez dans **WhatsApp** > **App Settings**
3. Section **Webhook Configuration**
4. Entrez l'URL de votre webhook :
   - **Callback URL** : `https://votre-domaine.com/api/webhooks/gupshup`
5. Cliquez sur **Save**

### Étape 3 : Vérifier la Réception des Webhooks

Envoyez un message test depuis WhatsApp vers votre numéro Business et vérifiez les logs :

```bash
# Voir les logs du backend
tail -f backend/logs/app.log
```

Vous devriez voir :
```
INFO - Webhook Gupshup parsé: 1 interaction(s) extraite(s)
```

---

## Création de Templates sur Gupshup Dashboard

### Étape 1 : Accéder au Gestionnaire de Templates

1. Connectez-vous à [Gupshup Dashboard](https://www.gupshup.io/developer/home)
2. Allez dans **WhatsApp** > **Templates**
3. Cliquez sur **Create Template**

### Étape 2 : Créer un Template

1. **Template Name** : Utilisez des minuscules et underscores
   - Exemple : `campagne_bienvenue`

2. **Category** : Choisissez selon votre cas d'usage
   - **Marketing** : Promotions, offres
   - **Utility** : Confirmations, rappels
   - **Authentication** : Codes de vérification

3. **Language** : Sélectionnez la langue
   - French (fr)
   - English (en)

4. **Body** : Rédigez le contenu du message
   ```
   Bonjour {{1}} !
   
   Merci de votre intérêt pour nos services.
   
   Découvrez nos offres : {{2}}
   
   Répondez à ce message pour plus d'informations.
   ```

5. **Sample Values** : Fournissez des exemples pour chaque variable
   - {{1}} : Jean
   - {{2}} : https://example.com/offres

6. Cliquez sur **Submit for Approval**

### Étape 3 : Attendre l'Approbation

- Les templates sont examinés par WhatsApp (généralement 24-48h)
- Statuts possibles :
  - **Pending** : En cours d'examen
  - **Approved** : Prêt à l'utilisation
  - **Rejected** : Modifiez et resoumettez

### Bonnes Pratiques pour les Templates

- ✅ Soyez clair sur l'identité de l'expéditeur
- ✅ Incluez une option de désabonnement si nécessaire
- ✅ Utilisez un langage professionnel
- ❌ Évitez le langage promotionnel agressif
- ❌ N'utilisez pas de liens raccourcis (bit.ly, etc.)
- ❌ Ne promettez pas de gains financiers

### Utiliser un Template dans le Code

```python
from app.services.gupshup_service import gupshup_service

# Envoi d'un template avec paramètres
result = await gupshup_service.send_template_message(
    phone="+33612345678",
    template_name="campagne_bienvenue",
    params=["Jean", "https://example.com/offres"]
)

if result.success:
    print(f"Message envoyé, ID: {result.message_id}")
else:
    print(f"Erreur: {result.error_message}")
```

---

## Test de l'Intégration

### Test 1 : Vérifier la Connexion API

```bash
curl -X GET "https://api.gupshup.io/sm/api/v1/users/me" \
  -H "apikey: VOTRE_API_KEY"
```

Réponse attendue :
```json
{
  "status": "success",
  "user": {
    "name": "Votre Nom",
    "email": "votre@email.com"
  }
}
```

### Test 2 : Envoyer un Message Template

```bash
curl -X POST "https://api.gupshup.io/sm/api/v1/template/msg" \
  -H "apikey: VOTRE_API_KEY" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "channel=whatsapp" \
  -d "source=33753117215" \
  -d "destination=33612345678" \
  -d 'template={"id":"hello_world","params":[]}' \
  -d "src.name=newsteck"
```

Réponse attendue :
```json
{
  "status": "submitted",
  "messageId": "gBEGVzU..."
}
```

### Test 3 : Envoyer un Message Texte

```bash
curl -X POST "https://api.gupshup.io/sm/api/v1/msg" \
  -H "apikey: VOTRE_API_KEY" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "channel=whatsapp" \
  -d "source=33753117215" \
  -d "destination=33612345678" \
  -d 'message={"type":"text","text":"Bonjour, ceci est un test !"}' \
  -d "src.name=newsteck"
```

### Test 4 : Vérifier les Webhooks

1. Envoyez un message depuis WhatsApp vers votre numéro Business
2. Vérifiez que le webhook est reçu dans les logs
3. Vérifiez que l'interaction est enregistrée en base de données

---

## Erreurs Communes et Solutions

### Erreur 401 - Unauthorized

**Symptôme** :
```json
{"status": "error", "message": "Invalid API key"}
```

**Solutions** :
- Vérifiez que `GUPSHUP_API_KEY` est correctement configuré
- Vérifiez que la clé API n'a pas expiré
- Régénérez une nouvelle clé API si nécessaire

### Erreur 400 - Bad Request

**Symptôme** :
```json
{"status": "error", "message": "Invalid request format"}
```

**Solutions** :
- Vérifiez que le Content-Type est `application/x-www-form-urlencoded`
- Vérifiez que le numéro de téléphone est au bon format (sans +)
- Vérifiez que le JSON du template est valide

### Erreur 429 - Rate Limit Exceeded

**Symptôme** :
```json
{"status": "error", "message": "Rate limit exceeded"}
```

**Solutions** :
- Respectez la limite de 25 messages par minute
- Implémentez un délai entre les envois (2.4 secondes minimum)
- Utilisez les tâches Celery pour l'envoi massif

### Erreur "Template not found"

**Symptôme** :
```json
{"status": "error", "message": "Template not found or not approved"}
```

**Solutions** :
- Vérifiez que le nom du template est exact (sensible à la casse)
- Vérifiez que le template est approuvé sur Gupshup Dashboard
- Attendez l'approbation si le template est en "Pending"

### Webhook non reçu

**Solutions** :
- Vérifiez que l'URL du webhook est accessible publiquement (HTTPS)
- Vérifiez la configuration du webhook sur Gupshup Dashboard
- Vérifiez les logs du backend pour les erreurs
- Testez avec ngrok en développement

### Numéro de téléphone invalide

**Symptôme** :
```json
{"status": "error", "message": "Invalid destination number"}
```

**Solutions** :
- Utilisez le format international sans + (ex: 33612345678)
- Vérifiez que le numéro a WhatsApp installé
- Vérifiez que le numéro n'est pas bloqué

### Message non délivré

**Solutions** :
- Vérifiez le statut du message via les webhooks
- Le destinataire doit avoir WhatsApp installé
- Le destinataire doit avoir accepté les messages de votre numéro Business
- Vérifiez les limites de votre tier Gupshup

---

## Référence API Gupshup

### Endpoints Principaux

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/template/msg` | POST | Envoi de message template |
| `/msg` | POST | Envoi de message texte |
| `/users/me` | GET | Informations du compte |

### Headers Requis

```
apikey: VOTRE_API_KEY
Content-Type: application/x-www-form-urlencoded
```

### Paramètres Communs

| Paramètre | Description | Exemple |
|-----------|-------------|---------|
| `channel` | Canal de communication | `whatsapp` |
| `source` | Numéro source (sans +) | `33753117215` |
| `destination` | Numéro destinataire (sans +) | `33612345678` |
| `src.name` | Nom de l'application | `newsteck` |

### Format du Template

```json
{
  "id": "nom_du_template",
  "params": ["param1", "param2"]
}
```

### Format du Message Texte

```json
{
  "type": "text",
  "text": "Contenu du message"
}
```

### Codes de Réponse

| Code | Status | Description |
|------|--------|-------------|
| 200 | submitted | Message envoyé avec succès |
| 400 | error | Requête invalide |
| 401 | error | Authentification échouée |
| 429 | error | Rate limit dépassé |
| 500 | error | Erreur serveur Gupshup |

---

## Ressources

- [Documentation Gupshup WhatsApp API](https://docs.gupshup.io/docs/whatsapp-api-documentation)
- [Gupshup Dashboard](https://www.gupshup.io/developer/home)
- [Guide des Templates WhatsApp](https://docs.gupshup.io/docs/template-messages)
- [Webhooks Gupshup](https://docs.gupshup.io/docs/webhooks)
- [Support Gupshup](https://www.gupshup.io/support)

---

## Checklist de Migration

- [ ] Créer un compte Gupshup et obtenir l'API Key
- [ ] Configurer les variables d'environnement dans `.env`
- [ ] Créer et faire approuver les templates sur Gupshup Dashboard
- [ ] Configurer l'URL du webhook sur Gupshup Dashboard
- [ ] Tester l'envoi d'un message template
- [ ] Tester l'envoi d'un message texte
- [ ] Vérifier la réception des webhooks
- [ ] Tester le flux complet : Campagne → Envoi → Webhook → Message 2
- [ ] Vérifier les statistiques et le dashboard
- [ ] Archiver l'ancien service `whatsapp_service.py`
