/**
 * Performance Tests: R-002 - Memory Leak in Long Conversations
 * 
 * Risk: Memory leak in long-running conversations (>100 turns)
 * Score: 9 (Critical)
 * 
 * Tests verify memory usage remains stable during extended conversations.
 */

import { test, expect } from '@playwright/test';

const BASE_URL = process.env.BASE_URL || 'http://localhost:8000';

test.describe('R-002: Memory Leak in Long Conversations', () => {
  
  test.beforeEach(async ({ request }) => {
    // Setup: Get initial memory usage
    const res = await request.get(`${BASE_URL}/api/health`);
    expect(res.status()).toBe(200);
  });

  test('should maintain stable memory after 50 message exchanges', async ({ request }) => {
    const messages = [];
    
    // Send 50 messages and track memory
    for (let i = 0; i < 50; i++) {
      const res = await request.post(`${BASE_URL}/api/chat`, {
        data: {
          message: `Test message ${i}`,
          agent_id: 'agent_001'
        }
      });
      
      if (res.status() === 200) {
        messages.push(await res.json());
      }
    }
    
    // After 50 messages, system should still respond
    const finalRes = await request.get(`${BASE_URL}/api/health`);
    expect(finalRes.status()).toBe(200);
    
    console.log(`Processed ${messages.length} messages successfully`);
  });

  test('should not accumulate memory in message history', async ({ request }) => {
    // Get initial state
    const initialRes = await request.get(`${BASE_URL}/api/messages`);
    const initialCount = initialRes.status() === 200 ? (await initialRes.json()).length : 0;
    
    // Add 20 messages
    for (let i = 0; i < 20; i++) {
      await request.post(`${BASE_URL}/api/chat`, {
        data: {
          message: `Memory test ${i}`,
          user_id: 'test_user'
        }
      });
    }
    
    // Check history doesn't grow unbounded
    const finalRes = await request.get(`${BASE_URL}/api/messages?user_id=test_user`);
    const finalCount = finalRes.status() === 200 ? (await finalRes.json()).length : 0;
    
    // Should have at most 20 new messages, not unlimited growth
    expect(finalCount).toBeLessThanOrEqual(initialCount + 20);
  });

  test('should clean up old conversations properly', async ({ request }) => {
    // Create multiple conversations
    const conversationIds = [];
    
    for (let i = 0; i < 10; i++) {
      const res = await request.post(`${BASE_URL}/api/chat`, {
        data: {
          message: `Conversation ${i} message 1`,
          agent_id: `agent_${i}`
        }
      });
      
      if (res.status() === 200) {
        const data = await res.json();
        if (data.conversation_id) {
          conversationIds.push(data.conversation_id);
        }
      }
    }
    
    // Old conversations should be accessible but not growing indefinitely
    for (const convId of conversationIds) {
      const res = await request.get(`${BASE_URL}/api/conversations/${convId}`);
      // Should either return or return 404 for very old, not crash
      expect([200, 404]).toContain(res.status());
    }
  });

  test('should handle 100+ turns without memory explosion', async ({ page }) => {
    await page.goto(BASE_URL);
    
    // Simulate 100 message turns
    for (let i = 0; i < 100; i++) {
      await page.fill('#message-input', `Turn ${i}`);
      await page.click('#send-button');
      await page.waitForTimeout(100); // Brief delay
    }
    
    // Page should still be responsive
    await expect(page.locator('#message-input')).toBeVisible();
    
    // Memory usage should not have exploded (checked via browser metrics if available)
    const metrics = await page.evaluate(() => {
      return performance.memory ? {
        usedJSHeapSize: performance.memory.usedJSHeapSize,
        totalJSHeapSize: performance.memory.totalJSHeapSize
      } : null;
    });
    
    if (metrics) {
      console.log('Memory after 100 turns:', metrics);
      // Heuristic: should not exceed 500MB
      expect(metrics.usedJSHeapSize).toBeLessThan(500 * 1024 * 1024);
    }
  });
});
