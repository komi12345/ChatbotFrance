# Templates WhatsApp pour Gupshup - Newsteck

> ⚠️ **OBSOLÈTE** : Ce guide est obsolète. L'intégration Gupshup a été remplacée par Twilio WhatsApp Sandbox.
> Pour le Sandbox Twilio, utilisez les templates pré-approuvés fournis par Twilio.
> Date de migration : Décembre 2025

## Guide de création sur Gupshup (Obsolète)

1. Va sur https://www.gupshup.io/whatsapp-api
2. Sélectionne ton app "newsteck"
3. Va dans "Templates" > "Create Template"
4. Copie les informations ci-dessous

---

## 📋 TEMPLATE 1 : Message de Bienvenue (MARKETING)

**Nom du template:** `welcome_message`
**Catégorie:** MARKETING
**Langue:** French (fr)

**Header (Texte):**
```
Bienvenue chez {{1}} ! 🎉
```

**Body:**
```
Bonjour {{1}},

Merci de nous avoir contactés ! Nous sommes ravis de vous compter parmi nos clients.

Notre équipe est disponible pour répondre à toutes vos questions du lundi au vendredi, de 8h à 18h.

À très bientôt !
```

**Footer:**
```
Répondez STOP pour vous désabonner
```

**Boutons (optionnel):**
- Type: QUICK_REPLY
- Texte: "En savoir plus"

**Variables:**
- {{1}} dans Header = Nom de l'entreprise (ex: "Newsteck")
- {{1}} dans Body = Prénom du client

---

## 📋 TEMPLATE 2 : Notification de Campagne (MARKETING)

**Nom du template:** `campaign_notification`
**Catégorie:** MARKETING
**Langue:** French (fr)

**Header (Texte):**
```
📢 Nouvelle offre {{1}}
```

**Body:**
```
Bonjour {{1}},

{{2}}

Cette offre est valable jusqu'au {{3}}.

Pour plus d'informations, n'hésitez pas à nous contacter.

Cordialement,
L'équipe {{4}}
```

**Footer:**
```
Répondez STOP pour vous désabonner
```

**Variables:**
- {{1}} Header = Type d'offre (ex: "spéciale", "exclusive")
- {{1}} Body = Prénom du client
- {{2}} = Contenu de l'offre/message
- {{3}} = Date de fin
- {{4}} = Nom de l'entreprise

---

## 📋 TEMPLATE 3 : Rappel/Relance (MARKETING)

**Nom du template:** `reminder_message`
**Catégorie:** MARKETING
**Langue:** French (fr)

**Body:**
```
Bonjour {{1}},

Nous voulions simplement prendre de vos nouvelles et vous rappeler que nous sommes toujours là pour vous accompagner.

{{2}}

N'hésitez pas à nous contacter si vous avez des questions.

Bien cordialement,
{{3}}
```

**Footer:**
```
Répondez STOP pour vous désabonner
```

**Variables:**
- {{1}} = Prénom du client
- {{2}} = Message personnalisé
- {{3}} = Nom de l'entreprise/signature

---

## 📋 TEMPLATE 4 : Confirmation (UTILITY)

**Nom du template:** `confirmation_message`
**Catégorie:** UTILITY
**Langue:** French (fr)

**Body:**
```
Bonjour {{1}},

Votre demande a bien été enregistrée.

Référence : {{2}}
Date : {{3}}

Notre équipe vous contactera dans les plus brefs délais.

Merci de votre confiance.
```

**Variables:**
- {{1}} = Prénom du client
- {{2}} = Numéro de référence
- {{3}} = Date

---

## 📋 TEMPLATE 5 : Message Générique (MARKETING)

**Nom du template:** `generic_campaign`
**Catégorie:** MARKETING
**Langue:** French (fr)

**Body:**
```
Bonjour {{1}},

{{2}}

Pour toute question, contactez-nous.

Cordialement,
{{3}}
```

**Footer:**
```
Répondez STOP pour vous désabonner
```

**Variables:**
- {{1}} = Prénom du client
- {{2}} = Message libre (contenu de la campagne)
- {{3}} = Signature/Nom entreprise

---

## ⚠️ Règles importantes pour l'approbation

1. **Toujours inclure** une option de désabonnement (STOP)
2. **Éviter** les mots comme "gratuit", "promotion", "réduction" dans le header
3. **Ne pas utiliser** de majuscules excessives
4. **Être clair** sur l'identité de l'expéditeur
5. **Les variables** doivent avoir des exemples réalistes lors de la soumission

## 📝 Exemples de valeurs pour la soumission

Lors de la création du template, Gupshup demande des exemples :

| Variable | Exemple |
|----------|---------|
| {{1}} (prénom) | Jean |
| {{2}} (message) | Découvrez nos nouveaux services disponibles dès maintenant. |
| {{3}} (date) | 31 décembre 2025 |
| {{4}} (entreprise) | Newsteck |

## 🔧 Utilisation dans le code

Une fois approuvé, utilise le template ainsi :

```python
# Exemple d'envoi avec template
template_data = {
    "id": "welcome_message",  # Nom du template
    "params": ["Jean"]  # Variables dans l'ordre
}
```

## ⏱️ Délai d'approbation

- Templates UTILITY : 24-48h
- Templates MARKETING : 48h-7 jours
- Rejet possible si non conforme aux règles Meta
