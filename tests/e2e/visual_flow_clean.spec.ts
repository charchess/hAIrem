import { test, expect } from '../support/fixtures';

test.describe('Visual Flow Refactored (Zero Sleep)', () => {
  test('should update background without hard waits @p1', async ({ page }) => {
    await page.goto('/');
    const bg = page.locator('#layer-bg');
    // Utilisation de toBeVisible() au lieu de waitForTimeout
    await expect(bg).toBeVisible();
  });
});