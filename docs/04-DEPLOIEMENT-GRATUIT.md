# Guide de Déploiement Gratuit - Chatbot WhatsApp

Ce guide détaille les étapes pour déployer le système de chatbot WhatsApp sur des plateformes gratuites.

## Table des Matières

1. [Vue d'Ensemble](#vue-densemble)
2. [Déploiement du Backend sur Railway](#déploiement-du-backend-sur-railway)
3. [Alternative : Déploiement sur Render](#alternative--déploiement-sur-render)
4. [Configuration Redis sur Upstash](#configuration-redis-sur-upstash)
5. [Déploiement du Frontend sur Vercel](#déploiement-du-frontend-sur-vercel)
6. [Configuration des Webhooks en Production](#configuration-des-webhooks-en-production)
7. [Tests de Bout en Bout](#tests-de-bout-en-bout)
8. [Monitoring et Maintenance](#monitoring-et-maintenance)

---

## Vue d'Ensemble

### Architecture de Déploiement

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     Vercel      │     │ Railway/Render  │     │    Supabase     │
│   (Frontend)    │────▶│   (Backend)     │────▶│  (PostgreSQL)   │
│   Next.js       │     │   FastAPI       │     │                 │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                                 │
                        ┌────────▼────────┐
                        │     Upstash     │
                        │     (Redis)     │
                        └─────────────────┘
```

### Services Utilisés (Gratuits)

| Service | Plateforme | Limite Gratuite |
|---------|------------|-----------------|
| Frontend | Vercel | Illimité (hobby) |
| Backend | Railway | 500h/mois ou $5 crédit |
| Backend (alt) | Render | 750h/mois |
| Redis | Upstash | 10K commandes/jour |
| Base de données | Supabase | 500MB, 2 projets |

---

## Déploiement du Backend sur Railway

Railway est une plateforme simple pour déployer des applications Python.

### Étape 1 : Créer un Compte Railway

1. Rendez-vous sur [railway.app](https://railway.app)
2. Connectez-vous avec GitHub
3. Vérifiez votre compte (carte bancaire requise, mais pas de frais)

### Étape 2 : Préparer le Projet

Créez un fichier `Procfile` à la racine du dossier `backend/` :

```bash
cd backend
```

Créez le fichier `Procfile` :
```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
worker: celery -A app.tasks.celery_app worker --loglevel=info
```

Créez un fichier `runtime.txt` :
```
python-3.11.0
```

### Étape 3 : Déployer sur Railway

1. Dans Railway, cliquez sur "New Project"
2. Sélectionnez "Deploy from GitHub repo"
3. Autorisez l'accès à votre repository
4. Sélectionnez le repository et le dossier `backend/`

### Étape 4 : Configurer les Variables d'Environnement

Dans Railway > Settings > Variables, ajoutez :

```env
ENVIRONMENT=production
DEBUG=False

# Supabase
SUPABASE_URL=https://votre-projet.supabase.co
SUPABASE_KEY=votre_anon_key
SUPABASE_SERVICE_ROLE_KEY=votre_service_role_key
DATABASE_URL=postgresql://postgres:password@db.votre-projet.supabase.co:5432/postgres

# WhatsApp
WHATSAPP_PHONE_NUMBER_ID=votre_phone_number_id
WHATSAPP_ACCESS_TOKEN=votre_access_token
WHATSAPP_WEBHOOK_VERIFY_TOKEN=votre_token
WHATSAPP_API_VERSION=v18.0

# Redis (Upstash - voir section suivante)
REDIS_URL=rediss://default:password@endpoint.upstash.io:6379

# JWT
SECRET_KEY=votre_cle_secrete_production_minimum_32_caracteres
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
ALLOWED_ORIGINS=https://votre-app.vercel.app

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100
WHATSAPP_RATE_LIMIT_PER_MINUTE=25
MAX_RETRY_ATTEMPTS=3
RETRY_BASE_DELAY_SECONDS=60
```

### Étape 5 : Déployer le Worker Celery

Railway permet de déployer plusieurs services :

1. Dans votre projet Railway, cliquez sur "New Service"
2. Sélectionnez le même repository
3. Dans Settings > Deploy, changez la commande de démarrage :
   ```
   celery -A app.tasks.celery_app worker --loglevel=info
   ```
4. Ajoutez les mêmes variables d'environnement

### Étape 6 : Obtenir l'URL du Backend

1. Dans Railway > Settings > Networking
2. Cliquez sur "Generate Domain"
3. Notez l'URL (ex: `https://votre-app.up.railway.app`)

---

## Alternative : Déploiement sur Render

Render offre une alternative gratuite à Railway.

### Étape 1 : Créer un Compte Render

1. Rendez-vous sur [render.com](https://render.com)
2. Connectez-vous avec GitHub

### Étape 2 : Créer un Web Service

1. Cliquez sur "New" > "Web Service"
2. Connectez votre repository GitHub
3. Configurez le service :
   - **Name** : chatbot-whatsapp-api
   - **Region** : Frankfurt (EU) ou Oregon (US)
   - **Branch** : main
   - **Root Directory** : backend
   - **Runtime** : Python 3
   - **Build Command** : `pip install -r requirements.txt`
   - **Start Command** : `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Étape 3 : Configurer les Variables d'Environnement

Dans Render > Environment, ajoutez les mêmes variables que pour Railway.

### Étape 4 : Créer un Background Worker

Pour Celery sur Render :

1. Cliquez sur "New" > "Background Worker"
2. Même repository et configuration
3. **Start Command** : `celery -A app.tasks.celery_app worker --loglevel=info`

### Note sur les Limites Render

- Le plan gratuit met le service en veille après 15 minutes d'inactivité
- Le premier appel après la veille prend ~30 secondes
- Pour éviter cela, utilisez un service de ping (UptimeRobot)

---

## Configuration Redis sur Upstash

Upstash offre un Redis serverless gratuit, idéal pour Celery.

### Étape 1 : Créer un Compte Upstash

1. Rendez-vous sur [upstash.com](https://upstash.com)
2. Créez un compte (gratuit)

### Étape 2 : Créer une Base de Données Redis

1. Cliquez sur "Create Database"
2. Configurez :
   - **Name** : chatbot-whatsapp-redis
   - **Region** : Choisissez la plus proche de votre backend
   - **Type** : Regional (gratuit)
3. Cliquez sur "Create"

### Étape 3 : Récupérer l'URL de Connexion

1. Dans le dashboard Upstash, cliquez sur votre base de données
2. Copiez l'**Endpoint** et le **Password**
3. Construisez l'URL Redis :

```
rediss://default:VOTRE_PASSWORD@VOTRE_ENDPOINT:6379
```

> **Note** : Utilisez `rediss://` (avec deux 's') pour la connexion TLS.

### Étape 4 : Configurer Celery pour Upstash

Upstash nécessite TLS. Vérifiez que votre configuration Celery supporte SSL :

```python
# Dans app/tasks/celery_app.py
from celery import Celery
import ssl

redis_url = os.getenv("REDIS_URL")

celery_app = Celery(
    "tasks",
    broker=redis_url,
    backend=redis_url,
    broker_use_ssl={
        'ssl_cert_reqs': ssl.CERT_NONE
    },
    redis_backend_use_ssl={
        'ssl_cert_reqs': ssl.CERT_NONE
    }
)
```

### Limites du Plan Gratuit Upstash

- 10 000 commandes par jour
- 256 MB de stockage
- Suffisant pour un usage modéré

---

## Déploiement du Frontend sur Vercel

Vercel est la plateforme idéale pour Next.js (créée par les mêmes développeurs).

### Étape 1 : Créer un Compte Vercel

1. Rendez-vous sur [vercel.com](https://vercel.com)
2. Connectez-vous avec GitHub

### Étape 2 : Importer le Projet

1. Cliquez sur "Add New" > "Project"
2. Importez votre repository GitHub
3. Configurez :
   - **Framework Preset** : Next.js
   - **Root Directory** : frontend
   - **Build Command** : `npm run build`
   - **Output Directory** : .next

### Étape 3 : Configurer les Variables d'Environnement

Dans Vercel > Settings > Environment Variables :

```env
NEXT_PUBLIC_API_URL=https://votre-backend.up.railway.app/api
NEXT_PUBLIC_SUPABASE_URL=https://votre-projet.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=votre_anon_key
```

### Étape 4 : Déployer

1. Cliquez sur "Deploy"
2. Attendez la fin du build (~2-3 minutes)
3. Notez l'URL de production (ex: `https://votre-app.vercel.app`)

### Étape 5 : Configurer le Domaine Personnalisé (Optionnel)

1. Dans Vercel > Settings > Domains
2. Ajoutez votre domaine personnalisé
3. Configurez les DNS selon les instructions

---

## Configuration des Webhooks en Production

### Étape 1 : Mettre à Jour le Webhook dans Meta

1. Dans Meta Developers > WhatsApp > Configuration
2. Modifiez le webhook :
   - **URL** : `https://votre-backend.up.railway.app/api/webhooks/whatsapp`
   - **Token** : Votre `WHATSAPP_WEBHOOK_VERIFY_TOKEN`
3. Cliquez sur "Vérifier et enregistrer"

### Étape 2 : Vérifier les Abonnements

Assurez-vous que les événements suivants sont cochés :
- ✅ messages
- ✅ message_deliveries
- ✅ message_reads
- ✅ message_reactions

### Étape 3 : Tester le Webhook

```bash
# Test de vérification
curl "https://votre-backend.up.railway.app/api/webhooks/whatsapp?hub.mode=subscribe&hub.verify_token=VOTRE_TOKEN&hub.challenge=test123"

# Réponse attendue : test123
```

---

## Tests de Bout en Bout

### Test 1 : Authentification

```bash
# Connexion
curl -X POST "https://votre-backend.up.railway.app/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "superadmin@example.com", "password": "votre_mot_de_passe"}'
```

### Test 2 : Accès au Dashboard

1. Ouvrez `https://votre-app.vercel.app`
2. Connectez-vous avec les identifiants Super Admin
3. Vérifiez que le dashboard s'affiche correctement

### Test 3 : Création de Données

1. Créez une catégorie
2. Ajoutez un contact (numéro de test)
3. Vérifiez que les données apparaissent

### Test 4 : Envoi de Message

1. Créez une campagne
2. Lancez l'envoi
3. Vérifiez :
   - Les logs du backend (Railway/Render)
   - Les logs Celery
   - La réception du message sur WhatsApp

### Test 5 : Réception de Webhook

1. Répondez au message WhatsApp
2. Vérifiez que l'interaction est enregistrée
3. Vérifiez que le Message 2 est envoyé (si configuré)

---

## Monitoring et Maintenance

### Logs sur Railway

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
3. Onglet "Deployments" > "Functions"

### Monitoring Uptime

Utilisez [UptimeRobot](https://uptimerobot.com) (gratuit) pour :
- Surveiller la disponibilité
- Éviter la mise en veille (Render)
- Recevoir des alertes en cas de panne

Configuration :
1. Créez un compte UptimeRobot
2. Ajoutez un moniteur HTTP(s)
3. URL : `https://votre-backend.up.railway.app/`
4. Intervalle : 5 minutes

### Sauvegardes

Supabase effectue des sauvegardes automatiques. Pour des sauvegardes manuelles :

```bash
# Export de la base de données
pg_dump "postgresql://..." > backup.sql
```

---

## Checklist de Déploiement

### Avant le Déploiement

- [ ] Variables d'environnement configurées
- [ ] Clé secrète JWT générée (production)
- [ ] CORS configuré avec l'URL Vercel
- [ ] Templates WhatsApp approuvés
- [ ] Super Admin créé dans Supabase

### Après le Déploiement

- [ ] Backend accessible et répond
- [ ] Frontend accessible et affiche la page de login
- [ ] Authentification fonctionne
- [ ] Connexion à Supabase OK
- [ ] Connexion à Redis/Upstash OK
- [ ] Worker Celery actif
- [ ] Webhook WhatsApp vérifié
- [ ] Test d'envoi de message réussi
- [ ] Test de réception de webhook réussi

---

## Coûts Estimés

### Plan Gratuit (Recommandé pour Démarrer)

| Service | Coût | Limite |
|---------|------|--------|
| Vercel | $0 | Hobby plan |
| Railway | $0 | 500h/mois |
| Upstash | $0 | 10K cmd/jour |
| Supabase | $0 | 500MB |
| **Total** | **$0** | |

### Plan Production (Si Besoin de Plus)

| Service | Coût | Avantages |
|---------|------|-----------|
| Vercel Pro | $20/mois | Plus de builds, analytics |
| Railway | $5-20/mois | Plus d'heures, pas de veille |
| Upstash | $10/mois | Plus de commandes |
| Supabase | $25/mois | Plus de stockage, backups |

---

## Dépannage

### Le Backend ne Démarre Pas

1. Vérifiez les logs dans Railway/Render
2. Vérifiez que toutes les variables d'environnement sont définies
3. Vérifiez la connexion à Supabase et Redis

### Erreur CORS

1. Vérifiez `ALLOWED_ORIGINS` dans le backend
2. Assurez-vous que l'URL Vercel est correcte (avec https://)
3. Redéployez le backend après modification

### Celery ne Traite Pas les Tâches

1. Vérifiez que le worker est démarré
2. Vérifiez la connexion à Redis/Upstash
3. Vérifiez les logs du worker

### Webhook Non Vérifié

1. Vérifiez que l'URL est accessible publiquement
2. Vérifiez que le token correspond exactement
3. Vérifiez les logs du backend pour les erreurs

---

## Ressources

- [Documentation Railway](https://docs.railway.app)
- [Documentation Render](https://render.com/docs)
- [Documentation Vercel](https://vercel.com/docs)
- [Documentation Upstash](https://docs.upstash.com)
- [Documentation Supabase](https://supabase.com/docs)
