"""
Service Wassenger WhatsApp 2025 - Intégration avec Wassenger API
Remplace twilio_service.py pour la migration vers Wassenger

Ce service gère :
- L'envoi de messages texte via Wassenger API
- Le parsing des webhooks Wassenger
- La gestion des erreurs spécifiques Wassenger
"""
import logging
import re
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

import httpx

from app.config import settings

# Configuration du logger
logger = logging.getLogger(__name__)


@dataclass
class WassengerResponse:
    """
    Réponse de l'API Wassenger.
    
    Attributes:
        success: Indique si la requête a réussi
        message_id: ID du message Wassenger (si succès)
        error_code: Code d'erreur Wassenger (si échec)
        error_message: Message d'erreur détaillé (si échec)
        raw_response: Réponse brute de l'API pour debug
    
    Requirements: 2.3, 2.4
    """
    success: bool
    message_id: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None


@dataclass
class WassengerWebhookInteraction:
    """
    Interaction parsée depuis un webhook Wassenger.
    
    Attributes:
        contact_phone: Numéro de téléphone du contact (format: 22890123456)
        interaction_type: Type d'interaction ('reply', 'sent', 'delivered', 'read', 'failed')
        content: Contenu du message (pour les réponses)
        wassenger_message_id: ID du message Wassenger
        timestamp: Horodatage de l'interaction
        error_message: Message d'erreur (si échec)
    
    Requirements: 3.1
    """
    contact_phone: str
    interaction_type: str
    content: Optional[str] = None
    wassenger_message_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    error_message: Optional[str] = None


@dataclass
class WhatsAppExistsResponse:
    """
    Réponse de vérification d'existence WhatsApp via Wassenger API.
    
    Attributes:
        exists: True si le numéro est enregistré sur WhatsApp, False sinon
        phone: Numéro de téléphone vérifié (format normalisé)
        error_code: Code d'erreur Wassenger (si échec de vérification)
        error_message: Message d'erreur détaillé (si échec de vérification)
    
    Requirements: 1.2
    """
    exists: bool
    phone: str
    error_code: Optional[str] = None
    error_message: Optional[str] = None



# ==========================================================================
# MESSAGES D'ERREUR WASSENGER (en français)
# ==========================================================================
# Messages utilisateur pour les codes d'erreur Wassenger courants
# Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
WASSENGER_ERROR_MESSAGES: Dict[str, str] = {
    "device_not_connected": (
        "L'appareil WhatsApp doit être reconnecté via QR code dans le dashboard Wassenger. "
        "Allez dans Wassenger Dashboard > Devices et scannez le QR code."
    ),
    "invalid_phone_number": (
        "Le format du numéro de téléphone est incorrect. "
        "Utilisez le format international sans + (ex: 22890123456)."
    ),
    "rate_limit_exceeded": (
        "Limite de débit atteinte. Réessai automatique dans 60 secondes. "
        "Veuillez patienter avant d'envoyer d'autres messages."
    ),
    "session_expired": (
        "La session WhatsApp a expiré. "
        "Reconnectez l'appareil dans le dashboard Wassenger via QR code."
    ),
    "message_too_long": (
        "Le message dépasse la limite de 4096 caractères. "
        "Veuillez raccourcir votre message."
    ),
    "unauthorized": (
        "Erreur d'authentification. Vérifiez votre API Key Wassenger."
    ),
    "device_not_found": (
        "L'appareil spécifié n'existe pas. Vérifiez le Device ID dans votre configuration."
    ),
    "insufficient_credits": (
        "Crédits insuffisants sur votre compte Wassenger. "
        "Veuillez recharger votre compte."
    ),
}

# Instructions détaillées pour la reconnexion de l'appareil
DEVICE_RECONNECT_INSTRUCTIONS = """
Pour reconnecter votre appareil WhatsApp à Wassenger:

1. Connectez-vous au dashboard Wassenger (https://app.wassenger.com)
2. Allez dans la section "Devices"
3. Cliquez sur votre appareil ou "Add Device"
4. Scannez le QR code avec WhatsApp sur votre téléphone
5. Attendez la confirmation de connexion
6. Vérifiez que le statut passe à "Connected"

Note: La session peut expirer après une période d'inactivité.
"""


class WassengerService:
    """
    Service pour l'intégration avec Wassenger API 2025.
    Interface compatible avec l'ancien TwilioService pour faciliter la migration.
    
    Différences clés avec Twilio:
    - Authentification via Bearer Token (API Key)
    - Client HTTP httpx (async)
    - Format numéro: sans préfixe + (22890123456)
    - Device ID requis dans chaque requête
    - Rate limit: 2 secondes entre messages
    
    Note: Ce service crée un nouveau client HTTP pour chaque requête afin d'éviter
    les problèmes d'event loop fermé dans Celery.
    
    Requirements: 1.3, 1.4, 2.1
    """
    
    BASE_URL = "https://api.wassenger.com/v1"
    
    def __init__(self):
        """
        Initialise le service avec les paramètres de configuration.
        
        Requirements: 1.1, 1.3, 1.4
        """
        self.api_key = settings.WASSENGER_API_KEY
        self.device_id = settings.WASSENGER_DEVICE_ID
        
        # Ne pas créer de client singleton - sera créé à la demande
        # pour éviter les problèmes d'event loop fermé dans Celery
        self._client = None
        
        logger.info(
            "Service Wassenger initialisé",
            extra={
                "device_id": self.device_id[:8] + "..." if self.device_id else "N/A",
                "api_key_prefix": self.api_key[:12] + "..." if self.api_key else "N/A"
            }
        )
    
    def _get_client(self, timeout: float = 30.0) -> httpx.AsyncClient:
        """
        Crée un nouveau client HTTP async pour chaque requête.
        Évite les problèmes d'event loop fermé dans Celery.
        
        Args:
            timeout: Timeout en secondes pour les requêtes (défaut: 30s)
        """
        return httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            timeout=timeout
        )

    def format_phone_number(self, phone: str) -> str:
        """
        Formate le numéro de téléphone pour Wassenger API.
        Format: uniquement les chiffres sans le préfixe + (ex: 22890123456)
        
        Args:
            phone: Numéro de téléphone (avec ou sans +, avec ou sans espaces)
        
        Returns:
            Numéro au format Wassenger (chiffres uniquement)
        
        Requirements: 2.2
        """
        # Retirer tous les caractères non numériques (espaces, tirets, parenthèses, +)
        clean_phone = re.sub(r'[^\d]', '', phone)
        
        return clean_phone


    @staticmethod
    def get_error_details(error_code: str) -> Dict[str, Any]:
        """
        Retourne les détails complets d'une erreur Wassenger avec message utilisateur.
        
        Args:
            error_code: Code d'erreur Wassenger
        
        Returns:
            Dictionnaire avec:
            - error_type: Type d'erreur
            - message: Message d'erreur utilisateur en français
            - instructions: Instructions détaillées pour résoudre le problème
            - requires_reconnect: True si l'appareil doit être reconnecté
        
        Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
        """
        result = {
            "error_type": error_code,
            "message": WASSENGER_ERROR_MESSAGES.get(
                error_code, 
                f"Erreur Wassenger inconnue: {error_code}"
            ),
            "instructions": None,
            "requires_reconnect": False,
            "retry_delay_seconds": None
        }
        
        # Erreurs nécessitant une reconnexion de l'appareil
        if error_code in ("device_not_connected", "session_expired"):
            result["requires_reconnect"] = True
            result["instructions"] = DEVICE_RECONNECT_INSTRUCTIONS
        
        # Erreur de rate limiting avec délai de retry
        if error_code == "rate_limit_exceeded":
            result["retry_delay_seconds"] = 60
        
        return result

    async def send_message(self, phone: str, text: str) -> WassengerResponse:
        """
        Envoie un message WhatsApp via Wassenger API.
        
        Args:
            phone: Numéro de téléphone du destinataire
            text: Contenu du message texte
        
        Returns:
            WassengerResponse avec le résultat de l'envoi
        
        Requirements: 2.1, 2.3, 2.4, 2.5
        """
        # Créer un nouveau client pour chaque requête (évite event loop closed)
        client = self._get_client()
        
        try:
            # Formater le numéro au format Wassenger (sans +)
            formatted_phone = self.format_phone_number(phone)
            
            # Construire le payload avec device ID
            # Requirements: 1.4, 2.1
            payload = {
                "phone": formatted_phone,
                "message": text,
                "device": self.device_id
            }
            
            logger.info(
                f"Envoi message Wassenger à {formatted_phone}",
                extra={
                    "phone": formatted_phone,
                    "device_id": self.device_id[:8] + "..." if self.device_id else "N/A",
                    "text_length": len(text)
                }
            )
            
            # Appeler l'API Wassenger
            # Requirements: 2.1
            response = await client.post(
                f"{self.BASE_URL}/messages",
                json=payload
            )
            
            response_data = response.json()
            
            # Vérifier le succès de la requête
            if response.status_code in (200, 201):
                # Extraire le message_id de la réponse
                # Requirements: 2.3
                message_id = response_data.get("id")
                
                logger.info(
                    f"Message Wassenger envoyé avec succès, ID: {message_id}",
                    extra={
                        "message_id": message_id,
                        "status": response_data.get("status")
                    }
                )
                
                return WassengerResponse(
                    success=True,
                    message_id=message_id,
                    raw_response=response_data
                )
            else:
                # Parser l'erreur de la réponse
                # Requirements: 2.4
                error_code = response_data.get("error", "unknown_error")
                error_message = response_data.get("message", "Erreur inconnue")
                
                # Obtenir les détails de l'erreur avec message utilisateur
                error_details = self.get_error_details(error_code)
                user_message = error_details["message"]
                
                logger.error(
                    f"Erreur API Wassenger: {error_code} - {error_message}",
                    extra={
                        "error_code": error_code,
                        "error_message": error_message,
                        "phone": formatted_phone,
                        "status_code": response.status_code,
                        "requires_reconnect": error_details["requires_reconnect"]
                    }
                )
                
                return WassengerResponse(
                    success=False,
                    error_code=error_code,
                    error_message=user_message,
                    raw_response=response_data
                )
                
        except httpx.TimeoutException as e:
            logger.error(
                f"Timeout lors de l'envoi du message Wassenger: {str(e)}",
                extra={"phone": phone}
            )
            
            return WassengerResponse(
                success=False,
                error_code="timeout",
                error_message="La requête a expiré. Veuillez réessayer."
            )
            
        except httpx.RequestError as e:
            logger.error(
                f"Erreur réseau lors de l'envoi du message Wassenger: {str(e)}",
                extra={"phone": phone}
            )
            
            return WassengerResponse(
                success=False,
                error_code="network_error",
                error_message=f"Erreur réseau: {str(e)}"
            )
            
        except Exception as e:
            logger.exception(
                f"Erreur inattendue lors de l'envoi du message Wassenger: {str(e)}",
                extra={"phone": phone}
            )
            
            return WassengerResponse(
                success=False,
                error_code="unexpected_error",
                error_message=f"Erreur inattendue: {str(e)}"
            )
        
        finally:
            # Toujours fermer le client après utilisation
            try:
                await client.aclose()
            except Exception:
                pass  # Ignorer les erreurs de fermeture

    async def check_whatsapp_exists(self, phone: str, max_retries: int = 2) -> WhatsAppExistsResponse:
        """
        Vérifie si un numéro de téléphone est enregistré sur WhatsApp via Wassenger API.
        
        Endpoint: POST /v1/numbers/exists
        Body: {"phone": "+22892146653"}  # Format E164 avec +
        
        Args:
            phone: Numéro de téléphone à vérifier (avec ou sans +, avec ou sans espaces)
            max_retries: Nombre maximum de tentatives en cas de timeout (défaut: 2)
        
        Returns:
            WhatsAppExistsResponse avec le résultat de la vérification:
            - exists=True si le numéro est sur WhatsApp
            - exists=False si le numéro n'est pas sur WhatsApp
            - exists=False avec error_code si une erreur s'est produite
        
        Requirements: 1.1, 1.3
        """
        import asyncio
        
        # Timeout très long pour la vérification WhatsApp (5 minutes = 300 secondes)
        # car l'API Wassenger doit communiquer avec WhatsApp et peut être lente
        VERIFICATION_TIMEOUT = 300.0
        
        # Créer un nouveau client pour chaque requête (évite event loop closed)
        client = self._get_client(timeout=VERIFICATION_TIMEOUT)
        
        # Formater le numéro au format E164 avec + pour l'API /numbers/exists
        # L'API Wassenger /numbers/exists requiert le format E164 complet avec +
        clean_phone = self.format_phone_number(phone)  # Retire tous les caractères non numériques
        formatted_phone = f"+{clean_phone}" if clean_phone and not clean_phone.startswith('+') else clean_phone
        
        try:
            logger.info(
                f"Vérification WhatsApp pour {formatted_phone}",
                extra={
                    "phone": formatted_phone,
                    "device_id": self.device_id[:8] + "..." if self.device_id else "N/A"
                }
            )
            
            # Appeler l'API Wassenger pour vérifier l'existence
            # Endpoint correct: POST /v1/numbers/exists avec body {"phone": "..."}
            # Requirements: 1.1
            response = await client.post(
                f"{self.BASE_URL}/numbers/exists",
                json={
                    "phone": formatted_phone
                }
            )
            
            response_data = response.json()
            
            # Vérifier le succès de la requête
            # Status 200: numéro trouvé sur WhatsApp (exists=true)
            # Status 404: numéro NON trouvé sur WhatsApp (exists=false) - c'est un résultat valide!
            if response.status_code == 200 or response.status_code == 404:
                # Extraire le résultat de la vérification
                # L'API retourne exists=true (200) ou exists=false (404)
                exists = response_data.get("exists", False)
                
                logger.info(
                    f"Vérification WhatsApp terminée: {formatted_phone} -> exists={exists}",
                    extra={
                        "phone": formatted_phone,
                        "exists": exists,
                        "status_code": response.status_code
                    }
                )
                
                return WhatsAppExistsResponse(
                    exists=exists,
                    phone=formatted_phone
                )
            
            # Gérer les erreurs de rate limit (429)
            elif response.status_code == 429:
                error_details = self.get_error_details("rate_limit_exceeded")
                
                logger.warning(
                    f"Rate limit atteint lors de la vérification WhatsApp: {formatted_phone}",
                    extra={
                        "phone": formatted_phone,
                        "status_code": response.status_code,
                        "retry_delay": error_details.get("retry_delay_seconds")
                    }
                )
                
                return WhatsAppExistsResponse(
                    exists=False,
                    phone=formatted_phone,
                    error_code="rate_limit_exceeded",
                    error_message=error_details["message"]
                )
            
            # Gérer les erreurs d'authentification (401)
            elif response.status_code == 401:
                error_details = self.get_error_details("unauthorized")
                
                logger.error(
                    f"Erreur d'authentification lors de la vérification WhatsApp",
                    extra={
                        "phone": formatted_phone,
                        "status_code": response.status_code
                    }
                )
                
                return WhatsAppExistsResponse(
                    exists=False,
                    phone=formatted_phone,
                    error_code="unauthorized",
                    error_message=error_details["message"]
                )
            
            # Gérer les autres erreurs API
            else:
                error_code = response_data.get("error", "unknown_error")
                error_message = response_data.get("message", "Erreur inconnue")
                
                # Vérifier si c'est une erreur de format de numéro
                if response.status_code == 400 or "invalid" in error_code.lower():
                    error_code = "invalid_phone_number"
                    error_details = self.get_error_details(error_code)
                    error_message = error_details["message"]
                
                logger.error(
                    f"Erreur API Wassenger lors de la vérification: {error_code}",
                    extra={
                        "phone": formatted_phone,
                        "error_code": error_code,
                        "error_message": error_message,
                        "status_code": response.status_code
                    }
                )
                
                return WhatsAppExistsResponse(
                    exists=False,
                    phone=formatted_phone,
                    error_code=error_code,
                    error_message=error_message
                )
                
        except httpx.TimeoutException as e:
            # Gérer les timeouts réseau avec retry
            # Requirements: 1.3
            logger.warning(
                f"Timeout lors de la vérification WhatsApp (tentative): {str(e)}",
                extra={"phone": formatted_phone, "max_retries": max_retries}
            )
            
            # Fermer le client actuel
            try:
                await client.aclose()
            except Exception:
                pass
            
            # Retry si on a encore des tentatives
            if max_retries > 0:
                logger.info(f"Retry vérification WhatsApp pour {formatted_phone}, tentatives restantes: {max_retries}")
                await asyncio.sleep(2)  # Attendre 2 secondes avant retry
                return await self.check_whatsapp_exists(phone, max_retries - 1)
            
            logger.error(
                f"Timeout définitif lors de la vérification WhatsApp après toutes les tentatives: {str(e)}",
                extra={"phone": formatted_phone}
            )
            
            return WhatsAppExistsResponse(
                exists=False,
                phone=formatted_phone,
                error_code="timeout",
                error_message="La vérification WhatsApp a expiré après plusieurs tentatives. Veuillez réessayer plus tard."
            )
            
        except httpx.RequestError as e:
            # Gérer les erreurs réseau
            # Requirements: 1.3
            logger.error(
                f"Erreur réseau lors de la vérification WhatsApp: {str(e)}",
                extra={"phone": formatted_phone}
            )
            
            return WhatsAppExistsResponse(
                exists=False,
                phone=formatted_phone,
                error_code="network_error",
                error_message=f"Erreur réseau: {str(e)}"
            )
            
        except Exception as e:
            # Gérer les erreurs inattendues
            # Requirements: 1.3
            logger.exception(
                f"Erreur inattendue lors de la vérification WhatsApp: {str(e)}",
                extra={"phone": formatted_phone}
            )
            
            return WhatsAppExistsResponse(
                exists=False,
                phone=formatted_phone,
                error_code="unexpected_error",
                error_message=f"Erreur inattendue: {str(e)}"
            )
        
        finally:
            # Toujours fermer le client après utilisation
            try:
                await client.aclose()
            except Exception:
                pass  # Ignorer les erreurs de fermeture

    def _parse_timestamp(self, timestamp_str: Optional[str]) -> Optional[datetime]:
        """
        Parse un timestamp ISO 8601 depuis Wassenger.
        
        Args:
            timestamp_str: Timestamp au format ISO 8601 (ex: "2025-01-15T10:35:00Z")
        
        Returns:
            datetime ou None si le parsing échoue
        """
        if not timestamp_str:
            return datetime.utcnow()
        
        try:
            return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return datetime.utcnow()

    def parse_webhook_payload(
        self,
        payload: Dict[str, Any]
    ) -> List[WassengerWebhookInteraction]:
        """
        Parse le payload d'un webhook Wassenger 2025 pour extraire les interactions.
        
        Wassenger 2025 envoie les événements suivants:
        
        1. Message entrant (message:in:new):
        {
            "event": "message:in:new",
            "data": {
                "id": "msg_xyz789",
                "fromNumber": "22890123456",
                "body": "Réponse du contact",
                "timestamp": "2025-01-15T10:35:00Z",
                "device": "device_id_here"
            }
        }
        
        2. Message sortant créé (message:out:new):
        {
            "event": "message:out:new",
            "data": {
                "id": "msg_abc123",
                "phone": "22890123456",
                "createdAt": "2025-01-15T10:30:00Z"
            }
        }
        
        3. Mise à jour de statut (message:update) - NOUVEAU en 2025:
        {
            "event": "message:update",
            "data": {
                "id": "msg_abc123",
                "phone": "22890123456",
                "status": "delivered",
                "timestamp": "2025-01-15T10:31:00Z",
                "error": "message d'erreur si failed"
            }
        }
        
        4. Réaction à un message (message:reaction):
        {
            "event": "message:reaction",
            "data": {
                "fromNumber": "22890123456",
                "messageId": "msg_abc123",
                "reaction": "👍",
                "timestamp": "2025-01-15T10:32:00Z"
            }
        }
        
        Args:
            payload: Payload du webhook Wassenger (JSON)
        
        Returns:
            Liste des interactions extraites
        
        Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
        """
        event_type = payload.get("event", "")
        data = payload.get("data", {})
        
        try:
            # 1. Messages entrants (réponses des contacts)
            if event_type == "message:in:new":
                return [WassengerWebhookInteraction(
                    contact_phone=self.format_phone_number(data.get("fromNumber", "")),
                    interaction_type="reply",
                    content=data.get("body", ""),
                    wassenger_message_id=data.get("id"),
                    timestamp=self._parse_timestamp(data.get("timestamp"))
                )]
            
            # 2. Messages sortants créés (nouveau en 2025)
            elif event_type == "message:out:new":
                return [WassengerWebhookInteraction(
                    contact_phone=self.format_phone_number(data.get("phone", "")),
                    interaction_type="queued",  # Nouveau statut pour message en file d'attente
                    wassenger_message_id=data.get("id"),
                    timestamp=self._parse_timestamp(data.get("createdAt"))
                )]
            
            # 3. Mises à jour de statut (NOUVEAU - regroupe sent/delivered/read/failed)
            elif event_type == "message:update":
                status = data.get("status", "")
                
                # Mapping des statuts Wassenger → statuts BDD
                status_mapping = {
                    "sent": "sent",
                    "delivered": "delivered",
                    "read": "read",
                    "failed": "failed",
                    "queued": "pending"
                }
                
                interaction_type = status_mapping.get(status, "unknown")
                
                return [WassengerWebhookInteraction(
                    contact_phone=self.format_phone_number(data.get("phone", "")),
                    interaction_type=interaction_type,
                    wassenger_message_id=data.get("id"),
                    timestamp=self._parse_timestamp(data.get("timestamp")),
                    error_message=data.get("error") if status == "failed" else None
                )]
            
            # 4. Réactions aux messages
            elif event_type == "message:reaction":
                return [WassengerWebhookInteraction(
                    contact_phone=self.format_phone_number(data.get("fromNumber", "")),
                    interaction_type="reaction",
                    content=data.get("reaction", ""),  # Emoji de réaction
                    wassenger_message_id=data.get("messageId"),
                    timestamp=self._parse_timestamp(data.get("timestamp"))
                )]
            
            # 5. Accusé de réception (message:out:ack) - IMPORTANT pour delivered/read
            elif event_type == "message:out:ack":
                # message:out:ack contient le statut "delivered" ou "read"
                ack_type = data.get("ack", "")
                
                # Mapping des types d'ack Wassenger → statuts BDD
                ack_mapping = {
                    "device": "sent",      # Envoyé au serveur WhatsApp
                    "server": "sent",      # Reçu par le serveur WhatsApp
                    "delivered": "delivered",  # Délivré au destinataire
                    "read": "read",        # Lu par le destinataire
                    "played": "read",      # Audio/vidéo joué (équivalent à lu)
                }
                
                interaction_type = ack_mapping.get(ack_type, "unknown")
                
                logger.info(f"message:out:ack reçu: ack={ack_type} -> status={interaction_type}")
                
                return [WassengerWebhookInteraction(
                    contact_phone=self.format_phone_number(data.get("phone", data.get("to", ""))),
                    interaction_type=interaction_type,
                    wassenger_message_id=data.get("id", data.get("waId", "")),
                    timestamp=self._parse_timestamp(data.get("timestamp", data.get("t", None)))
                )]
            
            # 6. Échec d'envoi (message:out:failed)
            elif event_type == "message:out:failed":
                error_message = data.get("error", {})
                if isinstance(error_message, dict):
                    error_message = error_message.get("message", "Erreur inconnue")
                
                logger.info(f"message:out:failed reçu: error={error_message}")
                
                return [WassengerWebhookInteraction(
                    contact_phone=self.format_phone_number(data.get("phone", data.get("to", ""))),
                    interaction_type="failed",
                    wassenger_message_id=data.get("id", data.get("waId", "")),
                    timestamp=self._parse_timestamp(data.get("timestamp")),
                    error_message=error_message
                )]
            
            # 7. Anciens événements (rétrocompatibilité message:out:sent/delivered/read)
            elif event_type.startswith("message:out:"):
                interaction = self._parse_status_event(event_type, data)
                if interaction:
                    return [interaction]
            
            else:
                logger.debug(f"Événement Wassenger ignoré: {event_type}")
            
        except Exception as e:
            logger.exception(
                f"Erreur lors du parsing du webhook Wassenger: {str(e)}",
                extra={"payload": payload, "event": event_type}
            )
        
        return []


    def _parse_incoming_message(
        self,
        data: Dict[str, Any]
    ) -> Optional[WassengerWebhookInteraction]:
        """
        Parse un webhook de message entrant Wassenger.
        Note: Cette méthode est conservée pour rétrocompatibilité.
        La logique principale est maintenant dans parse_webhook_payload().
        
        Args:
            data: Données du webhook message
        
        Returns:
            WassengerWebhookInteraction ou None si le parsing échoue
        
        Requirements: 3.1, 3.2
        """
        try:
            return WassengerWebhookInteraction(
                contact_phone=self.format_phone_number(data.get("fromNumber", "")),
                interaction_type="reply",
                content=data.get("body", ""),
                wassenger_message_id=data.get("id", ""),
                timestamp=self._parse_timestamp(data.get("timestamp"))
            )
        except Exception as e:
            logger.error(
                f"Erreur parsing webhook message Wassenger: {str(e)}",
                extra={"data": data}
            )
            return None

    def _parse_status_event(
        self,
        event: str,
        data: Dict[str, Any]
    ) -> Optional[WassengerWebhookInteraction]:
        """
        Parse un webhook de statut de livraison Wassenger (anciens événements).
        Note: Cette méthode est conservée pour rétrocompatibilité avec les anciens
        événements message:out:sent/delivered/read/failed.
        Les nouveaux webhooks utilisent message:update.
        
        Args:
            event: Type d'événement (message:out:sent, etc.)
            data: Données du webhook statut
        
        Returns:
            WassengerWebhookInteraction ou None si le parsing échoue
        
        Requirements: 3.3, 3.4, 3.5, 3.6
        """
        try:
            # Mapper les événements Wassenger vers nos types d'interaction
            event_status_map = {
                "message:out:sent": "sent",
                "message:out:delivered": "delivered",
                "message:out:read": "read",
                "message:out:failed": "failed",
            }
            
            interaction_type = event_status_map.get(event)
            
            if not interaction_type:
                logger.debug(f"Événement Wassenger non mappé: {event}")
                return None
            
            # Extraire le message d'erreur si échec
            error_message = None
            if interaction_type == "failed":
                error_data = data.get("error")
                if isinstance(error_data, dict):
                    error_message = error_data.get("message")
                elif isinstance(error_data, str):
                    error_message = error_data
            
            return WassengerWebhookInteraction(
                contact_phone=self.format_phone_number(data.get("phone", "")),
                interaction_type=interaction_type,
                wassenger_message_id=data.get("id", ""),
                timestamp=self._parse_timestamp(data.get("timestamp")),
                error_message=error_message
            )
            
        except Exception as e:
            logger.error(
                f"Erreur parsing webhook statut Wassenger: {str(e)}",
                extra={"event": event, "data": data}
            )
            return None

    async def close(self):
        """Ferme le client HTTP (no-op car on crée un client par requête)."""
        pass  # Les clients sont fermés après chaque requête


# Instance singleton du service
# Note: L'initialisation peut échouer si les variables d'environnement ne sont pas configurées
# Dans ce cas, le service sera None et devra être initialisé manuellement
try:
    wassenger_service = WassengerService()
except Exception as e:
    logger.warning(f"Impossible d'initialiser WassengerService: {e}")
    wassenger_service = None
