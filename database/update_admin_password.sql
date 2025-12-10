-- ============================================
-- Mise à jour du mot de passe Admin
-- ============================================
-- Ce script met à jour le hash du mot de passe pour l'admin existant
-- Mot de passe: Admin123!
-- ============================================

UPDATE users 
SET password_hash = '$2b$12$k22AFmd2WDRLuPhBaiGwhOZSW/qBeOsaNGlbkjccXirLDfKBJ39ZG',
    updated_at = CURRENT_TIMESTAMP
WHERE email = 'admin@chatbot.local';

-- Vérification
SELECT id, email, role, is_active, 
       LEFT(password_hash, 20) || '...' as password_hash_preview,
       updated_at
FROM users 
WHERE email = 'admin@chatbot.local';
