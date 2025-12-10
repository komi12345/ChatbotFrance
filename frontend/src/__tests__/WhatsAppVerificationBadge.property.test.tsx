/**
 * Property-Based Tests for WhatsAppVerificationBadge Component
 * 
 * **Feature: whatsapp-verification, Property 4: Badge rendering matches verification status**
 * **Validates: Requirements 2.1, 2.2, 2.3**
 * 
 * Tests that the badge renders correctly for all possible verification statuses:
 * - Green badge with WhatsApp icon when verified (Requirements 2.1)
 * - Red badge with warning icon when not_whatsapp (Requirements 2.2)
 * - Gray badge with "non vérifié" when pending/null (Requirements 2.3)
 */

import { describe, it, expect } from 'vitest'
import * as fc from 'fast-check'
import { render, screen } from '@testing-library/react'
import { WhatsAppVerificationBadge, WhatsAppVerificationStatus } from '@/components/whatsapp/WhatsAppVerificationBadge'

// Arbitrary for generating all possible WhatsApp verification statuses
const whatsAppStatusArbitrary = fc.oneof(
  fc.constant('verified' as const),
  fc.constant('not_whatsapp' as const),
  fc.constant('pending' as const),
  fc.constant(null)
)

// Arbitrary for badge size
const sizeArbitrary = fc.oneof(
  fc.constant('sm' as const),
  fc.constant('md' as const)
)

describe('WhatsAppVerificationBadge Property Tests', () => {
  /**
   * **Feature: whatsapp-verification, Property 4: Badge rendering matches verification status**
   * **Validates: Requirements 2.1, 2.2, 2.3**
   * 
   * *For any* contact, the WhatsAppVerificationBadge component SHALL render:
   * - Green badge with WhatsApp icon when `whatsapp_verified === true` (status = 'verified')
   * - Red badge with warning icon when `whatsapp_verified === false` (status = 'not_whatsapp')
   * - Gray badge with "non vérifié" text when `whatsapp_verified === null` (status = 'pending' or null)
   */
  it('should render correct label for any verification status', () => {
    fc.assert(
      fc.property(
        whatsAppStatusArbitrary,
        sizeArbitrary,
        (status: WhatsAppVerificationStatus, size) => {
          const { unmount } = render(
            <WhatsAppVerificationBadge status={status} size={size} />
          )

          // Determine expected label based on status
          let expectedLabel: string
          if (status === 'verified') {
            expectedLabel = 'WhatsApp'
          } else if (status === 'not_whatsapp') {
            expectedLabel = 'Non-WhatsApp'
          } else {
            // pending or null should show "Non vérifié"
            expectedLabel = 'Non vérifié'
          }

          // Verify the label is rendered
          expect(screen.getByText(expectedLabel)).toBeDefined()

          unmount()
        }
      ),
      { numRuns: 100 }
    )
  })

  /**
   * Property: Badge styling matches verification status
   * 
   * Verifies that the correct CSS classes are applied based on status:
   * - verified: green styling (bg-[#D1FAE5], text-[#059669])
   * - not_whatsapp: red styling (bg-[#FEE2E2], text-[#DC2626])
   * - pending/null: gray styling (bg-[#F3F4F6], text-[#6B7280])
   */
  it('should apply correct styling classes for any verification status', () => {
    fc.assert(
      fc.property(
        whatsAppStatusArbitrary,
        (status: WhatsAppVerificationStatus) => {
          const { container, unmount } = render(
            <WhatsAppVerificationBadge status={status} />
          )

          const badge = container.querySelector('span')
          expect(badge).not.toBeNull()

          if (status === 'verified') {
            // Green badge for verified (Requirements 2.1)
            expect(badge?.className).toContain('bg-[#D1FAE5]')
            expect(badge?.className).toContain('text-[#059669]')
          } else if (status === 'not_whatsapp') {
            // Red badge for not_whatsapp (Requirements 2.2)
            expect(badge?.className).toContain('bg-[#FEE2E2]')
            expect(badge?.className).toContain('text-[#DC2626]')
          } else {
            // Gray badge for pending/null (Requirements 2.3)
            expect(badge?.className).toContain('bg-[#F3F4F6]')
            expect(badge?.className).toContain('text-[#6B7280]')
          }

          unmount()
        }
      ),
      { numRuns: 100 }
    )
  })

  /**
   * Property: null status is treated as pending
   * 
   * Verifies that null status is mapped to 'pending' display behavior
   */
  it('should treat null status identically to pending status', () => {
    fc.assert(
      fc.property(
        sizeArbitrary,
        (size) => {
          // Render with null status
          const { container: nullContainer, unmount: unmountNull } = render(
            <WhatsAppVerificationBadge status={null} size={size} />
          )
          const nullBadge = nullContainer.querySelector('span')
          const nullClassName = nullBadge?.className
          const nullText = nullBadge?.textContent

          unmountNull()

          // Render with pending status
          const { container: pendingContainer, unmount: unmountPending } = render(
            <WhatsAppVerificationBadge status="pending" size={size} />
          )
          const pendingBadge = pendingContainer.querySelector('span')
          const pendingClassName = pendingBadge?.className
          const pendingText = pendingBadge?.textContent

          unmountPending()

          // Both should have the same styling and text
          expect(nullClassName).toBe(pendingClassName)
          expect(nullText).toBe(pendingText)
        }
      ),
      { numRuns: 50 }
    )
  })
})
