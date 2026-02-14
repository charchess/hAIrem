/**
 * UI Tests for VALIDATIONS.md Scenarios
 * Real E2E tests - no mocking, actual browser automation
 * Tests FAIL if UI elements or interactions are missing
 */

import { test, expect } from '@playwright/test';

test.describe('VALIDATIONS.md UI Scenarios', () => {
  
  test.beforeEach(async ({ page }) => {
    // Navigate to the application
    await page.goto('http://localhost:8000');
    // Wait for the app to load
    await page.waitForLoadState('networkidle');
  });

  test.describe('Background Tests', () => {
    
    test('background: presence du background au chargement', async ({ page }) => {
      // FAIL: Background should be present when app loads
      const background = page.locator('[data-testid="background"], .background, .layer-background');
      
      try {
        await expect(background).toBeVisible({ timeout: 5000 });
      } catch {
        throw new Error(
          'VALIDATIONS.md background test FAILED: Background element not found at app load.\n' +
          'Expected: [data-testid="background"] or .background or .layer-background\n' +
          'Stories: 3.1 - Layer Rendering, 11.1 - Expression Mapping'
        );
      }
    });

    test('background: background layer should load content', async ({ page }) => {
      // FAIL: Background should have loaded content (not just empty div)
      const background = page.locator('[data-testid="background"]');
      
      await expect(background).toBeVisible();
      
      // Check if background has actual content (image, color, etc.)
      const bgElement = await background.elementHandle();
      const computedStyle = await bgElement?.evaluate((el) => {
        const style = window.getComputedStyle(el);
        return {
          backgroundImage: style.backgroundImage,
          backgroundColor: style.backgroundColor,
          width: style.width,
          height: style.height
        };
      });

      if (computedStyle) {
        const hasContent = 
          computedStyle.backgroundImage !== 'none' || 
          computedStyle.backgroundColor !== 'rgba(0, 0, 0, 0)';

        try {
          expect(hasContent).toBeTruthy();
        } catch {
          throw new Error(
            'VALIDATIONS.md background test FAILED: Background has no visual content.\n' +
            'Expected: backgroundImage or backgroundColor to be set\n' +
            'Check: Background asset loading and visual rendering'
          );
        }
      }
    });
  });

  test.describe('Avatar Tests', () => {
    
    test('avatar: presence au chargement', async ({ page }) => {
      // FAIL: Avatar should be present when app loads
      const avatar = page.locator('[data-testid="avatar"], .avatar, .agent-avatar');
      
      try {
        await expect(avatar).toBeVisible({ timeout: 5000 });
      } catch {
        throw new Error(
          'VALIDATIONS.md avatar test FAILED: Avatar element not found at app load.\n' +
          'Expected: [data-testid="avatar"] or .avatar or .agent-avatar\n' +
          'Stories: 11.1 - Expression Mapping, 11.2 - Expression Test Model'
        );
      }
    });

    test('avatar: should have visible agent face/body', async ({ page }) => {
      // FAIL: Avatar should display actual agent representation
      const avatar = page.locator('[data-testid="avatar"], #avatar');
      
      await expect(avatar).toBeVisible();
      
      // Check if avatar has content (image, face, body parts)
      const avatarContent = await avatar.locator('img, #layer-agent-face, #layer-agent-body, .agent-layer').count();
      
      try {
        expect(avatarContent).toBeGreaterThan(0);
      } catch {
        throw new Error(
          'VALIDATIONS.md avatar test FAILED: Avatar has no visible content.\n' +
          'Expected: img, agent-face, or agent-body elements within avatar\n' +
          'Check: Avatar asset loading and visual rendering'
        );
      }
    });
  });

  test.describe('Dashboard Tests', () => {
    
    test('dashboard: quand on clique sur l\'icone dashboard, ca l\'ouvre', async ({ page }) => {
      // FAIL: Clicking dashboard icon should open dashboard
      const dashboardIcon = page.locator('[data-testid="dashboard-icon"], .dashboard-icon, #dashboard-btn');
      
      try {
        await expect(dashboardIcon).toBeVisible();
      } catch {
        throw new Error(
          'VALIDATIONS.md dashboard test FAILED: Dashboard icon not found.\n' +
          'Expected: [data-testid="dashboard-icon"] or .dashboard-icon or #dashboard-btn\n' +
          'Stories: 7.3 - Agent Dashboard, 17.2 - Control Panel Functionality'
        );
      }
      
      // Dashboard should be closed initially
      const dashboard = page.locator('[data-testid="dashboard"], .dashboard, .control-panel, #admin-panel');
      await expect(dashboard).toBeHidden();
      
      // Click dashboard icon
      await dashboardIcon.click();
      
      // Dashboard should open
      try {
        await expect(dashboard).toBeVisible({ timeout: 3000 });
      } catch {
        throw new Error(
          'VALIDATIONS.md dashboard test FAILED: Dashboard did not open after clicking icon.\n' +
          'Expected: Dashboard element to become visible\n' +
          'Check: Dashboard toggle logic and event handlers'
        );
      }
    });

    test('dashboard: quand on reclique sur l\'icone dashboard, ca le ferme', async ({ page }) => {
      // FAIL: Clicking dashboard icon again should close dashboard
      const dashboardIcon = page.locator('[data-testid="dashboard-icon"], #nav-admin');
      const dashboard = page.locator('[data-testid="dashboard"], #admin-panel');
      
      // Open dashboard first
      await dashboardIcon.click();
      await expect(dashboard).toBeVisible();
      
      // Click again to close
      await dashboardIcon.click();
      
      try {
        await expect(dashboard).toBeHidden({ timeout: 3000 });
      } catch {
        throw new Error(
          'VALIDATIONS.md dashboard test FAILED: Dashboard did not close when clicking icon again.\n' +
          'Expected: Dashboard element to become hidden\n' +
          'Check: Dashboard toggle logic (should be boolean)'
        );
      }
    });

    test('dashboard: quand je clique en dehors, ca le ferme', async ({ page }) => {
      // FAIL: Clicking outside should close dashboard
      const dashboardIcon = page.locator('[data-testid="dashboard-icon"], #nav-admin');
      const dashboard = page.locator('[data-testid="dashboard"], #admin-panel');
      
      // Open dashboard
      await dashboardIcon.click();
      await expect(dashboard).toBeVisible();
      
      // Click outside (on background)
      await page.click('body', { position: { x: 50, y: 50 } });
      
      try {
        await expect(dashboard).toBeHidden({ timeout: 3000 });
      } catch {
        throw new Error(
          'VALIDATIONS.md dashboard test FAILED: Dashboard did not close when clicking outside.\n' +
          'Expected: Click outside should close dashboard\n' +
          'Check: Outside click event handler and propagation'
        );
      }
    });

    test('dashboard: quand je clique sur la croix, ca le ferme', async ({ page }) => {
      // FAIL: Clicking X button should close dashboard
      const dashboardIcon = page.locator('[data-testid="dashboard-icon"], #nav-admin');
      const dashboard = page.locator('[data-testid="dashboard"], #admin-panel');
      const closeButton = page.locator('[data-testid="dashboard-close"], #close-admin, .close-button');
      
      // Open dashboard
      await dashboardIcon.click();
      await expect(dashboard).toBeVisible();
      
      // Click close button
      try {
        await expect(closeButton).toBeVisible();
      } catch {
        throw new Error(
          'VALIDATIONS.md dashboard test FAILED: Close button (X) not found in dashboard.\n' +
          'Expected: [data-testid="dashboard-close"] or .dashboard-close\n' +
          'Check: Dashboard close button implementation'
        );
      }
      
      await closeButton.click();
      
      try {
        await expect(dashboard).toBeHidden({ timeout: 3000 });
      } catch {
        throw new Error(
          'VALIDATIONS.md dashboard test FAILED: Dashboard did not close when clicking X button.\n' +
          'Expected: Close button should hide dashboard\n' +
          'Check: Close button event handler'
        );
      }
    });

    test('dashboard: quand je clique echap, ca le ferme', async ({ page }) => {
      // FAIL: Pressing Escape should close dashboard
      const dashboardIcon = page.locator('[data-testid="dashboard-icon"], #nav-admin');
      const dashboard = page.locator('[data-testid="dashboard"], #admin-panel');
      
      // Open dashboard
      await dashboardIcon.click();
      await expect(dashboard).toBeVisible();
      
      // Press Escape key
      await page.keyboard.press('Escape');
      
      try {
        await expect(dashboard).toBeHidden({ timeout: 3000 });
      } catch {
        throw new Error(
          'VALIDATIONS.md dashboard test FAILED: Dashboard did not close when pressing Escape.\n' +
          'Expected: Escape key should close dashboard\n' +
          'Check: Keyboard event handler for Escape key'
        );
      }
    });
  });

  test.describe('Crew Tests', () => {
    
    test('crew: quand on clique sur l\'icone crew, ca l\'ouvre', async ({ page }) => {
      // FAIL: Clicking crew icon should open crew panel
      const crewIcon = page.locator('[data-testid="crew-icon"], .crew-icon, #crew-btn');
      
      try {
        await expect(crewIcon).toBeVisible();
      } catch {
        throw new Error(
          'VALIDATIONS.md crew test FAILED: Crew icon not found.\n' +
          'Expected: [data-testid="crew-icon"] or .crew-icon or #crew-btn\n' +
          'Stories: 7.3 - Agent Dashboard, 17.3 - Crew Panel Enhancements'
        );
      }
      
      // Crew should be closed initially
      const crew = page.locator('[data-testid="crew"], .crew, .crew-panel, #crew-panel');
      await expect(crew).toBeHidden();
      
      // Click crew icon
      await crewIcon.click();
      
      // Crew should open
      try {
        await expect(crew).toBeVisible({ timeout: 3000 });
      } catch {
        throw new Error(
          'VALIDATIONS.md crew test FAILED: Crew panel did not open after clicking icon.\n' +
          'Expected: Crew element to become visible\n' +
          'Check: Crew panel toggle logic and event handlers'
        );
      }
    });

    test('crew: quand on reclique sur l\'icone crew, ca le ferme', async ({ page }) => {
      // FAIL: Clicking crew icon again should close crew panel
      const crewIcon = page.locator('[data-testid="crew-icon"], #nav-crew');
      const crew = page.locator('[data-testid="crew"], #crew-panel');
      
      // Open crew panel
      await crewIcon.click();
      await expect(crew).toBeVisible();
      
      // Click again to close
      await crewIcon.click();
      
      try {
        await expect(crew).toBeHidden({ timeout: 3000 });
      } catch {
        throw new Error(
          'VALIDATIONS.md crew test FAILED: Crew panel did not close when clicking icon again.\n' +
          'Expected: Crew element to become hidden\n' +
          'Check: Crew panel toggle logic (should be boolean)'
        );
      }
    });

    test('crew: quand je clique en dehors, ca le ferme', async ({ page }) => {
      // FAIL: Clicking outside should close crew panel
      const crewIcon = page.locator('[data-testid="crew-icon"], #nav-crew');
      const crew = page.locator('[data-testid="crew"], #crew-panel');
      
      // Open crew panel
      await crewIcon.click();
      await expect(crew).toBeVisible();
      
      // Click outside (on background)
      await page.click('body', { position: { x: 100, y: 100 } });
      
      try {
        await expect(crew).toBeHidden({ timeout: 3000 });
      } catch {
        throw new Error(
          'VALIDATIONS.md crew test FAILED: Crew panel did not close when clicking outside.\n' +
          'Expected: Click outside should close crew panel\n' +
          'Check: Outside click event handler and propagation'
        );
      }
    });

    test('crew: quand je clique sur la croix, ca le ferme', async ({ page }) => {
      // FAIL: Clicking X button should close crew panel
      const crewIcon = page.locator('[data-testid="crew-icon"], #nav-crew');
      const crew = page.locator('[data-testid="crew"], #crew-panel');
      const closeButton = page.locator('[data-testid="crew-close"], #close-crew, .close-button');
      
      // Open crew panel
      await crewIcon.click();
      await expect(crew).toBeVisible();
      
      // Click close button
      try {
        await expect(closeButton).toBeVisible();
      } catch {
        throw new Error(
          'VALIDATIONS.md crew test FAILED: Close button (X) not found in crew panel.\n' +
          'Expected: [data-testid="crew-close"] or .crew-close\n' +
          'Check: Crew panel close button implementation'
        );
      }
      
      await closeButton.click();
      
      try {
        await expect(crew).toBeHidden({ timeout: 3000 });
      } catch {
        throw new Error(
          'VALIDATIONS.md crew test FAILED: Crew panel did not close when clicking X button.\n' +
          'Expected: Close button should hide crew panel\n' +
          'Check: Close button event handler'
        );
      }
    });

    test('crew: quand je clique echap, ca le ferme', async ({ page }) => {
      // FAIL: Pressing Escape should close crew panel
      const crewIcon = page.locator('[data-testid="crew-icon"], #nav-crew');
      const crew = page.locator('[data-testid="crew"], #crew-panel');
      
      // Open crew panel
      await crewIcon.click();
      await expect(crew).toBeVisible();
      
      // Press Escape key
      await page.keyboard.press('Escape');
      
      try {
        await expect(crew).toBeHidden({ timeout: 3000 });
      } catch {
        throw new Error(
          'VALIDATIONS.md crew test FAILED: Crew panel did not close when pressing Escape.\n' +
          'Expected: Escape key should close crew panel\n' +
          'Check: Keyboard event handler for Escape key'
        );
      }
    });
  });
});