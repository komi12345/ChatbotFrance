#!/usr/bin/env python3
"""
Script de vérification complète du setup backend
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

def main():
    print("🔍 Vérification du setup backend...")
    print("=" * 60)
    
    errors = []
    
    # 1. Vérifier les variables d'environnement
    print("\n1. Variables d'environnement:")
    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_KEY", 
        "SUPABASE_SERVICE_ROLE_KEY",
        "SECRET_KEY"
    ]
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            display = value[:20] + "..." if len(value) > 20 else value
            print(f"   ✅ {var}: {display}")
        else:
            print(f"   ❌ {var}: MANQUANT")
            errors.append(f"Variable {var} manquante")
    
    # 2. Tester la connexion Supabase
    print("\n2. Connexion Supabase:")
    try:
        from app.supabase_client import get_supabase_db
        db = get_supabase_db()
        users = db.get_users(skip=0, limit=1)
        print(f"   ✅ Connexion réussie ({len(users)} utilisateur(s) trouvé(s))")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        errors.append(f"Connexion Supabase: {e}")
    
    # 3. Tester l'import de l'application
    print("\n3. Application FastAPI:")
    try:
        from app.main import app
        print(f"   ✅ Application importée: {app.title} v{app.version}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        errors.append(f"Import FastAPI: {e}")
    
    # 4. Résumé
    print("\n" + "=" * 60)
    if errors:
        print(f"❌ {len(errors)} erreur(s) détectée(s):")
        for err in errors:
            print(f"   - {err}")
        return 1
    else:
        print("🎉 Setup vérifié avec succès!")
        print("\nPour démarrer le serveur:")
        print("   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
        return 0

if __name__ == "__main__":
    sys.exit(main())
