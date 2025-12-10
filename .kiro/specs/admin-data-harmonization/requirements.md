# Requirements Document

## Introduction

Ce document spécifie les exigences pour l'harmonisation des données entre les rôles Super Admin et Admin dans le système de chatbot WhatsApp. Actuellement, chaque utilisateur (admin ou super admin) ne voit que ses propres données (contacts, catégories, campagnes, messages). L'objectif est que tous les utilisateurs partagent les mêmes données avec des permissions différentes uniquement pour la gestion des utilisateurs.

## Glossary

- **Super Admin**: Utilisateur avec accès complet incluant la gestion des autres utilisateurs (création, modification, suppression d'admins)
- **Admin**: Utilisateur standard avec accès au dashboard et aux fonctionnalités de gestion des contacts, catégories et campagnes
- **Contact**: Numéro WhatsApp enregistré dans le système avec informations associées
- **Dashboard**: Interface principale affichant les statistiques et données du système
- **full_number**: Numéro de téléphone complet au format international (ex: +33612345678)

## Requirements

### Requirement 1

**User Story:** As a super admin, I want to see all contacts created by any user, so that I can have a complete view of the system data.

#### Acceptance Criteria

1. WHEN a super admin accesses the contacts list THEN the System SHALL display all contacts regardless of who created them
2. WHEN a super admin views dashboard statistics THEN the System SHALL display aggregated statistics from all users' data
3. WHEN a super admin accesses categories THEN the System SHALL display all categories regardless of creator

### Requirement 2

**User Story:** As an admin, I want to see all contacts in the system, so that I can work with the complete dataset like the super admin.

#### Acceptance Criteria

1. WHEN an admin accesses the contacts list THEN the System SHALL display all contacts regardless of who created them
2. WHEN an admin views dashboard statistics THEN the System SHALL display the same aggregated statistics as the super admin
3. WHEN an admin accesses categories THEN the System SHALL display all categories regardless of creator

### Requirement 3

**User Story:** As a user, I want phone numbers to be unique across the entire system, so that duplicate contacts cannot be created by different users.

#### Acceptance Criteria

1. WHEN a user attempts to create a contact with a phone number that already exists THEN the System SHALL reject the creation with an error message indicating the number already exists
2. WHEN a user attempts to update a contact's phone number to one that already exists THEN the System SHALL reject the update with an error message
3. WHEN validating phone number uniqueness THEN the System SHALL check against all contacts in the system regardless of creator

### Requirement 4

**User Story:** As a super admin, I want to manage other users while sharing the same data view, so that user management is the only differentiating permission.

#### Acceptance Criteria

1. WHEN a super admin accesses user management THEN the System SHALL allow creating, modifying, and deleting admin and super admin users
2. WHEN an admin attempts to access user management THEN the System SHALL deny access with a forbidden error
3. WHILE a user has super admin role THEN the System SHALL display the user management menu option

### Requirement 5

**User Story:** As a user, I want campaigns and messages to be visible to all users, so that the entire team can monitor campaign performance.

#### Acceptance Criteria

1. WHEN a user accesses the campaigns list THEN the System SHALL display all campaigns regardless of creator
2. WHEN a user views message statistics THEN the System SHALL include messages from all campaigns
3. WHEN a user accesses a specific campaign THEN the System SHALL display it if it exists regardless of who created it

### Requirement 6

**User Story:** As a user, I want the created_by field to be preserved for audit purposes, so that we can track who created each record.

#### Acceptance Criteria

1. WHEN a contact is created THEN the System SHALL store the creator's user ID in the created_by field
2. WHEN displaying contact details THEN the System SHALL show the creator information for audit purposes
3. WHEN a category is created THEN the System SHALL store the creator's user ID in the created_by field
