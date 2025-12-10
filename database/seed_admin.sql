-- ============================================
-- Seed Admin de Test - Chatbot WhatsApp
-- ============================================
-- Ce script crée un compte Admin de test pour le développement.
-- NE PAS utiliser en production.
-- 
-- Exigences : 18.6
-- ============================================

-- IMPORTANT: Le mot de passe ci-dessous est un hash bcrypt de "Admin123!"
-- Ce compte est uniquement pour les tests de développement.
-- 
-- Pour générer un hash bcrypt en Python:
-- from passlib.context import CryptContext
-- pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
-- hash = pwd_context.hash("VotreMotDePasse")

-- Suppression de l'Admin de test existant (si présent)
DELETE FROM users WHERE email = 'admin@chatbot.local';

-- Insertion de l'Admin de test
-- Hash bcrypt pour "Admin123!" avec 12 rounds
INSERT INTO users (email, password_hash, role, is_active, created_at, updated_at)
VALUES (
    'admin@chatbot.local',
    '$2b$12$k22AFmd2WDRLuPhBaiGwhOZSW/qBeOsaNGlbkjccXirLDfKBJ39ZG',
    'admin',
    TRUE,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- Vérification de l'insertion
SELECT id, email, role, is_active, created_at 
FROM users 
WHERE email = 'admin@chatbot.local';

-- ============================================
-- Données de test optionnelles
-- ============================================

-- Créer une catégorie de test pour l'Admin
INSERT INTO categories (name, color, created_by, created_at, updated_at)
SELECT 
    'Catégorie Test',
    '#3B82F6',
    id,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
FROM users WHERE email = 'admin@chatbot.local';

-- Créer quelques contacts de test
INSERT INTO contacts (phone_number, country_code, full_number, first_name, last_name, created_by, created_at, updated_at)
SELECT 
    '612345678',
    '+33',
    '+33612345678',
    'Jean',
    'Dupont',
    id,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
FROM users WHERE email = 'admin@chatbot.local';

INSERT INTO contacts (phone_number, country_code, full_number, first_name, last_name, created_by, created_at, updated_at)
SELECT 
    '698765432',
    '+33',
    '+33698765432',
    'Marie',
    'Martin',
    id,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
FROM users WHERE email = 'admin@chatbot.local';

-- Associer les contacts à la catégorie de test
INSERT INTO category_contacts (category_id, contact_id, added_at)
SELECT 
    c.id,
    co.id,
    CURRENT_TIMESTAMP
FROM categories c
CROSS JOIN contacts co
WHERE c.name = 'Catégorie Test'
AND co.created_by = (SELECT id FROM users WHERE email = 'admin@chatbot.local');

-- Vérification des données de test
SELECT 'Catégories créées:' as info, COUNT(*) as count FROM categories;
SELECT 'Contacts créés:' as info, COUNT(*) as count FROM contacts;
SELECT 'Associations créées:' as info, COUNT(*) as count FROM category_contacts;

-- ============================================
-- Identifiants de test
-- ============================================
-- Email: admin@chatbot.local
-- Mot de passe: Admin123!
-- 
-- ATTENTION: Supprimer ce compte en production!
-- ============================================
