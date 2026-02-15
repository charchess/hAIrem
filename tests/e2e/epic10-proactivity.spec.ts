/**
 * E2E Tests for Epic 10 - Proactivity
 * 
 * Tests proactive behaviors: events, hardware, calendar, stimulus.
 */

import { test, expect } from '@playwright/test';

test.describe('Epic 10 - Proactivity E2E', () => {
  
  test('AC1: Agent reacts to hardware event', async ({ page, request }) => {
    await page.goto('/');
    
    // Simulate hardware event (motion)
    await request.post('/api/hardware/events', {
      data: {
        event_type: 'motion',
        device_id: 'sensor_livingroom',
        value: 'detected'
      }
    });
    
    // Agent should react proactively
    await page.waitForSelector('.agent-proactive-response');
  });

  test('AC2: Agent reminds about upcoming calendar event', async ({ page, request }) => {
    await page.goto('/');
    
    // Create upcoming event
    await request.post('/api/calendar/events', {
      data: {
        title: 'Meeting in 5 min',
        start_time: '2026-02-15T17:00:00Z'
      }
    });
    
    // Agent should remind
    await page.waitForSelector('.calendar-reminder');
  });

  test('AC3: Agent reacts to stimulus trigger', async ({ page, request }) => {
    await page.goto('/');
    
    // Trigger stimulus
    await request.post('/api/stimulus/trigger', {
      data: { type: 'proactive' }
    });
    
    // Agent reacts
    await page.waitForSelector('.stimulus-response');
  });

  test('AC4: Multiple agents subscribe to events', async ({ page }) => {
    await page.goto('/');
    
    // Subscribe agents to events
    await request.post('/api/events/subscribe', {
      data: { agent_id: 'agent1', event_type: 'system_status' }
    });
    
    // Trigger event
    await request.post('/api/events/trigger', {
      data: { type: 'system_status' }
    });
    
    // Multiple agents respond
    await page.waitForSelector('.multi-agent-response');
  });
});
