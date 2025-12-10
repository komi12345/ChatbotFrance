-- ============================================
-- Migration: Add WhatsApp Verification Fields
-- ============================================
-- This migration adds columns to track WhatsApp verification status
-- for contacts, enabling filtering and display of verification badges.
--
-- Requirements: 1.2, 4.2
-- ============================================

-- Add whatsapp_verified column to contacts table
-- NULL = not verified yet, TRUE = WhatsApp active, FALSE = not on WhatsApp
ALTER TABLE contacts 
ADD COLUMN IF NOT EXISTS whatsapp_verified BOOLEAN DEFAULT NULL;

-- Add verified_at timestamp to track when verification was performed
ALTER TABLE contacts 
ADD COLUMN IF NOT EXISTS verified_at TIMESTAMP DEFAULT NULL;

-- Create index for filtering contacts by WhatsApp verification status
-- This improves performance when filtering contacts list by status
CREATE INDEX IF NOT EXISTS idx_contacts_whatsapp_verified 
ON contacts(whatsapp_verified);

-- Add comments for documentation
COMMENT ON COLUMN contacts.whatsapp_verified IS 'WhatsApp verification status: TRUE=verified WhatsApp user, FALSE=not on WhatsApp, NULL=not verified';
COMMENT ON COLUMN contacts.verified_at IS 'Timestamp of last WhatsApp verification check';
