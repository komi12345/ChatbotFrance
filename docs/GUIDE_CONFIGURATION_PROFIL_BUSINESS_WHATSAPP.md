# 🏢 Guide de Configuration du Profil Business WhatsApp

Ce guide explique comment configurer votre profil WhatsApp Business pour afficher un nom professionnel au lieu du numéro de téléphone, améliorer la confiance des contacts et optimiser votre présence sur WhatsApp.

---

## 📋 Table des Matières

1. [Comprendre le Profil WhatsApp Business](#1-comprendre-le-profil-whatsapp-business)
2. [Vérifier le Type de Compte WhatsApp](#2-vérifier-le-type-de-compte-whatsapp)
3. [Configuration du Profil Business dans WhatsApp](#3-configuration-du-profil-business-dans-whatsapp)
4. [Configuration dans Wassenger Dashboard](#4-configuration-dans-wassenger-dashboard)
5. [Demande de Vérification WhatsApp Business](#5-demande-de-vérification-whatsapp-business)
6. [Utilisation de l'API WhatsApp Business](#6-utilisation-de-lapi-whatsapp-business)
7. [Configuration des Messages avec Nom du Chatbot](#7-configuration-des-messages-avec-nom-du-chatbot)
8. [Tests et Vérification](#8-tests-et-vérification)
9. [Limitations et Contraintes](#9-limitations-et-contraintes)
10. [Bonnes Pratiques](#10-bonnes-pratiques)
11. [Dépannage](#11-dépannage)

---

## 1. Comprendre le Profil WhatsApp Business

### 1.1 Qu'est-ce qu'un Profil Business ?

Le profil WhatsApp Business permet aux entreprises de :
- 🏷️ Afficher un **nom d'entreprise** au lieu du numéro de téléphone
- 🖼️ Montrer une **photo de profil** professionnelle
- 📝 Présenter une **description** de l'activité
- 📍 Indiquer l'**adresse** et les **horaires** d'ouverture
- 🌐 Partager le **site web** et l'**email** de contact

### 1.2 Avantages pour le Chatbot

| Avantage | Impact |
|----------|--------|
| **Confiance** | Les contacts voient un nom d'entreprise, pas un numéro inconnu |
| **Professionnalisme** | Image de marque cohérente |
| **Identification** | Les contacts reconnaissent immédiatement l'expéditeur |
| **Crédibilité** | Badge de vérification possible (compte vérifié) |

### 1.3 Types de Comptes WhatsApp

| Type | Nom affiché | API disponible | Recommandé |
|------|-------------|----------------|------------|
| WhatsApp Standard | Numéro uniquement | ❌ Non | ❌ |
| WhatsApp Business App | Nom d'entreprise | Via Wassenger | ✅ Oui |
| WhatsApp Business API | Nom d'entreprise + Badge | ✅ Officielle | ✅✅ Idéal |

---

## 2. Vérifier le Type de Compte WhatsApp

### 2.1 Identifier Votre Type de Compte

Sur votre smartphone :

1. Ouvrez **WhatsApp**
2. Allez dans **Paramètres**
3. Regardez l'icône de l'application :
   - 📱 **Icône verte standard** = WhatsApp Standard
   - 🏢 **Icône avec "B"** = WhatsApp Business App

### 2.2 Migrer vers WhatsApp Business App

Si vous utilisez WhatsApp Standard :

1. Téléchargez **WhatsApp Business** depuis :
   - [Google Play Store](https://play.google.com/store/apps/details?id=com.whatsapp.w4b)
   - [Apple App Store](https://apps.apple.com/app/whatsapp-business/id1386412985)

2. Lors de l'installation :
   - Acceptez de migrer vos conversations
   - Utilisez le même numéro de téléphone
   - Vos contacts et messages seront conservés

⚠️ **Important** : La migration est irréversible. WhatsApp Standard sera désinstallé.

### 2.3 Vérifier la Compatibilité avec Wassenger

Wassenger supporte :
- ✅ WhatsApp Business App (via QR code)
- ✅ WhatsApp Business API (intégration directe)
- ⚠️ WhatsApp Standard (fonctionne mais sans profil business)

---

## 3. Configuration du Profil Business dans WhatsApp

### 3.1 Accéder aux Paramètres du Profil

1. Ouvrez **WhatsApp Business**
2. Allez dans **Paramètres > Outils professionnels > Profil de l'entreprise**

### 3.2 Configurer le Nom de l'Entreprise

1. Cliquez sur **Nom de l'entreprise**
2. Entrez le nom de votre chatbot/entreprise :
   - ✅ Bon : "Assistant MonEntreprise"
   - ✅ Bon : "Service Client XYZ"
   - ❌ Éviter : "Bot" seul ou noms génériques

**Règles pour le nom** :
- Maximum 256 caractères
- Pas de caractères spéciaux excessifs
- Doit représenter une vraie entreprise
- Pas de termes trompeurs

### 3.3 Ajouter une Photo de Profil

1. Cliquez sur l'icône de la photo
2. Choisissez une image :
   - 📐 Format carré recommandé (640x640 px minimum)
   - 🎨 Logo de l'entreprise ou icône du chatbot
   - 🖼️ Image claire et professionnelle

**Conseils** :
- Utilisez votre logo sur fond uni
- Évitez les photos personnelles
- Assurez-vous que l'image est lisible en petit format

### 3.4 Rédiger la Description

1. Cliquez sur **À propos**
2. Rédigez une description concise :

```
🤖 Assistant automatique de [Nom Entreprise]
📞 Réponse rapide à vos questions
⏰ Disponible 24h/24
```

**Limite** : 256 caractères maximum

### 3.5 Ajouter les Informations de Contact

Remplissez les champs optionnels :

| Champ | Exemple |
|-------|---------|
| **Adresse** | 123 Rue Example, Lomé, Togo |
| **Email** | contact@monentreprise.com |
| **Site web** | https://www.monentreprise.com |

### 3.6 Configurer les Horaires

1. Allez dans **Horaires d'ouverture**
2. Choisissez :
   - **Toujours ouvert** (recommandé pour un chatbot)
   - Ou définissez des horaires spécifiques

---

## 4. Configuration dans Wassenger Dashboard

### 4.1 Synchroniser le Profil

Après avoir configuré WhatsApp Business sur votre téléphone :

1. Connectez-vous à [app.wassenger.com](https://app.wassenger.com/)
2. Allez dans **Devices**
3. Cliquez sur votre appareil connecté
4. Vérifiez que les informations du profil sont synchronisées

### 4.2 Vérifier les Informations Affichées

Dans les détails de l'appareil, vous devriez voir :
- ✅ Nom de l'entreprise
- ✅ Photo de profil
- ✅ Numéro de téléphone
- ✅ Statut de connexion

### 4.3 Mettre à Jour le Profil via Wassenger

Certaines informations peuvent être mises à jour via l'API :

```bash
curl -X PATCH "https://api.wassenger.com/v1/devices/{device_id}/profile" \
  -H "Authorization: Bearer {api_key}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Assistant MonEntreprise",
    "about": "Service client automatisé 24/7"
  }'
```

⚠️ **Note** : Les modifications via API peuvent être limitées selon votre plan Wassenger.

---

## 5. Demande de Vérification WhatsApp Business

### 5.1 Qu'est-ce que la Vérification ?

La vérification WhatsApp Business ajoute :
- ✅ Un **badge vert** à côté du nom
- ✅ Une **confiance accrue** des utilisateurs
- ✅ Un **accès prioritaire** aux nouvelles fonctionnalités

### 5.2 Critères d'Éligibilité

Pour être vérifié, vous devez :
- 🏢 Être une entreprise légalement enregistrée
- 📄 Avoir des documents officiels (RCCM, NIF, etc.)
- 🌐 Avoir une présence en ligne vérifiable
- 📱 Utiliser WhatsApp Business API (pas l'App)

### 5.3 Processus de Vérification

1. **Via Meta Business Suite** :
   - Créez un compte Meta Business
   - Ajoutez votre entreprise
   - Soumettez les documents de vérification

2. **Documents requis** :
   - Certificat d'enregistrement de l'entreprise
   - Facture de services publics au nom de l'entreprise
   - Licence commerciale

3. **Délai** : 2 à 4 semaines généralement

### 5.4 Alternative sans Vérification

Si la vérification n'est pas possible :
- Le nom d'entreprise s'affiche quand même
- Pas de badge vert
- Fonctionnalités identiques pour l'envoi de messages

---

## 6. Utilisation de l'API WhatsApp Business

### 6.1 Différence avec WhatsApp Business App

| Aspect | Business App + Wassenger | Business API |
|--------|--------------------------|--------------|
| **Configuration** | QR code simple | Processus Meta |
| **Coût** | Abonnement Wassenger | Frais Meta + hébergement |
| **Limites d'envoi** | ~1000/jour | Selon tier |
| **Badge vérifié** | Non | Possible |
| **Templates** | Non requis | Obligatoires hors 24h |

### 6.2 Quand Passer à l'API Officielle ?

Considérez l'API WhatsApp Business si :
- 📈 Volume > 1000 messages/jour
- ✅ Badge de vérification nécessaire
- 🔒 Conformité stricte requise
- 💼 Entreprise de grande taille

### 6.3 Migration vers l'API Officielle

Si vous décidez de migrer :
1. Créez un compte Meta Business
2. Demandez l'accès à l'API WhatsApp Business
3. Configurez un BSP (Business Solution Provider) ou hébergez vous-même
4. Migrez votre numéro (le numéro sera déconnecté de l'App)

---

## 7. Configuration des Messages avec Nom du Chatbot

### 7.1 Comment le Nom Apparaît

Quand vous envoyez un message via Wassenger :

**Ce que voit le contact** :
```
┌─────────────────────────────────┐
│ 🏢 Assistant MonEntreprise      │
│ ✓ Message professionnel         │
├─────────────────────────────────┤
│ Bonjour ! Comment puis-je vous  │
│ aider aujourd'hui ?             │
│                          10:30 ✓│
└─────────────────────────────────┘
```

### 7.2 Personnaliser les Messages

Dans votre application, vous pouvez ajouter une signature :

```python
def format_message(content: str, chatbot_name: str = "Assistant") -> str:
    """Ajoute une signature au message."""
    return f"{content}\n\n— {chatbot_name}"
```

**Exemple de message** :
```
Bonjour Jean ! Merci pour votre intérêt.
Voici les informations demandées...

— Assistant MonEntreprise
```

### 7.3 Cohérence de la Marque

Assurez-vous que :
- Le nom dans WhatsApp = Nom dans les messages
- La photo de profil = Logo de l'entreprise
- Le ton des messages = Image de marque

---

## 8. Tests et Vérification

### 8.1 Tester l'Affichage du Profil

1. Envoyez un message test à un numéro externe
2. Demandez à la personne de vérifier :
   - ✅ Le nom de l'entreprise s'affiche
   - ✅ La photo de profil est visible
   - ✅ Les informations du profil sont accessibles

### 8.2 Vérifier sur Différents Appareils

Testez sur :
- 📱 Android (différentes versions)
- 🍎 iPhone
- 💻 WhatsApp Web

### 8.3 Checklist de Vérification

- [ ] Nom d'entreprise configuré et visible
- [ ] Photo de profil professionnelle ajoutée
- [ ] Description "À propos" rédigée
- [ ] Informations de contact complètes
- [ ] Horaires d'ouverture définis
- [ ] Profil synchronisé avec Wassenger
- [ ] Test d'envoi réussi avec affichage correct

---

## 9. Limitations et Contraintes

### 9.1 Limitations de WhatsApp Business App

| Limitation | Détail |
|------------|--------|
| **Pas de badge vérifié** | Réservé à l'API officielle |
| **Limite d'envoi** | ~1000 messages/jour recommandé |
| **Un seul appareil** | Le téléphone doit rester connecté |
| **Pas de templates** | Messages libres uniquement |

### 9.2 Limitations du Nom d'Entreprise

- ❌ Ne peut pas contenir "WhatsApp" ou "Meta"
- ❌ Ne peut pas être trompeur ou usurper une identité
- ❌ Peut être refusé si non conforme aux règles
- ⚠️ Peut être modifié par WhatsApp si signalé

### 9.3 Limitations Techniques

- Le nom ne s'affiche pas si le contact vous a déjà enregistré
- Les anciens contacts voient le numéro jusqu'à mise à jour de leur cache
- Certains clients WhatsApp anciens peuvent ne pas afficher le nom

---

## 10. Bonnes Pratiques

### 10.1 Nom d'Entreprise

✅ **À faire** :
- Utiliser le nom officiel de l'entreprise
- Ajouter "Assistant" ou "Service Client" si c'est un bot
- Garder le nom court et mémorable

❌ **À éviter** :
- Noms génériques ("Support", "Info")
- Caractères spéciaux excessifs
- Noms trompeurs ou spam

### 10.2 Photo de Profil

✅ **À faire** :
- Logo de l'entreprise sur fond uni
- Image haute résolution (640x640 px)
- Couleurs de la marque

❌ **À éviter** :
- Photos personnelles
- Images floues ou pixelisées
- Texte illisible en petit format

### 10.3 Description

✅ **À faire** :
- Expliquer clairement le service
- Utiliser des emojis avec modération
- Inclure les horaires si pertinent

❌ **À éviter** :
- Descriptions trop longues
- Langage promotionnel excessif
- Informations obsolètes

### 10.4 Messages

✅ **À faire** :
- Ton professionnel et amical
- Messages clairs et concis
- Signature cohérente

❌ **À éviter** :
- Spam ou messages répétitifs
- Langage inapproprié
- Promesses non tenues

---

## 11. Dépannage

### ❌ Le nom d'entreprise ne s'affiche pas

**Causes possibles** :
- Le contact vous a enregistré avec un autre nom
- Cache WhatsApp non mis à jour
- Profil non configuré correctement

**Solutions** :
1. Demandez au contact de supprimer votre numéro et de vous recontacter
2. Vérifiez la configuration dans WhatsApp Business
3. Attendez 24-48h pour la propagation

### ❌ La photo de profil n'apparaît pas

**Causes possibles** :
- Image trop petite ou format incorrect
- Paramètres de confidentialité restrictifs
- Synchronisation en cours

**Solutions** :
1. Utilisez une image de 640x640 px minimum
2. Vérifiez les paramètres de confidentialité
3. Reconnectez l'appareil à Wassenger

### ❌ Profil non synchronisé avec Wassenger

**Causes possibles** :
- Session WhatsApp déconnectée
- Problème de connexion Internet
- Cache Wassenger

**Solutions** :
1. Vérifiez que l'appareil est "Connected" dans Wassenger
2. Déconnectez et reconnectez l'appareil
3. Contactez le support Wassenger

### ❌ Nom refusé par WhatsApp

**Causes possibles** :
- Nom non conforme aux règles
- Usurpation d'identité suspectée
- Signalement par des utilisateurs

**Solutions** :
1. Choisissez un nom différent
2. Utilisez le nom légal de votre entreprise
3. Contactez le support WhatsApp Business

### ❌ Badge de vérification refusé

**Causes possibles** :
- Documents insuffisants
- Entreprise non éligible
- Informations incohérentes

**Solutions** :
1. Vérifiez les critères d'éligibilité
2. Soumettez des documents plus complets
3. Assurez la cohérence entre les informations

---

## 📚 Ressources Supplémentaires

- 📖 [Documentation WhatsApp Business](https://business.whatsapp.com/)
- 🔧 [Meta Business Help Center](https://www.facebook.com/business/help)
- 💬 [Support Wassenger](https://wassenger.com/support)
- 📁 [Guide de configuration Wassenger](./GUIDE_CONFIGURATION_WASSENGER_2025.md)
- 📁 [Guide de lancement du projet](./GUIDE_LANCEMENT_PROJET_WASSENGER_2025.md)

---

*Guide mis à jour : Décembre 2025*
