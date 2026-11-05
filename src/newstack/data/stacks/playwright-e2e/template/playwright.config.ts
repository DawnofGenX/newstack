import { defineConfig, devices } from "@playwright/test";

const PORT = 5464;

/**
 * The fixture server is started by Playwright itself (`webServer`), so the suite is
 * one command: no separate terminal, and no "port already in use" if a run is killed.
 */
export default defineConfig({
  testDir: "./tests",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: process.env.CI ? [["github"], ["line"]] : [["list"]],
  timeout: 30_000,
  expect: { timeout: 5_000 },
  use: {
    baseURL: `http://127.0.0.1:${PORT}`,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "off",
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] }, testIgnore: /mobile\.spec\.ts/ },
    { name: "mobile", use: { ...devices["Pixel 7"] }, testMatch: /mobile\.spec\.ts/ },
  ],
  webServer: {
    command: `node fixtures/server.mjs`,
    url: `http://127.0.0.1:${PORT}/api/health`,
    env: { PORT: String(PORT), HOST: "127.0.0.1" },
    reuseExistingServer: false,
    timeout: 30_000,
    stdout: "pipe",
    stderr: "pipe",
  },
});
