/**
 * E2E Tests for Epic 3 - Social Arbiter UI
 * 
 * Tests the complete conversation flow with multiple agents responding.
 */

import { test, expect } from '@playwright/test';

test.describe('Epic 3 - Social Arbiter E2E', () => {
  
  test('AC1: Correct agent responds to user message', async ({ page }) => {
    await page.goto('/');
    
    // Send message
    await page.fill('#message-input', 'Hello agents!');
    await page.click('#send-button');
    
    // Wait for response from appropriate agent
    await page.waitForSelector('[data-agent="arbiter-selected"]');
    
    const respondingAgent = page.locator('[data-agent]');
    await expect(respondingAgent).toBeVisible();
  });

  test('AC2: Avatar animates and text appears when agent speaks', async ({ page }) => {
    await page.goto('/');
    
    await page.fill('#message-input', 'Tell me a joke');
    await page.click('#send-button');
    
    // Agent avatar should animate
    await page.waitForSelector('.agent-avatar.animating');
    
    // Response text appears
    await page.waitForSelector('.agent-response');
    const responseText = page.locator('.agent-response');
    await expect(responseText).toBeVisible();
  });

  test('AC3: No overlapping speech during turn-taking', async ({ page }) => {
    await page.goto('/');
    
    // Send message that triggers multiple agents
    await page.fill('#message-input', 'Everyone say hello');
    await page.click('#send-button');
    
    // Only one agent speaks at a time
    const speakingAgents = page.locator('.agent-speaking');
    const speakingCount = await speakingAgents.count();
    expect(speakingCount).toBeLessThan(2);
  });

  test('AC4: Low-priority responses suppressed in UI', async ({ page }) => {
    await page.goto('/');
    
    // Send message with low-interest content
    await page.fill('#message-input', 'The weather is nice');
    await page.click('#send-button');
    
    // Check if low-priority agent is suppressed
    await page.waitForTimeout(3000); // Allow time for suppression
    
    const suppressedAgent = page.locator('[data-agent="low-priority"]');
    await expect(suppressedAgent).not.toBeVisible();
  });
});
