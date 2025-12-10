# Design Document: Admin Data Harmonization

## Overview

This design document describes the changes needed to harmonize data visibility between Super Admin and Admin roles in the WhatsApp chatbot system. The goal is to ensure all users see the same data (contacts, categories, campaigns, messages) while maintaining role-based access control only for user management.

Currently, the system isolates data by `created_by` field, meaning each user only sees their own data. This design removes that isolation for data visibility while preserving the audit trail.

## Architecture

### Current Architecture (Before)

```
┌─────────────────┐     ┌─────────────────┐
│   Super Admin   │     │     Admin       │
└────────┬────────┘     └────────┬────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│ Contacts where  │     │ Contacts where  │
│ created_by = 1  │     │ created_by = 2  │
└─────────────────┘     └─────────────────┘
         │                       │
         ▼                       ▼
    [Isolated Data]         [Isolated Data]
```

### Target Architecture (After)

```
┌─────────────────┐     ┌─────────────────┐
│   Super Admin   │     │     Admin       │
└────────┬────────┘     └────────┬────────┘
         │                       │
         └───────────┬───────────┘
                     ▼
         ┌─────────────────────┐
         │   Shared Data Pool  │
         │  (All Contacts,     │
         │   Categories,       │
         │   Campaigns,        │
         │   Messages)         │
         └─────────────────────┘
                     │
    ┌────────────────┼────────────────┐
    │                │                │
    ▼                ▼                ▼
┌────────┐    ┌────────────┐    ┌──────────┐
│Contacts│    │ Categories │    │Campaigns │
│created │    │  created   │    │ created  │
│by any  │    │  by any    │    │ by any   │
│ user   │    │   user     │    │  user    │
└────────┘    └────────────┘    └──────────┘
```

### Permission Model

| Feature | Super Admin | Admin |
|---------|-------------|-------|
| View all contacts | ✅ | ✅ |
| Create contacts | ✅ | ✅ |
| Edit/Delete contacts | ✅ | ✅ |
| View all categories | ✅ | ✅ |
| Manage categories | ✅ | ✅ |
| View all campaigns | ✅ | ✅ |
| Manage campaigns | ✅ | ✅ |
| View all messages | ✅ | ✅ |
| View dashboard stats | ✅ | ✅ |
| **Manage users** | ✅ | ❌ |

## Components and Interfaces

### Backend Components to Modify

#### 1. SupabaseDB Client (`backend/app/supabase_client.py`)

Remove `user_id` filtering from data queries:

```python
# BEFORE
def get_contacts_paginated(self, user_id: int, ...):
    query = query.eq("created_by", user_id)

# AFTER  
def get_contacts_paginated(self, user_id: int, ...):
    # No created_by filter - return all contacts
    query = self.client.table("contacts").select("*", count="exact")
```

Methods to modify:
- `get_contacts_paginated()` - Remove `created_by` filter
- `get_contacts()` - Remove `created_by` filter
- `get_contact_by_id()` - Remove `created_by` filter
- `get_contact_by_full_number()` - Change to global check (already exists as `get_contact_by_full_number_global`)
- `get_categories_paginated()` - Already global (no change needed)
- `get_campaigns()` - Remove `created_by` filter
- `get_campaign_by_id()` - Remove `created_by` filter
- `get_dashboard_stats()` - Remove `created_by` filter
- `get_whatsapp_verification_stats()` - Remove `created_by` filter

#### 2. Contacts Router (`backend/app/routers/contacts.py`)

Update contact creation to check global uniqueness:

```python
# BEFORE
existing = db.get_contact_by_full_number(full_number, current_user["id"])

# AFTER
existing = db.get_contact_by_full_number_global(full_number)
```

#### 3. Messages Router (`backend/app/routers/messages.py`)

Remove campaign ownership filtering:

```python
# BEFORE
campaigns, _ = db.get_campaigns(user_id=current_user["id"], ...)
user_campaign_ids = [c["id"] for c in campaigns]
query = query.in_("campaign_id", user_campaign_ids)

# AFTER
# Query all messages directly without campaign ownership filter
query = client.table("messages").select("*", count="exact")
```

#### 4. Campaigns Router (`backend/app/routers/campaigns.py`)

Remove `created_by` filtering from queries.

### Database Changes

No schema changes required. The `created_by` field is preserved for audit purposes but no longer used for access control filtering.

### RLS Policies Update (`database/rls_policies.sql`)

Update Row Level Security policies to allow all authenticated users to access all data:

```sql
-- BEFORE: contacts_select_policy
CREATE POLICY contacts_select_policy ON contacts
    FOR SELECT
    USING (
        created_by = (auth.jwt() ->> 'user_id')::integer
        OR (auth.jwt() ->> 'role') = 'super_admin'
    );

-- AFTER: contacts_select_policy
CREATE POLICY contacts_select_policy ON contacts
    FOR SELECT
    USING (true);  -- All authenticated users can see all contacts
```

## Data Models

No changes to data models. The existing models remain:

### Contact Model
```python
class Contact:
    id: int
    phone_number: str
    country_code: str
    full_number: str  # UNIQUE constraint (global)
    first_name: Optional[str]
    last_name: Optional[str]
    created_by: int  # Preserved for audit
    whatsapp_verified: Optional[bool]
    verified_at: Optional[datetime]
```

### Category Model
```python
class Category:
    id: int
    name: str
    color: Optional[str]
    created_by: int  # Preserved for audit
```

### Campaign Model
```python
class Campaign:
    id: int
    name: str
    message_1: str
    message_2: Optional[str]
    status: str
    created_by: int  # Preserved for audit
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: All users see all contacts
*For any* set of contacts created by different users, when any authenticated user (admin or super admin) queries the contacts list, the result SHALL include all contacts in the system regardless of their `created_by` value.
**Validates: Requirements 1.1, 2.1**

### Property 2: Dashboard statistics are identical for all users
*For any* authenticated user (admin or super admin), the dashboard statistics (total contacts, total categories, total campaigns, total messages) SHALL return the same values as any other authenticated user.
**Validates: Requirements 1.2, 2.2**

### Property 3: Global phone number uniqueness
*For any* phone number that exists in the contacts table, attempting to create a new contact with that same phone number SHALL fail with an error, regardless of which user attempts the creation.
**Validates: Requirements 3.1, 3.2, 3.3**

### Property 4: All users see all campaigns
*For any* campaign in the system, when any authenticated user queries the campaigns list or accesses a specific campaign by ID, the campaign SHALL be visible regardless of its `created_by` value.
**Validates: Requirements 5.1, 5.3**

### Property 5: Message statistics aggregate all data
*For any* authenticated user, the message statistics SHALL include counts from all messages in the system, not filtered by campaign ownership.
**Validates: Requirements 5.2**

### Property 6: Creator audit trail preserved
*For any* entity (contact, category, campaign) created by a user, the `created_by` field SHALL contain the ID of the user who created it, and this value SHALL not change after creation.
**Validates: Requirements 6.1, 6.3**

### Property 7: User management restricted to super admin
*For any* request to user management endpoints (create/update/delete users), the request SHALL succeed only if the authenticated user has the `super_admin` role; otherwise it SHALL return a 403 Forbidden error.
**Validates: Requirements 4.1, 4.2**

## Error Handling

### Contact Creation with Duplicate Number
- **Error**: `400 Bad Request`
- **Message**: `"Un contact avec le numéro '{full_number}' existe déjà"`
- **Behavior**: The system checks globally for existing numbers before creation

### Unauthorized User Management Access
- **Error**: `403 Forbidden`
- **Message**: `"Accès réservé aux Super Admins"`
- **Behavior**: Admin users attempting to access user management endpoints receive this error

## Testing Strategy

### Property-Based Testing Framework
- **Library**: Hypothesis (Python)
- **Minimum iterations**: 100 per property test

### Unit Tests
- Test contact creation with duplicate numbers (global check)
- Test dashboard stats aggregation
- Test user management authorization

### Property-Based Tests

Each correctness property will be implemented as a property-based test:

1. **Property 1 Test**: Generate random contacts with random `created_by` values, verify any user query returns all
2. **Property 2 Test**: Generate random data, verify stats are identical for different user roles
3. **Property 3 Test**: Generate random contacts, attempt duplicate creation, verify rejection
4. **Property 4 Test**: Generate random campaigns, verify visibility for all users
5. **Property 5 Test**: Generate random messages across campaigns, verify stats include all
6. **Property 6 Test**: Create entities, verify `created_by` matches creator and doesn't change
7. **Property 7 Test**: Generate requests to user endpoints with different roles, verify authorization

### Test Annotations
Each property-based test MUST include a comment in this format:
```python
# **Feature: admin-data-harmonization, Property {number}: {property_text}**
```
