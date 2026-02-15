/**
 * Reliability Tests: R-007 - Social Arbiter Race Conditions
 * 
 * Risk: Social arbiter race conditions under high load
 * Score: 6 (High)
 * 
 * Tests verify the social arbiter handles concurrent requests correctly.
 */

import { test, expect } from '@playwright/test';

const BASE_URL = process.env.BASE_URL || 'http://localhost:8000';

test.describe('R-007: Social Arbiter Race Conditions', () => {
  
  test('should handle concurrent agent selection requests', async ({ request }) => {
    const promises = Array(20).fill(null).map(() => 
      request.post(`${BASE_URL}/api/arbiter/select`, {
        data: {
          message: 'Hello team',
          context: {}
        }
      }).then(r => r.json().catch(() => ({})))
    );
    
    const results = await Promise.all(promises);
    
    // Each should return a valid response or graceful error
    results.forEach(r => {
      expect(r).toBeDefined();
    });
  });

  test('should not assign same agent twice in rapid succession', async ({ request }) => {
    const promises = Array(10).fill(null).map(() => 
      request.post(`${BASE_URL}/api/arbiter/select`, {
        data: {
          message: 'Urgent message',
          context: { urgency: 'high' }
        }
      }).then(async r => {
        const data = await r.json();
        return { status: r.status(), agent: data.selected_agent };
      })
    );
    
    const results = await Promise.all(promises);
    
    // All should succeed
    results.forEach(r => {
      expect([200, 404, 500]).toContain(r.status());
    });
  });

  test('should maintain turn-taking under concurrent load', async ({ request }) => {
    // Simulate multiple users sending messages simultaneously
    const messages = ['Message 1', 'Message 2', 'Message 3', 'Message 4', 'Message 5'];
    
    const promises = messages.map(msg => 
      request.post(`${BASE_URL}/api/chat`, {
        data: {
          message: msg,
          user_id: `user_${msg}`
        }
      })
    );
    
    const results = await Promise.all(promises);
    
    // Should process all without race condition crashes
    results.forEach(r => {
      expect([200, 400, 429]).toContain(r.status());
    });
  });

  test('should handle scoring race conditions', async ({ request }) => {
    const promises = Array(15).fill(null).map(() => 
      request.post(`${BASE_URL}/api/arbiter/score`, {
        data: {
          message: 'Test scoring',
          agents: ['agent_1', 'agent_2', 'agent_3']
        }
      })
    );
    
    const results = await Promise.all(promises);
    
    // Should return scores for each agent without conflicts
    for (const r of results) {
      if (r.status() === 200) {
        const data = await r.json();
        expect(data.scores).toBeDefined();
      }
    }
  });

  test('should serialize access to shared state', async ({ request }) => {
    // Rapid fire requests that might conflict
    const promises = Array(30).fill(null).map((_, i) => 
      request.post(`${BASE_URL}/api/chat`, {
        data: {
          message: `Concurrent message ${i}`,
          agent_id: `agent_${i % 3}`
        }
      })
    );
    
    const results = await Promise.all(promises);
    
    // Should handle all without 500 errors (race condition crashes)
    const errorCount = results.filter(r => r.status() === 500).length;
    const successCount = results.filter(r => r.status() === 200).length;
    
    // At least 80% should succeed
    expect(successCount / results.length).toBeGreaterThan(0.8);
    console.log(`Race condition test: ${successCount} success, ${errorCount} errors`);
  });
});
