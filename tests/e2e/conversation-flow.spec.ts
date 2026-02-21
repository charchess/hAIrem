import { test, expect } from '@playwright/test';

test.describe('Conversation Flow Scenarios', () => {
  
  test.beforeEach(async ({ page }) => {
    // Navigate to the application
    await page.goto('http://localhost:8000');
    // Wait for the app to load
    await page.waitForLoadState('networkidle');
  });

  test('conversation: agent should respond to "bonjour les filles"', async ({ page }) => {
    const chatInput = page.locator('#chat-input');
    const sendButton = page.locator('#chat-send');
    const dialogueText = page.locator('#dialogue-text');
    const stage = page.locator('#the-stage');

    // Initial state check
    const initialText = await dialogueText.textContent();
    console.log('Initial text:', initialText);

    // Send greeting
    await chatInput.fill('bonjour les filles');
    await sendButton.click();

    // Verify thinking state (stage usually gets a class or style change)
    // Based on previous troubleshooting, we expect some visual feedback
    // In our case, the user reported "écran grisâtre" which corresponds to .state-thinking
    await expect(stage).toHaveClass(/state-thinking/, { timeout: 5000 });
    console.log('Thinking state detected');

    // Wait for response
    // We expect the text to change from "Initialisation..." or the thinking state to end
    // and a new message to appear in the dialogue container
    await expect(dialogueText).not.toHaveText(/Initialisation|bonjour les filles/, { timeout: 30000 });
    
    const responseText = await dialogueText.textContent();
    console.log('Agent response:', responseText);

    // Final assertion: response should not be empty and not the initial text
    expect(responseText?.length).toBeGreaterThan(0);
    expect(responseText).not.toBe(initialText);
    
    // Also check that we are no longer in thinking state
    await expect(stage).not.toHaveClass(/state-thinking/, { timeout: 10000 });
  });
});
