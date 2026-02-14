import { test, expect } from '@playwright/test';

test.describe('Chat Engine (Core)', () => {
  
  test('should receive response from Renarde', async ({ page }) => {
    // Wait for page to load
    await page.goto('/');
    
    // Wait for WebSocket to be ready
    await page.waitForFunction(() => {
      return window.network && window.network.socket && window.network.socket.readyState === WebSocket.OPEN;
    }, { timeout: 15000 });
    
    // Find the message input
    const messageInput = page.locator('#chat-input');
    
    // Type message to Renarde
    await messageInput.fill('salut Renarde, comment ça va ?');
    
    // Click send button
    await page.click('#chat-send');
    
    // Wait longer for Renarde to respond (LLM takes time)
    await page.waitForTimeout(15000);
    
    // Get all chat content
    const chatHistory = page.locator('#chat-history');
    const content = await chatHistory.textContent();
    
    console.log('=== CHAT CONTENT ===');
    console.log(content);
    console.log('====================');
    
    // Should have user message AND agent response
    expect(content).toContain('Renarde');
    expect(content).toContain('Moi');
    
    // Check that there's more than just the user's message
    // (should have Renarde's response)
    const messageCount = await chatHistory.locator('.message-bubble').count();
    expect(messageCount).toBeGreaterThanOrEqual(2);
    
    console.log('Total messages found:', messageCount);
  });
  
  test('should receive broadcast response', async ({ page }) => {
    await page.goto('/');
    
    // Wait for WebSocket
    await page.waitForFunction(() => {
      return window.network && window.network.socket && window.network.socket.readyState === WebSocket.OPEN;
    }, { timeout: 15000 });
    
    const messageInput = page.locator('#chat-input');
    await messageInput.fill('bonjour à tous !');
    
    // Click send
    await page.click('#chat-send');
    
    // Wait for agent(s) to respond
    await page.waitForTimeout(15000);
    
    const chatHistory = page.locator('#chat-history');
    const content = await chatHistory.textContent();
    
    console.log('=== BROADCAST CHAT ===');
    console.log(content);
    console.log('======================');
    
    // Should have at least user + 1 agent
    expect(content.length).toBeGreaterThan(50);
  });
});
