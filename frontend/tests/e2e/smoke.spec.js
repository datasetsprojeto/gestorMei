import { expect, test } from "@playwright/test";

test("loads login screen", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("#login-screen")).toBeVisible();
  await expect(page.locator("#login-email")).toBeVisible();
  await expect(page.locator("#login-pass")).toBeVisible();
});
