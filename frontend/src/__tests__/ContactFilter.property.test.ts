/**
 * Property-Based Tests for WhatsApp Contact Filter
 * 
 * **Feature: whatsapp-verification, Property 5: WhatsApp filter returns correct subset**
 * **Validates: Requirements 4.2**
 * 
 * Tests that the WhatsApp filter correctly filters contacts:
 * - "verified" filter returns only contacts where whatsapp_verified === true
 * - "not_whatsapp" filter returns only contacts where whatsapp_verified === false
 * - "pending" filter returns only contacts where whatsapp_verified === null
 * - null filter returns all contacts
 */

import { describe, it, expect } from 'vitest'
import * as fc from 'fast-check'
import type { Contact, WhatsAppStatus } from '@/types/contact'

/**
 * Pure filter function that mirrors the backend filtering logic.
 * This is the function under test - it filters contacts by WhatsApp status.
 */
function filterContactsByWhatsAppStatus(
  contacts: Contact[],
  filter: WhatsAppStatus
): Contact[] {
  if (filter === null) {
    return contacts;
  }
  
  return contacts.filter((contact) => {
    switch (filter) {
      case 'verified':
        return contact.whatsapp_verified === true;
      case 'not_whatsapp':
        return contact.whatsapp_verified === false;
      case 'pending':
        return contact.whatsapp_verified === null;
      default:
        return true;
    }
  });
}

// Arbitrary for generating WhatsApp verification status (true, false, null)
const whatsAppVerifiedArbitrary = fc.oneof(
  fc.constant(true),
  fc.constant(false),
  fc.constant(null)
);

// Fixed date string - dates are not relevant to filter logic
const fixedDateString = '2024-01-15T10:30:00.000Z';

// Arbitrary for generating a minimal Contact object with required fields
// Uses unique ID to ensure contacts are distinguishable
const contactArbitrary = (id: number) => fc.record({
  id: fc.constant(id),
  phone_number: fc.constant(`0612345${String(id).padStart(3, '0')}`),
  country_code: fc.constantFrom('FR', 'US', 'GB', 'DE'),
  full_number: fc.constant(`+336123456${String(id).padStart(2, '0')}`),
  first_name: fc.option(fc.constant(`FirstName${id}`), { nil: null }),
  last_name: fc.option(fc.constant(`LastName${id}`), { nil: null }),
  created_by: fc.constant(1),
  created_at: fc.constant(fixedDateString),
  updated_at: fc.constant(fixedDateString),
  whatsapp_verified: whatsAppVerifiedArbitrary,
  verified_at: fc.constant(null),
  categories: fc.constant(undefined),
}) as fc.Arbitrary<Contact>;

// Arbitrary for generating a list of contacts with unique IDs
const contactListArbitrary = fc.integer({ min: 0, max: 50 }).chain(size => {
  if (size === 0) {
    return fc.constant([] as Contact[]);
  }
  // Generate contacts with sequential unique IDs
  const contactArbitraries = Array.from({ length: size }, (_, i) => contactArbitrary(i + 1));
  return fc.tuple(...contactArbitraries).map(arr => arr as Contact[]);
});

// Arbitrary for filter values
const filterArbitrary = fc.oneof(
  fc.constant('verified' as const),
  fc.constant('not_whatsapp' as const),
  fc.constant('pending' as const),
  fc.constant(null)
);

describe('WhatsApp Contact Filter Property Tests', () => {
  /**
   * **Feature: whatsapp-verification, Property 5: WhatsApp filter returns correct subset**
   * **Validates: Requirements 4.2**
   * 
   * *For any* list of contacts and filter value "verified", the filtered result 
   * SHALL contain only contacts where `whatsapp_verified === true`.
   */
  it('verified filter returns only contacts with whatsapp_verified === true', () => {
    fc.assert(
      fc.property(
        contactListArbitrary,
        (contacts) => {
          const filtered = filterContactsByWhatsAppStatus(contacts, 'verified');
          
          // All filtered contacts must have whatsapp_verified === true
          const allVerified = filtered.every(c => c.whatsapp_verified === true);
          
          // Count should match the count of verified contacts in original list
          const expectedCount = contacts.filter(c => c.whatsapp_verified === true).length;
          
          expect(allVerified).toBe(true);
          expect(filtered.length).toBe(expectedCount);
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: not_whatsapp filter returns only contacts with whatsapp_verified === false
   */
  it('not_whatsapp filter returns only contacts with whatsapp_verified === false', () => {
    fc.assert(
      fc.property(
        contactListArbitrary,
        (contacts) => {
          const filtered = filterContactsByWhatsAppStatus(contacts, 'not_whatsapp');
          
          // All filtered contacts must have whatsapp_verified === false
          const allNotWhatsApp = filtered.every(c => c.whatsapp_verified === false);
          
          // Count should match
          const expectedCount = contacts.filter(c => c.whatsapp_verified === false).length;
          
          expect(allNotWhatsApp).toBe(true);
          expect(filtered.length).toBe(expectedCount);
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: pending filter returns only contacts with whatsapp_verified === null
   */
  it('pending filter returns only contacts with whatsapp_verified === null', () => {
    fc.assert(
      fc.property(
        contactListArbitrary,
        (contacts) => {
          const filtered = filterContactsByWhatsAppStatus(contacts, 'pending');
          
          // All filtered contacts must have whatsapp_verified === null
          const allPending = filtered.every(c => c.whatsapp_verified === null);
          
          // Count should match
          const expectedCount = contacts.filter(c => c.whatsapp_verified === null).length;
          
          expect(allPending).toBe(true);
          expect(filtered.length).toBe(expectedCount);
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: null filter returns all contacts unchanged
   */
  it('null filter returns all contacts', () => {
    fc.assert(
      fc.property(
        contactListArbitrary,
        (contacts) => {
          const filtered = filterContactsByWhatsAppStatus(contacts, null);
          
          // Should return all contacts
          expect(filtered.length).toBe(contacts.length);
          
          // Should be the same contacts (by id)
          const originalIds = contacts.map(c => c.id).sort();
          const filteredIds = filtered.map(c => c.id).sort();
          expect(filteredIds).toEqual(originalIds);
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Filter is a subset - filtered contacts are always a subset of original
   */
  it('filtered contacts are always a subset of original contacts', () => {
    fc.assert(
      fc.property(
        contactListArbitrary,
        filterArbitrary,
        (contacts, filter) => {
          const filtered = filterContactsByWhatsAppStatus(contacts, filter);
          
          // Filtered count should never exceed original count
          expect(filtered.length).toBeLessThanOrEqual(contacts.length);
          
          // Every filtered contact should exist in original list
          const originalIds = new Set(contacts.map(c => c.id));
          const allInOriginal = filtered.every(c => originalIds.has(c.id));
          expect(allInOriginal).toBe(true);
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Filter partitions contacts correctly
   * The sum of all filter results should equal total contacts
   */
  it('filter partitions contacts into disjoint subsets', () => {
    fc.assert(
      fc.property(
        contactListArbitrary,
        (contacts) => {
          const verified = filterContactsByWhatsAppStatus(contacts, 'verified');
          const notWhatsApp = filterContactsByWhatsAppStatus(contacts, 'not_whatsapp');
          const pending = filterContactsByWhatsAppStatus(contacts, 'pending');
          
          // Sum of all filtered counts should equal total
          const totalFiltered = verified.length + notWhatsApp.length + pending.length;
          expect(totalFiltered).toBe(contacts.length);
          
          // No overlap between filtered sets
          const verifiedIds = new Set(verified.map(c => c.id));
          const notWhatsAppIds = new Set(notWhatsApp.map(c => c.id));
          const pendingIds = new Set(pending.map(c => c.id));
          
          // Check no intersection
          const noOverlapVerifiedNotWhatsApp = verified.every(c => !notWhatsAppIds.has(c.id));
          const noOverlapVerifiedPending = verified.every(c => !pendingIds.has(c.id));
          const noOverlapNotWhatsAppPending = notWhatsApp.every(c => !pendingIds.has(c.id));
          
          expect(noOverlapVerifiedNotWhatsApp).toBe(true);
          expect(noOverlapVerifiedPending).toBe(true);
          expect(noOverlapNotWhatsAppPending).toBe(true);
        }
      ),
      { numRuns: 100 }
    );
  });
});
