# 🚀 Guide de Déploiement Frontend sur Netlify

**Plateforme** : Chatbot WhatsApp - Frontend Next.js  
**Date** : Décembre 2025  
**Version** : Next.js 16 + React 19

---

## 📋 Table des Matières

1. [Vue d'Ensemble](#1-vue-densemble)
2. [Prérequis](#2-prérequis)
3. [Préparation du Projet](#3-préparation-du-projet)
4. [Création du Compte Netlify](#4-création-du-compte-netlify)
5. [Déploiement Étape par Étape](#5-déploiement-étape-par-étape)
6. [Configuration des Variables d'Environnement](#6-configuration-des-variables-denvironnement)
7. [Configuration du Domaine](#7-configuration-du-domaine)
8. [Vérification et Tests](#8-vérification-et-tests)
9. [Dépannage](#9-dépannage)
10. [Maintenance et Mises à Jour](#10-maintenance-et-mises-à-jour)

---

## 1. Vue d'Ensemble

### Architecture de Déploiement

```
┌─────────────────────────────────────────────────────────────────┐
│                         NETLIFY                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Frontend Next.js 16                         │   │
│  │         https://votre-app.netlify.app                   │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Backend FastAPI                               │
│              (Railway / Render / Autre)                         │
│         https://votre-backend.up.railway.app/api                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Supabase                                   │
│                    (Base de données)                            │
└─────────────────────────────────────────────────────────────────┘
```

### Pourquoi Netlify ?

| Avantage | Description |
|----------|-------------|
| ✅ **Gratuit** | Plan Starter généreux (100 GB bande passante/mois) |
| ✅ **Simple** | Déploiement automatique depuis GitHub |
| ✅ **Rapide** | CDN mondial pour des temps de chargement optimaux |
| ✅ **HTTPS** | Certificat SSL automatique et gratuit |
| ✅ **Preview** | Déploiements de prévisualisation pour chaque PR |
| ✅ **Next.js** | Support natif de Next.js via @netlify/plugin-nextjs |

### Limites du Plan Gratuit (Starter)

- 100 GB de bande passante par mois
- 300 minutes de build par mois
- 1 membre d'équipe
- Déploiements illimités
- HTTPS gratuit

---

## 2. Prérequis

### Comptes Requis

- [ ] **GitHub** : Votre code doit être hébergé sur GitHub
- [ ] **Netlify** : Compte gratuit (création dans ce guide)
- [ ] **Backend déployé** : Votre API FastAPI doit être accessible en ligne

### Informations à Préparer

Avant de commencer, récupérez ces informations :

```bash
# URL de votre backend déployé (Railway, Render, etc.)
NEXT_PUBLIC_API_URL=https://votre-backend.up.railway.app/api

# Supabase (Dashboard > Settings > API)
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Vérifications Locales

Avant de déployer, assurez-vous que le projet fonctionne localement :

```bash
# Aller dans le dossier frontend
cd frontend

# Installer les dépendances
npm install

# Tester le build
npm run build

# Si le build réussit, vous êtes prêt !
```

---

## 3. Préparation du Projet

### Étape 3.1 : Créer le Fichier de Configuration Netlify

Créez un fichier `netlify.toml` à la racine du dossier `frontend/` :

```bash
# Créer le fichier
cd frontend
```

**Contenu du fichier `frontend/netlify.toml`** :

```toml
[build]
  # Commande de build
  command = "npm run build"
  # Dossier de sortie pour Next.js
  publish = ".next"

[build.environment]
  # Version de Node.js (Next.js 16 nécessite Node 18+)
  NODE_VERSION = "20"
  # Désactiver les avertissements de dépendances
  NPM_FLAGS = "--legacy-peer-deps"

# Plugin Next.js pour Netlify (ESSENTIEL)
[[plugins]]
  package = "@netlify/plugin-nextjs"

# Redirections pour le routage Next.js
[[redirects]]
  from = "/*"
  to = "/.netlify/functions/___netlify-handler"
  status = 200
  conditions = {Role = ["admin"]}

# Headers de sécurité
[[headers]]
  for = "/*"
  [headers.values]
    X-Frame-Options = "DENY"
    X-XSS-Protection = "1; mode=block"
    X-Content-Type-Options = "nosniff"
    Referrer-Policy = "strict-origin-when-cross-origin"
```

### Étape 3.2 : Vérifier le fichier .gitignore

Assurez-vous que `.env.local` est dans le `.gitignore` (ne jamais commiter les secrets) :

```bash
# Vérifier le contenu de .gitignore
cat frontend/.gitignore
```

Le fichier doit contenir :
```
.env.local
.env*.local
```

### Étape 3.3 : Pousser les Modifications sur GitHub

```bash
# Ajouter le fichier netlify.toml
git add frontend/netlify.toml

# Commiter
git commit -m "feat(frontend): ajouter configuration Netlify"

# Pousser sur GitHub
git push origin main
```

---

## 4. Création du Compte Netlify

### Étape 4.1 : Inscription

1. Rendez-vous sur **[netlify.com](https://www.netlify.com)**
2. Cliquez sur **"Sign up"** (en haut à droite)
3. Choisissez **"Sign up with GitHub"** (recommandé)
4. Autorisez Netlify à accéder à votre compte GitHub

### Étape 4.2 : Vérification du Compte

1. Vérifiez votre email si demandé
2. Complétez le profil si nécessaire
3. Vous arrivez sur le **Dashboard Netlify**

---

## 5. Déploiement Étape par Étape

### Étape 5.1 : Créer un Nouveau Site

1. Dans le Dashboard Netlify, cliquez sur **"Add new site"**
2. Sélectionnez **"Import an existing project"**

![Netlify Add Site](https://docs.netlify.com/images/add-new-site.png)

### Étape 5.2 : Connecter GitHub

1. Cliquez sur **"Deploy with GitHub"**
2. Si c'est la première fois, autorisez Netlify à accéder à vos repositories
3. Vous pouvez choisir :
   - **All repositories** : Netlify voit tous vos repos
   - **Only select repositories** : Choisissez uniquement ce projet

### Étape 5.3 : Sélectionner le Repository

1. Recherchez votre repository dans la liste
2. Cliquez dessus pour le sélectionner

### Étape 5.4 : Configurer le Build

Remplissez les paramètres suivants :

| Paramètre | Valeur |
|-----------|--------|
| **Branch to deploy** | `main` (ou votre branche principale) |
| **Base directory** | `frontend` |
| **Build command** | `npm run build` |
| **Publish directory** | `frontend/.next` |

**Configuration visuelle :**

```
┌─────────────────────────────────────────────────────────────┐
│ Site settings for your new site                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ Branch to deploy:     [ main                    ▼ ]         │
│                                                              │
│ Base directory:       [ frontend                  ]         │
│                                                              │
│ Build command:        [ npm run build             ]         │
│                                                              │
│ Publish directory:    [ frontend/.next            ]         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Étape 5.5 : Ajouter les Variables d'Environnement

**IMPORTANT** : Avant de lancer le build, ajoutez les variables d'environnement !

1. Cliquez sur **"Show advanced"** (ou "Advanced build settings")
2. Dans la section **"Environment variables"**, cliquez sur **"New variable"**
3. Ajoutez chaque variable :

| Clé | Valeur |
|-----|--------|
| `NEXT_PUBLIC_API_URL` | `https://votre-backend.up.railway.app/api` |
| `NEXT_PUBLIC_SUPABASE_URL` | `https://xxxxx.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | `eyJhbGciOiJIUzI1NiIs...` |

**Exemple visuel :**

```
┌─────────────────────────────────────────────────────────────┐
│ Environment variables                                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ Key:   [ NEXT_PUBLIC_API_URL                    ]           │
│ Value: [ https://votre-backend.up.railway.app/api ]         │
│                                              [+ New variable]│
│                                                              │
│ Key:   [ NEXT_PUBLIC_SUPABASE_URL               ]           │
│ Value: [ https://xxxxx.supabase.co              ]           │
│                                              [+ New variable]│
│                                                              │
│ Key:   [ NEXT_PUBLIC_SUPABASE_ANON_KEY          ]           │
│ Value: [ eyJhbGciOiJIUzI1NiIs...                ]           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Étape 5.6 : Lancer le Déploiement

1. Cliquez sur **"Deploy site"**
2. Netlify va :
   - Cloner votre repository
   - Installer les dépendances (`npm install`)
   - Exécuter le build (`npm run build`)
   - Déployer le site

### Étape 5.7 : Suivre le Build

1. Vous êtes redirigé vers la page du site
2. Cliquez sur **"Deploys"** pour voir les logs en temps réel
3. Le build prend généralement **2-5 minutes**

**Logs de build réussi :**
```
12:00:00 PM: Build ready to start
12:00:05 PM: Cloning repository...
12:00:10 PM: Installing dependencies...
12:02:00 PM: Running build command...
12:04:30 PM: Build successful
12:04:35 PM: Deploying to Netlify Edge...
12:04:45 PM: Site is live ✓
```

### Étape 5.8 : Accéder au Site

Une fois le build terminé :

1. Netlify génère une URL automatique : `https://random-name-123456.netlify.app`
2. Cliquez sur l'URL pour voir votre site en ligne !

---

## 6. Configuration des Variables d'Environnement

### Modifier les Variables Après Déploiement

Si vous devez modifier les variables d'environnement :

1. Allez dans **Site settings** > **Environment variables**
2. Cliquez sur la variable à modifier
3. Modifiez la valeur
4. Cliquez sur **"Save"**
5. **Redéployez** le site (Deploys > Trigger deploy > Deploy site)

### Variables Requises

| Variable | Description | Exemple |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | URL de votre API backend | `https://api.example.com/api` |
| `NEXT_PUBLIC_SUPABASE_URL` | URL de votre projet Supabase | `https://xxx.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Clé publique Supabase | `eyJhbGci...` |

### Variables Optionnelles

| Variable | Description | Valeur par défaut |
|----------|-------------|-------------------|
| `NEXT_PUBLIC_ENV` | Environnement | `production` |

---

## 7. Configuration du Domaine

### Option A : Utiliser le Domaine Netlify Gratuit

Par défaut, votre site est accessible via `https://random-name.netlify.app`.

**Personnaliser le nom :**

1. Allez dans **Site settings** > **Domain management**
2. Cliquez sur **"Options"** à côté du domaine Netlify
3. Sélectionnez **"Edit site name"**
4. Entrez un nom personnalisé : `chatbot-whatsapp`
5. Votre site sera accessible via : `https://chatbot-whatsapp.netlify.app`

### Option B : Utiliser un Domaine Personnalisé

Si vous avez votre propre domaine (ex: `app.mondomaine.com`) :

1. Allez dans **Site settings** > **Domain management**
2. Cliquez sur **"Add custom domain"**
3. Entrez votre domaine : `app.mondomaine.com`
4. Cliquez sur **"Verify"**

**Configuration DNS :**

Ajoutez ces enregistrements chez votre registrar DNS :

| Type | Nom | Valeur |
|------|-----|--------|
| CNAME | `app` | `votre-site.netlify.app` |

Ou pour un domaine apex (sans sous-domaine) :

| Type | Nom | Valeur |
|------|-----|--------|
| A | `@` | `75.2.60.5` |
| AAAA | `@` | `2600:1f14:e22:5a00::1` |

**Certificat SSL :**

Netlify génère automatiquement un certificat SSL Let's Encrypt gratuit une fois le DNS configuré (peut prendre jusqu'à 24h).

---

## 8. Vérification et Tests

### Test 1 : Accès au Site

1. Ouvrez l'URL de votre site Netlify
2. Vérifiez que la page de login s'affiche correctement

### Test 2 : Connexion à l'API

1. Ouvrez les DevTools (F12) > Console
2. Essayez de vous connecter
3. Vérifiez qu'il n'y a pas d'erreurs CORS

### Test 3 : Authentification

1. Connectez-vous avec vos identifiants admin
2. Vérifiez que le dashboard s'affiche
3. Vérifiez que les données se chargent (contacts, catégories)

### Checklist de Validation

- [ ] Le site est accessible via l'URL Netlify
- [ ] La page de login s'affiche correctement
- [ ] Pas d'erreurs dans la console du navigateur
- [ ] L'authentification fonctionne
- [ ] Les données se chargent depuis l'API
- [ ] Le HTTPS fonctionne (cadenas vert)

---

## 9. Dépannage

### Erreur : Build Failed

**Symptôme** : Le build échoue avec des erreurs

**Solutions** :

1. **Vérifiez les logs de build** dans Netlify > Deploys
2. **Testez le build localement** :
   ```bash
   cd frontend
   npm run build
   ```
3. **Vérifiez la version de Node.js** : Next.js 16 nécessite Node 18+
4. **Ajoutez dans netlify.toml** :
   ```toml
   [build.environment]
     NODE_VERSION = "20"
   ```

### Erreur : Page 404 sur les Routes

**Symptôme** : Les pages fonctionnent en local mais pas sur Netlify

**Solution** : Assurez-vous que le plugin Next.js est installé :

```toml
# Dans netlify.toml
[[plugins]]
  package = "@netlify/plugin-nextjs"
```

### Erreur : CORS (Cross-Origin)

**Symptôme** : `Access-Control-Allow-Origin` error dans la console

**Solutions** :

1. **Vérifiez l'URL du backend** dans les variables d'environnement
2. **Mettez à jour ALLOWED_ORIGINS** dans votre backend :
   ```env
   ALLOWED_ORIGINS=https://votre-site.netlify.app
   ```
3. **Redéployez le backend** après modification

### Erreur : Variables d'Environnement Non Définies

**Symptôme** : `undefined` pour les variables `NEXT_PUBLIC_*`

**Solutions** :

1. Vérifiez que les variables sont bien définies dans Netlify
2. Les variables doivent commencer par `NEXT_PUBLIC_` pour être accessibles côté client
3. **Redéployez** après avoir ajouté/modifié les variables

### Erreur : Timeout de Build

**Symptôme** : Le build dépasse 15 minutes et échoue

**Solutions** :

1. **Optimisez le build** dans `next.config.ts` :
   ```typescript
   typescript: {
     ignoreBuildErrors: true,
   },
   ```
2. **Utilisez le cache** : Netlify met en cache `node_modules` automatiquement
3. **Vérifiez les dépendances** : Supprimez les dépendances inutilisées

### Erreur : "Function invocation failed"

**Symptôme** : Erreur 500 sur certaines pages

**Solutions** :

1. Vérifiez les logs dans **Functions** > **Logs**
2. Assurez-vous que toutes les variables d'environnement sont définies
3. Vérifiez que le backend est accessible

---

## 10. Maintenance et Mises à Jour

### Déploiement Automatique

Par défaut, Netlify redéploie automatiquement à chaque push sur la branche `main`.

**Désactiver le déploiement automatique** (si nécessaire) :

1. Allez dans **Site settings** > **Build & deploy** > **Continuous deployment**
2. Cliquez sur **"Stop builds"**

### Déploiement Manuel

Pour déclencher un déploiement manuellement :

1. Allez dans **Deploys**
2. Cliquez sur **"Trigger deploy"** > **"Deploy site"**

### Rollback (Retour en Arrière)

Si un déploiement pose problème :

1. Allez dans **Deploys**
2. Trouvez un déploiement précédent qui fonctionnait
3. Cliquez sur les **"..."** > **"Publish deploy"**

### Prévisualisation des Pull Requests

Netlify crée automatiquement un déploiement de prévisualisation pour chaque Pull Request :

- URL de preview : `https://deploy-preview-123--votre-site.netlify.app`
- Permet de tester les changements avant de merger

### Monitoring

**Vérifier l'état du site :**

1. **Analytics** : Netlify > Analytics (plan payant)
2. **Logs de fonctions** : Netlify > Functions > Logs
3. **Monitoring externe** : Utilisez [UptimeRobot](https://uptimerobot.com) (gratuit)

---

## 📝 Récapitulatif

### URLs Importantes

| Service | URL |
|---------|-----|
| **Frontend (Netlify)** | `https://votre-site.netlify.app` |
| **Backend (Railway/Render)** | `https://votre-backend.up.railway.app/api` |
| **Supabase** | `https://xxxxx.supabase.co` |

### Variables d'Environnement

```env
NEXT_PUBLIC_API_URL=https://votre-backend.up.railway.app/api
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIs...
```

### Fichiers de Configuration

```
frontend/
├── netlify.toml          # Configuration Netlify
├── next.config.ts        # Configuration Next.js
├── package.json          # Dépendances et scripts
└── .env.local            # Variables locales (NE PAS COMMITER)
```

### Commandes Utiles

```bash
# Tester le build localement
cd frontend && npm run build

# Voir les logs de build
# → Netlify Dashboard > Deploys > [Dernier déploiement]

# Redéployer manuellement
# → Netlify Dashboard > Deploys > Trigger deploy
```

---

## 🔗 Ressources

- [Documentation Netlify](https://docs.netlify.com)
- [Next.js sur Netlify](https://docs.netlify.com/frameworks/next-js/overview/)
- [Plugin Next.js Netlify](https://github.com/netlify/next-runtime)
- [Variables d'environnement Netlify](https://docs.netlify.com/environment-variables/overview/)

---

**Guide créé le** : Décembre 2025  
**Dernière mise à jour** : Décembre 2025
