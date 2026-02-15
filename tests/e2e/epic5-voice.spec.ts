/**
 * E2E Tests for Epic 5 - Voice
 * 
 * Tests the complete voice pipeline: STT → Agent Response → TTS.
 */

import { test, expect } from '@playwright/test';

test.describe('Epic 5 - Voice E2E', () => {
  
  test('AC1: Microphone input → STT → Agent response', async ({ page, context }) => {
    await page.goto('/');
    
    // Grant microphone permission
    await context.grantPermissions(['microphone']);
    
    // Click microphone button (simulate speaking)
    await page.click('#microphone-button');
    
    // Wait for STT processing
    await page.waitForSelector('.stt-processing');
    
    // Should trigger agent response
    await page.waitForSelector('.agent-response');
  });

  test('AC2: Agent response → TTS audio playback', async ({ page }) => {
    await page.goto('/');
    
    await page.fill('#message-input', 'Speak this text');
    await page.click('#send-button');
    
    // Wait for TTS audio
    await page.waitForSelector('audio.playing');
    
    const audio = page.locator('audio');
    await expect(audio).toBeVisible();
  });

  test('AC3: Voice modulation with emotion', async ({ page }) => {
    await page.goto('/');
    
    // Set emotion (via API or UI)
    await page.goto('/admin');
    await page.click('#emotion-selector');
    await page.selectOption('#emotion-selector', 'happy');
    
    await page.goto('/');
    await page.fill('#message-input', 'Happy message');
    await page.click('#send-button');
    
    // Verify modulated voice (via params or audio analysis)
    await page.waitForSelector('.voice-modulated[data-emotion="happy"]');
  });

  test('AC4: Prosody/intonation variation', async ({ page }) => {
    await page.goto('/');
    
    // Set prosody style
    await page.goto('/admin');
    await page.selectOption('#prosody-selector', 'question');
    
    await page.goto('/');
    await page.fill('#message-input', 'Is this working?');
    await page.click('#send-button');
    
    // Verify prosody applied
    await page.waitForSelector('.prosody-applied[data-style="question"]');
  });
});
