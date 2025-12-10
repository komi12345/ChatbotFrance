# Requirements Document

## Introduction

Cette fonctionnalité permet de vérifier automatiquement si un numéro de téléphone est enregistré sur WhatsApp lors de l'ajout d'un contact dans le dashboard admin. Le système affiche un badge visuel (vert pour WhatsApp actif, rouge pour non-WhatsApp) à côté de chaque numéro dans la liste des contacts et lors de la sélection de contacts pour les catégories. Cela permet d'éviter le gaspillage de ressources en ciblant uniquement les numéros WhatsApp valides pour les campagnes.

## Glossary

- **Contact**: Un enregistrement dans la base de données contenant un numéro de téléphone et des informations associées
- **WhatsApp Verification**: Processus de vérification via l'API Wassenger pour déterminer si un numéro est enregistré sur WhatsApp
- **Wassenger API**: Service tiers utilisé pour l'intégration WhatsApp Business
- **Badge WhatsApp**: Indicateur visuel (vert/rouge) affichant le statut de vérification WhatsApp d'un contact
- **Dashboard Admin**: Interface d'administration pour gérer les contacts et campagnes

## Requirements

### Requirement 1

**User Story:** As an admin, I want phone numbers to be automatically verified for WhatsApp when I add a new contact, so that I know immediately if the number can receive WhatsApp messages.

#### Acceptance Criteria

1. WHEN an admin creates a new contact THEN the System SHALL automatically trigger a WhatsApp verification request to the Wassenger API
2. WHEN the Wassenger API returns a verification result THEN the System SHALL store the verification status (verified_whatsapp: true/false/null) in the contact record
3. WHEN the verification request fails due to network or API errors THEN the System SHALL set the verification status to null and log the error
4. WHEN a contact is created THEN the System SHALL complete the creation process regardless of verification result to avoid blocking the user

### Requirement 2

**User Story:** As an admin, I want to see a visual badge next to each phone number indicating WhatsApp status, so that I can quickly identify which contacts can receive WhatsApp messages.

#### Acceptance Criteria

1. WHEN displaying a contact with verified_whatsapp=true THEN the System SHALL show a green badge with a WhatsApp icon
2. WHEN displaying a contact with verified_whatsapp=false THEN the System SHALL show a red badge with a warning icon
3. WHEN displaying a contact with verified_whatsapp=null THEN the System SHALL show a gray badge indicating "non vérifié"
4. WHEN hovering over a WhatsApp badge THEN the System SHALL display a tooltip explaining the status

### Requirement 3

**User Story:** As an admin, I want to manually re-verify a contact's WhatsApp status, so that I can update outdated verification information.

#### Acceptance Criteria

1. WHEN an admin clicks the re-verify button on a contact THEN the System SHALL send a new verification request to the Wassenger API
2. WHEN the re-verification completes THEN the System SHALL update the contact's verification status and timestamp
3. WHILE a verification is in progress THEN the System SHALL display a loading indicator on the badge

### Requirement 4

**User Story:** As an admin, I want to filter contacts by WhatsApp status when selecting contacts for categories, so that I can ensure my campaigns only target valid WhatsApp numbers.

#### Acceptance Criteria

1. WHEN viewing the contacts list THEN the System SHALL provide a filter option for WhatsApp status (All, WhatsApp Only, Non-WhatsApp, Not Verified)
2. WHEN the "WhatsApp Only" filter is active THEN the System SHALL display only contacts with verified_whatsapp=true
3. WHEN adding contacts to a category THEN the System SHALL display the WhatsApp badge next to each contact for informed selection

### Requirement 5

**User Story:** As an admin, I want to see a summary of WhatsApp verification status in my contact statistics, so that I can understand the quality of my contact database.

#### Acceptance Criteria

1. WHEN viewing the contacts page THEN the System SHALL display a summary showing count of verified WhatsApp contacts, non-WhatsApp contacts, and unverified contacts
2. WHEN viewing a category detail THEN the System SHALL display the percentage of WhatsApp-verified contacts in that category

### Requirement 6

**User Story:** As an admin, I want the system to handle Wassenger API rate limits gracefully, so that bulk contact imports don't fail.

#### Acceptance Criteria

1. WHEN importing multiple contacts THEN the System SHALL queue verification requests with appropriate delays to respect API rate limits
2. WHEN a rate limit error occurs THEN the System SHALL retry the verification after the specified delay
3. WHEN bulk verification is in progress THEN the System SHALL allow the admin to continue using the application without blocking

