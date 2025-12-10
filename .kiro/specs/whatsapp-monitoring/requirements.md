# Requirements Document

## Introduction

Ce document définit les exigences pour un système de monitoring WhatsApp intégré au dashboard d'administration existant. Le système permet de suivre en temps réel le nombre de messages envoyés quotidiennement, d'appliquer une limite stricte de 180 messages/jour pour éviter le bannissement WhatsApp, et d'afficher des alertes visuelles sur le dashboard admin.

Le système utilise une architecture hybride Redis (temps réel) + Supabase (persistance) pour garantir performance et fiabilité. Les alertes sont exclusivement affichées sur le dashboard admin, sans notifications externes (Telegram/Email).

## Glossary

- **Daily_Message_Counter**: Compteur Redis qui suit le nombre de messages WhatsApp envoyés pour la journée en cours
- **Message_Limit**: Limite quotidienne stricte de 180 messages WhatsApp par jour
- **Alert_Level**: Niveau d'alerte basé sur le pourcentage de la limite atteinte (OK, ATTENTION, DANGER, BLOCKED)
- **Monitoring_Service**: Service backend Python qui gère les compteurs Redis et la synchronisation Supabase
- **Monitoring_Dashboard**: Page Next.js `/dashboard/monitoring` affichant les statistiques temps réel
- **Interaction_Rate**: Pourcentage de contacts ayant répondu au Message 1 (déclenchant un Message 2)
- **Remaining_Capacity**: Nombre de contacts pouvant encore être contactés aujourd'hui
- **Daily_Stats_Table**: Table Supabase `daily_message_stats` stockant l'historique quotidien

## Requirements

### Requirement 1

**User Story:** As an administrator, I want to track the number of WhatsApp messages sent today in real-time, so that I can monitor usage and avoid exceeding the daily limit.

#### Acceptance Criteria

1. WHEN a message is successfully sent via Wassenger API THEN the Monitoring_Service SHALL increment the Daily_Message_Counter in Redis
2. WHEN the Daily_Message_Counter is incremented THEN the Monitoring_Service SHALL distinguish between message_1 and message_2 types in separate counters
3. WHEN a new day begins (00:00 UTC) THEN the Monitoring_Service SHALL reset the Daily_Message_Counter to zero
4. WHEN the Daily_Message_Counter is reset THEN the Monitoring_Service SHALL persist the previous day's statistics to the Daily_Stats_Table in Supabase
5. WHEN the API endpoint `/api/monitoring/stats` is called THEN the Monitoring_Service SHALL return the current counter values within 100 milliseconds

### Requirement 2

**User Story:** As an administrator, I want the system to automatically block message sending when the daily limit is reached, so that my WhatsApp account is protected from being banned.

#### Acceptance Criteria

1. WHEN a message send task is initiated THEN the Monitoring_Service SHALL check the Daily_Message_Counter before allowing the send
2. WHEN the Daily_Message_Counter reaches 180 THEN the Monitoring_Service SHALL reject all subsequent message send requests for the current day
3. WHEN a message send is blocked due to limit THEN the Monitoring_Service SHALL return an error response with code "daily_limit_reached" and a user-friendly message in French
4. WHEN a message send is blocked THEN the Monitoring_Service SHALL log the blocked attempt with timestamp and message details
5. WHEN a new day begins THEN the Monitoring_Service SHALL automatically unblock message sending

### Requirement 3

**User Story:** As an administrator, I want to see visual alerts on the dashboard when approaching the daily limit, so that I can take action before being blocked.

#### Acceptance Criteria

1. WHEN the Daily_Message_Counter is between 0 and 135 (0-75%) THEN the Monitoring_Dashboard SHALL display a green "OK" status indicator
2. WHEN the Daily_Message_Counter is between 136 and 162 (76-90%) THEN the Monitoring_Dashboard SHALL display a yellow "ATTENTION" status indicator
3. WHEN the Daily_Message_Counter is between 163 and 180 (91-100%) THEN the Monitoring_Dashboard SHALL display a red "DANGER" status indicator
4. WHEN the Daily_Message_Counter exceeds 180 THEN the Monitoring_Dashboard SHALL display a blocked status indicator with a message explaining that sending is paused until tomorrow
5. WHEN the alert level changes THEN the Monitoring_Dashboard SHALL display a toast notification informing the administrator

### Requirement 4

**User Story:** As an administrator, I want to see a dedicated monitoring page with detailed statistics, so that I can analyze message sending patterns and plan campaigns effectively.

#### Acceptance Criteria

1. WHEN the administrator navigates to `/dashboard/monitoring` THEN the Monitoring_Dashboard SHALL display a gauge showing messages sent vs daily limit (180)
2. WHEN the monitoring page loads THEN the Monitoring_Dashboard SHALL display separate counters for message_1 and message_2 sent today
3. WHEN the monitoring page loads THEN the Monitoring_Dashboard SHALL display the current interaction rate (message_2 / message_1 ratio)
4. WHEN the monitoring page loads THEN the Monitoring_Dashboard SHALL display a line chart showing the last 7 days of message statistics
5. WHEN the monitoring page is open THEN the Monitoring_Dashboard SHALL auto-refresh statistics every 10 seconds without full page reload

### Requirement 5

**User Story:** As an administrator, I want to see the remaining capacity for today, so that I can decide how many new contacts to add to a campaign.

#### Acceptance Criteria

1. WHEN the monitoring page loads THEN the Monitoring_Dashboard SHALL calculate and display the remaining message capacity using the formula: (180 - messages_sent) / (1 + interaction_rate)
2. WHEN the interaction rate changes THEN the Monitoring_Dashboard SHALL recalculate the remaining capacity in real-time
3. WHEN the remaining capacity is less than 10 THEN the Monitoring_Dashboard SHALL display a warning message suggesting to wait until tomorrow
4. WHEN the remaining capacity is zero THEN the Monitoring_Dashboard SHALL display a message indicating no more contacts can be added today

### Requirement 6

**User Story:** As an administrator, I want to see error statistics and failed messages, so that I can identify and resolve issues quickly.

#### Acceptance Criteria

1. WHEN a message fails to send THEN the Monitoring_Service SHALL increment an error counter in Redis for the current day
2. WHEN the error rate exceeds 10% of sent messages THEN the Monitoring_Dashboard SHALL display a warning alert
3. WHEN the monitoring page loads THEN the Monitoring_Dashboard SHALL display a list of recent errors (last 10) with timestamps and error messages
4. WHEN an error occurs THEN the Monitoring_Service SHALL log the error details to the `message_errors` table in Supabase

### Requirement 7

**User Story:** As an administrator, I want historical statistics persisted in Supabase, so that I can analyze trends over time and the data survives Redis restarts.

#### Acceptance Criteria

1. WHEN the Monitoring_Service starts THEN it SHALL synchronize Redis counters with the latest values from Supabase for the current day
2. WHEN one hour has passed since the last sync THEN the Monitoring_Service SHALL persist current Redis counters to Supabase
3. WHEN the application shuts down gracefully THEN the Monitoring_Service SHALL persist current Redis counters to Supabase immediately
4. WHEN querying historical data THEN the Monitoring_Dashboard SHALL retrieve data from the Daily_Stats_Table in Supabase

### Requirement 8

**User Story:** As an administrator, I want the monitoring system to integrate seamlessly with the existing dashboard, so that I can access it from the main navigation.

#### Acceptance Criteria

1. WHEN the administrator is logged in THEN the main navigation SHALL display a "Monitoring" link to `/dashboard/monitoring`
2. WHEN the Daily_Message_Counter exceeds 135 (75%) THEN the navigation link SHALL display a warning badge
3. WHEN the monitoring page loads THEN it SHALL use the existing DashboardLayout component and Tailwind CSS styling
4. WHEN the monitoring API is called THEN it SHALL require JWT authentication like other protected endpoints
