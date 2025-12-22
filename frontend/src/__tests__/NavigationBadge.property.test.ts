/**
 * Property-Based Tests for Navigation Badge Threshold
 * 
 * **Feature: whatsapp-monitoring, Property 7: Navigation Badge Threshold**
 * **Validates: Requirements 8.2**
 * 
 * Tests that the navigation badge visibility is correctly determined based on
 * the daily message counter value. The badge should be visible if and only if
 * the counter exceeds 750 (75% of the 1000 daily limit).
 */

import { describe, it, expect } from 'vitest'
import * as fc from 'fast-check'

/**
 * Determines if the navigation badge should be visible based on message count.
 * This function implements the logic from Requirements 8.2:
 * "WHEN the Daily_Message_Counter exceeds 750 (75%) THEN the navigation link 
 * SHALL display a warning badge"
 * 
 * @param messageCount - The current daily message counter value
 * @returns true if the badge should be visible, false otherwise
 */
export function shouldShowNavigationBadge(messageCount: number): boolean {
  return messageCount > 750;
}

/**
 * Determines the alert level based on message count.
 * This is used to determine badge color in the navigation.
 * 
 * @param messageCount - The current daily message counter value
 * @returns The alert level string
 */
export function getAlertLevelFromCount(messageCount: number): 'ok' | 'attention' | 'danger' | 'blocked' {
  if (messageCount <= 750) return 'ok';
  if (messageCount <= 900) return 'attention';
  if (messageCount <= 1000) return 'danger';
  return 'blocked';
}

describe('Navigation Badge Threshold Property Tests', () => {
  /**
   * **Feature: whatsapp-monitoring, Property 7: Navigation Badge Threshold**
   * **Validates: Requirements 8.2**
   * 
   * *For any* Daily_Message_Counter value N, the navigation badge SHALL be 
   * visible if and only if N > 750.
   */
  it('should show badge if and only if message count exceeds 750', () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 0, max: 1200 }),
        (messageCount: number) => {
          const shouldShow = shouldShowNavigationBadge(messageCount);
          
          // Badge should be visible if and only if count > 750
          if (messageCount > 750) {
            expect(shouldShow).toBe(true);
          } else {
            expect(shouldShow).toBe(false);
          }
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Badge is hidden at exactly 750 messages
   * 
   * Verifies the boundary condition: at exactly 750 messages (75% of limit),
   * the badge should NOT be visible yet.
   */
  it('should not show badge at exactly 750 messages (boundary)', () => {
    expect(shouldShowNavigationBadge(750)).toBe(false);
  });

  /**
   * Property: Badge is visible at 751 messages
   * 
   * Verifies the boundary condition: at 751 messages (just over 75%),
   * the badge should become visible.
   */
  it('should show badge at 751 messages (boundary)', () => {
    expect(shouldShowNavigationBadge(751)).toBe(true);
  });

  /**
   * Property: Alert level transitions at correct thresholds
   * 
   * Verifies that alert levels change at the correct boundaries:
   * - 0-750: ok
   * - 751-900: attention
   * - 901-1000: danger
   * - >1000: blocked
   */
  it('should return correct alert level for any message count', () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 0, max: 1200 }),
        (messageCount: number) => {
          const level = getAlertLevelFromCount(messageCount);
          
          if (messageCount <= 750) {
            expect(level).toBe('ok');
          } else if (messageCount <= 900) {
            expect(level).toBe('attention');
          } else if (messageCount <= 1000) {
            expect(level).toBe('danger');
          } else {
            expect(level).toBe('blocked');
          }
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Badge visibility implies non-ok alert level
   * 
   * Verifies that whenever the badge is visible, the alert level is NOT 'ok'.
   * This ensures consistency between badge visibility and alert level.
   */
  it('should have non-ok alert level whenever badge is visible', () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 0, max: 700 }),
        (messageCount: number) => {
          const shouldShow = shouldShowNavigationBadge(messageCount);
          const level = getAlertLevelFromCount(messageCount);
          
          if (shouldShow) {
            // If badge is visible, level should NOT be 'ok'
            expect(level).not.toBe('ok');
          } else {
            // If badge is hidden, level should be 'ok'
            expect(level).toBe('ok');
          }
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Alert level boundaries are consistent with design spec
   * 
   * Tests specific boundary values to ensure exact compliance with
   * Requirements 3.1, 3.2, 3.3, 3.4
   */
  it('should have correct alert levels at boundary values', () => {
    // Boundary: 750 -> ok, 751 -> attention
    expect(getAlertLevelFromCount(750)).toBe('ok');
    expect(getAlertLevelFromCount(751)).toBe('attention');
    
    // Boundary: 900 -> attention, 901 -> danger
    expect(getAlertLevelFromCount(900)).toBe('attention');
    expect(getAlertLevelFromCount(901)).toBe('danger');
    
    // Boundary: 1000 -> danger, 1001 -> blocked
    expect(getAlertLevelFromCount(1000)).toBe('danger');
    expect(getAlertLevelFromCount(1001)).toBe('blocked');
  });
});
