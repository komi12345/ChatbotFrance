# Implementation Plan

- [x] 1. Update SupabaseDB client to remove user filtering






  - [x] 1.1 Modify get_contacts_paginated to return all contacts

    - Remove `created_by` filter from query
    - Remove `is_super_admin` parameter (no longer needed)
    - _Requirements: 1.1, 2.1_

  - [x] 1.2 Modify get_contacts to return all contacts

    - Remove `created_by` filter from query
    - _Requirements: 1.1, 2.1_

  - [x] 1.3 Modify get_contact_by_id to not filter by user

    - Remove `created_by` filter, only filter by contact_id
    - _Requirements: 1.1, 2.1_

  - [x] 1.4 Modify get_campaigns to return all campaigns

    - Remove `created_by` filter from query
    - _Requirements: 5.1_

  - [x] 1.5 Modify get_campaign_by_id to not filter by user

    - Remove `created_by` filter, only filter by campaign_id
    - _Requirements: 5.3_

  - [x] 1.6 Modify get_dashboard_stats to aggregate all data

    - Remove `created_by` filter from all count queries
    - _Requirements: 1.2, 2.2_

  - [x] 1.7 Modify get_whatsapp_verification_stats to aggregate all data

    - Remove `created_by` filter from verification stats queries
    - _Requirements: 1.2, 2.2_
  - [x] 1.8 Write property test for shared data visibility


    - **Property 1: All users see all contacts**
    - **Validates: Requirements 1.1, 2.1**

- [x] 2. Update contacts router for global uniqueness





  - [x] 2.1 Update create_contact to check global uniqueness


    - Replace `get_contact_by_full_number(full_number, user_id)` with `get_contact_by_full_number_global(full_number)`
    - _Requirements: 3.1, 3.3_

  - [x] 2.2 Update update_contact to check global uniqueness

    - Ensure phone number update checks against all contacts globally
    - _Requirements: 3.2, 3.3_

  - [x] 2.3 Update list_contacts to not pass user filtering

    - Remove user_id filtering in the call to get_contacts_paginated
    - _Requirements: 1.1, 2.1_
  - [x] 2.4 Update get_contact to not filter by user


    - Allow any user to access any contact by ID
    - _Requirements: 1.1, 2.1_

  - [x] 2.5 Write property test for global phone uniqueness

    - **Property 3: Global phone number uniqueness**
    - **Validates: Requirements 3.1, 3.2, 3.3**

- [x] 3. Update messages router for shared visibility





  - [x] 3.1 Update list_messages to show all messages


    - Remove campaign ownership filtering
    - Query all messages directly
    - _Requirements: 5.2_

  - [x] 3.2 Update get_global_stats to aggregate all messages

    - Remove campaign ownership filtering from stats calculation
    - _Requirements: 5.2_

  - [x] 3.3 Update get_message to allow access to any message

    - Remove campaign ownership check
    - _Requirements: 5.2_
  - [x] 3.4 Write property test for message stats aggregation


    - **Property 5: Message statistics aggregate all data**
    - **Validates: Requirements 5.2**

- [x] 4. Update campaigns router for shared visibility






  - [x] 4.1 Update list_campaigns to show all campaigns

    - Remove user_id filtering in get_campaigns call
    - _Requirements: 5.1_

  - [x] 4.2 Update get_campaign to allow access to any campaign

    - Remove user_id filtering in get_campaign_by_id call

    - _Requirements: 5.3_
  - [x] 4.3 Update update_campaign to allow any user to modify

    - Remove ownership check for updates
    - _Requirements: 5.1_

  - [x] 4.4 Update delete_campaign to allow any user to delete

    - Remove ownership check for deletion
    - _Requirements: 5.1_
  - [x] 4.5 Write property test for campaign visibility


    - **Property 4: All users see all campaigns**
    - **Validates: Requirements 5.1, 5.3**

- [x] 5. Update categories router for shared visibility






  - [x] 5.1 Update list_categories to show all categories

    - Ensure no user filtering (already global, verify)
    - _Requirements: 1.3, 2.3_

  - [x] 5.2 Update category operations to allow any user

    - Verify create/update/delete work for any authenticated user
    - _Requirements: 1.3, 2.3_

- [x] 6. Checkpoint - Ensure all tests pass





  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Update verification router for shared data






  - [x] 7.1 Update verify stats to aggregate all contacts

    - Remove user_id filtering from verification stats
    - _Requirements: 1.2, 2.2_

  - [x] 7.2 Update bulk verify to work with any contacts

    - Allow verification of any contact regardless of creator
    - _Requirements: 1.1, 2.1_

- [x] 8. Preserve audit trail

  - [x] 8.1 Verify created_by is set on contact creation
    - Ensure the creator's user_id is stored
    - _Requirements: 6.1_

  - [x] 8.2 Verify created_by is set on category creation
    - Ensure the creator's user_id is stored
    - _Requirements: 6.3_

  - [x] 8.3 Verify created_by is set on campaign creation
    - Ensure the creator's user_id is stored
    - _Requirements: 6.1_

  - [x] 8.4 Write property test for audit trail preservation

    - **Property 6: Creator audit trail preserved**
    - **Validates: Requirements 6.1, 6.3**

- [x] 9. Verify user management authorization

  - [x] 9.1 Verify super admin can manage users
    - Test create/update/delete user endpoints with super admin
    - _Requirements: 4.1_

  - [x] 9.2 Verify admin cannot manage users
    - Test that admin gets 403 on user management endpoints
    - _Requirements: 4.2_

  - [x] 9.3 Write property test for user management authorization

    - **Property 7: User management restricted to super admin**
    - **Validates: Requirements 4.1, 4.2**



- [x] 10. Final Checkpoint - Ensure all tests pass







  - Ensure all tests pass, ask the user if questions arise.
