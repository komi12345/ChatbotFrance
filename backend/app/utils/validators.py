"""
Validateurs personnalisés pour les données - Numéros de téléphone, URLs, etc.
"""
import re
from typing import Optional, Tuple

from app.utils.constants import (
    VALID_COUNTRY_CODES,
    MIN_PHONE_LENGTH,
    MAX_PHONE_LENGTH,
)


def validate_country_code(country_code: str) -> Tuple[bool, Optional[str]]:
    """
    Valide un indicatif pays.
    
    Args:
        country_code: L'indicatif pays à valider (ex: "+33")
        
    Returns:
        Tuple (is_valid, error_message)
        - is_valid: True si l'indicatif est valide
        - error_message: Message d'erreur si invalide, None sinon
    """
    if not country_code:
        return False, "L'indicatif pays est requis"
    
    # Vérifier le format de base
    if not country_code.startswith("+"):
        return False, "L'indicatif pays doit commencer par '+'"
    
    # Vérifier que le reste est numérique
    code_digits = country_code[1:]
    if not code_digits.isdigit():
        return False, "L'indicatif pays doit contenir uniquement des chiffres après le '+'"
    
    # Vérifier la longueur (1 à 4 chiffres)
    if len(code_digits) < 1 or len(code_digits) > 4:
        return False, "L'indicatif pays doit contenir entre 1 et 4 chiffres"
    
    # Vérifier si l'indicatif est dans la liste des indicatifs valides
    if country_code not in VALID_COUNTRY_CODES:
        return False, f"L'indicatif pays '{country_code}' n'est pas reconnu"
    
    return True, None


def validate_phone_number(phone_number: str) -> Tuple[bool, Optional[str]]:
    """
    Valide un numéro de téléphone (sans indicatif pays).
    
    Args:
        phone_number: Le numéro de téléphone à valider
        
    Returns:
        Tuple (is_valid, error_message)
        - is_valid: True si le numéro est valide
        - error_message: Message d'erreur si invalide, None sinon
    """
    if not phone_number:
        return False, "Le numéro de téléphone est requis"
    
    # Nettoyer le numéro (retirer espaces et tirets)
    cleaned = phone_number.replace(" ", "").replace("-", "").replace(".", "")
    
    # Vérifier que le numéro ne contient que des chiffres
    if not cleaned.isdigit():
        return False, "Le numéro de téléphone ne doit contenir que des chiffres"
    
    # Vérifier la longueur
    if len(cleaned) < MIN_PHONE_LENGTH:
        return False, f"Le numéro de téléphone doit contenir au moins {MIN_PHONE_LENGTH} chiffres"
    
    if len(cleaned) > MAX_PHONE_LENGTH:
        return False, f"Le numéro de téléphone ne doit pas dépasser {MAX_PHONE_LENGTH} chiffres"
    
    return True, None


def clean_phone_number(phone_number: str) -> str:
    """
    Nettoie un numéro de téléphone en retirant les caractères non numériques.
    
    Args:
        phone_number: Le numéro de téléphone à nettoyer
        
    Returns:
        Le numéro nettoyé (uniquement des chiffres)
    """
    return phone_number.replace(" ", "").replace("-", "").replace(".", "")


def format_full_number(country_code: str, phone_number: str) -> str:
    """
    Formate un numéro complet avec indicatif pays.
    
    Args:
        country_code: L'indicatif pays (ex: "+33")
        phone_number: Le numéro de téléphone (ex: "612345678")
        
    Returns:
        Le numéro complet formaté (ex: "+33612345678")
    """
    cleaned_phone = clean_phone_number(phone_number)
    return f"{country_code}{cleaned_phone}"


def validate_full_phone_number(
    country_code: str, 
    phone_number: str
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Valide un numéro de téléphone complet (indicatif + numéro).
    
    Args:
        country_code: L'indicatif pays (ex: "+33")
        phone_number: Le numéro de téléphone (ex: "612345678")
        
    Returns:
        Tuple (is_valid, error_message, full_number)
        - is_valid: True si le numéro complet est valide
        - error_message: Message d'erreur si invalide, None sinon
        - full_number: Le numéro complet formaté si valide, None sinon
    """
    # Valider l'indicatif pays
    is_valid_code, code_error = validate_country_code(country_code)
    if not is_valid_code:
        return False, code_error, None
    
    # Valider le numéro de téléphone
    is_valid_phone, phone_error = validate_phone_number(phone_number)
    if not is_valid_phone:
        return False, phone_error, None
    
    # Formater le numéro complet
    full_number = format_full_number(country_code, phone_number)
    
    return True, None, full_number


def validate_url(url: str) -> Tuple[bool, Optional[str]]:
    """
    Valide une URL.
    
    Args:
        url: L'URL à valider
        
    Returns:
        Tuple (is_valid, error_message)
        - is_valid: True si l'URL est valide
        - error_message: Message d'erreur si invalide, None sinon
    """
    if not url:
        return False, "L'URL est requise"
    
    # Pattern pour valider les URLs (http, https, wa.me)
    url_pattern = re.compile(
        r'^(https?://|wa\.me/)'  # Protocole http, https ou wa.me
        r'[a-zA-Z0-9]'  # Premier caractère du domaine
        r'[a-zA-Z0-9\-\.]*'  # Reste du domaine
        r'[a-zA-Z0-9]'  # Dernier caractère du domaine
        r'(\.[a-zA-Z]{2,})?'  # Extension de domaine (optionnel pour wa.me)
        r'(:\d+)?'  # Port optionnel
        r'(/[^\s]*)?$'  # Chemin optionnel
    )
    
    # Pattern simplifié pour wa.me
    wame_pattern = re.compile(r'^wa\.me/\d+$')
    
    if wame_pattern.match(url):
        return True, None
    
    if not url_pattern.match(url):
        return False, "Format d'URL invalide. Utilisez http://, https:// ou wa.me/"
    
    return True, None


def extract_urls_from_text(text: str) -> list:
    """
    Extrait toutes les URLs d'un texte.
    
    Args:
        text: Le texte à analyser
        
    Returns:
        Liste des URLs trouvées
    """
    url_pattern = re.compile(
        r'(https?://[^\s]+|wa\.me/[^\s]+)'
    )
    return url_pattern.findall(text)


def validate_message_content(content: str) -> Tuple[bool, Optional[str]]:
    """
    Valide le contenu d'un message et ses URLs.
    
    Args:
        content: Le contenu du message à valider
        
    Returns:
        Tuple (is_valid, error_message)
        - is_valid: True si le contenu est valide
        - error_message: Message d'erreur si invalide, None sinon
    """
    if not content or not content.strip():
        return False, "Le contenu du message est requis"
    
    # Extraire et valider les URLs
    urls = extract_urls_from_text(content)
    for url in urls:
        is_valid, error = validate_url(url)
        if not is_valid:
            return False, f"URL invalide dans le message: {url}"
    
    return True, None
