# Phase 3 Metrics

Metrics for the Phase 3 frontend dashboard, as required by the Phase 3 Plan.
Runtime numbers (bundle size, coverage, upload→findings time) are filled in after
a local `npm install` + build/test run — see the note at the bottom.

## Pages / components implemented

- **Route pages (4):** `DashboardPage`, `UploadPage`, `ScanListPage` (`ScansPage`),
  `ScanDetailPage`.
- **Feature components (2):** `FindingsTable`, `SeverityBadge`.
- **Shared UI primitives (4):** `Badge`, `Button`, `Card`, `Spinner`.
- **API layer:** `client.ts`, `scans.ts`, `types.ts`.
- **Mock layer:** `handlers.ts`, `data.ts`, `browser.ts` (+ Node `setupServer` in
  tests).
- **Charts:** 2 (findings-by-severity pie, findings-by-resource-type bar).

## Tests

- **Test files: 5** — `UploadPage`, `ScansPage`, `ScanDetailPage`, `FindingsTable`,
  `DashboardPage`.
- **Cases: 11** covering upload success/error/client-validation, list render +
  empty, detail render + 404, severity filter + null-field rendering, and chart
  aggregation + empty state.
- Pass/fail and coverage %: **pending first CI/local run** (see note).

## Bundle size

- After `npm run build`: **pending** (`vite build` needs the platform native
  bundler binary from `npm install`).

## Upload → findings-on-screen time (standard fixture)

- **Pending** — measure once running against the real Phase 2 backend.

---

> **Note:** This phase was assembled and reviewed offline (no `npm install`), so
> the numbers marked *pending* above have not been captured yet. Member 4's chart
> and test dependencies (`recharts`, `vitest`, `@testing-library/*`, `jsdom`) are
> declared in `package.json` but not yet installed. Run `npm install` in
> `frontend/`, then `npm run build` and `npm run coverage` to populate them. See
> `guides/phase 3/Phase 3 Fixes.md` for the full assembly/verification status.
