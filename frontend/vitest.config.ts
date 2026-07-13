import { defineConfig } from "vitest/config";

// Force the automatic JSX runtime via esbuild so test files don't need `React`
// in scope. (Under vite 8 / rolldown the @vitejs/plugin-react transform wasn't
// applying in the test pipeline, which surfaced as "React is not defined".)
// Kept separate from vite.config.ts so tests don't pull in the Tailwind plugin.
// Tests run against the same MSW handlers Member 1 authored (see src/test/setup.ts).
export default defineConfig({
  esbuild: {
    jsx: "automatic",
    jsxImportSource: "react",
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: "./src/test/setup.ts",
    include: ["src/**/*.test.{ts,tsx}"],
    coverage: {
      provider: "v8",
      include: ["src/**/*.{ts,tsx}"],
      exclude: ["src/**/*.test.{ts,tsx}", "src/test/**", "src/mocks/**", "src/main.tsx"],
    },
  },
});