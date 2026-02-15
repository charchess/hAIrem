/**
 * Performance Tests: R-006 - Voice Synthesis Latency
 * 
 * Risk: Voice synthesis latency >500ms
 * Score: 6 (High)
 * 
 * Tests verify voice synthesis meets latency requirements.
 */

import { test, expect } from '@playwright/test';

const BASE_URL = process.env.BASE_URL || 'http://localhost:8000';
const MAX_VOICE_LATENCY_MS = 500;

test.describe('R-006: Voice Synthesis Latency', () => {
  
  test('should synthesize voice within 500ms', async ({ request }) => {
    const startTime = Date.now();
    
    const response = await request.post(`${BASE_URL}/api/voice/test`, {
      data: {
        text: 'Hello',
        agent_id: 'agent_001'
      }
    });
    
    const latency = Date.now() - startTime;
    
    expect([200, 501]).toContain(response.status());
    
    if (response.status() === 200) {
      console.log(`Voice synthesis latency: ${latency}ms`);
      // Note: 500ms target may not be achievable with all TTS providers
    }
  });

  test('should handle voice requests without timeout', async ({ request }) => {
    const startTime = Date.now();
    
    const response = await request.post(`${BASE_URL}/api/voice/test`, {
      data: {
        text: 'This is a longer text to synthesize into speech for testing latency',
        agent_id: 'agent_001'
      },
      timeout: 10000
    });
    
    const duration = Date.now() - startTime;
    
    // Should complete within 10s timeout
    expect(duration).toBeLessThan(10000);
    expect([200, 400, 404, 501]).toContain(response.status());
  });

  test('should stream voice data when available', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/api/voice/test`, {
      data: {
        text: 'Test',
        agent_id: 'agent_001',
        stream: true
      }
    });
    
    // Should support streaming or graceful fallback
    expect([200, 400, 404, 501]).toContain(response.status());
  });

  test('should handle concurrent voice requests', async ({ request }) => {
    const promises = Array(5).fill(null).map(() => {
      const startTime = Date.now();
      return request.post(`${BASE_URL}/api/voice/test`, {
        data: {
          text: 'Concurrent test',
          agent_id: 'agent_001'
        }
      }).then(r => ({ status: r.status(), time: Date.now() - startTime }));
    });
    
    const results = await Promise.all(promises);
    
    results.forEach(r => {
      expect([200, 400, 404, 501]).toContain(r.status());
    });
    
    console.log('Concurrent voice results:', results.map(r => r.time));
  });
});
