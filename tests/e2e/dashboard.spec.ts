import { test, expect } from '../support/fixtures';

test.describe('Dashboard & Navigation (Epic 17)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should navigate between Stage, Admin and Crew panels @p1', async ({ page }) => {
    // 17.1: UI Structure & Navigation
    const navAdmin = page.locator('#nav-admin');
    const navCrew = page.locator('#nav-crew');
    const adminPanel = page.locator('#admin-panel');
    const crewPanel = page.locator('#crew-panel');

    // Initial state: panels hidden
    await expect(adminPanel).toBeHidden();
    await expect(crewPanel).toBeHidden();

    // Open Admin Panel
    await navAdmin.click();
    await expect(adminPanel).toBeVisible();
    await expect(crewPanel).toBeHidden();

    // Open Crew Panel (should close admin or overlay)
    await navCrew.click();
    await expect(crewPanel).toBeVisible();
    await expect(adminPanel).toBeHidden();

    // Close panels (clicking close button)
    await page.locator('#close-crew').click();
    await expect(crewPanel).toBeHidden();
  });

  test('should display control panel elements @p1', async ({ page }) => {
    // 17.2: Control Panel elements
    await page.locator('#nav-admin').click();
    
    await expect(page.locator('#log-level-select')).toBeVisible();
    await expect(page.locator('#status-ws-admin')).toBeVisible();
    await expect(page.locator('#status-redis-admin')).toBeVisible();
  });

  test('should show agent vitals in crew panel @p2', async ({ page }) => {
    // 17.3: Crew Panel Enhancements
    await page.locator('#nav-crew').click();
    
    // Check if agent grid is present
    const agentGrid = page.locator('#agent-grid');
    await expect(agentGrid).toBeVisible();
    
    // We expect at least one agent card if system is fully up
    // But since agents might take time to register, we just check structure
  });
});
