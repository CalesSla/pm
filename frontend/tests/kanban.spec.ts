import { expect, test } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  // Log in before each test
  await page.goto("/");
  await page.getByLabel("Username").fill("user");
  await page.getByLabel("Password").fill("password");
  await page.getByRole("button", { name: /sign in/i }).click();
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
});

test("loads the kanban board", async ({ page }) => {
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(5);
});

test("adds a card to a column", async ({ page }) => {
  const firstColumn = page.locator('[data-testid^="column-"]').first();
  await firstColumn.getByRole("button", { name: /add a card/i }).click();
  await firstColumn.getByPlaceholder("Card title").fill("Playwright card");
  await firstColumn.getByPlaceholder("Details").fill("Added via e2e.");
  await firstColumn.getByRole("button", { name: /add card/i }).click();
  await expect(firstColumn.getByText("Playwright card")).toBeVisible();
});

test("deletes a card", async ({ page }) => {
  const firstColumn = page.locator('[data-testid^="column-"]').first();
  const cardCount = await firstColumn.locator('[data-testid^="card-"]').count();
  const firstCard = firstColumn.locator('[data-testid^="card-"]').first();
  const deleteBtn = firstCard.getByRole("button", { name: /delete/i });
  await deleteBtn.click();
  await expect(firstColumn.locator('[data-testid^="card-"]')).toHaveCount(cardCount - 1);
});
