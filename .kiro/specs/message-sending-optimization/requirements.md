# Requirements Document

## Introduction

Optimisation de l'envoi de messages WhatsApp pour supporter 500-1000 messages de manière fiable et rapide, tout en préservant la logique existante de Message 1 et Message 2, et en évitant les bans WhatsApp.

## Glossaire

- **Message_Sender**: Système d'envoi de messages via Celery et Wassenger API
- **Rate_Limiter**: Mécanisme de contrôle du débit d'envoi pour éviter les bans WhatsApp
- **Batch_Processor**: Système de traitement par lots des messages
- **Campaign_Manager**: Gestionnaire de campagnes et de leur statut
- **Idempotency_Guard**: Mécanisme de protection contre les doublons d'envoi

## Requirements

### Requirement 1: Optimisation du Rate Limiting

**User Story:** As an administrator, I want to send messages faster while avoiding WhatsApp bans, so that campaigns complete in a reasonable time.

#### Acceptance Criteria

1. THE Rate_Limiter SHALL support configurable delay between messages (2-10 seconds)
2. WHEN a mature account is detected, THE Rate_Limiter SHALL use a reduced delay of 3 seconds
3. WHEN sending to 500+ contacts, THE Rate_Limiter SHALL use adaptive delays based on error rates
4. IF the error rate exceeds 5%, THEN THE Rate_Limiter SHALL increase the delay by 50%
5. THE Rate_Limiter SHALL log all delay adjustments for monitoring

### Requirement 2: Optimisation du Batch Processing

**User Story:** As an administrator, I want batch processing to be more efficient, so that large campaigns complete faster.

#### Acceptance Criteria

1. THE Batch_Processor SHALL support configurable batch sizes (25-100 messages)
2. WHEN processing batches, THE Batch_Processor SHALL reduce inter-batch pause from 60s to 30s
3. THE Batch_Processor SHALL calculate accurate completion time estimates
4. WHEN a batch completes, THE Batch_Processor SHALL update campaign progress in real-time
5. THE Batch_Processor SHALL support resuming interrupted campaigns from the last successful message

### Requirement 3: Préservation de la Logique Message 1/Message 2

**User Story:** As a system architect, I want the Message 1 and Message 2 logic to remain unchanged, so that the campaign workflow continues to work correctly.

#### Acceptance Criteria

1. WHEN Message 1 is sent, THE Message_Sender SHALL NOT modify the existing message creation logic
2. WHEN a contact replies within 24h, THE Message_Sender SHALL send Message 2 immediately (existing behavior)
3. IF a contact does not reply within 24h, THEN THE Campaign_Manager SHALL mark the contact as "no_interaction"
4. THE Campaign_Manager SHALL preserve the existing campaign completion logic
5. THE Idempotency_Guard SHALL continue to prevent duplicate message sends

### Requirement 4: Robustesse pour Envois Massifs

**User Story:** As an administrator, I want large campaigns to be reliable, so that all messages are delivered without errors.

#### Acceptance Criteria

1. WHEN sending 500+ messages, THE Message_Sender SHALL use enhanced error handling
2. IF a message fails, THEN THE Message_Sender SHALL retry with exponential backoff (existing behavior)
3. THE Message_Sender SHALL track progress in Redis for crash recovery
4. WHEN the server restarts, THE Message_Sender SHALL resume pending messages automatically
5. THE Campaign_Manager SHALL provide real-time progress updates via API

### Requirement 5: Configuration Dynamique

**User Story:** As an administrator, I want to configure sending parameters, so that I can optimize for different scenarios.

#### Acceptance Criteria

1. THE Rate_Limiter SHALL read configuration from environment variables
2. THE Batch_Processor SHALL support runtime configuration changes
3. WHEN configuration changes, THE Message_Sender SHALL apply changes to new batches only
4. THE Campaign_Manager SHALL expose current configuration via API endpoint
5. THE Rate_Limiter SHALL support per-campaign configuration overrides

### Requirement 6: Monitoring et Alertes

**User Story:** As an administrator, I want to monitor campaign progress, so that I can identify and resolve issues quickly.

#### Acceptance Criteria

1. THE Campaign_Manager SHALL provide detailed progress statistics
2. WHEN error rate exceeds threshold, THE Campaign_Manager SHALL log warnings
3. THE Message_Sender SHALL track message delivery latency
4. THE Campaign_Manager SHALL calculate estimated completion time accurately
5. WHEN a campaign completes, THE Campaign_Manager SHALL generate a summary report
