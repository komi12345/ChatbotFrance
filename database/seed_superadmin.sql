-- ============================================
-- Seed Super Admin - Chatbot WhatsApp
-- ============================================
-- Ce script crée le compte Super Admin initial.
-- Le mot de passe doit être hashé avec bcrypt avant insertion.
-- 
-- Exigences : 18.5
-- ============================================

-- IMPORTANT: Le mot de passe ci-dessous est un hash bcrypt de "SuperAdmin123!"
-- En production, générez un nouveau hash avec un mot de passe sécurisé.
-- 
-- Pour générer un hash bcrypt en Python:
-- from passlib.context import CryptContext
-- pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
-- hash = pwd_context.hash("VotreMotDePasse")

-- Suppression du Super Admin existant (si présent)
DELETE FROM users WHERE email = 'superadmin@chatbot.local';

-- Insertion du Super Admin
-- Hash bcrypt pour "SuperAdmin123!" avec 12 rounds (généré avec bcrypt directement)
INSERT INTO users (email, password_hash, role, is_active, created_at, updated_at)
VALUES (
    'superadmin@chatbot.local',
    '$2b$12$Q38zmJzj7qyV4oD3p5MjSOV8ZPYC9SauZ0URKDihCaFtAaolYXyZK',
    'super_admin',
    TRUE,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- Vérification de l'insertion
SELECT id, email, role, is_active, created_at 
FROM users 
WHERE role = 'super_admin';

-- ============================================
-- Instructions post-installation
-- ============================================
-- 1. Connectez-vous avec superadmin@chatbot.local / SuperAdmin123!
-- 2. Changez immédiatement le mot de passe via le dashboard
-- 3. Créez les comptes Admin nécessaires
-- ============================================
