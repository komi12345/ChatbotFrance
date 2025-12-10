"""
Configuration de la base de données
Note: Ce fichier est conservé pour la compatibilité mais n'est plus utilisé.
La connexion à la base de données se fait maintenant via le client Supabase.
Voir: app/supabase_client.py
"""

# Ce fichier est déprécié - utiliser app/supabase_client.py à la place
# Les fonctions ci-dessous sont conservées pour éviter les erreurs d'import
# mais ne doivent plus être utilisées

def get_db():
    """
    DÉPRÉCIÉ: Utiliser get_supabase_db() de app/supabase_client.py
    """
    raise NotImplementedError(
        "get_db() est déprécié. Utilisez get_supabase_db() de app/supabase_client.py"
    )


def init_db():
    """
    DÉPRÉCIÉ: Les tables sont gérées directement dans Supabase
    """
    raise NotImplementedError(
        "init_db() est déprécié. Les tables sont gérées dans Supabase."
    )
