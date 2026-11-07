import { test, expect } from '@playwright/test';
const image = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAIAAAAlC+aJAAAAY0lEQVR4nO3PQQ3AIADAQEArIhCB6IngcVnSU9DOfe74s6UDXjWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgfRv4AegGUyqUAAAAAElFTkSuQmCC', 'base64');


// These routes test UI transport only, never actual protection efficacy.
async function connected(page: import('@playwright/test').Page) {
  await page.route('**/api/face/health', route => route.fulfill({ json: { ready: true, method: 'upstream-fawkes' } }));
}

test('offline Fawkes service disables generation', async ({ page }) => {
  await page.route('**/api/face/health', route => route.fulfill({ status: 503 }));
  await page.goto('/');
  await expect(page.getByRole('heading', { name: /Keep the picture/ })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Generate Fawkes cloak' })).toBeDisabled();
  await page.screenshot({ path: 'test-results/face-workspace.png', fullPage: true });
});

test('cloaking requires consent and returns a labelled unverified result', async ({ page }) => {
  await connected(page);
  let requests=0;
  await page.route('**/api/face/jobs?*', route => { requests++; return route.fulfill({ status: 202, json: { id: 'fixture' } }); });
  await page.route('**/api/face/jobs/fixture', route => route.fulfill({ json: { status: 'done', message: 'Completed', report: { method: 'test-fixture' } } }));
  await page.route('**/api/face/jobs/fixture/result', route => route.fulfill({ body: image, contentType: 'image/png' }));
  await page.goto('/');
  await page.getByLabel('Choose face photo').setInputFiles({ name: 'photo.png', mimeType: 'image/png', buffer: image });
  const button=page.getByRole('button', { name: 'Generate Fawkes cloak' });
  await expect(button).toBeDisabled();expect(requests).toBe(0);
  await page.getByRole('checkbox').check();await button.click();
  await expect(page.getByRole('link', { name: 'Download cloaked PNG' })).toBeVisible();
  await expect(page.getByText('CLOAK GENERATED / UNVERIFIED')).toBeVisible();
});

test('a failed recognition experiment is displayed as no reduction', async ({ page }) => {
  await connected(page);
  const report={baseline_correct:2,cloaked_correct:2,test_count:2,drop_percentage_points:0,interpretation:'no-reduction-in-this-test'};
  await page.route('**/api/face/jobs?*', route => route.fulfill({ status: 202, json: { id: 'proof-fixture' } }));
  await page.route('**/api/face/jobs/proof-fixture', route => route.fulfill({ json: { status: 'done', message: 'Completed', report } }));
  await page.route('**/api/face/jobs/proof-fixture/result', route => route.fulfill({ json: report }));
  await page.goto('/');
  await page.getByLabel('What would you like to do?').selectOption('proof');
  await page.getByLabel('Identity to protect').fill('person_a');
  await page.getByLabel('Choose experiment ZIP').setInputFiles({ name: 'fixture.zip', mimeType: 'application/zip', buffer: Buffer.from('transport fixture only') });
  await page.getByRole('checkbox').check();
  await page.getByRole('button', { name: 'Run recognition experiment', exact: true }).click();
  await expect(page.getByText('No recognition reduction demonstrated.')).toBeVisible();
  await expect(page.getByRole('link', { name: 'Download measured report' })).toBeVisible();
});

test('failed cloak offers no download', async ({ page }) => {
  await connected(page);
  await page.route('**/api/face/jobs?*', route => route.fulfill({ status: 202, json: { id: 'bad' } }));
  await page.route('**/api/face/jobs/bad', route => route.fulfill({ json: { status: 'failed', message: 'No face detected.' } }));
  await page.goto('/');
  await page.getByLabel('Choose face photo').setInputFiles({ name:'photo.png', mimeType:'image/png', buffer:image });
  await page.getByRole('checkbox').check();
  await page.getByRole('button', { name:'Generate Fawkes cloak' }).click();
  await expect(page.getByText('No face detected.')).toBeVisible();
  await expect(page.getByRole('link', { name: 'Download cloaked PNG' })).toHaveCount(0);
});

test('mobile page fits viewport', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await page.route('**/api/face/health', route => route.fulfill({ status: 503 }));
  await page.goto('/');
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(375);
});
