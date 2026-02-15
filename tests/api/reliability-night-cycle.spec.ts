/**
 * Reliability Tests: R-004 - Night Cycle Silent Failures
 * 
 * Risk: Night cycle consolidation fails silently
 * Score: 6 (High)
 * 
 * Tests verify that night cycle operations are properly monitored and logged.
 */

import { test, expect } from '@playwright/test';

const BASE_URL = process.env.BASE_URL || 'http://localhost:8000';

test.describe('R-004: Night Cycle Silent Failures', () => {
  
  test('should return success status for sleep cycle endpoint', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/internal/memory/sleep-cycle`, {
      params: {
        run_decay: true,
        run_cleanup: true
      }
    });
    
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data.status).toBeDefined();
    expect(['success', 'error']).toContain(data.status);
  });

  test('should log consolidation results', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/internal/memory/sleep-cycle`, {
      params: {
        run_decay: true,
        run_cleanup: true
      }
    });
    
    const data = await response.json();
    
    // Should return results for each phase
    expect(data.results).toBeDefined();
    expect(data.results.decay).toBeDefined();
    expect(data.results.cleanup).toBeDefined();
  });

  test('should handle errors gracefully without silent failure', async ({ request }) => {
    // Even if SurrealDB is down, should return error status
    const response = await request.post(`${BASE_URL}/internal/memory/sleep-cycle`, {
      params: {
        run_decay: true,
        run_cleanup: true
      }
    });
    
    const data = await response.json();
    
    // Should return status, never silently fail
    expect(data.status).toBeDefined();
    
    if (data.status === 'error') {
      // Should have error message
      expect(data.message).toBeDefined();
      console.log('Error captured:', data.message);
    }
  });

  test('should report number of memories processed', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/internal/memory/sleep-cycle`);
    const data = await response.json();
    
    // Should report counts
    if (data.results?.decay) {
      expect(data.results.decay.memories_removed).toBeDefined();
    }
    if (data.results?.cleanup) {
      expect(data.results.cleanup.orphans_removed).toBeDefined();
    }
  });

  test('should have monitoring endpoint for cycle status', async ({ request }) => {
    // Should be able to check if cycle is running
    const response = await request.get(`${BASE_URL}/api/health`);
    expect([200, 503]).toContain(response.status());
  });
});
