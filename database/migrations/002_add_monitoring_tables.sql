-- ============================================
-- Migration: Add WhatsApp Monitoring Tables
-- ============================================
-- This migration creates tables for tracking daily message statistics
-- and message errors for the WhatsApp monitoring system.
--
-- Requirements: 6.4, 7.4
-- ============================================

-- ==========================================
-- Table: daily_message_stats
-- ==========================================
-- Stores daily aggregated statistics for WhatsApp messages.
-- Used for historical analysis and persistence of Redis counters.
--
-- Requirements: 7.4

CREATE TABLE IF NOT EXISTS daily_message_stats (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    message_1_count INTEGER DEFAULT 0 NOT NULL,
    message_2_count INTEGER DEFAULT 0 NOT NULL,
    error_count INTEGER DEFAULT 0 NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index on date for efficient lookups and range queries
CREATE INDEX IF NOT EXISTS idx_daily_message_stats_date 
ON daily_message_stats(date);

-- Add comments for documentation
COMMENT ON TABLE daily_message_stats IS 'Daily aggregated statistics for WhatsApp messages';
COMMENT ON COLUMN daily_message_stats.date IS 'Date of the statistics (YYYY-MM-DD)';
COMMENT ON COLUMN daily_message_stats.message_1_count IS 'Number of message_1 (initial) messages sent';
COMMENT ON COLUMN daily_message_stats.message_2_count IS 'Number of message_2 (follow-up) messages sent';
COMMENT ON COLUMN daily_message_stats.error_count IS 'Number of message send errors';

-- ==========================================
-- Table: message_errors
-- ==========================================
-- Stores detailed error information for failed message sends.
-- Used for debugging and error analysis.
--
-- Requirements: 6.4

CREATE TABLE IF NOT EXISTS message_errors (
    id SERIAL PRIMARY KEY,
    message_id INTEGER REFERENCES messages(id) ON DELETE SET NULL,
    error_code VARCHAR(100),
    error_message TEXT,
    occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index on occurred_at for efficient time-based queries
CREATE INDEX IF NOT EXISTS idx_message_errors_occurred_at 
ON message_errors(occurred_at);

-- Add comments for documentation
COMMENT ON TABLE message_errors IS 'Detailed error logs for failed WhatsApp message sends';
COMMENT ON COLUMN message_errors.message_id IS 'Reference to the message that failed (nullable if message was not created)';
COMMENT ON COLUMN message_errors.error_code IS 'Error code from Wassenger API or internal error code';
COMMENT ON COLUMN message_errors.error_message IS 'Detailed error message for debugging';
COMMENT ON COLUMN message_errors.occurred_at IS 'Timestamp when the error occurred';
