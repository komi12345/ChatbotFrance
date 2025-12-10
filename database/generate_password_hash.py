#!/usr/bin/env python3
"""
Script pour générer des hashes bcrypt pour les mots de passe.
Utilisez ce script pour créer des hashes sécurisés avant d'exécuter les seeds.

Usage:
    python generate_password_hash.py "VotreMotDePasse"
    
Ou en mode interactif:
    python generate_password_hash.py
"""

import sys

try:
    import bcrypt
except ImportError:
    print("Erreur: bcrypt n'est pas installé.")
    print("Installez-le avec: pip install bcrypt")
    sys.exit(1)

# Configuration bcrypt avec 12 rounds (recommandé)
BCRYPT_ROUNDS = 12


def generate_hash(password: str) -> str:
    """Génère un hash bcrypt pour le mot de passe donné."""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_hash(password: str, hashed: str) -> bool:
    """Vérifie qu'un mot de passe correspond à son hash."""
    password_bytes = password.encode('utf-8')
    hashed_bytes = hashed.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def main():
    if len(sys.argv) > 1:
        # Mode ligne de commande
        password = sys.argv[1]
    else:
        # Mode interactif
        print("=" * 50)
        print("Générateur de Hash Bcrypt")
        print("=" * 50)
        password = input("Entrez le mot de passe à hasher: ")
    
    if not password:
        print("Erreur: Le mot de passe ne peut pas être vide.")
        sys.exit(1)
    
    # Générer le hash
    hashed = generate_hash(password)
    
    print("\n" + "=" * 50)
    print("Hash généré avec succès!")
    print("=" * 50)
    print(f"\nMot de passe: {password}")
    print(f"Hash bcrypt:  {hashed}")
    
    # Vérification
    if verify_hash(password, hashed):
        print("\n✓ Vérification réussie: le hash est valide")
    else:
        print("\n✗ Erreur: la vérification a échoué")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("Copiez ce hash dans vos fichiers SQL seed:")
    print("=" * 50)
    print(f"\npassword_hash = '{hashed}'")
    print()


if __name__ == "__main__":
    main()
