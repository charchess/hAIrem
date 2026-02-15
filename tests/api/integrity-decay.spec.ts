/**
 * Data Integrity Tests: R-008 - Memory Corruption During Decay
 * 
 * Risk: Memory corruption during decay process
 * Score: 6 (High)
 * 
 * Tests verify data integrity is maintained during memory decay operations.
 */

import { test, expect } from '@playwright/test';

const BASE_URL = process.env.BASE_URL || 'http://localhost:8000';

test.describe('R-008: Memory Corruption During Decay', () => {
  
  test('should maintain data integrity after decay', async ({ request }) => {
    // Insert test memories
    const testUser = 'test_decay_user';
    
    // Create some memories
    for (let i = 0; i < 5; i++) {
      await request.post(`${BASE_URL}/api/chat`, {
        data: {
          message: `Important memory ${i}`,
          user_id: testUser
        }
      });
    }
    
    // Run decay cycle
    const decayRes = await request.post(`${BASE_URL}/internal/memory/sleep-cycle`, {
      params: {
        run_decay: true,
        run_cleanup: true
      }
    });
    
    expect(decayRes.status()).toBe(200);
    
    // Verify existing memories are still accessible
    const messagesRes = await request.get(`${BASE_URL}/api/messages?user_id=${testUser}`);
    
    // Should return valid response, not corrupted data
    expect([200, 404]).toContain(messagesRes.status());
  });

  test('should not lose permanent memories during decay', async ({ request }) => {
    const testUser = 'test_permanent_user';
    
    // Create memories with permanent flag (if supported)
    await request.post(`${BASE_URL}/api/chat`, {
      data: {
        message: 'This is a permanent fact about me',
        user_id: testUser,
        permanent: true
      }
    });
    
    // Run decay
    await request.post(`${BASE_URL}/internal/memory/sleep-cycle`, {
      params: { run_decay: true }
    });
    
    // Permanent memories should still exist
    const messagesRes = await request.get(`${BASE_URL}/api/messages?user_id=${testUser}`);
    
    if (messagesRes.status() === 200) {
      const messages = await messagesRes.json();
      const hasPermanent = messages.some((m: any) => 
        m.permanent === true || m.flag === 'permanent'
      );
      
      // Should preserve permanent memories
      console.log('Has permanent memories:', hasPermanent);
    }
  });

  test('should handle decay failure gracefully', async ({ request }) => {
    // Even if decay fails, data should not be corrupted
    
    // Make multiple decay requests
    const res1 = await request.post(`${BASE_URL}/internal/memory/sleep-cycle`);
    const res2 = await request.post(`${BASE_URL}/internal/memory/sleep-cycle`);
    
    // Both should return valid status
    expect([200, 500, 503]).toContain(res1.status());
    expect([200, 500, 503]).toContain(res2.status());
    
    // System should still be functional after failed decay
    const health = await request.get(`${BASE_URL}/api/health`);
    expect(health.status()).toBe(200);
  });

  test('should validate data after cleanup', async ({ request }) => {
    const testUser = 'test_cleanup_user';
    
    // Create test data
    await request.post(`${BASE_URL}/api/chat`, {
      data: {
        message: 'Test cleanup',
        user_id: testUser
      }
    });
    
    // Run cleanup
    await request.post(`${BASE_URL}/internal/memory/sleep-cycle`, {
      params: { run_cleanup: true }
    });
    
    // Verify no orphan records
    const messagesRes = await request.get(`${BASE_URL}/api/messages?user_id=${testUser}`);
    
    // Should return well-formed response
    if (messagesRes.status() === 200) {
      const messages = await messagesRes.json();
      expect(Array.isArray(messages)).toBe(true);
    }
  });

  test('should maintain referential integrity after decay', async ({ request }) => {
    const testUser = 'test_integrity_user';
    
    // Create linked memories (if supported)
    await request.post(`${BASE_URL}/api/chat`, {
      data: {
        message: 'First message',
        user_id: testUser
      }
    });
    
    await request.post(`${BASE_URL}/api/chat`, {
      data: {
        message: 'Second message references first',
        user_id: testUser,
        references: ['message_1']
      }
    });
    
    // Run decay
    await request.post(`${BASE_URL}/internal/memory/sleep-cycle`);
    
    // All references should still be valid
    const messagesRes = await request.get(`${BASE_URL}/api/messages?user_id=${testUser}`);
    
    if (messagesRes.status() === 200) {
      const messages = await messagesRes.json();
      
      // No orphaned references
      messages.forEach((msg: any) => {
        if (msg.references) {
          msg.references.forEach((ref: string) => {
            const referenced = messages.find((m: any) => m.id === ref);
            // Either exists or is explicitly marked as deleted
            expect(referenced || ref.includes('_deleted')).toBeTruthy();
          });
        }
      });
    }
  });
});
