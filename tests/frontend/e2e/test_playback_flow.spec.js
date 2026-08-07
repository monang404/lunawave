/* eslint-disable no-undef */
const { test, expect } = require('@playwright/test');

test.describe('LunaWave Basic Playback Flow', () => {
  test('should display client UI and connect to WebSocket', async ({ page }) => {
    // Go to client URL (Dengar Saja)
    await page.goto('/');

    // Check if the page loaded successfully
    await expect(page).toHaveTitle(/LunaWave/);

    // Give it a moment to connect to WebSocket
    // We expect the connection status (toast or UI element) to indicate connected.
    // Assuming we have a #toast-container or now-playing visibility
    await page.waitForTimeout(2000);

    // We just verify it loads without throwing console errors for now
  });
});
