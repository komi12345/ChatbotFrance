-- Migration: Ajouter les colonnes de statistiques à la table campaigns
-- Date: 2025-12-28
-- Description: Ajoute les colonnes delivered_count et read_count pour le suivi des statistiques

-- Ajouter delivered_count si elle n'existe pas
ALTER TABLE campaigns 
ADD COLUMN IF NOT EXISTS delivered_count INTEGER DEFAULT 0;

-- Ajouter read_count si elle n'existe pas
ALTER TABLE campaigns 
ADD COLUMN IF NOT EXISTS read_count INTEGER DEFAULT 0;

-- Ajouter sent_count si elle n'existe pas
ALTER TABLE campaigns 
ADD COLUMN IF NOT EXISTS sent_count INTEGER DEFAULT 0;

-- Ajouter failed_count si elle n'existe pas
ALTER TABLE campaigns 
ADD COLUMN IF NOT EXISTS failed_count INTEGER DEFAULT 0;

-- Ajouter total_recipients si elle n'existe pas
ALTER TABLE campaigns 
ADD COLUMN IF NOT EXISTS total_recipients INTEGER DEFAULT 0;

-- Rafraîchir le cache du schéma PostgREST
NOTIFY pgrst, 'reload schema';
