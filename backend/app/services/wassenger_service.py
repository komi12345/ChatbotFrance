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
    "server_error": (
        "Erreur temporaire du serveur Wassenger. "
        "Veuillez réessayer dans quelques instants."
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

    async def check_whatsapp_exists(self, phone: str, max_retries: int = 3) -> WhatsAppExistsResponse:
        """
        Vérifie si un numéro de téléphone est enregistré sur WhatsApp via Wassenger API.
        
        Endpoint: POST /v1/numbers/exists
        Body: {"phone": "+22892146653"}  # Format E164 AVEC + selon doc Wassenger
        
        Documentation officielle Wassenger:
        https://wassenger.com/blog/how-to-verify-a-whatsapp-number-exists
        - Format: E164 avec + (ex: +14155552671)
        - Body: {"phone": "+14158586273"} - PAS de device dans le body
        - Auth: via query param ?token=API_KEY ou header Token: API_KEY
        
        Args:
            phone: Numéro de téléphone à vérifier (avec ou sans +, avec ou sans espaces)
            max_retries: Nombre maximum de tentatives en cas d'erreur serveur (défaut: 3)
        
        Returns:
            WhatsAppExistsResponse avec le résultat de la vérification:
            - exists=True si le numéro est sur WhatsApp
            - exists=False si le numéro n'est pas sur WhatsApp
            - exists=False avec error_code si une erreur s'est produite
        
        Requirements: 1.1, 1.3
        """
        import asyncio
        
        # Timeout pour la vérification WhatsApp (60 secondes)
        VERIFICATION_TIMEOUT = 60.0
        
        # Créer un client HTTP avec le header Token (format Wassenger)
        client = httpx.AsyncClient(
            headers={
                "Token": self.api_key,  # Wassenger utilise "Token" pas "Authorization: Bearer"
                "Content-Type": "application/json"
            },
            timeout=VERIFICATION_TIMEOUT
        )
        
        # Formater le numéro au format E164 avec + (selon documentation Wassenger)
        # D'abord nettoyer le numéro (retirer espaces, tirets, etc.)
        clean_phone = self.format_phone_number(phone)  # Retire tous les caractères non numériques
        
        # Validation du numéro avant d'appeler l'API
        # Un numéro E164 valide doit avoir entre 8 et 15 chiffres
        if len(clean_phone) < 8:
            logger.error(
                f"Numéro trop court pour vérification WhatsApp: {phone} -> {clean_phone} ({len(clean_phone)} chiffres)",
                extra={"phone": phone, "clean_phone": clean_phone, "length": len(clean_phone)}
            )
            return WhatsAppExistsResponse(
                exists=False,
                phone=phone,
                error_code="invalid_phone_number",
                error_message=f"Le numéro est trop court ({len(clean_phone)} chiffres). Un numéro valide doit avoir au moins 8 chiffres."
            )
        
        if len(clean_phone) > 15:
            logger.error(
                f"Numéro trop long pour vérification WhatsApp: {phone} -> {clean_phone} ({len(clean_phone)} chiffres)",
                extra={"phone": phone, "clean_phone": clean_phone, "length": len(clean_phone)}
            )
            return WhatsAppExistsResponse(
                exists=False,
                phone=phone,
                error_code="invalid_phone_number",
                error_message=f"Le numéro est trop long ({len(clean_phone)} chiffres). Un numéro valide ne doit pas dépasser 15 chiffres."
            )
        
        # Toujours ajouter le + au début
        formatted_phone = f"+{clean_phone}"
        
        try:
            logger.info(
                f"Vérification WhatsApp pour {formatted_phone} (original: {phone})",
                extra={
                    "phone": formatted_phone,
                    "original_phone": phone,
                    "clean_phone": clean_phone,
                    "device_id": self.device_id[:8] + "..." if self.device_id else "N/A"
                }
            )
            
            # Appeler l'API Wassenger pour vérifier l'existence
            # Endpoint: POST /v1/numbers/exists avec body {"phone": "+..."}
            # NOTE: L'API n'accepte PAS de "device" dans le body (erreur 400 si présent)
            # Requirements: 1.1
            request_body = {
                "phone": formatted_phone
            }
            
            logger.info(f"Wassenger API request: POST /v1/numbers/exists, body={request_body}, headers=Token: {self.api_key[:12]}...")
            
            response = await client.post(
                f"{self.BASE_URL}/numbers/exists",
                json=request_body
            )
            
            # Logger la réponse brute pour debug - IMPORTANT pour diagnostiquer les erreurs
            logger.info(
                f"Wassenger API response: status={response.status_code}, body={response.text[:500] if response.text else 'empty'}"
            )
            
            # Parser la réponse JSON de manière sécurisée
            response_data = {}
            try:
                if response.text and response.text.strip():
                    response_data = response.json()
            except Exception as json_err:
                logger.warning(
                    f"Impossible de parser la réponse JSON: {json_err}, content={response.text[:200] if response.text else 'empty'}"
                )
            
            # Vérifier le succès de la requête
            # Status 200: numéro trouvé sur WhatsApp (exists=true)
            # Status 404: numéro NON trouvé sur WhatsApp (exists=false) - c'est un résultat valide!
            if response.status_code == 200:
                # Extraire le résultat de la vérification
                exists = response_data.get("exists", True)  # Par défaut True si status 200
                
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
            
            elif response.status_code == 404:
                # 404 = numéro non trouvé sur WhatsApp
                logger.info(
                    f"Vérification WhatsApp terminée: {formatted_phone} -> exists=False (404)",
                    extra={
                        "phone": formatted_phone,
                        "exists": False,
                        "status_code": response.status_code
                    }
                )
                
                return WhatsAppExistsResponse(
                    exists=False,
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
            
            # Gérer les erreurs serveur 5xx (500, 502, 503, 504) avec retry automatique
            # TOUTES les erreurs 5xx sont considérées comme temporaires et méritent un retry
            elif response.status_code >= 500:
                # Détecter si c'est une réponse HTML (erreur proxy/serveur)
                is_html_error = response.text and "<html" in response.text.lower()
                
                logger.warning(
                    f"Erreur serveur {response.status_code} lors de la vérification WhatsApp: {formatted_phone}",
                    extra={
                        "phone": formatted_phone,
                        "status_code": response.status_code,
                        "is_html_error": is_html_error,
                        "max_retries": max_retries,
                        "response_message": response_data.get("message", "")[:200] if response_data else ""
                    }
                )
                
                # Fermer le client actuel
                try:
                    await client.aclose()
                except Exception:
                    pass
                
                # Retry si on a encore des tentatives (TOUJOURS retry sur 5xx)
                if max_retries > 0:
                    wait_time = 10  # Attendre 10 secondes pour les erreurs serveur
                    logger.info(f"Retry vérification WhatsApp pour {formatted_phone} après erreur {response.status_code}, attente {wait_time}s, tentatives restantes: {max_retries}")
                    await asyncio.sleep(wait_time)
                    return await self.check_whatsapp_exists(phone, max_retries - 1)
                
                # Plus de tentatives - retourner erreur appropriée
                # Si c'est un 503 JSON, c'est probablement un problème de session
                if response.status_code == 503 and not is_html_error:
                    error_details = self.get_error_details("device_not_connected")
                    return WhatsAppExistsResponse(
                        exists=False,
                        phone=formatted_phone,
                        error_code="device_not_connected",
                        error_message=error_details["message"]
                    )
                
                # Sinon, erreur serveur générique
                return WhatsAppExistsResponse(
                    exists=False,
                    phone=formatted_phone,
                    error_code="server_error",
                    error_message=f"Erreur serveur Wassenger ({response.status_code}) après plusieurs tentatives. Veuillez réessayer plus tard."
                )
            
            # Gérer les autres erreurs API (4xx)
            else:
                error_code = response_data.get("errorCode", response_data.get("error", "unknown_error"))
                error_message = response_data.get("message", response.text[:200] if response.text else "Erreur inconnue")
                
                # Vérifier si c'est une erreur de format de numéro (400 avec message spécifique)
                if response.status_code == 400 and ("invalid" in str(error_message).lower() or "phone" in str(error_message).lower()):
                    error_code = "invalid_phone_number"
                    error_details = self.get_error_details(error_code)
                    # Ajouter des détails sur le numéro problématique
                    error_message = f"{error_details['message']} Numéro reçu: '{phone}' -> formaté: '{formatted_phone}' ({len(clean_phone)} chiffres)"
                
                logger.error(
                    f"Erreur API Wassenger lors de la vérification: {error_code}",
                    extra={
                        "original_phone": phone,
                        "clean_phone": clean_phone,
                        "formatted_phone": formatted_phone,
                        "phone_length": len(clean_phone),
                        "error_code": error_code,
                        "error_message": error_message,
                        "status_code": response.status_code,
                        "response_text": response.text[:500] if response.text else "empty"
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
