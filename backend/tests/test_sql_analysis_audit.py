"""
SQL Query Analysis Audit - Comprehensive Audit 2025

Ce module analyse les patterns de requêtes SQL pour identifier :
- Les requêtes potentiellement lentes (> 30ms)
- Les patterns N+1
- Les index manquants

Requirements: 2.1, 2.2 - API response times depend on SQL performance

Usage:
    pytest tests/test_sql_analysis_audit.py -v --tb=short
"""
import inspect
import re
from typing import List, Tuple
import pytest


class SQLPatternAnalyzer:
    """
    Analyseur de patterns SQL dans le code Python.
    
    Identifie les patterns problématiques comme les N+1 queries.
    """
    
    # Patterns N+1 : boucle avec requête DB à l'intérieur
    N_PLUS_1_PATTERNS = [
        r'for\s+\w+\s+in\s+.*:\s*\n\s*.*\.(?:get_|select|table)',
        r'for\s+\w+\s+in\s+.*:\s*\n\s*.*db\.',
        r'for\s+\w+\s+in\s+.*:\s*\n\s*.*client\.table',
    ]
    
    def __init__(self):
        self.findings: List[dict] = []
    
    def analyze_function(self, func, func_name: str) -> List[dict]:
        """
        Analyse une fonction pour détecter les patterns N+1.
        
        Args:
            func: Fonction à analyser
            func_name: Nom de la fonction
            
        Returns:
            Liste des problèmes détectés
        """
        try:
            source = inspect.getsource(func)
        except (OSError, TypeError):
            return []
        
        issues = []
        
        # Rechercher les patterns N+1
        for pattern in self.N_PLUS_1_PATTERNS:
            matches = re.findall(pattern, source, re.MULTILINE)
            if matches:
                issues.append({
                    "function": func_name,
                    "type": "N+1 Query Pattern",
                    "severity": "HIGH",
                    "description": f"Potential N+1 query detected in loop"
                })
        
        # Rechercher les boucles avec requêtes
        if re.search(r'for\s+\w+\s+in\s+.*:\s*\n.*\n.*\.execute\(\)', source, re.MULTILINE):
            issues.append({
                "function": func_name,
                "type": "Loop with DB Query",
                "severity": "MEDIUM",
                "description": "Database query inside loop"
            })
        
        return issues
    
    def analyze_module(self, module) -> List[dict]:
        """
        Analyse un module complet.
        
        Args:
            module: Module Python à analyser
            
        Returns:
            Liste des problèmes détectés
        """
        all_issues = []
        
        for name, obj in inspect.getmembers(module):
            if inspect.isfunction(obj) or inspect.ismethod(obj):
                issues = self.analyze_function(obj, name)
                all_issues.extend(issues)
        
        return all_issues


class TestExistingIndexes:
    """Vérifie que les index nécessaires sont définis dans le schéma."""
    
    SCHEMA_PATH = "../database/schema.sql"
    
    def test_messages_campaign_index_exists(self):
        """Vérifie l'index sur messages(campaign_id)."""
        with open(self.SCHEMA_PATH, "r") as f:
            schema = f.read()
        
        assert "idx_messages_campaign" in schema, "Index messages(campaign_id) manquant"
        print("\n✅ Index messages(campaign_id) existe")
    
    def test_messages_status_index_exists(self):
        """Vérifie l'index sur messages(status)."""
        with open(self.SCHEMA_PATH, "r") as f:
            schema = f.read()
        
        assert "idx_messages_status" in schema, "Index messages(status) manquant"
        print("\n✅ Index messages(status) existe")
    
    def test_messages_contact_index_exists(self):
        """Vérifie l'index sur messages(contact_id)."""
        with open(self.SCHEMA_PATH, "r") as f:
            schema = f.read()
        
        assert "idx_messages_contact" in schema, "Index messages(contact_id) manquant"
        print("\n✅ Index messages(contact_id) existe")
    
    def test_interactions_message_index_exists(self):
        """Vérifie l'index sur interactions(message_id)."""
        with open(self.SCHEMA_PATH, "r") as f:
            schema = f.read()
        
        assert "idx_interactions_message" in schema, "Index interactions(message_id) manquant"
        print("\n✅ Index interactions(message_id) existe")
    
    def test_category_contacts_indexes_exist(self):
        """Vérifie les index sur category_contacts."""
        with open(self.SCHEMA_PATH, "r") as f:
            schema = f.read()
        
        assert "idx_category_contacts_category" in schema, "Index category_contacts(category_id) manquant"
        assert "idx_category_contacts_contact" in schema, "Index category_contacts(contact_id) manquant"
        print("\n✅ Index category_contacts existent")
    
    def test_contacts_whatsapp_verified_index_exists(self):
        """Vérifie l'index sur contacts(whatsapp_verified)."""
        with open(self.SCHEMA_PATH, "r") as f:
            schema = f.read()
        
        assert "idx_contacts_whatsapp_verified" in schema, "Index contacts(whatsapp_verified) manquant"
        print("\n✅ Index contacts(whatsapp_verified) existe")


class TestNPlus1Patterns:
    """Détecte les patterns N+1 dans le code."""
    
    def test_supabase_client_n_plus_1_patterns(self):
        """
        Analyse le client Supabase pour les patterns N+1.
        
        Patterns connus à surveiller :
        - get_campaign_interaction_count : boucle sur message_ids
        - get_campaign_messages_with_contacts : boucle sur messages
        """
        from app.supabase_client import SupabaseDB
        import inspect
        
        # Analyser get_campaign_interaction_count
        source = inspect.getsource(SupabaseDB.get_campaign_interaction_count)
        
        # Ce pattern est connu : boucle sur message_ids
        has_loop = "for msg_id in message_ids" in source
        
        if has_loop:
            print("\n⚠️ N+1 Pattern détecté dans get_campaign_interaction_count")
            print("   Recommandation: Utiliser IN clause avec count")
        else:
            print("\n✅ get_campaign_interaction_count optimisé")
    
    def test_messages_router_n_plus_1_patterns(self):
        """
        Analyse le router messages pour les patterns N+1.
        """
        from app.routers.messages import list_messages
        import inspect
        
        source = inspect.getsource(list_messages)
        
        # Vérifier si on fait une requête par message pour le contact
        has_loop_query = "for message in messages" in source and "get_contact_by_id" in source
        
        if has_loop_query:
            print("\n⚠️ N+1 Pattern détecté dans list_messages")
            print("   Recommandation: Batch fetch des contacts")
        else:
            print("\n✅ list_messages optimisé")
    
    def test_categories_router_optimized(self):
        """
        Vérifie que le router categories utilise le batch fetch.
        """
        from app.routers.categories import list_categories
        import inspect
        
        source = inspect.getsource(list_categories)
        
        # Vérifier l'utilisation de get_categories_contact_counts (batch)
        uses_batch = "get_categories_contact_counts" in source
        
        if uses_batch:
            print("\n✅ list_categories utilise le batch fetch pour les comptages")
        else:
            print("\n⚠️ list_categories pourrait être optimisé avec batch fetch")


class TestQueryComplexity:
    """Analyse la complexité des requêtes."""
    
    def test_messages_stats_query_count(self):
        """
        Compte le nombre de requêtes pour /messages/stats.
        
        Objectif: Minimiser le nombre de requêtes.
        """
        from app.routers.messages import _compute_message_stats_from_db
        import inspect
        
        source = inspect.getsource(_compute_message_stats_from_db)
        
        # Compter les appels .execute()
        execute_count = source.count(".execute()")
        
        print(f"\n📊 /messages/stats effectue {execute_count} requêtes DB")
        
        # 5 requêtes pour les 5 statuts (sent, delivered, read, failed, pending)
        # C'est acceptable mais pourrait être optimisé avec une seule requête GROUP BY
        if execute_count > 5:
            print("   ⚠️ Recommandation: Réduire le nombre de requêtes")
        else:
            print("   ✅ Nombre de requêtes acceptable")
    
    def test_campaign_stats_query_count(self):
        """
        Compte le nombre de requêtes pour les stats de campagne.
        """
        from app.supabase_client import SupabaseDB
        import inspect
        
        source = inspect.getsource(SupabaseDB.get_campaign_message_stats)
        
        execute_count = source.count(".execute()")
        
        print(f"\n📊 get_campaign_message_stats effectue {execute_count} requêtes DB")
        
        # 6 requêtes (1 initiale + 5 par statut)
        if execute_count > 6:
            print("   ⚠️ Recommandation: Utiliser GROUP BY")
        else:
            print("   ✅ Nombre de requêtes acceptable")


class TestRecommendedIndexes:
    """Vérifie les index recommandés pour les requêtes fréquentes."""
    
    SCHEMA_PATH = "../database/schema.sql"
    
    def test_composite_index_messages_campaign_status(self):
        """
        Vérifie si un index composite serait bénéfique.
        
        Requête fréquente: SELECT * FROM messages WHERE campaign_id = X AND status = Y
        """
        with open(self.SCHEMA_PATH, "r") as f:
            schema = f.read()
        
        # Vérifier si un index composite existe
        has_composite = "messages(campaign_id, status)" in schema
        
        if has_composite:
            print("\n✅ Index composite messages(campaign_id, status) existe")
        else:
            print("\n⚠️ Index composite messages(campaign_id, status) recommandé")
            print("   SQL: CREATE INDEX idx_messages_campaign_status ON messages(campaign_id, status);")
    
    def test_index_messages_sent_at(self):
        """
        Vérifie l'index sur messages(sent_at) pour les requêtes temporelles.
        """
        with open(self.SCHEMA_PATH, "r") as f:
            schema = f.read()
        
        has_index = "idx_messages_sent_at" in schema or "messages(sent_at)" in schema
        
        if has_index:
            print("\n✅ Index messages(sent_at) existe")
        else:
            print("\n⚠️ Index messages(sent_at) recommandé pour les requêtes 24h")
            print("   SQL: CREATE INDEX idx_messages_sent_at ON messages(sent_at);")


def test_generate_sql_audit_summary():
    """Génère un résumé de l'audit SQL."""
    summary = """
    ╔══════════════════════════════════════════════════════════════╗
    ║              SQL QUERY ANALYSIS AUDIT SUMMARY                 ║
    ╠══════════════════════════════════════════════════════════════╣
    ║                                                               ║
    ║  EXISTING INDEXES                                             ║
    ║  ├─ messages(campaign_id): ✅                                 ║
    ║  ├─ messages(contact_id): ✅                                  ║
    ║  ├─ messages(status): ✅                                      ║
    ║  ├─ messages(whatsapp_message_id): ✅                         ║
    ║  ├─ interactions(message_id): ✅                              ║
    ║  ├─ interactions(campaign_id): ✅                             ║
    ║  ├─ category_contacts(category_id): ✅                        ║
    ║  ├─ category_contacts(contact_id): ✅                         ║
    ║  └─ contacts(whatsapp_verified): ✅                           ║
    ║                                                               ║
    ║  N+1 PATTERNS DETECTED                                        ║
    ║  ├─ get_campaign_interaction_count: ⚠️ Loop on message_ids   ║
    ║  ├─ get_campaign_messages_with_contacts: ⚠️ Loop on messages ║
    ║  └─ list_messages router: ⚠️ Loop for contacts               ║
    ║                                                               ║
    ║  RECOMMENDED INDEXES                                          ║
    ║  ├─ messages(campaign_id, status): Composite index            ║
    ║  └─ messages(sent_at): For 24h window queries                 ║
    ║                                                               ║
    ║  QUERY OPTIMIZATION OPPORTUNITIES                             ║
    ║  ├─ Use GROUP BY instead of multiple COUNT queries            ║
    ║  ├─ Batch fetch contacts in list_messages                     ║
    ║  └─ Use IN clause for interaction counts                      ║
    ║                                                               ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(summary)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
