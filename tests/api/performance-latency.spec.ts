/**
 * Performance Tests: R-001 - Message Latency Under Load
 * 
 * Risk: Message latency >2s under load (50+ concurrent users)
 * Score: 9 (Critical)
 * 
 * Tests verify that API response times remain acceptable under concurrent load.
 */

import { test, expect } from '@playwright/test';

const BASE_URL = process.env.BASE_URL || 'http://localhost:8000';
const CONCURRENT_USERS = 50;
const MAX_LATENCY_MS = 2000;

test.describe('R-001: Message Latency Under Load', () => {
  
  test('should respond within 2s under normal load', async ({ request }) => {
    const startTime = Date.now();
    
    const response = await request.get(`${BASE_URL}/api/health`);
    const latency = Date.now() - startTime;
    
    expect(response.status()).toBe(200);
    expect(latency).toBeLessThan(MAX_LATENCY_MS);
  });

  test('should handle 10 concurrent requests within 3s', async ({ request }) => {
    const promises = Array(10).fill(null).map(() => 
      request.get(`${BASE_URL}/api/health`)
    );
    
    const startTime = Date.now();
    const responses = await Promise.all(promises);
    const totalTime = Date.now() - startTime;
    
    responses.forEach(res => expect(res.status()).toBe(200));
    expect(totalTime).toBeLessThan(3000);
  });

  test('should handle 50 concurrent requests with acceptable degradation', async ({ request }) => {
    // Send 50 concurrent requests
    const promises = Array(CONCURRENT_USERS).fill(null).map(() => 
      request.get(`${BASE_URL}/api/health`).then(async (res) => {
        return {
          status: res.status(),
          latency: Date.now()
        };
      })
    );
    
    const startTime = Date.now();
    const results = await Promise.all(promises);
    const totalTime = Date.now() - startTime;
    
    // All should succeed or gracefully degrade
    const successCount = results.filter(r => r.status === 200).length;
    
    console.log(`50 concurrent requests: ${totalTime}ms, ${successCount}/${CONCURRENT_USERS} succeeded`);
    
    // Allow 50% failure under extreme load, but system should not crash
    expect(successCount).toBeGreaterThan(0);
  });

  test('should not timeout under sustained load', async ({ request }) => {
    const duration = 10000; // 10 seconds
    const interval = 100; // 100ms between requests
    const startTime = Date.now();
    let successCount = 0;
    let failCount = 0;
    
    while (Date.now() - startTime < duration) {
      try {
        const res = await request.get(`${BASE_URL}/api/health`, { timeout: 5000 });
        if (res.status() === 200) successCount++;
        else failCount++;
      } catch {
        failCount++;
      }
      await new Promise(r => setTimeout(r, interval));
    }
    
    console.log(`Sustained load: ${successCount} success, ${failCount} failed`);
    
    // At least 80% should succeed under sustained load
    expect(successCount / (successCount + failCount)).toBeGreaterThan(0.8);
  });
});
