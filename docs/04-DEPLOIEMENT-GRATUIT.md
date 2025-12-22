# Guide de Déploiement Gratuit - Chatbot WhatsApp

Ce guide détaille les étapes pour déployer le système de chatbot WhatsApp sur des plateformes gratuites ou à faible coût.

**Dernière mise à jour** : Décembre 2025

## Table des Matières

1. [Vue d'Ensemble](#vue-densemble)
2. [Prérequis](#prérequis)
3. [Configuration Redis sur Upstash](#configuration-redis-sur-upstash)
4. [Déploiement du Backend sur Railway](#déploiement-du-backend-sur-railway)
5. [Alternative : Déploiement sur Render](#alternative--déploiement-sur-render)
6. [Déploiement du Frontend sur Vercel](#déploiement-du-frontend-sur-vercel)
7. [Configuration des Webhooks Wassenger](#configuration-des-webhooks-wassenger)
8. [Tests de Bout en Bout](#tests-de-bout-en-bout)
9. [Monitoring et Maintenance](#monitoring-et-maintenance)
10. [Dépannage](#dépannage)

---

## Vue d'Ensemble

### Architecture de Déploiement

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     Vercel      │     │ Railway/Render  │     │    Supabase     │
│   (Frontend)    │────▶│   (Backend)     │────▶│  (PostgreSQL)   │
│   Next.js 16    │     │   FastAPI       │     │                 │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                        ┌────────┴────────┐
                        │                 │
               ┌────────▼────────┐ ┌──────▼──────┐
               │     Upstash     │ │  Wassenger  │
               │     (Redis)     │ │ (WhatsApp)  │
               └─────────────────┘ └─────────────┘
```

### Services Utilisés (Décembre 2025)

| Service | Plateforme | Offre Gratuite/Coût |
|---------|------------|---------------------|
| Frontend | Vercel | Gratuit (Hobby plan) |
| Backend | Railway | $5 crédit unique (compte vérifié) |
| Backend (alt) | Render | Gratuit (750h/mois, mise en veille) |
| Redis | Upstash | Gratuit (10K commandes/jour) |
| Base de données | Supabase | Gratuit (500MB, 2 projets) |
| WhatsApp API | Wassenger | À partir de $19/mois |

> **Note importante** : Railway n'offre plus de plan gratuit 500h/mois depuis 2023. Ils offrent maintenant un crédit unique de $5 pour les comptes vérifiés. Pour un déploiement vraiment gratuit, utilisez Render.

---

## Prérequis

Avant de commencer le déploiement, assurez-vous d'avoir :

### Comptes Requis
- [ ] **GitHub** : Pour héberger votre code source
- [ ] **Supabase** : Base de données PostgreSQL (déjà configurée)
- [ ] **Wassenger** : API WhatsApp (compte actif avec appareil connecté)
- [ ] **Upstash** : Redis serverless (gratuit)
- [ ] **Vercel** : Hébergement frontend (gratuit)
- [ ] **Railway** ou **Render** : Hébergement backend

### Informations à Préparer
Récupérez ces informations avant de commencer :

```
# Supabase (Dashboard > Settings > API)
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Wassenger (Dashboard > Settings > API Keys)
WASSENGER_API_KEY=wsp_live_xxxxxxxxxxxxx
WASSENGER_DEVICE_ID=64a1b2c3d4e5f6g7h8i9j0k1
```

### Générer une Clé Secrète JWT
```bash
# Windows PowerShell
python -c "import secrets; print(secrets.token_hex(32))"

# Ou en ligne : https://generate-secret.vercel.app/32
```

---

## Configuration Redis sur Upstash

Upstash offre un Redis serverless gratuit, idéal pour Celery.

### Étape 1 : Créer un Compte Upstash

1. Rendez-vous sur [upstash.com](https://upstash.com)
2. Créez un compte (gratuit, pas de carte bancaire requise)

### Étape 2 : Créer une Base de Données Redis

1. Cliquez sur "Create Database"
2. Configurez :
   - **Name** : `chatbot-whatsapp-redis`
   - **Region** : `EU-West-1` (ou la plus proche de votre backend)
   - **Type** : Regional (gratuit)
3. Cliquez sur "Create"

### Étape 3 : Récupérer l'URL de Connexion

1. Dans le dashboard Upstash, cliquez sur votre base de données
2. Copiez l'URL complète dans la section "REST API" ou "Redis"
3. Format de l'URL :

```
rediss://default:VOTRE_PASSWORD@VOTRE_ENDPOINT:6379
```

> **Important** : Utilisez `rediss://` (avec deux 's') pour la connexion TLS sécurisée.

### Limites du Plan Gratuit Upstash
- 10 000 commandes par jour
- 256 MB de stockage
- Suffisant pour un usage modéré (~100-200 messages/jour)

---

## Déploiement du Backend sur Railway

Railway est une plateforme simple pour déployer des applications Python.

> **Tarification 2025** : Railway offre un crédit unique de $5 pour les comptes vérifiés. Après épuisement, le plan Hobby coûte $5/mois. Pour un déploiement gratuit, voir la section Render.

### Étape 1 : Créer un Compte Railway

1. Rendez-vous sur [railway.app](https://railway.app)
2. Connectez-vous avec GitHub
3. Vérifiez votre compte (carte bancaire ou GitHub vérifié)

### Étape 2 : Préparer le Projet

Créez les fichiers de configuration dans le dossier `backend/` :

**Fichier `backend/Procfile`** :
```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Fichier `backend/runtime.txt`** :
```
python-3.11.0
```

**Fichier `backend/railway.json`** (optionnel, pour configuration avancée) :
```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### Étape 3 : Déployer sur Railway

1. Dans Railway, cliquez sur "New Project"
2. Sélectionnez "Deploy from GitHub repo"
3. Autorisez l'accès à votre repository
4. Sélectionnez le repository
5. Dans les paramètres, définissez le **Root Directory** : `backend`

### Étape 4 : Configurer les Variables d'Environnement

Dans Railway > Variables, ajoutez :

```env
# Environnement
ENVIRONMENT=production
DEBUG=False

# Supabase
SUPABASE_URL=https://votre-projet.supabase.co
SUPABASE_KEY=votre_anon_key
SUPABASE_SERVICE_ROLE_KEY=votre_service_role_key

# Wassenger (WhatsApp)
WASSENGER_API_KEY=wsp_live_xxxxxxxxxxxxx
WASSENGER_DEVICE_ID=votre_device_id
WASSENGER_WEBHOOK_URL=https://votre-app.up.railway.app/api/webhooks/wassenger

# Redis (Upstash)
REDIS_URL=rediss://default:password@endpoint.upstash.io:6379

# JWT
SECRET_KEY=votre_cle_secrete_production_minimum_32_caracteres
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS (URL de votre frontend Vercel)
ALLOWED_ORIGINS=https://votre-app.vercel.app

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100
```

### Étape 5 : Ajouter le Service Redis (Optionnel)

Si vous préférez Redis sur Railway plutôt qu'Upstash :

1. Dans votre projet Railway, cliquez sur "New" > "Database" > "Redis"
2. Railway créera automatiquement la variable `REDIS_URL`

### Étape 6 : Déployer le Worker Celery

Pour les tâches asynchrones (envoi de messages), vous avez deux options :

**Option A : Service séparé (recommandé pour production)**
1. Dans votre projet Railway, cliquez sur "New Service"
2. Sélectionnez le même repository GitHub
3. Définissez le **Root Directory** : `backend`
4. Dans Settings > Deploy, changez la commande :
   ```
   celery -A app.tasks.celery_app worker --loglevel=info --concurrency=2
   ```
5. Ajoutez les mêmes variables d'environnement

**Option B : Procfile multi-process (économique)**
Modifiez le `Procfile` :
```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT & celery -A app.tasks.celery_app worker --loglevel=info --concurrency=1
```

### Étape 7 : Obtenir l'URL du Backend

1. Dans Railway > Settings > Networking
2. Cliquez sur "Generate Domain"
3. Notez l'URL : `https://votre-app.up.railway.app`

---

## Alternative : Déploiement sur Render

Render offre un plan gratuit avec 750 heures/mois, idéal pour commencer.

> **Avantage** : Vraiment gratuit, pas de carte bancaire requise.
> **Inconvénient** : Le service se met en veille après 15 minutes d'inactivité (démarrage ~30s).

### Étape 1 : Créer un Compte Render

1. Rendez-vous sur [render.com](https://render.com)
2. Connectez-vous avec GitHub (pas de carte bancaire requise)

### Étape 2 : Créer un Web Service

1. Cliquez sur "New" > "Web Service"
2. Connectez votre repository GitHub
3. Configurez le service :
   - **Name** : `chatbot-whatsapp-api`
   - **Region** : `Frankfurt (EU Central)` ou `Oregon (US West)`
   - **Branch** : `main`
   - **Root Directory** : `backend`
   - **Runtime** : `Python 3`
   - **Build Command** : `pip install -r requirements.txt`
   - **Start Command** : `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type** : `Free`

### Étape 3 : Configurer les Variables d'Environnement

Dans Render > Environment, ajoutez les mêmes variables que pour Railway :

```env
ENVIRONMENT=production
DEBUG=False
SUPABASE_URL=https://votre-projet.supabase.co
SUPABASE_KEY=votre_anon_key
SUPABASE_SERVICE_ROLE_KEY=votre_service_role_key
WASSENGER_API_KEY=wsp_live_xxxxxxxxxxxxx
WASSENGER_DEVICE_ID=votre_device_id
WASSENGER_WEBHOOK_URL=https://votre-app.onrender.com/api/webhooks/wassenger
REDIS_URL=rediss://default:password@endpoint.upstash.io:6379
SECRET_KEY=votre_cle_secrete_32_caracteres
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
ALLOWED_ORIGINS=https://votre-app.vercel.app
RATE_LIMIT_PER_MINUTE=100
```

### Étape 4 : Créer un Background Worker pour Celery

1. Cliquez sur "New" > "Background Worker"
2. Même repository et configuration
3. **Root Directory** : `backend`
4. **Build Command** : `pip install -r requirements.txt`
5. **Start Command** : `celery -A app.tasks.celery_app worker --loglevel=info --concurrency=1`
6. **Instance Type** : `Free`
7. Ajoutez les mêmes variables d'environnement

### Étape 5 : Éviter la Mise en Veille (Optionnel)

Pour éviter que le service ne se mette en veille :

1. Créez un compte sur [UptimeRobot](https://uptimerobot.com) (gratuit)
2. Ajoutez un moniteur HTTP(s) :
   - **URL** : `https://votre-app.onrender.com/api/health`
   - **Intervalle** : 5 minutes
3. Cela enverra un ping régulier pour garder le service actif

### Note sur les Limites Render

- 750 heures gratuites par mois (suffisant pour 1 service 24/7)
- Si vous avez 2 services (web + worker), ils partagent les 750h
- Le premier appel après la veille prend ~30 secondes

---

## Déploiement du Frontend sur Vercel

Vercel est la plateforme idéale pour Next.js (créée par les mêmes développeurs).

> **Plan Hobby** : Gratuit, parfait pour les projets personnels et petites équipes.

### Étape 1 : Créer un Compte Vercel

1. Rendez-vous sur [vercel.com](https://vercel.com)
2. Connectez-vous avec GitHub (pas de carte bancaire requise)

### Étape 2 : Importer le Projet

1. Cliquez sur "Add New" > "Project"
2. Importez votre repository GitHub
3. Configurez :
   - **Framework Preset** : Next.js (détecté automatiquement)
   - **Root Directory** : `frontend`
   - **Build Command** : `npm run build` (par défaut)
   - **Output Directory** : `.next` (par défaut)
   - **Install Command** : `npm install` (par défaut)

### Étape 3 : Configurer les Variables d'Environnement

Dans Vercel > Settings > Environment Variables, ajoutez :

```env
# URL de votre backend (Railway ou Render)
NEXT_PUBLIC_API_URL=https://votre-backend.up.railway.app/api

# Supabase (mêmes valeurs que le backend)
NEXT_PUBLIC_SUPABASE_URL=https://votre-projet.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=votre_anon_key
```

> **Important** : Les variables `NEXT_PUBLIC_*` sont exposées côté client. N'y mettez jamais de secrets !

### Étape 4 : Déployer

1. Cliquez sur "Deploy"
2. Attendez la fin du build (~2-3 minutes)
3. Notez l'URL de production : `https://votre-app.vercel.app`

### Étape 5 : Mettre à Jour le CORS du Backend

Après avoir obtenu l'URL Vercel, mettez à jour la variable `ALLOWED_ORIGINS` dans votre backend :

```env
ALLOWED_ORIGINS=https://votre-app.vercel.app
```

Redéployez le backend pour appliquer le changement.

### Étape 6 : Configurer un Domaine Personnalisé (Optionnel)

1. Dans Vercel > Settings > Domains
2. Ajoutez votre domaine personnalisé
3. Configurez les DNS selon les instructions Vercel
4. Vercel génère automatiquement un certificat SSL

### Limites du Plan Hobby Vercel

- Builds illimités
- Bande passante : 100 GB/mois
- Fonctions serverless : 100 GB-heures/mois
- Pas de support commercial

---

## Configuration des Webhooks Wassenger

Les webhooks permettent de recevoir les notifications de statut des messages et les messages entrants.

### Étape 1 : Obtenir l'URL du Webhook

Votre URL de webhook est :
```
https://votre-backend.up.railway.app/api/webhooks/wassenger
```
ou
```
https://votre-backend.onrender.com/api/webhooks/wassenger
```

### Étape 2 : Configurer dans Wassenger

1. Connectez-vous à [app.wassenger.com](https://app.wassenger.com)
2. Allez dans **Settings** > **Webhooks**
3. Cliquez sur "Add Webhook"
4. Configurez :
   - **URL** : `https://votre-backend.up.railway.app/api/webhooks/wassenger`
   - **Events** : Sélectionnez tous les événements pertinents :
     - ✅ `message:in` (messages entrants)
     - ✅ `message:out` (messages sortants)
     - ✅ `message:status` (statuts de livraison)
     - ✅ `message:ack` (accusés de réception)
5. Cliquez sur "Save"

### Étape 3 : Mettre à Jour la Variable d'Environnement

Dans votre backend (Railway/Render), mettez à jour :
```env
WASSENGER_WEBHOOK_URL=https://votre-backend.up.railway.app/api/webhooks/wassenger
```

### Étape 4 : Tester le Webhook

```bash
# Vérifier que l'endpoint répond
curl -X GET "https://votre-backend.up.railway.app/api/webhooks/wassenger"

# Réponse attendue : {"status": "ok"} ou similaire
```

### Événements Webhook Supportés

| Événement | Description |
|-----------|-------------|
| `message:in` | Message reçu d'un contact |
| `message:out` | Message envoyé confirmé |
| `message:status` | Changement de statut (sent, delivered, read) |
| `message:ack` | Accusé de réception |

---

## Tests de Bout en Bout

### Test 1 : Vérifier le Backend

```bash
# Vérifier que l'API répond
curl "https://votre-backend.up.railway.app/api/health"

# Réponse attendue : {"status": "healthy"} ou {"detail": "Not Found"} (OK aussi)
```

### Test 2 : Authentification

```bash
# Connexion avec le Super Admin
curl -X POST "https://votre-backend.up.railway.app/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "superadmin@example.com", "password": "votre_mot_de_passe"}'

# Réponse attendue : {"access_token": "...", "token_type": "bearer", ...}
```

### Test 3 : Accès au Dashboard

1. Ouvrez `https://votre-app.vercel.app`
2. Connectez-vous avec les identifiants Super Admin
3. Vérifiez que le dashboard s'affiche correctement
4. Vérifiez que les données (contacts, catégories) se chargent

### Test 4 : Création de Données

1. Créez une catégorie de test
2. Ajoutez un contact (votre numéro de téléphone)
3. Vérifiez que les données apparaissent dans la liste

### Test 5 : Envoi de Message

1. Créez une campagne de test
2. Sélectionnez votre contact
3. Lancez l'envoi
4. Vérifiez :
   - Les logs du backend (Railway/Render)
   - La réception du message sur WhatsApp
   - Le statut de la campagne passe à "completed"

### Test 6 : Réception de Webhook

1. Répondez au message WhatsApp reçu
2. Vérifiez dans le dashboard :
   - L'interaction est enregistrée
   - Le compteur d'interactions augmente
3. Si configuré, vérifiez que le Message 2 est envoyé

### Checklist de Validation

- [ ] Backend accessible et répond
- [ ] Frontend accessible et affiche la page de login
- [ ] Authentification fonctionne
- [ ] Connexion à Supabase OK (données chargées)
- [ ] Worker Celery actif (messages envoyés)
- [ ] Webhook Wassenger configuré
- [ ] Test d'envoi de message réussi
- [ ] Test de réception de webhook réussi

---

## Monitoring et Maintenance

### Logs sur Railway

**Via le Dashboard :**
1. Allez dans votre projet Railway
2. Cliquez sur le service
3. Onglet "Logs" pour voir les logs en temps réel

**Via CLI (optionnel) :**
```bash
# Installer Railway CLI
npm install -g @railway/cli

# Se connecter
railway login

# Voir les logs
railway logs
```

### Logs sur Render

1. Dans le dashboard Render
2. Cliquez sur votre service
3. Onglet "Logs"

### Logs sur Vercel

1. Dans le dashboard Vercel
2. Cliquez sur votre projet
3. Onglet "Logs" > "Runtime Logs"

### Monitoring Uptime avec UptimeRobot

[UptimeRobot](https://uptimerobot.com) est gratuit et permet de :
- Surveiller la disponibilité 24/7
- Éviter la mise en veille (Render)
- Recevoir des alertes par email/SMS

**Configuration :**
1. Créez un compte UptimeRobot (gratuit)
2. Ajoutez un moniteur HTTP(s) :
   - **Friendly Name** : Chatbot WhatsApp API
   - **URL** : `https://votre-backend.up.railway.app/api/health`
   - **Monitoring Interval** : 5 minutes
3. Configurez les alertes (email)

### Sauvegardes Supabase

Supabase effectue des sauvegardes automatiques quotidiennes (plan gratuit : 7 jours de rétention).

**Export manuel :**
```bash
# Via pg_dump (nécessite PostgreSQL installé)
pg_dump "postgresql://postgres:password@db.xxx.supabase.co:5432/postgres" > backup_$(date +%Y%m%d).sql
```

### Mise à Jour du Projet

Pour déployer une nouvelle version :

**Railway/Render :**
- Push sur la branche `main` → déploiement automatique

**Vercel :**
- Push sur la branche `main` → déploiement automatique
- Preview deployments sur les autres branches

---

## Dépannage

### Le Backend ne Démarre Pas

**Symptôme** : Erreur 503 ou timeout

**Solutions** :
1. Vérifiez les logs dans Railway/Render
2. Vérifiez que toutes les variables d'environnement sont définies
3. Vérifiez la connexion à Supabase :
   ```bash
   curl "https://votre-projet.supabase.co/rest/v1/" \
     -H "apikey: votre_anon_key"
   ```
4. Vérifiez la connexion à Redis/Upstash

### Erreur CORS

**Symptôme** : `Access-Control-Allow-Origin` error dans la console

**Solutions** :
1. Vérifiez `ALLOWED_ORIGINS` dans le backend
2. Assurez-vous que l'URL Vercel est exacte (avec `https://`, sans `/` final)
3. Redéployez le backend après modification
4. Exemple correct :
   ```env
   ALLOWED_ORIGINS=https://votre-app.vercel.app
   ```

### Celery ne Traite Pas les Tâches

**Symptôme** : Messages restent en "pending", campagne bloquée

**Solutions** :
1. Vérifiez que le worker Celery est démarré (logs)
2. Vérifiez la connexion à Redis :
   ```bash
   # Test de connexion Redis
   redis-cli -u "rediss://default:password@endpoint.upstash.io:6379" ping
   ```
3. Vérifiez les logs du worker pour les erreurs
4. Assurez-vous que `REDIS_URL` utilise `rediss://` (avec TLS)

### Messages Non Envoyés

**Symptôme** : Campagne "completed" mais pas de messages reçus

**Solutions** :
1. Vérifiez les logs Celery pour les erreurs Wassenger
2. Vérifiez que `WASSENGER_API_KEY` est valide
3. Vérifiez que `WASSENGER_DEVICE_ID` correspond à un appareil connecté
4. Testez l'API Wassenger directement :
   ```bash
   curl -X GET "https://api.wassenger.com/v1/devices" \
     -H "Token: votre_api_key"
   ```

### Webhook Non Reçu

**Symptôme** : Interactions non enregistrées, Message 2 non envoyé

**Solutions** :
1. Vérifiez que l'URL webhook est accessible publiquement
2. Vérifiez la configuration dans Wassenger Dashboard
3. Testez l'endpoint manuellement :
   ```bash
   curl -X POST "https://votre-backend.up.railway.app/api/webhooks/wassenger" \
     -H "Content-Type: application/json" \
     -d '{"event": "test"}'
   ```
4. Vérifiez les logs du backend pour les requêtes entrantes

### Frontend ne Charge Pas les Données

**Symptôme** : Spinner infini, erreurs réseau

**Solutions** :
1. Ouvrez les DevTools (F12) > Network
2. Vérifiez les requêtes vers l'API
3. Si erreur 401 : token expiré, reconnectez-vous
4. Si erreur 500 : vérifiez les logs backend
5. Si erreur CORS : voir section CORS ci-dessus

### Build Vercel Échoue

**Symptôme** : Déploiement échoue avec erreurs TypeScript

**Solutions** :
1. Vérifiez les logs de build dans Vercel
2. Testez le build localement :
   ```bash
   cd frontend
   npm run build
   ```
3. Le projet est configuré pour ignorer les erreurs TypeScript (`ignoreBuildErrors: true`)
4. Si erreurs de dépendances : supprimez `node_modules` et `package-lock.json`, puis `npm install`

---

## Coûts Estimés (Décembre 2025)

### Option 1 : Gratuit avec Render

| Service | Coût | Limite |
|---------|------|--------|
| Vercel (Frontend) | $0 | Hobby plan |
| Render (Backend) | $0 | 750h/mois, mise en veille |
| Render (Worker) | $0 | Partage les 750h |
| Upstash (Redis) | $0 | 10K cmd/jour |
| Supabase (DB) | $0 | 500MB, 2 projets |
| Wassenger | ~$19/mois | Plan de base |
| **Total** | **~$19/mois** | |

### Option 2 : Railway (Plus Fiable)

| Service | Coût | Avantages |
|---------|------|-----------|
| Vercel (Frontend) | $0 | Hobby plan |
| Railway (Backend + Worker) | $5-10/mois | Pas de mise en veille |
| Upstash (Redis) | $0 | 10K cmd/jour |
| Supabase (DB) | $0 | 500MB |
| Wassenger | ~$19/mois | Plan de base |
| **Total** | **~$24-29/mois** | |

### Option 3 : Production (Recommandé)

| Service | Coût | Avantages |
|---------|------|-----------|
| Vercel Pro | $20/mois | Analytics, support |
| Railway | $20/mois | Plus de ressources |
| Upstash Pro | $10/mois | Plus de commandes |
| Supabase Pro | $25/mois | Plus de stockage, backups |
| Wassenger | ~$49/mois | Plus de messages |
| **Total** | **~$124/mois** | |

---

## Ressources

- [Documentation Railway](https://docs.railway.app)
- [Documentation Render](https://render.com/docs)
- [Documentation Vercel](https://vercel.com/docs)
- [Documentation Upstash](https://docs.upstash.com)
- [Documentation Supabase](https://supabase.com/docs)
- [Documentation Wassenger](https://wassenger.com/docs)
- [UptimeRobot](https://uptimerobot.com) - Monitoring gratuit

---

## Récapitulatif des URLs

Après déploiement, vous aurez :

| Service | URL |
|---------|-----|
| Frontend | `https://votre-app.vercel.app` |
| Backend API | `https://votre-app.up.railway.app/api` |
| Webhook Wassenger | `https://votre-app.up.railway.app/api/webhooks/wassenger` |
| Supabase | `https://votre-projet.supabase.co` |

---

**Guide mis à jour le** : Décembre 2025
