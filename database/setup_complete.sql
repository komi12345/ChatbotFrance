-- ============================================
-- Script Complet de Configuration - Chatbot WhatsApp
-- ============================================
-- Ce script combine tous les scripts SQL en un seul fichier
-- pour une installation rapide dans Supabase.
-- 
-- INSTRUCTIONS:
-- 1. Ouvrez Supabase Dashboard > SQL Editor
-- 2. Créez une nouvelle requête
-- 3. Copiez-collez ce fichier entier
-- 4. Exécutez (Ctrl+Enter ou bouton Run)
-- 
-- Exigences : 18.1, 18.2, 18.3, 18.4, 18.5, 18.6
-- ============================================

-- ============================================
-- PARTIE 1: SCHÉMA DE BASE DE DONNÉES
-- ============================================

-- Suppression des tables existantes (dans l'ordre inverse des dépendances)
DROP TABLE IF EXISTS interactions CASCADE;
DROP TABLE IF EXISTS messages CASCADE;
DROP TABLE IF EXISTS campaign_categories CASCADE;
DROP TABLE IF EXISTS category_contacts CASCADE;
DROP TABLE IF EXISTS campaigns CASCADE;
DROP TABLE IF EXISTS contacts CASCADE;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Table users (Super Admin et Admin)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('super_admin', 'admin')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- Table categories
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    color VARCHAR(50),
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_categories_created_by ON categories(created_by);


-- Table contacts
CREATE TABLE contacts (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL,
    country_code VARCHAR(5) NOT NULL,
    full_number VARCHAR(25) UNIQUE NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_contacts_full_number ON contacts(full_number);
CREATE INDEX idx_contacts_created_by ON contacts(created_by);

-- Table de jonction category_contacts (many-to-many)
CREATE TABLE category_contacts (
    id SERIAL PRIMARY KEY,
    category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
    contact_id INTEGER REFERENCES contacts(id) ON DELETE CASCADE,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(category_id, contact_id)
);

CREATE INDEX idx_category_contacts_category ON category_contacts(category_id);
CREATE INDEX idx_category_contacts_contact ON category_contacts(contact_id);

-- Table campaigns
CREATE TABLE campaigns (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    message_1 TEXT NOT NULL,
    message_2 TEXT,
    template_name VARCHAR(100),
    status VARCHAR(50) DEFAULT 'draft' CHECK (status IN ('draft', 'sending', 'completed', 'failed')),
    total_recipients INTEGER DEFAULT 0,
    sent_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    interaction_count INTEGER DEFAULT 0,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_campaigns_created_by ON campaigns(created_by);
CREATE INDEX idx_campaigns_status ON campaigns(status);

-- Table de jonction campaign_categories
CREATE TABLE campaign_categories (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER REFERENCES campaigns(id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
    UNIQUE(campaign_id, category_id)
);

CREATE INDEX idx_campaign_categories_campaign ON campaign_categories(campaign_id);
CREATE INDEX idx_campaign_categories_category ON campaign_categories(category_id);

-- Table messages (tracking individuel)
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER REFERENCES campaigns(id) ON DELETE CASCADE,
    contact_id INTEGER REFERENCES contacts(id) ON DELETE CASCADE,
    message_type VARCHAR(20) CHECK (message_type IN ('message_1', 'message_2')),
    content TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'delivered', 'read', 'failed')),
    whatsapp_message_id VARCHAR(255),
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    sent_at TIMESTAMP,
    delivered_at TIMESTAMP,
    read_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_messages_campaign ON messages(campaign_id);
CREATE INDEX idx_messages_contact ON messages(contact_id);
CREATE INDEX idx_messages_status ON messages(status);
CREATE INDEX idx_messages_whatsapp_id ON messages(whatsapp_message_id);

-- Table interactions (webhooks reçus)
CREATE TABLE interactions (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER REFERENCES campaigns(id) ON DELETE CASCADE,
    contact_id INTEGER REFERENCES contacts(id) ON DELETE CASCADE,
    message_id INTEGER REFERENCES messages(id) ON DELETE SET NULL,
    interaction_type VARCHAR(50) CHECK (interaction_type IN ('reply', 'reaction', 'read', 'delivered')),
    content TEXT,
    whatsapp_message_id VARCHAR(255),
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_interactions_campaign ON interactions(campaign_id);
CREATE INDEX idx_interactions_contact ON interactions(contact_id);
CREATE INDEX idx_interactions_message ON interactions(message_id);
CREATE INDEX idx_interactions_type ON interactions(interaction_type);

-- Fonction pour mettre à jour updated_at automatiquement
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers pour updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_categories_updated_at BEFORE UPDATE ON categories FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_contacts_updated_at BEFORE UPDATE ON contacts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_campaigns_updated_at BEFORE UPDATE ON campaigns FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_messages_updated_at BEFORE UPDATE ON messages FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- ============================================
-- PARTIE 2: ROW LEVEL SECURITY (RLS)
-- ============================================

-- Activer RLS sur toutes les tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE category_contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE campaign_categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE interactions ENABLE ROW LEVEL SECURITY;

-- Politiques pour users
CREATE POLICY users_select_policy ON users FOR SELECT
    USING ((auth.jwt() ->> 'role') = 'super_admin' OR id = (auth.jwt() ->> 'user_id')::integer);
CREATE POLICY users_insert_policy ON users FOR INSERT
    WITH CHECK ((auth.jwt() ->> 'role') = 'super_admin');
CREATE POLICY users_update_policy ON users FOR UPDATE
    USING ((auth.jwt() ->> 'role') = 'super_admin' OR id = (auth.jwt() ->> 'user_id')::integer);
CREATE POLICY users_delete_policy ON users FOR DELETE
    USING ((auth.jwt() ->> 'role') = 'super_admin');

-- Politiques pour categories
CREATE POLICY categories_select_policy ON categories FOR SELECT
    USING (created_by = (auth.jwt() ->> 'user_id')::integer OR (auth.jwt() ->> 'role') = 'super_admin');
CREATE POLICY categories_insert_policy ON categories FOR INSERT
    WITH CHECK (created_by = (auth.jwt() ->> 'user_id')::integer);
CREATE POLICY categories_update_policy ON categories FOR UPDATE
    USING (created_by = (auth.jwt() ->> 'user_id')::integer OR (auth.jwt() ->> 'role') = 'super_admin');
CREATE POLICY categories_delete_policy ON categories FOR DELETE
    USING (created_by = (auth.jwt() ->> 'user_id')::integer OR (auth.jwt() ->> 'role') = 'super_admin');

-- Politiques pour contacts
CREATE POLICY contacts_select_policy ON contacts FOR SELECT
    USING (created_by = (auth.jwt() ->> 'user_id')::integer OR (auth.jwt() ->> 'role') = 'super_admin');
CREATE POLICY contacts_insert_policy ON contacts FOR INSERT
    WITH CHECK (created_by = (auth.jwt() ->> 'user_id')::integer);
CREATE POLICY contacts_update_policy ON contacts FOR UPDATE
    USING (created_by = (auth.jwt() ->> 'user_id')::integer OR (auth.jwt() ->> 'role') = 'super_admin');
CREATE POLICY contacts_delete_policy ON contacts FOR DELETE
    USING (created_by = (auth.jwt() ->> 'user_id')::integer OR (auth.jwt() ->> 'role') = 'super_admin');

-- Politiques pour category_contacts
CREATE POLICY category_contacts_select_policy ON category_contacts FOR SELECT
    USING (category_id IN (SELECT id FROM categories WHERE created_by = (auth.jwt() ->> 'user_id')::integer) OR (auth.jwt() ->> 'role') = 'super_admin');
CREATE POLICY category_contacts_insert_policy ON category_contacts FOR INSERT
    WITH CHECK (category_id IN (SELECT id FROM categories WHERE created_by = (auth.jwt() ->> 'user_id')::integer));
CREATE POLICY category_contacts_delete_policy ON category_contacts FOR DELETE
    USING (category_id IN (SELECT id FROM categories WHERE created_by = (auth.jwt() ->> 'user_id')::integer) OR (auth.jwt() ->> 'role') = 'super_admin');

-- Politiques pour campaigns
CREATE POLICY campaigns_select_policy ON campaigns FOR SELECT
    USING (created_by = (auth.jwt() ->> 'user_id')::integer OR (auth.jwt() ->> 'role') = 'super_admin');
CREATE POLICY campaigns_insert_policy ON campaigns FOR INSERT
    WITH CHECK (created_by = (auth.jwt() ->> 'user_id')::integer);
CREATE POLICY campaigns_update_policy ON campaigns FOR UPDATE
    USING (created_by = (auth.jwt() ->> 'user_id')::integer OR (auth.jwt() ->> 'role') = 'super_admin');
CREATE POLICY campaigns_delete_policy ON campaigns FOR DELETE
    USING (created_by = (auth.jwt() ->> 'user_id')::integer OR (auth.jwt() ->> 'role') = 'super_admin');

-- Politiques pour campaign_categories
CREATE POLICY campaign_categories_select_policy ON campaign_categories FOR SELECT
    USING (campaign_id IN (SELECT id FROM campaigns WHERE created_by = (auth.jwt() ->> 'user_id')::integer) OR (auth.jwt() ->> 'role') = 'super_admin');
CREATE POLICY campaign_categories_insert_policy ON campaign_categories FOR INSERT
    WITH CHECK (campaign_id IN (SELECT id FROM campaigns WHERE created_by = (auth.jwt() ->> 'user_id')::integer));
CREATE POLICY campaign_categories_delete_policy ON campaign_categories FOR DELETE
    USING (campaign_id IN (SELECT id FROM campaigns WHERE created_by = (auth.jwt() ->> 'user_id')::integer) OR (auth.jwt() ->> 'role') = 'super_admin');

-- Politiques pour messages
CREATE POLICY messages_select_policy ON messages FOR SELECT
    USING (campaign_id IN (SELECT id FROM campaigns WHERE created_by = (auth.jwt() ->> 'user_id')::integer) OR (auth.jwt() ->> 'role') = 'super_admin');
CREATE POLICY messages_insert_policy ON messages FOR INSERT
    WITH CHECK (campaign_id IN (SELECT id FROM campaigns WHERE created_by = (auth.jwt() ->> 'user_id')::integer));
CREATE POLICY messages_update_policy ON messages FOR UPDATE
    USING (campaign_id IN (SELECT id FROM campaigns WHERE created_by = (auth.jwt() ->> 'user_id')::integer) OR (auth.jwt() ->> 'role') = 'super_admin');

-- Politiques pour interactions
CREATE POLICY interactions_select_policy ON interactions FOR SELECT
    USING (campaign_id IN (SELECT id FROM campaigns WHERE created_by = (auth.jwt() ->> 'user_id')::integer) OR (auth.jwt() ->> 'role') = 'super_admin');
CREATE POLICY interactions_insert_policy ON interactions FOR INSERT
    WITH CHECK (true);  -- Les webhooks utilisent le service role


-- ============================================
-- PARTIE 3: SEED SUPER ADMIN
-- ============================================

-- Suppression du Super Admin existant (si présent)
DELETE FROM users WHERE email = 'superadmin@chatbot.local';

-- Insertion du Super Admin
-- Hash bcrypt pour "SuperAdmin123!" avec 12 rounds
INSERT INTO users (email, password_hash, role, is_active, created_at, updated_at)
VALUES (
    'superadmin@chatbot.local',
    '$2b$12$CgKhSUDkk1XjSpjo2.mzNutwmfGx76Fg75JSIT5zHiiTaCDV1WmzS',
    'super_admin',
    TRUE,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- ============================================
-- PARTIE 4: SEED ADMIN DE TEST
-- ============================================

-- Suppression de l'Admin de test existant (si présent)
DELETE FROM users WHERE email = 'admin@chatbot.local';

-- Insertion de l'Admin de test
-- Hash bcrypt pour "Admin123!" avec 12 rounds
INSERT INTO users (email, password_hash, role, is_active, created_at, updated_at)
VALUES (
    'admin@chatbot.local',
    '$2b$12$fEciaFx7JDBaBB5/0ZDEAefz57qTCg0m/pwRxCX6ug57BXob.JvzG',
    'admin',
    TRUE,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

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

-- ============================================
-- VÉRIFICATION FINALE
-- ============================================

SELECT '=== INSTALLATION TERMINÉE ===' as status;
SELECT 'Tables créées:' as info, COUNT(*) as count FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
SELECT 'Utilisateurs:' as info, COUNT(*) as count FROM users;
SELECT 'Catégories:' as info, COUNT(*) as count FROM categories;
SELECT 'Contacts:' as info, COUNT(*) as count FROM contacts;
SELECT 'Associations:' as info, COUNT(*) as count FROM category_contacts;

-- ============================================
-- IDENTIFIANTS PAR DÉFAUT
-- ============================================
-- Super Admin: superadmin@chatbot.local / SuperAdmin123!
-- Admin Test:  admin@chatbot.local / Admin123!
-- 
-- ⚠️ CHANGEZ CES MOTS DE PASSE EN PRODUCTION!
-- ============================================
