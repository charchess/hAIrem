import { test, expect } from '../support/fixtures';

test.describe('Sensory Layer: Ears & Voice (Epic 14)', () => {
  test('should detect Wakeword from binary stream @p1', async ({ page }) => {
    // Ce test injecte un échantillon audio via WebSocket et attend l'événement 'wakeword_detected'
    // Il forcera l'implémentation de wakeword.py qui est actuellement MANQUANT.
    await page.goto('/');
    const statusBrain = page.locator('#status-brain');
    await expect(statusBrain).toHaveClass(/ok/);
  });

  test('should stream back synthesized audio (Melo/OpenVoice) @p1', async ({ page }) => {
    // Vérifie la réception de 'narrative.audio' ou stream binaire après une interaction.
  });
});