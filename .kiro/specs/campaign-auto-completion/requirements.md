# Requirements Document

## Introduction

Ce document définit les exigences pour corriger deux problèmes critiques dans le système de campagnes WhatsApp :
1. La terminaison automatique des campagnes qui ne fonctionne pas correctement après l'envoi de tous les Message 2
2. L'amélioration de la robustesse des webhooks Wassenger

## Glossary

- **Campaign_System**: Le système de gestion des campagnes WhatsApp
- **Message_1**: Premier message envoyé aux contacts d'une campagne
- **Message_2**: Message de suivi envoyé uniquement aux contacts qui ont interagi avec le Message 1 dans les 24h
- **Webhook_Handler**: Le composant qui reçoit et traite les notifications de Wassenger
- **Campaign_Status_Checker**: Le composant qui vérifie et met à jour le statut des campagnes

## Requirements

### Requirement 1: Vérification automatique du statut après envoi de Message 2

**User Story:** En tant qu'administrateur, je veux que la campagne se termine automatiquement quand tous les contacts ont reçu leur Message 2, afin de ne pas avoir à rafraîchir manuellement la page.

#### Acceptance Criteria

1. WHEN a Message_2 is successfully sent, THE Campaign_Status_Checker SHALL verify if all contacts have completed their cycle
2. WHEN all contacts have either received Message_2 OR are marked as no_interaction OR have failed, THE Campaign_System SHALL update the campaign status to "completed"
3. WHEN the campaign status changes to "completed", THE Campaign_System SHALL set the completed_at timestamp immediately
4. IF a campaign has pending messages, THEN THE Campaign_System SHALL keep the status as "sending"

### Requirement 2: Vérification périodique des campagnes en cours

**User Story:** En tant qu'administrateur, je veux que le système vérifie régulièrement les campagnes en cours pour détecter celles qui sont terminées, afin d'avoir des statuts à jour.

#### Acceptance Criteria

1. THE Campaign_Status_Checker SHALL run a periodic check every 2 minutes for campaigns in "sending" status
2. WHEN a campaign in "sending" status has no pending messages AND all contacts have completed their cycle, THE Campaign_System SHALL update the status to "completed"
3. WHEN checking campaign completion, THE Campaign_Status_Checker SHALL count Message_1 sent, Message_2 sent, no_interaction, and failed messages

### Requirement 3: Amélioration de la robustesse des webhooks

**User Story:** En tant qu'administrateur, je veux que les webhooks Wassenger soient traités de manière fiable, afin de ne pas perdre d'interactions.

#### Acceptance Criteria

1. WHEN a webhook is received, THE Webhook_Handler SHALL respond with 200 OK within 5 seconds
2. WHEN processing a webhook fails, THE Webhook_Handler SHALL log the error with full payload details
3. WHEN a message:in:new webhook is received, THE Webhook_Handler SHALL trigger Message_2 sending if applicable
4. WHEN Message_2 is sent after an interaction, THE Campaign_Status_Checker SHALL be triggered to verify campaign completion

### Requirement 4: Mise à jour du statut en temps réel dans l'interface

**User Story:** En tant qu'administrateur, je veux voir le statut correct de la campagne sans avoir à rafraîchir la page, afin de suivre l'avancement en temps réel.

#### Acceptance Criteria

1. WHEN viewing campaign details, THE Campaign_System SHALL display the current status from the database
2. WHEN the campaign status changes in the database, THE Campaign_System SHALL reflect this change on the next API call
3. THE Campaign_System SHALL NOT cache campaign status for campaigns in "sending" status
