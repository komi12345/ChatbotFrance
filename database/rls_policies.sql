-- ============================================
-- Row Level Security (RLS) Policies - Chatbot WhatsApp
-- ============================================
-- Ce script configure les politiques de sécurité au niveau des lignes
-- pour Supabase afin d'isoler les données par utilisateur.
-- 
-- Exigences : 18.4, 1.6
-- ============================================

-- ============================================
-- Activer RLS sur toutes les tables
-- ============================================
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE category_contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE campaign_categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE interactions ENABLE ROW LEVEL SECURITY;

-- ============================================
-- Politiques pour la table users
-- ============================================
-- Super Admin peut voir tous les utilisateurs
-- Admin ne peut voir que son propre profil

-- SELECT policy
CREATE POLICY users_select_policy ON users
    FOR SELECT
    USING (
        (auth.jwt() ->> 'role') = 'super_admin'
        OR id = (auth.jwt() ->> 'user_id')::integer
    );

-- INSERT policy (Super Admin uniquement)
CREATE POLICY users_insert_policy ON users
    FOR INSERT
    WITH CHECK (
        (auth.jwt() ->> 'role') = 'super_admin'
    );

-- UPDATE policy
CREATE POLICY users_update_policy ON users
    FOR UPDATE
    USING (
        (auth.jwt() ->> 'role') = 'super_admin'
        OR id = (auth.jwt() ->> 'user_id')::integer
    );

-- DELETE policy (Super Admin uniquement)
CREATE POLICY users_delete_policy ON users
    FOR DELETE
    USING (
        (auth.jwt() ->> 'role') = 'super_admin'
    );


-- ============================================
-- Politiques pour la table categories
-- ============================================
-- Admin ne peut voir/modifier que ses propres catégories

-- SELECT policy
CREATE POLICY categories_select_policy ON categories
    FOR SELECT
    USING (
        created_by = (auth.jwt() ->> 'user_id')::integer
        OR (auth.jwt() ->> 'role') = 'super_admin'
    );

-- INSERT policy
CREATE POLICY categories_insert_policy ON categories
    FOR INSERT
    WITH CHECK (
        created_by = (auth.jwt() ->> 'user_id')::integer
    );

-- UPDATE policy
CREATE POLICY categories_update_policy ON categories
    FOR UPDATE
    USING (
        created_by = (auth.jwt() ->> 'user_id')::integer
        OR (auth.jwt() ->> 'role') = 'super_admin'
    );

-- DELETE policy
CREATE POLICY categories_delete_policy ON categories
    FOR DELETE
    USING (
        created_by = (auth.jwt() ->> 'user_id')::integer
        OR (auth.jwt() ->> 'role') = 'super_admin'
    );

-- ============================================
-- Politiques pour la table contacts
-- ============================================
-- Admin ne peut voir/modifier que ses propres contacts

-- SELECT policy
CREATE POLICY contacts_select_policy ON contacts
    FOR SELECT
    USING (
        created_by = (auth.jwt() ->> 'user_id')::integer
        OR (auth.jwt() ->> 'role') = 'super_admin'
    );

-- INSERT policy
CREATE POLICY contacts_insert_policy ON contacts
    FOR INSERT
    WITH CHECK (
        created_by = (auth.jwt() ->> 'user_id')::integer
    );

-- UPDATE policy
CREATE POLICY contacts_update_policy ON contacts
    FOR UPDATE
    USING (
        created_by = (auth.jwt() ->> 'user_id')::integer
        OR (auth.jwt() ->> 'role') = 'super_admin'
    );

-- DELETE policy
CREATE POLICY contacts_delete_policy ON contacts
    FOR DELETE
    USING (
        created_by = (auth.jwt() ->> 'user_id')::integer
        OR (auth.jwt() ->> 'role') = 'super_admin'
    );

-- ============================================
-- Politiques pour la table category_contacts
-- ============================================
-- Basé sur l'appartenance de la catégorie

-- SELECT policy
CREATE POLICY category_contacts_select_policy ON category_contacts
    FOR SELECT
    USING (
        category_id IN (
            SELECT id FROM categories 
            WHERE created_by = (auth.jwt() ->> 'user_id')::integer
        )
        OR (auth.jwt() ->> 'role') = 'super_admin'
    );

-- INSERT policy
CREATE POLICY category_contacts_insert_policy ON category_contacts
    FOR INSERT
    WITH CHECK (
        category_id IN (
            SELECT id FROM categories 
            WHERE created_by = (auth.jwt() ->> 'user_id')::integer
        )
    );

-- DELETE policy
CREATE POLICY category_contacts_delete_policy ON category_contacts
    FOR DELETE
    USING (
        category_id IN (
            SELECT id FROM categories 
            WHERE created_by = (auth.jwt() ->> 'user_id')::integer
        )
        OR (auth.jwt() ->> 'role') = 'super_admin'
    );


-- ============================================
-- Politiques pour la table campaigns
-- ============================================
-- Admin ne peut voir/modifier que ses propres campagnes

-- SELECT policy
CREATE POLICY campaigns_select_policy ON campaigns
    FOR SELECT
    USING (
        created_by = (auth.jwt() ->> 'user_id')::integer
        OR (auth.jwt() ->> 'role') = 'super_admin'
    );

-- INSERT policy
CREATE POLICY campaigns_insert_policy ON campaigns
    FOR INSERT
    WITH CHECK (
        created_by = (auth.jwt() ->> 'user_id')::integer
    );

-- UPDATE policy
CREATE POLICY campaigns_update_policy ON campaigns
    FOR UPDATE
    USING (
        created_by = (auth.jwt() ->> 'user_id')::integer
        OR (auth.jwt() ->> 'role') = 'super_admin'
    );

-- DELETE policy
CREATE POLICY campaigns_delete_policy ON campaigns
    FOR DELETE
    USING (
        created_by = (auth.jwt() ->> 'user_id')::integer
        OR (auth.jwt() ->> 'role') = 'super_admin'
    );

-- ============================================
-- Politiques pour la table campaign_categories
-- ============================================
-- Basé sur l'appartenance de la campagne

-- SELECT policy
CREATE POLICY campaign_categories_select_policy ON campaign_categories
    FOR SELECT
    USING (
        campaign_id IN (
            SELECT id FROM campaigns 
            WHERE created_by = (auth.jwt() ->> 'user_id')::integer
        )
        OR (auth.jwt() ->> 'role') = 'super_admin'
    );

-- INSERT policy
CREATE POLICY campaign_categories_insert_policy ON campaign_categories
    FOR INSERT
    WITH CHECK (
        campaign_id IN (
            SELECT id FROM campaigns 
            WHERE created_by = (auth.jwt() ->> 'user_id')::integer
        )
    );

-- DELETE policy
CREATE POLICY campaign_categories_delete_policy ON campaign_categories
    FOR DELETE
    USING (
        campaign_id IN (
            SELECT id FROM campaigns 
            WHERE created_by = (auth.jwt() ->> 'user_id')::integer
        )
        OR (auth.jwt() ->> 'role') = 'super_admin'
    );

-- ============================================
-- Politiques pour la table messages
-- ============================================
-- Basé sur l'appartenance de la campagne

-- SELECT policy
CREATE POLICY messages_select_policy ON messages
    FOR SELECT
    USING (
        campaign_id IN (
            SELECT id FROM campaigns 
            WHERE created_by = (auth.jwt() ->> 'user_id')::integer
        )
        OR (auth.jwt() ->> 'role') = 'super_admin'
    );

-- INSERT policy
CREATE POLICY messages_insert_policy ON messages
    FOR INSERT
    WITH CHECK (
        campaign_id IN (
            SELECT id FROM campaigns 
            WHERE created_by = (auth.jwt() ->> 'user_id')::integer
        )
    );

-- UPDATE policy
CREATE POLICY messages_update_policy ON messages
    FOR UPDATE
    USING (
        campaign_id IN (
            SELECT id FROM campaigns 
            WHERE created_by = (auth.jwt() ->> 'user_id')::integer
        )
        OR (auth.jwt() ->> 'role') = 'super_admin'
    );

-- ============================================
-- Politiques pour la table interactions
-- ============================================
-- Basé sur l'appartenance de la campagne

-- SELECT policy
CREATE POLICY interactions_select_policy ON interactions
    FOR SELECT
    USING (
        campaign_id IN (
            SELECT id FROM campaigns 
            WHERE created_by = (auth.jwt() ->> 'user_id')::integer
        )
        OR (auth.jwt() ->> 'role') = 'super_admin'
    );

-- INSERT policy (système uniquement via service role)
CREATE POLICY interactions_insert_policy ON interactions
    FOR INSERT
    WITH CHECK (true);  -- Les webhooks utilisent le service role

-- ============================================
-- Note importante pour Supabase
-- ============================================
-- Ces politiques utilisent auth.jwt() qui est disponible dans Supabase.
-- Pour le backend FastAPI, utilisez le service_role_key qui bypass RLS.
-- Les politiques s'appliquent uniquement aux requêtes avec anon_key.
