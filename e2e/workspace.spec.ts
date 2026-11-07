import { test, expect } from '@playwright/test';
const image = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAIAAAAlC+aJAAAAY0lEQVR4nO3PQQ3AIADAQEArIhCB6IngcVnSU9DOfe74s6UDXjWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgfRv4AegGUyqUAAAAAElFTkSuQmCC', 'base64');

test('offline engine keeps shielding disabled', async ({ page }) => {
  await page.route('**/api/health', route => route.fulfill({ status: 503 }));
  await page.goto('/');
  await expect(page.getByRole('heading', { name: /Keep the picture/ })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Generate shield candidate' })).toBeDisabled();
  await expect(page.getByText('Engine offline — start the service')).toBeVisible();
});

test('upload requires consent, returns download, and clears stale result', async ({ page }) => {
  let requests = 0;
  await page.route('**/api/health', route => route.fulfill({ json: { ready: true, busy: false, experimental: true } }));
  await page.route('**/api/protect?*', route => {
    requests++;
    // Synthetic transport fixture only; never evidence of actual protection.
    return route.fulfill({ body: image, contentType: 'image/png', headers: { 'X-Viel-Report': JSON.stringify({ status: 'experimental-unverified', max_channel_change: 4 }) } });
  });
  await page.goto('/');
  await page.getByLabel('Choose your original').setInputFiles({ name: 'photo.png', mimeType: 'image/png', buffer: image });
  await expect(page.getByAltText('Original selected photo')).toBeVisible();
  const button = page.getByRole('button', { name: 'Generate shield candidate' });
  await expect(button).toBeDisabled();
  expect(requests).toBe(0);
  await page.getByRole('checkbox').check();
  await button.click();
  await expect(page.getByRole('link', { name: 'Download candidate PNG' })).toBeVisible();
  expect(requests).toBe(1);
  await page.getByRole('button', { name: 'Remove original' }).click();
  await expect(page.getByRole('link', { name: 'Download candidate PNG' })).toHaveCount(0);
  await expect(button).toBeDisabled();
});

test('failed experiment offers no download', async ({ page }) => {
  await page.route('**/api/health', route => route.fulfill({ json: { ready: true, busy: false, experimental: true } }));
  await page.route('**/api/protect?*', route => route.fulfill({ status: 500, json: { error: { message: 'Experiment failed safely.' } } }));
  await page.goto('/');
  await page.getByLabel('Choose your original').setInputFiles({ name: 'photo.png', mimeType: 'image/png', buffer: image });
  await page.getByRole('checkbox').check();
  await page.getByRole('button', { name: 'Generate shield candidate' }).click();
  await expect(page.getByText('Experiment failed safely.')).toBeVisible();
  await expect(page.getByRole('link', { name: 'Download candidate PNG' })).toHaveCount(0);
});

test('mobile layout fits the viewport', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await page.route('**/api/health', route => route.fulfill({ status: 503 }));
  await page.goto('/');
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(375);
});
