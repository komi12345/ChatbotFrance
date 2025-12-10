/**
 * Property-Based Tests for Category WhatsApp Verification Percentage
 * 
 * **Feature: whatsapp-verification, Property 7: Category verification percentage**
 * **Validates: Requirements 5.2**
 * 
 * Tests that the category verification percentage is calculated correctly:
 * - Percentage equals (verified_count / total_contacts_in_category) * 100
 * - Result is rounded to one decimal place
 */

import { describe, it, expect } from 'vitest'
import * as fc from 'fast-check'
import { calculateVerificationPercentage } from '@/components/whatsapp/CategoryWhatsAppStats'
import type { CategoryContact } from '@/types/category'

// Arbitrary for generating WhatsApp verification status (true, false, null)
const whatsAppVerifiedArbitrary = fc.oneof(
  fc.constant(true),
  fc.constant(false),
  fc.constant(null)
)

// Arbitrary for generating a minimal CategoryContact object
const categoryContactArbitrary = (id: number) => fc.record({
  id: fc.constant(id),
  phone_number: fc.constant(`0612345${String(id).padStart(3, '0')}`),
  country_code: fc.constantFrom('FR', 'US', 'GB', 'DE'),
  full_number: fc.constant(`+336123456${String(id).padStart(2, '0')}`),
  first_name: fc.option(fc.constant(`FirstName${id}`), { nil: null }),
  last_name: fc.option(fc.constant(`LastName${id}`), { nil: null }),
  whatsapp_verified: whatsAppVerifiedArbitrary,
}) as fc.Arbitrary<CategoryContact>

// Arbitrary for generating a list of category contacts with unique IDs
const categoryContactListArbitrary = fc.integer({ min: 0, max: 50 }).chain(size => {
  if (size === 0) {
    return fc.constant([] as CategoryContact[])
  }
  const contactArbitraries = Array.from({ length: size }, (_, i) => categoryContactArbitrary(i + 1))
  return fc.tuple(...contactArbitraries).map(arr => arr as CategoryContact[])
})

describe('Category WhatsApp Verification Percentage Property Tests', () => {
  /**
   * **Feature: whatsapp-verification, Property 7: Category verification percentage**
   * **Validates: Requirements 5.2**
   * 
   * *For any* category with contacts, the WhatsApp verification percentage SHALL equal
   * `(verified_count / total_contacts_in_category) * 100`, rounded to one decimal place.
   */
  it('percentage equals (verified_count / total) * 100 rounded to one decimal', () => {
    fc.assert(
      fc.property(
        categoryContactListArbitrary,
        (contacts) => {
          const result = calculateVerificationPercentage(contacts)
          
          if (contacts.length === 0) {
            // Empty list should return 0
            expect(result).toBe(0)
            return
          }
          
          // Calculate expected percentage
          const verifiedCount = contacts.filter(c => c.whatsapp_verified === true).length
          const expectedPercentage = (verifiedCount / contacts.length) * 100
          const expectedRounded = Math.round(expectedPercentage * 10) / 10
          
          expect(result).toBe(expectedRounded)
        }
      ),
      { numRuns: 100 }
    )
  })

  /**
   * Property: Percentage is always between 0 and 100 inclusive
   */
  it('percentage is always between 0 and 100', () => {
    fc.assert(
      fc.property(
        categoryContactListArbitrary,
        (contacts) => {
          const result = calculateVerificationPercentage(contacts)
          
          expect(result).toBeGreaterThanOrEqual(0)
          expect(result).toBeLessThanOrEqual(100)
        }
      ),
      { numRuns: 100 }
    )
  })

  /**
   * Property: All verified contacts yields 100%
   */
  it('returns 100% when all contacts are verified', () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 1, max: 50 }),
        (size) => {
          // Create contacts all with whatsapp_verified = true
          const contacts: CategoryContact[] = Array.from({ length: size }, (_, i) => ({
            id: i + 1,
            phone_number: `061234500${i}`,
            country_code: 'FR',
            full_number: `+3361234500${i}`,
            first_name: null,
            last_name: null,
            whatsapp_verified: true,
          }))
          
          const result = calculateVerificationPercentage(contacts)
          expect(result).toBe(100)
        }
      ),
      { numRuns: 50 }
    )
  })

  /**
   * Property: No verified contacts yields 0%
   */
  it('returns 0% when no contacts are verified', () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 1, max: 50 }),
        fc.constantFrom(false, null),
        (size, status) => {
          // Create contacts all with whatsapp_verified = false or null
          const contacts: CategoryContact[] = Array.from({ length: size }, (_, i) => ({
            id: i + 1,
            phone_number: `061234500${i}`,
            country_code: 'FR',
            full_number: `+3361234500${i}`,
            first_name: null,
            last_name: null,
            whatsapp_verified: status,
          }))
          
          const result = calculateVerificationPercentage(contacts)
          expect(result).toBe(0)
        }
      ),
      { numRuns: 50 }
    )
  })

  /**
   * Property: Empty contacts array returns 0%
   */
  it('returns 0% for empty contacts array', () => {
    const result = calculateVerificationPercentage([])
    expect(result).toBe(0)
  })

  /**
   * Property: Result has at most one decimal place
   */
  it('result is rounded to at most one decimal place', () => {
    fc.assert(
      fc.property(
        categoryContactListArbitrary,
        (contacts) => {
          const result = calculateVerificationPercentage(contacts)
          
          // Check that multiplying by 10 gives an integer (within floating point tolerance)
          const multiplied = result * 10
          const isOneDecimal = Math.abs(multiplied - Math.round(multiplied)) < 0.0001
          
          expect(isOneDecimal).toBe(true)
        }
      ),
      { numRuns: 100 }
    )
  })
})
