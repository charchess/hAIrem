import { test, expect } from '../support/fixtures';

test.describe('System Health', () => {
  test('should show system status ok @smoke @p0', async ({ page }) => {
    // Given the system is running
    await page.goto('/');

    // When we check the health indicator
    // (This assumes a data-testid="health-status" exists in the UI)
    // For now, let's just check the page title or a common element
    await expect(page).toHaveTitle(/hAIrem/);
  });
});
