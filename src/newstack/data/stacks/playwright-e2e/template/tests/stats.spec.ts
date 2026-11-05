import { expect, test } from "@playwright/test";

test.describe("text stats page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test("shows an empty summary first", async ({ page }) => {
    await expect(page.getByRole("heading", { name: "Text stats" })).toBeVisible();
    await expect(page.getByTestId("summary")).toHaveText("0 lines \u00b7 0 words \u00b7 0 bytes");
  });

  test("counts while typing", async ({ page }) => {
    await page.getByTestId("input").fill("a b\nc\n");
    await expect(page.getByTestId("lines")).toHaveText("2");
    await expect(page.getByTestId("words")).toHaveText("3");
    await expect(page.getByTestId("bytes")).toHaveText("6");
    await expect(page.getByTestId("summary")).toHaveText("2 lines \u00b7 3 words \u00b7 6 bytes");
  });

  test("counts bytes, not characters", async ({ page }) => {
    await page.getByTestId("input").fill("h\u00e9llo w\u00f6rld\n");
    await expect(page.getByTestId("bytes")).toHaveText("14");
    await expect(page.getByTestId("summary")).toContainText("1 line \u00b7 2 words");
  });

  test("clears the field", async ({ page }) => {
    await page.getByTestId("input").fill("something");
    await page.getByTestId("clear").click();
    await expect(page.getByTestId("input")).toHaveValue("");
    await expect(page.getByTestId("bytes")).toHaveText("0");
  });

  test("asks the server and renders its answer", async ({ page }) => {
    await page.getByTestId("input").fill("a b\nc\n");
    await page.getByTestId("ask-server").click();
    await expect(page.getByTestId("server-answer")).toHaveText("server saw 2/3/6");
  });

  test("the label is wired to the textarea", async ({ page }) => {
    // getByLabel is the assertion that matters: a visible label that is not
    // associated passes a human eye and fails every screen reader.
    await page.getByLabel("Text").fill("x");
    await expect(page.getByTestId("words")).toHaveText("1");
  });

  test("an unknown api path answers json 404", async ({ request }) => {
    const response = await request.get("/api/nope");
    expect(response.status()).toBe(404);
    expect(await response.json()).toEqual({
      error: "not_found",
      detail: "no endpoint for GET /api/nope",
    });
  });

  test("a client route serves the page", async ({ page }) => {
    await page.goto("/about");
    await expect(page.getByTestId("input")).toBeVisible();
  });
});
