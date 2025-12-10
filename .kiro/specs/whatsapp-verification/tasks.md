# Implementation Plan

- [x] 1. Database schema migration






  - [x] 1.1 Create SQL migration to add whatsapp_verified and verified_at columns to contacts table

    - Add `whatsapp_verified BOOLEAN DEFAULT NULL` column
    - Add `verified_at TIMESTAMP DEFAULT NULL` column
    - Create index `idx_contacts_whatsapp_verified` for filtering performance
    - _Requirements: 1.2, 4.2_

- [x] 2. Backend - Wassenger service extension






  - [x] 2.1 Add WhatsAppExistsResponse dataclass to wassenger_service.py

    - Define fields: exists (bool), phone (str), error_code (Optional[str]), error_message (Optional[str])
    - _Requirements: 1.2_

  - [x] 2.2 Implement check_whatsapp_exists method in WassengerService

    - Call Wassenger API endpoint GET /v1/contacts/exists
    - Handle success response (exists: true/false)
    - Handle error responses (network, rate limit, invalid phone)
    - _Requirements: 1.1, 1.3_
  - [x] 2.3 Write property test for check_whatsapp_exists error handling







    - **Property 3: Error handling sets null status**
    - **Validates: Requirements 1.3**

- [x] 3. Backend - Update contact schemas and models






  - [x] 3.1 Update Contact model in models/contact.py

    - Add whatsapp_verified column (Boolean, nullable)
    - Add verified_at column (DateTime, nullable)
    - _Requirements: 1.2_

  - [x] 3.2 Update ContactResponse schema in schemas/contact.py

    - Add whatsapp_verified: Optional[bool] field
    - Add verified_at: Optional[datetime] field
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 3.3 Update SupabaseDB client to handle new fields

    - Update get_contacts_paginated to include new fields
    - Add filter parameter for whatsapp_status
    - _Requirements: 4.2_

- [x] 4. Backend - Verification router and endpoints





  - [x] 4.1 Create new router file routers/verify.py


    - POST /api/verify/{contact_id} - Verify single contact
    - POST /api/verify/bulk - Queue bulk verification
    - _Requirements: 3.1, 6.1_

  - [x] 4.2 Implement single contact verification endpoint

    - Call WassengerService.check_whatsapp_exists
    - Update contact record with result
    - Return verification result
    - _Requirements: 3.1, 3.2_
  - [x] 4.3 Write property test for verification status persistence









    - **Property 2: Verification status persistence**
    - **Validates: Requirements 1.2, 3.2**

- [x] 5. Backend - Celery task for async verification






  - [x] 5.1 Create verify_whatsapp_task in tasks/message_tasks.py

    - Async task to verify a single contact
    - Handle rate limiting with exponential backoff
    - Update contact record on completion
    - _Requirements: 1.1, 6.2_

  - [x] 5.2 Create bulk_verify_task for batch processing

    - Queue individual verifications with delays
    - Respect Wassenger API rate limits (2 seconds between calls)
    - _Requirements: 6.1, 6.2_
  - [x] 5.3 Write property test for rate limit retry behavior






    - **Property 8: Rate limit retry behavior**
    - **Validates: Requirements 6.1, 6.2**

- [x] 6. Backend - Update contacts router for auto-verification






  - [x] 6.1 Modify create_contact endpoint to trigger verification

    - Queue verification task after contact creation
    - Do not block contact creation on verification result
    - _Requirements: 1.1, 1.4_

  - [x] 6.2 Add whatsapp_status filter parameter to list_contacts

    - Filter options: all, verified, not_whatsapp, pending
    - _Requirements: 4.1, 4.2_
  - [x] 6.3 Write property test for contact creation independence







    - **Property 1: Contact creation independence from verification**
    - **Validates: Requirements 1.4**

- [x] 7. Checkpoint - Backend tests





  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Frontend - WhatsApp verification badge component






  - [x] 8.1 Create WhatsAppVerificationBadge component

    - Props: status, onReVerify, isLoading, size
    - Green badge for verified, red for not_whatsapp, gray for pending/null
    - Tooltip with status explanation
    - _Requirements: 2.1, 2.2, 2.3, 2.4_
  - [x] 8.2 Write property test for badge rendering






    - **Property 4: Badge rendering matches verification status**
    - **Validates: Requirements 2.1, 2.2, 2.3**

- [x] 9. Frontend - Update contact types






  - [x] 9.1 Update Contact interface in types/contact.ts

    - Add whatsapp_verified: boolean | null
    - Add verified_at: string | null
    - _Requirements: 2.1_

  - [x] 9.2 Add WhatsAppStatus type and ContactFilters update


    - Type: 'verified' | 'not_whatsapp' | 'pending' | null
    - Add whatsapp_status to ContactFilters
    - _Requirements: 4.1_

- [x] 10. Frontend - Verification hook






  - [x] 10.1 Create useVerifyContact hook in hooks/useContacts.ts

    - Mutation for POST /api/verify/{contact_id}
    - Invalidate contacts cache on success
    - _Requirements: 3.1_

  - [ ] 10.2 Create useBulkVerify hook for batch verification
    - Mutation for POST /api/verify/bulk
    - _Requirements: 6.1_

- [x] 11. Frontend - Update ContactTable component

  - [x] 11.1 Add WhatsApp badge column to ContactTable
    - Display WhatsAppVerificationBadge for each contact
    - Add re-verify button functionality
    - _Requirements: 2.1, 2.2, 2.3, 3.1_

  - [x] 11.2 Add WhatsApp status filter dropdown
    - Options: Tous, WhatsApp vérifié, Non-WhatsApp, Non vérifié
    - Update useContacts hook call with filter
    - _Requirements: 4.1, 4.2_

  - [x] 11.3 Write property test for filter correctness






    - **Property 5: WhatsApp filter returns correct subset**
    - **Validates: Requirements 4.2**

- [x] 12. Frontend - Update contacts page with statistics






  - [x] 12.1 Add verification statistics summary to contacts page

    - Display counts: verified, not_whatsapp, pending
    - Show as cards or inline stats
    - _Requirements: 5.1_
  - [ ]* 12.2 Write property test for statistics calculation
    - **Property 6: Statistics calculation accuracy**
    - **Validates: Requirements 5.1**

- [x] 13. Frontend - Update category detail page






  - [x] 13.1 Add WhatsApp verification percentage to category detail

    - Calculate and display percentage of verified contacts
    - Show warning if percentage is low
    - _Requirements: 5.2_
  - [x] 13.2 Write property test for category percentage calculation






    - **Property 7: Category verification percentage**
    - **Validates: Requirements 5.2**

- [x] 14. Frontend - Update ContactForm for badge display






  - [x] 14.1 Show WhatsApp badge in contact selection (category assignment)

    - Display badge next to each contact in selection list
    - _Requirements: 4.3_

- [x] 15. Final Checkpoint - All tests passing





  - Ensure all tests pass, ask the user if questions arise.
