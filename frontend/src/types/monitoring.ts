/**
 * Types for WhatsApp Monitoring System
 * Requirements: 4.1
 */

/**
 * Alert level based on daily message counter percentage
 * - ok: 0-75% (0-135 messages)
 * - attention: 76-90% (136-162 messages)
 * - danger: 91-100% (163-180 messages)
 * - blocked: >100% (>180 messages)
 */
export type AlertLevel = 'ok' | 'attention' | 'danger' | 'blocked';

/**
 * Real-time monitoring statistics from the backend
 * Returned by GET /api/monitoring/stats
 */
export interface MonitoringStats {
  /** Number of Message 1 (initial contact) sent today */
  message_1_count: number;
  /** Number of Message 2 (follow-up) sent today */
  message_2_count: number;
  /** Total messages sent today (message_1 + message_2) */
  total_sent: number;
  /** Number of errors today */
  error_count: number;
  /** Daily message limit (180) */
  daily_limit: number;
  /** Messages remaining before limit (180 - total_sent) */
  remaining: number;
  /** Current alert level based on usage percentage */
  alert_level: AlertLevel;
  /** Interaction rate (message_2 / message_1) */
  interaction_rate: number;
  /** Estimated contacts that can still be contacted today */
  remaining_capacity: number;
  /** Whether message sending is currently blocked */
  is_blocked: boolean;
  /** Timestamp of last sync with Supabase */
  last_sync: string | null;
}

/**
 * Daily history entry for the 7-day chart
 * Returned by GET /api/monitoring/history
 */
export interface DailyHistory {
  /** Date in YYYY-MM-DD format */
  date: string;
  /** Number of Message 1 sent on this day */
  message_1: number;
  /** Number of Message 2 sent on this day */
  message_2: number;
  /** Number of errors on this day */
  errors: number;
}

/**
 * Recent error entry
 * Returned by GET /api/monitoring/errors
 */
export interface RecentError {
  /** Error timestamp in ISO format */
  timestamp: string;
  /** ID of the message that failed (if available) */
  message_id: number | null;
  /** Error code from Wassenger API */
  error_code: string | null;
  /** Human-readable error message */
  error: string;
}

/**
 * Alert level details with percentage and message
 */
export interface AlertLevelInfo {
  /** Alert level */
  level: AlertLevel;
  /** Percentage of daily limit used */
  percentage: number;
  /** User-friendly message in French */
  message: string;
}

/**
 * Remaining capacity details
 */
export interface RemainingCapacity {
  /** Number of contacts that can still be contacted */
  contacts: number;
  /** Number of messages that can still be sent */
  messages: number;
  /** Whether to show a warning (capacity < 10) */
  warning: boolean;
}
