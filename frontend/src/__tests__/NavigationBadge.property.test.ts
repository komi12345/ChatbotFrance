/**
 * Property-Based Tests for Navigation Badge Threshold
 * 
 * **Feature: whatsapp-monitoring, Property 7: Navigation Badge Threshold**
 * **Validates: Requirements 8.2**
 * 
 * Tests that the navigation badge visibility is correctly determined based on
 * the daily message counter value. The badge should be visible if and only if
 * the counter exceeds 135 (75% of the 180 daily limit).
 */

import { describe, it, expect } from 'vitest'
import * as fc from 'fast-check'

/**
 * Determines if the navigation badge should be visible based on message count.
 * This function implements the logic from Requirements 8.2:
 * "WHEN the Daily_Message_Counter exceeds 135 (75%) THEN the navigation link 
 * SHALL display a warning badge"
 * 
 * @param messageCount - The current daily message counter value
 * @returns true if the badge should be visible, false otherwise
 */
export function shouldShowNavigationBadge(messageCount: number): boolean {
  return messageCount > 135;
}

/**
 * Determines the alert level based on message count.
 * This is used to determine badge color in the navigation.
 * 
 * @param messageCount - The current daily message counter value
 * @returns The alert level string
 */
export function getAlertLevelFromCount(messageCount: number): 'ok' | 'attention' | 'danger' | 'blocked' {
  if (messageCount <= 135) return 'ok';
  if (messageCount <= 162) return 'attention';
  if (messageCount <= 180) return 'danger';
  return 'blocked';
}

describe('Navigation Badge Threshold Property Tests', () => {
  /**
   * **Feature: whatsapp-monitoring, Property 7: Navigation Badge Threshold**
   * **Validates: Requirements 8.2**
   * 
   * *For any* Daily_Message_Counter value N, the navigation badge SHALL be 
   * visible if and only if N > 135.
   */
  it('should show badge if and only if message count exceeds 135', () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 0, max: 300 }),
        (messageCount: number) => {
          const shouldShow = shouldShowNavigationBadge(messageCount);
          
          // Badge should be visible if and only if count > 135
          if (messageCount > 135) {
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
   * Property: Badge is hidden at exactly 135 messages
   * 
   * Verifies the boundary condition: at exactly 135 messages (75% of limit),
   * the badge should NOT be visible yet.
   */
  it('should not show badge at exactly 135 messages (boundary)', () => {
    expect(shouldShowNavigationBadge(135)).toBe(false);
  });

  /**
   * Property: Badge is visible at 136 messages
   * 
   * Verifies the boundary condition: at 136 messages (just over 75%),
   * the badge should become visible.
   */
  it('should show badge at 136 messages (boundary)', () => {
    expect(shouldShowNavigationBadge(136)).toBe(true);
  });

  /**
   * Property: Alert level transitions at correct thresholds
   * 
   * Verifies that alert levels change at the correct boundaries:
   * - 0-135: ok
   * - 136-162: attention
   * - 163-180: danger
   * - >180: blocked
   */
  it('should return correct alert level for any message count', () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 0, max: 300 }),
        (messageCount: number) => {
          const level = getAlertLevelFromCount(messageCount);
          
          if (messageCount <= 135) {
            expect(level).toBe('ok');
          } else if (messageCount <= 162) {
            expect(level).toBe('attention');
          } else if (messageCount <= 180) {
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
        fc.integer({ min: 0, max: 300 }),
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
    // Boundary: 135 -> ok, 136 -> attention
    expect(getAlertLevelFromCount(135)).toBe('ok');
    expect(getAlertLevelFromCount(136)).toBe('attention');
    
    // Boundary: 162 -> attention, 163 -> danger
    expect(getAlertLevelFromCount(162)).toBe('attention');
    expect(getAlertLevelFromCount(163)).toBe('danger');
    
    // Boundary: 180 -> danger, 181 -> blocked
    expect(getAlertLevelFromCount(180)).toBe('danger');
    expect(getAlertLevelFromCount(181)).toBe('blocked');
  });
});
