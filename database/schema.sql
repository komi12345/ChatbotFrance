-- ============================================
-- Schéma de Base de Données - Chatbot WhatsApp
-- ============================================
-- Ce script crée toutes les tables nécessaires pour le système
-- de chatbot WhatsApp avec dashboard d'administration.
-- 
-- Exigences : 18.1, 18.2, 18.3
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

-- ============================================
-- Table users (Super Admin et Admin)
-- ============================================
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('super_admin', 'admin')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour recherche par email
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- ============================================
-- Table categories
-- ============================================
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    color VARCHAR(50),
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour recherche par créateur
CREATE INDEX idx_categories_created_by ON categories(created_by);


-- ============================================
-- Table contacts
-- ============================================
CREATE TABLE contacts (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL,
    country_code VARCHAR(5) NOT NULL,
    full_number VARCHAR(25) UNIQUE NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    whatsapp_verified BOOLEAN DEFAULT NULL,
    verified_at TIMESTAMP DEFAULT NULL,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour recherche par numéro complet
CREATE INDEX idx_contacts_full_number ON contacts(full_number);
CREATE INDEX idx_contacts_created_by ON contacts(created_by);
-- Index pour filtrage par statut de vérification WhatsApp
CREATE INDEX idx_contacts_whatsapp_verified ON contacts(whatsapp_verified);

-- ============================================
-- Table de jonction category_contacts (many-to-many)
-- ============================================
CREATE TABLE category_contacts (
    id SERIAL PRIMARY KEY,
    category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
    contact_id INTEGER REFERENCES contacts(id) ON DELETE CASCADE,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(category_id, contact_id)
);

-- Index pour les jointures
CREATE INDEX idx_category_contacts_category ON category_contacts(category_id);
CREATE INDEX idx_category_contacts_contact ON category_contacts(contact_id);

-- ============================================
-- Table campaigns
-- ============================================
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

-- Index pour recherche par créateur et statut
CREATE INDEX idx_campaigns_created_by ON campaigns(created_by);
CREATE INDEX idx_campaigns_status ON campaigns(status);

-- ============================================
-- Table de jonction campaign_categories
-- ============================================
CREATE TABLE campaign_categories (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER REFERENCES campaigns(id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
    UNIQUE(campaign_id, category_id)
);

-- Index pour les jointures
CREATE INDEX idx_campaign_categories_campaign ON campaign_categories(campaign_id);
CREATE INDEX idx_campaign_categories_category ON campaign_categories(category_id);


-- ============================================
-- Table messages (tracking individuel)
-- ============================================
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

-- Index pour les requêtes fréquentes
CREATE INDEX idx_messages_campaign ON messages(campaign_id);
CREATE INDEX idx_messages_contact ON messages(contact_id);
CREATE INDEX idx_messages_status ON messages(status);
CREATE INDEX idx_messages_whatsapp_id ON messages(whatsapp_message_id);

-- ============================================
-- Table interactions (webhooks reçus)
-- ============================================
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

-- Index pour les requêtes fréquentes
CREATE INDEX idx_interactions_campaign ON interactions(campaign_id);
CREATE INDEX idx_interactions_contact ON interactions(contact_id);
CREATE INDEX idx_interactions_message ON interactions(message_id);
CREATE INDEX idx_interactions_type ON interactions(interaction_type);

-- ============================================
-- Fonction pour mettre à jour updated_at automatiquement
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers pour updated_at
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_categories_updated_at
    BEFORE UPDATE ON categories
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_contacts_updated_at
    BEFORE UPDATE ON contacts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_campaigns_updated_at
    BEFORE UPDATE ON campaigns
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_messages_updated_at
    BEFORE UPDATE ON messages
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- Commentaires sur les tables
-- ============================================
COMMENT ON TABLE users IS 'Utilisateurs du système (Super Admin et Admin)';
COMMENT ON TABLE categories IS 'Catégories pour regrouper les contacts';
COMMENT ON TABLE contacts IS 'Contacts WhatsApp avec numéros internationaux';
COMMENT ON COLUMN contacts.whatsapp_verified IS 'WhatsApp verification status: TRUE=verified WhatsApp user, FALSE=not on WhatsApp, NULL=not verified';
COMMENT ON COLUMN contacts.verified_at IS 'Timestamp of last WhatsApp verification check';
COMMENT ON TABLE category_contacts IS 'Association many-to-many entre catégories et contacts';
COMMENT ON TABLE campaigns IS 'Campagnes d''envoi de messages';
COMMENT ON TABLE campaign_categories IS 'Association many-to-many entre campagnes et catégories';
COMMENT ON TABLE messages IS 'Messages individuels envoyés avec tracking de statut';
COMMENT ON TABLE interactions IS 'Interactions reçues via webhooks WhatsApp';
