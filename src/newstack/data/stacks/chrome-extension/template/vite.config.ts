import { crx } from "@crxjs/vite-plugin";
import { defineConfig } from "vitest/config";

import manifest from "./manifest.json" with { type: "json" };

export default defineConfig({
  plugins: [crx({ manifest })],
  build: {
    outDir: "dist",
    emptyOutDir: true,
    sourcemap: false,
  },
  test: {
    environment: "jsdom",
    include: ["src/**/*.test.ts"],
    passWithNoTests: false,
  },
});
