import { test, expect } from '@playwright/test';

test.describe('Health Indicators Validation', () => {
  
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:8000');
    await page.waitForLoadState('networkidle');
  });

  test('health: all indicators should be OK in Admin panel', async ({ page }) => {
    // Open Admin Panel
    const navAdmin = page.locator('#nav-admin');
    await navAdmin.click();
    
    // Check Status Tab (active by default)
    const statusTab = page.locator('#tab-system');
    await expect(statusTab).toBeVisible();

    // Verify indicators
    const redisStatus = page.locator('#status-redis-admin');
    const llmStatus = page.locator('#status-llm-admin');
    const brainStatus = page.locator('#status-brain-admin');
    const wsStatus = page.locator('#status-ws-admin');

    // Wait for indicators to pass the 'CHECKING' phase
    // h-core heartbeat is every 5s, bridge sends last heartbeat on connect
    await expect(redisStatus).toHaveText('OK', { timeout: 10000 });
    await expect(llmStatus).toHaveText('OK', { timeout: 10000 });
    await expect(brainStatus).toHaveText('OK', { timeout: 10000 });
    await expect(wsStatus).toHaveText('OK', { timeout: 10000 });

    // Verify CSS classes for green color
    await expect(redisStatus).toHaveClass(/ok/);
    await expect(llmStatus).toHaveClass(/ok/);
    await expect(brainStatus).toHaveClass(/ok/);
    await expect(wsStatus).toHaveClass(/ok/);
    
    console.log('All health indicators are GREEN and OK');
  });
});
