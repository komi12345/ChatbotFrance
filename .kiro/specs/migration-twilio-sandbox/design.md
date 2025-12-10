# Document de Conception - Migration Gupshup vers Twilio WhatsApp Sandbox 2025

## Vue d'Ensemble

Cette migration remplace l'intégration Gupshup API par Twilio WhatsApp Sandbox dans le système de chatbot WhatsApp existant. La migration est conçue pour permettre des tests gratuits d'envoi de messages tout en conservant l'architecture existante.

### Objectifs de Conception

- **Tests Gratuits** : Utilisation du Sandbox Twilio pour tester sans frais
- **Transparence** : Aucune modification du schéma de base de données
- **Compatibilité** : Interface publique similaire pour le nouveau service Twilio
- **Fiabilité** : Conservation de toutes les fonctionnalités existantes
- **Documentation** : Guides complets en français pour la configuration et l'utilisation

### Différences Clés Gupshup vs Twilio Sandbox

| Aspect | Gupshup API 2025 | Twilio WhatsApp Sandbox |
|--------|------------------|-------------------------|
| **Coût** | Payant | Gratuit (Sandbox) |
| **Authentification** | Header apikey | Basic Auth (Account SID:Auth Token) |
| **Format requête** | x-www-form-urlencoded | SDK Python (twilio-python) |
| **Format numéro** | 33612345678 (sans +) | whatsapp:+33612345678 |
| **Numéro source** | Votre numéro Business | +14155238886 (Sandbox partagé) |
| **Opt-in** | Non requis | Requis (code "join") |
| **Rate limit** | 25 msg/min | 1 msg/3s (Sandbox) |
| **Session** | Illimitée | 24h (Sandbox) |
| **Webhook format** | type, mobile, text | From, Body, MessageSid |


## Architecture

### Architecture de Migration

```
┌─────────────────────────────────────────────────────────────┐
│                  FRONTEND (Next.js 14+)                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              MODIFICATIONS MINEURES                   │   │
│  │  - Bandeau info Sandbox                              │   │
│  │  - Instructions de join                              │   │
│  │  - Indicateurs contacts inscrits                     │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ REST API (Axios)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  BACKEND (FastAPI)                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              COUCHE MODIFIÉE                          │   │
│  │  ┌────────────────────┐  ┌────────────────────────┐  │   │
│  │  │ twilio_service.py  │  │ routers/webhooks.py    │  │   │
│  │  │ (NOUVEAU)          │  │ (MODIFIÉ)              │  │   │
│  │  └────────────────────┘  └────────────────────────┘  │   │
│  │  ┌────────────────────┐  ┌────────────────────────┐  │   │
│  │  │ config.py          │  │ tasks/message_tasks.py │  │   │
│  │  │ (MODIFIÉ)          │  │ (MODIFIÉ)              │  │   │
│  │  └────────────────────┘  └────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              FICHIERS À SUPPRIMER                     │   │
│  │  - gupshup_service.py                                │   │
│  │  - test_gupshup_*.py                                 │   │
│  │  - Variables GUPSHUP_* dans config.py                │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ HTTPS (SDK twilio-python)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  TWILIO WHATSAPP SANDBOX                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Numéro Sandbox: +1 415 523 8886                     │   │
│  │  - Messages texte                                    │   │
│  │  - Templates pré-approuvés                           │   │
│  │  - Webhooks entrants et statuts                      │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ Webhooks
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  SUPABASE (PostgreSQL)                       │
│                    [AUCUNE MODIFICATION]                     │
└─────────────────────────────────────────────────────────────┘
```

### Flux d'Envoi de Message (Twilio Sandbox)

```
Admin → Configure Campagne → POST /api/campaigns
→ Backend crée Campaign → Celery Task créée
→ Celery Worker → Pour chaque contact:
    1. Formater numéro (whatsapp:+XXXXXXXXXXX)
    2. Vérifier si contact inscrit au Sandbox
    3. Appeler client.messages.create()
    4. Parser réponse (message.sid)
    5. Stocker SID dans messages.whatsapp_message_id
    6. Attendre 3s (rate limit Sandbox)
→ Mettre à jour statistiques campagne
```

### Flux de Webhook (Twilio)

```
Twilio → POST /api/webhooks/twilio
→ Valider signature X-Twilio-Signature
→ Parser payload:
   - From: whatsapp:+33612345678
   - Body: "Contenu du message"
   - MessageSid: SMxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
→ Si message entrant:
    1. Extraire numéro (retirer "whatsapp:")
    2. Rechercher contact par numéro
    3. Vérifier si Message 2 doit être envoyé
    4. Créer tâche Celery pour Message 2
    5. Enregistrer interaction
→ Si statut de livraison:
    1. Extraire MessageStatus
    2. Mettre à jour statut message
    3. Incrémenter compteurs campagne
→ Retourner TwiML vide (200 OK)
```


## Composants et Interfaces

### Fichiers à Créer

#### 1. services/twilio_service.py (NOUVEAU)

```python
"""
Service Twilio WhatsApp Sandbox 2025 - Intégration avec Twilio API
Remplace gupshup_service.py pour la migration vers Twilio Sandbox
"""
from twilio.rest import Client
from twilio.request_validator import RequestValidator
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime

@dataclass
class TwilioResponse:
    """Réponse de l'API Twilio"""
    success: bool
    message_sid: Optional[str] = None
    error_code: Optional[int] = None
    error_message: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None


@dataclass
class TwilioWebhookInteraction:
    """Interaction parsée depuis un webhook Twilio"""
    contact_phone: str
    interaction_type: str  # 'reply', 'delivered', 'read', 'failed', 'sent'
    content: Optional[str] = None
    twilio_message_sid: Optional[str] = None
    timestamp: Optional[datetime] = None
    error_code: Optional[int] = None


class TwilioService:
    """
    Service pour l'intégration avec Twilio WhatsApp Sandbox 2025.
    Interface compatible avec l'ancien GupshupService.
    """
    
    SANDBOX_NUMBER = "+14155238886"
    
    def __init__(self):
        self.account_sid = settings.TWILIO_ACCOUNT_SID
        self.auth_token = settings.TWILIO_AUTH_TOKEN
        self.sandbox_number = settings.TWILIO_SANDBOX_NUMBER or self.SANDBOX_NUMBER
        self.client = Client(self.account_sid, self.auth_token)
        self.validator = RequestValidator(self.auth_token)
    
    def format_whatsapp_number(self, phone: str) -> str:
        """
        Formate le numéro de téléphone pour Twilio WhatsApp.
        Format: whatsapp:+XXXXXXXXXXX
        """
        # Nettoyer le numéro
        clean_phone = phone.strip()
        if not clean_phone.startswith("+"):
            clean_phone = f"+{clean_phone}"
        return f"whatsapp:{clean_phone}"
    
    def extract_phone_from_whatsapp(self, whatsapp_number: str) -> str:
        """
        Extrait le numéro de téléphone du format WhatsApp Twilio.
        whatsapp:+33612345678 -> +33612345678
        """
        return whatsapp_number.replace("whatsapp:", "")
    
    async def send_message(
        self,
        phone: str,
        text: str
    ) -> TwilioResponse:
        """
        Envoie un message WhatsApp via Twilio Sandbox.
        """
        try:
            to_number = self.format_whatsapp_number(phone)
            from_number = self.format_whatsapp_number(self.sandbox_number)
            
            message = self.client.messages.create(
                body=text,
                from_=from_number,
                to=to_number
            )
            
            return TwilioResponse(
                success=True,
                message_sid=message.sid,
                raw_response={"sid": message.sid, "status": message.status}
            )
            
        except TwilioRestException as e:
            return TwilioResponse(
                success=False,
                error_code=e.code,
                error_message=e.msg
            )
    
    def validate_webhook_signature(
        self,
        url: str,
        params: Dict[str, str],
        signature: str
    ) -> bool:
        """Valide la signature d'un webhook Twilio."""
        return self.validator.validate(url, params, signature)
    
    def parse_webhook_payload(
        self,
        payload: Dict[str, Any]
    ) -> List[TwilioWebhookInteraction]:
        """Parse le payload d'un webhook Twilio."""
        # Implémentation détaillée...
        pass


# Instance singleton du service
twilio_service = TwilioService()
```


### Fichiers à Modifier

#### 2. config.py (MODIFIÉ)

Nouvelles variables à ajouter :

```python
class Settings(BaseSettings):
    # ... variables existantes ...
    
    # ==========================================================================
    # TWILIO WHATSAPP SANDBOX (2025) - NOUVELLE INTÉGRATION
    # ==========================================================================
    # Account SID Twilio (obligatoire)
    TWILIO_ACCOUNT_SID: str = ""
    # Auth Token Twilio (obligatoire, secret)
    TWILIO_AUTH_TOKEN: str = ""
    # Numéro Sandbox Twilio (par défaut: +14155238886)
    TWILIO_SANDBOX_NUMBER: str = "+14155238886"
    # URL de base pour les webhooks (pour validation de signature)
    TWILIO_WEBHOOK_BASE_URL: str = ""
    
    def validate_twilio_config(self) -> None:
        """Valide que les variables Twilio obligatoires sont configurées."""
        missing_vars = []
        if not self.TWILIO_ACCOUNT_SID:
            missing_vars.append("TWILIO_ACCOUNT_SID")
        if not self.TWILIO_AUTH_TOKEN:
            missing_vars.append("TWILIO_AUTH_TOKEN")
        
        if missing_vars:
            raise ValueError(
                f"Variables Twilio manquantes: {', '.join(missing_vars)}"
            )
```

Variables à supprimer :
- `GUPSHUP_API_KEY`
- `GUPSHUP_APP_NAME`
- `GUPSHUP_PHONE_NUMBER`
- `GUPSHUP_API_URL`
- `GUPSHUP_CUSTOMER_ID`

#### 3. routers/webhooks.py (MODIFIÉ)

Remplacer l'endpoint Gupshup par Twilio :

```python
from twilio.twiml.messaging_response import MessagingResponse

@router.post("/twilio", status_code=status.HTTP_200_OK)
async def receive_twilio_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: SupabaseDB = Depends(get_supabase_db),
) -> Response:
    """
    Endpoint de réception des webhooks Twilio WhatsApp.
    
    Gère deux types de webhooks:
    - Messages entrants (From, Body, MessageSid)
    - Statuts de livraison (MessageStatus, MessageSid)
    
    Retourne une réponse TwiML vide.
    """
    # Valider la signature Twilio
    signature = request.headers.get("X-Twilio-Signature", "")
    form_data = await request.form()
    params = dict(form_data)
    
    url = str(request.url)
    if not twilio_service.validate_webhook_signature(url, params, signature):
        raise HTTPException(status_code=403, detail="Invalid signature")
    
    # Détecter le type de webhook
    message_status = params.get("MessageStatus")
    
    if message_status:
        # Webhook de statut de livraison
        background_tasks.add_task(process_twilio_status, params, db)
    else:
        # Webhook de message entrant
        background_tasks.add_task(process_twilio_message, params, db)
    
    # Retourner TwiML vide
    response = MessagingResponse()
    return Response(
        content=str(response),
        media_type="application/xml"
    )
```

#### 4. tasks/message_tasks.py (MODIFIÉ)

Remplacer l'import et l'utilisation du service :

```python
# AVANT
from app.services.gupshup_service import gupshup_service

# APRÈS
from app.services.twilio_service import twilio_service

# Modifier le rate limit pour Sandbox (1 msg/3s au lieu de 25/min)
SANDBOX_RATE_LIMIT_SECONDS = 3

# Dans send_single_message:
response = await twilio_service.send_message(
    phone=phone,
    text=message["content"]
)

# Stocker le SID Twilio
if response.success:
    db.update_message(message_id, {
        "status": "sent",
        "whatsapp_message_id": response.message_sid,  # SID Twilio
        "sent_at": datetime.utcnow().isoformat()
    })
```

### Fichiers à Supprimer

| Fichier | Raison |
|---------|--------|
| `backend/app/services/gupshup_service.py` | Remplacé par twilio_service.py |
| `backend/test_gupshup_*.py` | Tests Gupshup obsolètes |
| `backend/tests/test_gupshup_*.py` | Tests Gupshup obsolètes |
| `backend/app/services/archive/` | Dossier d'archive Gupshup |


## Modèles de Données

### Aucune Modification du Schéma

Le schéma de base de données reste inchangé. Le champ `whatsapp_message_id` dans la table `messages` sera utilisé pour stocker le SID Twilio.

```sql
-- Table messages (INCHANGÉE)
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER REFERENCES campaigns(id),
    contact_id INTEGER REFERENCES contacts(id),
    message_type VARCHAR(20),
    content TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    whatsapp_message_id VARCHAR(255),  -- Stockera le SID Twilio (SMxxx...)
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    sent_at TIMESTAMP,
    delivered_at TIMESTAMP,
    read_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Format des Identifiants

| Plateforme | Format ID | Exemple |
|------------|-----------|---------|
| Gupshup | gBEGVzU... | gBEGVzUxMjM0NTY3ODkw |
| Twilio | SMxxx... | SM1234567890abcdef1234567890abcdef |

## Propriétés de Correction

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Formatage des numéros WhatsApp
*For any* numéro de téléphone passé au service Twilio, le résultat doit être au format `whatsapp:+XXXXXXXXXXX`
**Validates: Requirements 2.2**

### Property 2: Numéro source Sandbox constant
*For any* message envoyé via le service Twilio, le numéro source doit toujours être le numéro Sandbox configuré (whatsapp:+14155238886)
**Validates: Requirements 2.3**

### Property 3: Gestion des erreurs Twilio
*For any* erreur retournée par l'API Twilio, le service doit retourner un TwilioResponse avec success=False, le code d'erreur et le message
**Validates: Requirements 2.5**

### Property 4: Encodage JSON des paramètres template
*For any* liste de paramètres de template, l'encodage ContentVariables doit produire un JSON valide
**Validates: Requirements 3.2**

### Property 5: Validation des paramètres template
*For any* template avec N variables, le service doit rejeter les appels avec moins de N paramètres
**Validates: Requirements 3.4**

### Property 6: Validation de signature webhook
*For any* webhook Twilio reçu, la signature X-Twilio-Signature doit être validée avant traitement
**Validates: Requirements 4.1**

### Property 7: Extraction des champs webhook message
*For any* webhook Twilio de message entrant, le parsing doit extraire correctement From, Body et MessageSid
**Validates: Requirements 4.2**

### Property 8: Réponse webhook TwiML
*For any* webhook traité, la réponse doit être une réponse TwiML valide avec statut 200 OK
**Validates: Requirements 4.6**

### Property 9: Extraction du MessageStatus
*For any* webhook Twilio de statut, le parsing doit extraire correctement le MessageStatus parmi (queued, sent, delivered, read, failed, undelivered)
**Validates: Requirements 5.1**

### Property 10: Gestion des erreurs de livraison
*For any* webhook avec MessageStatus "failed" ou "undelivered", le message doit être marqué comme échoué avec le ErrorCode
**Validates: Requirements 5.4**

### Property 11: Respect du rate limiting Sandbox
*For any* envoi massif de messages, le système ne doit jamais envoyer plus de 1 message toutes les 3 secondes
**Validates: Requirements 6.2**

### Property 12: Calcul du délai de retry exponentiel
*For any* retry de message échoué, le délai doit suivre la formule : délai = 60 × 2^(tentative-1) secondes
**Validates: Requirements 6.3**

### Property 13: Gestion de l'erreur Sandbox non-inscrit
*For any* erreur Twilio avec code 63007, le service doit retourner un message explicite indiquant que le destinataire doit rejoindre le Sandbox
**Validates: Requirements 7.1, 7.5**


## Gestion des Erreurs

### Erreurs API Twilio Courantes

| Code | Description | Action |
|------|-------------|--------|
| 20003 | Authentication error | Vérifier Account SID et Auth Token |
| 21211 | Invalid phone number | Vérifier le format du numéro |
| 21608 | Unverified number (Sandbox) | Le destinataire doit rejoindre le Sandbox |
| 63007 | Recipient not in Sandbox | Afficher instructions de join |
| 63016 | Message body too long | Limiter à 1600 caractères |
| 30003 | Unreachable destination | Retry avec backoff |
| 30005 | Unknown destination | Vérifier le numéro |
| 30006 | Landline or unreachable | Le numéro n'a pas WhatsApp |

### Stratégie de Retry

```python
def calculate_retry_delay(attempt: int) -> int:
    """
    Calcule le délai avant le prochain retry.
    Formule: délai = 60 × 2^(tentative-1) secondes
    
    Args:
        attempt: Numéro de la tentative (1, 2, 3)
    
    Returns:
        Délai en secondes (60, 120, 240)
    """
    base_delay = 60  # 1 minute
    return base_delay * (2 ** (attempt - 1))
```

### Messages d'Erreur Utilisateur

```python
TWILIO_ERROR_MESSAGES = {
    63007: "Le destinataire n'a pas rejoint le Sandbox Twilio. "
           "Il doit envoyer 'join <code>' au +1 415 523 8886.",
    21608: "Numéro non vérifié. En mode Sandbox, le destinataire "
           "doit d'abord rejoindre le Sandbox.",
    21211: "Numéro de téléphone invalide. Vérifiez le format.",
    30006: "Ce numéro n'a pas WhatsApp installé.",
}
```

## Stratégie de Tests

### Tests Unitaires

1. **test_phone_formatting** : Vérifier que format_whatsapp_number produit `whatsapp:+XXX`
2. **test_phone_extraction** : Vérifier que extract_phone_from_whatsapp retire le préfixe
3. **test_webhook_signature_validation** : Vérifier la validation de signature
4. **test_webhook_parsing_message** : Vérifier le parsing des webhooks message
5. **test_webhook_parsing_status** : Vérifier le parsing des webhooks statut
6. **test_retry_delay_calculation** : Vérifier le calcul du délai exponentiel
7. **test_error_code_handling** : Vérifier la gestion des codes d'erreur Twilio

### Tests Property-Based (avec Hypothesis)

La bibliothèque **Hypothesis** sera utilisée pour les tests property-based en Python.

Configuration minimale : 100 itérations par test.

Format d'annotation des tests :
```python
# **Feature: migration-twilio-sandbox, Property 1: Formatage des numéros WhatsApp**
@given(phone_number=st.text(min_size=10, max_size=15).filter(lambda x: x.isdigit()))
def test_phone_formatting_produces_whatsapp_format(phone_number):
    result = twilio_service.format_whatsapp_number(phone_number)
    assert result.startswith("whatsapp:+")
    assert result.count(":") == 1
```

### Tests d'Intégration

1. **test_send_message_integration** : Envoi réel d'un message (avec Sandbox)
2. **test_webhook_flow** : Simulation complète du flux webhook
3. **test_campaign_flow** : Test du flux complet de campagne
4. **test_twilio_connection** : Vérification de la connexion API

