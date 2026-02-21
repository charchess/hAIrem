import { test, expect } from '@playwright/test';

test.describe.configure({ mode: 'serial' });

test.describe('Configuration Priority Validation', () => {
  
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:8000');
    await page.waitForLoadState('networkidle');
    
    // Cleanup any existing overrides via direct console command if we had one
    // Since we don't have a delete UI, we'll just use a fresh agent for each check
  });

  test('config: global LLM config change should propagate to agents (Renarde)', async ({ page }) => {
    // Open Admin Panel
    await page.locator('#nav-admin').click();
    
    // Switch to LLM Tab
    await page.locator('.admin-tab[data-tab="llm"]').click();
    
    // Change Global Model
    const testModel = 'openrouter/google/gemma-2-9b-it:free';
    await page.locator('#global-llm-model').fill(testModel);
    await page.locator('#save-global-llm').click();
    
    // Wait for propagation
    await page.waitForTimeout(3000);

    // Switch to Crew Panel
    await page.locator('#nav-crew').click();
    
    // Check Renarde's card (she shouldn't have an override)
    const renardeCard = page.locator('#agent-card-Renarde');
    await expect(renardeCard).toContainText(testModel, { timeout: 15000 });
    
    console.log('Global config propagation: PASS');
  });

  test('config: agent override should take priority over global (Lisa)', async ({ page }) => {
    // Open Admin Panel
    await page.locator('#nav-admin').click();
    
    // Switch to Agents Tab
    await page.locator('.admin-tab[data-tab="agents"]').click();
    
    // Select Lisa
    await page.locator('#agent-sub-tabs .admin-tab:has-text("Lisa")').click();
    
    // Set Override Model
    const overrideModel = 'openrouter/meta-llama/llama-3-8b-instruct:free';
    await page.locator('#agent-llm-model').fill(overrideModel);
    await page.locator('#save-agent-override').click();
    
    await page.waitForTimeout(3000);

    // Switch to Crew Panel
    await page.locator('#nav-crew').click();
    
    // Check Lisa has override
    const lisaCard = page.locator('#agent-card-Lisa');
    await expect(lisaCard).toContainText(overrideModel, { timeout: 15000 });
    
    console.log('Agent override priority: PASS');
  });
});
