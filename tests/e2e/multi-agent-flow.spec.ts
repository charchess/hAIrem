import { test, expect } from '@playwright/test';

test.describe('Multi-Agent Conversation Flow', () => {
  
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:8000');
    await page.waitForLoadState('networkidle');
  });

  test('conversation: multiple agents should respond to direct mention', async ({ page }) => {
    const chatInput = page.locator('#chat-input');
    const sendButton = page.locator('#chat-send');
    const dialogueText = page.locator('#dialogue-text');
    const stage = page.locator('#the-stage');

    // Send message mentioning two agents
    await chatInput.fill('Lisa et Renarde, quelle est votre couleur préférée ? Répondez une après l\'autre.');
    await sendButton.click();

    // Expect thinking state
    await expect(stage).toHaveClass(/state-thinking/);

    // Wait for the chain of responses
    // We expect at least two different agents to speak in sequence
    // This might take some time as they respond one after another
    
    // Monitor console logs
    page.on('console', msg => {
        if (msg.text().includes('[SpeechQueue]')) console.log(`BROWSER: ${msg.text()}`);
    });

    // First response
    const agentName = page.locator('#agent-name');
    console.log('Waiting for first response...');
    await expect(dialogueText).not.toHaveText(/Initialisation/, { timeout: 45000 });
    const firstAgent = await agentName.textContent();
    console.log(`First responder detected: ${firstAgent}`);

    // Second response (Cascade or Inter-agent)
    console.log(`Waiting for second responder (different from ${firstAgent})...`);
    try {
        await page.waitForFunction(
            (oldAgent) => {
                const current = document.getElementById('agent-name')?.textContent;
                return current && current.trim() !== '' && current !== oldAgent && current !== 'System';
            },
            firstAgent,
            { timeout: 60000 }
        );
        const secondAgent = await agentName.textContent();
        console.log(`Second responder detected: ${secondAgent}`);
        expect(secondAgent).not.toBe(firstAgent);
    } catch (e) {
        console.log('Timeout waiting for second responder. Check if rate limits occurred.');
        // Don't fail immediately, let's see what we got
        const finalAgent = await agentName.textContent();
        console.log(`Final agent on screen: ${finalAgent}`);
        throw e;
    }

    
    // Check that we saw visual focus changes (though hard to assert exact timing)
    // The fact that the text changed twice is a strong indicator of multi-agent flow
  });
});
