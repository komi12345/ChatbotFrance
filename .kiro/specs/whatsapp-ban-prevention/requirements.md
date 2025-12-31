# Requirements Document

## Introduction

Optimisation du système d'envoi de messages WhatsApp pour **éviter les bannissements** de compte. Le système actuel envoie les messages trop rapidement (5 secondes entre messages), ce qui a causé un ban du compte Wassenger. Cette spec implémente une stratégie anti-ban avec des délais beaucoup plus longs, de la randomisation, des pauses stratégiques et un système de warm-up progressif.

## Glossaire

- **Anti_Ban_Rate_Limiter**: Système de contrôle du débit d'envoi avec délais longs et randomisés pour éviter les bans WhatsApp
- **Warm_Up_System**: Système de montée en charge progressive qui commence lentement et accélère graduellement
- **Strategic_Pause_Manager**: Gestionnaire de pauses automatiques après un certain nombre de messages
- **Human_Behavior_Simulator**: Système qui simule un comportement humain avec des délais aléatoires et des micro-pauses
- **Ban_Risk_Detector**: Système de détection précoce des signes de bannissement via les codes d'erreur API
- **Daily_Limit_Enforcer**: Système de limitation stricte à 180 messages par jour maximum
- **Message_Sender**: Système d'envoi de messages via Celery et Wassenger API (existant)

## Requirements

### Requirement 1: Délais d'envoi anti-ban avec randomisation renforcée

**User Story:** As an administrator, I want messages to be sent with very long, randomized delays, so that WhatsApp cannot detect automated sending patterns.

#### Acceptance Criteria

1. THE Anti_Ban_Rate_Limiter SHALL enforce a minimum delay of 15 seconds between messages
2. THE Anti_Ban_Rate_Limiter SHALL add random variation of ±5 seconds to each delay
3. WHEN calculating delay, THE Anti_Ban_Rate_Limiter SHALL use the formula: `base_delay + random(-5, +5)` where base_delay is between 15 and 30 seconds
4. THE Anti_Ban_Rate_Limiter SHALL log each calculated delay for monitoring
5. THE Anti_Ban_Rate_Limiter SHALL never allow delays shorter than 10 seconds
6. THE Anti_Ban_Rate_Limiter SHALL add an additional random "human typing" delay of 1-3 seconds before each message

### Requirement 2: Système de warm-up progressif renforcé

**User Story:** As an administrator, I want the system to start very slowly and gradually increase speed, so that WhatsApp sees natural account behavior.

#### Acceptance Criteria

1. WHEN fewer than 30 messages have been sent today, THE Warm_Up_System SHALL use delays of 25-35 seconds (very slow start)
2. WHEN 30-80 messages have been sent today, THE Warm_Up_System SHALL use delays of 20-28 seconds
3. WHEN 80-200 messages have been sent today, THE Warm_Up_System SHALL use delays of 15-22 seconds (cruising speed)
4. WHEN 200-500 messages have been sent today, THE Warm_Up_System SHALL use delays of 18-25 seconds (slowing down)
5. WHEN more than 500 messages have been sent today, THE Warm_Up_System SHALL use delays of 22-30 seconds (approaching limit)
6. THE Warm_Up_System SHALL track daily message count in Redis with automatic reset at midnight

### Requirement 3: Pauses stratégiques automatiques renforcées

**User Story:** As an administrator, I want the system to take automatic breaks, so that sending patterns appear more human-like.

#### Acceptance Criteria

1. WHEN 20 messages have been sent consecutively, THE Strategic_Pause_Manager SHALL pause for 3-5 minutes (random)
2. WHEN 40 messages have been sent consecutively, THE Strategic_Pause_Manager SHALL pause for 5-8 minutes (random)
3. WHEN 60 messages have been sent consecutively, THE Strategic_Pause_Manager SHALL pause for 10-15 minutes (random)
4. WHEN 100 messages have been sent consecutively, THE Strategic_Pause_Manager SHALL pause for 20-30 minutes (random)
5. THE Strategic_Pause_Manager SHALL log all pauses with duration and reason
6. THE Strategic_Pause_Manager SHALL reset the consecutive counter after each pause

### Requirement 4: Simulation de comportement humain

**User Story:** As an administrator, I want the system to behave like a human operator, so that WhatsApp cannot detect automation.

#### Acceptance Criteria

1. THE Human_Behavior_Simulator SHALL add random micro-pauses (30-120 seconds) with 10% probability
2. WHEN the current hour is between 23:00 and 06:00, THE Human_Behavior_Simulator SHALL postpone sending to 07:00
3. THE Human_Behavior_Simulator SHALL vary message timing based on message length (longer messages = slightly longer delay)
4. THE Human_Behavior_Simulator SHALL never send more than 4 messages per minute on average

### Requirement 5: Détection précoce des risques de ban

**User Story:** As an administrator, I want to be alerted when WhatsApp shows signs of blocking, so that I can stop sending before getting banned.

#### Acceptance Criteria

1. WHEN Wassenger API returns error codes 'rate_limit', 'spam_detected', 'blocked', or HTTP 429, THE Ban_Risk_Detector SHALL trigger an emergency pause of 30 minutes
2. WHEN 3 consecutive errors occur, THE Ban_Risk_Detector SHALL halt all sending and alert the administrator
3. WHEN 5 errors occur within 10 minutes, THE Ban_Risk_Detector SHALL halt all sending for 1 hour
4. THE Ban_Risk_Detector SHALL log all suspicious error codes with timestamps
5. THE Ban_Risk_Detector SHALL track error rate and trigger warning at 5% error rate

### Requirement 6: Limite quotidienne existante (1000 messages)

**User Story:** As an administrator, I want to keep the existing daily limit of 1000 messages, so that I can send campaigns while staying within WhatsApp's tolerance.

#### Acceptance Criteria

1. THE Daily_Limit_Enforcer SHALL keep the existing limit of 1000 messages per day
2. THE Daily_Limit_Enforcer SHALL display a warning when 800 messages have been sent (approaching limit)
3. THE Daily_Limit_Enforcer SHALL reset the counter at midnight UTC
4. THE Daily_Limit_Enforcer SHALL persist the counter in Redis with 24-hour TTL
5. IF the daily limit is reached, THEN THE Daily_Limit_Enforcer SHALL return a clear error message to the user

### Requirement 7: Configuration Celery anti-ban

**User Story:** As a system administrator, I want Celery configured for single-threaded, slow processing, so that messages are never sent in parallel.

#### Acceptance Criteria

1. THE Celery_Worker SHALL run with concurrency of 1 (single worker)
2. THE Celery_Worker SHALL have prefetch_multiplier set to 1 (no prefetching)
3. THE Celery_Worker SHALL have a rate limit of 4 messages per minute maximum
4. THE Celery_Worker SHALL process tasks sequentially, never in parallel
5. THE Celery_Worker SHALL have soft_time_limit of 300 seconds per task

### Requirement 8: Préservation de la logique existante

**User Story:** As a system architect, I want the existing Message 1/Message 2 logic to remain unchanged, so that the campaign workflow continues to work correctly.

#### Acceptance Criteria

1. WHEN Message 1 is sent, THE Message_Sender SHALL NOT modify the existing message creation logic
2. WHEN a contact replies within 24h, THE Message_Sender SHALL send Message 2 with anti-ban delays applied
3. IF a contact does not reply within 24h, THEN THE Campaign_Manager SHALL mark the contact as "no_interaction"
4. THE Campaign_Manager SHALL preserve the existing campaign completion logic
5. THE Idempotency_Guard SHALL continue to prevent duplicate message sends

