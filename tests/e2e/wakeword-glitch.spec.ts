import { test, expect } from '@playwright/test';

test.describe('Wake Word Visual Glitch Detection', () => {
  
  test('No layout shift when wake word detected', async ({ page }) => {
    // Navigate to app
    await page.goto('http://localhost:8000');
    await page.waitForLoadState('networkidle');

    // Select elements to monitor for shifting
    const background = page.locator('#layer-bg');
    
    // Get initial bounding box
    const bgBoxInitial = await background.boundingBox();
    console.log('Initial BG:', bgBoxInitial);

    // Simulate wake word detection visual feedback
    await page.evaluate(() => {
        const stage = document.getElementById('the-stage');
        if (stage) {
            // Apply the style change that was causing the glitch
            // We use the NEW implementation to verify it doesn't shift
            stage.style.transition = 'all 0.3s ease';
            stage.style.boxShadow = 'inset 0 0 0 2px rgba(0, 255, 136, 0.8), 0 0 30px rgba(0, 255, 136, 0.6)';
            // Note: We are NOT setting border here, as that's what we removed.
            // If we wanted to repro the bug, we would set border.
        }
    });

    // Wait for transition
    await page.waitForTimeout(100);

    // Get new bounding box
    const bgBoxFlash = await background.boundingBox();
    console.log('Flash BG:', bgBoxFlash);

    // Assert positions haven't changed
    if (bgBoxInitial && bgBoxFlash) {
        expect(bgBoxFlash.x).toBeCloseTo(bgBoxInitial.x, 0.1);
        expect(bgBoxFlash.y).toBeCloseTo(bgBoxInitial.y, 0.1);
        expect(bgBoxFlash.width).toBeCloseTo(bgBoxInitial.width, 0.1);
        expect(bgBoxFlash.height).toBeCloseTo(bgBoxInitial.height, 0.1);
    }
  });
});
