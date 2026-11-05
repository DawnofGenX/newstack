import { expect, test } from "@playwright/test";

test("the page is usable on a phone viewport", async ({ page }, testInfo) => {
  test.skip(!testInfo.project.name.includes("mobile"), "mobile project only");

  await page.goto("/");
  await page.getByTestId("input").fill("a b\nc\n");

  await expect(page.getByTestId("lines")).toHaveText("2");
  // Nothing may overflow the viewport: a horizontal scrollbar on a phone is a bug,
  // and `documentElement.scrollWidth` is the cheapest honest check for it.
  const width = await page.evaluate(() => document.documentElement.scrollWidth);
  const viewport = page.viewportSize();
  expect(viewport).not.toBeNull();
  expect(width).toBeLessThanOrEqual(viewport!.width + 1);
});
