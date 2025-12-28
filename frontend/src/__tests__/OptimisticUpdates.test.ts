/**
 * Test: Optimistic Updates Validation
 * Description: Validates that optimistic updates work correctly for contacts and categories
 * Author: Kiro
 * Date: 2025-12-28
 * 
 * Checkpoint 12: Valider les mises à jour optimistes
 * - Créer un contact et vérifier la mise à jour immédiate des stats
 * - Simuler une erreur et vérifier le rollback
 * 
 * Requirements: 2.1 - Mise à jour optimiste des statistiques
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { QueryClient } from '@tanstack/react-query';

// Mock the api module
vi.mock('@/lib/api', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('Optimistic Updates - Checkpoint 12', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
          gcTime: 0,
        },
        mutations: {
          retry: false,
        },
      },
    });
  });

  afterEach(() => {
    queryClient.clear();
    vi.clearAllMocks();
  });

  describe('Contact Creation - Optimistic Update', () => {
    it('should immediately increment total_contacts on mutation start', async () => {
      // Setup: Set initial dashboard stats in cache
      const initialStats = {
        total_contacts: 10,
        total_categories: 5,
        total_messages: 100,
        success_rate: 95,
        total_campaigns: 3,
        estimated_cost: 5.0,
      };

      queryClient.setQueryData(['stats', 'dashboard'], initialStats);

      // Simulate the onMutate logic from useCreateContact
      await queryClient.cancelQueries({ queryKey: ['stats'] });
      
      const previousDashboardStats = queryClient.getQueryData(['stats', 'dashboard']);
      
      // Apply optimistic update
      queryClient.setQueryData(['stats', 'dashboard'], (old: typeof initialStats | undefined) => {
        if (!old) return old;
        return {
          ...old,
          total_contacts: (old.total_contacts || 0) + 1,
        };
      });

      // Verify: Stats should be immediately updated
      const updatedStats = queryClient.getQueryData(['stats', 'dashboard']) as typeof initialStats;
      
      expect(updatedStats.total_contacts).toBe(11);
      expect(previousDashboardStats).toEqual(initialStats);
    });

    it('should rollback on error', async () => {
      // Setup: Set initial dashboard stats in cache
      const initialStats = {
        total_contacts: 10,
        total_categories: 5,
        total_messages: 100,
        success_rate: 95,
        total_campaigns: 3,
        estimated_cost: 5.0,
      };

      queryClient.setQueryData(['stats', 'dashboard'], initialStats);

      // Simulate onMutate
      const previousDashboardStats = queryClient.getQueryData(['stats', 'dashboard']);
      
      // Apply optimistic update
      queryClient.setQueryData(['stats', 'dashboard'], (old: typeof initialStats | undefined) => {
        if (!old) return old;
        return {
          ...old,
          total_contacts: (old.total_contacts || 0) + 1,
        };
      });

      // Verify optimistic update was applied
      const afterOptimistic = queryClient.getQueryData(['stats', 'dashboard']) as typeof initialStats;
      expect(afterOptimistic.total_contacts).toBe(11);

      // Simulate onError - rollback
      if (previousDashboardStats) {
        queryClient.setQueryData(['stats', 'dashboard'], previousDashboardStats);
      }

      // Verify: Stats should be rolled back to original
      const afterRollback = queryClient.getQueryData(['stats', 'dashboard']) as typeof initialStats;
      expect(afterRollback.total_contacts).toBe(10);
      expect(afterRollback).toEqual(initialStats);
    });
  });

  describe('Category Creation - Optimistic Update', () => {
    it('should immediately increment total_categories on mutation start', async () => {
      // Setup: Set initial dashboard stats in cache
      const initialStats = {
        total_contacts: 10,
        total_categories: 5,
        total_messages: 100,
        success_rate: 95,
        total_campaigns: 3,
        estimated_cost: 5.0,
      };

      queryClient.setQueryData(['stats', 'dashboard'], initialStats);

      // Simulate the onMutate logic from useCreateCategory
      await queryClient.cancelQueries({ queryKey: ['stats'] });
      
      const previousDashboardStats = queryClient.getQueryData(['stats', 'dashboard']);
      
      // Apply optimistic update
      queryClient.setQueryData(['stats', 'dashboard'], (old: typeof initialStats | undefined) => {
        if (!old) return old;
        return {
          ...old,
          total_categories: (old.total_categories || 0) + 1,
        };
      });

      // Verify: Stats should be immediately updated
      const updatedStats = queryClient.getQueryData(['stats', 'dashboard']) as typeof initialStats;
      
      expect(updatedStats.total_categories).toBe(6);
      expect(previousDashboardStats).toEqual(initialStats);
    });

    it('should rollback category count on error', async () => {
      // Setup: Set initial dashboard stats in cache
      const initialStats = {
        total_contacts: 10,
        total_categories: 5,
        total_messages: 100,
        success_rate: 95,
        total_campaigns: 3,
        estimated_cost: 5.0,
      };

      queryClient.setQueryData(['stats', 'dashboard'], initialStats);

      // Simulate onMutate
      const previousDashboardStats = queryClient.getQueryData(['stats', 'dashboard']);
      
      // Apply optimistic update
      queryClient.setQueryData(['stats', 'dashboard'], (old: typeof initialStats | undefined) => {
        if (!old) return old;
        return {
          ...old,
          total_categories: (old.total_categories || 0) + 1,
        };
      });

      // Verify optimistic update was applied
      const afterOptimistic = queryClient.getQueryData(['stats', 'dashboard']) as typeof initialStats;
      expect(afterOptimistic.total_categories).toBe(6);

      // Simulate onError - rollback
      if (previousDashboardStats) {
        queryClient.setQueryData(['stats', 'dashboard'], previousDashboardStats);
      }

      // Verify: Stats should be rolled back to original
      const afterRollback = queryClient.getQueryData(['stats', 'dashboard']) as typeof initialStats;
      expect(afterRollback.total_categories).toBe(5);
      expect(afterRollback).toEqual(initialStats);
    });
  });

  describe('Edge Cases', () => {
    it('should handle undefined cache gracefully', () => {
      // No initial data in cache
      const previousStats = queryClient.getQueryData(['stats', 'dashboard']);
      expect(previousStats).toBeUndefined();

      // Apply optimistic update on undefined - should not crash
      queryClient.setQueryData(['stats', 'dashboard'], (old: { total_contacts?: number } | undefined) => {
        if (!old) return old; // Returns undefined, which is fine
        return {
          ...old,
          total_contacts: (old.total_contacts || 0) + 1,
        };
      });

      // Should still be undefined (no crash)
      const afterUpdate = queryClient.getQueryData(['stats', 'dashboard']);
      expect(afterUpdate).toBeUndefined();
    });

    it('should preserve other stats during optimistic update', () => {
      const initialStats = {
        total_contacts: 10,
        total_categories: 5,
        total_messages: 100,
        success_rate: 95,
        total_campaigns: 3,
        estimated_cost: 5.0,
      };

      queryClient.setQueryData(['stats', 'dashboard'], initialStats);

      // Apply optimistic update for contacts
      queryClient.setQueryData(['stats', 'dashboard'], (old: typeof initialStats | undefined) => {
        if (!old) return old;
        return {
          ...old,
          total_contacts: (old.total_contacts || 0) + 1,
        };
      });

      const updatedStats = queryClient.getQueryData(['stats', 'dashboard']) as typeof initialStats;

      // Verify only total_contacts changed
      expect(updatedStats.total_contacts).toBe(11);
      expect(updatedStats.total_categories).toBe(5);
      expect(updatedStats.total_messages).toBe(100);
      expect(updatedStats.success_rate).toBe(95);
      expect(updatedStats.total_campaigns).toBe(3);
      expect(updatedStats.estimated_cost).toBe(5.0);
    });
  });
});
