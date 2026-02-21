import { test, expect } from '@playwright/test';

test.describe('Visual Glitch Detection', () => {
  
  test('No layout shift when agent speaks', async ({ page }) => {
    // Navigate to app
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Select elements to monitor for shifting
    const background = page.locator('#layer-bg');
    const chatInput = page.locator('#chat-input');
    const avatar = page.locator('#avatar');
    const agentBody = page.locator('#layer-agent-body');

    // Get initial bounding boxes
    const bgBoxInitial = await background.boundingBox();
    const inputBoxInitial = await chatInput.boundingBox();
    const avatarBoxInitial = await avatar.boundingBox();
    const bodyBoxInitial = await agentBody.boundingBox();
    
    console.log('Initial BG:', bgBoxInitial);
    console.log('Initial Input:', inputBoxInitial);

    // Force agent into speaking state via JS
    await page.evaluate(() => {
        // Trigger the renderer state change
        if (window.renderer) {
            window.renderer.setState('speaking');
            // Force the active-speaker class on avatar just in case logic differs
            document.getElementById('avatar').classList.add('active-speaker');
        }
    });

    // Wait for any potential transition
    await page.waitForTimeout(500);

    // Get new bounding boxes
    const bgBoxSpeaking = await background.boundingBox();
    const inputBoxSpeaking = await chatInput.boundingBox();
    const avatarBoxSpeaking = await avatar.boundingBox();
    const bodyBoxSpeaking = await agentBody.boundingBox();

    console.log('Speaking BG:', bgBoxSpeaking);
    console.log('Speaking Input:', inputBoxSpeaking);

    // Assert positions haven't changed
    expect(bgBoxSpeaking.x).toBeCloseTo(bgBoxInitial.x, 0.1);
    expect(bgBoxSpeaking.y).toBeCloseTo(bgBoxInitial.y, 0.1);
    expect(bgBoxSpeaking.width).toBeCloseTo(bgBoxInitial.width, 0.1);
    expect(bgBoxSpeaking.height).toBeCloseTo(bgBoxInitial.height, 0.1);

    expect(inputBoxSpeaking.x).toBeCloseTo(inputBoxInitial.x, 0.1);
    expect(inputBoxSpeaking.y).toBeCloseTo(inputBoxInitial.y, 0.1);

    // Check Avatar and Body
    expect(avatarBoxSpeaking.x).toBeCloseTo(avatarBoxInitial.x, 0.1);
    expect(avatarBoxSpeaking.y).toBeCloseTo(avatarBoxInitial.y, 0.1);
    
    if (bodyBoxInitial && bodyBoxSpeaking) {
        expect(bodyBoxSpeaking.x).toBeCloseTo(bodyBoxInitial.x, 0.1);
        expect(bodyBoxSpeaking.y).toBeCloseTo(bodyBoxInitial.y, 0.1);
    }

    // Verify CSS implementation: Ensure NO BORDER is used on active speaker
    const styles = await avatar.evaluate((el) => {
        const computed = window.getComputedStyle(el);
        return {
            borderWidth: computed.borderTopWidth,
            boxShadow: computed.boxShadow
        };
    });
    
    // Expect 0px border
    expect(styles.borderWidth).toBe('0px');
    
    // Expect box-shadow to be present (green line simulation)
    // The exact color string varies by browser/computed style, but should contain the RGB components
    // 0, 255, 204
    expect(styles.boxShadow).toContain('0, 255, 204');
  });
});
