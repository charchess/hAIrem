import { test, expect } from '@playwright/test';

test.describe('Ctrl+Shift+R Bug Fixes', () => {
  test('should not replay old messages after hard refresh @p1', async ({ page }) => {
    // Go to the app
    await page.goto('/');
    await page.waitForTimeout(3000);
    
    // Send a message
    await page.fill('#chat-input', 'test replay fix');
    await page.click('#chat-send');
    
    // Wait for response
    await page.waitForTimeout(5000);
    
    // Get current message count AFTER sending
    const messagesAfterSend = await page.locator('.message-bubble').count();
    console.log(`Messages after send: ${messagesAfterSend}`);
    
    // Hard refresh (Ctrl+Shift+R)
    await page.keyboard.press('Control+Shift+R');
    await page.waitForTimeout(3000);
    
    // Get message count after refresh
    const messagesAfterRefresh = await page.locator('.message-bubble').count();
    console.log(`Messages after refresh: ${messagesAfterRefresh}`);
    
    // Should NOT have MORE messages after refresh (no replay)
    // Allow small difference for system messages
    expect(messagesAfterRefresh).toBeLessThanOrEqual(messagesAfterSend + 1);
  });

  test('should not show Dieu in target dropdown @p1', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(3000);
    
    const dropdown = page.locator('#target-agent-select');
    await expect(dropdown).toBeVisible({ timeout: 5000 });
    
    const options = await dropdown.locator('option').allTextContents();
    console.log('Dropdown options:', options);
    
    // Dieu should NOT be in the list
    expect(options).not.toContain('Dieu');
    
    // Should have at least "Tous" and some agents
    expect(options.length).toBeGreaterThanOrEqual(2);
  });

  test('should send message and receive response @p1', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(3000);
    
    const initialCount = await page.locator('.message-bubble').count();
    
    // Send a broadcast message
    await page.selectOption('#target-agent-select', 'broadcast');
    await page.fill('#chat-input', 'Test Playwright');
    await page.click('#chat-send');
    
    // Wait for response
    await page.waitForTimeout(10000);
    
    const finalCount = await page.locator('.message-bubble').count();
    
    // Should have more messages (at least user + agent response)
    expect(finalCount).toBeGreaterThan(initialCount);
  });
});
